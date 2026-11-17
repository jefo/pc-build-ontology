---
uri: "pcbo:reasoning/allocation"
type: "RuleSet"
version: "3.0.0-draft"
layer: "Reasoning"
provenance:
  source: "ENGINEERING_DERIVATION"
  date: "2026-06-03"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    AR-02 target allocation ranges — инженерная оценка на основе
    типичных рыночных пропорций. Требуют валидации на 10+ сборках.
    AR-03 MV thresholds (1.0 / 0.5) — стандартные пороги marginal analysis,
    заимствованы из экономики решений (Keeney & Raiffa).
    severity: info
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"
    - "pcbo:ontology/L1_intent/context"
  feedsInto:
    - "pcbo:ontology/L4_decision/decision"
    - "pcbo:reasoning/synthesis"
tags: ["reasoning", "allocation", "budget", "marginal-value", "rules", "AR"]
---

# Reasoning · Allocation — Закон Распределения

> Бюджет — это физика экономики.  
> Мы уходим от фразы «постарайся уложиться» к строгим математическим правилам AR (Allocation Rules).

---

## AR-01 · Budget Envelope (Hard Ceiling)

```yaml
AR-01_Hard_Ceiling:
  rule: "actual_cost_USD ≤ budget_ceiling_USD"
  enforcement: STRICT_BLOCK
  description: >
    Жёсткий потолок бюджета. Ни при каких обстоятельствах сборка
    не должна превышать budget_ceiling_USD. Это не рекомендация —
    это физический предел (у пользователя нет денег сверх этой суммы).
  validation: "VAL-BUD-01 (L5)"
  on_violation: "Rollback на L4 с constraint: reduce tier одного или нескольких компонентов"
  note: >
    Отличать ceiling от target. Ceiling — жёсткая граница.
    Target — желаемая точка. Сборка может быть между target и ceiling,
    но никогда выше ceiling.
```

---

## AR-02 · Target Allocation Matrix

Идеальное распределение бюджета (Target %) в зависимости от Intent.  
Проценты — от **бюджетного потолка** (ceiling), не от target.

