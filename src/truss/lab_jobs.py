"""M5: one bounded benchmark child per API, immutable recent job results and cancellation."""

import os
import subprocess
import sys
import threading
from uuid import uuid4
from .api_models import BenchmarkResult, LabJob
from .mock import utc_now


class LabJobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = {}
        self.keys = {}
        self.process = None
        self.closed = False
        self.worker = None

    def submit(self, request, key):
        body = request.model_dump_json()
        with self.lock:
            if self.closed:
                raise ValueError("unavailable")
            if key in self.keys:
                old, job_id = self.keys[key]
                if old != body:
                    raise ValueError("idempotency_conflict")
                return self.jobs[job_id]
            if any(j.status == "running" for j in self.jobs.values()):
                raise ValueError("busy")
            if len(self.jobs) >= 32:
                oldest = next(iter(self.jobs))
                del self.jobs[oldest]
                self.keys = {k: v for k, v in self.keys.items() if v[1] != oldest}
            job = LabJob(
                job_id=str(uuid4()),
                status="running",
                request=request,
                created_at=utc_now(),
            )
            self.jobs[job.job_id] = job
            self.keys[key] = (body, job.job_id)
            self.worker = threading.Thread(
                target=self._run, args=(job,), daemon=True, name="truss-lab-job"
            )
            self.worker.start()
            return job

    def _run(self, job):
        process = None
        try:
            # No MQTT credentials, run manifests or user tokens in the child's environment.
            env = {
                key: os.environ[key]
                for key in ("PATH", "LANG", "PYTHONPATH")
                if key in os.environ
            }
            with self.lock:
                if self.closed:
                    raise ValueError("cancelled")
                process = subprocess.Popen(
                    [sys.executable, "-m", "truss.lab_worker"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                self.process = process
            stdout, stderr = process.communicate(
                job.request.model_dump_json().encode(), timeout=15
            )
            if process.returncode:
                raise ValueError(f"worker_exit_{process.returncode}")
            if len(stdout) > 131072:
                raise ValueError("oversized_worker_output")
            result = BenchmarkResult.model_validate_json(stdout)
            updated = job.model_copy(
                update={
                    "status": "complete",
                    "result": result,
                    "finished_at": utc_now(),
                }
            )
        except Exception as exc:
            if process and process.poll() is None:
                process.kill()
                process.communicate()
            updated = job.model_copy(
                update={
                    "status": "failed",
                    "error": "timeout"
                    if isinstance(exc, subprocess.TimeoutExpired)
                    else str(exc),
                    "finished_at": utc_now(),
                }
            )
        with self.lock:
            self.jobs[job.job_id] = updated
            self.process = None

    def get(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)

    def close(self):
        with self.lock:
            self.closed = True
            if self.process and self.process.poll() is None:
                self.process.kill()
        if self.worker:
            self.worker.join(timeout=3)
