# Optional ESP32 status screen

**Decision:** use the existing round screen as a read-only witness to the PC's virtual demonstration. It does not act as a member, planner, meter, relay or lease enforcer. Removing the board or stopping its bridge cannot change allocations. This adds a presentation peripheral after B11; it replaces no backend component and needs no AI, Wi-Fi credentials or new electronic components.

## Hardware findings and evidence

Verified from the user's local `/home/medrid/ccode/platformio.ini` and `src/utils/face_controller.h` on 6 September 2026:

| Item | Existing configuration |
|---|---|
| Board | ESP32-S3, configured for N16R8: 16 MB flash, 8 MB PSRAM, QIO/OPI |
| Screen | 1.28-inch round GC9A01, 240 × 240, SPI |
| Power | VCC → 3V3; GND → GND, as documented in the existing project |
| SCL / SDA | GPIO12 clock / GPIO11 MOSI; these labels refer to SPI here |
| DC / CS / RST | GPIO13 / GPIO10 / GPIO14 |
| Display dependency | Arduino_GFX 1.4.9, Arduino ESP32 core 2.0.17 |
| Serial | 115200 baud; existing USB adapter ID `usb-1a86_USB_Single_Serial_5C38119516-if00` is currently enumerated locally |
| Current application | `main.cpp` enables `face_controller`; its Truss logo animation is present but disabled |

These verify what the files configure, not the physical module marking, current wiring or what was last flashed. The old default uploader targets a separate homelab; the new project intentionally has no remote uploader. The serial adapter's presence alone does not prove its attached screen works.