```yaml
AR-02_Target_Allocation:

  aaa_gaming:
    dominant: GPU
    matrix:
      GPU:     { range: "40-50%", note: "Главный драйвер FPS. Экономия здесь = потеря FPS." }
      CPU:     { range: "15-20%", note: "Не создавать BI > 15% с выбранным GPU." }
      MB:      { range: "8-12%",  note: "Чипсет без переплаты. B650 > X670 для gaming." }
      RAM:     { range: "5-10%",  note: "2×16GB DDR5 — стандарт. 32GB если background multitask." }
      Storage: { range: "8-12%",  note: "NVMe Gen4 1-2TB. Не HDD для gaming." }
      PSU:     { range: "5-8%",   note: "System TDP × 1.5. 80+ Gold минимум." }
      Cooling: { range: "3-5%",   note: "Air cooler для mid-range CPU. AIO для high-end." }
      Case:    { range: "3-5%",   note: "Mesh front, 2-3 вентилятора в комплекте." }

  esports:
    dominant: CPU
    matrix:
      CPU:     { range: "30-35%", note: "CPU-bound игры. X3D предпочтителен." }
      GPU:     { range: "20-25%", note: "Mid-tier достаточно для 1080p low/medium." }
      RAM:     { range: "10-15%", note: "Высокая частота + низкий CL важнее объёма." }
      MB:      { range: "10-15%", note: "Стабильный VRM, BIOS flashback." }
      Storage: { range: "8-12%",  note: "NVMe Gen4. Скорость загрузки карт." }
      PSU:     { range: "5-8%",   note: "System TDP × 1.5." }
      Cooling: { range: "5-10%",  note: "CPU охлаждение важно для sustained boost." }
      Case:    { range: "3-5%",   note: "Airflow приоритетнее шумоизоляции." }

  ai_inference:
    dominant: GPU
    matrix:
      GPU:     { range: "45-55%", note: "VRAM — король. Бюджет GPU доминирует." }
      RAM:     { range: "15-20%", note: "Объём > скорость. 64GB минимум для 70B offload." }
      CPU:     { range: "8-12%",  note: "Не bottleneck для prompt processing." }
      MB:      { range: "8-12%",  note: "PCIe Gen4 x16. B650 достаточно." }
      Storage: { range: "5-8%",   note: "2TB+ для моделей. Gen4." }
      PSU:     { range: "8-10%",  note: "Sustained GPU load. Качественный PSU обязателен." }
      Cooling: { range: "3-5%",   note: "GPU охлаждение важнее CPU." }
      Case:    { range: "3-5%",   note: "Airflow для sustained GPU load." }

  video_editing:
    dominant: CPU
    matrix:
      CPU:     { range: "30-40%", note: "Многопоточный рендер. Больше ядер = быстрее экспорт." }
      RAM:     { range: "15-20%", note: "32-64GB. Объём критичен для 4K проектов." }
      Storage: { range: "12-18%", note: "NVMe Gen4 2TB+. Быстрый scratch диск." }
      GPU:     { range: "12-18%", note: "NVENC для экспорта. VRAM для GPU-эффектов." }
      MB:      { range: "8-12%",  note: "Множество M.2 слотов. USB-C для камер." }
      PSU:     { range: "5-8%",   note: "Sustained CPU+GPU load." }
      Cooling: { range: "5-10%",  note: "Sustained CPU load — AIO предпочтительнее." }
      Case:    { range: "3-5%",   note: "Тишина в студии. Шумоизоляция." }

  silent_build:
    dominant: Cooling
    matrix:
      Cooling: { range: "10-15%", note: "Премиум-кулеры. Большие вентиляторы на малых оборотах." }
      Case:    { range: "8-12%",  note: "Шумоизоляция (демпфирующие панели)." }
      PSU:     { range: "8-12%",  note: "Semi-passive или fanless. 80+ Platinum." }
      CPU:     { range: "15-25%", note: "Низкий TDP приоритетнее производительности." }
      GPU:     { range: "25-35%", note: "Максимальная производительность при минимальном TDP." }
      RAM:     { range: "5-10%",  note: "Без RGB (доп. нагрев)." }
      Storage: { range: "8-12%",  note: "NVMe без активного охлаждения." }
      MB:      { range: "8-12%",  note: "Пассивное охлаждение VRM/чипсета." }

  data_engineering:
    dominant: CPU
    matrix:
      CPU:     { range: "25-35%", note: "Многопоточность. 8+ ядер." }
      RAM:     { range: "20-25%", note: "64GB минимум. Объём > скорость." }
      Storage: { range: "15-20%", note: "NVMe Gen4 2TB+. Dataset storage." }
      GPU:     { range: "5-10%",  note: "Часто не нужен. iGPU достаточно для display." }
      MB:      { range: "8-12%",  note: "Множество M.2 + SATA для данных." }
      PSU:     { range: "5-8%",   note: "Стабильность, не мощность." }
      Cooling: { range: "5-10%",  note: "Sustained CPU load." }
      Case:    { range: "3-5%",   note: "Функциональность > эстетика." }

  general_rule:
    note: >
      Если компонент выходит за пределы target range, это должно быть
      явно обосновано в Decision Rationale с указанием:
      (1) какой компонент «потерял» бюджет, (2) почему это допустимо,
      (3) как изменился общий utility score сборки.
```

---

## AR-03 · Marginal Value Threshold

**Главное правило вывода.** Стоит ли переплачивать за компонент?

