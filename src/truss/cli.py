"""Local development entry points. Owner M2; no invisible mock fallback."""

import argparse
import json
from .config import load_run, load_member


def main():
    parser = argparse.ArgumentParser(
        description="Truss: shared-capacity protocol scaffold"
    )
    parser.add_argument(
        "command", choices=["mock", "api", "live", "check-config", "lab"]
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--members", type=int, default=50)
    parser.add_argument("--broker-port", type=int, default=18883)
    args = parser.parse_args()
    if args.command == "check-config":
        from pathlib import Path

        policy = load_run(Path(args.config_dir) / "run.json")
        for member in policy.members:
            load_member(Path(args.config_dir) / f"{member.member_id}.json", member)
        print(
            f"Valid: {len(policy.members)} households; baselines and protected maxima fit."
        )
    elif args.command == "lab":
        from .lab import benchmark

        print(json.dumps(benchmark(args.members), indent=2))
    elif args.command == "live":
        import uvicorn
        from .runtime import TrussRun
        from .observer import LiveState
        from .api import create_app

        run = TrussRun(args.config_dir, broker_port=args.broker_port)
        observer = None
        try:
            run.start()
            observer = LiveState(run)
            observer.start()
            print(
                f"Live virtual processes ready. Manifest: {run.manifest_path}",
                flush=True,
            )
            uvicorn.run(create_app(observer), host=args.host, port=args.port)
        finally:
            if observer:
                observer.close()
            run.close()
    else:
        import uvicorn
        from .api import create_app
        from .mock import MockState

        uvicorn.run(
            create_app(MockState(args.config_dir) if args.command == "mock" else None),
            host=args.host,
            port=args.port,
        )


if __name__ == "__main__":
    main()
