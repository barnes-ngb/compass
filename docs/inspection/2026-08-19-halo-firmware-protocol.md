# Inspection report — halo-firmware BLE protocol and Lua runtime

Date: 2026-08-19
Scope: read-only audit of https://github.com/brilliantlabsAR/halo-firmware host-app protocol docs, mapped against compass's `Glasses` Protocol (`src/compass/glasses/base.py`) and ADR 0008/0009.
Method: fetched raw doc files (`applications/halo/PROTOCOL.md`, `BLE_SERVICES.md`, `LUA_RUNTIME.md`, `BUTTON_LED_GUIDE.md`, `PM_SLEEP.md`, `FLASHING.md`, `PAIRING.md`, `README.md`) plus the `samples/halo/` listing. No cloning; nothing vendored.
Upstream revision audited: halo-firmware `main` @ commit `9a306ae7072d84a94f377e1b857d47d30ddaf014` (every fetched file byte-verified against that SHA). All file/section citations below refer to that revision.

---

## Protocol overview

A host app talks to Halo through a **custom GATT "Halo Lua Service"** (`7A230001-…`), not a request/response RPC. Per `applications/halo/PROTOCOL.md` § 3.1, the advertised service carries **LUA RX** (host→device, Write) and **LUA TX** (device→host, Notify), each sized to the negotiated MTU (up to 512) — together a full-duplex **Lua REPL**: the host sends Lua source text; the device replies with execution results (§ 2.2). Binary traffic is multiplexed on the same pair using a one-byte header: `0x01` = user data, `0x02–0x07` = control codes (reboot, interrupt, restart runtime, remove `main.lua`, exit runtime, wipe files) (§ 3.1.2; `BLE_SERVICES.md` § Lua Service → Control Codes). Fragmentation/reassembly is automatic per MTU for the protocol's own traffic, but **user data on the data channel is the app's responsibility to frame and reassemble** (`PROTOCOL.md` § 2.1); device-side sends are capped at MTU−1 (`frame.bluetooth.max_length()`, § 7.5).

`BLE_SERVICES.md` § Lua Service additionally documents **Video** (`7A230004`, Notify, "JPEG video streaming") and **Audio TX** (`7A230006`, Notify, mic capture) characteristics that `PROTOCOL.md` § 3.1.1's table omits, and an **AUDIO RX** (`7A230005`, host→device speaker data). No Lua API for pushing to Video/Audio TX is documented — flagged under Gaps. Other services: standard Battery (`0x180F`), SMP OTA, and standard **LE Audio** (BAP/PACS/VCS/MICS, LC3) (`BLE_SERVICES.md` § LE Audio Service).

**Pairing/bonding** (`PAIRING.md` § 3): LE Secure Connections, Just Works, **5 bond slots, LRU-evicted**; **one connection at a time**. Unknown hosts are rejected unless the ~60 s pairing window is open (5 s button hold) or zero bonds exist (out-of-box = always pairable) (§ 3.2–3.3). For `connect()`: first-time pairing is a physical act on the device; afterwards a bonded host reconnects freely, but is refused if another bonded host holds the link, and is refused *while the pairing window is open*.

## Compass protocol mapping

