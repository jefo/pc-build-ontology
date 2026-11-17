---
uri: "pcbo:ontology/L2_constraint/operational"
type: "OntologyDocument"
layer: "L2"
version: "3.0.0-draft"
provenance:
  source: "LLM_ESTIMATE"
  model: "gemini-3.1-pro"
  date: "2026-06-02"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    Операциональные ограничения (thermal margin, noise envelope, power budget) —
    инженерная оценка. Числовые пороги не верифицированы измерениями.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"         # Intent → какие constraints активны
    - "pcbo:ontology/L1_intent/context"        # Context → параметры constraints
  feedsInto:
    - "pcbo:ontology/L4_decision/decision"      # Активирует MOD-CTX, влияет на выбор
    - "pcbo:ontology/L3_behavior/thermal"       # Thermal constraint → cooling requirement
    - "pcbo:ontology/L3_behavior/acoustic"      # Noise constraint → acoustic class ceiling
    - "pcbo:ontology/L5_validation"             # VAL-POWER, VAL-TH, VAL-AC checks
  seealso:
    - "pcbo:ontology/L2_constraint/structural"  # Физические ограничения
tags: ["constraint", "operational", "thermal", "noise", "power", "L2"]
---

# L2 · Operational Constraints — эксплуатационные ограничения

> Не всё что физически совместимо — разумно.
> Operational constraints определяют границы допустимой работы системы.

---

## Power Budget Constraint

```yaml
PowerBudget:
  formula: "system_power_W ≤ psu.wattage × 0.85"
  reasoning: >
    PSU не должен работать на >85% номинала длительно.
    Запас 15% учитывает: transient spikes, capacitor aging, efficiency curve.

  hard_ceiling: "system_power_W_full_load < psu.wattage"
  soft_target: "system_power_W_gaming < psu.wattage × 0.70"
  reason_soft: "40-60% нагрузки = пик КПД для 80+ Gold"

  # Из L1 Context
  power_outlet_limit_W:
    condition: "context.power_outlet_max_W задан"
    constraint: "system_power_W_full_load < context.power_outlet_max_W × 0.85"
    note: "Запас 15% на другие устройства на той же линии"

  ups_sizing:
    condition: "context.ups_exists = true"
    constraint: "system_power_W_full_load < ups.wattage × 0.75"
    note: "UPS обычно рассчитан на 75% нагрузки для sustained operation"
```

---

## Thermal Envelope Constraint

```yaml
ThermalEnvelope:
  formula: "T_component = T_ambient + (TDP_W / cooler_efficiency)"
  constraint: "T_component ≤ T_junction_max - thermal_margin"

  thermal_margin_C:
    standard: 10       # запас на degradation, пыль, пиковые нагрузки
    conservative: 15   # жаркий климат, плохой airflow
    aggressive: 5      # custom loop, кондиционируемое помещение

  ambient_adjustment:
    # MOD-CTX-02: при высокой ambient — увеличить margin
    condition: "context.ambient_temp_celsius > 30"
    action: "thermal_margin_C += 5"

  cpu_thermal_limit:
    constraint: "cpu_expected_temp_C ≤ cpu.tjunction_max_C - thermal_margin_C"
    note: "Ryzen: tjmax = 89-95°C. Intel: tjmax = 100°C."

  gpu_thermal_limit:
    constraint: "gpu_expected_temp_C ≤ 83"
    note: "NVIDIA начинает снижать boost при ~83°C. AMD hotspot до 110°C."
```

---

## Noise Envelope Constraint

```yaml
NoiseEnvelope:
  # Из L1 Context: noise_constraint
  silent:
    idle_max_class: A1_Ambient
    load_max_class: A2_LowHum
    note: "Требует: fanless/semi-passive PSU, premium cooling, low-TDP GPU"

  strict:
    idle_max_class: A1_Ambient
    load_max_class: A2_LowHum
    note: "Допустим лёгкий шум под нагрузкой"

  moderate:
    load_max_class: A3_Noticeable
    note: "Заметный шум допустим. Типично для большинства сборок."

  none:
    load_max_class: A4_Loud
    note: "Шум не важен. Любые компоненты допустимы."

  # Активация MOD-CTX-03
  activation:
    condition: "context.noise_constraint IN [silent, strict]"
    effects:
      - "BLOCK: components WHERE noise_rating = 'loud'"
      - "PREFER: PSU semi-passive OR fanless"
      - "PREFER: cooler_type = Air_DualTower OR AIO_360"
      - "REJECT: budget_fans, blower_GPU"
```

---

## Budget Allocation Constraint

