---
uri: "pcbo:ontology/L5_validation/validation"
type: "OntologyDocument"
layer: "L5"
version: "3.0.0-draft"
provenance:
  source: "LLM_ESTIMATE"
  model: "gemini-3.1-pro"
  date: "2026-06-02"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    Validation thresholds и severity classifications — инженерная оценка.
    BLOCK/WARN границы требуют калибровки на реальных сборках.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"           # Intent → performance targets
    - "pcbo:ontology/L1_intent/context"          # Context → constraints
    - "pcbo:ontology/L2_constraint"              # Hard constraints
    - "pcbo:ontology/L4_decision/decision"       # Decision chain
    - "pcbo:ontology/L3_behavior/acoustic"       # Акустическая симуляция
    - "pcbo:ontology/L3_behavior/thermal"        # Тепловая симуляция
    - "pcbo:ontology/L3_behavior/compute"        # Вычислительная симуляция
    - "pcbo:ontology/L3_behavior/power"          # Энергетическая симуляция
    - "pcbo:ontology/L3_behavior/latency"        # Latency симуляция
    - "pcbo:ontology/L3_behavior/reliability"    # Reliability риски
    - "pcbo:ontology/L3_behavior/utility_functions"  # MAUT weights
  feedsInto:
    - "pcbo:builds/template"                     # validation_status в Build Artifact
tags: ["validation", "verification", "quality-gate", "L5", "simulation"]
---

# L5 · Validation — протокол верификации сборки

> L5 — это quality gate. Ни одна сборка не покидает систему без прохождения валидации.
> Валидация — не набор советов, а **протокол с жёсткими BLOCK checks**.

---

## Место L5 в пайплайне

```
L1 Intent → L2 Constraints → L4 Decisions → L3 Simulation → L5 Validation
                                                                    │
                                          ┌─────────┬──────────────┘
                                          ▼         ▼
                                        PASS    FAIL / PASS_WITH_WARNINGS
                                          │         │
                                          ▼         ▼
                                    Build        Rollback
                                    Artifact     на L4
                                                 (новые constraints)
```

---

## Статусы валидации

```yaml
ValidationStatus:
  PASS:
    description: "Все BLOCK checks пройдены. Сборка готова к выдаче."
    action: "Сборка переходит в Build Artifact."

  PASS_WITH_WARNINGS:
    description: "BLOCK checks пройдены. Есть WARN проверки, требующие внимания."
    action: "Сборка выдаётся пользователю с предупреждениями."
    required: "Список warnings включён в Build Artifact (блок Active Risks)."

  FAIL:
    description: "Один или несколько BLOCK checks не пройдены."
    action: "Rollback на L4 с новыми constraints."
    forbidden: "НЕ выдавать сборку пользователю. НЕ ослаблять BLOCK checks."
```

---

## Validation Checks

### 1. Structural Compatibility (L2)

```yaml
StructuralValidation:
  - id: "VAL-STRUCT-01"
    type: BLOCK
    check: "cpu.socket = mb.socket"
    fail_message: "CPU socket не совместим с материнской платой"
    rollback_action: "Пересмотреть Platform Decision"

  - id: "VAL-STRUCT-02"
    type: BLOCK
    check: "ram.type = mb.ram_type"
    fail_message: "Тип RAM не совместим с платформой"
    rollback_action: "Пересмотреть RAM Decision"

  - id: "VAL-STRUCT-03"
    type: BLOCK
    check: "ram.channels ≥ 2"
    fail_message: "Single-channel RAM"
    rollback_action: "Выбрать 2-канальный комплект RAM"

  - id: "VAL-STRUCT-04"
    type: BLOCK
    check: "gpu.length_mm ≤ case.max_gpu_mm"
    fail_message: "GPU не помещается в корпус"
    rollback_action: "Выбрать GPU меньшей длины ИЛИ сменить корпус"

  - id: "VAL-STRUCT-05"
    type: BLOCK
    check: "cooler.height_mm ≤ case.max_cooler_mm"
    fail_message: "Кулер не помещается в корпус"
    rollback_action: "Выбрать low-profile кулер ИЛИ сменить корпус"

  - id: "VAL-STRUCT-06"
    type: BLOCK
    check: "mb.form_factor = case.form_factor"
    fail_message: "Форм-фактор MB не совместим с корпусом"
    rollback_action: "Пересмотреть Motherboard Decision"

  - id: "VAL-STRUCT-07"
    type: BLOCK
    check: "psu.form_factor IN case.psu_support"
    fail_message: "PSU форм-фактор не поддерживается корпусом"
    rollback_action: "Выбрать PSU совместимого форм-фактора"
```

