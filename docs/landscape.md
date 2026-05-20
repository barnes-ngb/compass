# compass — Hardware Landscape (May 19, 2026)

A living snapshot. Re-check quarterly; sooner if a trigger fires (see bottom).

---

## What we want

Three things on one device, ideally under $500:
1. A glanceable HUD (single-eye monocular is fine; doesn't need to be color, doesn't need to be wide FOV).
2. A user-accessible camera that produces image bytes we can send to a cloud VLM.
3. An open SDK that works from Python on Windows (or behind a thin bridge from a phone-hosted SDK).

No single device under $500 in May 2026 ships all three. The decision tree in `docs/decisions/0004-hardware-strategy.md` is the response.

---

## The shipping candidates

### Brilliant Labs Frame ✱ Primary target

- **Status**: discontinued from first-party (brilliant.xyz/products/frame → HTTP 404, confirmed May 18, 2026). Used market only.
- **eBay comp** (May 15, 2026): H20 "Excellent condition" sold $135.00 / Best Offer. Item #236098220817.
- **Camera**: 1280×720 (`frame_sdk.camera.take_photo()` → JPEG bytes)
- **HUD**: 640×400 16-color microOLED + geometric prism, ~20° FoV diagonal
- **SDK**: Lua on-device + Python via Bluetooth. Official `frame-sdk-python` repo README says "Deprecated"; replaced by community packages `frame-ble` (1.1.1) and `frame-msg` (5.2.1) by CitizenOne — actively maintained, on PyPI, docs.brilliant.xyz now recommends.
- **Risk**: single-community-maintainer dependency. Frame's bundled cloud features (Noa) may degrade over time but our pipeline is BYO-cloud — irrelevant.
- **Decision**: Phase 1 primary. eBay saved-search alert active at `ebay.com/sch/i.html?_nkw=Brilliant+Labs+Frame`.

### Brilliant Labs Halo ✱ Watch list

- **Status**: aspirational. Promised Nov 2025; slipped to Q1 2026; brilliant.xyz/products/halo says "Shipping starts soon 🚀" with no firm date as of May 18, 2026.
- **Price**: $349 (was $299 pre-order).
- **Camera**: "optical sensor for AI inference" — raw bytes undocumented; partnership PR (FutureFive) says raw video doesn't leave the glasses, which suggests bytes are *deliberately not exposed* to third parties.
- **HUD**: 0.2" color microOLED, single-eye.
- **NPU**: Alif Balletto B1 — Cortex-M55 + Ethos-U55 at ~46 GOPS. Not capable of running general VLMs; suitable for wakeword / classifier-grade inference only.
- **SDK**: `docs.brilliant.xyz/halo/halo/` says "more details will be shared soon." No GitHub repo. No Python SDK.
- **Re-check triggers**: (1) docs page moves past "soon," (2) Halo-specific repo appears in `github.com/brilliantlabsAR`, (3) first-hand customer reviews confirm camera-byte access.

### Meta Ray-Ban Display ✱ Q3 2026 watch

- **Status**: developer preview as of May 14, 2026 (Wearables Device Access Toolkit). Publishing to GA "later in 2026."
- **Price**: $799 + $499 prescription optics. Neural Band included.
- **Camera**: 12 MP, 3K video.
- **HUD**: in-lens color, glanceable.
- **SDK**: Swift / Kotlin / Web Apps. No Python. 100-tester cap per build. Custom voice commands gated.
- **Re-check trigger**: Meta Connect 2026 (Sept 23–24) for GA timing and tester-cap changes.

### Vuzix Z100 ✱ Fallback primary

- **Status**: shipping today.
- **Price**: ~$499.
- **Camera**: none.
- **HUD**: monocular green waveguide, 35–38 g, glanceable.
- **SDK**: Vuzix Ultralite SDK (Android/iOS) + MentraOS support.
- **Use case**: pair with Mentra Live or a phone camera. If Frame doesn't appear on eBay within 30 days, this is the fallback HUD half.

### Vuzix M400 ✱ Industrial / Zahner pilot

- **Status**: shipping today.
- **Price**: ~$2,000.
- **Camera**: 4K30 / 1080p60, autofocus 10 cm → infinity.
- **HUD**: nHD OLED monocular, >2,000 nits.
- **SDK**: full Android 11, standard `Camera2` API, Vuzix Speech SDK, Vuzix Barcode SDK.
- **Use case**: the device a foreman would actually accept. Drop-rated 2 m, IP-rated. For when a Zahner manufacturing-QA pilot crystallizes — not for the consumer/portfolio demo.

### Mentra Live ✱ Open-source camera sibling

- **Status**: shipping today; batches Feb–Mar 2026.
- **Price**: $299.
- **Camera**: 12 MP, 119° FOV, 1080p.
- **HUD**: none.
- **SDK**: MentraOS, MIT-licensed, TypeScript. Full camera/mic/speaker/Bluetooth access.
- **Use case**: the camera-only sibling. Demonstrates that the `Glasses` Protocol abstraction is real (a different device, no display, same backend).

### Even Realities G1

- **Status**: shipping today.
- **Price**: ~$599 base + $150 prescription.
- **Camera**: none — relies on phone.
- **HUD**: dual-eye microLED green, MentraOS-compatible.
- **Use case**: the display-only sibling. Best-looking glasses on this list. Pair with phone camera for the visual mode.

### RealWear Navigator 520

- **Status**: shipping; ~$3,150.
- **Camera**: 48 MP + autofocus + optional thermal module.
- **HUD**: 1280×720 monocular optical.
- **SDK**: Android underneath, voice-only UX, partner integrations (TeamViewer Frontline). Not a Python-first platform.
- **Use case**: ignore for V0/V1. Only relevant if a real enterprise customer asks for IP66/MIL-STD-810H hardware.

---

## Explicitly dead or EOL

- **Microsoft HoloLens 2** — Microsoft stopped production Oct 2024; security updates only until Dec 31, 2027; hardware exit confirmed Feb 11, 2025. **Do not start new builds.**
- **Trimble XR10** — rides HoloLens 2; same fate.
- **Magic Leap 1** — bricked Dec 31, 2024 per Magic Leap's official EOL notice.
- **Brilliant Monocle** — Brilliant Labs' predecessor to Frame; superseded.

---

## What we ignored and why

- **Apple Vision Pro** — wrong form factor; ski-goggle passthrough is not glance-paced glasses.
- **RayNeo X2/X3 Pro** — interesting hardware ($1,099–1,299), but proprietary RayNeo AIOS, China-first ecosystem, and a SDK approval gate. Worth watching, not betting on.
- **Rokid Glasses** — similar to RayNeo, China-first, proprietary.
- **XReal Air 2 family** — display-only; designed as a phone/PC external monitor, not a hackable platform.
- **Snap Spectacles ('25)** — Lens Studio is the only authoring path, not Python-friendly.

---

## Re-check schedule

| When | Re-check |
|---|---|
| Quarterly (next: 2026-08-15) | Brilliant Labs Halo shipping status + SDK availability |
| Sept 24, 2026 (post-Meta-Connect) | Meta Ray-Ban Display GA, tester-cap changes |
| Whenever an eBay Frame appears at < $250 | Buy and move to Phase 1 |
| If a Zahner customer pilot crystallizes | Buy Vuzix M400 for that engagement |
| If Mentra ships their promised display product ("late 2026") | Evaluate as open-source HUD primary |