| Compass method | Verdict | Documented path |
|---|---|---|
| `connect()` / `close()` | ✅ | Scan for Lua service UUID, connect as bonded peer (`PROTOCOL.md` § 4; `PAIRING.md` § 3.2). Upload `halo.lua` as `main.lua` via `frame.file.open("main.lua","w")` over the REPL channel, then `0x04` restart-runtime (§ 3.1.2, § 7.3, § 5). Close = plain BLE disconnect; advertising resumes (`PAIRING.md` § 3.2). |
| `wait_for_trigger()` | ✅ | Two event sources, device-side callbacks relayed by Lua via `frame.bluetooth.send()`: **button** `frame.button.single/double/long` (§ 7.4) and **IMU taps** `frame.imu.tap_callback` firing `'single'/'double'/'triple'` (§ 7.6). Caveats: single tap is reported ~one gesture window late by design (§ 7.6); the `long` callback covers only a 1 s hold released **before 2 s** — 2 s/5 s/15 s holds are firmware-reserved for deep sleep / pairing / ship mode (§ 7.4; `BUTTON_LED_GUIDE.md` § Quick Reference). |
| `capture_image() -> bytes` | ✅ | `frame.camera.capture(cfg)` (async) → poll `image_ready()` → `camera.read(bytes)` returns **complete JPEG data in chunks** (§ 7.11). Lua relays chunks to host over the data channel (§ 7.5). Only `resolution = 640` supported; quality `VERY_HIGH…LOW` ≈ 80/47/25/16 KB (§ 7.11 `camera.capture`). Camera must be woken with `camera.power_save(false)` first. Note: an empty `bluetooth.send("")` transmits nothing, so end-of-image needs a real sentinel byte (§ 7.5 `bluetooth.send`). |
| `show_text(line1, line2, color)` | ✅ | `frame.display.text(text, x, y, color)` with **`0xRRGGBB` color** (§ 7.10). Logical canvas ~256×256 (`display.width()/height()` examples), coordinates 1–256 clamped. Draws render directly — no buffer flip (`display.show` is a no-op, § 7.10). Fonts: Dogica / DogicaBold, sizes in multiples of 8 (`set_font`). Chars-per-line is not documented; verify on hardware. Internally a 16-entry palette exists (`assign_color`), but `text` takes RGB directly. |
| `RollingBuffer` feed (mic → host) | ✅ | `frame.microphone.start{encoder="pcm"\|"lc3", sample_rate=8000\|16000, bit_depth=8\|16 (PCM)}`; LC3 bitrate ≤ 96 kbps, 7.5/10 ms frames (§ 7.9). `microphone.read(≤4096)` is **non-blocking** (empty string until first DMA block; partial reads OK) — Lua pumps chunks to the host via `bluetooth.send()`. Optional AEC and voice-band (~300–3400 Hz) stages, both off by default (§ 7.9). Alternative: standard **LE Audio BAP source stream** (LC3, 8–48 kHz; `BLE_SERVICES.md` § Supported Codec Configurations), which **preempts** `frame.microphone` (§ 3.1.3 "LE Audio precedence"). Stop = `microphone.stop()`; standby/light-sleep clears the ring buffer (§ 7.9 startup-latency note). |
| Speaker (future verbal mode) | ✅ (unused) | Host→device audio over AUDIO RX characteristic (§ 3.1.1); `frame.speaker.start/play/stop`, PCM or LC3, 8/16 kHz (§ 7.8); plus LE Audio sink and an on-device SFXR sound-effect module (§ 7.12). |

## Lua runtime surface for compass's on-device app

Everything the ADR 0009 `halo.lua` sketch needs exists, with shape differences:

- **Startup text**: `main.lua` runs at boot/runtime-restart; `frame.display.text(...)` immediately (`PROTOCOL.md` § 7.10; `LUA_RUNTIME.md` § API Modules).
- **Tap / hold notify**: `frame.button.*` and `frame.imu.tap_callback` are **callback-registered**, so `main.lua` is an event loop calling `frame.yield()`/`sleep()` (§ 7.1), not linear code. The whole API is aliased as `halo == frame` (`LUA_RUNTIME.md` § API Modules).
- **Hold shaped differently than assumed**: ADR 0009 §2 assumed "button-hold (>500 ms) = retro". The documented long-press is a **1 s hold released before 2 s**; anything ≥2 s is firmware-owned (`PROTOCOL.md` § 7.4). Double-tap (`imu` or `button`) is the safer retro trigger.
- **Render host text**: `frame.bluetooth.receive_callback(func)` delivers data-channel payloads (§ 7.5); compass defines its own tiny framing (text+color in, JPEG/audio chunks out).
- **Relay capture/audio**: `camera.read`/`microphone.read` are chunked, non-blocking pulls the loop forwards over `bluetooth.send` — matching § 7.9/7.11 examples.
- **Sleep/power**: `frame.standby()` suspends and **resumes in place**, BLE kept; `light_sleep()` keeps BLE but **restarts `main.lua` from the top** (check `frame.wakeup_source()` at startup); `sleep()` drops BLE (§ 7.1; `PM_SLEEP.md` § Sleep Modes). `stay_awake(true)` exists for active sessions.
- Inconsistency: `LUA_RUNTIME.md` § IMU shows `imu.accelerometer_callback`/`gyroscope_callback`, absent from `PROTOCOL.md` § 7.6. Treat `PROTOCOL.md` as authoritative; verify.

