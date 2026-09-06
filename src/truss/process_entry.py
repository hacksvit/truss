"""M2: internal named process entrypoint; launched only by the local supervisor."""

import sys


def main():
    role, manifest, *member = sys.argv[1:]
    if role == "coordinator":
        from .coordinator_process import run

        run(manifest)
    elif role == "member":
        from .member_process import run

        run(manifest, member[0])
    elif role == "plant":
        from .plant_process import run

        run(manifest, member[0])
    else:
        raise ValueError("unknown process role")


if __name__ == "__main__":
    main()
