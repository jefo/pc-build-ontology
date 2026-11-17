---
uri: "pcbo:ontology/L3_behavior/reliability"
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
    Reliability risks и их вероятности — инженерная оценка на основе
    известных паттернов, сообществ (r/nvidia, r/amd, OCN, LTT forum)
    и обзорной практики. Не верифицированы статистическими данными RMA.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L4_decision/decision"      # каждый Decision содержит risks
  feedsInto:
    - "pcbo:ontology/L5_validation"             # reliability risks учитываются валидацией
    - "pcbo:ontology/L3_behavior/acoustic"      # coil whine → acoustic class shift
    - "pcbo:ontology/L3_behavior/thermal"       # thermal cycling → degradation
  seealso:
    - "pcbo:ontology/L1_intent/context"         # user_skill_level влияет на risk tolerance
tags: ["reliability", "risk", "coil-whine", "failure", "behavior", "L3", "physical-model"]
---

# L3 · Reliability Model — модель надёжности и рисков

> Легализуем инженерные «болячки», о которых молчат маркетологи.
> Каждая сборка несёт известные риски. Их перечисление — честность, а не пессимизм.

---

## Реестр рисков

```yaml
ReliabilityRisks:

  # --- Электрические / акустические ---
  Coil_Whine:
    category: "Electrical / Acoustic"
    description: >
      Высокочастотный писк дросселей на GPU/PSU/MB при высокой нагрузке.
      Физически безопасен, но акустически раздражает.
    triggers:
      - "GPU Tier T0-T1 (high-end — больше дросселей, выше токи)"
      - "High FPS scenarios (меню игр, esports при 300+ FPS)"
      - "PSU бюджетного сегмента (упрощённая фильтрация)"
    probability:
      GPU_T0_T1_highfps:           HIGH
      GPU_T2_T3_any_load:          MEDIUM
      GPU_T4_any_load:             LOW
    impact: "AcousticClass +1 (тональный шум воспринимается громче)"
    mitigation:
      - "FPS cap в меню (RTSS / драйвер)"
      - "Undervolt GPU (снижает ток через дроссели)"
      - "PSU с качественной фильтрацией (Seasonic Prime, Corsair RMx)"
    residual_risk: "Даже на premium GPU может проявляться при 500+ FPS"
    references: "pcbo:ontology/L3_behavior/acoustic#CoilWhineModifier"

  # --- Память ---
  DDR5_Memory_Training:
    category: "Memory / Platform"
    description: >
      DDR5 выполняет memory training при каждом холодном старте.
      Время training растёт с объёмом и количеством планок.
    triggers:
      - "4 sticks of RAM (2DPC конфигурация)"
      - "Total capacity > 64GB"
      - "High-speed kits (DDR5-7200+)"
    probability:
      "2×16GB DDR5-6000":          LOW
      "2×32GB DDR5-6000":          LOW
      "4×16GB DDR5-6000":          MEDIUM
      "4×32GB DDR5-6000":          HIGH
      "4×48GB DDR5-5600":          HIGH
    impact:
      - "First boot: +30-90s на memory training"
      - "EXPO instability: возможны BSOD при нестабильном профиле"
      - "Subsequent warm boots: training пропускается (Memory Context Restore)"
    mitigation:
      - "2 sticks вместо 4 (1DPC оптимально для DDR5)"
      - "QVL-проверенные киты (список совместимости MB)"
      - "Memory Context Restore = Enabled (пропускает training при warm boot)"
      - "Stress test: TestMem5 / Karhu 24h после сборки"
    residual_risk: "На некоторых MB training может сбрасываться после обновления BIOS"

  EXPO_XMP_Instability:
    category: "Memory / Platform"
    description: >
      Заводской разгон (EXPO/XMP) не гарантирует стабильность на конкретном CPU IMC.
      Зависит от silicon lottery контроллера памяти.
    triggers:
      - "DDR5-6400+ (выше официальной поддержки AMD 6000 / Intel 5600)"
      - "4 sticks на любых частотах"
      - "Budget MB (слабая трассировка памяти)"
    probability:
      DDR5_6000_2sticks_quality_MB: LOW
      DDR5_6400_2sticks:             MEDIUM
      DDR5_6400_4sticks:             HIGH
      DDR5_7200_any:                 HIGH
    mitigation:
      - "Выбор частоты на 1-2 ступени ниже максимума"
      - "QVL-проверка материнской платы"
      - "Двухранговые 2×32GB вместо 4×16GB"
    residual_risk: "Даже QVL не гарантирует на конкретном экземпляре CPU"

  # --- Вентиляторы / охлаждение ---
  Fan_Failure:
    category: "Mechanical"
    description: "Выход из строя вентилятора (подшипник, смазка, кабель)."
    probability:
      quality_fan_Noctua_bequiet:   LOW       # MTBF > 150,000h
      mid_range_fan:                LOW       # MTBF > 100,000h
      budget_fan:                   MEDIUM    # MTBF > 30,000h
      sleeve_bearing:               MEDIUM    # деградация через 2-3 года
      FDB_rifle_bearing:            LOW       # деградация минимальна
    impact:
      single_fan: "Компонент без охлаждения → throttling → возможно повреждение"
      multi_fan:  "Остальные вентиляторы компенсируют → повышенный шум"
    mitigation:
      - "Предпочтение FDB / rifle bearing"
      - "Минимум 2 front-intake (отказ одного не критичен)"
      - "Мониторинг RPM в HWiNFO / FanControl (alert если RPM = 0)"

  AIO_Pump_Failure:
    category: "Mechanical / Liquid"
    description: "Отказ помпы AIO. Без циркуляции жидкости CPU мгновенно перегревается."
    probability:
      quality_AIO:                  LOW       # Arctic / EK / Lian Li — MTBF > 70,000h
      budget_AIO:                   MEDIUM
    impact: "CPU → T_Critical за 30-60 секунд. Автоматическое выключение."
    mitigation:
      - "Air cooler не имеет этого failure mode (принципиальное преимущество)"
      - "HWiNFO alert на pump RPM"
    residual_risk: "Даже качественная помпа может отказать — движущаяся часть"

  AIO_Permeation:
    category: "Mechanical / Liquid"
    description: "Жидкость медленно диффундирует через шланги. Через 5-7 лет уровень падает."
    probability:
      age_lt_3y:                    LOW
      age_3_5y:                     MEDIUM
      age_gt_5y:                    HIGH
    impact: "Бульканье, пузыри в помпе, снижение эффективности охлаждения."
    mitigation:
      - "Air cooler лишён этой проблемы"
      - "Заливаемые AIO (refillable) — редкость"
    residual_risk: "Все AIO имеют ограниченный срок службы (5-7 лет)"

  # --- Деградация ---
  Thermal_Paste_Degradation:
    category: "Material / Temporal"
    description: "Термопаста высыхает и теряет теплопроводность."
    probability:
      factory_paste_3y:             MEDIUM
      quality_paste_3y:             LOW
    impact: "+3-8°C через 3-5 лет"
    mitigation:
      - "Замена термопасты раз в 2-3 года"
      - "PTM7950 (Honeywell) — не деградирует (фазовый переход)"
    note: "Часто игнорируется. Простая операция с большим эффектом."

  PSU_Capacitor_Aging:
    category: "Material / Temporal"
    description: "Электролитические конденсаторы в PSU деградируют со временем."
    probability:
      quality_PSU_5y:               LOW
      quality_PSU_10y:              MEDIUM
      budget_PSU_5y:                MEDIUM
    impact: "PSU теряет 10-20% эффективной ёмкости → нестабильность при пиковых нагрузках"
    mitigation: "Выбор PSU с запасом по мощности (20-30%)"
    references: "pcbo:ontology/L6_lifecycle/lifecycle#PSU_degradation"

  # --- Платформа ---
  Bent_Socket_Pins:
    category: "Assembly / Handling"
    description: "Погнутые пины в LGA сокете при установке CPU."
    probability:
      expert_installer:             LOW
      beginner_installer:           MEDIUM
    impact: "Каналы памяти не работают. RMA не принимается."
    mitigation: "Установка CPU в сервисе. Видео-инструкция."
    notes: "Особенно актуально для LGA 1700/1851. AM5 (LGA) тоже."

  BIOS_Update_Brick:
    category: "Platform / Firmware"
    description: "Неудачное обновление BIOS (отключение питания, несовместимость)."
    probability:
      USB_Flashback_supported:      LOW       # можно восстановить без CPU
      USB_Flashback_absent:         MEDIUM
    mitigation:
      - "MB с USB Flashback / Q-Flash Plus"
      - "ИБП (UPS) на время обновления"
```

