---
uri: "pcbo:reasoning/synthesis"
type: "Algorithm"
version: "3.0.0-draft"
layer: "Reasoning"
provenance:
  source: "ENGINEERING_DERIVATION"
  date: "2026-06-03"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    Порядок состояний (DAG) выведен из топологических зависимостей
    компонентов PC. STATE_0-5 — deterministic. STATE_6 (L3 Simulation) —
    поведенческая модель. STATE_7 (Validation Gate) — quality gate.
    Rollback лимит (3 попытки) — инженерная оценка.
    severity: info
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"
    - "pcbo:ontology/L1_intent/context"
    - "pcbo:ontology/L1_intent/workload"
    - "pcbo:ontology/L2_constraint"
    - "pcbo:ontology/L3_behavior"
    - "pcbo:ontology/L4_decision"
    - "pcbo:ontology/L5_validation"
    - "pcbo:reasoning/allocation"
  feedsInto:
    - "pcbo:builds/template"
    - "pcbo:meta/llm-guide"
tags: ["reasoning", "synthesis", "algorithm", "state-machine", "DAG"]
---

# Reasoning · Synthesis — Алгоритм Сборки

> Сборка — это направленный ациклический граф (DAG).  
> Компоненты нельзя выбирать в случайном порядке.  
> Выбор материнской платы до выбора CPU и корпуса — топологическая ошибка.

---

## DAG визуализация

```
STATE_0: Context_Initialization
         │
         ▼
STATE_1: Primary_Component_Selection   ← [Rollback target]
         │
         ▼
STATE_2: Platform_Core
         │
         ▼
STATE_3: Memory_Subsystem
         │
         ▼
STATE_4: Physical_Foundation
         │
         ▼
STATE_5: Power_and_Thermals
         │
         ▼
STATE_6: Behavioral_Simulation (L3)
         │
         ▼
STATE_7: Validation_Gate (L5)
         │
         ├── PASS ──→ STATE_8: Artifact_Generation
         │
         └── FAIL ──→ STATE_1 (с новыми constraints)
                        ↑
                        │  (max 3 rollbacks)
                        │
                  ON_MAX_EXCEEDED:
                  Сообщить о невыполнимости
```

---

## STATE_0 · Context Initialization

```yaml
STATE_0:
  name: "Context_Initialization"
  inputs:
    - "User_Request (сырые данные от пользователя)"
    - "pcbo:ontology/L1_intent/intent"
    - "pcbo:ontology/L1_intent/context"
    - "pcbo:ontology/L1_intent/workload"

  outputs:
    - "BuildGoal (структурированный)"
    - "Active_Constraints (из L2)"
    - "Active_Modifiers (MOD-CTX-01..06)"
    - "Active_Workload_Profiles"

  action:
    step_1: "Определить primary и secondary intent из запроса"
    step_2: "Извлечь context parameters (бюджет, регион, шум, ambient temp)"
    step_3: "Загрузить workload profiles, релевантные intent"
    step_4: "Применить MOD-CTX правила (сдвиги весов utility functions)"
    step_5: "Загрузить AR-02 Target Allocation Matrix для intent"

  validation:
    - "Все обязательные поля BuildGoal заполнены?"
    - "Нет конфликтующих constraints? (например, silent + ITX + 14900K)"
    - "Бюджет реалистичен для intent? (если AAA 4K за $500 — предупредить)"

  on_incomplete_data:
    action: "Запросить пользователя. НЕ угадывать."
    minimum_required:
      - "Основная задача (intent)"
      - "Бюджетный потолок (ceiling)"
      - "Разрешение монитора (для gaming)"
      - "Специальные ограничения (шум, размер, ОС)"
```

---

## STATE_1 · Primary Component Selection