Primary dependency references: [PlatformIO ESP32 platform and board overrides](https://docs.platformio.org/en/latest/platforms/espressif32.html), [Arduino_GFX controller support](https://github.com/moononournation/Arduino_GFX), [Espressif DevKitC documentation](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp-dev-kits-en-master-esp32s3.pdf). Board defaults describe an N8 variant; the explicit overrides preserve the user's N16R8 configuration. Do not interpret the default board name as detection of actual flash/PSRAM.

**Assumptions:** the documented screen wiring is still accurate. USB access and a successful local upload were subsequently verified with the connected board; the physical screen has not been visually inspected. Touch input and extra LEDs/buttons are not assumed. New application firmware is written in `firmware/status-display/`; no face/logo/other project implementation was copied from `ccode`. Wiring facts and public dependency choices were used as configuration references.

## What appears on the screen

- `VIRTUAL LIVE`, `MOCK DEMO` or `REPLAY` is always visible while a sample is current. The bridge CLI permits only live/mock today.
- `CAP`: currently requested site cap, which may still be in transition.
- `DRAW`: fresh observed total from virtual plants, or `UNKNOWN`. This is not a reading from a physical electricity meter.
- `BASE`: registered floor total, including protected/unclassified reservations. This is a configuration value, not evidence that critical appliances are currently powered.
- State and coordinator status: `leased`, `recovering`, `cap_transition`, `infeasible`, `unverified`, etc.
- Red marks infeasibility or an observed over-cap value; amber marks uncertainty/transition; cyan marks an ordinary current leased view. No color certifies safety.
- `NO DATA` replaces the values when the screen lacks a current reply. Coordinator failure can still yield current data because the observer and virtual plants continue independently.

The renderer uses a single 115,200-byte RGB565 canvas to avoid clearing the visible panel between text updates. It has no network stack or actuator pins. If display initialization fails, polling continues but no visual result is claimed.

## Files, interfaces and owners

| File | Public interface | Dependencies | Owner |
|---|---|---|---|
| `firmware/status-display/platformio.ini` | `pio run --project-dir firmware/status-display`; explicit USB upload | Espressif platform 7.1.0, Arduino_GFX 1.4.9 | M2 |
| `firmware/status-display/include/status_protocol.h` | `Receiver.request(now, boot, sequence)`, `nonce()`, `accept(line, now)`, `tick(now)`, `fresh(now)`, read-only use of `frame` | C/C++ library only | M2 |
| `firmware/status-display/src/main.cpp` | Arduino `setup()` and `loop()` | Above receiver, Arduino_GFX, Arduino Serial, ESP random boot token | M2 |
| `firmware/status-display/tests/protocol_test.cpp` | Native test executable; invoked by pytest | Header, C++11 compiler | M2 |
| `src/truss/display_bridge.py` | `display_frame(snapshot, nonce)`, `answer_request(line, client, source)`, `truss-display` CLI | Existing Snapshot, HTTPX, optional pyserial 3.5 | M5 |
| `tests/test_display_bridge.py` | Projection/HTTP rejection and native parser tests | pytest, HTTPX mock transport, g++ | M5 |

M2 can build/test the screen parser against an authored reply. M5 can verify the bridge with a pseudo-terminal and current mock API. Neither waits for frontend changes. Handoff: M5 supplies the ASCII contract below; M2 verifies a compiled firmware before any upload. The physical upload and serial checks passed; visual screen inspection is still pending.

## Exact USB contract

115200 baud, 8 data bits, no parity, 1 stop bit, newline terminated ASCII, no carriage return. Maximum response is 127 bytes excluding newline; overlong/non-printable input is discarded through its newline. Each second the board emits:

```text
TRUSS? 0123456700000001
```

The nonce is exactly 16 lowercase hexadecimal characters: a random 32-bit boot token and a 32-bit increasing poll sequence. The PC performs one new `GET /api/v1/state?source=live` (or mock), validates the existing Snapshot and replies:

```text
TRUSS1 0123456700000001 live leased 5000 4900 900 online
```

Fields, in order: literal protocol version; echoed nonce; source; site state; cap watts; observed watts; baseline watts; coordinator status. The source/state/coordinator enums are the Snapshot enums. Watts are unsigned decimal integers from 0–999999; observed alone permits `-1` for unknown. No household/device names, offers or authority messages go over USB. The bridge internally reads the privileged local operator Snapshot, which does contain demo device details; this is an output projection, not a new household privacy boundary.

The board accepts only its current pending poll and consumes it once. A new poll replaces the pending nonce. A valid frame is fresh for 2500 ms **from the board's request**, not from reply receipt; duplicate, wrong-boot, old-poll and late replies cannot extend it. Unsigned elapsed-time subtraction handles millis rollover, and expiry latches in the running loop. Painting runs every 250 ms, so NO DATA appears on the next repaint after expiry. This is display freshness only: a frozen CPU/screen cannot repaint itself and is not evidence of protocol failure or success.

Diagnostic lines start with `TRUSS-DISPLAY`: READY/INIT_FAILED at setup, ACCEPT followed by the consumed nonce, and NO_DATA when a previously fresh view expires during painting. The bridge ignores these as polls; `--verbose` prints them for hardware checking. An ACCEPT records parser acceptance, not optical confirmation of the screen pixels.

Bridge reads have a 0.5 s per-I/O HTTP timeout, 0.75 s elapsed-time check and 1 MiB body cap. It never forwards an expired fetch, a wrong-source response or an invalid Snapshot. It performs no POST, MQTT operation or serial upload. Local HTTP stays bound to loopback. Untrusted serial packets may at most change this non-authoritative display; random tokens are stale-buffer protection, not authentication.

## Build, upload and run

From the Truss repository root:

```bash
.venv/bin/python -m pip install -e '.[display]'
pio run --project-dir firmware/status-display
.venv/bin/pytest -q tests/test_display_bridge.py
```

Install/build dependencies before the offline judging session. Build-only does not modify the ESP32. To deliberately replace its running animation with this new firmware, close any serial monitor and use the explicit device path:

```bash
pio run --project-dir firmware/status-display --target upload --upload-port /dev/serial/by-id/usb-1a86_USB_Single_Serial_5C38119516-if00
```

Then, with the live backend already running on 8001:

```bash
.venv/bin/truss-display --port /dev/serial/by-id/usb-1a86_USB_Single_Serial_5C38119516-if00 --url http://127.0.0.1:8001 --source live
```

For the mock server use port 8000 and `--source mock`; the screen must say MOCK DEMO. Opening a USB serial port may toggle the adapter's reset lines; allow the board to restart before expecting its first poll. There is no auto-upload, auto-port scan or homelab requirement. This optional bridge has its own process; stopping it does not stop the backend.

## Acceptance and 3 a.m. fallback

1. Compile and run the native parser/bridge tests. This proves software cases, not the physical panel.
2. After a deliberate upload, see NO DATA before the bridge starts, then the correctly labelled source and numbers matching `/api/v1/state`.
3. Stop the bridge without unplugging board power: see NO DATA after the request freshness window and repaint. Leave it stopped; it must not regain freshness.
4. Restart the bridge. Kill the coordinator through the console; the screen should report coordinator offline and eventually fresh virtual draw at the configured baseline. The screen's reading is supporting evidence; preserve independent plant logs.
5. Stop the broker: observed draw must become UNKNOWN while the API remains reachable. Stop the API: screen goes to NO DATA. Recovery must restore new evidence rather than replay old USB bytes.

If the board is blank, check the existing wiring, selected USB path, panel initialization and the documented board profile. If upload or display work takes more than 30 minutes, cut the screen and keep the laptop demo. Do not rewire hardware at 3 a.m. to rescue a cosmetic feature. The existing `ccode` project is unchanged; restoring its former firmware is a separate deliberate upload, not an automatic failure action.

**Claim boundary:** “The ESP32 displays our virtual site's status.” Never “The ESP32 protects breathing equipment” or “This screen measures our feeder.” Critical real appliances remain entirely outside this prototype.

## Verified on 6 September 2026

PlatformIO compilation and USB upload succeeded; the uploader verified written hashes. Firmware accepted three live replies containing cap 5000 W, virtual observed 4900 W and baseline 900 W. With subsequent replies withheld, it emitted NO_DATA 2.676 seconds after the final poll (PC-observed serial timing, including repaint/transport). It remained expired while polling continued. This exercises the real board's parser/timer/render path; it is not optical inspection or electrical evidence.

Seven display tests passed, including a natively compiled parser regression covering duplicate/late/wrong-boot replies, malformed values and clock rollover. The three existing API contract tests also passed in the targeted run (10 total). The previous full core backend run remains separately recorded as 38 passed; it was not rerun solely for this optional USB addition.

Raw serial evidence is saved locally in ignored `runtime/display-verification.json`. Firmware SHA-256: `c49f21d875aa8837bedb240beb02da5bc58ae249153735f977bb4dc779852897`. The API's existing `capabilities.hardware=false` continues to mean no hardware appliance adapter; this independent read-only peripheral is not a controlled appliance and its connection is not tracked by the API.