### 2. Power Validation (L3 Power Model)

```yaml
PowerValidation:
  - id: "VAL-POWER-01"
    type: BLOCK
    check: "psu.wattage ≥ system_power_W_full_load × 1.1"
    fail_message: "PSU недостаточен для полной нагрузки"
    rollback_action: "Увеличить PSU wattage ИЛИ снизить TDP компонентов"

  - id: "VAL-POWER-02"
    type: WARN
    check: "psu.wattage ≥ system_power_W_gaming × 1.5"
    warn_message: "PSU headroom ниже рекомендованного для gaming (1.5×)"
    recommendation: "Рассмотреть PSU на ступень выше"

  - id: "VAL-POWER-03"
    type: WARN
    check: "psu.wattage ≤ system_power_W_idle × 10"
    warn_message: "PSU значительно переразмерен — низкая эффективность в idle"
    recommendation: "Выбрать PSU с лучшим КПД при низкой нагрузке (Titanium)"

  - id: "VAL-POWER-04"
    type: BLOCK
    check: "system_power_W_full_load < context.power_outlet_max_W"
    fail_message: "Система превышает мощность розетки"
    rollback_action: "Снизить TDP компонентов"
```

### 3. Thermal Validation (L3 Thermal Model)

```yaml
ThermalValidation:
  - id: "VAL-TH-01"
    type: BLOCK
    check: "cpu_expected_temp_C < cpu.tjunction_max_C - 5"
    fail_message: "CPU temperature exceeds safe margin"
    rollback_action: "Улучшить кулер ИЛИ снизить TDP CPU"

  - id: "VAL-TH-02"
    type: BLOCK
    check: "gpu_hotspot_temp_C < 95"
    fail_message: "GPU hotspot exceeds safe threshold"
    rollback_action: "Улучшить airflow корпуса ИЛИ выбрать GPU с лучшим охлаждением"

  - id: "VAL-TH-03"
    type: BLOCK
    check: "thermal_state != T_Critical"
    fail_message: "Система входит в критический тепловой режим"
    rollback_action: "Полный пересмотр Cooling + Case Decision"

  - id: "VAL-TH-04"
    type: WARN
    check: "thermal_state != T_Throttle"
    warn_message: "Система может троттлить под длительной нагрузкой"
    recommendation: "Рассмотреть улучшение охлаждения на 1 tier"
```

### 4. Acoustic Validation (L3 Acoustic Model)

```yaml
AcousticValidation:
  - id: "VAL-AC-01"
    type: BLOCK
    check: >
      IF context.noise_constraint = 'silent'
      THEN acoustic_prediction.idle ≤ A1_Ambient
      AND acoustic_prediction.load ≤ A2_LowHum
    fail_message: "Сборка не удовлетворяет silent constraint"
    rollback_action: "Выбрать компоненты с меньшим TDP, улучшить охлаждение"

  - id: "VAL-AC-02"
    type: BLOCK
    check: >
      IF context.noise_constraint = 'strict'
      THEN acoustic_prediction.load ≤ A2_LowHum
    fail_message: "Сборка превышает strict noise constraint"
    rollback_action: "Заменить бюджетные вентиляторы, рассмотреть undervolt"

  - id: "VAL-AC-03"
    type: BLOCK
    check: >
      IF context.noise_constraint = 'moderate'
      THEN acoustic_prediction.load ≤ A3_Noticeable
    fail_message: "Сборка слишком шумная даже для moderate constraint"

  - id: "VAL-AC-04"
    type: WARN
    check: "acoustic_prediction.load ≥ A3_Noticeable"
    warn_message: "Сборка будет заметно шумной под нагрузкой"
    recommendation: "Рассмотреть undervolt GPU, fan curve настройку"
```

