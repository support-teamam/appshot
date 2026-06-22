---
name: appshot
description: Generate high-quality, conversion-tuned, App Store Review Guideline 2.3.7-compliant App Store screenshots for an iOS app. Captures real app screens (simulator, or a browser for web), composes branded marketing posters (HTML rendered headless by Chrome at exact device pixels), and uploads to App Store Connect. Config-driven (config.json) — no hardcoded apps, repos, or credentials. Use to (re)build an app's screenshot set.
user_invocable: true
---

# appshot — App Store screenshot factory

Capture → compose → comply → upload, driven by a per-app `config.json`. No hardcoded
project, repo, or secrets. App Store Connect credentials come from the environment
(`ASC_KEY_PATH`, `ASC_ISSUER_ID`, `ASC_KEY_ID`). Scripts live in `scripts/`.

## Flow:  /appshot
1. **Load** `config.json` (app_id, bundle_id, simulator UDID, device display type + size, brand
   colors, and the ordered `screens` with launch args + headlines).
2. **Capture** — `scripts/capture.py config.json raw/`. Pins the simulator by **UDID** (never
   `booted`), forces a clean 9:41 status bar, launches each screen's args, waits to settle,
   saves raw PNGs. The app should expose a DEBUG `-seed` (curated data) and per-screen deep
   links, or use a fastlane snapshot / XCUITest for navigation. Empty states make bad shots.
   For web apps, capture the page at the exact viewport with headless Chrome instead.
3. **Compose** — for each screen, `scripts/compose.py '<spec json>'` renders an HTML poster
   headless in Chrome at the exact display-type pixels: brand `bg`/`ink`/`accent`, the framed
   device (tilt per brand — upright for content), and a two-tone headline (`<span class="accent">`).
   Captions are REAL text, never baked by an image model.
4. **Arrange** — order by impact: frame 1 = signature visual + ≤5-word promise; frames 1–3 carry
   ~70% of the decision. 5–7 frames, one idea each, one consistent template, distinct screens.
5. **Comply (gate)** — captions must be 2.3.7-clean (no price / "free" / "subscription" / "$" /
   "% off"); no price/paywall UI in any frame; exact dimensions; legible at search-thumbnail scale.
6. **Review** — show a contact sheet; do not upload without the human's OK.
7. **Upload** — `scripts/upload.py <app_id> <display_type> out/*.png` (replaces the set, ordered,
   verifies every asset reaches `COMPLETE`). Generate a set only for supported device families
   (iPhone `APP_IPHONE_67` 1320×2868; iPad 13" `APP_IPAD_PRO_3GEN_129` 2048×2732).
8. **Submit** stays a human action in App Store Connect (irreversible).

## Quality bar
- Frame 1: signature visual + concrete ≤5-word promise (+ social-proof badge once ratings exist).
- Background chosen for **contrast** with the app's hero color (a dark app often wants a light poster).
- Current device frame, upright for content; rich seeded data; one consistent template; distinct screens.

## Gotchas (do not repeat)
- Capture by **UDID**, not `booted`. No foreground `sleep` race — settle or XCUITest. Status bar resets on reinstall.
- Build/version numbers may be literal in `Info.plist`, not build settings.
- CDN PUT to the upload URL must use ONLY Apple's returned headers (no `Authorization`); verify `assetDeliveryState == COMPLETE` (the count lies).
- Don't pull a queued version to swap screenshots — it goes `DEVELOPER_REJECTED` and the API won't resubmit (UI-only). Update screenshots before first submit or in a new version.
