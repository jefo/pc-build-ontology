---
uri: "pcbo:ontology/L4_decision/decision"
type: "OntologyDocument"
layer: "L4"
version: "2.0.0"
relations:
  uses: ["pcbo:ontology/L1_intent", "pcbo:ontology/L2_constraint",
         "pcbo:ontology/L3_performance", "pcbo:ontology/L4_decision/rationale",
         "pcbo:ontology/L4_decision/tradeoff", "pcbo:ontology/L4_decision/risk"]
  produces: ["pcbo:builds/template"]
tags: ["decision", "rationale", "tradeoff", "core", "L4"]
---

# L4 · Decision — акт инженерного выбора

> "Не галлюцинировать выбор, а воспроизводить его как **инженерный акт**."

Decision — центральная сущность PCBO v2.  
Это то, что превращает сборку из списка деталей в **аргументированный артефакт**.

---

## Класс Decision

```yaml
Decision:
  # Идентификация
  id:             String          # "decision:gpu_primary"
  component_class: ComponentClass # GPU, CPU, RAM, ...
  build_ref:      URI             # ссылка на Build, к которому относится

  # Кандидаты
  candidates:     [Component]     # все рассмотренные варианты
  selected:       Component       # выбранный
  rejected:       [RejectedOption] # отклонённые + причины
  
  # Критерии
  primary_criterion:  Metric      # главная метрика выбора
  secondary_criteria: [Metric]    # вторичные метрики
  constraint_set:     [URI]       # активные ограничения из L2
  
  # Аргументация
  rationale:      Rationale       # почему именно этот выбор
  tradeoffs:      [TradeOff]      # что принесено в жертву
  risks:          [Risk]          # известные риски выбора
  
  # Метаданные
  confidence:     Enum[high, medium, low]  # уверенность в выборе
  sensitivity:    String          # "Цена +$50 не меняет вывод; +$100 - меняет"

RejectedOption:
  component:  Component
  reason:     Enum[price, performance, compatibility, availability, risk]
  explanation: String
  
  # Количественное обоснование отклонения
  delta_vs_selected:
    price_delta_USD:     Float    # +/- относительно selected
    performance_delta_pct: Float  # +/- производительность
    marginal_value:      Float    # delta_fps / delta_price
```

---

## Класс Rationale

```yaml
Rationale:
  # Тип аргументации (один или несколько)
  argument_types: [ArgumentType]
  
  # Конкретные аргументы
  arguments: [Argument]
  
  # Трассировка к метрикам и правилам
  metrics_referenced: [URI]     # pcbo:ontology/L3_performance/metrics#PPR
  rules_applied:      [URI]     # pcbo:reasoning/allocation#AR-03

ArgumentType:
  price_performance    # PPR argument
  compatibility        # совместимость с остальной сборкой
  thermal              # тепловой аргумент
  acoustic             # акустический аргумент
  upgrade_path         # долгосрочность платформы
  availability         # доступность на рынке
  reliability          # надёжность, репутация
  power_efficiency     # энергопотребление
  synergy              # синергия с другими компонентами
  future_proof         # запас для будущих нагрузок
  diminishing_returns  # закон убывающей отдачи
  budget_reallocation  # освобождение бюджета для другого компонента
```

---

## Класс TradeOff

```yaml
TradeOff:
  objective_a:     Objective    # что получаем
  objective_b:     Objective    # чем жертвуем
  magnitude:       Enum[minor, moderate, significant, major]
  reversible:      Boolean      # можно ли исправить апгрейдом
  
  quantification:
    gain:          String       # "+20% FPS в AAA"
    cost:          String       # "-25% производительности в Blender"
    
  context_dependency:
    relevant_for:  [Intent]     # для каких Intent этот tradeoff важен
    irrelevant_for: [Intent]    # для каких — нет

Objective:
  type:   Enum[performance, value, reliability, longevity, thermal, acoustic, ...]
  metric: URI                   # ссылка на метрику из L3
  value:  Float                 # конкретное значение, если применимо
```

---

## Класс Risk

```yaml
Risk:
  id:              String
  behavior_ref:    URI          # pcbo:ontology/L3_performance/behavior#X
  trigger:         Predicate    # условие активации риска
  
  severity:        Enum[critical, high, medium, low]
  probability:     Float        # 0..1 при активированном trigger
  
  impact:          String       # что произойдёт если риск реализуется
  mitigation:      [String]     # способы снижения
  residual_risk:   String       # что остаётся после митигации
  
  monitoring:      String       # как обнаружить риск в реальной эксплуатации
```

