# 0004 — Hardware strategy

**Status:** Accepted · **Date:** 2026-05-19

## Context

Compass needs glasses with three things: a glanceable HUD, a user-accessible camera, and an open SDK that works from Python (or behind a thin bridge). The May 2026 market doesn't deliver all three on a single, freely-available, sub-$500 device.

What we know about the landscape (full survey in `docs/landscape.md`):

- **Brilliant Labs Frame** — the target device when compass was conceived. `brilliant.xyz/products/frame` returns 404. Used on eBay $135–200 (last comp May 15, 2026 at $135 H20 "Excellent condition"). SDK transitioned to community packages (`frame-ble`, `frame-msg` by CitizenOne). Maintenance-mode, not abandoned.
- **Brilliant Labs Halo** — $349, color HUD, on-device NPU (Alif Balletto B1, ~46 GOPS Ethos-U55), but the SDK is `docs.brilliant.xyz/halo/halo/` saying "more details soon" and no Python SDK. Originally promised Nov 2025; "shipping soon" since.
- **Meta Ray-Ban Display** — $799, gorgeous color HUD, Wearables Device Access Toolkit opened to developer preview May 14, 2026 — but Swift/Kotlin or Web Apps only, no Python, 100-tester cap, GA "later in 2026."
- **Vuzix Z100** — $499, monocular green HUD, no camera, fully open Vuzix Ultralite + MentraOS SDK. Ships today.
- **Vuzix M400** — $2,000, 4K camera, monocular HUD, full Android 11 + standard `Camera2`. Industrial-grade. Ships today.
- **Mentra Live** — $299, 12 MP + 119° FOV camera, no display, fully open MentraOS (TypeScript). Ships today.
- **Even Realities G1** — $599, dual-eye green HUD, no camera. MentraOS-compatible. Ships today.

## Decision

**Three-phase hardware ladder.** Each step builds on the prior; the architecture's `Glasses` Protocol absorbs the swaps.

### Phase 1 — Used Frame (~$135–200 on eBay)

The cheapest path that matches the original spec: HUD + camera + open Python SDK. Buy a used Frame H20 from a reputable eBay seller, verify Mister Power dock is included, build against the community `frame-msg` package. This is the V0 of "compass on real glasses."

Set an eBay saved search at `ebay.com/sch/i.html?_nkw=Brilliant+Labs+Frame` with US-only + price ceiling $250 + "Newly Listed" + push notifications via the eBay mobile app.

### Phase 2 — Vuzix M400 (~$2,000) for the fab/install demo

Once Phase 1 proves the architecture, the Zahner-style manufacturing QA story needs a device a foreman would accept: drop-rated, IP-rated, all-day battery, full Camera2 API. M400 is the documented industrial choice (Fujitec, surgical OR, warehouse logistics). Pairs with Z100 ($499) if a fashion-light HUD demo is also wanted for the consumer-portfolio side.

### Phase 3 — Re-evaluate Halo / Meta on quarterly cadence

By Q3 2026 (post-Meta-Connect, Sept 23–24), at least one of these may be a viable third driver:
- Halo with a published Python or REST SDK and exposed camera bytes
- Meta Ray-Ban Display with publishing past developer preview (GA + raised tester cap)
- Mentra Display (Mentra's promised "later 2026" HUD device)

## Consequences

**Good:**
- Cheapest viable starting point: a used Frame at $135 is one-fifth of Halo and one-sixth of Z100+M400 together.
- Industrial credibility path is documented. The Zahner-portfolio narrative can point to M400 as the device a shop would actually accept.
- No vendor lock. The `Glasses` Protocol means any of the Phase 3 candidates is a drop-in driver, not a rewrite.

**Bad:**
- Frame is genuinely scarce. eBay listings are sporadic; the May 15 comp sold in days. We may wait weeks for a good listing.
- M400 is not a portfolio-impressive device. It looks like a tool, not a thesis. Solution: don't lead the portfolio page with M400 photos.
- Halo dependency is real. If Halo ships well and opens its NPU, the project's "on-device VLM" story changes; we should plan for that revisit.

## Alternatives considered

- **Buy Halo on preorder and wait.** Rejected: shipping has slipped twice, SDK is a stub, no Python. Money tied up in a watch item.
- **Skip Frame, go straight to Vuzix Z100 + Mentra Live as the portfolio pair.** Considered seriously. Z100 ($499) + Mentra Live ($299) = $798 — two devices, both shipping, both open. Falls down on portfolio coherence: two devices to show off is less elegant than one Frame doing both, and the camera-less Z100 means the "what is this?" demo doesn't work on the device with the HUD.
- **Buy a used HoloLens 2 cheap on eBay.** Rejected. EOL, security updates only until Dec 31, 2027, full hardware exit confirmed by Microsoft Feb 11, 2025.

## Triggers to revisit

| If… | Then… |
|---|---|
| 30 days pass without finding a Frame under $250 on eBay | Pivot to Vuzix Z100 + Mentra Live as the dev pair. |
| Brilliant Labs publishes Halo SDK with raw camera access | Add `HaloGlasses` driver; evaluate as third primary. |
| Meta opens Ray-Ban Display past developer preview with raised tester cap | Build a Swift/Kotlin bridge; consider as the consumer hero. |
| A Zahner pilot crystallizes with a real customer | Buy M400 for that engagement specifically. |
| Mentra Display ships | Add as the open-source HUD primary. |
