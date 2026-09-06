"""Read-only USB screen bridge. Owner M5; no MQTT credentials or control calls."""

import argparse
import re
import time

import httpx

from .api_models import Snapshot

REQUEST = re.compile(rb"TRUSS\? ([0-9a-f]{16})\n")
MAX_HTTP_BYTES = 1_048_576
MAX_DISPLAY_W = 999999


def display_frame(snapshot: Snapshot, nonce: str) -> bytes:
    """Project aggregate data only; -1 means unknown, never measured zero."""
    if not re.fullmatch(r"[0-9a-f]{16}", nonce):
        raise ValueError("Invalid display nonce")
    site = snapshot.site
    observed = site.observed_w
    if (
        site.observed_quality != "fresh"
        or site.oldest_sample_age_ms is None
        or site.oldest_sample_age_ms > 1500
    ):
        observed = None
    for value in (site.cap_w, site.baseline_sum_w, observed):
        if value is not None and not 0 <= value <= MAX_DISPLAY_W:
            raise ValueError("Value exceeds six-digit display range")
    return (
        f"TRUSS1 {nonce} {snapshot.source} {site.state} {site.cap_w} "
        f"{observed if observed is not None else -1} {site.baseline_sum_w} "
        f"{site.coordinator_status}\n"
    ).encode("ascii")


def answer_request(line: bytes, client: httpx.Client, source: str) -> bytes | None:
    """Answer one exact poll using a newly fetched, validated Snapshot."""
    match = REQUEST.fullmatch(line)
    if not match:
        return None
    started = time.monotonic()
    with client.stream("GET", "/api/v1/state", params={"source": source}) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > MAX_HTTP_BYTES or time.monotonic() - started > 0.75:
                raise ValueError("Display fetch exceeded its bound")
    snapshot = Snapshot.model_validate_json(data)
    if snapshot.source != source:
        raise ValueError("Backend source mismatch")
    if time.monotonic() - started > 0.75:
        raise ValueError("Display response arrived too late")
    return display_frame(snapshot, match[1].decode("ascii"))


def main():
    parser = argparse.ArgumentParser(description="Read-only Truss USB status screen")
    parser.add_argument("--port", required=True, help="Explicit USB serial device path")
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--source", choices=("live", "mock"), default="live")
    parser.add_argument(
        "--verbose", action="store_true", help="Print firmware diagnostics"
    )
    args = parser.parse_args()
    try:
        import serial
    except ImportError:
        parser.error(
            "Install the optional display dependency: pip install -e '.[display]'"
        )
    # Explicit port only: do not probe, reset or flash unrelated connected boards.
    with (
        serial.Serial(
            args.port, 115200, timeout=0.2, write_timeout=0.5, exclusive=True
        ) as port,
        httpx.Client(
            base_url=args.url, timeout=0.5, follow_redirects=False, trust_env=False
        ) as client,
    ):
        print(
            "Display bridge ready; aggregate reads only. Ctrl-C stops the bridge.",
            flush=True,
        )
        pending = bytearray()
        overflow = False
        last_error_at = -10.0
        try:
            while True:
                # Partial input persists across serial timeouts. Overlong lines
                # are discarded through the next newline, not treated as a suffix.
                for byte in port.read(128):
                    if byte != 10:
                        if len(pending) >= 64:
                            overflow = True
                        if not overflow:
                            pending.append(byte)
                        continue
                    line = bytes(pending) + b"\n" if not overflow else b""
                    pending.clear()
                    overflow = False
                    if args.verbose and line.startswith(b"TRUSS-DISPLAY "):
                        print(
                            line.decode("ascii", errors="replace").strip(), flush=True
                        )
                    try:
                        frame = answer_request(line, client, args.source)
                        if frame is not None:
                            port.write(frame)
                    except (ValueError, httpx.HTTPError):
                        if time.monotonic() - last_error_at > 5:
                            print(
                                "No valid backend sample; screen will expire to NO DATA.",
                                flush=True,
                            )
                            last_error_at = time.monotonic()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