```yaml
STATE_1:
  name: "Primary_Component_Selection"
  depends_on: [STATE_0]

  description: >
    Определить доминантный компонент из матрицы Intent → Primary Component
    (intent.md). Выделить ему бюджет согласно AR-02 target range.
    Это центральное решение, вокруг которого строится вся сборка.

  action:
    step_1: >
      Определить primary_component_class из intent.md (матрица Intent → Доминант).
      Пример: ai_inference → GPU, esports_240hz → CPU, silent_build → Cooling.

    step_2: >
      Выделить бюджет: budget_primary = ceiling × AR-02[primary_component].range_upper.
      Пример: $1500 × 0.55 = $825 на GPU для ai_inference.

    step_3: >
      Сформировать candidate set (3-5 вариантов) из компонентов,
      удовлетворяющих active constraints (TDP, VRAM, размер).

    step_4: >
      Для каждого candidate вычислить MAUT utility score U(candidate)
      используя utility_functions.md + контекстные модификаторы из STATE_0.

    step_5: >
      Применить AR-03 (Marginal Value) для сравнения candidates.
      Выбрать candidate с max U, проходящий все BLOCK constraints.

    step_6: >
      Заполнить Decision (candidates, selected, rejected с MV, rationale,
      tradeoffs, risks).

  outputs:
    - "Selected_Primary (компонент)"
    - "Primary_Decision (Decision artifact)"
    - "Remaining_Budget = ceiling − primary.price"
    - "Budget_Allocation_Log (куда ушли деньги)"

  constraints:
    - "primary.price ДОЛЖЕН быть в пределах AR-02 target range для своего класса"
    - "Если AR-03 возвращает REJECT для всех candidates дороже baseline → выбор baseline"
    - "Если BLOCK constraint отсекает всех candidates кроме одного → confidence=LOW, задокументировать"

  anti_patterns:
    - "Выбор 'лучшего на рынке' без учёта бюджета остальных компонентов"
    - "Выбор без MAUT scoring (ANTI-UT-03)"
    - "Один кандидат без rejection (ANTI-02 из decision.md)"
```

---

## STATE_2 · Platform Core

```yaml
STATE_2:
  name: "Platform_Core"
  depends_on: [STATE_1]

  description: >
    Выбрать связку CPU + Platform Type. Это решение определяет:
    сокет, тип RAM, поколение PCIe, upgrade horizon.

  action:
    step_1: "Определить platform candidates: AM5, LGA1851, LGA1700"
    step_2: "Для каждой платформы определить совместимые CPU в оставшемся бюджете"
    step_3: >
      Проверить Bottleneck Index (BI) с Selected_Primary:
      IF primary = GPU: cpu ДОЛЖЕН обеспечивать BI < 15% при целевом разрешении
      IF primary = CPU: это и есть primary (esports) — этот шаг = STATE_1
    step_4: "Применить MOD-CTX-04 (upgrade_path) если бюджет низкий + horizon длинный"
    step_5: "Заполнить Platform Decision + CPU Decision"

  outputs:
    - "Selected_CPU"
    - "Selected_Platform (AM5/LGA1851/...)"
    - "Socket"
    - "RAM_Type (DDR4/DDR5)"
    - "Platform_Decision"
    - "CPU_Decision"

  constraints:
    - "cpu.socket ДОЛЖЕН быть совместим с platform"
    - "cpu.price ДОЛЖЕН быть в AR-02 target range для CPU"
    - "cpu.tdp_W УЧИТЫВАЕТ MOD-CTX-02 (hot climate) и MOD-CTX-03 (silent)"
    - "BI (CPU/GPU) ДОЛЖЕН быть < 15% для gaming intent"

  platform_tradeoff:
    AM5:
      pros: ["Upgrade path до 2027+", "Лучшая энергоэффективность", "DDR5"]
      cons: ["Дороже чем used LGA1700 на $30-50", "DDR5 обязателен"]
    LGA1851:
      pros: ["Intel Core Ultra 200", "QuickSync для video editing"]
      cons: ["Нет подтверждённого upgrade path", "Intel меняет сокет каждые 2 поколения"]
    LGA1700:
      pros: ["Дёшево (used)", "DDR4 совместимость"]
      cons: ["DEAD END — 14th Gen последнее поколение", "Нет апгрейда без замены MB"]
```

---

## STATE_3 · Memory Subsystem