---

## Шаблон Decision для LLM

Когда LLM выбирает компонент, он должен заполнить эту структуру.  
Это предотвращает галлюцинации и делает reasoning прозрачным:

```markdown
### Decision: GPU

**Кандидаты рассмотрены**:
- RTX 4070 ($550) — основной кандидат
- RTX 4070 Ti ($750) — следующий тир
- RX 7800 XT ($500) — альтернатива AMD

**Выбран**: RTX 4070

**Отклонены**:
- RTX 4070 Ti: +$200 при +18% FPS → Marginal Value = 0.09 FPS/$ < порога AR-03.
  Высвобождённые $200 эффективнее работают в CPU/RAM.
- RX 7800 XT: Производительность сопоставима, но DLSS4 MFG у RTX 4070
  критичен для intent:aaa_gaming_1440p при использовании DLSS-supported тайтлов.

**Ключевой критерий**: PPR в 1440p gaming

**Rationale**:
- [price_performance] RTX 4070 показывает лучший PPR в классе mid-high для 1440p
- [synergy] DLSS4 активирует syn:rtx40_dlss4 — эффективный прирост без
  реального апгрейда GPU
- [budget_reallocation] $200 сэкономлены vs Ti переходят в Ryzen 7 7800X3D

**TradeOff**:
- Получаем: $200 на CPU, DLSS4
- Жертвуем: 18% native FPS, 4GB VRAM
- Magnitude: moderate
- Reversible: да (апгрейд GPU)

**Risks**:
- VRAM_Pressure при 1440p ultra в тяжёлых сценах: severity=medium
  Mitigation: DLSS Quality снижает рабочее разрешение
- Driver maturity (NVIDIA): severity=low (зрелый драйвер)
```

---

## Decision Chain (цепочка решений)

Решения взаимозависимы. Порядок принятия решений важен:

```
DECISION_CHAIN для AAA Gaming 1440p:

1. PLATFORM_DECISION
   "AM5 или LGA1851?"
   → Определяет: RAM type, MB, CPU candidates
   → Влияет на: upgrade_path, budget_distribution

2. GPU_DECISION  ← PRIMARY для gaming intent
   "Какой GPU?"
   → Определяет: PSU wattage, PCIe slot, VRAM headroom
   → Влияет на: CPU_DECISION (bottleneck pairing)

3. CPU_DECISION
   "Какой CPU?" (с учётом выбранного GPU)
   → Constraint: должен не создавать BI > 15% с выбранным GPU
   → Влияет на: RAM speed (платформо-зависимо)

4. RAM_DECISION
   "Сколько + как быстро?"
   → Constraint: тип платформы, скорость IMC
   → Rule: всегда dual-channel

5. STORAGE_DECISION
   "NVMe Gen4 обязателен?"
   → Constraint: PCIe lanes на MB
   
6. PSU_DECISION
   "Какая мощность?"
   → Constraint: system_tdp × 1.2 ≤ psu.wattage
   → NOT a creativity zone — следуй правилу

7. COOLING_DECISION
   "Air или AIO?"
   → Constraint: cpu.tdp_W, ambient_temp, noise_constraint

8. MOTHERBOARD_DECISION
   "Финальный выбор MB"
   → Must satisfy: all previous decisions' constraints
```

---

## Антипаттерны Decision

Ситуации, которые LLM должен явно отклонять:

### ANTI-01 — Имплицитный выбор

```
ANTI-PATTERN: "Я выбираю RTX 4070 — хорошая карта"
PROBLEM: Нет candidate set, нет критериев, нет tradeoff
CORRECT: Всегда сравнивай ≥ 2 кандидата с явными критериями
```

### ANTI-02 — Один кандидат без rejection

```
ANTI-PATTERN: Рассмотрен только один вариант
PROBLEM: Решение нельзя проверить — нет baseline для сравнения
CORRECT: Минимум 2 кандидата, один из которых дешевле на $50-100
```

### ANTI-03 — Трансфер rationale

```
ANTI-PATTERN: "RTX 4090 лучший GPU, поэтому рекомендую его"
PROBLEM: Rationale "лучший GPU" не релевантен для intent:budget_gaming
CORRECT: Rationale всегда привязан к конкретному Intent + Context
```

### ANTI-04 — Игнорирование Risk

```
ANTI-PATTERN: Decision без поля risks
PROBLEM: Каждый выбор несёт риски — их замалчивание нечестно
CORRECT: Всегда идентифицируй хотя бы один риск, даже если severity=low
```
