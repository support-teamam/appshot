#!/usr/bin/env python3
"""Capture clean simulator screenshots for each screen in config.json.

Targets a specific simulator by UDID (never `booted` — with several sims
running it grabs the wrong one), forces a clean 9:41 status bar, launches the
app with each screen's launch args, waits for the UI to settle, and saves the
raw capture.

Your app needs a DEBUG way to reach each screen with seeded, screenshot-worthy
data — e.g. a `-seed` launch arg and per-screen deep links like `-screen x`
(or a fastlane snapshot / XCUITest for full navigation). Empty states make bad
screenshots; seed real-looking content.

Usage:  python3 capture.py config.json [out_dir=raw]
"""
import sys, json, time, subprocess, os

cfg = json.load(open(sys.argv[1]))
out = sys.argv[2] if len(sys.argv) > 2 else "raw"
os.makedirs(out, exist_ok=True)
udid = cfg["simulator_udid"]; bundle = cfg["bundle_id"]


def sim(*args):
    return subprocess.run(["xcrun", "simctl", *args], capture_output=True, text=True)


# clean status bar (9:41, full battery/signal) — re-applied each run (it resets on reinstall)
sim("status_bar", udid, "override", "--time", "9:41", "--batteryState", "charged",
    "--batteryLevel", "100", "--wifiBars", "3", "--cellularBars", "4", "--dataNetwork", "wifi")

for s in cfg["screens"]:
    sim("terminate", udid, bundle)
    sim("launch", udid, bundle, *s.get("launch_args", []))
    time.sleep(s.get("settle", 8))  # let the UI render (can't rely on a fixed instant)
    path = os.path.join(out, s["name"] + ".png")
    sim("io", udid, "screenshot", path)
    print("captured", path)
print("done — now run compose.py per screen, then upload.py")
