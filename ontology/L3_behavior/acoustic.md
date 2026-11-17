---
uri: "pcbo:ontology/L3_behavior/acoustic"
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
    Границы акустических классов (25/35/45 dBA) и правила маппинга
    компонентов на классы — инженерная оценка. Не верифицированы
    инструментальными замерами SPL-метром. Требуют калибровки.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/context"        # noise_constraint, ambient_temp
    - "pcbo:ontology/L4_decision/decision"      # cooling_decision, case_decision
  feedsInto:
    - "pcbo:ontology/L5_validation"             # acoustic class проверяется при валидации
    - "pcbo:ontology/L3_behavior/thermal"       # thermal → fan speed → acoustic
  seealso:
    - "pcbo:ontology/L3_behavior/power"         # system_power_W определяет нижнюю границу класса
tags: ["acoustic", "noise", "behavior", "L3", "physical-model"]
---

# L3 · Acoustic Model — акустическая модель системы

> Уходим от прилагательных «тихий / громкий» к детерминированным классам.
> Акустический класс сборки — это предсказуемое следствие физических параметров,
> а не субъективная оценка.

---

## Акустические классы

```yaml
AcousticClasses:
  A0_Passive:
    dba_range: "0 dBA"
    description: "Нет движущихся частей или Zero-RPM режим на всех компонентах."
    requirements:
      - "PSU: fanless или semi-passive с порогом включения > 150W"
      - "GPU: fan-stop при idle (все современные mid/high-end GPU)"
      - "CPU Cooler: passive (Noctua NH-P1) или AIO с pump-stop"
      - "Case fans: 0 RPM при idle"
    typical_system_power_W: "< 80W в idle"

  A1_Ambient:
    dba_range: "< 25 dBA"
    description: "Сливается с фоном тихой комнаты. Неразличим с 1 метра."
    requirements:
      - "Вентиляторы на минимальных оборотах (< 600 RPM для 120mm)"
      - "PSU: semi-passive (вентилятор выключен при низкой нагрузке)"
      - "Отсутствие coil whine"
    typical_system_power_W: "< 150W под нагрузкой"

  A2_LowHum:
    dba_range: "25-35 dBA"
    description: "Лёгкий шелест воздуха. Не мешает спать или работать."
    note: "Реалистичная цель для большинства хорошо собранных систем."
    requirements:
      - "Вентиляторы 600-900 RPM (120mm)"
      - "AIO pump < 2500 RPM"
      - "GPU fans < 40% PWM"
    typical_system_power_W: "150-350W под нагрузкой"

  A3_Noticeable:
    dba_range: "35-45 dBA"
    description: "Явный шум потока воздуха. Слышен в наушниках открытого типа."
    note: "Типично для компактных сборок (ITX) или бюджетных кулеров."
    requirements:
      - "Вентиляторы 900-1400 RPM (120mm)"
      - "Возможно: турбинный GPU cooler (blower-style)"
    typical_system_power_W: "350-550W под нагрузкой"

  A4_Loud:
    dba_range: "> 45 dBA"
    description: "Дискомфорт без закрытых наушников. Турбины на 100% RPM."
    note: "Приемлемо только для серверных / industrial workloads."
    requirements:
      - "Вентиляторы > 1400 RPM (120mm) или blower GPU на 100%"
    typical_system_power_W: "> 550W под нагрузкой"
```

---

## Правила маппинга (Behavior Rules)

Правила определяют **минимально возможный** акустический класс для заданных физических параметров.
Система не может быть тише, чем диктует самое шумное правило.

```yaml
BehaviorRules:

  # --- Ограничения по энергопотреблению ---
  - id: "ACOUSTIC-POWER-01"
    condition: "system_power_W > 150"
    constraint: "AcousticClass >= A2_LowHum"
    reason: "150W тепловыделения требуют активного airflow; passive невозможен"

  - id: "ACOUSTIC-POWER-02"
    condition: "system_power_W > 350"
    constraint: "AcousticClass >= A3_Noticeable"
    reason: "350W требует высоких оборотов даже на качественных вентиляторах"

  - id: "ACOUSTIC-POWER-03"
    condition: "system_power_W > 550"
    constraint: "AcousticClass >= A4_Loud"
    reason: "550W тепловыделения — индустриальный уровень шума неизбежен"

  # --- Ограничения по охлаждению ---
  - id: "ACOUSTIC-COOLING-01"
    condition: "cooler_type = 'Air_SingleFan_92mm'"
    constraint: "AcousticClass >= A3_Noticeable"
    reason: "92mm вентилятор на высоких оборотах неизбежно шумит"

  - id: "ACOUSTIC-COOLING-02"
    condition: "cooler_type = 'Air_DualTower_140mm'"
    constraint: "AcousticClass <= A2_LowHum"   # этот кулер МОЖЕТ быть тихим
    reason: "Большие вентиляторы на малых оборотах = низкий шум"

  # --- Ограничения по форм-фактору ---
  - id: "ACOUSTIC-FORM-01"
    condition: "form_factor = 'ITX' AND system_power_W > 250"
    constraint: "AcousticClass >= A3_Noticeable"
    reason: "В ITX корпусах ограниченный airflow; вентиляторы работают на повышенных оборотах"

  # --- Ограничения по PSU ---
  - id: "ACOUSTIC-PSU-01"
    condition: "psu_fan_type = 'always-on'"
    constraint: "AcousticClass >= A1_Ambient"
    reason: "PSU с always-on вентилятором добавляет фоновый шум даже в idle"

  - id: "ACOUSTIC-PSU-02"
    condition: "psu_fan_type = 'fanless'"
    constraint: "AcousticClass <= A1_Ambient AT idle"
    reason: "Fanless PSU не производит шума"

  # --- Ограничения по GPU ---
  - id: "ACOUSTIC-GPU-01"
    condition: "gpu_cooler_type = 'blower'"
    constraint: "AcousticClass >= A3_Noticeable AT load"
    reason: "Blower-турбина шумнее открытых вентиляторов"

  - id: "ACOUSTIC-GPU-02"
    condition: "gpu_tier IN ['T1', 'T2'] AND gpu_load = 100%"
    constraint: "AcousticClass >= A2_LowHum AT load"
    reason: "High-end GPU при полной нагрузке потребляет 250W+"
```

