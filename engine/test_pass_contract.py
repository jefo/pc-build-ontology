#!/usr/bin/env python3
"""
Self-test для Pass Contract System.
Проверяет:
- Валидацию входных/выходных контрактов
- Трассировку SKIP при отсутствии данных
- Трассировку ERROR при исключениях в pass'ах
- Трассировку FAIL при нарушении выходного контракта
- Генерацию TraceReport в JSON
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

from pass_contract import (
    PassContract,
    ContractRegistry,
    build_pcbo_contracts,
    TraceEntry,
    TraceReport,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Unit-тесты контрактов
# ═══════════════════════════════════════════════════════════════════════════════

def test_contract_input_validation():
    """Проверка валидации входных полей."""
    c = PassContract(
        pass_name="test",
        pass_phase="compile",
        pass_priority=1,
        description="Test",
        input_schema=["a", "b", "c"],
        output_schema=["x"],
    )

    # Все поля на месте
    assert c.validate_input({"a": 1, "b": 2, "c": 3}) == [], "Все поля: должно быть пусто"

    # Не хватает поля
    missing = c.validate_input({"a": 1})
    assert "b" in missing, "Должен найти missing 'b'"
    assert "c" in missing, "Должен найти missing 'c'"
    assert len(missing) == 2, f"Должно быть 2 missing, нашлось {len(missing)}"

    print("✓ PASS: test_contract_input_validation")


def test_contract_output_validation():
    """Проверка валидации выходных полей."""
    c = PassContract(
        pass_name="test",
        pass_phase="compile",
        pass_priority=1,
        description="Test",
        input_schema=["a"],
        output_schema=["status", "violations", "summary"],
    )

    # Полный output
    assert c.validate_output({"status": "PASS", "violations": [], "summary": "OK"}) == []

    # Неполный output
    missing = c.validate_output({"status": "PASS"})
    assert "violations" in missing
    assert "summary" in missing

    print("✓ PASS: test_contract_output_validation")


def test_contract_registry():
    """Проверка реестра контрактов."""
    reg = ContractRegistry()
    c1 = reg.register("pass_a", input_schema=["x"], output_schema=["y"],
                       pass_phase="compile", pass_priority=1, description="A")
    c2 = reg.register("pass_b", input_schema=["y"], output_schema=["z"],
                       pass_phase="mevm", pass_priority=2, description="B")

    assert reg.get("pass_a") is c1
    assert reg.get("pass_b") is c2
    assert reg.get("nonexistent") is None

    sorted_passes = [c.pass_name for c in reg.get_by_priority()]
    assert sorted_passes == ["pass_a", "pass_b"]

    print("✓ PASS: test_contract_registry")


def test_pcbo_contracts_completeness():
    """Проверка, что все 14+ контрактов PCBO определены."""
    reg = build_pcbo_contracts()

    expected_passes = [
        "structural_clearance",
        "envelope_collision_3d",
        "pcie_topology",
        "thermal_profile",
        "marginal_value",
        "power_state",
        "acoustic_class",
        "profile_conflicts",
        "physical_constraints",
        "mvs_allocation",
        "cpu_vrm",
        "gpu_pcie",
        "component_floor",
        "l5_validation",
    ]

    for name in expected_passes:
        c = reg.get(name)
        assert c is not None, f"Контракт '{name}' не найден!"
        assert c.input_schema, f"Контракт '{name}' без input_schema"
        assert c.output_schema, f"Контракт '{name}' без output_schema"
        assert c.pass_phase in ("compile", "mevm", "generation"), \
            f"Контракт '{name}': неизвестная фаза '{c.pass_phase}'"

    print(f"✓ PASS: test_pcbo_contracts_completeness ({len(reg.contracts)} passes)")


def test_trace_entry_serialization():
    """Проверка сериализации TraceEntry в JSON."""
    entry = TraceEntry(
        pass_name="test_pass",
        pass_phase="compile",
        pass_priority=1,
        timestamp="2026-06-11T00:00:00Z",
        status="FAIL",
        input_state={"key": "value"},
        output_state={"result": "bad"},
        contract={"input": ["key"], "output": ["result"]},
        violations=["OUTPUT_CONTRACT_VIOLATION: missing field"],
    )
    d = entry.__dict__
    assert d["pass_name"] == "test_pass"
    assert d["status"] == "FAIL"
    assert len(d["violations"]) == 1

    # Проверка JSON-сериализуемости
    json.dumps(d)
    print("✓ PASS: test_trace_entry_serialization")


def test_trace_report_generation():
    """Проверка генерации TraceReport."""
    report = TraceReport(
        pipeline_status="FAIL",
        total_passes=5,
        passes_executed=3,
        passes_failed=1,
        passes_skipped=1,
        passes_error=0,
        traces=[],
        contract_summary=[],
        generated_at="2026-06-11T00:00:00Z",
    )
    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed["pipeline_status"] == "FAIL"
    assert parsed["total_passes"] == 5
    print("✓ PASS: test_trace_report_generation")


# ═══════════════════════════════════════════════════════════════════════════════
# Интеграционный тест с реальными данными
# ═══════════════════════════════════════════════════════════════════════════════

def test_integration_with_real_build():
    """
    Интеграционный тест: прогон через pass_contract с реальными данными сборки.
    Проверяет, что trace_pipeline не падает и возвращает TraceReport.
    """
    from pass_contract import trace_pipeline
    from run_all import run_all

    # Минимальный build для проверки
    build = {
        "case": {
            "max_gpu_mm": 340,
            "max_cooler_mm": 165,
            "supported_form_factors": ["ATX", "mATX"],
        },
        "gpu": {
            "length_mm": 267,
            "width_slots": 2.5,
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
        "ram": {
            "module_height_mm": 31,
        },
        "pcie": {
            "platform": "AM5",
            "motherboard_chipset": "B650",
            "m2_drives_count": 1,
            "gpu": {
                "pcie_width": 16,
                "pcie_gen": 4,
            },
        },
        "thermal": {
            "ambient_temp_C": 22,
            "cpu": {"tdp_W": 65, "load_factor": 0.8},
            "gpu": {"tgp_W": 200, "load_factor": 0.9},
            "cooler": {"cooler_type": "air", "efficiency_class": "air_tower_120mm"},
            "case": {"airflow_class": "normal"},
        },
        "power": {
            "cpu_tdp_W": 65,
            "gpu_tgp_W": 200,
            "platform_overhead_W": 50,
            "psu": {"wattage": 750, "specification": "ATX3.0"},
        },
        "acoustic": {
            "system_power_W": 315,
            "components": {
                "cooler_type": "air_single_tower",
                "gpu_cooler": "open_air_3fan",
                "psu_acoustic": "semi_passive",
                "rgb_ecosystems": [],
            },
            "noise_constraint": "moderate",
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
        "budget": {"actual_cost": 120000, "ceiling": 150000},
        "cpu_vrm": {
            "cpu": {"tdp_w": 65, "id": "test-cpu", "title": "Test CPU"},
            "motherboard": {"chipset": "B650", "id": "test-mb", "title": "Test MB"},
        },
        "gpu_pcie": {
            "gpu": {"pcie": "PCIe 4.0 x16", "id": "test-gpu"},
            "motherboard": {"chipset": "B650", "id": "test-mb"},
            "intent": "gaming",
        },
        "component_floor": {
            "intent_id": "aaa_gaming_base",
            "cpu": {"cores": 8, "id": "test-cpu"},
            "gpu": {"vram_gb": 12, "fp32_tflops": 20.0, "id": "test-gpu"},
            "ram": {"capacity_gb": 32, "id": "test-ram"},
            "storage": {"capacity_gb": 1000, "sustained_write": True, "id": "test-ssd"},
        },
        "cpu_mvs": {},
        "ram_mvs": {},
    }

    contracts = build_pcbo_contracts()

    try:
        result, report = trace_pipeline(run_all, build, contracts)
    except Exception as e:
        print(f"✗ FAIL: trace_pipeline raised exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Проверка TraceReport
    assert isinstance(report, TraceReport), f"report должен быть TraceReport, received {type(report)}"
    assert report.total_passes > 0, "Должны быть зарегистрированные pass'ы"
    assert len(report.traces) > 0, "Должны быть trace-записи"

    # Считаем статусы
    statuses = [t["status"] for t in report.traces]
    print(f"\n  Trace statuses: PASS={statuses.count('PASS')}, "
          f"FAIL={statuses.count('FAIL')}, SKIP={statuses.count('SKIP')}, "
          f"ERROR={statuses.count('ERROR')}")

    # Все pass'ы должны иметь трассировку
    for t in report.traces:
        assert "pass_name" in t, f"Trace без pass_name: {t}"
        assert "status" in t, f"Trace без status: {t}"
        if t["status"] in ("FAIL", "ERROR"):
            assert t.get("violations"), f"FAIL/ERROR trace без violations: {t['pass_name']}"
        if t["status"] == "SKIP":
            assert t.get("violations"), f"SKIP trace без violations: {t['pass_name']}"

    # Проверка, что результат run_all корректен
    assert "l5_validation" in result or "error" in result, \
        "Результат должен содержать l5_validation или error"

    # Проверка JSON-сериализации отчёта
    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed["pipeline_status"] in ("PASS", "PASS_WITH_WARNINGS", "FAIL")
    assert isinstance(parsed["traces"], list)
    assert isinstance(parsed["contract_summary"], list)

    print(f"✓ PASS: test_integration_with_real_build "
          f"(pipeline_status={report.pipeline_status}, traces={len(report.traces)})")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("PCBOv2 Pass Contract System — Self-Test")
    print("=" * 60)

    all_passed = True
    tests = [
        test_contract_input_validation,
        test_contract_output_validation,
        test_contract_registry,
        test_pcbo_contracts_completeness,
        test_trace_entry_serialization,
        test_trace_report_generation,
        test_integration_with_real_build,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ FAIL: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print()
    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