---

## Матрица рисков × Intent

Не все риски одинаково важны для всех Intent:

```yaml
RiskRelevanceMatrix:
  silent_build:
    critical:    [Coil_Whine, Fan_Failure]
    moderate:    [AIO_Pump_Failure, Thermal_Paste_Degradation]
    irrelevant:  [DDR5_Memory_Training]

  esports_240hz:
    critical:    [Coil_Whine]               # high FPS → high risk
    moderate:    [EXPO_XMP_Instability]      # RAM speed важна
    irrelevant:  [AIO_Permeation]

  aaa_gaming_1440p:
    critical:    []
    moderate:    [Coil_Whine, Thermal_Paste_Degradation]
    irrelevant:  []

  ai_inference_local:
    critical:    [Coil_Whine]               # GPU 100% load постоянно
    moderate:    [Fan_Failure, Thermal_Paste_Degradation]
    irrelevant:  [DDR5_Memory_Training]

  video_editing:
    critical:    [EXPO_XMP_Instability]      # 64GB+ RAM common
    moderate:    [AIO_Pump_Failure]
    irrelevant:  [Coil_Whine]
```

---

## Симуляция reliability

```yaml
ReliabilityPrediction:
  risks:
    - id: String
      category: String
      probability: LOW | MEDIUM | HIGH
      severity: LOW | MEDIUM | HIGH | CRITICAL
      trigger_condition: String
      mitigation_applied: [String]
      residual_risk: String

  overall_reliability_score:
    # Простейший scoring — сумма severity × probability
    score: Integer   # ниже = лучше
    classification: HIGH_RELIABILITY | STANDARD | ELEVATED_RISK
```

