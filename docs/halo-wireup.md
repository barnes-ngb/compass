# Halo wire-in playbook

What to do the day the Halo arrives (~September 2026, ADR 0008/0009) — the
"first-hour playbook" `docs/roadmap.md` Phase 2 calls for. Work it top to
bottom; each step verifies infrastructure the next one needs.

Sources: `docs/inspection/2026-08-19-halo-firmware-protocol.md` (halo-firmware
`main` @ `9a306ae7…`), ADR 0009, and the `TODO(hardware)` markers in
`src/compass/glasses/halo.py` and `halo.lua` — both **pre-hardware sketches
that have never run**. Nothing here is measured; anything not traceable to the
repo or the report is an open question in §6.

Pre-hardware baseline: `python -m pytest` = 23 passed, 1 skipped (`sounddevice`
absent). That number should not drop.

## 0 — Before the box arrives

- **`pip install brilliant-msg`** into the venv and confirm it resolves. ADR
  0009 keeps it out of the project extras, so it stays a manual install — but
  a failed install shouldn't be discovered on hardware day. `cli.py:24` gates
  `GLASSES=halo` on `find_spec("brilliant_msg")`; until it installs, that path
  exits with the install hint.
- **Re-check upstream.** The report pins halo-firmware
  `9a306ae7072d84a94f377e1b857d47d30ddaf014`. As of 2026-08-22 `main` is
  `3a4fd2ea` — two commits ahead, both CI/release tooling, nothing under
  `applications/halo/`. Re-check on the day (`git ls-remote
  https://github.com/brilliantlabsAR/halo-firmware refs/heads/main`); if the
  protocol docs moved, **re-read the changed sections before debugging
  anything** — a stale citation looks exactly like a driver bug.
- **Firmware version on the shipped device.** The driver was written against
  brilliant-msg docs claiming a true-up to firmware 0.8.8 (`halo.py:6`).
  Record what ships and whether it matches.
- **`.env` ready:** `GLASSES=halo`, plus `ANTHROPIC_API_KEY`,
  `VISION_PROVIDER=claude`, `COACH_PROVIDER=claude`, and for verbal/retro
  `AUDIO_BUFFER=laptop`, `STT_PROVIDER=whisper` (`config.py:52`).
  `CAMERA_INDEX` is mock-only. Keep the `mock` values one toggle away.

## 1 — Isolate the SDK before involving compass

Do **not** start with `python -m compass`. Get a standalone `brilliant-msg`
script working first: connect → render text → disconnect. Take it from the
`brilliant_sdk` examples (ADR 0009 Cross-references) rather than writing one —
run code Brilliant knows works.

Rationale: if compass then fails, this separates *"the SDK or the device is
the problem"* from *"the compass driver is the problem."* Without it, every
later failure has two suspects.

Record: pairing friction (first pairing is a physical 5 s button hold opening
a ~60 s window; one host at a time, 5 LRU bond slots — §PAIRING 3.2/3.3),
connect latency, and anything the docs did not prepare you for.

## 2 — The `TODO(hardware)` list, in dependency order

Every marker, with file and line. Work the groups in this order.

