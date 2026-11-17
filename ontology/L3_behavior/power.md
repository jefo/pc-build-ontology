---
uri: "pcbo:ontology/L3_behavior/power"
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
    Power state values (Idle/Gaming/Load percentages от TDP) — инженерная оценка.
    Platform overhead (50-80W) и PSU loss (10-15%) — оценки.
    Не верифицированы измерениями из розетки.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/context"        # electricity_cost_kwh, power_outlet_max_W
    - "pcbo:ontology/L4_decision/decision"      # cpu, gpu, psu decisions
  feedsInto:
    - "pcbo:ontology/L5_validation"             # PSU headroom check
    - "pcbo:ontology/L3_behavior/thermal"       # power → heat
    - "pcbo:ontology/L3_behavior/acoustic"      # power → fan speed → noise
  seealso:
    - "pcbo:ontology/L3_behavior/compute"       # compute load → power draw
tags: ["power", "energy", "tdp", "psu", "behavior", "L3", "physical-model"]
---

# L3 · Power Model — энергетическая модель

> Предсказание энергопотребления в разных режимах.
> Основа для: PSU sizing, thermal prediction, acoustic floor, annual cost.

---

## Состояния энергопотребления

```yaml
PowerStates:
  Idle:
    label: "Простой"
    description: "Система включена, рабочий стол, без активных задач."
    cpu_load_pct: "5-10%"
    gpu_load_pct: "0-5% (fan-stop активен)"
    typical_power_W: "50-80W (без монитора)"

  Light_Load:
    label: "Лёгкая нагрузка"
    description: "Браузер, офис, YouTube 4K."
    cpu_load_pct: "10-25%"
    gpu_load_pct: "5-20% (видеодекодинг)"
    typical_power_W: "80-150W"

  Gaming:
    label: "Игровая нагрузка"
    description: "AAA игра на целевом разрешении."
    cpu_load_pct: "40-60% (не все ядра)"
    gpu_load_pct: "90-100%"
    typical_power_W: "250-450W"
    note: "Сильно варьируется: CPU-bound игры — ниже, GPU-bound — выше"

  Full_Load:
    label: "Полная нагрузка"
    description: "CPU + GPU stress одновременно (Prime95 + FurMark)."
    cpu_load_pct: "100%"
    gpu_load_pct: "100%"
    typical_power_W: "450-800W"
    note: "Синтетический сценарий. Не репрезентативен для реальной эксплуатации."

  AI_Load:
    label: "AI Inference"
    description: "GPU compute на 100%, CPU near-idle."
    cpu_load_pct: "10-20% (подготовка батчей)"
    gpu_load_pct: "100% (compute)"
    typical_power_W: "250-400W"
    note: "GPU power limit часто ниже TGP в compute-режиме"
```

---

## Расчётная модель

### System Power

```yaml
SystemPower:
  formula: >
    system_power_W =
      cpu_power_W +
      gpu_power_W +
      platform_overhead_W +
      psu_loss_W

  cpu_power_W:
    formula: "cpu.tdp_W × load_factor"
    load_factor:
      idle:         0.08
      light_load:   0.20
      gaming:       0.50
      rendering:    0.95
      stress:       1.05   # выше TDP на AVX-нагрузках
      ai_inference: 0.20

  gpu_power_W:
    formula: "gpu.tgp_W × load_factor"
    load_factor:
      idle:         0.03   # fan-stop, minimal power
      light_load:   0.15   # видео декодинг
      gaming:       0.90   # близко к TGP в GPU-bound играх
      compute:      0.85   # CUDA/ROCm нагрузки
      stress:       1.00

  platform_overhead_W:
    description: "RAM, чипсет, вентиляторы, RGB, накопители."
    default: 60
    formula: >
      40 + (ram_sticks × 3) + (fan_count × 2) + (rgb ? 10 : 0) + (ssd_count × 3)
    typical_range: "40-80W"

  psu_loss_W:
    formula: "system_power_W × (1.0 - psu_efficiency_at_load)"
    efficiency_at_load:
      80plus_Gold:
        load_20pct:  0.87
        load_50pct:  0.90
        load_100pct: 0.87
      80plus_Platinum:
        load_20pct:  0.90
        load_50pct:  0.92
        load_100pct: 0.89
      80plus_Titanium:
        load_20pct:  0.92
        load_50pct:  0.94
        load_100pct: 0.90
```

### Пример расчёта

```yaml
# Система: Ryzen 7800X3D (120W PPT) + RTX 4070 (200W TGP)
# PSU: 80+ Gold

power_breakdown:
  gaming_load:
    cpu_power_W:      65    # 120W × 0.54
    gpu_power_W:      185   # 200W × 0.925
    platform_overhead_W: 55 # 40 + (2×3) + (3×2) + 3
    subtotal_W:       305
    psu_loss_W:       34    # 305 × (1 - 0.90) при ~50% нагрузке
    system_power_W:   339

  full_load:
    cpu_power_W:      126   # 120W × 1.05 (AVX)
    gpu_power_W:      200   # 200W × 1.0
    platform_overhead_W: 55
    subtotal_W:       381
    psu_loss_W:       42    # 381 × (1 - 0.89) при ~55% нагрузке
    system_power_W:   423

  idle:
    cpu_power_W:      10    # 120W × 0.08
    gpu_power_W:      6     # 200W × 0.03
    platform_overhead_W: 35 # вентиляторы на минимуме
    subtotal_W:       51
    psu_loss_W:       8     # низкая эффективность при малой нагрузке
    system_power_W:   59
```

