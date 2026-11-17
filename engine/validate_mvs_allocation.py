'''
Skill 11: validate_mvs_allocation v3.0
Приоритет — предотвращение системного дисбаланса (Requirements Allocation Error).

v3.0: +CPU (cores, arch_gen, max_tdp) и RAM (capacity, speed) MVS-проверки.
MVS теперь покрывает MB + CPU + RAM — все структурные компоненты бюджета.
LLM не участвует — все значения из budget_tiers.yaml.
'''

import json, sys
from _pcbo_config import get_chipset, get_vrm_tier_rank, get_budget_tier


def evaluate(data: dict) -> dict:
    """
    data fields:
      - budget.actual_cost
      - motherboard.chipset (or motherboard_id)
      - motherboard.ram_slots (optional, from entry)
      - motherboard.m2_slots (optional, from entry)
      - motherboard.price (optional)
      - cpu.cores (int)
      - cpu.tdp_w (int)
      - cpu.arch_gen (str, e.g. "zen4")
      - cpu.price (optional)
      - ram.capacity_gb (int)
      - ram.speed (str, e.g. "ddr5_6000")
      - ram.price (optional)
    """
    budget = data.get("budget", {})
    actual_cost = budget.get("actual_cost", 0)
    mb = data.get("motherboard", {})
    cpu = data.get("cpu", {})
    ram = data.get("ram", {})

    chipset = mb.get("chipset", data.get("motherboard_chipset", ""))
    mb_price = mb.get("price", 0)
    ram_slots = mb.get("ram_slots", 2)
    m2_slots = mb.get("m2_slots", 1)

    cpu_cores = cpu.get("cores", 0)
    cpu_tdp = cpu.get("tdp_w", 0)
    cpu_arch = cpu.get("arch_gen", "")
    cpu_price = cpu.get("price", 0)

    ram_capacity = ram.get("capacity_gb", 0)
    ram_speed = ram.get("speed", "")
    ram_price = ram.get("price", 0)

    tier = get_budget_tier(actual_cost)
    if not tier:
        return {
            "mvs_status": "NO_TIER",
            "summary": f"Бюджет {actual_cost:,}₽ вне известных тиров",
            "violations": [],
            "tier_label": "unknown",
        }

    reqs = tier["mb_requirements"]
    alloc = tier["allocation"]
    violations = []

    # 1. M.2 slots check
    min_m2 = reqs.get("min_m2_slots", 1)
    if m2_slots < min_m2:
        violations.append({
            "check": "m2_slots",
            "severity": "WARN",
            "message": f"MVS: плата имеет {m2_slots} M.2 слотов, "
                       f"тир требует ≥{min_m2}. Ограничено расширение хранилища.",
            "required": f"≥{min_m2}",
            "actual": str(m2_slots),
        })

    # 3. PCIe generation check
    min_pcie = reqs.get("min_pcie_gen", 4)
    chipset_profile = get_chipset(chipset)
    chipset_pcie = chipset_profile.get("pcie_gen", 4)
    if chipset_pcie < min_pcie:
        violations.append({
            "check": "pcie_gen",
            "severity": "BLOCK",
            "message": f"MVS: чипсет {chipset} поддерживает PCIe Gen{chipset_pcie}, "
                       f"тир требует Gen{min_pcie}. Карты Gen5 будут работать на пониженной скорости.",
            "required": f"Gen{min_pcie}",
            "actual": f"Gen{chipset_pcie}",
        })

    # 4. VRM tier check
    min_vrm = reqs.get("vrm_tier", "basic_stable")
    chipset_vrm = chipset_profile.get("vrm_tier", "basic_stable")
    vrm_rank = get_vrm_tier_rank()
    if vrm_rank.get(chipset_vrm, 1) < vrm_rank.get(min_vrm, 1):
        violations.append({
            "check": "vrm_tier",
            "severity": "WARN",
            "message": f"MVS: чипсет {chipset} имеет VRM уровня «{chipset_vrm}», "
                       f"тир требует «{min_vrm}». Под sustained нагрузкой возможен троттлинг.",
            "required": min_vrm,
            "actual": chipset_vrm,
        })

    # 5. Budget share check
    if mb_price > 0 and actual_cost > 0:
        share = mb_price / actual_cost
        min_share = alloc.get("mb_budget_share_min", 0.08)
        if share < min_share:
            violations.append({
                "check": "budget_share",
                "severity": "WARN",
                "message": f"MVS: плата стоит {mb_price:,}₽ — это {share:.0%} бюджета, "
                           f"тир требует ≥{min_share:.0%}. Системный дисбаланс: "
                           f"дорогие GPU/CPU на дешёвой платформе.",
                "required": f"≥{min_share:.0%}",
                "actual": f"{share:.0%}",
            })

    # 6. CPU core count check
    cpu_reqs = tier.get("cpu_requirements", {})
    min_cores = cpu_reqs.get("min_cores", 0)
    if min_cores and cpu_cores > 0 and cpu_cores < min_cores:
        violations.append({
            "check": "cpu_cores",
            "severity": "BLOCK",
            "message": f"MVS: CPU имеет {cpu_cores} ядер, "
                       f"тир требует ≥{min_cores}. Процессор не соответствует бюджетному классу.",
            "required": f"≥{min_cores}",
            "actual": str(cpu_cores),
        })

    # 7. CPU TDP check (not BLOCK — VRM handles the thermal BLOCK separately)
    max_tdp = cpu_reqs.get("max_tdp_w", 999)
    if cpu_tdp > max_tdp:
        violations.append({
            "check": "cpu_tdp",
            "severity": "WARN",
            "message": f"MVS: CPU TDP {cpu_tdp}W превышает рекомендованный максимум "
                       f"{max_tdp}W для тира. VRM может не справиться с sustained нагрузкой.",
            "required": f"≤{max_tdp}W",
            "actual": f"{cpu_tdp}W",
        })

    # 8. RAM capacity check
    ram_reqs = tier.get("ram_requirements", {})
    min_ram_cap = ram_reqs.get("min_capacity_gb", 0)
    if min_ram_cap and ram_capacity > 0 and ram_capacity < min_ram_cap:
        violations.append({
            "check": "ram_capacity",
            "severity": "BLOCK",
            "message": f"MVS: RAM имеет {ram_capacity}GB, "
                       f"тир требует ≥{min_ram_cap}GB. "
                       f"Недостаточно памяти для задач этого бюджетного класса.",
            "required": f"≥{min_ram_cap}GB",
            "actual": f"{ram_capacity}GB",
        })

    has_block = any(v["severity"] == "BLOCK" for v in violations)

    return {
        "mvs_status": "FAIL" if has_block else ("WARN" if violations else "PASS"),
        "tier_label": tier["label"],
        "summary": f"Тир: {tier['label']} ({tier['budget_min']:,}–{tier['budget_max']:,}₽). "
                   f"Нарушений: {len(violations)}.",
        "violations": violations,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(evaluate(data), ensure_ascii=False, indent=2))
