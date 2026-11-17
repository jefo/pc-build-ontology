---
uri: "pcbo:ontology/L1_intent/context"
type: "OntologyDocument"
layer: "L1"
version: "2.0.0"
relations:
  feedsInto: ["pcbo:ontology/L2_constraint", "pcbo:ontology/L4_decision/rationale"]
  seealso: ["pcbo:ontology/L1_intent/intent", "pcbo:ontology/L1_intent/workload"]
tags: ["context", "environment", "constraints-source", "L1", "ontology"]
---

# L1 · Context — эксплуатационный контекст

> Контекст важен, потому что одна и та же сборка может быть разумной  
> в одном контексте и **бессмысленной в другом**.

Context — это не часть Intent ("зачем"), это условия существования системы.  
Именно Context активирует дополнительные ограничения, которых нет в Intent.

---

## Класс OperationalContext

```yaml
OperationalContext:

  # Экономический контекст
  budget_ceiling_USD:   Float         # жёсткий потолок
  budget_target_USD:    Float         # целевая точка (может быть меньше потолка)
  price_sensitivity:    Enum[low, medium, high, critical]
  market_region:        String        # влияет на доступность и цены
  currency:             String
  
  # Временной контекст
  expected_lifespan_years:    Integer  # сколько лет система должна служить
  upgrade_horizon_years:      Integer  # когда планируется первый апгрейд
  upgrade_budget_reserved:    Float    # зарезервировано на апгрейд
  purchase_urgency:     Enum[now, flexible, wait_for_sale]
  
  # Физические ограничения
  form_factor:          Enum[ATX, mATX, ITX, open_frame]
  case_max_gpu_mm:      Integer        # макс. длина GPU в мм
  case_max_cooler_mm:   Integer        # макс. высота кулера в мм
  ambient_temp_celsius: Integer        # температура окружающей среды
  
  # Акустические ограничения
  noise_constraint:     Enum[none, moderate, strict, silent]
  dba_max_under_load:   Float          # если noise_constraint != none
  
  # Энергетические ограничения
  electricity_cost_kwh: Float          # стоимость кВт·ч (влияет на выбор PSU, TDP)
  power_outlet_max_W:   Integer        # предельная мощность розетки
  ups_exists:           Boolean
  
  # Пользовательский контекст
  user_skill_level:     Enum[beginner, intermediate, enthusiast, expert]
  diy_assembly:         Boolean        # самосборка или сборка в магазине
  overclocking_intent:  Boolean
  
  # Программный контекст  
  os_target:            String         # Windows 11, Linux, macOS (Hackintosh)
  software_dependencies: [String]      # специфичные требования к ПО/драйверам
  
  # Предпочтения
  brand_preferences:    Map[ComponentClass → [Brand]]  # если реальное ограничение
  brand_exclusions:     Map[ComponentClass → [Brand]]  # например, driver_issues
  aesthetics:           Enum[irrelevant, minimal, rgb_welcome]
```

---

## Контекстные модификаторы Decision

Context напрямую модифицирует аргументацию выбора (Rationale).

### MOD-CTX-01 — Высокая стоимость электричества

```
IF context.electricity_cost_kwh > 0.20 USD
THEN
  weight(power_efficiency) += 0.15
  PREFER components WHERE tdp_W = lower AT same performance
  REASON: "При стоимости {cost}/кВт·ч экономия 50W = ${annual}$/год"
  ACTIVATES: Rationale.power_efficiency_argument
```

### MOD-CTX-02 — Жаркий климат / плохая вентиляция

```
IF context.ambient_temp_celsius > 30
   OR context.case_airflow = "restricted"
THEN
  weight(thermal_envelope) += 0.20
  PREFER components WHERE tdp_W < tier_average
  PREFER cooler.type IN [AIO_360, custom_loop]
  REJECT components WHERE thermalmargin < 10°C AT ambient
  REASON: "Высокая ambient temp снижает эффективное охлаждение на {delta}°C"
```

### MOD-CTX-03 — Строгое акустическое ограничение

```
IF context.noise_constraint IN [strict, silent]
THEN
  BLOCK: components WHERE noise_rating = "loud"
  PREFER: Noctua, be quiet!, Fractal Design (bios fan curves важны)
  CONSTRAIN: cpu.tdp_W ≤ 95 OR cooling = AIO_360
  MODIFY: psu.fan_type = semi-passive OR fanless
```

### MOD-CTX-04 — Низкий бюджет + длинный horizon

```
IF context.budget_ceiling < 600 USD
   AND context.expected_lifespan_years >= 4
THEN
  PREFER: platform WITH long_upgrade_path
  PREFER: AM5 OVER LGA1700 (LGA1700 dead-end)
  INCREASE: weight(upgrade_path_argument)
  REASON: "Платформа живёт дольше любого отдельного компонента"
```

### MOD-CTX-05 — ITX / компактный корпус

```
IF context.form_factor = ITX
THEN
  FILTER: motherboard WHERE form_factor = ITX
  FILTER: gpu WHERE length_mm ≤ context.case_max_gpu_mm
  FILTER: cooler WHERE height_mm ≤ context.case_max_cooler_mm
  PREFER: PSU SFX OVER ATX
  WARN: "ITX thermal management требует тщательного планирования airflow"
  NOTE: "В ITX корпусах горячий воздух GPU может нагревать CPU cooler"
```

### MOD-CTX-06 — Программные зависимости

```
IF context.software_dependencies CONTAINS ["DaVinci Resolve"]
THEN
  PREFER: GPU vendor = NVIDIA (лучшая поддержка CUDA в Resolve)
  NOTE: "AMD GPU работает в OpenCL, но CUDA быстрее для GPU-acceleration"

IF context.software_dependencies CONTAINS ["Linux"]
THEN
  PREFER: GPU vendor = AMD (open-source drivers)
  WARN: "NVIDIA на Linux: проприетарный драйвер, возможны сложности"
  
IF context.software_dependencies CONTAINS ["macOS_Hackintosh"]
THEN
  BLOCK: GPU vendor = NVIDIA (нет поддержки macOS после Kepler)
  PREFER: AMD RX 6xxx/7xxx (лучшая поддержка)
```

---

## Неочевидные контекстные факторы

Часто упускаемые, но важные:

| Фактор | Влияние |
|---|---|
| Регион: Россия/СНГ | Ограниченная доступность некоторых брендов, серый импорт |
| Мониторинг рынка | GPU часто дешевеют на 10-20% через 6-9 месяцев после релиза |
| Электричество | Разница 100W × 8ч × 365д × €0.25 = €73/год |
| Ambient temp | При +35°C и слабом airflow — тротлинг неминуем |
| User skill | Разгон требует времени и риска; beginners → надёжность > производительность |
| Апгрейд-резерв | Купить слабее сейчас + сильнее потом = часто лучше, чем всё сразу в середине |
