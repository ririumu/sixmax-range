#!/usr/bin/env python3
"""Deploy dist/ to Netlify via the REST API (no CLI install needed).

Auth resolution order:
  1. NETLIFY_AUTH_TOKEN env var
  2. netlify-cli configstore ~/Library/Preferences/netlify/config.json

Site resolution order:
  1. .netlify/state.json {"siteId": ...}  (written after first deploy)
  2. NETLIFY_SITE_ID env var
  3. existing site named NAME in the account (fresh clone without state.json)
  4. create a new site (--name NAME, default rfi-range-grid)

Usage: python3 tools/deploy_netlify.py [--name NAME]
Requires: dist/ already built (run `make dist` first, or `make deploy-netlify`).
"""
import argparse
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.netlify.com/api/v1"
STATE = ROOT / ".netlify" / "state.json"


def get_token() -> str:
    tok = os.environ.get("NETLIFY_AUTH_TOKEN")
    if tok:
        return tok
    home = Path.home()
    candidates = [
        home / "Library/Preferences/netlify/config.json",  # macOS
        home / ".config/netlify/config.json",              # Linux
        home / ".config/configstore/netlify-cli.json",     # configstore fallback
    ]
    for cfg in candidates:
        if cfg.is_file():
            users = json.loads(cfg.read_text()).get("users", {})
            for u in users.values():
                tok = (u.get("auth") or {}).get("token")
                if tok:
                    return tok
    sys.exit("error: no Netlify token (set NETLIFY_AUTH_TOKEN or run netlify login)")


def req(token: str, method: str, path: str, body=None, ctype=None):
    r = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": f"Bearer {token}"})
    if body is not None:
        r.add_header("Content-Type", ctype or "application/json")
        r.data = body if isinstance(body, bytes) else json.dumps(body).encode()
    try:
        with urllib.request.urlopen(r) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode("utf-8", "replace")
        sys.exit(f"error: {method} {path} -> {e.code} {detail}")


def ensure_site(token: str, name: str) -> dict:
    if STATE.is_file():
        sid = json.loads(STATE.read_text()).get("siteId")
        if sid:
            return req(token, "GET", f"/sites/{sid}")
    sid = os.environ.get("NETLIFY_SITE_ID")
    if sid:
        return req(token, "GET", f"/sites/{sid}")
    # state.json is gitignored, so a fresh clone looks the site up by name
    sites = req(token, "GET", f"/sites?filter=all&name={urllib.parse.quote(name)}")
    found = [s for s in sites if s.get("name") == name]
    site = found[0] if found else req(token, "POST", "/sites", {"name": name})
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({"siteId": site["id"]}))
    return site


def zip_dir(d: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(d.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(d))
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="rfi-range-grid", help="site name for creation")
    args = ap.parse_args()

    dist = ROOT / "dist"
    if not dist.is_dir():
        sys.exit("error: dist/ not found — run `make dist` first")

    token = get_token()
    site = ensure_site(token, args.name)
    print(f"site: {site['name']}  ({site.get('ssl_url') or site.get('url')})")

    payload = zip_dir(dist)
    print(f"uploading {len(payload)} bytes ...")
    dep = req(token, "POST", f"/sites/{site['id']}/deploys",
              body=payload, ctype="application/zip")

    import time
    for _ in range(40):
        dep = req(token, "GET", f"/sites/{site['id']}/deploys/{dep['id']}")
        if dep.get("state") in ("ready", "error"):
            break
        time.sleep(2)
    print("state:", dep.get("state"))
    if dep.get("state") != "ready":
        return 1
    print("live:", site.get("ssl_url") or site.get("url"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
