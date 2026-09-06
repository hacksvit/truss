"""Own-child process lifecycle only. Owner M2. Never kill arbitrary machine PIDs."""

import subprocess
from collections.abc import Sequence


class Supervisor:
    def __init__(self):
        self.children: dict[str, subprocess.Popen] = {}

    def start(self, name: str, argv: Sequence[str], **popen_options) -> int:
        if name in self.children and self.children[name].poll() is None:
            raise ValueError("already running")
        child = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL, **popen_options)
        self.children[name] = child
        return child.pid

    def stop(self, name: str, abrupt: bool = False):
        child = self.children[name]
        if child.poll() is None:
            child.kill() if abrupt else child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)

    def close(self):
        for name in self.children:
            self.stop(name)
