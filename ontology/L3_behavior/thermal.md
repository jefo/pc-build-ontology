---
uri: "pcbo:ontology/L3_behavior/thermal"
type: "OntologyDocument"
layer: "L3"
version: "3.0.0-draft"
provenance:
  source: "LLM_ESTIMATE"
  model: "gemini-3.1-pro"
  date: "2026-06-02"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    Тепловые диапазоны (Delta T < 50°C / 50-65°C / > 65°C) и значения
    cooler_efficiency_W_per_C являются инженерной оценкой. Не верифицированы
    инструментальными замерами в контролируемых условиях.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/context"        # ambient_temp_celsius, case_airflow
    - "pcbo:ontology/L4_decision/decision"      # cooling_decision, cpu_decision, gpu_decision
  feedsInto:
    - "pcbo:ontology/L5_validation"             # thermal check при валидации
    - "pcbo:ontology/L3_behavior/acoustic"      # higher temp → faster fans → more noise
  seealso:
    - "pcbo:ontology/L3_behavior/power"         # TDP → thermal load
tags: ["thermal", "temperature", "cooling", "behavior", "L3", "physical-model"]
---

# L3 · Thermal Model — тепловая модель системы

> Связываем контекст (ambient temperature) с hardware (TDP, cooler) —
> получаем предсказание температур, а не гадание.

---

## Тепловые состояния

```yaml
ThermalStates:
  T_Safe:
    label: "Холодный режим"
    delta_T_range: "< 50°C"
    description: "Максимальный буст. Температура не ограничивает производительность."
    condition: "T_junction - T_ambient < 50°C"
    boost_behavior: "CPU/GPU держат максимальные частоты неограниченно долго"

  T_Warm:
    label: "Штатная работа"
    delta_T_range: "50-65°C"
    description: "Нормальный рабочий диапазон. Лёгкое снижение буста возможно на отдельных ядрах."
    condition: "50°C ≤ T_junction - T_ambient < 65°C"
    boost_behavior: "Кратковременный буст работает; длительный — с ограничениями"

  T_Throttle:
    label: "Перегрев"
    delta_T_range: "> 65°C"
    description: "Сброс частот для предотвращения повреждения. Производительность деградирует."
    condition: "T_junction - T_ambient ≥ 65°C"
    boost_behavior: "Thermal throttling активен. Частоты снижаются до безопасного уровня."

  T_Critical:
    label: "Критический перегрев"
    delta_T_range: "> 85°C"
    description: "Система близка к T_junction_max. Аварийное выключение возможно."
    condition: "T_junction - T_ambient ≥ 85°C"
    action: "BLOCK в L5 Validation — сборка не должна достигать этого состояния"
```

---

## Расчётная модель

### Базовое уравнение

```
T_component = T_ambient + (Power_W / Cooler_Efficiency_W_per_C)
```

### Компоненты тепловой модели

```yaml
ThermalInputs:
  cpu:
    tdp_W:          Float       # из спецификации CPU (PL1 / PPT)
    max_tdp_W:      Float       # PL2 / max PPT
    tjunction_max_C: Integer    # из спецификации CPU (обычно 89-95°C для Ryzen, 100°C для Intel)

  gpu:
    tgp_W:          Float       # Total Graphics Power
    tjunction_max_C: Integer    # обычно 83-93°C (NVIDIA) или 110°C hotspot (AMD)

  cooler:
    type:           CoolerType
    efficiency_W_per_C: Float   # сколько ватт отводит на градус Цельсия
    rpm_range:      [Integer]   # мин / макс обороты

  case:
    form_factor:    FormFactor
    airflow_class:  Enum[restricted, normal, high_airflow]
    fan_count:      Integer
    fan_config:     String      # e.g. "2×140mm intake, 1×120mm exhaust"
```

### Cooler Efficiency Lookup Table

