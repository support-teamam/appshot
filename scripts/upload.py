#!/usr/bin/env python3
"""Upload screenshots to App Store Connect for one app + display type.

Credentials come from the environment (never committed):
  ASC_KEY_PATH    path to your AuthKey_XXXX.p8
  ASC_ISSUER_ID   App Store Connect API issuer id
  ASC_KEY_ID      the key id (the XXXX in the filename)

Usage:
  python3 upload.py <app_id> <display_type> <image1.png> <image2.png> ...
  # display_type e.g. APP_IPHONE_67 (1320x2868) or APP_IPAD_PRO_3GEN_129 (2048x2732)

Targets the app's editable iOS version's localization, replaces that display
type's screenshot set, uploads in order, and verifies each asset reaches
COMPLETE. Two hard-won correctness details are baked in:
  1. The CDN PUT to Apple's pre-signed upload URL must use ONLY the headers
     Apple returns — adding Authorization breaks it and leaves blank assets.
  2. Verify assetDeliveryState == COMPLETE; the screenshot count alone lies
     (reserved-but-empty screenshots still count).
"""
import os, sys, json, time, hashlib, urllib.request, urllib.error
import jwt  # PyJWT

KEY_PATH = os.environ["ASC_KEY_PATH"]
ISSUER = os.environ["ASC_ISSUER_ID"]
KEY_ID = os.environ["ASC_KEY_ID"]
B = "https://api.appstoreconnect.apple.com"


def tok():
    now = int(time.time())
    return jwt.encode({"iss": ISSUER, "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      open(KEY_PATH).read(), algorithm="ES256", headers={"kid": KEY_ID})


def api(method, url, body=None):
    try:
        r = urllib.request.Request(url, data=(json.dumps(body).encode() if body else None), method=method,
                                   headers={"Authorization": "Bearer " + tok(), "Content-Type": "application/json"})
        resp = urllib.request.urlopen(r, timeout=60); d = resp.read()
        return json.loads(d) if d.strip() else {"_ok": resp.status}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode()[:300]}


def put_cdn(op, chunk):
    # ONLY Apple's provided headers — never add Authorization to the pre-signed URL.
    headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
    try:
        resp = urllib.request.urlopen(urllib.request.Request(op["url"], data=chunk, method=op["method"], headers=headers), timeout=180)
        return 200 <= resp.status < 300
    except urllib.error.HTTPError as e:
        print("   PUT failed:", e.code, e.read().decode()[:120]); return False


def get(u): return api("GET", u)


def main():
    app_id, display_type, shots = sys.argv[1], sys.argv[2], sys.argv[3:]
    versions = get(f"{B}/v1/apps/{app_id}/appStoreVersions?limit=10")["data"]
    editable = [v for v in versions if v["attributes"]["appStoreState"] in
                ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED")]
    if not editable:
        sys.exit("No editable iOS version (need PREPARE_FOR_SUBMISSION). Create/edit a version first.")
    vid = editable[0]["id"]
    lid = get(f"{B}/v1/appStoreVersions/{vid}/appStoreVersionLocalizations")["data"][0]["id"]
    sets = get(f"{B}/v1/appStoreVersionLocalizations/{lid}/appScreenshotSets")["data"]
    setid = next((s["id"] for s in sets if s["attributes"]["screenshotDisplayType"] == display_type), None)
    if not setid:
        r = api("POST", f"{B}/v1/appScreenshotSets", {"data": {"type": "appScreenshotSets",
                "attributes": {"screenshotDisplayType": display_type},
                "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": lid}}}}})
        setid = r["data"]["id"]
    for sh in get(f"{B}/v1/appScreenshotSets/{setid}/appScreenshots")["data"]:
        api("DELETE", f"{B}/v1/appScreenshots/{sh['id']}")
    ids = []
    for p in shots:
        data = open(p, "rb").read(); fn = os.path.basename(p)
        res = api("POST", f"{B}/v1/appScreenshots", {"data": {"type": "appScreenshots",
                  "attributes": {"fileName": fn, "fileSize": len(data)},
                  "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": setid}}}}})
        if res.get("_err"):
            sys.exit(f"reserve failed for {fn}: {res['_body']}")
        sid = res["data"]["id"]
        ok = all(put_cdn(op, data[op["offset"]:op["offset"] + op["length"]]) for op in res["data"]["attributes"]["uploadOperations"])
        api("PATCH", f"{B}/v1/appScreenshots/{sid}", {"data": {"type": "appScreenshots", "id": sid,
            "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
        ids.append(sid); print(f"  {fn}: {'uploaded' if ok else 'PUT FAILED'}")
    api("PATCH", f"{B}/v1/appScreenshotSets/{setid}/relationships/appScreenshots",
        {"data": [{"type": "appScreenshots", "id": i} for i in ids]})
    time.sleep(4)
    print("verify delivery:")
    for sh in get(f"{B}/v1/appScreenshotSets/{setid}/appScreenshots")["data"]:
        st = sh["attributes"].get("assetDeliveryState", {}).get("state")
        print(f"  {sh['attributes'].get('fileName')}: {st}" + (""  if st == "COMPLETE" else "  <-- NOT COMPLETE"))


if __name__ == "__main__":
    main()
