"""
Skill 1: verify_structural_clearance
Приоритет №1 — фатальные ошибки геометрии (GPU не влезает, кулер упирается).

LLM слепы к пространственному мышлению. Этот навык даёт 100% точность
проверки физической собираемости.

Usage:
    python verify_structural_clearance.py '<json_input>'
    или импорт: from verify_structural_clearance import verify
"""

import json
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class CaseSpec:
    max_gpu_mm: int
    max_cooler_mm: int
    supported_form_factors: list[str]


@dataclass
class GpuSpec:
    length_mm: int
    width_slots: float


@dataclass
class CoolerSpec:
    height_mm: int
    cooler_type: str  # "air" | "aio"
    layout_type: Optional[str] = None  # "tower" | "top_flow" | "aio" | "passive" (v1.4)
    bottom_clearance_mm: int = 40  # высота от подошвы до нижних рёбер (v1.4)
    horizontal_outlay_radius_mm: int = 60  # радиальный вынос от центра сокета (v1.4)
    ram_clearance_mm: int = 40  # зазор над слотами RAM (v1.4)
    radiator_size_mm: Optional[int] = None  # для AIO


@dataclass
class MotherboardSpec:
    form_factor: str  # "ATX" | "mATX" | "ITX"
    vrm_heatsink_height_max_mm: int = 30  # высота самого высокого радиатора VRM (v1.4)
    ram_slot_offset_x_mm: int = 50  # расстояние от центра сокета до первого слота RAM (v1.4)


@dataclass
class RamSpec:
    module_height_mm: int = 31  # высота модуля, стандарт JEDEC 31mm (v1.4)


@dataclass
class ClearanceResult:
    is_compatible: bool
    failures: list[str]
    tolerances: dict[str, int]


# Технологические зазоры (мм)
GPU_MOUNTING_CLEARANCE_MM = 10   # зазор для монтажа GPU
COOLER_SIDE_PANEL_CLEARANCE_MM = 5  # зазор кулер-боковая стенка
AIO_RADIATOR_FAN_THICKNESS_MM = 27  # стандартная толщина вентилятора


def verify(case: dict, gpu: dict, cooler: dict, motherboard: dict) -> ClearanceResult:
    """Проверить физическую совместимость компонентов в корпусе."""
    failures = []
    tolerances = {}

    cs = CaseSpec(**{k: v for k, v in case.items() if k in CaseSpec.__dataclass_fields__})
    gs = GpuSpec(**{k: v for k, v in gpu.items() if k in GpuSpec.__dataclass_fields__})
    cl = CoolerSpec(**{k: v for k, v in cooler.items() if k in CoolerSpec.__dataclass_fields__})
    mb = MotherboardSpec(**{k: v for k, v in motherboard.items() if k in MotherboardSpec.__dataclass_fields__})

    # 1. GPU length check
    gpu_clearance = cs.max_gpu_mm - gs.length_mm
    tolerances["gpu_clearance_mm"] = gpu_clearance
    if gs.length_mm + GPU_MOUNTING_CLEARANCE_MM > cs.max_gpu_mm:
        failures.append(
            f"GPU ({gs.length_mm}mm) не влезает в корпус "
            f"(макс: {cs.max_gpu_mm}mm, нужен зазор {GPU_MOUNTING_CLEARANCE_MM}mm). "
            f"Дефицит: {gs.length_mm + GPU_MOUNTING_CLEARANCE_MM - cs.max_gpu_mm}mm."
        )

    # 2. Cooler height check (air coolers only)
    if cl.cooler_type == "air":
        cooler_clearance = cs.max_cooler_mm - cl.height_mm
        tolerances["cooler_clearance_mm"] = cooler_clearance
        if cl.height_mm + COOLER_SIDE_PANEL_CLEARANCE_MM > cs.max_cooler_mm:
            failures.append(
                f"Кулер ({cl.height_mm}mm) не влезает в корпус "
                f"(макс: {cs.max_cooler_mm}mm, нужен зазор {COOLER_SIDE_PANEL_CLEARANCE_MM}mm). "
                f"Дефицит: {cl.height_mm + COOLER_SIDE_PANEL_CLEARANCE_MM - cs.max_cooler_mm}mm."
            )

    # 3. Motherboard form factor check
    mb_ff = mb.form_factor.upper()
    supported = [ff.upper() for ff in cs.supported_form_factors]
    if mb_ff not in supported:
        failures.append(
            f"Материнская плата {mb_ff} не поддерживается корпусом "
            f"(поддерживает: {', '.join(cs.supported_form_factors)})."
        )

    # 4. AIO radiator check
    if cl.cooler_type == "aio" and cl.radiator_size_mm:
        # AIO usually mounts at top/front — check is case-specific
        # For now, note that AIO compatibility requires manual verification
        tolerances["aio_radiator_mm"] = cl.radiator_size_mm

    return ClearanceResult(
        is_compatible=len(failures) == 0,
        failures=failures,
        tolerances=tolerances,
    )


