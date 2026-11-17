---
uri: "pcbo:meta/llm-guide"
type: "MetaDocument"
version: "3.0.0-draft"
provenance:
  date: "2026-06-03"
  note: "v3 — добавлен reasoning слой (synthesis + allocation), L3 Simulation в критическом пути"
relations:
  references:
    - "pcbo:ontology/L1_intent"
    - "pcbo:ontology/L2_constraint"
    - "pcbo:ontology/L3_behavior/acoustic"
    - "pcbo:ontology/L3_behavior/thermal"
    - "pcbo:ontology/L3_behavior/compute"
    - "pcbo:ontology/L3_behavior/power"
    - "pcbo:ontology/L3_behavior/latency"
    - "pcbo:ontology/L3_behavior/reliability"
    - "pcbo:ontology/L3_behavior/utility_functions"
    - "pcbo:ontology/L4_decision"
    - "pcbo:ontology/L5_validation"
    - "pcbo:ontology/L6_lifecycle"
    - "pcbo:reasoning/synthesis"
    - "pcbo:reasoning/allocation"
  isEntryPointFor: "LLM_Agent"
tags: ["meta", "llm", "reasoning", "decision-first", "synthesis", "v3"]
---

# Руководство для LLM-агента (v3) — Decision-First + L3 Simulation

---

## Фундаментальный сдвиг v3

В v1 reasoning шёл: *компоненты → сборка*.  
В v2 reasoning шёл: *Intent + Context → BuildGoal → Decisions → Build Artifact*.

**В v3 добавлен центральный слой симуляции:**
*Decisions → L3 Behavior Simulation → Validation → Build Artifact*.

Сборка — это не набор деталей и даже не набор обоснованных решений.  
**Сборка — это предсказание поведения физической системы в заданных условиях.**
Решения лишь средство достижения целевого поведения.

---

## Протокол reasoning (8 шагов)

### STEP 1 — Reconstruct BuildGoal

Прежде чем выбирать что-либо, построй полный BuildGoal:

```
BuildGoal {
  intent:    ← из pcbo:ontology/L1_intent/intent
  context:   ← из pcbo:ontology/L1_intent/context
  workload:  ← из pcbo:ontology/L1_intent/workload
}
```

Если данных недостаточно — **спрашивай**. Не угадывай.

Минимально необходимо:
- Основная задача (gaming / content / office / mixed)
- Бюджет (жёсткий потолок)
- Разрешение монитора (для gaming)
- Есть ли специальные ограничения (шум, размер, ОС)

### STEP 2 — Activate Context Modifiers

Загрузи `pcbo:ontology/L1_intent/context` и примени MOD-CTX-01..06.  
Каждый активированный модификатор меняет веса в последующих Decision.

```
ЕСЛИ context.noise_constraint = strict
→ MOD-CTX-03 активирован: TDP ограничение, fan preferences

ЕСЛИ context.electricity_cost_kwh > 0.20
→ MOD-CTX-01 активирован: power_efficiency weight += 0.15
```

### STEP 3 — Identify Active System Behaviors

Из онтологии L3_behavior определи, какие модели поведения  
наиболее вероятны и релевантны для данного Intent+Context:

```
intent:aaa_gaming_1440p →
  primary:   [compute (gaming), thermal]
  secondary: [acoustic, power]
  irrelevant: [latency, llm_inference]

intent:esports_240hz →
  primary:   [compute (esports), latency (input+render)]
  secondary: [thermal]
  critical:  [frametime_variance]

intent:ai_inference_local →
  primary:   [compute (llm), vram_capacity]
  secondary: [power, thermal (sustained GPU)]
  irrelevant: [gaming_fps, audio_latency]

intent:video_editing →
  primary:   [compute (encode), ram_capacity, storage_latency]
  secondary: [thermal (sustained CPU)]
  irrelevant: [gaming_fps]

intent:silent_build →
  primary:   [acoustic (idle + load)]
  secondary: [thermal, power (lower TDP = lower noise)]
  irrelevant: [compute ceiling]
```

