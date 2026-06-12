# 0009 — Halo language strategy: Python host + minimal Lua, phone deferred

**Status:** Accepted · **Date:** 2026-06-12 · **Supplements:** 0008 (Halo primary, Frame backup)

## Context

The published Halo SDK (https://docs.brilliant.xyz/halo/halo-sdk/, https://github.com/brilliantlabsAR/brilliant_sdk) exposes four programming layers:

| Layer | Where it runs | What it's for | Latency |
|---|---|---|---|
| Lua | On Halo MCU | Reflexes — immediate UI feedback, event filtering, power management | <1ms |
| Python host | Laptop / desktop / server | Heavy lifting — cloud calls, ML, files, persistent state | BLE + cloud RT |
| Flutter host | Phone | Self-contained mobile app pattern | BLE + cloud RT |
| Web Bluetooth host | Chromium browser | Demos, zero-install sharing | BLE + cloud RT |

Compass's existing architecture is 100% Python with mock-first design (ADR 0001), structural typing via `typing.Protocol` (ADR 0002), and a hardware-agnostic `Glasses` abstraction. The natural fit is a Python host with a minimal Lua app on Halo. Flutter and Web Bluetooth solve different problems and are not the right architecture for compass today.

Long-term, the user wants phone-based mobility — using compass walking around an office or shop floor, not just at a desk. Six paths exist to that mobility (laptop, Pi-in-pocket, Termux/Android, phone-as-bridge to cloud Python, Flutter rewrite, Web Bluetooth rewrite). Of these, **phone-as-bridge to cloud Python** preserves the entire existing Python codebase and is the right destination when phone mobility becomes necessary.

## Decision

1. **Host language: Python.** All compass coach logic, STT, Claude calls, memory persistence, and mode dispatch stay in Python. No Flutter rewrite. No Web Bluetooth rewrite. The `brilliant-msg` PyPI package becomes a dependency when hardware arrives.

2. **On-device code: minimal Lua.** Maybe 50–100 lines total. Handles reflexes only:
   - On startup: display "compass ready"
   - On button-tap (single): notify host (maps to `Glasses.wait_for_trigger()` returning True for visual or verbal mode)
   - On button-hold (>500ms): notify host with a "retro" flag (button overload for retro mode)
   - On host message with text + color: render to HUD
   - On host message requesting camera or audio: forward via standard `brilliant-msg` channels
   - Heavy lifting (cloud calls, STT, memory) stays on Python host.

3. **Rolling audio buffer location: host, not on-device.** Compass's existing `LaptopMicBuffer` pattern continues. Halo streams audio to the host via `RxAudio`; the host maintains the RAM-only rolling buffer. On-device buffering on Halo is technically possible but constrained by ~2 MB of SRAM — too short to support compass's "what happened 5 minutes ago" retro mode use case.

4. **On-device NPU (Ethos-U55, ~46 GOPS): not exercised in V0-V1.** The NPU is not exposed for third-party developer models in the current SDK; even if it were, the budget supports only wake-word, simple classification, and gesture detection — not general VLMs. Brilliant's own Liquid AI LFM2-VL runs in their firmware/Noa stack, not in third-party apps. Cloud Claude (Sonnet 4.6) remains the brain.

5. **Phone mobility: deferred.** Build laptop-only for V0-V1. When the laptop-tethering constraint blocks a use case the user actually wants (likely "walking the shop while compass is alive"), build the phone-as-bridge layer. Estimated effort: 2–3 weeks. Phone runs a minimal app whose only job is BLE bridging; all Python code stays on a server. **Compass does not need to refactor its current code to be "server-shaped" today** — the refactor happens when the bridge is built.

6. **Compass repository layout for Halo code:** Lua source for the Halo app lives at `src/compass/glasses/halo.lua`. The `HaloGlasses` Python implementation lives at `src/compass/glasses/halo.py` and uses `brilliant-msg`. Both ship as part of the same package; the Lua file is uploaded to the device on `Glasses.connect()`.

## What would trigger re-evaluation

Not a commitment, just plausible signals:

- The user adopts compass for use cases that require walkaround mobility (shop floor, field installs, meetings outside the office). Trigger to build phone-as-bridge.
- Brilliant Labs ships a third-party-model loader for the Halo NPU. Trigger to evaluate on-device wake-word or VAD.
- Compass's host-side latency budget (visual ~5–10 s, retro ~12–22 s) becomes unacceptable. Trigger to re-evaluate where work runs.
- The Flutter SDK gains capabilities the Python SDK doesn't, or compass needs a feature that's mobile-only (e.g., notifications, deep OS integration). Trigger to consider a thin Flutter companion app.

## Consequences

**Good:**

- Single host language across all of compass. No code duplication.
- Existing Python codebase (Glasses Protocol, RollingBuffer, STT, VisionProvider, CoachProvider, MemoryStore) ports to Halo with no architectural changes.
- The Lua sliver is small enough to write and test in a single session.
- Phone mobility has a clean future path (bridge to cloud Python) without committing to it now.
- Compass remains a Python project; the user's skill set and toolchain stay aligned.

**Bad:**

- Mobility requires either a laptop nearby or building the bridge layer when the time comes (~2–3 weeks of work).
- Phone-only self-contained app pattern (the Flutter route) is not available without significant rewrite.
- Future Halo NPU capabilities (when they're exposed) require additional work to integrate; the current architecture doesn't leverage on-device AI at all.

## Watching

- `brilliant-msg` PyPI for new releases and changelog (Halo-specific examples, breaking changes).
- Brilliant Labs Discord and forum for Halo-related Python examples and shipping updates.
- Brilliant's firmware repo for third-party-model loader work ("coming soon" in current docs).
- Compass usage patterns once hardware arrives: how often does laptop tethering bite?

## Alternatives considered

- **Flutter host (self-contained mobile app).** Rejected: requires rewriting compass's host-side code in Dart. Loses 100% of existing Python work. Right architecture for consumer products, wrong for a Python-first personal tool.
- **Web Bluetooth host.** Rejected: even worse, total rewrite in TypeScript/JavaScript. Useful only for "click this URL to demo" scenarios, which compass doesn't need.
- **Build phone-as-bridge from day one.** Rejected: speculative refactor. Compass works fine on a laptop for V0-V1 use cases. Add the bridge when there's a real reason.
- **Run Python on the phone (Termux on Android).** Rejected: Android-only, hostile to backgrounding, no iOS equivalent. Not a long-term solution.
- **Run Python on a Pi-in-pocket.** Rejected: works mechanically but adds hardware ops, battery management, and a third device to the system. Not the path to a clean phone experience.

## Cross-references

- ADR 0001 (Mock-first) — preserved; mocks remain the source of truth for development
- ADR 0002 (Glasses as Protocol) — preserved; `HaloGlasses` is just another implementation
- ADR 0005 (Coach modes) — all three modes (visual, verbal, retro) work on Python host + Lua reflex pattern
- ADR 0006 (Memory layers) — preserved; rolling buffer stays on host (RAM only)
- ADR 0008 (Halo primary, Frame backup) — supplemented by this ADR; the hardware choice is unchanged
- `docs/inspection/2026-05-20-sibling-repos.md` — directive-engine as the consumption target
- Halo SDK: https://docs.brilliant.xyz/halo/halo-sdk/
- `brilliant_sdk` repo: https://github.com/brilliantlabsAR/brilliant_sdk