**2.1 `connect()` / `close()`** — `halo.py:171` (RxPhoto/RxTap import path),
`:193` (is `upload_stdlua_libs(['data','sprite'])` needed first?), `:199`
(does `RxTap().attach(msg)` return an `asyncio.Queue`?), `:89` (does
brilliant-msg tolerate one private loop on a daemon thread?), `:257` (how does
disconnect surface?), `halo.py:31` / `halo.lua:67` (#6: is the msg code byte 1
of the Lua payload, and do compass's `MSG_*` codes collide?), `halo.lua:115`
(#1: registration shape for `frame.button.single/double` and
`frame.imu.tap_callback`).
*Run:* `HaloGlasses().connect()` in a REPL. *Success:* "compass ready" on the
HUD (`halo.lua:126`) — proves upload + runtime restart + render in one shot.
*Failure:* no HUD text and no exception means the app uploaded and died; an
exception self-cleans (`halo.py:180`) — read which await raised.

**2.2 `show_text()`** — `halo.py:61` (chars-per-line), `halo.lua:28` (#4: no
documented way to clear drawn text; `display.show` is a no-op), `halo.lua:33`
(#7: host→device payloads over one MTU need app-side reassembly; compass
assumes single-chunk). Cheapest full-chain check: host → BLE → Lua → render.
*Run:* `show_text()` with long strings and every name in `COLORS`
(`halo.py:38`). *Record:* real chars-per-line at the font `halo.lua` sets,
versus the 28/32 from `MockGlasses` (`mock.py:115-116`) and the 30 assumed at
`halo.py:65-66`; whether successive draws overwrite or smear. *Failure:*
garbled ⇒ framing offset (#6); nothing ⇒ codes or connection.

**2.3 `wait_for_trigger()`** — `halo.py:276` (does RxTap yield `str` or
`bytes`?), plus `halo.lua:115` (#1) if 2.1 left it open. ADR 0009 §2's
">500 ms hold = retro" is already replaced by double-tap (`halo.lua:8-12`);
confirm it works worn, and measure the documented single-tap delay of ~one
gesture window (§7.6). *Record:* which gesture actually fires, false-positives
while walking, whether button and IMU both report. *Failure:* no taps ⇒
callback registration; wrong kind ⇒ the `last_trigger_kind` mapping
(`halo.py:284-290`).

**2.4 `capture_image()`** — `halo.py:308` (does RxPhoto yield assembled bytes,
and does the Lua sentinel match its final-chunk rule?), `:108` (is `MEDIUM` a
sensible default?), `halo.lua:88` (#2: `camera.capture` cfg keys),
`halo.lua:94`/`:98` (#3: `camera.read` end-of-data convention and the `"\x00"`
sentinel). *Success:* bytes that open as a JPEG. *Record:* actual resolution
(only 640 is supported — §7.11), quality vs size across `QUALITY_LEVELS`,
capture→host latency. *Failure:* truncated JPEG ⇒ sentinel (#3); a hang to
`capture_timeout_s` ⇒ the request never reached Lua.

**2.5 Audio → `RollingBuffer`** — `halo.lua:35` (#8: mic first-read latency
after `start()`, and whether `pcm`/16 kHz/16-bit at `halo.lua:77` is right),
`halo.lua:30` (#5: `frame.yield()` vs a short sleep — cadence vs power). Note
nothing wires `MSG_AUDIO` into a `RollingBuffer` yet: `halo.py` defines the
code but implements no feed. *Record:* format, sample rate, drops, and whether
the host ring buffer (`audio/laptop_mic.py`) needs changes for a chunked BLE
source rather than a local mic.

## 3 — First end-to-end run per mode

Simplest chain first. Compare each against the laptop baselines already
measured, and expect BLE round-trips plus on-device capture on top (ADR 0009's
glasses budgets: visual ~5–10 s, retro ~12–22 s).

1. **Visual** — `$env:GLASSES="halo"; python -m compass --mode visual`.
   Baseline ~2 s to HUD on mock (`docs/architecture.md` §Latency budget); new
   on Halo are BLE trigger, on-device JPEG, BLE image transfer.
2. **Verbal** — add `$env:AUDIO_BUFFER="laptop"; $env:STT_PROVIDER="whisper"`;
   `--mode verbal`.
3. **Retro** — same env, `--mode retro`. Baseline 12–22 s press-to-HUD with
   `small.en` (`docs/architecture.md` §Retro).

**Mic question — answer it deliberately.** Keep audio on the laptop mic
(`AUDIO_BUFFER=laptop`) for the first run: the Halo path is then only trigger
+ display + camera, all verified in §2. Halo's mics add the §2.5 unknowns
*and* the LE-Audio-versus-`frame.microphone` precedence question at once.
Switch only once all three modes run green on the laptop mic.

## 4 — Failure triage

| Symptom | First question | Likely cause |
|---|---|---|
| §1 script also fails | — | Device, pairing, or SDK — not compass |
| §1 works, `connect()` doesn't | Does "compass ready" show? | No ⇒ Lua upload/start (2.1); yes ⇒ Rx attach (`halo.py:199`) |
| HUD text garbled | Right chars, wrong layout? | Framing offset (#6) or chars-per-line (`halo.py:61`) |
| Taps never arrive | Does the LED/button respond at all? | Callback registration (#1) vs RxTap payload type (`halo.py:276`) |
| JPEG truncated / never completes | Any bytes at all? | Sentinel mismatch (#3) vs capture cfg keys (#2) |
| Worked yesterday, not today | Did firmware or `brilliant-msg` update? | Version drift — re-check §0 |

**Standing rollback:** `GLASSES=mock` is the default (`config.py:69`) and
depends on no hardware. A broken Halo path never blocks other work — fall
back, keep building, return with a narrower question.

## 5 — What to write down

Measurements become follow-up PRs or an ADR postscript, never a silent edit:

- Measured latencies per mode against ADR 0009's budgets. A blown budget is
  ADR 0009's re-evaluation trigger and a `docs/roadmap.md` Phase 2 exit
  criterion — a decision point, not a silent failure.
- Real display constraints (chars-per-line, clearing) → replaces the 28/30
  constants at `halo.py:65-66`.
- Gesture behavior worn, including the single-tap delay.
- Anything the inspection report got wrong → a new dated report in
  `docs/inspection/`, not an edit to the 2026-08-19 one.
- ADR 0009's assumptions (RAM, hold gesture, `RxAudio` framing) get a
  **postscript**, not a rewrite — an accepted ADR records what was decided and
  why, including where it was wrong.

## 6 — Open questions

Answerable on hardware day or in the Brilliant Discord. The first four are the
report's own unanswered questions.

1. What writes the Video (`7A230004`) and Audio TX (`7A230006`)
   characteristics — is there a firmware-driven streaming mode to prefer to
   Lua-pumped `bluetooth.send()` for JPEG and mic data?
2. Is `brilliant-msg` the intended framing layer over the `0x01` data channel,
   and does it ship camera/audio message classes for Halo?
3. Are `imu.accelerometer_callback` / `gyroscope_callback` (in
   `LUA_RUNTIME.md`, absent from `PROTOCOL.md` §7.6) real, or stale docs?
4. Recommended host-side LC3 decoder for the custom channel (not LE Audio)?
5. Real chars-per-line per font size — and **how do you clear text already
   drawn**, when `display.show` is a no-op (#4)?
6. Do `RxTap` / `RxPhoto` exist at the assumed import path, and what does
   `attach()` return (`halo.py:171`, `:199`)?
7. Does `brilliant-msg` tolerate being driven from one long-lived loop on a
   non-main thread (`halo.py:89`)?
8. Do compass's `MSG_*` codes collide with brilliant-msg's reserved ones, and
   is the code byte 1 of the Lua payload (`halo.py:31`, #6)?
9. `camera.read`'s end-of-data convention, and what `RxPhoto` treats as the
   final chunk (#3)?
10. Mic first-read latency after `start()` — and does the LE Audio BAP source
    (which preempts `frame.microphone`) beat the Lua-pumped path (#8)?
