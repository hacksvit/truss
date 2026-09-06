"""M5: one disposable benchmark child with Linux CPU/memory limits and no broker access."""

import json
import os
import sys


def main():
    if sys.platform == "linux":
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (12, 13))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
        os.nice(10)
        allowed = os.sched_getaffinity(0)
        os.sched_setaffinity(0, {max(allowed)})
    from .api_models import LabRequest
    from .lab import benchmark

    raw = sys.stdin.buffer.read(4097)
    if len(raw) > 4096:
        raise ValueError("oversized benchmark input")
    request = LabRequest.model_validate_json(raw)
    print(json.dumps(benchmark(**request.model_dump())), flush=True)


if __name__ == "__main__":
    main()
