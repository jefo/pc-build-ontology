#!/usr/bin/env python3
"""Render the static demo to PNG screenshots.

Requires Playwright and a Chromium build:
    pip install playwright
    python tools/screenshot_demo.py

Set CHROME_PATH if Chromium is not in the default Playwright cache.
Screenshots are written to docs/screenshots/.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"

SHOTS = [
    ("esports-240hz", "demo-valid.png"),
    ("xeon-rtx4090-trap", "demo-trap.png"),
]


def default_chrome() -> str | None:
    cache = Path.home() / ".cache" / "ms-playwright"
    candidates = sorted(cache.glob("chromium-*/chrome-linux64/chrome"))
    return str(candidates[-1]) if candidates else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME_PATH") or default_chrome()
    if not chrome or not Path(chrome).exists():
        raise SystemExit("Chromium not found. Set CHROME_PATH.")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000},
            device_scale_factor=2,
        )
        for slug, filename in SHOTS:
            url = (ROOT / "docs" / "index.html").as_uri() + f"?scenario={slug}"
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / filename), full_page=True)
            print(f"wrote {OUT / filename}")
        browser.close()


if __name__ == "__main__":
    main()