```yaml
BudgetAllocation:
  # Бюджет — общий ресурс. Каждый Decision потребляет его часть.

  allocation_rules:
    - id: "ALLOC-01"
      description: "Primary component получает 25-40% бюджета"
      constraint: >
        primary_component_cost / total_budget IN [0.25, 0.40]
      exception: "Для budget builds (< $600) primary может занимать до 45%"

    - id: "ALLOC-02"
      description: "PSU — 5-10% бюджета, не меньше $60"
      constraint: >
        psu_cost / total_budget IN [0.05, 0.10]
        AND psu_cost ≥ 60
      note: "Экономия на PSU = риск для всей системы"

    - id: "ALLOC-03"
      description: "Cooling — 5-10% бюджета для gaming, до 15% для silent"
      constraint: "cooler_cost / total_budget IN [0.05, 0.15]"

    - id: "ALLOC-04"
      description: "MB не должна быть дороже CPU"
      constraint: "mb_cost ≤ cpu_cost"
      exception: "ITX сборки (дорогие ITX платы)"

    - id: "ALLOC-05"
      description: "RAM не дороже GPU в gaming-сборках"
      constraint: "ram_cost ≤ gpu_cost × 0.5"
      note: "Исключение: AI/Compute где RAM критична"

  # Метрика качества распределения бюджета
  budget_allocation_quality:
    formula: >
      BAQ = 1.0 - Σ |actual_share_i - target_share_i| / 2
      где target_share_i — рекомендованная доля компонента в бюджете
    interpretation:
      "0.9-1.0": "Отличное распределение"
      "0.7-0.9": "Приемлемо"
      "0.5-0.7": "Перекос — проверить Marginal Value"
      "< 0.5": "Неоптимально — пересмотреть Decisions"
```

---

## Physical Dimension Constraints

```yaml
DimensionConstraints:
  # Активируются MOD-CTX-05 (ITX)
  case_clearance:
    gpu_length:
      constraint: "gpu.length_mm + clearance_mm ≤ case.max_gpu_mm"
      clearance_mm: 10  # зазор для удобства установки

    cooler_height:
      constraint: "cooler.height_mm + clearance_mm ≤ case.max_cooler_mm"
      clearance_mm: 5

    radiator_thickness:
      condition: "cooler_type INCLUDES AIO"
      constraint: "radiator_thickness_mm + fan_thickness_mm ≤ case.radiator_clearance_mm"

  itx_specific:
    - "PSU form_factor = SFX PREFERRED"
    - "GPU length ≤ 300mm TYPICAL (зависит от корпуса)"
    - "Cooler height ≤ 70mm для sandwich layout"
    - "M.2 storage preferred (экономия места)"
```

---

## Software Dependency Constraints

```yaml
SoftwareConstraints:
  # Активируются MOD-CTX-06

  davinci_resolve:
    constraint: "GPU vendor = NVIDIA PREFERRED"
    reason: "CUDA acceleration значительно быстрее OpenCL в Resolve"
    block_amd: false    # не BLOCK, но WARN

  linux:
    constraint: "GPU vendor = AMD PREFERRED"
    reason: "Open-source драйверы (Mesa) — лучше чем проприетарный NVIDIA"
    note: "NVIDIA на Linux работает, но с ограничениями (Wayland, Gamescope)"

  macos_hackintosh:
    constraint: "GPU vendor = AMD"
    reason: "NVIDIA не поддерживается macOS с эпохи Kepler"
    block_nvidia: true  # BLOCK
    supported_gpu: ["RX 6600", "RX 6800", "RX 6900", "RX 6950 XT"]

  ai_ml_frameworks:
    tensorflow_pytorch:
      constraint: "GPU vendor = NVIDIA"
      reason: "CUDA — единственный first-class citizen для ML-фреймворков"
      note: "ROCm (AMD) работает, но с ограничениями (Linux-only, не все GPU)"
```

---

## Constraint Interaction Matrix

Ограничения могут конфликтовать. Приоритет разрешения:

```yaml
ConstraintPriority:
  # При конфликте — вышестоящее ограничение побеждает
  priority_order:
    - 1: "Физическая совместимость (L2 Structural)"
    - 2: "Бюджетный потолок (L1 Context)"
    - 3: "Noise constraint (L1 Context → L2 Operational)"
    - 4: "Thermal safety (L2 Operational)"
    - 5: "Программные зависимости (L1 Context)"
    - 6: "Эстетические предпочтения (L1 Context)"

  conflict_resolution_example:
    scenario: "Silent build, бюджет $1200, нужен мощный GPU для 1440p AAA"
    conflict:
      - "Silent → low TDP GPU (RTX 4060 Ti)"
      - "1440p AAA → RTX 4070 minimum"
      - "Budget → не хватает на premium cooling"
    resolution: >
      1. Бюджет $1200 = ceiling (приоритет 2) — не нарушать.
      2. Noise = strict (приоритет 3) — смягчаем с silent до strict.
      3. В strict: load ≤ A2_LowHum.
      4. RTX 4070 + качественный air cooler + undervolt → A2_LowHum достижимо.
      5. Сообщить пользователю: downgrade с silent до strict.
```
