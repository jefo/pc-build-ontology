'''
Skill 2 (enhanced): evaluate_pcie_topology v2.0 — Interface Protocol Validation
Приоритет №2 — «тихий убийца» производительности.

v2.0 (2026-06-04): добавлена проверка PCIe generation negotiation
  — карта 5.0 в слоте 4.0 = падение bandwidth вдвое
  — effective_bandwidth_GBs vs minimum_required_bandwidth_GBs
  — WARN при деградации поколения

LLM не читают таблицы бифуркации из мануалов. Этот навык детектирует:
- Потерю линий GPU при установке 2+ M.2 (x16 → x8)
- Падение поколения PCIe (Gen5→Gen4, Gen4→Gen3)
- DRAM-less SSD под data engineering (скорость упадёт до HDD)
- Падение offload bandwidth для AI-нагрузок
'''

import json, sys
from _pcbo_config import get_chipset_pcie_gen, get_bifurcation_chipsets

# Bifurcation chipsets (GPU loses lanes with 2+ M.2)
BIFURCATION_CHIPSETS = set(get_bifurcation_chipsets())

# PCIe bandwidth per lane per generation (GB/s, 128b/130b encoding for 3.0+, 8b/10b for 2.0)
PCIe_BW_PER_LANE = {
    1: 0.250,
    2: 0.500,
    3: 0.985,
    4: 1.969,
    5: 3.938,
}

# Minimum bandwidth thresholds for GPU classes (GB/s)
MIN_GPU_BANDWIDTH_GBS = {
    "enthusiast_unrestricted": 28.0,   # 4K path tracing, LLM inference
    "balanced_performance": 20.0,       # 1440p high
    "mainstream_efficiency": 14.0,      # 1080p, esports
}


def _calculate_bandwidth(gen: int, lanes: int) -> float:
    """Calculate effective PCIe bandwidth in GB/s."""
    bw_per_lane = PCIe_BW_PER_LANE.get(gen, 1.969)
    return round(lanes * bw_per_lane, 1)


def evaluate(data: dict) -> dict:
    platform = data["platform"]
    chipset = data.get("motherboard_chipset", "")
    m2_count = data.get("m2_drives_count", 1)
    gpu = data["gpu"]
    storage = data.get("storage_target", {})
    intent = data.get("intent", "")

    warnings = []
    
    # ── PCIe Generation Negotiation (v2.0) ──
    gpu_pcie_gen = gpu.get("pcie_gen", 4)
    slot_pcie_gen = get_chipset_pcie_gen(chipset)
    effective_gen = min(gpu_pcie_gen, slot_pcie_gen)
    generation_degraded = effective_gen < gpu_pcie_gen
    
    gpu_physical_lanes = gpu["pcie_width"]
    
    # 1. Bifurcation check (lane stealing)
    gpu_effective_lanes = gpu_physical_lanes
    if chipset in BIFURCATION_CHIPSETS and m2_count >= 2:
        gpu_effective_lanes = 8
        warnings.append(
            f"BIFURCATION: На чипсете {chipset} при {m2_count} M.2-накопителях "
            f"GPU переходит в режим x{gpu_effective_lanes} (вместо x{gpu_physical_lanes}). "
            f"Линии чипсета разделены между M.2 и PCIe-слотом."
        )

    # 2. Generation negotiation (v2.0)
    if generation_degraded:
        original_bw = _calculate_bandwidth(gpu_pcie_gen, gpu_effective_lanes)
        effective_bw = _calculate_bandwidth(effective_gen, gpu_effective_lanes)
        degradation_pct = round((1 - effective_bw / original_bw) * 100)
        warnings.append(
            f"PCIe GEN DEGRADATION: GPU поддерживает Gen{gpu_pcie_gen}, "
            f"но чипсет {chipset} предоставляет только Gen{slot_pcie_gen}. "
            f"Эффективная полоса: {effective_bw} GB/s "
            f"(потеря {degradation_pct}% относительно Gen{gpu_pcie_gen} ×{gpu_effective_lanes} = {original_bw} GB/s)."
        )
    else:
        effective_bw = _calculate_bandwidth(effective_gen, gpu_effective_lanes)

    # 3. Minimum bandwidth check (v2.0)
    bandwidth_warning = None
    # Determine GPU class from bandwidth
    if effective_bw < MIN_GPU_BANDWIDTH_GBS.get("mainstream_efficiency", 14.0):
        bandwidth_warning = (
            f"BANDWIDTH BOTTLENECK: Effective PCIe bandwidth {effective_bw} GB/s "
            f"(Gen{effective_gen} ×{gpu_effective_lanes}) ниже минимального порога "
            f"для современных GPU ({MIN_GPU_BANDWIDTH_GBS['mainstream_efficiency']} GB/s). "
            f"Текстуры высокого разрешения будут загружаться с задержкой."
        )
        warnings.append(bandwidth_warning)
    elif effective_bw < MIN_GPU_BANDWIDTH_GBS.get("balanced_performance", 20.0):
        bandwidth_warning = (
            f"BANDWIDTH WARNING: Effective PCIe bandwidth {effective_bw} GB/s "
            f"(Gen{effective_gen} ×{gpu_effective_lanes}) ниже рекомендованного уровня "
            f"для 1440p+ гейминга ({MIN_GPU_BANDWIDTH_GBS['balanced_performance']} GB/s). "
            f"Возможны микрофризы при потоковой подгрузке текстур."
        )
        warnings.append(bandwidth_warning)

    # 4. AI workload bandwidth impact
    offload_bandwidth_gbs = None
    if gpu_effective_lanes < gpu_physical_lanes and "inference" in intent.lower():
        offload_bandwidth_gbs = effective_bw
        warnings.append(
            f"AI_OFFLOAD: RAM Offload bandwidth снижен до {offload_bandwidth_gbs:.1f} GB/s "
            f"(x{gpu_effective_lanes} вместо x{gpu_physical_lanes}). "
            f"LLM 70B offload будет в 2× медленнее."
        )

    # 5. DRAM-less SSD under data engineering
    storage_compliant = True
    dram_warn = None
    if "data_engineering" in intent.lower() and not storage.get("dram_cache", True):
        storage_compliant = False
        dram_warn = (
            "VAL-DATA-01: DRAM-less SSD (HMB) непригоден для data engineering. "
            "После исчерпания SLC-кэша скорость записи упадёт до 200-400 MB/s "
            "(уровень HDD). Требуется SSD с DRAM-буфером или TLC с устойчивой записью."
        )
        warnings.append(dram_warn)

    return {
        "gpu_effective_pcie_lanes": gpu_effective_lanes,
        "gpu_pcie_gen_effective": effective_gen,
        "gpu_pcie_gen_original": gpu_pcie_gen,
        "slot_pcie_gen": slot_pcie_gen,
        "generation_degraded": generation_degraded,
        "effective_bandwidth_gbs": effective_bw,
        "bandwidth_warning": bandwidth_warning,
        "intent": intent,  # pass through for L5 gaming BLOCK check
        "offload_bandwidth_gbs": round(offload_bandwidth_gbs, 1) if offload_bandwidth_gbs else None,
        "storage_sustained_write_compliant": storage_compliant,
        "dram_warning": dram_warn,
        "warnings": warnings,
        "original_gpu_lanes": gpu_physical_lanes,
        "lane_loss": gpu_physical_lanes - gpu_effective_lanes,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(evaluate(data), ensure_ascii=False, indent=2))
