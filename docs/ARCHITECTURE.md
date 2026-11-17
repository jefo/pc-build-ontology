# Архитектура

## 1. Место в процессе

```text
┌─────────────────────────────────────────────────────────────┐
│ LLM                                                         │
│   интерпретирует запрос                                     │
│   предлагает intent и кандидатов                            │
│   объясняет выбор                                           │
└───────────────────────────┬─────────────────────────────────┘
                            │ build.json
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PCBO Engine                                                 │
│   структурная геометрия                                     │
│   PCIe / питание / тепло / шум                              │
│   профили компонентов                                       │
│   бюджет и floors                                           │
│   L5 gate                                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ PASS | PASS_WITH_WARNINGS | FAIL
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Build Artifact                                              │
│   решение + отклонённые альтернативы                        │
│   trade-offs + риски + lifecycle                            │
└─────────────────────────────────────────────────────────────┘
```

Ключевая граница проходит между «предложить» и «разрешить». LLM работает до границы. После неё — только детерминированный код и данные.

---

## 2. Вход

`run_all.py` принимает JSON из stdin или первым аргументом. Полный пример — `examples/esports-240hz/build.json`.

Минимально значимые блоки:

```json
{
  "intent": "esports_1080p_240hz",
  "budget": { "actual_cost": 101800, "ceiling": 120000 },
  "case": { "max_gpu_mm": 350, "max_cooler_mm": 165 },
  "gpu": { "length_mm": 240, "width_slots": 2.0 },
  "cooler": { "height_mm": 155, "cooler_type": "air" },
  "motherboard": { "form_factor": "mATX", "m2_slots": 2 },
  "pcie": {
    "motherboard_chipset": "B650E",
    "gpu": { "pcie_width": 8, "pcie_gen": 4 }
  },
  "thermal": { "...": "..." },
  "power": {
    "cpu_tdp_W": 120,
    "gpu_tgp_W": 165,
    "psu": { "wattage": 650, "specification": "ATX2.4" }
  },
  "profile_check": {
    "components": [
      { "id": "amd-rx-7600", "type": "gpu", "file": "examples/kb/catalog/gpu/amd-rx-7600.md" }
    ],
    "user_intents": ["esports_1080p_240hz"],
    "primary_intent": "esports_1080p_240hz"
  }
}
```

Отсутствующий блок — не ошибка. Проверка, которой не хватает данных, возвращает `SKIP`. Но `SKIP` не равен `PASS`: итоговый gate видит, что проверка не выполнялась.

---

## 3. Проходы

| # | Pass | Вход | Что проверяет |
|---|---|---|---|
| 1 | `structural_clearance` | case, gpu, cooler, motherboard | Длина GPU, высота кулера, монтажные зазоры |
| 2 | `envelope_collision_3d` | cooler, motherboard, ram | 3D-пересечения с VRM и RAM |
| 3 | `pcie_topology` | pcie | Линии, поколение, бифуркация, DRAM-less |
| 4 | `thermal_profile` | thermal | Нагрев, mutual heating, thermal soak |
| 5 | `marginal_value` | mv_candidates | ΔPerformance / ΔPrice |
| 6 | `power_state` | power | Полная нагрузка, headroom, ATX 3.0 |
| 7 | `acoustic_class` | acoustic | Класс шума и ограничение интента |
| 8 | `profile_conflicts` | profile_check | `optimal` / `BLOCK` по профилям KB |
| 9 | `physical_constraints` | physical_check | Бинарные физические предикаты |
| 10 | `mvs_allocation` | budget, chipset, cpu, ram | Минимальная жизнеспособная спецификация |
| 11 | `cpu_vrm` | cpu_vrm | TDP процессора → класс VRM |
| 12 | `gpu_pcie` | gpu_pcie | Класс GPU → поколение слота |
| 13 | `component_floor` | component_floor | Полы интента для не-бутылочных компонентов |
| 14 | `l5_validation` | все результаты | Итоговый вердикт и rollback |

`run_all.py` вызывает проходы по порядку и собирает словарь результатов. `pass_contract.py` может обернуть этот вызов и записать трассировку каждого прохода: вход, выход, контракт, статус, нарушения.

---

## 4. Контракты

