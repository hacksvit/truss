"""M2: owned local Mosquitto/member/plant/coordinator lifecycle and private run files."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import threading
from pathlib import Path
from uuid import uuid4
from .config import load_run, load_member
from .supervisor import Supervisor
from .authority_store import AuthorityStore


def broker_binary():
    candidate = os.environ.get("TRUSS_MOSQUITTO") or shutil.which("mosquitto")
    if not candidate:
        # The Heroku Apt buildpack unpacks packages beneath /app/.apt. Its
        # profile script adds usr/bin, but Mosquitto itself is installed in
        # usr/sbin and therefore is not found by shutil.which().
        apt_roots = (Path.cwd() / ".apt", Path("/app/.apt"), Path.home() / ".apt")
        for root in apt_roots:
            for directory in ("usr/sbin", "usr/bin"):
                packaged = root / directory / "mosquitto"
                if packaged.is_file():
                    candidate = str(packaged)
                    break
            if candidate:
                break
    if not candidate:
        local = Path.home() / ".cache/truss-deps/arch/usr/bin/mosquitto"
        if local.exists():
            candidate = str(local)
    if not candidate:
        raise RuntimeError(
            "Mosquitto unavailable. Install it or set TRUSS_MOSQUITTO; no mock fallback."
        )
    return Path(candidate).resolve()


def broker_password_binary(broker):
    """Find mosquitto_passwd next to a system or Apt-buildpack broker."""
    candidates = (
        broker.parent / "mosquitto_passwd",
        broker.parent.parent / "bin" / "mosquitto_passwd",
        broker.parent.parent / "sbin" / "mosquitto_passwd",
    )
    return next(
        (path for path in candidates if path.is_file()),
        Path(shutil.which("mosquitto_passwd") or ""),
    )


class TrussRun:
    def __init__(self, config_dir="config", runtime_root="runtime", broker_port=18883):
        self.config_dir = Path(config_dir).resolve()
        self.policy = load_run(self.config_dir / "run.json")
        for m in self.policy.members:
            load_member(self.config_dir / f"{m.member_id}.json", m)
        self.policy = self.policy.model_copy(update={"run_id": str(uuid4())})
        self.directory = Path(runtime_root).resolve() / self.policy.run_id
        self.directory.mkdir(parents=True, mode=0o700)
        self.port = broker_port
        self.supervisor = Supervisor()
        self.argv = {}
        self.logs = {}
        self.action_lock = threading.Lock()
        self.binary = broker_binary()
        self.environment = os.environ.copy()
        lib = self.binary.parent.parent / "lib"
        if (lib / "libmosquitto.so.1").exists():
            self.environment["LD_LIBRARY_PATH"] = str(lib) + (
                os.pathsep + self.environment["LD_LIBRARY_PATH"]
                if self.environment.get("LD_LIBRARY_PATH")
                else ""
            )
        self.manifest_path = self.directory / "manifest.json"

    def snapshot_profiles(self):
        directory = self.directory / "profiles"
        directory.mkdir(mode=0o700, exist_ok=True)
        for member in self.policy.members:
            profile = load_member(self.config_dir / f"{member.member_id}.json", member)
            path = directory / f"{member.member_id}.json"
            path.write_text(profile.model_dump_json(indent=2))
            path.chmod(0o600)
        return directory

    def prepare(self):
        from secrets import token_urlsafe

        private_profiles = self.snapshot_profiles()
        roles = (
            ["coordinator", "evidence", "api-control"]
            + [m.member_id for m in self.policy.members]
            + [
                "plant-" + m.member_id.removeprefix("member-")
                for m in self.policy.members
            ]
        )
        credentials = {name: token_urlsafe(24) for name in roles}
        credentials_path = self.directory / "credentials.json"
        credentials_path.write_text(json.dumps(credentials))
        credentials_path.chmod(0o600)
        passwords = self.directory / "passwords"
        passwords.write_text(
            "".join(f"{name}:{password}\n" for name, password in credentials.items())
        )
        passwords.chmod(0o600)
        passwd = broker_password_binary(self.binary)
        result = subprocess.run(
            [str(passwd), "-U", str(passwords)],
            env=self.environment,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(
                "Broker password conversion failed; inspect installed mosquitto_passwd compatibility"
            )
        acl = self.directory / "acl"
        acl.write_text(
            (self.config_dir / "acl")
            .read_text()
            .replace("hostel-demo", self.policy.site_id)
        )
        policy_path = self.directory / "run.json"
        policy_path.write_text(self.policy.model_dump_json(indent=2))
        broker_config = self.directory / "mosquitto.conf"
        broker_config.write_text(
            f"listener {self.port} 127.0.0.1\nallow_anonymous false\npassword_file {passwords}\nacl_file {acl}\npersistence false\nmax_packet_size 131072\nmax_queued_messages 1024\nlog_type warning\n"
        )
        authority = self.directory / "authority.sqlite"
        store = AuthorityStore(authority)
        store.set(
            "control",
            {"revision": 1, "cap_w": self.policy.cap_w, "rule": "equal_surplus"},
        )
        store.close()
        manifest = dict(
            run_id=self.policy.run_id,
            runtime_dir=str(self.directory),
            config_dir=str(private_profiles),
            policy_path=str(policy_path),
            credentials_path=str(credentials_path),
            authority_path=str(authority),
            broker_port=self.port,
            broker_binary=str(self.binary),
            pid=os.getpid(),
        )
        self.manifest_path.write_text(json.dumps(manifest, indent=2))
        self.manifest_path.chmod(0o600)
        self.argv["broker"] = [str(self.binary), "-c", str(broker_config)]
        for member in self.policy.members:
            for role in ("plant", "member"):
                self.argv[f"{role}:{member.member_id}"] = [
                    sys.executable,
                    "-m",
                    "truss.process_entry",
                    role,
                    str(self.manifest_path),
                    member.member_id,
                ]
        self.argv["coordinator"] = [
            sys.executable,
            "-m",
            "truss.process_entry",
            "coordinator",
            str(self.manifest_path),
        ]

    def start_child(self, name):
        log = self.logs.get(name)
        if log is None:
            log = (self.directory / (name.replace(":", "-") + ".log")).open(
                "ab", buffering=0
            )
            self.logs[name] = log
        return self.supervisor.start(
            name, self.argv[name], stdout=log, stderr=log, env=self.environment
        )

    def start(self):
        self.prepare()
        try:
            self.start_child("broker")
            deadline = time.monotonic() + 5
            while True:
                if self.supervisor.children["broker"].poll() is not None:
                    raise RuntimeError(
                        f"Broker exited; inspect {self.directory}/broker.log"
                    )
                try:
                    with socket.create_connection(
                        ("127.0.0.1", self.port), timeout=0.2
                    ):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        raise RuntimeError("Broker readiness timeout")
                    time.sleep(0.05)
            for m in self.policy.members:
                self.start_child("plant:" + m.member_id)
            for m in self.policy.members:
                self.start_child("member:" + m.member_id)
            self.start_child("coordinator")
            self.write_processes()
            return self.manifest_path
        except BaseException:
            self.close()
            raise

    def write_processes(self):
        (self.directory / "processes.json").write_text(
            json.dumps(
                {
                    name: dict(pid=p.pid, exit_code=p.poll())
                    for name, p in self.supervisor.children.items()
                },
                indent=2,
            )
        )

    def act(self, action, member_id=None):
        with self.action_lock:
            return self._act(action, member_id)

    def _act(self, action, member_id=None):
        if action in ("kill_coordinator", "restart_coordinator"):
            name = "coordinator"
        elif action in ("kill_broker", "restart_broker"):
            name = "broker"
        elif action in ("kill_member", "restart_member") and member_id in {
            m.member_id for m in self.policy.members
        }:
            name = "member:" + member_id
        else:
            raise ValueError("unsupported real-process action or unknown member")
        if action.startswith("kill_"):
            self.supervisor.stop(name, abrupt=True)
        else:
            self.supervisor.stop(name)
            self.start_child(name)
        self.write_processes()

    def validate_fault(self, target, action, duration_ms=8000, delay_ms=0, rate=1.0):
        from .faults import DeliveryFault

        if (target not in self.argv or target == "broker") and target != "evidence":
            raise ValueError("unknown fault target")
        if not 0 < duration_ms <= 30000:
            raise ValueError("fault duration exceeds 30 s")
        fault = DeliveryFault(
            action, time.monotonic_ns() + duration_ms * 1_000_000, rate, delay_ms
        )
        if action == "delay_grants" and not target.startswith("member:"):
            raise ValueError("delay_grants requires member target")
        return fault

    def set_fault(self, target, action, duration_ms=8000, delay_ms=0, rate=1.0):
        with self.action_lock:
            return self._set_fault(target, action, duration_ms, delay_ms, rate)

    def _set_fault(self, target, action, duration_ms, delay_ms, rate):
        fault = self.validate_fault(target, action, duration_ms, delay_ms, rate)
        path = self.directory / "faults.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"target": target, **fault.__dict__}))
        os.replace(temporary, path)

    def close(self):
        # Stop issuer first; member stop cannot stop its plant. Whole-run teardown
        # then ends virtual plants and broker explicitly, never as a safety claim.
        for name in (
            ["coordinator"]
            + [n for n in self.supervisor.children if n.startswith("member:")]
            + [n for n in self.supervisor.children if n.startswith("plant:")]
            + ["broker"]
        ):
            if name in self.supervisor.children:
                self.supervisor.stop(name)
        for log in self.logs.values():
            log.close()
