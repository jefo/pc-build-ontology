---
uri: "pcbo:meta/uri-scheme"
type: "MetaDocument"
version: "3.0.0-draft"
layer: "Meta"
date: "2026-06-03"
relations:
  usedBy: ["pcbo:meta/llm-guide", "pcbo:reasoning/synthesis"]
tags: ["meta", "uri", "naming", "reference"]
---

# URI Scheme — схема идентификации ресурсов PCBO

> Все сущности онтологии идентифицируются через URI префикса `pcbo:`.
> Это позволяет ссылаться на концепты без привязки к файловой системе.

---

## Базовый синтаксис

```
pcbo:{category}/{path}#{fragment}
```

| Часть | Пример | Назначение |
|---|---|---|
| `pcbo:` | префикс | Пространство имён PC Build Ontology |
| `{category}` | `ontology`, `reasoning`, `builds`, `components`, `system`, `meta` | Категория ресурса |
| `{path}` | `L3_behavior/acoustic` | Путь внутри категории |
| `#{fragment}` | `#A1_Ambient` | Конкретный концепт внутри документа (опционально) |

---

## Категории

```yaml
pcbo:ontology:
  description: "Формальная онтология (слои L1-L6)"
  path_pattern: "pcbo:ontology/L{l}_layer/{document}"
  examples:
    - "pcbo:ontology/L1_intent/intent"
    - "pcbo:ontology/L3_behavior/acoustic"
    - "pcbo:ontology/L5_validation/validation"

pcbo:reasoning:
  description: "Правила вывода и алгоритмы синтеза"
  path_pattern: "pcbo:reasoning/{document}"
  examples:
    - "pcbo:reasoning/synthesis"
    - "pcbo:reasoning/allocation"

pcbo:builds:
  description: "Верифицированные сборки (Build Artifacts)"
  path_pattern: "pcbo:builds/{build_id}"
  examples:
    - "pcbo:builds/build-001"
    - "pcbo:builds/template"

pcbo:components:
  description: "Индивиды онтологии — конкретные компоненты"
  path_pattern: "pcbo:components/{class}/{family}#{model}"
  examples:
    - "pcbo:components/cpu/amd_ryzen_7000#ryzen_7_7700"
    - "pcbo:components/gpu/nvidia_rtx_40_series#rtx_4060_ti_16gb"
  status: "PLANNED (task-001)"

pcbo:system:
  description: "Системный уровень — профили целей и сценарии"
  status: "PLANNED"

pcbo:meta:
  description: "Мета-документация"
  path_pattern: "pcbo:meta/{document}"
  examples:
    - "pcbo:meta/llm-guide"
    - "pcbo:meta/uri-scheme"
```

---

## Фрагменты (fragments)

Фрагмент указывает на конкретный концепт внутри документа:

```
pcbo:ontology/L3_behavior/acoustic#A2_LowHum
pcbo:ontology/L1_intent/intent#ai_inference_local
pcbo:reasoning/allocation#AR-03_Marginal_Value
pcbo:builds/build-001#Decision_gpu
```

---

## Правила разрешения

1. **URI не привязан к файловой системе.** `pcbo:ontology/L3_behavior/acoustic` разрешается в `L3_behavior/acoustic.md`, а не в `ontology/L3_behavior/acoustic.md`. Префикс `ontology/` в URI — логическая категория, не путь.

2. **При конфликте имён** — уточнять через fragment: `pcbo:ontology/L1_intent/intent#silent_build` vs `pcbo:system/goals#silent_build`.

3. **Несуществующие ресурсы** — ссылки на PLANNED ресурсы (components, system) валидны как forward references. LLM должна проверять existence перед использованием.

---

## Иерархия

```
pcbo:root
├── pcbo:ontology/
│   ├── pcbo:ontology/L1_intent/
│   │   ├── pcbo:ontology/L1_intent/intent
│   │   ├── pcbo:ontology/L1_intent/context
│   │   └── pcbo:ontology/L1_intent/workload
│   ├── pcbo:ontology/L2_constraint/
│   │   ├── pcbo:ontology/L2_constraint/structural
│   │   └── pcbo:ontology/L2_constraint/operational
│   ├── pcbo:ontology/L3_behavior/
│   │   ├── pcbo:ontology/L3_behavior/acoustic
│   │   ├── pcbo:ontology/L3_behavior/thermal
│   │   ├── pcbo:ontology/L3_behavior/compute
│   │   ├── pcbo:ontology/L3_behavior/power
│   │   ├── pcbo:ontology/L3_behavior/latency
│   │   ├── pcbo:ontology/L3_behavior/reliability
│   │   └── pcbo:ontology/L3_behavior/utility_functions
│   ├── pcbo:ontology/L3_performance/behavior   (таксономия)
│   ├── pcbo:ontology/L4_decision/
│   │   └── pcbo:ontology/L4_decision/decision
│   ├── pcbo:ontology/L5_validation/
│   │   └── pcbo:ontology/L5_validation/validation
│   └── pcbo:ontology/L6_lifecycle/
│       └── pcbo:ontology/L6_lifecycle/lifecycle
│
├── pcbo:reasoning/
│   ├── pcbo:reasoning/synthesis
│   └── pcbo:reasoning/allocation
│
├── pcbo:builds/
│   ├── pcbo:builds/template
│   ├── pcbo:builds/build-001
│   └── pcbo:builds/build-002
│
├── pcbo:components/                       [PLANNED]
│   ├── cpu/
│   ├── gpu/
│   ├── ram/
│   ├── storage/
│   ├── motherboard/
│   ├── psu/
│   ├── cooling/
│   └── cases/
│
├── pcbo:system/                           [PLANNED]
│   ├── pcbo:system/goals
│   └── pcbo:system/scenarios
│
└── pcbo:meta/
    ├── pcbo:meta/llm-guide
    └── pcbo:meta/uri-scheme
```
