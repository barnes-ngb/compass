# 0001 — Mock-first development

**Status:** Accepted · **Date:** 2026-05-19

## Context

Compass needs hardware — at minimum, smart glasses with a camera, a display, and an open SDK — and the hardware market in May 2026 is uncertain. Brilliant Labs Frame is effectively discontinued (used on eBay only). Halo has slipped past its November 2025 ship date. Meta Ray-Ban Display opened to developers in dev preview but has no Python SDK. Vuzix and Mentra ship today, but each has trade-offs.

Waiting for hardware to start building would mean weeks of nothing. Building against a single fixed device would lock the architecture to whatever that device's quirks are. Neither is acceptable.

## Decision

The first driver is a **mock** that runs on the laptop: webcam captures images, an OpenCV window simulates the HUD. The full pipeline — capture, VLM call, memory logging, HUD render — runs end-to-end against the mock from day one. Real glasses become one more driver, swapped in via the `Glasses` Protocol when the hardware decision is made and the device is in hand.

## Consequences

**Good:**
- Build doesn't block on hardware availability. Pipeline, VLM integration, memory layer, coach prompts — all develop and iterate without any device on the desk.
- The abstraction gets *tested* by being used. If the mock works and a real Frame later works against the same Protocol, the abstraction is real, not aspirational.
- Cheap to demo. The portfolio site can show a working video on a laptop the day after a hardware change rather than the week after.
- Hardware decisions stay reversible. If Halo ships well, we add a `HaloGlasses` driver. If Vuzix Z100 is the answer, we add a `VuzixZ100Glasses` driver. The rest of the code doesn't move.

**Bad:**
- The mock's UX (cv2 window, keyboard SPACE to capture) is not the device's UX (look-up tap, side-arm button, voice trigger). Translation effort when wiring a real driver.
- Latency on a laptop with localhost-fast image upload masks the real-world Frame BLE transport latency. The latency budget in `architecture.md` accounts for both; we don't pretend the mock is the real measurement.
- Discipline required: it's tempting to keep building features against the mock and never test on real glasses. The roadmap has explicit hardware-integration phases to force the issue.

## Alternatives considered

- **Buy a device first, then build.** Rejected: hardware market too volatile in 2026, and we wouldn't have known which device to buy without first understanding what compass actually needs.
- **Build only for one specific device (e.g., used Frame).** Rejected: locks the architecture to one vendor's SDK and tooling. Worse if the vendor sunsets.
- **Skip the mock, use the Python SDK in headless mode.** Rejected: a mock with a visible HUD window is materially more useful for prompt-iteration than a headless print.
