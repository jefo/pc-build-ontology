'''
Skill 13: validate_cpu_vrm — CPU TDP → MB VRM floor.
Детерминированный маппинг: физика тепловыделения VRM.

Читает cpu_vrm_tiers.yaml + chipset_profiles.yaml через _pcbo_config.
Никаких хардкод-таблиц. При новом поколении CPU — правка YAML.
'''

import json, sys
from _pcbo_config import get_cpu_vrm_requirements, get_chipset_vrm_tier, get_vrm_tier_rank


def _find_vrm_requirement(tdp_w: int) -> dict | None:
    for r in get_cpu_vrm_requirements():
        if r["tdp_min"] <= tdp_w <= r["tdp_max"]:
            return r
    return None


def validate(data: dict) -> dict:
    """
    data fields:
      - cpu: {"tdp_w": int, "id": str, "title": str}
      - motherboard: {"chipset": str, "id": str, "title": str}
    """
    cpu = data.get("cpu", {})
    mb = data.get("motherboard", {})

    cpu_tdp = cpu.get("tdp_w", 0)
    chipset = mb.get("chipset", "")
    cpu_id = cpu.get("id", "?")
    mb_id = mb.get("id", "?")

    violations = []
    vrm_rank = get_vrm_tier_rank()

    # 1. Find required VRM tier for this TDP
    req = _find_vrm_requirement(cpu_tdp)
    if not req:
        return {
            "cpu_vrm_status": "SKIP",
            "summary": f"CPU TDP {cpu_tdp}W вне известных диапазонов.",
            "violations": [],
        }

    min_vrm_tier = req["min_vrm_tier"]
    min_rank = vrm_rank[min_vrm_tier]

    # 2. Find actual VRM tier for this chipset
    mb_vrm = get_chipset_vrm_tier(chipset)
    mb_rank = vrm_rank.get(mb_vrm, 1)

    # 3. Compare
    if mb_rank < min_rank:
        violations.append({
            "check": "cpu_vrm",
            "severity": "BLOCK",
            "message": (
                f"CPU VRM MISMATCH: {cpu_id} ({cpu_tdp}W TDP, класс «{req['label']}») "
                f"требует VRM ≥ «{min_vrm_tier}» ({req['rationale']}). "
                f"Чипсет {chipset} ({mb_id}) имеет VRM «{mb_vrm}» — "
                f"под sustained нагрузкой возможен троттлинг VRM и отключение."
            ),
            "cpu_tdp_w": cpu_tdp,
            "required_vrm": min_vrm_tier,
            "actual_vrm": mb_vrm,
            "tdp_range": req["label"],
        })

    return {
        "cpu_vrm_status": "FAIL" if violations else "PASS",
        "summary": (
            f"CPU {cpu_tdp}W (требует ≥{min_vrm_tier}) "
            f"→ MB {chipset} ({mb_vrm}): "
            f"{'НЕСОВМЕСТИМО' if violations else 'совместимо'}."
        ),
        "violations": violations,
        "cpu_tdp_w": cpu_tdp,
        "required_vrm": min_vrm_tier,
        "actual_vrm": mb_vrm,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(validate(data), ensure_ascii=False, indent=2))
