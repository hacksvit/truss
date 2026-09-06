"""M2: optional pinned Arch x86_64 dependency unpack; no root/system install."""

import hashlib
import platform
import subprocess
import urllib.request
from pathlib import Path

PACKAGES = {
    "cjson-1.7.19-1-x86_64.pkg.tar.zst": "a6f4cff724d7dfc0661c313680945c17c8416ef1d42c0ecd9c8be5feb7e1e90d",
    "mosquitto-2.1.2-2-x86_64.pkg.tar.zst": "c98660e6b17f81e73c7a7b10ff537d667bdaad8ef4729fedca848e7438d79987",
}


def main():
    if (
        platform.machine() != "x86_64"
        or "ID=arch" not in Path("/etc/os-release").read_text()
    ):
        raise SystemExit(
            "This helper is for the inspected Arch x86_64 host. Install Mosquitto using your OS package manager elsewhere."
        )
    directory = Path.home() / ".cache/truss-deps/arch"
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in PACKAGES.items():
        archive = directory / name
        if not archive.exists():
            urllib.request.urlretrieve(
                "https://fastly.mirror.pkgbuild.com/extra/os/x86_64/" + name, archive
            )
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Dependency archive hash mismatch: " + name)
        subprocess.run(
            ["tar", "--zstd", "-xf", str(archive), "-C", str(directory)],
            check=True,
            capture_output=True,
        )
    print(
        "Mosquitto dependency ready in the local user cache. No system service was installed."
    )


if __name__ == "__main__":
    main()
