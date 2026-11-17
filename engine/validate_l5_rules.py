'''
Skill 7 (enhanced): validate_l5_rules v3.0
Финал — агрегатор результатов всех симуляций и валидаторов.
v3.0 (2026-06-04): +CPU_VRM, +GPU_PCIe, +Component Floor, −tier_proportionality.

Собирает выходы Skills 1-15 и выносит итоговый вердикт:
- PASS — все проверки пройдены
- PASS_WITH_WARNINGS — есть WARN, но не BLOCK
- FAIL — хотя бы один BLOCK → rollback
'''

import json, sys


def validate(data: dict) -> dict:
    structural = data.get("structural_clearance", {})
    power = data.get("power_state", {})
    thermal = data.get("thermal_profile", {})
    acoustic = data.get("acoustic_class", {})
    pcie = data.get("pcie_topology", {})
    budget = data.get("budget", {})
    profile = data.get("profile_conflicts", {})
    physical = data.get("physical_constraints", {})
    mvs = data.get("mvs_allocation", {})
    cpu_vrm = data.get("cpu_vrm", {})
    gpu_pcie = data.get("gpu_pcie", {})
    comp_floor = data.get("component_floor", {})

    failed_checks = []
    warnings = []

    # ═══ BLOCK checks ═══

    if not structural.get("is_compatible", True):
        failed_checks.append("STRUCTURAL: Компоненты физически несовместимы.")

    if power.get("status") == "BLOCK":
        failed_checks.append(f"POWER: {power.get('messages', ['BLOCK'])[0]}")

    if thermal.get("cpu_thermal_state") in ("T_Throttle", "T_Critical"):
        failed_checks.append(
            f"THERMAL: CPU достигает {thermal.get('cpu_thermal_state')} "
            f"({thermal.get('predicted_cpu_temp_C', '?')}°C)."
        )

    if thermal.get("gpu_thermal_state") in ("T_Throttle", "T_Critical"):
        failed_checks.append(
            f"THERMAL: GPU достигает {thermal.get('gpu_thermal_state')}."
        )

    # Profile conflict BLOCKs (Skill 8)
    if profile:
        for block in profile.get("blocks", []):
            failed_checks.append(
                f"PROFILE: {block['component']} — "
                f"{block['profile']} конфликтует с {block['conflict_intents']} "
                f"[{block['failure_type']}, primary={block.get('is_primary', True)}]. "
                f"{block.get('description', '')[:100]}"
            )

    # Physical constraint BLOCKs (Skill 9)
    if physical:
        for fail in physical.get("failures", []):
            failed_checks.append(
                f"PHYSICAL: {fail.get('component', '?')} — {fail.get('message', '?')}"
            )

    # MVS BLOCKs (Skill 11)
    if mvs:
        for v in mvs.get("violations", []):
            if v["severity"] == "BLOCK":
                failed_checks.append(f"MVS: {v['message']}")

    # Budget BLOCK
    if budget:
        actual = budget.get("actual_cost", 0)
        ceiling = budget.get("ceiling", float("inf"))
        if actual > ceiling:
            failed_checks.append(
                f"BUDGET: {actual:,}₽ превышает потолок {ceiling:,}₽ "
                f"на {actual - ceiling:,}₽."
            )

    # ═══ WARN checks ═══

    if power.get("status") == "WARN":
        warnings.extend(power.get("messages", []))

    if thermal.get("cpu_thermal_state") == "T_Hot":
        warnings.append(
            f"THERMAL: CPU {thermal.get('predicted_cpu_temp_C', '?')}°C — "
            f"близко к пределу."
        )

    # Thermal soak warning (v2.0)
    if thermal.get("thermal_soak_active"):
        warnings.append(
            f"THERMAL SOAK: Корпус ({thermal.get('case_airflow_class', '?')}) "
            f"не справляется с отводом {thermal.get('total_heat_generation_W', 0):.0f}W тепла "
            f"(exhaust capacity: {thermal.get('case_exhaust_capacity_W', 0)}W). "
            f"При sustained нагрузке температуры будут расти "
            f"(+{thermal.get('thermal_soak_penalty_C', 0):.1f}°C penalty)."
        )

    if not acoustic.get("is_compliant", True):
        warnings.extend(acoustic.get("warnings", []))

    # PCIe bandwidth BLOCK for gaming intents (v2.1)
    pcie_intent = pcie.get("intent", "") or profile.get("primary_intent", "") or ""
    bw = pcie.get("effective_bandwidth_gbs", 0)
    gaming_intents = {"aaa_1080p", "aaa_1440p", "aaa_4k", "esports"}
    if bw > 0 and any(gi in pcie_intent.lower() for gi in gaming_intents):
        MIN_GAMING_BW = 20.0  # GB/s for 1440p+
        if bw < MIN_GAMING_BW:
            failed_checks.append(
                f"PCIe BANDWIDTH BLOCK: {bw} GB/s < {MIN_GAMING_BW} GB/s минимум для гейминга. "
                f"Gen{pcie.get('gpu_pcie_gen_effective','?')}×{pcie.get('gpu_effective_pcie_lanes','?')} — "
                f"замените плату на чипсет с PCIe Gen{pcie.get('gpu_pcie_gen_original','?')}."
            )

    # PCIe warnings (v2.0 — gen degradation)
    if pcie.get("warnings"):
        warnings.extend(pcie.get("warnings", []))

    if not pcie.get("storage_sustained_write_compliant", True):
        if pcie.get("dram_warning"):
            warnings.append(pcie["dram_warning"])

    # Profile WARNs (Skill 8)
    if profile:
        for warn in profile.get("warnings", []):
            warnings.append(
                f"PROFILE: {warn['component']} — "
                f"{warn['profile']} конфликтует со вторичным интентом "
                f"{warn['conflict_intents']} (вес {warn.get('weight', '?')}) — "
                f"допустимый trade-off. {warn.get('description', '')[:100]}"
            )

    # MVS WARNs (Skill 11)
    if mvs:
        for v in mvs.get("violations", []):
            if v["severity"] == "WARN":
                warnings.append(f"MVS: {v['message']}")

    # Tier proportionality BLOCK — УДАЛЁН (v3.0).
    # Заменён на физические валидаторы:
    #   - CPU_VRM (Skill 13): CPU TDP → MB VRM
    #   - GPU_PCIe (Skill 14): GPU PCIe class → MB slot gen
    #   - Component Floor (Skill 15): intent-based bottleneck minimums

    # CPU VRM BLOCKs (Skill 13)
    if cpu_vrm:
        for v in cpu_vrm.get("violations", []):
            if v["severity"] == "BLOCK":
                failed_checks.append(f"CPU_VRM: {v['message']}")

    # GPU PCIe slot BLOCKs (Skill 14)
    if gpu_pcie:
        for v in gpu_pcie.get("violations", []):
            if v["severity"] == "BLOCK":
                failed_checks.append(f"GPU_PCIe: {v['message']}")

    # Component Floor BLOCKs (Skill 15)
    if comp_floor:
        for v in comp_floor.get("violations", []):
            if v["severity"] == "BLOCK":
                failed_checks.append(f"FLOOR: {v['message']}")
            elif v["severity"] == "WARN":
                warnings.append(f"FLOOR: {v['message']}")

    # Deduplicate
    warnings = list(dict.fromkeys(warnings))

    if failed_checks:
        status = "FAIL"
        action = "rollback"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
        action = "proceed_to_document"
    else:
        status = "PASS"
        action = "proceed_to_document"

    return {
        "validation_status": status,
        "action_required": action,
        "failed_check_ids": failed_checks,
        "warnings": warnings,
        "summary": {
            "PASS": "Все проверки пройдены. Можно формировать Build Artifact.",
            "PASS_WITH_WARNINGS": "Есть предупреждения. Сборка допустима, но с оговорками.",
            "FAIL": "Критические ошибки. Необходим rollback и пересмотр.",
        }[status],
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(validate(data), ensure_ascii=False, indent=2))