```yaml
STATE_3:
  name: "Memory_Subsystem"
  depends_on: [STATE_2]

  description: >
    Выбрать RAM и Storage. Эти компоненты жёстко привязаны к платформе
    (RAM_Type из STATE_2) и workload (минимальные требования из L1 workload profiles).

  action:
    ram:
      step_1: "Определить минимальный объём RAM из workload profiles"
      step_2: "Определить тип: DDR5 или DDR4 (из STATE_2.RAM_Type)"
      step_3: "Выбрать конфигурацию: всегда 2 планки (dual channel — STRUCT-03 BLOCK)"
      step_4: "Проверить: EXPO/XMP профиль, частота поддерживается IMC CPU"
      step_5: "Оставить 2 слота свободными если budget позволяет (upgrade path)"
      step_6: "Заполнить RAM Decision"

    storage:
      step_1: "Определить минимальный объём из workload profiles"
      step_2: "Выбрать NVMe Gen4 (или Gen3 для budget builds) — не SATA для OS"
      step_3: "Проверить: достаточно ли PCIe линий на MB (определится в STATE_4)"
      step_4: "Заполнить Storage Decision"

  outputs:
    - "Selected_RAM (модель, объём, частота, latency)"
    - "Selected_Storage (модель, объём, интерфейс)"
    - "RAM_Decision"
    - "Storage_Decision"

  constraints:
    - "ram.type = STATE_2.RAM_Type (STRUCT-02 BLOCK)"
    - "ram.channels ≥ 2 (STRUCT-03 BLOCK)"
    - "ram.capacity ≥ workload.min_ram"
    - "ram.slots_used ≤ ram.total_slots − 2 (для upgrade path если horizon ≥ 3 года)"
    - "storage.capacity ≥ workload.min_storage"
    - "storage.interface = NVMe (для OS диска)"

  ram_speed_rule:
    note: >
      DDR5-5600 CL40 — стабильная база для AM5.
      DDR5-6000 CL30 — sweet spot (лучше на 5-8%).
      DDR5-6400+ — может требовать ручного тюнинга IMC.
      Для AI/Data intent: объём ВСЕГДА важнее скорости (capacity > speed).
      Для Esports intent: скорость ВСЕГДА важнее объёма (latency > capacity).
```

---

## STATE_4 · Physical Foundation

```yaml
STATE_4:
  name: "Physical_Foundation"
  depends_on: [STATE_1, STATE_2, STATE_3]

  description: >
    Выбрать Case и Motherboard. Это физический фундамент сборки.
    Порядок важен: сначала Case (физические ограничения), потом MB
    (должна помещаться в Case и поддерживать всё выбранное).

  action:
    case:
      step_1: "Определить form_factor из context (ATX, mATX, ITX)"
      step_2: "Выбрать Case удовлетворяющий:"
      step_3: "  - GPU length ≤ case.max_gpu_mm (STRUCT-04 BLOCK)"
      step_4: "  - Cooler height ≤ case.max_cooler_mm (STRUCT-05 BLOCK)"
      step_5: "  - Airflow: mesh front для hot climate (MOD-CTX-02)"
      step_6: "  - Acoustic: sound damping для silent constraint (MOD-CTX-03)"
      step_7: "Заполнить Case Decision"

    motherboard:
      step_1: "Фильтр: socket = STATE_2.Socket, ram_type = STATE_3.RAM_Type"
      step_2: "Фильтр: form_factor ≤ Case.form_factor (STRUCT-06 BLOCK)"
      step_3: "Проверить: достаточно M.2 слотов для всех NVMe дисков"
      step_4: "Проверить: PCIe Gen4 x16 для GPU (или Gen5 для future proof)"
      step_5: "Проверить: USB Flashback для обновления BIOS (upgrade path)"
      step_6: "Проверить: WiFi/Bluetooth если нужно (из context)"
      step_7: "Заполнить Motherboard Decision"

  outputs:
    - "Selected_Case"
    - "Selected_MB"
    - "Case_Decision"
    - "Motherboard_Decision"

  constraints:
    - "gpu.length_mm ≤ case.max_gpu_mm (STRUCT-04 BLOCK)"
    - "cooler.height_mm ≤ case.max_cooler_mm (STRUCT-05 BLOCK)"
    - "mb.form_factor IN case.supported_form_factors (STRUCT-06 BLOCK)"
    - "mb.m2_slots ≥ количество NVMe дисков"
    - "mb.pcie_x16_slots ≥ 1 (для дискретного GPU)"

  chipset_guidance:
    AM5:
      B650: "Достаточен для 95% сборок. PBO, EXPO, PCIe Gen4 x16 + Gen5 M.2."
      X670: "Избыточен для большинства. Больше линий PCIe, больше M.2, дороже."
      A620: "Бюджетный. Нет PBO, ограниченный VRM. Только для Ryzen 5."
    LGA1851:
      B860: "Аналог B650 для Intel. Достаточен для не-OC сборок."
      Z890: "Для OC и high-end. Избыточен для большинства задач."
```

---

## STATE_5 · Power and Thermals

