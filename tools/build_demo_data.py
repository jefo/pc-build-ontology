#!/usr/bin/env python3
"""Generate docs/data.js for the static PCBO demo.

Reads the two example builds and their expected engine output, adds a small
display-only component table, and writes a self-contained JS data file so the
demo works from file:// and from GitHub Pages.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = [
    {
        "slug": "esports-240hz",
        "file": "examples/esports-240hz",
        "label": "Киберспорт 240 Hz",
        "case_id": "CASE 001",
        "tagline": "CS2 и Valorant. 1080p. Стабильные 240+ FPS.",
        "note": "Каждый рубль выше RX 7600 уходит впустую: сценарий CPU-bound.",
        "components": [
            ["CPU", "Ryzen 7 7800X3D", "120 W", "cache_dominant_gaming"],
            ["GPU", "Radeon RX 7600 8GB", "165 W", "balanced_performance"],
            ["MB", "B650E", "—", "sweet_spot_stable"],
            ["RAM", "32 GB DDR5-6000", "—", "dual channel"],
            ["SSD", "1 TB NVMe", "—", "PCIe 4.0 x4"],
            ["PSU", "650 W", "—", "headroom 1.94×"],
            ["Cooler", "Air tower 155 mm", "—", "120 mm fan"],
            ["Case", "GPU до 350 mm", "—", "high airflow"],
        ],
        "total": "101 800 ₽",
    },
    {
        "slug": "xeon-rtx4090-trap",
        "file": "examples/xeon-rtx4090-trap",
        "label": "Ловушка с маркетплейса",
        "case_id": "CASE 002",
        "tagline": "Xeon + RTX 4090. «Игровой монстр 4K» за 132 000 ₽.",
        "note": "Каждый компонент по отдельности знаком. Вместе — не собирается.",
        "components": [
            ["CPU", "Xeon E5-2670 v3", "135 W", "X99, DDR3"],
            ["GPU", "RTX 4090 24GB", "320 W", "348 mm, 3.5 слота"],
            ["MB", "X99", "—", "1 × M.2, Gen4"],
            ["RAM", "32 GB DDR3 ECC", "—", "серверная"],
            ["SSD", "1 TB SATA", "—", "без sustained write"],
            ["PSU", "450 W", "—", "ATX 2.4"],
            ["Cooler", "Air tower 160 mm", "—", "лимит 155 мм"],
            ["Case", "GPU до 300 mm", "—", "normal airflow"],
        ],
        "total": "132 000 ₽",
    },
]


def main() -> None:
    scenarios = []
    for meta in SCENARIOS:
        base = ROOT / meta["file"]
        build = json.loads((base / "build.json").read_text(encoding="utf-8"))
        result = json.loads((base / "expected-output.json").read_text(encoding="utf-8"))
        scenarios.append(
            {
                "slug": meta["slug"],
                "label": meta["label"],
                "caseId": meta["case_id"],
                "tagline": meta["tagline"],
                "note": meta["note"],
                "total": meta["total"],
                "components": meta["components"],
                "build": build,
                "result": result,
            }
        )

    payload = json.dumps({"scenarios": scenarios}, ensure_ascii=False, indent=2)
    out = ROOT / "docs" / "data.js"
    out.write_text("window.PCBO_DEMO = " + payload + ";\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
