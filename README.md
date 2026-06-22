# appshot

A small, no-magic **App Store screenshot factory**: capture real app screens → compose
branded marketing posters → check Apple's rules → upload. One config file per app, runnable
by hand or as a [Claude Code](https://claude.com/claude-code) skill.

Built by [Team AM](https://teamam.org) while standardizing screenshots across our own
portfolio. The story (and the failures that shaped it) is in
[Screenshots Are Infrastructure](https://teamam.org/blog/2026-06-22-field-notes-screenshot-factory).

> Why bother: on the App Store the first 2–3 screenshots carry most of the install decision,
> made in ~7 seconds. For anyone shipping more than one app, screenshots are infrastructure —
> and doing them by hand is slow and easy to get subtly wrong.

## What it does

```
capture  →  compose  →  comply  →  upload
(simctl)    (HTML→Chrome)  (2.3.7)   (ASC API)
```

- **capture.py** — clean simulator captures (pinned device by UDID, forced 9:41 status bar, per-screen launch args). Seed real data; empty states make bad shots.
- **compose.py** — turns a raw screen into a branded poster (device frame, benefit headline, background) by rendering an HTML template headless in Chrome at the **exact** display-type pixel size. Captions are real text, never baked into an image model — so they stay crisp and checkable.
- **upload.py** — replaces a display type's screenshot set on your editable iOS version via the App Store Connect API, in order, and **verifies every asset reaches `COMPLETE`**.

## Quickstart

```bash
pip3 install pyjwt
cp config.example.json config.json   # fill in your app_id, bundle_id, simulator UDID, brand, screens

# ASC credentials via env (never in the repo)
export ASC_KEY_PATH=~/.appstoreconnect/private_keys/AuthKey_XXXX.p8
export ASC_ISSUER_ID=...   ASC_KEY_ID=XXXX

python3 scripts/capture.py config.json raw/                 # raw screens
python3 scripts/compose.py '{"screenshot":"raw/01_home.png","out":"out/01_home.png","size":[1320,2868],"bg":"linear-gradient(170deg,#F6F1E8,#EFE7D8)","ink":"#1C1712","accent":"#D4663C","bezel":"#0E0E0E","headline":"Your <span class=\"accent\">benefit</span> here","rot":0}'
python3 scripts/upload.py <app_id> APP_IPHONE_67 out/01_home.png out/02_feature.png   # review first!
```

Display types: **iPhone 6.9" `APP_IPHONE_67` → 1320×2868**, **iPad 13" `APP_IPAD_PRO_3GEN_129` → 2048×2732**. Generate a set only for the device families your app supports (`TARGETED_DEVICE_FAMILY`).

## The quality bar (what "good" means)

- **Frame 1 = your signature visual + a ≤5-word concrete promise** (add a social-proof badge once you have ratings). Frames 1–3 are the whole decision.
- **Background = contrast, not a fixed color.** Pick the bg that makes the app's hero shot pop — a dark app often wants a *light* poster.
- One idea per frame, 5–7 frames, one consistent template, **distinct screens** (don't ship the same screen with three captions).
- Upright devices read cleaner/more premium for content; reserve tilt for a playful hero.
- Rich, seeded data — never empty states.

## Gotchas (learned the hard way)

- **Target the simulator by UDID**, never `booted` — multiple sims = wrong-app captures.
- **No foreground `sleep` race** — wait for the UI to settle (or use XCUITest), or you capture the boot screen.
- The status-bar override **resets on reinstall** — re-apply every run.
- Build/version numbers may be **literal in `Info.plist`**, not from build settings — check the real source.
- **Guideline 2.3.7:** no price / "free" / "subscription" text in store screenshots or captions — price lives only in the IAP review field.
- **Upload:** the CDN `PUT` to Apple's pre-signed URL must use **only** Apple's returned headers — adding `Authorization` leaves blank assets. **Verify `assetDeliveryState == COMPLETE`**; the count alone lies.
- **Don't pull a queued version to swap screenshots:** canceling flips it to `DEVELOPER_REJECTED`, which the API **won't resubmit** (UI-only). Update screenshots *before* first submit, or in a new version.

## Use as a Claude Code skill

Drop the repo (or `SKILL.md`) into your skills directory and run `/appshot <app>` — it orchestrates capture → compose → comply → upload from your `config.json`, holding for your review before upload. See `SKILL.md`.

## License

MIT — see `LICENSE`.
