'''
Skill 3 (enhanced): simulate_thermal_profiles v2.0 — Transient Thermal Soak
Приоритет №3 — взаимный нагрев и учёт ambient temperature.

v2.0 (2026-06-04): добавлен transient thermal soak
  — расчёт exhaust capacity корпуса (сколько тепла успевает покидать)
  — thermal soak penalty при sustained нагрузке в restricted-корпусах
  — повышенный case_delta для глухих панелей под длительной нагрузкой

LLM считают температуры качественно («кулер хороший — холодно»).
Этот навык даёт численное предсказание с учётом:
- Температуры в помещении (ambient)
- Класса airflow корпуса (restricted/normal/high_airflow)
- Взаимного нагрева GPU→CPU (Airflow Topology)
- Накопления тепла в корпусе (Thermal Soak)
'''

import json, sys
from dataclasses import dataclass

# Airflow delta (нагрев воздуха внутри корпуса относительно ambient) — steady state
AIRFLOW_DELTA = {
    "restricted": 15.0,
    "normal": 8.0,
    "high_airflow": 3.0,
}

# Case exhaust capacity (сколько ватт тепла корпус может вывести) — conservative estimates
CASE_EXHAUST_CAPACITY_W = {
    "high_airflow": 450,     # mesh-панель, 3+ вентилятора
    "normal": 300,           # стандартный корпус с сеткой
    "restricted": 200,       # глухая панель + шумоподавление
}

# Thermal soak: дополнительный нагрев при sustained нагрузке, когда
# heat_generation > exhaust_capacity. Каждые 10W превышения → +0.5°C
THERMAL_SOAK_FACTOR = 0.5  # °C на 10W превышения exhaust

# GPU-CPU mutual heating threshold
GPU_MUTUAL_HEATING_THRESHOLD_W = 200  # если GPU > 200W, греет CPU-кулер
GPU_MUTUAL_HEATING_FACTOR = 0.05     # 5% TGP добавляется к internal ambient

# Typical cooler efficiency (Δ°C per Watt)
COOLER_EFFICIENCY = {
    "air_tower_120mm": 0.25,    # 120mm башня: +1°C за 4W
    "air_tower_140mm": 0.20,    # 140mm башня: +1°C за 5W
    "air_92mm": 0.45,           # 92mm кулер: +1°C за 2.2W
    "aio_240mm": 0.15,          # 240mm AIO
    "aio_280mm": 0.12,          # 280mm AIO
    "aio_360mm": 0.10,          # 360mm AIO
    "box": 0.60,                # Боксовый кулер
}

# Thermal state thresholds
THERMAL_STATES = [
    ("T_Cool", 55),
    ("T_Warm", 75),
    ("T_Hot", 85),
    ("T_Throttle", 95),
]


def classify_thermal(temp_c: float) -> str:
    for state, threshold in THERMAL_STATES:
        if temp_c < threshold:
            return state
    return "T_Critical"


def evaluate(data: dict) -> dict:
    ambient = data["ambient_temp_C"]
    cpu = data["cpu"]
    gpu = data["gpu"]
    cooler = data["cooler"]
    case = data["case"]

    airflow_class = case.get("airflow_class", "normal")

    # 1. Case internal delta (steady-state)
    case_delta = AIRFLOW_DELTA.get(airflow_class, 8.0)
    internal_ambient = ambient + case_delta

    # 2. GPU-CPU mutual heating (Airflow Topology)
    gpu_effective_w = gpu["tgp_W"] * gpu.get("load_factor", 0.9)
    mutual_heating_active = (
        cooler.get("cooler_type", "air") == "air"
        and gpu_effective_w > GPU_MUTUAL_HEATING_THRESHOLD_W
    )
    if mutual_heating_active:
        gpu_heat_contribution = gpu_effective_w * GPU_MUTUAL_HEATING_FACTOR
        internal_ambient += gpu_heat_contribution

    # 3. Thermal Soak (Transient) — v2.0
    cpu_effective_w = cpu["tdp_W"] * cpu.get("load_factor", 0.8)
    total_heat_w = gpu_effective_w + cpu_effective_w
    exhaust_capacity = CASE_EXHAUST_CAPACITY_W.get(airflow_class, 300)
    thermal_soak_active = total_heat_w > exhaust_capacity
    thermal_soak_penalty = 0.0

    if thermal_soak_active:
        excess_w = total_heat_w - exhaust_capacity
        thermal_soak_penalty = (excess_w / 10.0) * THERMAL_SOAK_FACTOR
        internal_ambient += thermal_soak_penalty

    # 4. CPU temperature
    efficiency = COOLER_EFFICIENCY.get(
        cooler.get("efficiency_class", "air_tower_120mm"), 0.25
    )
    cpu_temp = internal_ambient + (cpu_effective_w / (1.0 / efficiency))

    # 5. GPU temperature estimation
    gpu_temp = ambient + case_delta * 0.7 + thermal_soak_penalty * 0.6
    # GPU has direct airflow, so less affected by soak

    return {
        "ambient_temp_C": ambient,
        "case_delta_C": round(case_delta, 1),
        "case_airflow_class": airflow_class,
        "case_exhaust_capacity_W": exhaust_capacity,
        "total_heat_generation_W": round(total_heat_w, 1),
        "thermal_soak_active": thermal_soak_active,
        "thermal_soak_penalty_C": round(thermal_soak_penalty, 1),
        "internal_case_ambient_C": round(internal_ambient, 1),
        "predicted_cpu_temp_C": round(cpu_temp, 1),
        "predicted_gpu_temp_C": round(gpu_temp, 1),
        "cpu_thermal_state": classify_thermal(cpu_temp),
        "gpu_thermal_state": classify_thermal(gpu_temp),
        "is_mutual_heating_active": mutual_heating_active,
    }


if __name__ == "__main__":
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps(evaluate(data), ensure_ascii=False, indent=2))