---

## PSU Sizing

```yaml
PSU_Requirements:
  rule: "psu.wattage ≥ system_power_W_at_gaming × 1.5"
  reasoning: >
    Запас 1.5× от типичной игровой нагрузки обеспечивает:
    - Пиковые нагрузки (GPU transient spikes до 2× TGP на микросекунды)
    - Эффективность (PSU наиболее эффективен при 40-60% нагрузки)
    - Запас для апгрейда
    - Деградацию конденсаторов со временем (~10% за 5 лет)

  absolute_minimum: "psu.wattage ≥ system_power_W_at_full_load × 1.1"
  note: "Это пол, а не рекомендация. Gaming headroom — правильная цель."

  # Из L4/llm-guide RULE 7: PSU — не творческая зона
  # Вычисляется механически, не оптимизируется
```

---

## Годовые эксплуатационные расходы

```yaml
AnnualEnergyCost:
  formula: >
    annual_cost_USD =
      (power_gaming_W × gaming_hours_per_day +
       power_idle_W × idle_hours_per_day +
       power_other_W × other_hours_per_day)
      × 365
      × electricity_cost_kwh
      / 1000

  example:
    gaming_hours: 4
    idle_hours: 10
    other_hours: 2
    electricity_cost_kwh: 0.12   # USD

    daily_kwh: (339×4 + 59×10 + 100×2) / 1000 = 2.146 kWh
    annual_kwh: 2.146 × 365 = 783 kWh
    annual_cost_USD: 783 × 0.12 = $94

    note: "Для сравнения: система с RTX 4090 (600W gaming) = +$75/год"
```

### MOD-CTX-01 (из L1 context) — Высокая стоимость электричества

```yaml
# IF context.electricity_cost_kwh > 0.20
# THEN weight(power_efficiency) += 0.15

ElectricityCostImpact:
  cost_012_per_kwh:  "100W разница = $42/год (4ч gaming/день)"
  cost_025_per_kwh:  "100W разница = $88/год"
  cost_040_per_kwh:  "100W разница = $140/год"

  note: >
    При европейских ценах на электричество (€0.25-0.40/кВт·ч)
    разница в 100W между GPU эквивалентна $100+/год.
    За 4 года это $400 — половина стоимости GPU.
```

---

## Симуляция энергетического поведения

```yaml
PowerPrediction:
  states:
    idle_W:         Integer
    gaming_W:       Integer
    full_load_W:    Integer
    ai_load_W:      Integer    # если релевантно

  psu:
    wattage:            Integer
    headroom_gaming:    Float    # psu.W / gaming_W
    headroom_full_load: Float    # psu.W / full_load_W
    status:             OK | MARGINAL | UNDERSIZED

  annual:
    estimated_cost_USD:  Float
    assumptions:         String   # "(4h gaming, 10h idle, $0.12/kWh)"

  efficiency_gains:
    # Если есть выбор между компонентами с разным TDP
    - description: String
      annual_savings_USD: Float
```

### Пример

```yaml
power_prediction:
  states:
    idle_W: 59
    gaming_W: 339
    full_load_W: 423

  psu:
    wattage: 750
    headroom_gaming: 2.21
    headroom_full_load: 1.77
    status: OK
    note: "Запас достаточен. Пиковые spikes GPU (~1.5×) в пределах."

  annual:
    estimated_cost_USD: 94
    assumptions: "4h gaming, 10h idle/office, 2h mixed, $0.12/kWh"

  efficiency_comparison:
    rtx_4070_vs_4070Ti:
      gaming_power_delta_W: -50
      annual_savings_USD: 44
      note: "RTX 4070 Ti consumes ~50W more in gaming"
```

---

## Антипаттерны энергетических утверждений

### ANTI-PW-01 — Только TDP как мощность системы

```
ANTI-PATTERN: "Система потребляет 320W (120W CPU + 200W GPU)"
PROBLEM: Игнорируются platform overhead (~50-80W) и PSU loss (~10-15%).
CORRECT: "Система потребляет ~340W от розетки в играх (120W CPU + 200W GPU + 55W platform + 34W PSU loss)"
```

### ANTI-PW-02 — PSU «на вырост» без границ

```
ANTI-PATTERN: "Бери 1200W — запас не помешает"
PROBLEM: PSU неэффективен при низкой нагрузке. 1200W при 60W idle = 5% нагрузки = КПД 70-80%.
CORRECT: "750W = 2.2× headroom от gaming нагрузки. 1200W избыточен и менее эффективен в idle."
```

### ANTI-PW-03 — Игнорирование стоимости электричества

```
ANTI-PATTERN: "Разница 50W между GPU не важна"
PROBLEM: При 0.25 EUR/kWh и 6ч/день: 50W × 6h × 365d = 110 kWh × 0.25 = €27/год.
CORRECT: "RTX 4070 vs 4070 Ti: -50W gaming. При €0.25/кВт·ч экономия €27/год."
```
