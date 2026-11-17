"""
PCBOv2 Pass Contract System — делает падения артефактов отлаживаемыми.

Каждый pass компилятора (Rule Checker → MEVM → Writer) получает явный контракт:
- Input schema: какие поля обязаны быть во входном артефакте
- Output schema: какие поля pass обязан произвести
- Трассировка: при падении — какой pass, какое состояние на входе, какой контракт нарушен

Архитектура:
    1. PassContract — декларативный контракт для каждого pass'а
    2. ContractRegistry — реестр всех контрактов, маппинг pass → contract
    3. PassTracer — обёртка для run_all, которая:
       - валидирует вход перед каждым pass'ом
       - валидирует выход после pass'а
       - при нарушении контракта — трассирует FAIL с полным контекстом
       - генерирует debuggable TraceReport в JSON

Usage:
    from pass_contract import PassContract, ContractRegistry, trace_pipeline

    # Определить контракты для каждого pass'а
    contracts = ContractRegistry()
    contracts.register(
        "structural_clearance",
        input_schema=["case", "gpu", "cooler", "motherboard"],
        output_schema=["is_compatible", "failures", "tolerances"],
        pass_phase="compile",
        description="Skill 1: проверка геометрической совместимости"
    )
    ...

    # Обернуть пайплайн
    result = trace_pipeline(run_all, build, contracts)
"""

import json
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# Lazy imports for PCBO engine modules (avoid circular deps if run_all imports us)
_ENGINE_MODULES = None


def _get_engine_modules():
    global _ENGINE_MODULES
    if _ENGINE_MODULES is None:
        from run_all import (
            skill1, skill2, skill3, skill4, skill5, skill6,
            skill7, skill8, skill9, skill11, skill13, skill14, skill15, skill16,
        )
        _ENGINE_MODULES = {
            "skill1": skill1, "skill2": skill2, "skill3": skill3,
            "skill4": skill4, "skill5": skill5, "skill6": skill6,
            "skill7": skill7, "skill8": skill8, "skill9": skill9,
            "skill11": skill11, "skill13": skill13, "skill14": skill14,
            "skill15": skill15, "skill16": skill16,
        }
    return _ENGINE_MODULES


# ═══════════════════════════════════════════════════════════════════════════════
# PassContract — декларативный контракт
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PassContract:
    """Декларативный контракт для одного pass'а пайплайна."""

    pass_name: str
    pass_phase: str              # "compile" | "mevm" | "generation"
    pass_priority: int           # 1-15, порядок в пайплайне
    description: str
    input_schema: list[str]      # обязательные ключи во входном артефакте
    output_schema: list[str]     # обязательные ключи в выходе pass'а
    optional_input: list[str] = field(default_factory=list)  # опциональные, но проверяемые
    severity: str = "BLOCK"      # BLOCK | WARN — что значит нарушение контракта

    def validate_input(self, data: dict) -> list[str]:
        """Проверить, что все обязательные поля input_schema есть в data."""
        missing = [k for k in self.input_schema if k not in data]
        return missing

    def validate_output(self, data: dict) -> list[str]:
        """Проверить, что все обязательные поля output_schema есть в output.
        Если output_schema — dict с ключом '*', проверяет каждый вложенный элемент."""
        if isinstance(self.output_schema, dict) and "*" in self.output_schema:
            # Схема вида {"*": ["verdict", "marginal_value", ...]} — проверяет каждый кандидат
            sub_schema = self.output_schema["*"]
            missing = []
            for key, value in data.items():
                if isinstance(value, dict):
                    for field in sub_schema:
                        if field not in value:
                            missing.append(f"{key}.{field}")
            return missing
        missing = [k for k in self.output_schema if k not in data]
        return missing


