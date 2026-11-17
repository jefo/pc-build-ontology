#!/usr/bin/env python3
"""
Demo: показываем, как Pass Contract System делает падения отлаживаемыми.

Сценарий: GPU (350mm) не влезает в корпус (340mm максимум).
Pass Contract System покажет:
- Какой pass упал: structural_clearance (Skill 1)
- В каком состоянии был артефакт: входной build с case/gpu/cooler/motherboard
- Какой контракт нарушен: выходной контракт — is_compatible = False, failures непуст
- Контекст: полное состояние на входе в pass
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from pass_contract import build_pcbo_contracts, trace_pipeline
from run_all import run_all


def demo_broken_gpu():
    """GPU не влезает в корпус — structural_clearance BLOCK."""

    build = {
        "case": {
            "max_gpu_mm": 340,   # Корпус максимум 340mm
            "max_cooler_mm": 165,
            "supported_form_factors": ["ATX", "mATX"],
        },
        "gpu": {
            "length_mm": 358,    # RTX 5090 — 358mm
            "width_slots": 3.5,
        },
        "cooler": {
            "height_mm": 155,
            "cooler_type": "air",
            "layout_type": "tower",
            "horizontal_outlay_radius_mm": 55,
        },
        "motherboard": {
            "form_factor": "ATX",
            "ram_slots": 4,
            "m2_slots": 2,
            "vrm_heatsink_height_max_mm": 30,
            "ram_slot_offset_x_mm": 50,
        },
        "pcie": {
            "platform": "AM5",
            "motherboard_chipset": "B650",
            "m2_drives_count": 1,
            "gpu": {"pcie_width": 16, "pcie_gen": 5},
        },
        "thermal": {
            "ambient_temp_C": 22,
            "cpu": {"tdp_W": 120, "load_factor": 0.8},
            "gpu": {"tgp_W": 450, "load_factor": 0.9},
            "cooler": {"cooler_type": "air", "efficiency_class": "air_tower_120mm"},
            "case": {"airflow_class": "normal"},
        },
        "power": {
            "cpu_tdp_W": 120,
            "gpu_tgp_W": 450,
            "platform_overhead_W": 50,
            "psu": {"wattage": 750, "specification": "ATX3.0"},
        },
        "acoustic": {
            "system_power_W": 620,
            "components": {
                "cooler_type": "air_single_tower",
                "gpu_cooler": "open_air_3fan",
                "psu_acoustic": "active_standard",
                "rgb_ecosystems": [],
            },
            "noise_constraint": "moderate",
        },
        "budget": {"actual_cost": 350000, "ceiling": 350000},
        "cpu_vrm": {
            "cpu": {"tdp_w": 120, "id": "intel-i9-14900k", "title": "i9-14900K"},
            "motherboard": {"chipset": "B650", "id": "asus-b650e-proart", "title": "B650E ProArt"},
        },
        "gpu_pcie": {
            "gpu": {"pcie": "PCIe 5.0 x16", "id": "nvidia-rtx-5090"},
            "motherboard": {"chipset": "B650", "id": "asus-b650e-proart"},
            "intent": "aaa_4k",
        },
        "component_floor": {
            "intent_id": "aaa_gaming_base",
            "intent_params": {"resolution": "4K"},
            "cpu": {"cores": 24, "id": "i9-14900K"},
            "gpu": {"vram_gb": 32, "fp32_tflops": 82.0, "id": "RTX 5090", "length_mm": 358},
            "ram": {"capacity_gb": 64, "id": "DDR5-6000"},
            "storage": {"capacity_gb": 2000, "sustained_write": True, "id": "SN850X"},
        },
        "profile_check": {
            "components": [],
            "user_intents": [],
            "primary_intent": "",
        },
        "physical_check": {
            "components": {},
            "constraints": {},
        },
        "cpu_mvs": {},
        "ram_mvs": {},
    }

    contracts = build_pcbo_contracts()
    result, report = trace_pipeline(run_all, build, contracts)

    print("=" * 70)
    print("DEMO: Падение артефакта — GPU не влезает в корпус")
    print("=" * 70)

    print(f"\nPipeline Status: {report.pipeline_status}")
    print(f"Passes executed: {report.passes_executed}/{report.total_passes}")
    print(f"Failed: {report.passes_failed}, Skipped: {report.passes_skipped}, Errors: {report.passes_error}")

    print("\n── Failed / Violated Passes ──")
    for t in report.traces:
        if t["status"] in ("FAIL", "ERROR"):
            print(f"\n  ❌ {t['pass_name']} (phase={t['pass_phase']}, priority={t['pass_priority']})")
            print(f"     Status: {t['status']}")
            if t.get("violations"):
                for v in t["violations"]:
                    print(f"     ⚠  {v}")
            if t.get("input_state"):
                print(f"     📥 Input state: {json.dumps(t['input_state'], ensure_ascii=False, indent=8)[:500]}...")
            if t.get("error_traceback"):
                print(f"     🐞 Traceback (first 300 chars):\n{t['error_traceback'][:300]}")

    print(f"\n── L5 Gate Result ──")
    l5 = result.get("l5_validation", {})
    print(f"  Validation status: {l5.get('validation_status', 'N/A')}")
    print(f"  Action required: {l5.get('action_required', 'N/A')}")
    if l5.get("failed_check_ids"):
        print(f"  BLOCK checks:")
        for chk in l5["failed_check_ids"]:
            print(f"    - {chk}")

    print(f"\n── Full TraceReport (JSON snippet) ──")
    json_str = report.to_json()
    # Show first 2000 chars
    print(json_str[:2000])
    print("...")

    print("\n✅ Demo complete. Contract tracing works.")


if __name__ == "__main__":
    demo_broken_gpu()