```yaml
AR-03_Marginal_Value:

  description: >
    MV измеряет эффективность дополнительных затрат.
    Это Proof-of-Work для каждого Rejection в Decision.

  formula:
    mv: "(ΔPerformance% / ΔPrice%)"
    delta_performance_pct: "((Candidate_Score − Baseline_Score) / Baseline_Score) × 100"
    delta_price_pct: "((Candidate_Price − Baseline_Price) / Baseline_Price) × 100"

  definitions:
    Baseline: "Самый дешёвый кандидат, удовлетворяющий всем BLOCK constraints"
    Candidate: "Более дорогой рассматриваемый вариант"
    Candidate_Score: "Utility score U(candidate) из MAUT (utility_functions.md)"
    Baseline_Score: "Utility score U(baseline) из MAUT"

  thresholds:
    MV_Excellent:
      value: "≥ 1.0"
      verdict: "APPROVE"
      meaning: "Рост производительности обгоняет рост цены."
      action: "Выбор одобрен без дополнительного обоснования."

    MV_Acceptable:
      value: "≥ 0.5"
      verdict: "ACCEPT_WITH_RATIONALE"
      meaning: "Закон убывающей отдачи действует, но апгрейд всё ещё осмыслен."
      action: "Допустимо, если нет других узких мест в сборке. Требует явного tradeoff analysis."

    MV_Reject:
      value: "< 0.5"
      verdict: "REJECT"
      meaning: "Неоправданная переплата. Цена растёт быстрее полезности."
      action: "Отклонить кандидата. Направить бюджет через AR-04."

  exception_clause:
    condition: "Более дешёвый кандидат (baseline) нарушает BLOCK constraint"
    example: "RTX 4070 12GB имеет MV=0.4 vs RTX 4060 Ti 16GB при intent:ai_inference, НО 12GB < VRAM threshold (16GB). 4060 Ti 16GB выбирается несмотря на низкий MV, потому что baseline не проходит VAL-CP-03."
    rule: "MV игнорируется, если baseline нарушает любой BLOCK check из L5."

  worked_example:
    scenario: "AAA Gaming 1440p. GPU Decision."
    baseline:
      component: "RTX 4060 Ti 8GB"
      price: 400
      utility_score: 0.65
    candidate:
      component: "RTX 4070 12GB"
      price: 550
      utility_score: 0.82

    calculation:
      delta_price_pct: "((550 − 400) / 400) × 100 = 37.5%"
      delta_performance_pct: "((0.82 − 0.65) / 0.65) × 100 = 26.2%"
      mv: "26.2 / 37.5 = 0.70"
      verdict: "ACCEPT_WITH_RATIONALE (MV ≥ 0.5)"

    decision: >
      RTX 4070 принят. MV=0.70 — апгрейд обоснован.
      +$150 даёт +26% utility. Tradeoff: $150 могли пойти в RAM (32→64GB),
      но для gaming 32GB достаточно. Бюджет в рамках AR-02 target range (GPU 40-50%).
```

---

## AR-04 · Budget Reallocation Priority Queue

Куда направить сэкономленные деньги?  
Приоритетная очередь для каждого Intent.