```yaml
CoolerEfficiencyDB:
  # CPU Air Coolers
  Air_92mm_SingleFan:     { efficiency_W_per_C: 1.8, max_tdp_recommended_W: 95 }
  Air_120mm_SingleFan:    { efficiency_W_per_C: 2.5, max_tdp_recommended_W: 125 }
  Air_120mm_DualFan:      { efficiency_W_per_C: 3.0, max_tdp_recommended_W: 150 }
  Air_DualTower_140mm:    { efficiency_W_per_C: 4.0, max_tdp_recommended_W: 200 }

  # CPU AIO
  AIO_120mm:              { efficiency_W_per_C: 3.0, max_tdp_recommended_W: 120 }
  AIO_240mm:              { efficiency_W_per_C: 4.5, max_tdp_recommended_W: 200 }
  AIO_280mm:              { efficiency_W_per_C: 5.5, max_tdp_recommended_W: 250 }
  AIO_360mm:              { efficiency_W_per_C: 6.5, max_tdp_recommended_W: 300 }
  AIO_420mm:              { efficiency_W_per_C: 7.5, max_tdp_recommended_W: 350 }

  # Custom Loop estimate
  Custom_240mm:           { efficiency_W_per_C: 5.0, max_tdp_recommended_W: 250 }
  Custom_360mm:           { efficiency_W_per_C: 7.0, max_tdp_recommended_W: 350 }
  Custom_Dual360mm:       { efficiency_W_per_C: 10.0, max_tdp_recommended_W: 500 }

  # GPU Coolers (уже на GPU, не выбирается отдельно)
  GPU_OpenAir_2Fan:       { efficiency_W_per_C: 3.5 }
  GPU_OpenAir_3Fan:       { efficiency_W_per_C: 4.5 }
  GPU_Blower:             { efficiency_W_per_C: 2.5 }
  GPU_AIO_Hybrid_240mm:   { efficiency_W_per_C: 5.5 }
```

---

## Формулы расчёта

### CPU

```
cpu_expected_temp_C = ambient_C + (cpu_load_W / cooler_efficiency_W_per_C)

где:
  cpu_load_W = cpu.tdp_W × load_factor
  load_factor:
    gaming:         0.4-0.6   # игры не нагружают все ядра
    rendering:      0.9-1.0   # многопоточный рендер
    ai_inference:   0.2-0.3   # AI inference — GPU-bound, CPU near-idle
    stress:         1.0-1.1   # Prime95 / AVX — выше TDP
```

### GPU

```
gpu_expected_temp_C = ambient_C + (gpu_tgp_W / gpu_cooler_efficiency_W_per_C)

где:
  gpu_tgp_W — из спецификации GPU
  Для hotspot: gpu_hotspot_temp_C = gpu_expected_temp_C + 10-15°C
  Для VRAM:    gpu_vram_temp_C = gpu_expected_temp_C + 5-10°C
```

### Case Ambient

```
case_internal_ambient_C = ambient_C + case_heat_rise_C

где:
  case_heat_rise_C зависит от airflow_class:
    high_airflow:  2-5°C
    normal:        5-10°C
    restricted:    10-20°C
```

---

## Ambient Temperature Interaction

Критическая зависимость, часто игнорируемая в обзорах:

```yaml
AmbientEffect:
  principle: >
    T_effective = T_junction - T_ambient.
    При повышении ambient на 10°C effective cooling margin
    снижается на те же 10°C. Кулер, достаточный при 22°C,
    может быть недостаточен при 32°C.

  example:
    ambient_22C:
      cpu_temp: 72°C
      delta: 50°C          # T_Safe
      cooler_ok: true

    ambient_32C:
      cpu_temp: 82°C
      delta: 50°C           # всё ещё T_Safe
      cooler_ok: true
      note: "Температура выше, но Delta T тот же."

    ambient_35C:
      cpu_temp: 87°C
      delta: 52°C           # T_Warm — near throttle
      cooler_ok: MARGINAL   # вентиляторы на высоких оборотах
```

### MOD-CTX-02 (из L1 context)