`pass_contract.py` описывает 14 проходов как контракты:

```python
PassContract(
    pass_name="structural_clearance",
    pass_phase="compile",
    pass_priority=1,
    input_schema=["case", "gpu", "cooler", "motherboard"],
    output_schema=["is_compatible", "failures", "tolerances"],
)
```

Во время выполнения контракт проверяет:

- все ли входные поля присутствуют;
- все ли выходные поля вернулись;
- не нарушил ли проход собственный output schema;
- не упал ли проход с исключением.

Отсюда четыре статуса трассы:

| Статус | Значение |
|---|---|
| `PASS` | Контракт соблюдён, проверка выполнена |
| `FAIL` | Проверка выполнена, но нарушила выходной контракт |
| `SKIP` | Не хватает входных данных |
| `ERROR` | Проход выбросил исключение |

Трасса сериализуется в JSON и может быть приложена к Build Artifact.

---

## 5. Конфигурация как данные

Пороги не зашиты в код:

| Файл | Содержимое |
|---|---|
| `chipset_profiles.yaml` | PCIe gen, VRM tier, M.2 slots, bifurcation |
| `cpu_vrm_tiers.yaml` | TDP → минимальный VRM tier |
| `gpu_pcie_tiers.yaml` | Класс GPU → требования к слоту |
| `intent_floors.yaml` | Минимальные полы по интентам |
| `budget_tiers.yaml` | Бюджетные тиры, MVS, доли бюджета |
| `domain_impact_matrix.yaml` | Доменные флаги компонентов |

Добавление нового чипсета — это новая запись в YAML, а не патч валидатора. Это сознательное решение: рынок железа меняется быстрее кода.

---

## 6. Профили компонентов

Карточка компонента — Markdown с YAML frontmatter:

```yaml
---
id: "amd-rx-7600"
type: "gpu"
profiles:
  mainstream_efficiency_tgp_150w:
    optimal_for_intents: ["aaa_1080p_ultra", "esports_1080p_240hz"]
    failure_for_intents: ["aaa_4k_ultra"]
    failure_type: "LINEAR_DEGRADATION"
    failure_severity: "BLOCK"
---
```

`validate_profile_conflicts` читает `profiles` и сравнивает с `user_intents`.

Правила:

- `optimal` — компонент соответствует интенту;
- `failure_for_intents` + `CLIFF_DROP` — `BLOCK` всегда;
- `failure_for_intents` + `LINEAR_DEGRADATION` по primary intent — `BLOCK`;
- то же по вторичному интенту — `WARN`;
- нет профиля — проверка молчит, но это видно в трассировке.

Корень базы знаний задаётся переменной `PCBO_KB_ROOT`. По умолчанию — корень этого репозитория, поэтому демо-карточки в `examples/kb/` находятся без настройки.

---

## 7. Семантика вердиктов

| Вердикт | Значение | Действие |
|---|---|---|
| `PASS` | Все проверки пройдены | Формировать Build Artifact |
| `PASS_WITH_WARNINGS` | Есть предупреждения, блокирующих нет | Формировать с оговорками |
| `FAIL` | Есть хотя бы один `BLOCK` | Rollback и пересмотр |

`SKIP` не повышает вердикт. Если данных нет, это фиксируется в трассе, но не превращается в «всё хорошо».

---

## 8. Как расширять

**Новый чипсет.** Добавить запись в `chipset_profiles.yaml`.

**Новый интент.** Добавить floors в `intent_floors.yaml`, при необходимости — профили в карточки компонентов.

**Новый компонент.** Добавить карточку в базу знаний с `profiles`.

**Новый валидатор.** Написать функцию `validate(data) -> dict`, добавить вызов в `run_all.py` и контракт в `build_pcbo_contracts()`.

**Новый рынок.** Перекалибровать `budget_tiers.yaml`: валюта, диапазоны, reference prices.

---

## 9. Границы архитектуры

- Нет базы данных. Вход и выход — JSON.
- Нет сети. Движок полностью офлайн.
- Нет LLM внутри проверок.
- Нет веб-слоя и API.
- Нет автоматического обновления цен.
- Нет пользовательских сессий.

Это осознанно: сначала должен быть проверяемый домен, потом обвязка.
