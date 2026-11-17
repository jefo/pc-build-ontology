---
uri: "pcbo:builds/template"
type: "BuildTemplate"
version: "2.0.0"
relations:
  producedBy: ["pcbo:reasoning/synthesis"]
  verifiedBy: ["pcbo:ontology/L5_validation/validation"]
  instantiates: ["pcbo:ontology/L4_decision/decision"]
tags: ["build", "template", "decision-artifact", "v2"]
---

# Шаблон Build Artifact (v2)

Сборка как инженерный артефакт с полной трассировкой решений.

---

## Frontmatter схема

```yaml
---
uri: "pcbo:builds/{id}"
type: "PCBuild"
version: "2.0.0"
mbse_level: "Implementation Model"

# BuildGoal (L1)
intent:           "pcbo:ontology/L1_intent/intent#{intent_id}"
context:          "pcbo:ontology/L1_intent/context#{context_id}"
workload_profile: "pcbo:ontology/L1_intent/workload#{workload_id}"

# Бюджет и контекст
budget_ceiling_USD:  Float
actual_cost_USD:     Float
market_region:       String
build_date:          Date

# Верификация (L5)
validation_status:   Enum[PASS, PASS_WITH_WARNINGS, FAIL]
validation_ref:      "pcbo:ontology/L5_validation"
validation_date:     Date

# Метрики результата (L3)
achieved_metrics:
  fps_avg:             Float
  fps_1pct:            Float
  frametime_sigma_ms:  Float
  bottleneck_index:    Float
  system_tdp_W:        Integer
  noise_dba:           Float    # если измерено

# Decision chain (L4) — ссылки на Decision artifacts
decisions:
  platform:     {inline Decision}
  gpu:          {inline Decision}
  cpu:          {inline Decision}
  ram:          {inline Decision}
  storage:      {inline Decision}
  psu:          {inline Decision}
  cooling:      {inline Decision}
  motherboard:  {inline Decision}

# Lifecycle (L6)
lifecycle:
  tuning_plan:      [String]
  upgrade_horizon:  {Map<Year, UpgradePlan>}
  end_of_life_indicators: [String]

# Активные риски
active_risks: [{Risk}]   # риски, не полностью смягчённые

tags: ["{intent}", "{budget_tier}", "{resolution}"]
---
```

---

## Тело документа

```markdown
# Build: {Название}

> {Одна строка: для кого, для чего, ключевой компромисс}

## BuildGoal

| Параметр | Значение |
|---|---|
| Intent | {label} |
| Целевая нагрузка | {workload описание} |
| Разрешение / FPS | {resolution} / {fps_target} |
| Бюджет | ${budget} |
| Регион | {region} |
| Срок службы | {years} лет |
| Акустика | {noise_constraint} |

## Компонентная таблица

| Компонент | Модель | Цена | Доля | Tier |
|---|---|---|---|---|
| CPU | {model} | ${price} | {%} | {tier} |
| GPU | {model} | ${price} | {%} | {tier} |
| RAM | {model} | ${price} | {%} | {tier} |
| Storage | {model} | ${price} | {%} | {tier} |
| Motherboard | {model} | ${price} | {%} | {tier} |
| PSU | {model} | ${price} | {%} | {tier} |
| Cooling | {model} | ${price} | {%} | {tier} |
| **Итого** | | **${total}** | 100% | |

## Decision Chain

### Decision: GPU ← [PRIMARY]

**Рассмотрено**: RTX 4070 · RTX 4070 Ti · RX 7800 XT

**Выбран**: RTX 4070 ($550)

**Отклонены**:
- RTX 4070 Ti ($750): MV = +18% FPS / +$200 = 0.09 FPS/$ — ниже порога.
  $200 переходят в CPU budget.
- RX 7800 XT ($500): Сопоставимая производительность, но intent требует DLSS4.

**Rationale**:
- [price_performance] Лучший PPR в классе mid-high для 1440p
- [synergy] DLSS4 при intent:aaa_gaming_1440p — syn:rtx40_dlss4 активирован
- [budget_reallocation] -$200 vs Ti → перераспределены в CPU

**TradeOff**:
- Gain: $200 в CPU, DLSS4 MFG доступен
- Cost: -18% native FPS vs Ti, 12GB vs 16GB VRAM
- Magnitude: moderate | Reversible: да

**Risks**:
- VRAM_Pressure @ 1440p ultra: severity=medium, prob=0.4
  Mitigation: DLSS Quality снижает рабочее разрешение

---

### Decision: CPU

**Рассмотрено**: Ryzen 7 7800X3D · Ryzen 5 7600X · i5-14600K

**Выбран**: Ryzen 7 7800X3D ($390)

**Rationale**:
- [synergy] syn:x3d_games активирован для intent:aaa_gaming_1440p
- [price_performance] Лучший игровой CPU 2024 для 1440p
- [upgrade_path] AM5 платформа → апгрейд в рамках сокета до Ryzen 9000

**TradeOff**:
- Gain: лучший игровой FPS, X3D синергия
- Cost: слабый в multithread (Content Creation), DDR5 обязателен
- Magnitude: minor для gaming-intent | significant если появится Content_Creation

**Risks**:
- No_iGPU: severity=low. Mitigation: GPU присутствует в сборке

---

### Decision: PSU

**Выбран**: Seasonic Focus Gold 750W

**Rationale**:
- [compatibility] System TDP ≈ 350W → 750W = 2.1× headroom (норма)
- [reliability] Seasonic = топ-1 по надёжности (Cybenetics/JonnyGuru)
- [power_efficiency] 80+ Gold: КПД >90% при 50% нагрузке

**TradeOff**: None significant. PSU — not a creativity zone.

**Risks**: Нет при 2× headroom.

---

## Валидация

| Проверка | Статус | Заметка |
|---|---|---|
| Socket compatibility | ✅ | AM5 × AM5 |
| RAM type | ✅ | DDR5 × DDR5 |
| PSU headroom | ✅ | 750W / 350W = 2.1× |
| VRAM sufficiency | ✅ | 12GB ≥ 10GB threshold (1440p) |
| BI (CPU/GPU) | ✅ | ~5% @ 1440p |
| Dual channel RAM | ✅ | 2×16GB |
| Budget | ✅ | $1,350 / $1,400 = 96.4% |

**Статус**: ✅ PASS

## Метрики

| Метрика | Значение |
|---|---|
| BI (Bottleneck Index) | ~5% |
| BAQ (Budget Allocation) | 0.87 |
| System TDP | ~350W |
| PSU Headroom | 2.1× |

## Активные Risks

- VRAM_Pressure при 1440p ultra-settings: severity=medium
  → Workaround: DLSS Quality / снизить текстуры до high

## Lifecycle

**Tuning**: XMP DDR5-6000 CL30 в BIOS · Fan curves · Prime95 30min

**Апгрейд Year 2-3**: GPU если BI > 20% с новым поколением GPU (~$300-400)  
**Апгрейд Year 3-4**: CPU в рамках AM5 (Ryzen 9000X3D при выходе)  
**Refresh Year 5+**: Platform if AM5 не развивается далее

**Слабейшее звено сейчас**: VRAM (12GB на пределе для 1440p ultra к 2026)
```