### 5. Compute Validation (L3 Compute Model)

```yaml
ComputeValidation:
  - id: "VAL-CP-01"
    type: BLOCK
    check: "compute_prediction.workloads[primary].status != FAIL"
    fail_message: "Сборка не выполняет целевую нагрузку"
    rollback_action: "Пересмотреть GPU/CPU Decision"

  - id: "VAL-CP-02"
    type: BLOCK
    check: >
      IF intent = aaa_gaming
      THEN fps_1pct_expected ≥ fps_1pct_min
    fail_message: "1% Low FPS ниже минимального порога для intent"

  - id: "VAL-CP-03"
    type: BLOCK
    check: >
      IF intent INCLUDES AI_Inference
      THEN llm_fits_in_vram OR llm_offload_acceptable
    fail_message: "LLM inference не удовлетворяет минимальным требованиям"

  - id: "VAL-CP-04"
    type: WARN
    check: "vram_headroom_GB < 2"
    warn_message: "VRAM на грани. Через 1-2 года станет узким местом."
    recommendation: "Рассмотреть GPU с большим VRAM"
```

### 6. Reliability Validation (L3 Reliability Model)

```yaml
ReliabilityValidation:
  - id: "VAL-RL-01"
    type: BLOCK
    check: "Нет reliability рисков с severity = CRITICAL"
    fail_message: "Критический риск надёжности обнаружен"
    rollback_action: "Заменить проблемный компонент"

  - id: "VAL-RL-02"
    type: WARN
    check: "reliability_prediction.overall.classification != ELEVATED_RISK"
    warn_message: "Повышенный уровень рисков"
    recommendation: "Указать все риски в Build Artifact, предложить mitigation"

  - id: "VAL-RL-03"
    type: WARN
    check: "DDR5_Memory_Training.probability = HIGH"
    warn_message: "Высокая вероятность нестабильности памяти"
    recommendation: "Рассмотреть 2 планки вместо 4"
```

### 7. Budget Validation

```yaml
BudgetValidation:
  - id: "VAL-BUD-01"
    type: BLOCK
    check: "actual_cost_USD ≤ budget_ceiling_USD"
    fail_message: "Сборка превышает жёсткий потолок бюджета"
    rollback_action: "Снизить tier одного или нескольких компонентов"

  - id: "VAL-BUD-02"
    type: WARN
    check: "actual_cost_USD ≤ budget_target_USD × 1.05"
    warn_message: "Сборка превышает целевую точку бюджета на >5%"

  - id: "VAL-BUD-03"
    type: WARN
    check: "budget_allocation_quality ≥ 0.7"
    warn_message: "Бюджет распределён неоптимально"
    recommendation: "Проверить Marginal Value каждого Decision"
```

### 8. Lifecycle Validation

```yaml
LifecycleValidation:
  - id: "VAL-LC-01"
    type: WARN
    check: "upgrade_horizon ближайшего апгрейда ≥ 1 year"
    warn_message: "Первый апгрейд нужен менее чем через год"
    recommendation: "Рассмотреть более мощный компонент сейчас"

  - id: "VAL-LC-02"
    type: WARN
    check: "platform не находится в dead-end состоянии"
    warn_message: "Платформа на грани EOL — апгрейд потребует замены MB"
    recommendation: "Рассмотреть платформу с более длинным upgrade path"
```

---

## Протокол выполнения валидации

