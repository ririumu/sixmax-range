#!/usr/bin/env python3
"""Verify a live deployment of the PWA against the local working tree.

Modes:
  (default)     post-deploy smoke test. Every app file (sw.js + its
                precached ASSETS) must return 200 with exactly the local
                bytes, and dev-only files must not be public. Retried
                while the host/CDN catches up with the new deploy.
  --bump-guard  pre-deploy gate. If the live sw.js VERSION equals the
                local VERSION but any app file differs from what is live,
                fail: the cache-first service worker would never deliver
                the change to existing users. Run `make bump` to fix.
                Passes when nothing is live yet (first deploy).

Works for any static host (GitHub Pages, Netlify, ...).

Usage: python3 tools/verify_live.py [--bump-guard] [--retries N] URL
"""
import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files that exist in the repo but must never be published
PRIVATE = ["_headers", "AGENTS.md", "README.md", "Makefile",
           "netlify.toml", ".aidoc/OVERVIEW.md", "tools/check_deploy.py"]


def local_version_and_assets():
    src = (ROOT / "sw.js").read_text(encoding="utf-8")
    ver = re.search(r'var VERSION = "([^"]+)";', src).group(1)
    m = re.search(r"var ASSETS = \[(.*?)\];", src, re.S)
    return ver, re.findall(r'"([^"]+)"', m.group(1))


def app_files(assets):
    """(published path, local file) for every file the SW depends on."""
    files = [("sw.js", ROOT / "sw.js")]
    for a in assets:
        files.append((a, ROOT / ("index.html" if a == "./" else a)))
    return files


def fetch(url):
    """Return (status, body). Status 0 means the host was unreachable."""
    r = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(r, timeout=20) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, TimeoutError):
        return 0, b""


def live_version(base):
    """Return (status, VERSION or None) of the live sw.js."""
    status, body = fetch(base + "sw.js")
    m = re.search(rb'var VERSION = "([^"]+)";', body) if status == 200 else None
    return status, (m.group(1).decode() if m else None)


def smoke(base, files):
    """Return a list of problems (empty = live site matches local)."""
    problems = []
    for path, local in files:
        status, body = fetch(base + ("" if path == "./" else path))
        if status != 200:
            problems.append(f"{path}: HTTP {status}")
        elif body != local.read_bytes():
            problems.append(f"{path}: live content differs from local")
    for path in PRIVATE:
        local = ROOT / path
        status, body = fetch(base + path)
        # 200 alone is not a leak (SPA-style fallbacks); identical bytes are
        if status == 200 and local.is_file() and body == local.read_bytes():
            problems.append(f"{path}: dev file is publicly served")
    return problems


def bump_guard(base, ver, files) -> int:
    status, live = live_version(base)
    if status == 0:
        print(f"  warn  {base} unreachable — skipping comparison")
        return 0
    if live is None:
        print(f"  ok    no live sw.js at {base} (HTTP {status}, first deploy?) — nothing to compare")
        return 0
    if live != ver:
        print(f"  ok    VERSION {live} (live) -> {ver} (local)")
        return 0
    changed = []
    for path, local in files:
        status, body = fetch(base + ("" if path == "./" else path))
        if status != 200 or body != local.read_bytes():
            changed.append(path)
    if not changed:
        print(f"  ok    VERSION {ver} unchanged and app files identical (re-deploy)")
        return 0
    for path in changed:
        print(f"  ERROR {path} changed but VERSION is still {ver}")
    print("bump-guard: FAILED — run `make bump` and commit sw.js")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="live site URL, e.g. https://ririumu.github.io/sixmax-range/")
    ap.add_argument("--bump-guard", action="store_true", help="pre-deploy VERSION gate")
    ap.add_argument("--retries", type=int, default=12, help="smoke attempts (10s apart)")
    args = ap.parse_args()

    base = args.url if args.url.endswith("/") else args.url + "/"
    ver, assets = local_version_and_assets()
    files = app_files(assets)

    if args.bump_guard:
        print(f"bump-guard: {base}")
        return bump_guard(base, ver, files)

    print(f"verify_live: {base} (expect VERSION {ver})")
    for attempt in range(1, args.retries + 1):
        problems = smoke(base, files)
        if not problems:
            for path, _ in files:
                print(f"  ok    {path}")
            print(f"  ok    {len(PRIVATE)} dev files not public")
            print(f"verify_live: live site matches local ({ver})")
            return 0
        if attempt < args.retries:
            print(f"  ...   attempt {attempt}: {len(problems)} problem(s), retrying in 10s")
            time.sleep(10)
    for p in problems:
        print(f"  ERROR {p}")
    print(f"verify_live: FAILED ({len(problems)} problem(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