### Пример

```yaml
# Система: Ryzen 7800X3D + RTX 4070 + 2×16GB DDR5-6000 + Air_DualTower
# Intent: aaa_gaming_1440p

reliability_prediction:
  risks:
    - id: Coil_Whine
      category: Electrical
      probability: MEDIUM
      severity: LOW
      trigger: "GPU T2 + high FPS в меню"
      mitigation_applied: ["FPS cap 240 в драйвере"]
      residual_risk: "Возможен писк в меню игр без FPS cap"

    - id: DDR5_Memory_Training
      category: Memory
      probability: LOW
      severity: LOW
      note: "2×16GB DDR5-6000 — оптимальная конфигурация"

    - id: Fan_Failure
      category: Mechanical
      probability: LOW
      severity: MEDIUM
      mitigation_applied: ["FDB bearing", "2 front intake redundancy"]

    - id: Thermal_Paste_Degradation
      category: Material
      probability: LOW
      severity: LOW
      note: "Air cooler — простая замена пасты через 2-3 года"

  overall:
    score: 4               # низкий = надёжно
    classification: HIGH_RELIABILITY
    note: "Air cooling + 2-stick RAM + mid-tier GPU = минимальные точки отказа"
```

---

## Антипаттерны reliability-утверждений

### ANTI-RL-01 — Замалчивание рисков

```
ANTI-PATTERN: "Сборка идеальна, рисков нет"
PROBLEM: Любая инженерная система имеет известные failure modes.
CORRECT: "Известные риски: coil whine (MEDIUM при high FPS), memory training (LOW с 2×16GB)."
```

### ANTI-RL-02 — Прилагательные вместо вероятностей

```
ANTI-PATTERN: "Coil whine маловероятен"
PROBLEM: «Маловероятен» не даёт baseline для сравнения.
CORRECT: "Coil whine probability: MEDIUM для RTX 4070 (Tier 2) при 300+ FPS."
```

### ANTI-RL-03 — Игнорирование временных рисков

```
ANTI-PATTERN: "AIO остывает отлично"
PROBLEM: AIO через 5 лет = permeation + pump wear. Air cooler живёт 10+ лет.
CORRECT: "AIO эффективен сейчас, но срок службы 5-7 лет vs 10+ лет для air."
```