# ═══════════════════════════════════════════════════════════════════════════════
# ContractRegistry — реестр всех контрактов
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContractRegistry:
    """Реестр контрактов для всех pass'ов пайплайна."""

    contracts: dict[str, PassContract] = field(default_factory=dict)

    def register(
        self,
        pass_name: str,
        *,
        input_schema: list[str],
        output_schema: list[str],
        pass_phase: str = "compile",
        pass_priority: int = 0,
        description: str = "",
        optional_input: list[str] | None = None,
        severity: str = "BLOCK",
    ) -> PassContract:
        contract = PassContract(
            pass_name=pass_name,
            pass_phase=pass_phase,
            pass_priority=pass_priority,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            optional_input=optional_input or [],
            severity=severity,
        )
        self.contracts[pass_name] = contract
        return contract

    def get(self, pass_name: str) -> Optional[PassContract]:
        return self.contracts.get(pass_name)

    def get_by_priority(self) -> list[PassContract]:
        return sorted(self.contracts.values(), key=lambda c: c.pass_priority)

    def to_summary(self) -> list[dict]:
        return [
            {
                "pass": c.pass_name,
                "phase": c.pass_phase,
                "priority": c.pass_priority,
                "description": c.description,
                "input_schema": c.input_schema,
                "output_schema": c.output_schema,
            }
            for c in self.get_by_priority()
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# TraceEntry — запись в трассировочном логе
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TraceEntry:
    """Одна запись трассировки: вход, выход, результат контрактной проверки."""

    pass_name: str
    pass_phase: str
    pass_priority: int
    timestamp: str
    status: str                          # "PASS" | "FAIL" | "SKIP" | "ERROR"
    input_state: dict[str, Any] | None = None
    output_state: dict[str, Any] | None = None
    contract: dict[str, Any] | None = None
    violations: list[str] = field(default_factory=list)
    error: str | None = None
    error_traceback: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# TraceReport — итоговый отчёт трассировки
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TraceReport:
    """Полный отчёт трассировки пайплайна."""

    pipeline_status: str                  # "PASS" | "PASS_WITH_WARNINGS" | "FAIL"
    total_passes: int
    passes_executed: int
    passes_failed: int
    passes_skipped: int
    passes_error: int
    traces: list[dict[str, Any]]          # сериализованные TraceEntry
    contract_summary: list[dict[str, Any]]
    generated_at: str

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# PCBO Contract Registry — предопределённые контракты
# ═══════════════════════════════════════════════════════════════════════════════

def build_pcbo_contracts() -> ContractRegistry:
    """Построить реестр контрактов для всех 16 pass'ов PCBOv2."""

    reg = ContractRegistry()

    # ── Compile-time passes (Skills 1–15, детерминированные Python-валидаторы) ──

    reg.register(
        "structural_clearance",
        pass_phase="compile",
        pass_priority=1,
        input_schema=["case", "gpu", "cooler", "motherboard"],
        output_schema=["is_compatible", "failures", "tolerances"],
        description="Skill 1: геометрическая совместимость GPU/кулер/корпус",
    )

    reg.register(
        "envelope_collision_3d",
        pass_phase="compile",
        pass_priority=2,
        input_schema=["cooler", "motherboard"],
        output_schema=["is_compatible", "conflicts", "tolerances"],
        optional_input=["ram"],
        description="Skill 16: 3D-коллизия кулера с VRM и RAM",
    )

    reg.register(
        "pcie_topology",
        pass_phase="compile",
        pass_priority=3,
        input_schema=["gpu", "platform", "motherboard_chipset"],
        output_schema=[
            "gpu_effective_pcie_lanes",
            "gpu_pcie_gen_effective",
            "effective_bandwidth_gbs",
            "warnings",
        ],
        optional_input=["m2_drives_count", "storage_target", "intent"],
        description="Skill 2: PCIe топология — бифуркация, generation negotiation, bandwidth",
    )

    reg.register(
        "thermal_profile",
        pass_phase="compile",
        pass_priority=4,
        input_schema=["ambient_temp_C", "cpu", "gpu", "cooler", "case"],
        output_schema=[
            "predicted_cpu_temp_C",
            "predicted_gpu_temp_C",
            "cpu_thermal_state",
            "gpu_thermal_state",
            "thermal_soak_active",
        ],
        description="Skill 3: термальная симуляция — взаимный нагрев, thermal soak",
    )

    reg.register(
        "marginal_value",
        pass_phase="compile",
        pass_priority=5,
        input_schema=["mv_candidates"],
        output_schema={"*": ["verdict", "marginal_value", "price_delta_pct", "perf_delta_pct"]},
        description="Skill 4: marginal value — ΔPerf% / ΔPrice%",
        severity="WARN",  # MV never BLOCKs — only informs
    )

    reg.register(
        "power_state",
        pass_phase="compile",
        pass_priority=6,
        input_schema=["cpu_tdp_W", "gpu_tgp_W", "psu"],
        output_schema=["status", "messages", "full_load_power_W", "psu_headroom_factor"],
        description="Skill 5: энергобаланс, ATX 3.0, transient spikes",
    )

    reg.register(
        "acoustic_class",
        pass_phase="compile",
        pass_priority=7,
        input_schema=["system_power_W", "components"],
        output_schema=["predicted_acoustic_class_load", "is_compliant", "warnings"],
        optional_input=["noise_constraint"],
        description="Skill 6: математический класс шума, DPC latency risk",
    )

    reg.register(
        "profile_conflicts",
        pass_phase="compile",
        pass_priority=8,
        input_schema=["profile_check"],
        output_schema=["profile_validation_status", "blocks", "warnings"],
        description="Skill 8: профильные конфликты компонентов против интентов",
    )

    reg.register(
        "physical_constraints",
        pass_phase="compile",
        pass_priority=9,
        input_schema=["physical_check"],
        output_schema=["pass", "checks", "blocking_failures"],
        description="Skill 9: бинарные физические стереотипы (SFF/ITX/ATX-совместимость)",
    )

    reg.register(
        "mvs_allocation",
        pass_phase="compile",
        pass_priority=10,
        input_schema=["budget", "motherboard"],
        output_schema=["mvs_status", "violations", "tier_label"],
        optional_input=["cpu", "ram"],
        description="Skill 11: MVS allocation — системный баланс бюджета",
    )

    reg.register(
        "cpu_vrm",
        pass_phase="compile",
        pass_priority=11,
        input_schema=["cpu_vrm"],
        output_schema=["cpu_vrm_status", "violations"],
        description="Skill 13: CPU TDP → MB VRM floor",
    )

    reg.register(
        "gpu_pcie",
        pass_phase="compile",
        pass_priority=12,
        input_schema=["gpu_pcie"],
        output_schema=["gpu_pcie_status", "violations"],
        description="Skill 14: GPU PCIe класс → MB slot floor",
    )

    reg.register(
        "component_floor",
        pass_phase="compile",
        pass_priority=13,
        input_schema=["component_floor"],
        output_schema=["floor_status", "violations"],
        description="Skill 15: intent-based bottleneck floor",
    )

    # ── MEVM pass (Runtime) ──
    # L5 Gate агрегирует результаты всех compile-time skills

    reg.register(
        "l5_validation",
        pass_phase="mevm",
        pass_priority=14,
        input_schema=[
            "structural_clearance",
            "power_state",
            "thermal_profile",
            "pcie_topology",
        ],
        output_schema=["validation_status", "action_required", "failed_check_ids", "warnings"],
        optional_input=[
            "acoustic_class",
            "budget",
            "profile_conflicts",
            "physical_constraints",
            "mvs_allocation",
            "cpu_vrm",
            "gpu_pcie",
            "component_floor",
        ],
        description="Skill 7: L5 Gate — агрегатор, итоговый вердикт (PASS/FAIL/rollback)",
    )

    return reg


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Tracer — обёртка run_all, ловит падения с контекстом
# ═══════════════════════════════════════════════════════════════════════════════

def _serialize_state(obj: Any, max_depth: int = 3) -> Any:
    """Безопасная сериализация состояния артефакта в JSON-совместимый вид."""
    if max_depth <= 0:
        return "<max_depth_reached>"
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serialize_state(v, max_depth - 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_state(v, max_depth - 1) for v in obj[:20]]  # truncate at 20
    if hasattr(obj, "__dataclass_fields__"):
        return {
            k: _serialize_state(getattr(obj, k), max_depth - 1)
            for k in obj.__dataclass_fields__
        }
    return str(obj)


def _extract_input_for_pass(build: dict, contract: PassContract) -> dict:
    """Извлечь релевантное подмножество build-артефакта для данного pass'а."""
    relevant = {}
    for key in contract.input_schema:
        if key in build:
            relevant[key] = build[key]
    for key in contract.optional_input:
        if key in build:
            relevant[key] = build[key]
    return _serialize_state(relevant)


def _run_with_context(
    fn: Callable,
    build: dict,
    contract: PassContract,
    traces: list[TraceEntry],
) -> tuple[Any, TraceEntry]:
    """
    Выполнить pass с полным контекстом трассировки.
    Возвращает (output, trace_entry).
    При любом исключении — трассирует, но НЕ перебрасывает.
    """
    ts = datetime.now(timezone.utc).isoformat()
    input_state = _extract_input_for_pass(build, contract)

    # Проверка входного контракта
    missing_input = contract.validate_input(build)
    if missing_input:
        entry = TraceEntry(
            pass_name=contract.pass_name,
            pass_phase=contract.pass_phase,
            pass_priority=contract.pass_priority,
            timestamp=ts,
            status="SKIP",
            input_state=input_state,
            contract={
                "required_input": contract.input_schema,
                "expected_output": contract.output_schema,
                "phase": contract.pass_phase,
                "severity": contract.severity,
            },
            violations=[
                f"INPUT_CONTRACT_VIOLATION: отсутствуют обязательные поля: {missing_input}"
            ],
        )
        traces.append(entry)
        return None, entry

    # Выполнение pass'а
    try:
        output = fn(build)
    except Exception as e:
        entry = TraceEntry(
            pass_name=contract.pass_name,
            pass_phase=contract.pass_phase,
            pass_priority=contract.pass_priority,
            timestamp=ts,
            status="ERROR",
            input_state=input_state,
            contract={
                "required_input": contract.input_schema,
                "expected_output": contract.output_schema,
                "phase": contract.pass_phase,
                "severity": contract.severity,
            },
            error=str(e),
            error_traceback=traceback.format_exc(),
            violations=[f"PASS_EXECUTION_ERROR: unhandled exception — {e}"],
        )
        traces.append(entry)
        return None, entry

    # Проверка выходного контракта
    missing_output = contract.validate_output(output if isinstance(output, dict) else {})
    serialized_output = _serialize_state(output)

    if missing_output:
        entry = TraceEntry(
            pass_name=contract.pass_name,
            pass_phase=contract.pass_phase,
            pass_priority=contract.pass_priority,
            timestamp=ts,
            status="FAIL",
            input_state=input_state,
            output_state=serialized_output,
            contract={
                "required_input": contract.input_schema,
                "expected_output": contract.output_schema,
                "phase": contract.pass_phase,
                "severity": contract.severity,
            },
            violations=[
                f"OUTPUT_CONTRACT_VIOLATION: pass не произвёл обязательные поля: {missing_output}"
            ],
        )
    else:
        entry = TraceEntry(
            pass_name=contract.pass_name,
            pass_phase=contract.pass_phase,
            pass_priority=contract.pass_priority,
            timestamp=ts,
            status="PASS",
            input_state=input_state,
            output_state=serialized_output,
            contract={
                "required_input": contract.input_schema,
                "expected_output": contract.output_schema,
                "phase": contract.pass_phase,
                "severity": contract.severity,
            },
        )

    traces.append(entry)
    return output, entry


def _run_conditional_pass(
    fn: Callable,
    build: dict,
    contract: PassContract,
    condition_keys: list[str],
    traces: list[TraceEntry],
) -> tuple[Any | None, TraceEntry | None]:
    """
    Выполнить pass только если все condition_keys присутствуют в build.
    При отсутствии условия — SKIP с информативным сообщением.
    """
    if not all(k in build for k in condition_keys):
        ts = datetime.now(timezone.utc).isoformat()
        entry = TraceEntry(
            pass_name=contract.pass_name,
            pass_phase=contract.pass_phase,
            pass_priority=contract.pass_priority,
            timestamp=ts,
            status="SKIP",
            contract={
                "required_input": contract.input_schema,
                "expected_output": contract.output_schema,
                "phase": contract.pass_phase,
                "severity": contract.severity,
            },
            violations=[f"SKIP: отсутствуют данные — нет полей: {[k for k in condition_keys if k not in build]}"],
        )
        traces.append(entry)
        return None, entry
    return _run_with_context(fn, build, contract, traces)


def trace_pipeline(
    run_all_fn: Callable[[dict], dict],
    build: dict,
    contracts: ContractRegistry,
    *,
    verbose: bool = False,
) -> tuple[dict, TraceReport]:
    """
    Обёртка run_all с полной контрактной трассировкой.

    Вместо того чтобы просто вызвать run_all(build), этот метод:
    1. Выполняет каждый pass индивидуально
    2. Валидирует input/output контракты
    3. Трассирует все нарушения
    4. Генерирует TraceReport с полным контекстом

    Returns:
        (final_result, trace_report) — результат run_all и отчёт трассировки.
        Даже при FAIL отдельных passes, final_result содержит best-effort output.
    """
    from run_all import (
        skill1,
        skill2,
        skill3,
        skill4,
        skill5,
        skill6,
        skill7,
        skill8,
        skill9,
        skill11,
        skill13,
        skill14,
        skill15,
        skill16,
    )

    traces: list[TraceEntry] = []
    results: dict[str, Any] = {}

    # ── Compile-time passes (1–13) ──

    # Skill 1: structural_clearance
    contract = contracts.get("structural_clearance")
    if contract:
        cond_keys = ["case", "gpu", "cooler", "motherboard"]
        if all(k in build for k in cond_keys):
            # Специальная обёртка для Skill 1 (Positional args API)
            def _skill1_wrapper(b):
                r = skill1(b["case"], b["gpu"], b["cooler"], b["motherboard"])
                return {
                    "is_compatible": r.is_compatible,
                    "failures": r.failures,
                    "tolerances": r.tolerances,
                }
            out, entry = _run_with_context(_skill1_wrapper, build, contract, traces)
            if out:
                results["structural_clearance"] = out
        else:
            ts = datetime.now(timezone.utc).isoformat()
            missing = [k for k in cond_keys if k not in build]
            entry = TraceEntry(
                pass_name="structural_clearance",
                pass_phase="compile",
                pass_priority=1,
                timestamp=ts,
                status="SKIP",
                contract={"required_input": contract.input_schema, "expected_output": contract.output_schema},
                violations=[f"SKIP: отсутствуют поля: {missing}"],
            )
            traces.append(entry)

    # Skill 16: envelope_collision_3d
    contract = contracts.get("envelope_collision_3d")
    if contract:
        cond_keys = ["cooler", "motherboard"]
        if all(k in build for k in cond_keys):
            def _skill16_wrapper(b):
                ram_data = b.get("ram", None)
                return skill16(
                    b["motherboard"], b["cooler"], ram_data
                )
            out, entry = _run_with_context(_skill16_wrapper, build, contract, traces)
            if out:
                results["envelope_collision_3d"] = out
        else:
            ts = datetime.now(timezone.utc).isoformat()
            missing = [k for k in cond_keys if k not in build]
            traces.append(TraceEntry(
                pass_name="envelope_collision_3d", pass_phase="compile", pass_priority=2,
                timestamp=ts, status="SKIP",
                contract={"required_input": contract.input_schema, "expected_output": contract.output_schema},
                violations=[f"SKIP: отсутствуют поля: {missing}"],
            ))

    # Skill 2: pcie_topology
    contract = contracts.get("pcie_topology")
    if contract:
        def _skill2_wrapper(b):
            return skill2(b["pcie"])
        _run_conditional_pass(_skill2_wrapper, build, contract, ["pcie"], traces)

    # Skill 3: thermal_profile
    contract = contracts.get("thermal_profile")
    if contract:
        def _skill3_wrapper(b):
            return skill3(b["thermal"])
        _run_conditional_pass(_skill3_wrapper, build, contract, ["thermal"], traces)

    # Skill 4: marginal_value — выполняется run_all внутри цикла, трассируем постфактум
    # Skill 5: power_state
    contract = contracts.get("power_state")
    if contract:
        def _skill5_wrapper(b):
            return skill5(b["power"])
        _run_conditional_pass(_skill5_wrapper, build, contract, ["power"], traces)

    # Skill 6: acoustic_class
    contract = contracts.get("acoustic_class")
    if contract:
        def _skill6_wrapper(b):
            return skill6(b["acoustic"])
        _run_conditional_pass(_skill6_wrapper, build, contract, ["acoustic"], traces)

    # Skill 8: profile_conflicts
    contract = contracts.get("profile_conflicts")
    if contract:
        def _skill8_wrapper(b):
            return skill8(b["profile_check"])
        _run_conditional_pass(_skill8_wrapper, build, contract, ["profile_check"], traces)

    # Skill 9: physical_constraints
    contract = contracts.get("physical_constraints")
    if contract:
        def _skill9_wrapper(b):
            return skill9(b["physical_check"])
        _run_conditional_pass(_skill9_wrapper, build, contract, ["physical_check"], traces)

    # Skill 11: mvs_allocation
    contract = contracts.get("mvs_allocation")
    if contract:
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
        def _skill11_wrapper(b):
            _ = b  # unused — mvs_input constructed above
            return skill11(mvs_input)
        out, _ = _run_with_context(_skill11_wrapper, mvs_input, contract, traces)
        if out:
            results["mvs_allocation"] = out

    # Skill 13: cpu_vrm
    contract = contracts.get("cpu_vrm")
    if contract:
        def _skill13_wrapper(b):
            return skill13(b["cpu_vrm"])
        _run_conditional_pass(_skill13_wrapper, build, contract, ["cpu_vrm"], traces)

    # Skill 14: gpu_pcie
    contract = contracts.get("gpu_pcie")
    if contract:
        def _skill14_wrapper(b):
            return skill14(b["gpu_pcie"])
        _run_conditional_pass(_skill14_wrapper, build, contract, ["gpu_pcie"], traces)

    # Skill 15: component_floor
    contract = contracts.get("component_floor")
    if contract:
        def _skill15_wrapper(b):
            return skill15(b["component_floor"])
        _run_conditional_pass(_skill15_wrapper, build, contract, ["component_floor"], traces)

    # Выполняем run_all как fallback для остальных passes
    try:
        final_result = run_all_fn(build)
    except Exception as e:
        final_result = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "validation_status": "ERROR",
            "action_required": "debug",
        }

    # MEVM: L5 Gate
    contract = contracts.get("l5_validation")
    if contract:
        l5_result = final_result.get("l5_validation", {})
        l5_input_state = {
            **{k: final_result.get(k) for k in contract.input_schema},
            **{k: final_result.get(k) for k in contract.optional_input if k in final_result},
        }
        ts = datetime.now(timezone.utc).isoformat()

        missing_output = contract.validate_output(l5_result)
        if missing_output:
            traces.append(TraceEntry(
                pass_name="l5_validation",
                pass_phase="mevm",
                pass_priority=14,
                timestamp=ts,
                status="FAIL",
                input_state=_serialize_state(l5_input_state),
                output_state=_serialize_state(l5_result),
                contract={
                    "required_input": contract.input_schema,
                    "expected_output": contract.output_schema,
                    "phase": "mevm",
                },
                violations=[f"OUTPUT_CONTRACT_VIOLATION: L5 Gate не произвёл поля: {missing_output}"],
            ))
        else:
            l5_status = l5_result.get("validation_status", "UNKNOWN")
            traces.append(TraceEntry(
                pass_name="l5_validation",
                pass_phase="mevm",
                pass_priority=14,
                timestamp=ts,
                status="PASS" if l5_status != "ERROR" else "FAIL",
                input_state=_serialize_state(l5_input_state),
                output_state=_serialize_state(l5_result),
                contract={
                    "required_input": contract.input_schema,
                    "expected_output": contract.output_schema,
                    "phase": "mevm",
                },
            ))

    # Построить TraceReport
    statuses = [t.status for t in traces]
    pipeline_status = "FAIL" if "FAIL" in statuses or "ERROR" in statuses else (
        "PASS_WITH_WARNINGS" if "SKIP" in statuses else "PASS"
    )

    report = TraceReport(
        pipeline_status=pipeline_status,
        total_passes=len(contracts.contracts),
        passes_executed=sum(1 for s in statuses if s == "PASS"),
        passes_failed=sum(1 for s in statuses if s == "FAIL"),
        passes_skipped=sum(1 for s in statuses if s == "SKIP"),
        passes_error=sum(1 for s in statuses if s == "ERROR"),
        traces=[t.__dict__ for t in traces],
        contract_summary=contracts.to_summary(),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    return final_result, report


# ═══════════════════════════════════════════════════════════════════════════════
# CLI для ручного запуска
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI: python pass_contract.py '<build_json>'"""
    contracts = build_pcbo_contracts()

    if len(sys.argv) < 2:
        data = json.load(sys.stdin)
    else:
        data = json.loads(sys.argv[1])

    from run_all import run_all
    result, report = trace_pipeline(run_all, data, contracts)

    print(json.dumps({
        "pipeline_result": result,
        "trace_report": json.loads(report.to_json()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