---

## Симуляция акустического поведения

Для каждой сборки модель предсказывает акустический класс в трёх состояниях:

```yaml
AcousticPrediction:
  idle:
    class: A0..A4
    dominant_source: ComponentClass   # какой компонент определяет шум
    note: String

  typical_load:                        # gaming / рендеринг / inference
    class: A0..A4
    dominant_source: ComponentClass
    note: String

  synthetic_stress:                    # Prime95 + FurMark
    class: A0..A4
    dominant_source: ComponentClass
    note: String
    is_realistic: Boolean              # stress не отражает реальную эксплуатацию
```

### Пример симуляции

```yaml
# Система: Ryzen 7800X3D + RTX 4070 + Air_DualTower_140mm + ATX
# L1 Context: noise_constraint = moderate

acoustic_prediction:
  idle:
    class: A1_Ambient
    dominant_source: None (все компоненты в fan-stop или < 500 RPM)
    note: "GPU fan-stop активен, PSU semi-passive, case fans 400 RPM"

  typical_load:
    class: A2_LowHum
    dominant_source: GPU
    note: "RTX 4070 вентиляторы ~35% PWM (1200 RPM). CPU cooler 600 RPM."
    mitigation: "Undervolt GPU снижает обороты на 10-15%"

  synthetic_stress:
    class: A3_Noticeable
    dominant_source: GPU
    note: "GPU 100% load → вентиляторы 65% PWM. Не репрезентативно для игр."
    is_realistic: false
```

---

## Взаимодействие с L1 Context

```yaml
# MOD-CTX-03 из L1 context активирует акустические проверки
ContextValidation:
  - IF context.noise_constraint = "silent"
    THEN required: idle ≤ A1_Ambient AND load ≤ A2_LowHum

  - IF context.noise_constraint = "strict"
    THEN required: load ≤ A2_LowHum

  - IF context.noise_constraint = "moderate"
    THEN required: load ≤ A3_Noticeable

  - IF context.noise_constraint = "none"
    THEN required: none (A4 допустим)
```

---

## Взаимодействие с Reliability (coil whine)

Coil whine не увеличивает dBA, но добавляет **тональный шум** (высокочастотный писк), который субъективно воспринимается хуже широкополосного шума вентиляторов:

```yaml
CoilWhineModifier:
  condition: "ReliabilityRisk.CoilWhine.probability >= MEDIUM"
  effect: "AcousticClass.effective = AcousticClass + 1"
  note: "Тональный шум воспринимается на 5-10 dBA громче широкополосного"
  references: "pcbo:ontology/L3_behavior/reliability#CoilWhine"
```

---

## Компонентная база: acoustic signatures

Справочная таблица для L4 Decision — типичные акустические сигнатуры классов компонентов:

```yaml
ComponentAcousticDB:

  CPU_Coolers:
    Air_SingleFan_92mm:    { idle: A2, load: A4 }
    Air_SingleFan_120mm:   { idle: A2, load: A3 }
    Air_DualTower_140mm:   { idle: A1, load: A2 }
    AIO_240mm:             { idle: A1, load: A2 }     # pump noise при idle
    AIO_360mm:             { idle: A1, load: A2 }     # больше радиатор → ниже RPM
    AIO_420mm:             { idle: A1, load: A2 }

  GPU_Coolers:
    Open_Air_2Fan:         { idle: A0, load: A3 }     # fan-stop при idle
    Open_Air_3Fan:         { idle: A0, load: A2 }     # больше вентиляторов → ниже RPM
    Blower:                { idle: A2, load: A4 }
    AIO_Hybrid:            { idle: A1, load: A2 }

  PSU:
    Fanless:               { idle: A0, load: A0 }
    Semi_Passive:          { idle: A0, load: A1 }
    Always_On_120mm:       { idle: A1, load: A2 }
    Always_On_80mm:        { idle: A2, load: A3 }

  Case_Fans:
    140mm_500RPM:          { contribution: "A1" }
    120mm_800RPM:          { contribution: "A1" }
    120mm_1200RPM:         { contribution: "A2" }
    120mm_1500RPM:         { contribution: "A3" }
    92mm_2000RPM:          { contribution: "A4" }
```

---

## Антипаттерны акустических утверждений

Ситуации, которые LLM должен явно отклонять при генерации acoustic_prediction:

### ANTI-AC-01 — Прилагательное вместо класса

```
ANTI-PATTERN: "Система работает тихо"
PROBLEM: "Тихо" не имеет физического смысла.
CORRECT: "Ожидаемый акустический класс: A2_LowHum (25-35 dBA) при типичной нагрузке"
```

### ANTI-AC-02 — Игнорирование физики

```
ANTI-PATTERN: "Бесшумная система с RTX 4090 под нагрузкой"
PROBLEM: 450W тепловыделения физически невозможно охладить без шума.
CORRECT: "A3_Noticeable при полной нагрузке (неизбежно при 450W TGP)"
```

### ANTI-AC-03 — Усреднение

```
ANTI-PATTERN: "Система имеет acoustic class A2"
PROBLEM: Класс разный для idle и load.
CORRECT: "A1_Ambient idle / A2_LowHum load / A3_Noticeable stress"
```