```yaml
# IF context.ambient_temp_celsius > 30
# THEN UPGRADE cooler recommendation BY one tier

# Переносим в thermal model:
AmbientUpgradeRule:
  condition: "ambient_C > 30"
  action: "cooler_efficiency_W_per_C *= 0.85"
  reason: "Эффективность охлаждения снижается при высокой ambient"
```

---

## Симуляция теплового поведения

```yaml
ThermalPrediction:
  ambient_C: Integer

  cpu:
    expected_temp_C: Integer
    state: T_Safe | T_Warm | T_Throttle
    throttling_probability: LOW | MEDIUM | HIGH

  gpu:
    expected_temp_C: Integer
    hotspot_temp_C: Integer
    state: T_Safe | T_Warm | T_Throttle
    throttling_probability: LOW | MEDIUM | HIGH

  case_internal_ambient_C: Integer
  overall_state: T_Safe | T_Warm | T_Throttle
```

### Пример симуляции

```yaml
# Система: Ryzen 7800X3D (120W PPT) + RTX 4070 (200W TGP)
# Cooler: Air_DualTower_140mm (efficiency 4.0 W/°C)
# Case: ATX, normal airflow
# Ambient: 28°C

thermal_prediction:
  ambient_C: 28

  cpu:
    tdp_W: 120
    load_W_gaming: 65       # 0.54 × PPT (игры)
    expected_temp_C_gaming: 44     # 28 + (65/4.0)
    expected_temp_C_stress: 58     # 28 + (120/4.0)
    state_gaming: T_Safe
    state_stress: T_Warm
    throttling_probability: LOW

  gpu:
    tgp_W: 200
    expected_temp_C: 72           # 28 + (200/4.5)
    hotspot_temp_C: 85
    state: T_Warm
    throttling_probability: LOW

  case_internal_ambient_C: 35    # 28 + 7°C (normal airflow)

  overall_state: T_Warm
  note: "Температуры в норме. GPU hotspot на границе T_Warm/T_Throttle."
```

---

## Взаимодействие с L5 Validation

```yaml
ThermalValidation:
  BLOCK_CHECKS:
    - condition: "cpu_expected_temp_C > cpu.tjunction_max_C - 5"
      action: FAIL
      message: "CPU temperature exceeds safe margin"

    - condition: "gpu_hotspot_temp_C > 95"
      action: FAIL
      message: "GPU hotspot exceeds safe threshold"

    - condition: "thermal_state = T_Critical"
      action: FAIL
      message: "System enters critical thermal state — redesign required"

  WARN_CHECKS:
    - condition: "thermal_state = T_Throttle"
      action: PASS_WITH_WARNINGS
      message: "System may throttle under sustained load"
      recommendation: "Upgrade cooler OR reduce TDP"

    - condition: "ambient_C > 35 AND cooler_type = 'Air_SingleFan'"
      action: PASS_WITH_WARNINGS
      message: "High ambient + budget cooler — throttling risk"
```

---

## Антипаттерны тепловых утверждений

### ANTI-TH-01 — Игнорирование ambient

```
ANTI-PATTERN: "CPU под этим кулером не превышает 75°C"
PROBLEM: При какой ambient? При 20°C или 35°C?
CORRECT: "При ambient 22°C: CPU 72°C (T_Safe). При ambient 32°C: CPU 82°C (T_Warm)."
```

### ANTI-TH-02 — Только TDP без контекста нагрузки

```
ANTI-PATTERN: "125W TDP требует AIO 240mm"
PROBLEM: Gaming нагрузка = 60W, а не 125W.
CORRECT: "125W TDP. Gaming load ~65W → Air 120mm достаточен. Stress 125W → Air DualTower."
```

### ANTI-TH-03 — Уверенность без модели

```
ANTI-PATTERN: "Температуры будут отличные"
PROBLEM: Нет расчёта, нет cooler efficiency, нет ambient.
CORRECT: "Ожидаемая CPU temp: 58-65°C при gaming. Расчёт: 28°C ambient + (65W / 4.0 W/°C)."
```