```yaml
ValidationProtocol:
  order:
    - "1. Structural (hard blocks — физическая несовместимость)"
    - "2. Power (PSU sizing)"
    - "3. Thermal (температуры)"
    - "4. Acoustic (шум)"
    - "5. Compute (производительность)"
    - "6. Reliability (надёжность)"
    - "7. Budget (стоимость)"
    - "8. Lifecycle (долгосрочность)"

  on_first_BLOCK_failure:
    action: "STOP. Не продолжать валидацию."
    reason: "Последующие проверки невалидны при несовместимых компонентах."

  on_WARN_only:
    action: "Собрать все warnings. Продолжить валидацию до конца."
    result: "PASS_WITH_WARNINGS"

  on_all_clear:
    result: "PASS"
```

---

## Rollback Protocol

Когда L5 возвращает FAIL, система возвращается на L4 с дополнительными constraints:

```yaml
RollbackProtocol:
  # Каждый BLOCK check генерирует constraint для L4
  VAL-STRUCT-04_FAIL:
    new_constraint: "gpu.length_mm ≤ {case.max_gpu_mm}"
    applied_to: "GPU_DECISION"
    action: "Перезапустить GPU Decision с фильтром по длине"

  VAL-POWER-01_FAIL:
    new_constraint: "psu.wattage ≥ {system_power_W_full_load × 1.1}"
    applied_to: "PSU_DECISION"
    action: "Перезапустить PSU Decision с повышенным wattage"

  VAL-TH-01_FAIL:
    new_constraint: "cooler.efficiency_W_per_C ≥ {required_efficiency}"
    applied_to: "COOLING_DECISION"
    action: "Перезапустить Cooling Decision с улучшенным кулером"

  VAL-AC-01_FAIL:
    new_constraint: "acoustic_prediction.load ≤ A2_LowHum"
    applied_to: "COOLING_DECISION + GPU_DECISION"
    action: "Перезапустить с undervolt / более тихими компонентами"

  MAX_ROLLBACKS: 3
  # Если после 3 попыток сборка не валидируется:
  ON_MAX_ROLLBACKS_EXCEEDED:
    action: "Сообщить пользователю о невыполнимости требований"
    output: "Объяснение конфликта ограничений (какие constraints противоречат)"
    example: >
      "Невозможно собрать silent (A2) систему с RTX 4090 в ITX корпусе
       при бюджете $2000. Конфликт: thermal (450W TGP требует airflow),
       acoustic (airflow = шум), budget (custom loop превышает бюджет).
       Предложения: (1) увеличить бюджет до $2800, (2) снизить GPU до RTX 4080,
       (3) перейти на ATX корпус с лучшим airflow."
```

---

## Выход валидации: Build Artifact блок

```yaml
# Включается в Build Artifact (template.md)
validation:
  status: PASS | PASS_WITH_WARNINGS | FAIL
  date: Date
  checks_run: Integer
  blocks_failed: Integer
  warnings: Integer

  simulation_summary:
    acoustic_idle: A0..A4
    acoustic_load: A0..A4
    thermal_cpu_C: Integer
    thermal_gpu_C: Integer
    compute_mode: String
    power_gaming_W: Integer

  active_warnings:
    - check_id: String
      message: String
      recommendation: String
```

---

## Антипаттерны валидации

### ANTI-VL-01 — Ослабление BLOCK при FAIL

```
ANTI-PATTERN: "BLOCK check не пройден, но сборка хорошая — пропустим"
PROBLEM: BLOCK checks существуют потому что это жёсткие инженерные границы.
CORRECT: Rollback на L4 с новым constraint. НЕ ослаблять проверку.
```

### ANTI-VL-02 — PASS без L3 симуляции

```
ANTI-PATTERN: "Сборка выглядит нормально — PASS"
PROBLEM: Без L3 симуляции валидация = гадание.
CORRECT: "L3 acoustic: A2_LowHum. L3 thermal: CPU 75°C (T_Warm). L3 compute: FPS 1% low 55-70 (smooth). → PASS."
```

### ANTI-VL-03 — Умалчивание WARN пользователю

```
ANTI-PATTERN: "PASS_WITH_WARNINGS — но warnings не показаны"
PROBLEM: Warnings — это честность. Пользователь должен знать о граничных состояниях.
CORRECT: Включить все warnings в Build Artifact (секция Active Risks).
```