```yaml
STATE_5:
  name: "Power_and_Thermals"
  depends_on: [STATE_4]

  description: >
    Рассчитать System TDP. Выбрать PSU и Cooler.
    Это механический расчёт, не творческая зона (RULE 7).

  action:
    psu:
      step_1: "System_TDP = cpu.tdp_W + gpu.tdp_W + platform_overhead (55W)"
      step_2: "PSU_min_W = System_TDP × 1.2 (VAL-POWER-01 BLOCK)"
      step_3: "PSU_recommended_W = System_TDP × 1.5 (VAL-POWER-02 WARN)"
      step_4: "Выбрать PSU: 80+ Gold минимум, доверенный бренд (Seasonic, Corsair, be quiet!)"
      step_5: "Проверить: semi-passive для silent constraint (MOD-CTX-03)"
      step_6: "Заполнить PSU Decision"

    cooler:
      step_1: "cpu_tdp = STATE_2.Selected_CPU.tdp_W"
      step_2: "Рассчитать требуемую эффективность: efficiency ≥ cpu_tdp / (tjmax − ambient − margin)"
      step_3: "Выбрать тип: Air (до 120W CPU) | AIO 240 (120-180W) | AIO 360 (>180W)"
      step_4: "Проверить: cooler.height ≤ case.max_cooler_mm (STRUCT-05 BLOCK)"
      step_5: "Применить MOD-CTX-02: если ambient > 30°C → upgrade cooler на 1 tier"
      step_6: "Применить MOD-CTX-03: если silent → PREFER Noctua/be quiet!, fan-stop в idle"
      step_7: "Заполнить Cooling Decision"

  outputs:
    - "Selected_PSU"
    - "Selected_Cooler"
    - "System_TDP_estimated"
    - "PSU_Decision"
    - "Cooling_Decision"

  constraints:
    - "psu.wattage ≥ System_TDP × 1.1 (VAL-POWER-01 BLOCK)"
    - "psu.form_factor IN case.psu_support (STRUCT-07 BLOCK)"
    - "cooler.height_mm ≤ case.max_cooler_mm (STRUCT-05 BLOCK)"
    - "cpu_expected_temp_C < cpu.tjunction_max − 5 (VAL-TH-01 BLOCK)"

  rule_7_psu_non_creative:
    note: >
      PSU — не творческая зона. Не пытаться «оптимизировать» бюджет здесь.
      Сэкономленные $20 на PSU = риск нестабильности всей системы.
      Минимальный стандарт: 80+ Gold, доверенный бренд, semi-passive для silent.
```

---

## STATE_6 · Behavioral Simulation (L3)

```yaml
STATE_6:
  name: "Behavioral_Simulation"
  depends_on: [STATE_5]

  description: >
    Прогнать полную конфигурацию через L3 поведенческие модели.
    Это центральный шаг v3 пайплайна — предсказание поведения
    физической системы до её сборки.

  action:
    for_each_model:
      acoustic:
        file: "pcbo:ontology/L3_behavior/acoustic"
        inputs: [cpu.tdp_W, gpu.tdp_W, cooler.type, case.type, fan.config]
        outputs: [AcousticPrediction: idle_class (A0-A4), load_class (A0-A4)]

      thermal:
        file: "pcbo:ontology/L3_behavior/thermal"
        inputs: [cpu.tdp_W, gpu.tdp_W, cooler.efficiency, ambient_temp_C, case.airflow]
        outputs: [ThermalPrediction: cpu_temp_C, gpu_temp_C, hotspot_temp_C, throttling_probability]

      compute:
        file: "pcbo:ontology/L3_behavior/compute"
        inputs: [gpu.model, cpu.model, ram.capacity, workload_profiles]
        outputs: [ComputePrediction: fps_avg, fps_1pct, llm_tokens_per_sec, benchmark_scores]

      power:
        file: "pcbo:ontology/L3_behavior/power"
        inputs: [cpu.tdp_W, gpu.tdp_W, platform_overhead_W, psu.efficiency]
        outputs: [PowerPrediction: idle_W, gaming_W, full_load_W, annual_cost_USD]

      latency:
        file: "pcbo:ontology/L3_behavior/latency"
        inputs: [ram.latency_ns, storage.latency_us, gpu.render_latency_ms]
        outputs: [LatencyPrediction: input_latency_ms, render_latency_ms]
        condition: "Только для esports, music_production, VR intents"

      reliability:
        file: "pcbo:ontology/L3_behavior/reliability"
        inputs: [all_components, fan.models, ram.configuration]
        outputs: [ReliabilityPrediction: risks[], overall_classification]

    aggregate:
      action: "Собрать все predictions в единый SimulationOutput блок"
      format: "YAML (Expected System Behavior)"

  outputs:
    - "Simulation_Results (YAML)"
    - "AcousticPrediction"
    - "ThermalPrediction"
    - "ComputePrediction"
    - "PowerPrediction"
    - "LatencyPrediction (опционально)"
    - "ReliabilityPrediction"

  note: >
    На этом шаге не принимаются решения — только симуляция.
    Решения о PASS/FAIL принимаются в STATE_7.
```