## June 2026 evaluation: confirmed vs corrected

**Confirmed at the source:**
- **Complete JPEG bytes reach the host** — `camera.read()` returns JPEG data that Lua relays over BLE (`PROTOCOL.md` § 7.11). This also retires `docs/landscape.md`'s May suspicion that camera bytes are deliberately withheld.
- **PCM and LC3 mic audio**, 8/16 kHz, with documented LC3 framing (§ 7.9); LE Audio adds 32/48 kHz source configs (`BLE_SERVICES.md`).
- **Color HUD text** with per-call `0xRRGGBB` (§ 7.10).
- **Tap events** — hardware single/double/triple tap detection with a tunable detector (§ 7.6).
- Python host story: `pip install brilliant-sdk` (= `brilliant-ble` + `brilliant-msg`) is the documented debug path (§ 8.2.2), consistent with ADR 0009's host choice.

**Corrected:**
- **Hold gesture**: ">500 ms hold" for retro is not available; long-press is the 1–2 s slot only (§ 7.4).
- **On-device RAM**: ADR 0009 §3 cites "~2 MB SRAM"; `LUA_RUNTIME.md` § Memory Management documents **1.5 MB internal + 7.5 MB external SRAM**. Host-side buffering remains the right call for a 30-min buffer, but the constraint was overstated (5 min of 16 kbps LC3 ≈ 600 KB would fit).
- **Camera resolution**: only **640 px** capture is supported today (§ 7.11) — do not assume Frame-like 1280×720.
- The June "`RxAudio`" framing was `frame-msg`-lineage inference; the firmware defines raw channels (data channel or LE Audio), and whatever `brilliant-msg` classes exist sit above them — verify against that repo when writing `HaloGlasses`.

## Gaps and questions for hardware day

Hardware-only verification: end-to-end capture→host latency for a ~25–47 KB JPEG over the data channel (OTA reference point: ~384 bytes/packet, `FLASHING.md` § Flash); worn tap reliability and effective single-tap delay vs. the gesture window; mic first-read latency after `start()`/standby; real chars-per-line per font size; camera exposure quality (no AE/AWB controls documented).

For the Brilliant Discord:
1. What writes the **Video (`7A230004`) and Audio TX (`7A230006`)** characteristics — is there a firmware-driven streaming mode host apps should prefer over Lua-pumped `bluetooth.send()` for JPEG/mic data? Not documented.
2. Is `brilliant-msg` the intended framing layer over the `0x01` data channel, and does it ship camera/audio message classes for Halo? Not documented in the firmware repo.
3. Are `imu.accelerometer_callback`/`gyroscope_callback` (in `LUA_RUNTIME.md`) real, or stale docs?
4. Recommended host-side LC3 decoder for the custom channel (not LE Audio)?

## Licensing note

Per the repo `README.md` § Licensing, halo-firmware is deliberately mixed-license: Brilliant Labs code (`applications/halo/`, `modules/halo/`, board, most Halo drivers) is Apache-2.0; Alif Semiconductor SDK code (`samples/`, `subsys/`, most remaining drivers) is under the Alif Software License Agreement, which restricts use to Alif silicon and forbids copyleft relicensing; vendored third-party code (Lua 5.4 MIT, Dogica font OFL-1.1, Adafruit GFX BSD-3, etc.) is under its own headers, and "the per-file header governs." Compass must not vendor files from this repo; reading and citing it, as this report does, is fine.