**Источники поведения (загрузить из онтологии):**
- `pcbo:ontology/L3_behavior/compute` — вычислительные пороги
- `pcbo:ontology/L3_behavior/acoustic` — акустические классы A0-A4
- `pcbo:ontology/L3_behavior/thermal` — тепловые состояния
- `pcbo:ontology/L3_behavior/power` — энергопотребление
- `pcbo:ontology/L3_behavior/latency` — задержки
- `pcbo:ontology/L3_behavior/reliability` — риски надёжности
- `pcbo:ontology/L3_behavior/utility_functions` — MAUT веса для scoring

Это определяет, какие риски будут контролироваться в каждом Decision.

### STEP 4 — Execute Decision Chain

Выполни Decision Chain в правильном порядке:

(надо сделать разные стратегии под разные задачи не геймингом едины)
```
1. Platform Decision
2. GPU Decision    ← PRIMARY для gaming / AI
3. CPU Decision    ← учитывает выбранный GPU
4. RAM Decision    ← учитывает платформу
5. Storage Decision
6. PSU Decision    ← механически из TDP
7. Cooling Decision ← из CPU TDP + context
8. Motherboard Decision ← удовлетворяет всем предыдущим
```

Для каждого Decision:
- Рассмотри досточно кандидатов (3-5 конкурирующих между собой в классе решений норма)
- Явно отклони не-выбранных с количественным обоснованием
- **Используй MAUT веса из `utility_functions.md`** для scoring candidates
- Заполни Rationale (argument types)
- Идентифицируй TradeOffs
- Идентифицируй Risks + их Mitigation

### STEP 5 — Run L3 Behavior Simulation

**Это новый центральный шаг пайплайна.** После выбора компонентов,  
прогони сборку через все релевантные L3 модели:

```
L4 Decisions (выбранные компоненты)
        ↓
┌───────────────────────────────────────────┐
│ L3 Simulation                               │
│                                             │
│  acoustic.md  → AcousticPrediction          │
│  thermal.md   → ThermalPrediction           │
│  compute.md   → ComputePrediction           │
│  power.md     → PowerPrediction             │
│  latency.md   → LatencyPrediction (если релевантно) │
│  reliability.md → ReliabilityPrediction     │
└───────────────────────────────────────────┘
        ↓
   Simulation Output (YAML)
        ↓
   STEP 6 (Validation)
```

Для каждой модели:
1. Загрузи соответствующую онтологию из `L3_behavior/`
2. Подставь параметры выбранных компонентов + workload profile
3. Выполни расчёт по формулам модели
4. Запиши предсказание

**Результат симуляции** — это блок `Expected System Behavior` для Build Artifact:

```yaml
## Expected System Behavior (L3 Simulation)
- Ambient: 28°C
- Compute (1440p AAA): PASS — 85-110 FPS avg, 55-70 FPS 1% low (smooth)
- Compute (LLM 70B): PASS (RAM Offload) — 1.5-3.0 t/s (Reading Speed)
- Acoustic Idle: A1_Ambient
- Acoustic Load: A2_LowHum
- Thermal CPU: 75°C (T_Warm)
- Thermal GPU: 72°C (T_Warm)
- Power Gaming: 339W
- Known Risks: Coil whine MEDIUM (T2 GPU + high FPS)
```

### STEP 6 — Validate L3 Simulation Against Intent

Сравни результаты симуляции с целевыми значениями из Intent + Context:

```
Acoustic simulation vs noise_constraint:
  A2_LowHum ≤ A2_LowHum (strict) → OK

Thermal simulation vs safety margins:
  CPU 75°C < tjmax - 10°C → OK
  GPU 72°C < 83°C → OK

Compute simulation vs intent targets:
  FPS 1% low 55-70 > 45 minimum → OK
  LLM 1.5-3.0 t/s < 15 target → WARN
```

### STEP 7 — Run Formal Validation (L5)

Выполни протокол из `pcbo:ontology/L5_validation`:

```
BLOCK_CHECKS:  структурная совместимость, PSU headroom, thermal safety, budget
WARN_CHECKS:   VRAM headroom, acoustic margin, reliability risks
```

