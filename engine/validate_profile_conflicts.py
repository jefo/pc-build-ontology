#!/usr/bin/env python3
"""Skill 8: validate_profile_conflicts — детерминированная проверка профильных конфликтов.

Добавляется в пайплайн run_all.py как восьмой навык, передаётся в validate_l5_rules.py
через поле profile_conflicts.

Usage:
  python validate_profile_conflicts.py '<json>'

JSON format:
{
  "components": [
    {"id": "nvidia-rtx-5070", "type": "gpu", "file": "catalog/gpu/nvidia-rtx-5070.md"},
    {"id": "amd-ryzen-7-7800x3d", "type": "cpu", "file": "catalog/cpu/amd-ryzen-7-7800x3d.md"}
  ],
  "user_intents": ["esports_1080p_360hz", "heavy_compilation"],
  "primary_intent": "esports_1080p_360hz",
  "primary_weight": 0.8
}
"""

import json, os, re, sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required.")
    sys.exit(1)

# Root of the component knowledge base. Defaults to the repository root so the
# bundled examples resolve; override with PCBO_KB_ROOT for a real KB checkout.
ROOT = Path(os.environ.get("PCBO_KB_ROOT", Path(__file__).resolve().parents[1]))


def extract_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(m.group(1)) if m else None


def parse_profiles(filepath: str) -> dict:
    """Load profiles from a component entry file."""
    fp = ROOT / filepath if not filepath.startswith("/") else Path(filepath)
    if not fp.exists():
        return {}
    text = fp.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(m.group(1))
        return fm.get("profiles", {}) if fm else {}
    except yaml.YAMLError:
        return {}


def validate(data: dict) -> dict:
    components = data.get("components", [])
    user_intents = set(data.get("user_intents", []))
    primary_intent = data.get("primary_intent", "")
    primary_weight = data.get("primary_weight", 0.7)

    blocks = []
    warns = []
    optimal_matches = []

    for comp in components:
        comp_id = comp.get("id", "unknown")
        comp_file = comp.get("file", "")
        profiles = parse_profiles(comp_file) if comp_file else {}

        for pname, pdata in profiles.items():
            optimal_for = set(pdata.get("optimal_for_intents", []))
            failure_for = set(pdata.get("failure_for_intents", []))
            failure_type = pdata.get("failure_type", "LINEAR_DEGRADATION")
            severity = pdata.get("failure_severity", "WARN")
            steel_man = pdata.get("steel_man_desc", "")
            failure_desc = pdata.get("failure_mode_desc", "")

            # Optimal match
            matched_optimal = optimal_for & user_intents
            if matched_optimal:
                optimal_matches.append({
                    "component": comp_id,
                    "profile": pname,
                    "matched_intents": sorted(matched_optimal),
                    "steel_man": steel_man,
                })

            # Failure detection
            matched_failure = failure_for & user_intents
            if matched_failure:
                is_primary_conflict = primary_intent in matched_failure

                if failure_type == "CLIFF_DROP":
                    # Always BLOCK — catastrophic regardless of weight
                    blocks.append({
                        "component": comp_id,
                        "profile": pname,
                        "conflict_intents": sorted(matched_failure),
                        "failure_type": "CLIFF_DROP",
                        "is_primary": is_primary_conflict,
                        "description": failure_desc,
                    })
                elif failure_type == "LINEAR_DEGRADATION":
                    if is_primary_conflict:
                        # Primary intent hit → BLOCK
                        blocks.append({
                            "component": comp_id,
                            "profile": pname,
                            "conflict_intents": sorted(matched_failure),
                            "failure_type": "LINEAR_DEGRADATION",
                            "is_primary": True,
                            "description": failure_desc,
                        })
                    else:
                        # Secondary intent → WARN (acceptable trade-off)
                        warns.append({
                            "component": comp_id,
                            "profile": pname,
                            "conflict_intents": sorted(matched_failure),
                            "failure_type": "LINEAR_DEGRADATION",
                            "is_primary": False,
                            "description": failure_desc,
                            "weight": round(1.0 - primary_weight, 1),
                        })

    # Verdict
    if blocks:
        status = "BLOCK"
        action = "rollback"
    elif warns:
        status = "WARN"
        action = "proceed_with_caveats"
    else:
        status = "PASS"
        action = "proceed"

    return {
        "profile_validation_status": status,
        "profile_action": action,
        "optimal_matches": optimal_matches,
        "blocks": blocks,
        "warnings": warns,
        "summary": {
            "optimal_count": len(optimal_matches),
            "block_count": len(blocks),
            "warn_count": len(warns),
        },
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    output = validate(data)
    print(json.dumps(output, ensure_ascii=False, indent=2))