---

## STATE_7 · Validation Gate (L5)

```yaml
STATE_7:
  name: "Validation_Gate"
  depends_on: [STATE_6]

  description: >
    Формальный quality gate. Ни одна сборка не покидает систему
    без прохождения L5 Validation.

  action:
    step_1: "Structural checks (VAL-STRUCT-01..07)"
    step_2: "Power checks (VAL-POWER-01..04)"
    step_3: "Thermal checks (VAL-TH-01..04)"
    step_4: "Acoustic checks (VAL-AC-01..04)"
    step_5: "Compute checks (VAL-CP-01..04)"
    step_6: "Reliability checks (VAL-RL-01..03)"
    step_7: "Budget check (VAL-BUD-01..03)"
    step_8: "Lifecycle check (VAL-LC-01..02)"

    on_first_BLOCK_failure:
      action: "STOP. Прекратить валидацию."
      reason: "Последующие проверки невалидны при несовместимых компонентах."

    on_WARN_only:
      action: "Собрать все warnings. Продолжить валидацию до конца."

  outputs:
    - "Validation_Status: PASS | PASS_WITH_WARNINGS | FAIL"
    - "Active_Warnings (список)"
    - "Rollback_Constraints (если FAIL)"

  transitions:
    if_PASS:
      target: "STATE_8"
      action: "Сборка переходит к генерации Build Artifact"

    if_PASS_WITH_WARNINGS:
      target: "STATE_8"
      action: "Сборка переходит к генерации. Warnings включаются в Active Risks."

    if_FAIL:
      target: "STATE_1"
      action: >
        Rollback на STATE_1 с новыми constraints из RollbackProtocol (validation.md).
        Инкрементировать rollback_counter.
        Если rollback_counter > MAX_ROLLBACKS (3) → сообщить о невыполнимости.

  rollback_protocol:
    MAX_ROLLBACKS: 3
    on_each_rollback:
      - "Добавить failed constraint в Active_Constraints"
      - "Перезапустить синтез с STATE_1 (Primary Component может измениться)"
      - "Логировать причину rollback в Build Artifact"
    on_max_exceeded:
      action: "Сообщить пользователю о невыполнимости требований"
      output: >
        Документ с объяснением конфликта ограничений:
        (1) какие constraints противоречат друг другу,
        (2) почему система не может их удовлетворить,
        (3) 2-3 конкретных предложения по изменению требований для достижимости.
```

---

## STATE_8 · Artifact Generation

```yaml
STATE_8:
  name: "Artifact_Generation"
  depends_on: [STATE_7]
  condition: "STATE_7 вернул PASS или PASS_WITH_WARNINGS"

  description: >
    Финальный шаг. Заполнить template.md и выдать пользователю
    Build Artifact с полной трассировкой решений.

  action:
    step_1: "Заполнить Frontmatter (все поля из template.md)"
    step_2: "Заполнить BuildGoal таблицу"
    step_3: "Заполнить Компонентную таблицу"
    step_4: "Сформировать Decision Chain (все Decision из STATE_1..5)"
    step_5: "Вставить Expected System Behavior (из STATE_6 Simulation)"
    step_6: "Вставить Валидацию (из STATE_7)"
    step_7: "Вставить Lifecycle план (из STATE_0 context + STATE_2 platform)"
    step_8: "Указать Active Risks (из STATE_7 warnings + Decision risks)"
    step_9: "Вычислить метрики сборки (BAQ, BI, System TDP, Upgrade flexibility)"

  outputs:
    - "Build_Artifact (markdown файл в builds/)"
    - "Все Decision артефакты (inline в Build Artifact)"
    - "Simulation Output (YAML блок)"
    - "Validation Report"

  quality_checks:
    - "Все Decision имеют ≥ 2 candidates?"
    - "Все Rejection имеют MV calculation (AR-03)?"
    - "Все Decision имеют минимум 1 Risk?"
    - "Все Decision имеют TradeOff?"
    - "Цены помечены как ориентировочные (RULE 6)?"
    - "Lifecycle план содержит tuning plan + upgrade milestones?"

  note: >
    Build Artifact — это не «список деталей с ценами».
    Это инженерный артефакт, воспроизводящий полный путь
    от Intent до валидированной конфигурации.
```