```yaml
AR-04_Reallocation_Queue:

  description: >
    Когда AR-03 отклоняет дорогой компонент, высвобожденный бюджет
    не остаётся «в кармане» — он перераспределяется по приоритетной очереди.
    Очередь упорядочена по marginal utility на доллар.

  aaa_gaming:
    - target: "GPU tier upgrade"
      rationale: "Главный драйвер FPS. Следующий тир GPU даёт наибольший прирост."
      condition: "Если следующий тир GPU проходит AR-03 (MV ≥ 0.5)"

    - target: "RAM: 16GB → 32GB"
      rationale: "Background multitask (браузер + Discord + игра). 32GB = комфорт."
      condition: "Если RAM < 32GB И есть budget ≥ $50"

    - target: "Storage: 1TB → 2TB"
      rationale: "Современные AAA игры — 100-200GB каждая."
      condition: "Если storage < 2TB И есть budget ≥ $40"

    - target: "CPU tier upgrade"
      rationale: "Следующий тир CPU если BI > 10% с выбранным GPU."
      condition: "Если BI > 10% И есть budget ≥ $80"

  ai_inference:
    - target: "GPU VRAM upgrade"
      rationale: "VRAM — главный ограничитель. 12GB → 16GB → 24GB."
      condition: "Если больший VRAM доступен в бюджете И проходит AR-03"

    - target: "System RAM: 32GB → 64GB"
      rationale: "LLM offload. 70B Q4 требует 40+ GB RAM."
      condition: "Если RAM < 64GB И intent предполагает 70B модели"

    - target: "PSU headroom для будущего GPU"
      rationale: "GPU апгрейд может потребовать больше мощности."
      condition: "Если планируется GPU апгрейд в year 1-2"

    - target: "Storage: 1TB → 2TB+"
      rationale: "Модели весят 40-80GB. 4-5 моделей = 300-400GB."
      condition: "Если storage < 2TB"

  video_editing:
    - target: "RAM: 32GB → 64GB"
      rationale: "4K проекты требуют 64GB. Своп на диск = обвал производительности."
      condition: "Если RAM < 64GB И разрешение 4K"

    - target: "Storage: добавить scratch диск"
      rationale: "Отдельный NVMe для кэша/превью."
      condition: "Если storage = 1 диск И есть budget ≥ $60"

    - target: "CPU: больше ядер"
      rationale: "Рендер — многопоточный. +2 ядра = -15-20% времени экспорта."
      condition: "Если CPU < 8 ядер И есть budget ≥ $100"

  silent_build:
    - target: "Cooling: premium tier"
      rationale: "Большие вентиляторы на малых RPM = та же производительность при меньшем шуме."
      condition: "Всегда первый приоритет для silent intent"

    - target: "PSU: semi-passive → fanless"
      rationale: "Устранение единственного мотора в idle."
      condition: "Если system TDP < 300W"

    - target: "Case: improved sound damping"
      rationale: "Демпфирующие панели, резиновые крепления вентиляторов."
      condition: "Если есть budget ≥ $30"

  anti_pattern:
    description: "Запрещённые перераспределения"
    rules:
      - "НЕ перераспределять бюджет с PSU ниже 80+ Gold ради других компонентов"
      - "НЕ перераспределять бюджет с кулера если CPU > 95W TDP"
      - "НЕ перераспределять бюджет на эстетику (RGB, кастомные кабели) за счёт производительности"
      - "НЕ перераспределять бюджет на «будущий апгрейд» если это нарушает текущие BLOCK constraints"
```

---

## AR-05 · Budget Allocation Quality (BAQ)

Метрика качества распределения бюджета.

```yaml
AR-05_BAQ:
  formula: "BAQ = 1 − (Σ|actual_i − target_i| / 2)"
  definitions:
    actual_i: "Фактическая доля бюджета компонента i"
    target_i: "Среднее значение target range для компонента i из AR-02"
  range: "0.0 .. 1.0"
  thresholds:
    BAQ ≥ 0.85: "EXCELLENT — бюджет распределён близко к идеальным пропорциям"
    BAQ ≥ 0.70: "ACCEPTABLE — есть отклонения, но в пределах разумного"
    BAQ < 0.70: "WARN — требуется явное обоснование отклонений в Decision Rationale"
  note: >
    BAQ не BLOCK constraint. Это диагностическая метрика.
    Сборка с BAQ=0.65 может быть валидна, если отклонения обоснованы
    (например, пользователь уже имеет Case и Storage).
```

---

## Связь с другими слоями

```yaml
Traceability:
  AR-01 → L5: "VAL-BUD-01 (BLOCK)"
  AR-02 → L4: "Decision Chain (STATE_1 budget allocation)"
  AR-03 → L4: "Decision Rationale (MV calculation for each rejection)"
  AR-04 → L4: "Decision после каждого rejection"
  AR-05 → Build: "Метрика BAQ в Build Artifact"

  uses:
    - "pcbo:ontology/L1_intent/intent (определяет dominant component)"
    - "pcbo:ontology/L3_behavior/utility_functions (MAUT scores для AR-03)"
    - "pcbo:ontology/L4_decision/decision (Rationale + TradeOff структура)"
    - "pcbo:ontology/L5_validation/validation (VAL-BUD checks)"
```