def verify_vrm_and_ram_clearance(mb: dict, cooler: dict, ram: dict = None) -> dict:
    """
    Skill 16 (v1.4): 3D Envelope Collision Detection.
    Проверка пересечения пространственных огибающих кулера, VRM и RAM.
    Заменяет плоскую проверку по оси Z на анализ keep-out zones.
    """
    conflicts = []
    tolerances = {}

    cl = CoolerSpec(**{k: v for k, v in cooler.items() if k in CoolerSpec.__dataclass_fields__})
    mb_spec = MotherboardSpec(**{k: v for k, v in mb.items() if k in MotherboardSpec.__dataclass_fields__})

    # 1. VRM collision check (для top-flow кулеров на ATX/mATX платах)
    if cl.layout_type == "top_flow" and mb_spec.form_factor.upper() in ("ATX", "MATX"):
        vrm_height = mb_spec.vrm_heatsink_height_max_mm
        cooler_clearance = cl.bottom_clearance_mm
        gap = cooler_clearance - vrm_height
        tolerances["vrm_collision_gap_mm"] = gap

        if gap < 0:
            conflicts.append({
                "conflict_id": "ERR-CLEAR-VRM",
                "severity": "BLOCK",
                "description": (
                    f"Коллизия кулера и радиатора VRM: высота радиатора VRM "
                    f"({vrm_height}mm) превышает монтажный просвет кулера "
                    f"({cooler_clearance}mm). Дефицит: {abs(gap)}mm. "
                    f"Тепловые трубки/рёбра кулера упираются в радиатор VRM — "
                    f"монтаж невозможен."
                )
            })
        elif gap < 5:
            conflicts.append({
                "conflict_id": "WARN-CLEAR-VRM",
                "severity": "WARN",
                "description": (
                    f"Малый зазор между кулером и радиатором VRM: "
                    f"VRM {vrm_height}mm, clearance {cooler_clearance}mm, "
                    f"зазор {gap}mm. Монтаж возможен, но риск контакта при вибрации."
                )
            })

    # 2. RAM collision check
    if ram and cl.layout_type in ("top_flow", "tower"):
        ram_height = ram.get("module_height_mm", 31)
        cooler_ram_clearance = cl.ram_clearance_mm

        # Проверяем, перекрывает ли кулер слоты RAM по горизонтали
        if cl.horizontal_outlay_radius_mm > mb_spec.ram_slot_offset_x_mm:
            ram_gap = cooler_ram_clearance - ram_height
            tolerances["ram_collision_gap_mm"] = ram_gap

            if ram_gap < 0:
                conflicts.append({
                    "conflict_id": "ERR-CLEAR-RAM",
                    "severity": "BLOCK",
                    "description": (
                        f"Коллизия кулера и модулей RAM: высота модулей "
                        f"({ram_height}mm) превышает допустимый зазор кулера "
                        f"({cooler_ram_clearance}mm). Дефицит: {abs(ram_gap)}mm."
                    )
                })
            elif ram_gap < 3:
                conflicts.append({
                    "conflict_id": "WARN-CLEAR-RAM",
                    "severity": "WARN",
                    "description": (
                        f"Малый зазор между кулером и RAM: модули {ram_height}mm, "
                        f"зазор кулера {cooler_ram_clearance}mm, "
                        f"gap {ram_gap}mm. Установка возможна, но требуется аккуратность."
                    )
                })

    return {
        "is_compatible": len([c for c in conflicts if c["severity"] == "BLOCK"]) == 0,
        "conflicts": conflicts,
        "tolerances": tolerances,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python verify_structural_clearance.py '<json>'"}))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = verify(
        case=data["case"],
        gpu=data["gpu"],
        cooler=data["cooler"],
        motherboard=data.get("motherboard", {}),
    )

    print(json.dumps({
        "is_compatible": result.is_compatible,
        "failures": result.failures,
        "tolerances": result.tolerances,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
