"""
Сквозной прогон всех симуляций + валидаторов + L5 Gate.
v3.0 (2026-06-04): +CPU_VRM, +GPU_PCIe, +Component Floor, −tier_proportionality.

Использование:
    python run_all.py '<build_json>'

build_json содержит все данные для Skills 1-15.
"""

import json, sys
from pathlib import Path

# Allow both `python engine/run_all.py` and `python -m engine.run_all`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_structural_clearance import verify as skill1
from verify_structural_clearance import verify_vrm_and_ram_clearance as skill16  # v1.4: 3D Envelope
from evaluate_pcie_topology import evaluate as skill2
from simulate_thermal_profiles import evaluate as skill3
from evaluate_marginal_value import evaluate as skill4
from calculate_power_states import evaluate as skill5
from assess_acoustic_class import evaluate as skill6
from validate_l5_rules import validate as skill7
from validate_profile_conflicts import validate as skill8
from validate_physical_constraints import validate as skill9
from validate_mvs_allocation import evaluate as skill11
from validate_cpu_vrm import validate as skill13
from validate_gpu_pcie import validate as skill14
from validate_component_floor import validate as skill15


def run_all(build: dict) -> dict:
    results = {}

    # Skill 1: Structural
    if all(k in build for k in ("case", "gpu", "cooler", "motherboard")):
        r1 = skill1(build["case"], build["gpu"], build["cooler"], build["motherboard"])
        results["structural_clearance"] = {
            "is_compatible": r1.is_compatible,
            "failures": r1.failures,
            "tolerances": r1.tolerances,
        }

    # Skill 16: 3D Envelope Collision (v1.4 — VRM + RAM keep-out zones)
    if all(k in build for k in ("cooler", "motherboard")):
        ram_data = build.get("ram", None)
        r16 = skill16(build["motherboard"], build["cooler"], ram_data)
        results["envelope_collision_3d"] = {
            "is_compatible": r16["is_compatible"],
            "conflicts": r16["conflicts"],
            "tolerances": r16["tolerances"],
        }

    # Skill 2: PCIe topology (v2.0 — generation negotiation)
    if "pcie" in build:
        results["pcie_topology"] = skill2(build["pcie"])

    # Skill 3: Thermal (v2.0 — transient soak)
    if "thermal" in build:
        results["thermal_profile"] = skill3(build["thermal"])

    # Skill 4: MV
    if "mv_candidates" in build:
        mv_results = {}
        for name, mv_input in build["mv_candidates"].items():
            mv_results[name] = skill4(**mv_input)
        results["marginal_value"] = mv_results

    # Skill 5: Power
    if "power" in build:
        results["power_state"] = skill5(build["power"])

    # Skill 6: Acoustic
    if "acoustic" in build:
        results["acoustic_class"] = skill6(build["acoustic"])

    # Skill 8: Profile Conflicts
    if "profile_check" in build:
        results["profile_conflicts"] = skill8(build["profile_check"])

    # Skill 9: Physical Constraints
    if "physical_check" in build:
        results["physical_constraints"] = skill9(build["physical_check"])

    # Skill 11: MVS Allocation (v3.0 — +CPU, +RAM)
    mvs_input = {
        "budget": build.get("budget", {}),
        "motherboard": {
            "chipset": build.get("pcie", {}).get("motherboard_chipset", ""),
            "ram_slots": build.get("motherboard", {}).get("ram_slots", 2),
            "m2_slots": build.get("motherboard", {}).get("m2_slots", 1),
            "price": build.get("motherboard", {}).get("price", 0),
        },
        "cpu": build.get("cpu_mvs", {}),
        "ram": build.get("ram_mvs", {}),
    }
    results["mvs_allocation"] = skill11(mvs_input)

    # Skill 13: CPU VRM check
    if "cpu_vrm" in build:
        results["cpu_vrm"] = skill13(build["cpu_vrm"])

    # Skill 14: GPU PCIe slot check
    if "gpu_pcie" in build:
        results["gpu_pcie"] = skill14(build["gpu_pcie"])

    # Skill 15: Component Floor
    if "component_floor" in build:
        results["component_floor"] = skill15(build["component_floor"])

    # Skill 7: L5 Gate
    l5_input = {
        "structural_clearance": results.get("structural_clearance", {}),
        "power_state": results.get("power_state", {}),
        "thermal_profile": results.get("thermal_profile", {}),
        "acoustic_class": results.get("acoustic_class", {}),
        "pcie_topology": results.get("pcie_topology", {}),
        "budget": build.get("budget", {}),
        "profile_conflicts": results.get("profile_conflicts", {}),
        "physical_constraints": results.get("physical_constraints", {}),
        "mvs_allocation": results.get("mvs_allocation", {}),
        "cpu_vrm": results.get("cpu_vrm", {}),
        "gpu_pcie": results.get("gpu_pcie", {}),
        "component_floor": results.get("component_floor", {}),
    }
    results["l5_validation"] = skill7(l5_input)

    return results


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    output = run_all(data)
    print(json.dumps(output, ensure_ascii=False, indent=2))