---

## Топологические зависимости (почему порядок именно такой)

```yaml
Topological_Constraints:

  "STATE_1 перед STATE_2":
    reason: "Primary Component определяет бюджетный остаток для CPU и платформы."

  "STATE_2 перед STATE_3":
    reason: "RAM_Type (DDR4/DDR5) и сокет MB определяются платформой."

  "STATE_3 перед STATE_4":
    reason: "MB должна поддерживать выбранный RAM_Type и иметь достаточно M.2 слотов."

  "STATE_4 перед STATE_5":
    reason: "Case определяет ограничения по высоте кулера и форм-фактору PSU."

  "STATE_5 перед STATE_6":
    reason: "L3 Simulation требует System TDP, кулер и PSU."

  "STATE_6 перед STATE_7":
    reason: "Validation сравнивает Simulation результаты с Intent targets."

  "STATE_7 перед STATE_8":
    reason: "Только валидированные сборки становятся Build Artifacts."

  why_not_parallel:
    note: >
      STATE_1..5 образуют строгую топологическую цепочку.
      Единственное исключение: RAM и Storage внутри STATE_3
      могут выбираться параллельно (независимы друг от друга).
```

---

## Обработка ошибок и краевые случаи

```yaml
Error_Handling:

  insufficient_budget:
    condition: "Budget ceiling меньше минимальной цены всех BLOCK-совместимых components"
    action: >
      Сообщить пользователю: минимальная стоимость сборки для intent=X
      составляет $Y. Предложить: (1) увеличить бюджет, (2) снизить intent
      (например, AAA 4K → AAA 1440p), (3) купить used GPU.

  conflicting_constraints:
    condition: "Два активных constraints не могут быть удовлетворены одновременно"
    example: "Silent + ITX + RTX 4090 = невозможно (350W TGP в ITX не охладить бесшумно)"
    action: >
      Объяснить конфликт. Предложить: (1) ослабить acoustic constraint,
      (2) перейти на ATX корпус, (3) снизить GPU tier.

  component_unavailable:
    condition: "Выбранный компонент не доступен в market_region пользователя"
    action: >
      Отметить в Decision: confidence=LOW. Предложить 1-2 альтернативы,
      доступные в регионе. Проверить доступность через локальные marketplace.

  unknown_component:
    condition: "Компонент не описан в components/ KB (Gap 1)"
    action: >
      Запросить характеристики у пользователя ИЛИ использовать training data
      LLM с явной пометкой provenance: source=LLM_ESTIMATE.
      В любом случае: confidence=LOW.
```

---

## Связь с llm-guide.md

```yaml
Mapping:
  "llm-guide.md STEP 1 (Reconstruct BuildGoal)": "STATE_0"
  "llm-guide.md STEP 2 (Activate Context Modifiers)": "STATE_0"
  "llm-guide.md STEP 3 (Identify Active System Behaviors)": "STATE_0 (предзагрузка L3 моделей)"
  "llm-guide.md STEP 4 (Execute Decision Chain)": "STATE_1 → STATE_2 → STATE_3 → STATE_4 → STATE_5"
  "llm-guide.md STEP 5 (Run L3 Behavior Simulation)": "STATE_6"
  "llm-guide.md STEP 6 (Validate L3 Simulation Against Intent)": "STATE_7 (часть checks)"
  "llm-guide.md STEP 7 (Run Formal Validation L5)": "STATE_7"
  "llm-guide.md STEP 8 (Build Lifecycle Plan)": "STATE_8 (внутри Artifact Generation)"

  note: >
    llm-guide.md — это human-readable narrative протокола.
    synthesis.md — это формальный state machine того же процесса.
    Первый объясняет ЧТО делать, второй — КАК машина это исполняет.
    При расхождении — synthesis.md authoritative.
```
