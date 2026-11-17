---
uri: "pcbo:root"
type: "SystemRoot"
version: "3.0.0-draft"
mbse_level: "Implementation Model"
relations:
  defines: ["pcbo:ontology", "pcbo:system", "pcbo:reasoning"]
  entryFor: "LLM_Agent"
tags: ["root", "mbse", "decision-ontology", "v3"]
---

# PC Build Ontology (PCBO) v2

> **Онтология синтеза и верификации PC-конфигураций как инженерных решений.**

Не каталог железа. Не прайс. Не список лучших покупок.  
Формальная модель того, как из **цели**, **контекста**, **ограничений** и **метрик**  
получается *обоснованная*, *прослеживаемая*, *верифицируемая* сборка.

---

## Позиция в MBSE Framework

```
Problem / Need Model   ← "что нужно и зачем"
       ↓
Solution Model         ← "какое решение удовлетворяет потребность"
       ↓
Implementation Model   ← PCBO живёт здесь
       ↓
       "какая именно конфигурация является корректной,
        эффективной и объяснимой реализацией под данный контекст"
```

---

## Семь онтологических слоёв

| Слой | Документ | Роль |
|---|---|---|
| **L1a Intent** | `intent.md` | Зачем строится система |
| **L1b Context** | `context.md` | В каких условиях существует |
| **L1c Workload** | `L1_intent/workload.md` | Профили нагрузки |
| **L2 Constraint** | `L2_constraint/` | Feasibility envelope |
| **L3 Performance** | `behavior.md` + `L3_behavior/` | Таксономия + поведенческие модели |
| **L4 Decision** | `decision.md` | Decision + Rationale + TradeOff + Risk |
| **L5 Validation** | `L5_validation/validation.md` | Верификация корректности |
| **L6 Lifecycle** | `lifecycle.md` | Build → Upgrade → Obsolescence |
| **Reasoning** | `reasoning/synthesis.md` + `reasoning/allocation.md` | Алгоритм синтеза + правила бюджета |

---

## Центральный принцип: сборка как Decision Artifact

Каждый выбор компонента — это **Decision** со структурой:

```yaml
Decision:
  candidates:    [list of alternatives considered]
  selected:      chosen option
  rejected:      [alternatives] + reason why
  criteria:      [metrics used to compare]
  rationale:     argument for selection
  tradeoffs:     [what was sacrificed]
  risks:         [known risks of this choice]
  constraints_satisfied: [which constraints this satisfies]
```

Это превращает сборку из "списка деталей" в **инженерный артефакт** с полной трассировкой.

---

## Верхнеуровневые классы

```
Build                 ← конфигурация, не набор деталей
BuildGoal             ← Intent + Workload + Context
Constraint            ← feasibility envelope
Component             ← подчинённый слой (не центральный!)
CompatibilityRule     ← структурные ограничения
PerformanceMetric     ← многомерное измерение успеха
Decision              ← акт выбора + candidate set
Rationale             ← аргументация выбора
TradeOff              ← что принесено в жертву
Risk                  ← известные риски решения
ValidationResult      ← статус верификации
LifecycleStage        ← состояние системы во времени
SystemBehavior        ← bottleneck, throttling, contention
```

---

## Структура репозитория

```
ontology/                                 ← онтологическая часть (этот каталог)
├── README.md                             ← точка входа (pcbo:root)
├── llm-guide.md                          ← инструкция для LLM-агента
│
├── # L1 · Intent
├── intent.md                             ← таксономия Intent + инстанции
├── context.md                            ← OperationalContext + MOD-CTX правила
├── L1_intent/workload.md                 ← профили нагрузки
│
├── # L2 · Constraint
├── L2_constraint/structural.md           ← совместимость, физика
├── L2_constraint/operational.md          ← мощность, тепло, шум
│
├── # L3 · Performance / Behavior
├── behavior.md                           ← таксономия (обзорная карта концепций)
├── L3_behavior/acoustic.md               ← акустическая модель (A0-A4)
├── L3_behavior/thermal.md                ← тепловая модель
├── L3_behavior/compute.md                ← вычислительная модель
├── L3_behavior/power.md                  ← энергетическая модель
├── L3_behavior/latency.md                ← модель задержек
├── L3_behavior/reliability.md            ← модель надёжности
├── L3_behavior/utility_functions.md      ← MAUT веса для scoring
│
├── # L4 · Decision
├── decision.md                           ← Decision, Rationale, TradeOff, Risk
│
├── # L5 · Validation
├── L5_validation/validation.md           ← протокол верификации + Rollback
│
├── # L6 · Lifecycle
├── lifecycle.md                          ← жизненный цикл + obsolescence + upgrade
│
├── # Reasoning
├── reasoning/synthesis.md                ← STATE_0..8: алгоритм синтеза (DAG)
├── reasoning/allocation.md               ← AR-01..05: правила распределения бюджета
│
├── # Build Artifact
├── template.md                           ← шаблон Build Artifact
│
└── # Meta
    └── meta/uri-scheme.md                ← схема идентификации pcbo: URI
```

Движок и примеры лежат на уровень выше:

```
../engine/                                ← 14 детерминированных проверок
../examples/esports-240hz/                ← валидная сборка + ожидаемый вывод
../examples/xeon-rtx4090-trap/            ← сборка с блокирующими ошибками
../examples/kb/                           ← демо-карточки компонентов
```

### Запланировано, но не построено

```
components/          ← индивиды CPU, GPU, RAM, ... — см. kaizin-lab/pc_hardware_knowledge_base
system/goals.md      ← BuildGoal profiles
system/scenarios.md  ← сценарии использования
```

---

## Отношения между верхнеуровневыми сущностями

```
Build          consistsOf      Component
Build          satisfies       BuildGoal
Build          hasConstraint   Constraint
Build          optimizedFor    Workload
Build          hasStage        LifecycleStage

Decision       selects         Component
Decision       rejects         Alternative
Decision       justifiedBy     Rationale
Decision       involves        TradeOff
Decision       acknowledges    Risk

Rationale      references      PerformanceMetric
Rationale      cites           CompatibilityRule
TradeOff       links           [Objective × Objective]
Risk           affects         Decision
ValidationResult validates     Build

Component      exhibits        SystemBehavior
SystemBehavior triggers        Risk
```