**Любой BLOCK failure → Rollback на L4 с новыми constraints.**
**Только WARN → PASS_WITH_WARNINGS.**
**Всё чисто → PASS.**

### STEP 8 — Build Lifecycle Plan

Из `pcbo:ontology/L6_lifecycle`:
- Tuning plan (XMP, fan curves)
- 2-3 milestone апгрейда с trigger conditions
- Слабейшее звено (следующий апгрейд)

---

## Правила честного reasoning

```
RULE 1 — ТРАССИРОВКА ОБЯЗАТЕЛЬНА
  Каждое нетривиальное утверждение ссылается на правило или метрику.
  ❌ "Я рекомендую RTX 4070"
  ✅ "RTX 4070 выбран: MV vs RTX 4070 Ti = 0.09 FPS/$ < порога AR-03.
      $200 эффективнее работают в CPU (syn:x3d_games активирован)."

RULE 2 — REJECTION ОБЯЗАТЕЛЕН
  Нельзя выбрать компонент без явного отклонения альтернатив.
  Minimum: один более дешёвый + один более дорогой кандидат.

RULE 3 — RISK НЕЛЬЗЯ СКРЫВАТЬ
  У каждого Decision есть минимум один Risk.
  Severity=low — OK. Отсутствие — нечестно.

RULE 4 — CONTEXT-BOUND RATIONALE
  Rationale валиден только для конкретного Intent+Context.
  "Лучшая карта вообще" → не является Rationale.

RULE 5 — НЕОПРЕДЕЛЁННОСТЬ ПРИЗНАЁТСЯ
  Если данных недостаточно для уверенного Decision → confidence=low + объяснение.
  Лучше задать вопрос, чем заполнить Decision фикцией.

RULE 6 — ЦЕНЫ ОРИЕНТИРОВОЧНЫ
  Цены в базе знаний = MSRP или исторические данные.
  Всегда добавляй: "Проверь актуальную цену перед покупкой."

RULE 7 — PSU НЕ ТВОРЧЕСКАЯ ЗОНА
  PSU выбирается механически: system_tdp × 1.2, 80+ Gold, доверенный бренд.
  Не пытайся "оптимизировать" — это зона надёжности, не эффективности.
```

---

## Минимальный контекст для ответа

Если нельзя загрузить всё:

```
PRIORITY_1: L1_intent/intent.md                 (Intent — зачем)
PRIORITY_2: L1_intent/context.md                (Context — условия)
PRIORITY_3: L1_intent/workload.md               (Workload — нагрузка)
PRIORITY_4: L3_behavior/utility_functions.md    (MAUT weights)
PRIORITY_5: L4_decision/decision.md             (Decision structure)
PRIORITY_6: L3_behavior/{relevant}.md           (Acoustic/Thermal/Compute/Power — по Intent)
PRIORITY_7: L5_validation/validation.md         (Hard constraints)
```

---

## Типичные ошибки LLM при PC-рекомендациях

| Ошибка | Что происходит | Как избежать |
|---|---|---|
| Implicit selection | "Выбираю X — хорошее" | Всегда candidate set + rejection |
| Context blindness | Один ответ для всех | BuildGoal первым |
| Risk silence | Только плюсы | Risk обязателен в каждом Decision |
| Metric fixation | Только avg FPS | Смотри BI, 1% low, frametime |
| Lifecycle blindness | "Вот сборка" | Lifecycle plan обязателен |
| Tradeoff hiding | Ничем не жертвуем | TradeOff обязателен |
| VRAM blindness | "12GB хватит" | Проверяй VRAM_Pressure риск явно |
| CPU-bottleneck blindness | Флагман GPU + бюджет CPU | BI check обязателен |
| Simulation skip | "Сборка выглядит нормально" без L3 прогона | Всегда STEP 5 (L3 Simulation) перед STEP 7 (Validation) |
| Weight hallucination | LLM назначает веса MAUT "из головы" | Веса из `utility_functions.md`, не из prompt |
| Adjective claims | "Тихий", "мощный", "холодный" | Акустический класс A0-A4, FPS 1% low, °C с указанием ambient |
