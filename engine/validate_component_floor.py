'''
Skill 15: validate_component_floor — Intent-based bottleneck floor.
CPU↔GPU не равенство. Интент определяет, кто бутылка,
и задаёт минимальный пол для НЕ-бутылочного компонента.

Читает intent_floors.yaml через _pcbo_config.
При изменении требований игр/моделей — правка YAML.
'''

import json, sys
from _pcbo_config import get_intent_floor


def _resolve_floor(floor_def, params: dict | None = None):
    """Resolve floor value. If dict with per-param keys, match against params values.
    E.g. floor_def={"1080p": 6, "4K": 4}, params={"resolution": "4K"} → 4.
    """
    if floor_def is None:
        return None
    if isinstance(floor_def, dict) and params:
        for param_val in params.values():
            pv = str(param_val)
            if pv in floor_def:
                val = floor_def[pv]
                if isinstance(val, dict):
                    return _resolve_floor(val, params)
                return val
        for v in floor_def.values():
            if isinstance(v, (int, float)):
                return v
        return floor_def
    if isinstance(floor_def, dict):
        return None
    return floor_def


def validate(data: dict) -> dict:
    """
    data fields:
      - intent_id: str (e.g., "aaa_gaming_base")
      - intent_params: dict (e.g., {"resolution": "1440p"})
      - cpu: {"cores": int, "tdp_w": int, "id": str, "cache_mb": int}
      - gpu: {"vram_gb": int, "fp32_tflops": float, "id": str, "length_mm": int}
      - ram: {"capacity_gb": int, "id": str}
      - storage: {"capacity_gb": int, "sustained_write": bool, "id": str}
      - case: {"max_gpu_mm": int} (для SFF)
    """
    intent_id = data.get("intent_id", "")
    intent_cfg = get_intent_floor(intent_id)

    if not intent_cfg:
        return {
            "floor_status": "SKIP",
            "summary": f"Интент '{intent_id}' не имеет заданных floors.",
            "violations": [],
        }

    floors = intent_cfg.get("floors", {})
    bottleneck = intent_cfg.get("bottleneck", "unknown")
    intent_params = data.get("intent_params", {})
    violations = []

    cpu = data.get("cpu", {})
    gpu = data.get("gpu", {})
    ram = data.get("ram", {})
    storage = data.get("storage", {})

    # ── CPU cores ──
    min_cores = _resolve_floor(floors.get("cpu_min_cores"), intent_params)
    if min_cores and isinstance(min_cores, (int, float)):
        actual = cpu.get("cores", 0)
        if actual and actual < min_cores:
            violations.append({
                "check": "cpu_cores_floor",
                "severity": "BLOCK" if bottleneck != "cpu" else "WARN",
                "message": (
                    f"CPU FLOOR: {cpu.get('id', '?')} ({actual} ядер) "
                    f"ниже пола {intent_id} = {min_cores} ядер. Бутылка: {bottleneck}."
                ),
                "required": min_cores,
                "actual": actual,
            })

    # ── GPU VRAM ──
    min_vram = _resolve_floor(floors.get("gpu_min_vram_gb"), intent_params)
    if min_vram and isinstance(min_vram, (int, float)) and min_vram > 0:
        actual = gpu.get("vram_gb", 0)
        if actual and actual < min_vram:
            violations.append({
                "check": "gpu_vram_floor",
                "severity": "BLOCK",
                "message": (
                    f"GPU VRAM FLOOR: {gpu.get('id', '?')} ({actual}GB) "
                    f"ниже пола {intent_id} = {min_vram}GB."
                ),
                "required": min_vram,
                "actual": actual,
            })

    # ── GPU TFLOPS ──
    min_tflops = _resolve_floor(floors.get("gpu_min_fp32_tflops"), intent_params)
    if min_tflops and isinstance(min_tflops, (int, float)):
        actual = gpu.get("fp32_tflops", 0)
        if actual and actual < min_tflops:
            violations.append({
                "check": "gpu_tflops_floor",
                "severity": "WARN" if bottleneck == "cpu" else "BLOCK",
                "message": (
                    f"GPU TFLOPS FLOOR: {gpu.get('id', '?')} ({actual}) "
                    f"ниже пола {intent_id} = {min_tflops}."
                ),
                "required": min_tflops,
                "actual": actual,
            })

    # ── RAM capacity ──
    min_ram = _resolve_floor(floors.get("ram_min_capacity_gb"), intent_params)
    if min_ram and isinstance(min_ram, (int, float)):
        actual = ram.get("capacity_gb", 0)
        if actual and actual < min_ram:
            violations.append({
                "check": "ram_capacity_floor",
                "severity": "BLOCK",
                "message": (
                    f"RAM CAPACITY FLOOR: {ram.get('id', '?')} ({actual}GB) "
                    f"ниже пола {intent_id} = {min_ram}GB."
                ),
                "required": min_ram,
                "actual": actual,
            })

    # ── Storage capacity ──
    min_storage = _resolve_floor(floors.get("storage_min_capacity_gb"), intent_params)
    if min_storage and isinstance(min_storage, (int, float)):
        actual = storage.get("capacity_gb", 0)
        if actual and actual < min_storage:
            violations.append({
                "check": "storage_capacity_floor",
                "severity": "WARN",
                "message": (
                    f"STORAGE CAPACITY FLOOR: {storage.get('id', '?')} ({actual}GB) "
                    f"ниже пола {intent_id} = {min_storage}GB."
                ),
                "required": min_storage,
                "actual": actual,
            })

    # ── SFF: GPU length ──
    max_gpu_mm = _resolve_floor(floors.get("gpu_max_length_mm"), intent_params)
    if max_gpu_mm:
        actual_mm = gpu.get("length_mm", 0)
        if actual_mm and actual_mm > max_gpu_mm:
            violations.append({
                "check": "sff_gpu_length",
                "severity": "BLOCK",
                "message": (
                    f"SFF GPU LENGTH: {gpu.get('id', '?')} ({actual_mm}mm) "
                    f"превышает SFF-лимит {max_gpu_mm}mm."
                ),
                "required": f"≤{max_gpu_mm}mm",
                "actual": f"{actual_mm}mm",
            })

    return {
        "floor_status": "FAIL" if any(v["severity"] == "BLOCK" for v in violations)
                        else ("WARN" if violations else "PASS"),
        "summary": (
            f"Floor check для {intent_id} (бутылка: {bottleneck}). "
            f"Нарушений: {len(violations)}."
        ),
        "violations": violations,
        "intent_id": intent_id,
        "bottleneck": bottleneck,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(validate(data), ensure_ascii=False, indent=2))
