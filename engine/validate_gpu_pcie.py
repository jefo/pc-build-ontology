'''
Skill 14: validate_gpu_pcie — GPU PCIe lanes class → MB slot floor.
Детерминированный маппинг: физика пропускной способности шины.

Читает gpu_pcie_tiers.yaml + chipset_profiles.yaml через _pcbo_config.
Никаких хардкод-таблиц. При выходе PCIe 6.0 — правка YAML.
'''

import re, json, sys
from _pcbo_config import (get_gpu_pcie_requirements, get_gpu_pcie_ai_modifier,
                          get_chipset_pcie_gen)


def parse_pcie(pcie_str: str) -> tuple[int, int]:
    """Parse 'PCIe 5.0 x8' → (5, 8). Returns (0, 0) on failure."""
    m = re.search(r'PCI[eе]\s*(\d+\.?\d*)\s*[xх×]\s*(\d+)', pcie_str, re.IGNORECASE)
    if m:
        return int(float(m.group(1))), int(m.group(2))
    return (0, 0)


def classify_gpu(gen: int, lanes: int) -> str:
    return f"Gen{gen}_x{lanes}"


def calculate_bandwidth(gen: int, lanes: int) -> float:
    bw_per_lane = {1: 0.250, 2: 0.500, 3: 0.985, 4: 1.969, 5: 3.938}
    return round(lanes * bw_per_lane.get(gen, 1.969), 1)


def validate(data: dict) -> dict:
    """
    data fields:
      - gpu: {"pcie": "PCIe 5.0 x8", "id": str}
      - motherboard: {"chipset": "B650", "id": str}
      - intent: str (optional, для AI-модификатора)
    """
    gpu = data.get("gpu", {})
    mb = data.get("motherboard", {})
    intent = data.get("intent", "")

    pcie_str = gpu.get("pcie", "")
    gpu_gen, gpu_lanes = parse_pcie(pcie_str)
    gpu_class = classify_gpu(gpu_gen, gpu_lanes) if gpu_gen else "unknown"

    chipset = mb.get("chipset", "")
    slot_gen = get_chipset_pcie_gen(chipset)

    violations = []

    if gpu_class == "unknown":
        return {
            "gpu_pcie_status": "SKIP",
            "summary": f"Не удалось разобрать PCIe-спеку GPU: '{pcie_str}'.",
            "violations": [],
        }

    # Find slot requirement for this GPU class
    req = None
    for r in get_gpu_pcie_requirements():
        if r["gpu_class"] == gpu_class:
            req = r
            break

    if not req:
        req = {"gpu_class": gpu_class, "min_mb_gen": 3, "min_mb_effective_bw_gbs": 7.9,
               "rationale": "Неизвестный класс — консервативно Gen3."}

    min_mb_gen = req["min_mb_gen"]

    # AI intent modifier
    ai_mod = get_gpu_pcie_ai_modifier()
    ai_intent = ai_mod.get("enabled", False) and any(
        kw in intent.lower() for kw in ai_mod.get("keywords", [])
    )
    if ai_intent:
        min_mb_gen = ai_mod.get("force_mb_gen", 5)
        req["rationale"] += " AI_INTENT: поднято до Gen5×16 для offload bandwidth."

    if slot_gen < min_mb_gen:
        effective_bw = calculate_bandwidth(min(slot_gen, gpu_gen),
                                           gpu_lanes if gpu_lanes <= 8 else min(gpu_lanes, 16))
        violations.append({
            "check": "gpu_pcie_slot",
            "severity": "BLOCK",
            "message": (
                f"GPU PCIe SLOT MISMATCH: {gpu_class} требует слот Gen{min_mb_gen}+ "
                f"({req['rationale']}). Чипсет {chipset} даёт Gen{slot_gen}-слот. "
                f"Эффективная полоса упадёт до {effective_bw} GB/s — "
                f"{'CLIFF_DROP для x8-карт.' if gpu_lanes <= 8 else 'запас x16 спасает, но AI-интенту нужна Gen5.' if ai_intent else ''}"
            ),
            "gpu_class": gpu_class,
            "gpu_gen": gpu_gen,
            "gpu_lanes": gpu_lanes,
            "required_mb_gen": min_mb_gen,
            "actual_mb_gen": slot_gen,
            "ai_modifier": ai_intent,
        })

    return {
        "gpu_pcie_status": "FAIL" if violations else "PASS",
        "summary": (
            f"GPU {gpu_class} → MB {chipset} (Gen{slot_gen}-слот): "
            f"{'НЕСОВМЕСТИМО' if violations else 'совместимо'}"
            f"{' [AI-модификатор: Gen5]' if ai_intent else ''}."
        ),
        "violations": violations,
        "gpu_class": gpu_class,
        "gpu_pcie_gen": gpu_gen,
        "gpu_pcie_lanes": gpu_lanes,
        "required_mb_gen": min_mb_gen,
        "actual_mb_gen": slot_gen,
        "ai_modifier": ai_intent,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(validate(data), ensure_ascii=False, indent=2))
