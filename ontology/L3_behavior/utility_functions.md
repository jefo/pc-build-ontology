---
uri: "pcbo:ontology/L3_behavior/utility_functions"
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
    MAUT weights являются инженерной оценкой относительной важности метрик.
    Не калиброваны на пользовательских предпочтениях через A/B тестирование
    или опросы. Приоритеты отражают инженерное суждение, не эмпирику.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"         # каждый Intent имеет свою utility function
  feedsInto:
    - "pcbo:ontology/L4_decision/decision"      # веса используются в Rationale scoring
  seealso:
    - "pcbo:ontology/L3_behavior/compute"       # compute метрики — вход для utility
    - "pcbo:ontology/L3_behavior/acoustic"      # acoustic метрики — вход для utility
    - "pcbo:ontology/L3_behavior/thermal"       # thermal метрики — вход для utility
tags: ["maut", "utility", "weights", "multi-criteria", "L3", "decision-support"]
---

# L3 · Utility Functions — MAUT аксиомы

> **LLM не решает, что важно. LLM подставляет значения в заданные веса.**
>
> Multi-Attribute Utility Theory (Keeney & Raiffa, 1976):
> выбор = argmax Σ(wᵢ × uᵢ(candidate)) по всем критериям.

---

## Принцип

```yaml
MAUT_Principle:
  formula: "U(component) = Σ (weight_i × utility_i(component))"
  constraints:
    - "Σ weights = 1.0 для каждого Intent"
    - "Веса хранятся в онтологии, не в LLM prompt"
    - "LLM получает веса и вычисляет utility scores для candidates"
    - "LLM не модифицирует веса (если confidence < HIGH — запрашивает пользователя)"
```

---

## Utility Functions по Intent

### Gaming Intents

```yaml
intent:aaa_gaming_4k:
  dominant_component: GPU
  weights:
    fps_avg:            0.30
    vram_capacity:      0.25      # 4K ultra требует много VRAM
    fps_1pct_low:       0.20
    upgrade_path:       0.10
    power_efficiency:   0.05
    acoustic_load:      0.05
    thermal_margin:     0.05
  note: "4K = GPU bound практически всегда. CPU и RAM — вторичны."

intent:aaa_gaming_1440p:
  dominant_component: GPU
  weights:
    fps_avg:            0.25
    fps_1pct_low:       0.20
    vram_capacity:      0.20
    cpu_single_thread:  0.10      # при 1440p CPU уже важен
    upgrade_path:       0.10
    acoustic_load:      0.05
    power_efficiency:   0.05
    thermal_margin:     0.05
  note: "Баланс GPU/CPU. 1440p — sweet spot где оба важны."

intent:aaa_gaming_1080p:
  dominant_component: GPU
  weights:
    fps_avg:            0.25
    cpu_single_thread:  0.20      # 1080p CPU-bound много где
    fps_1pct_low:       0.20
    vram_capacity:      0.10      # 8GB обычно достаточно
    ram_latency:        0.10
    upgrade_path:       0.05
    power_efficiency:   0.05
    acoustic_load:      0.05
  note: "1080p — CPU важнее чем при 1440p/4K."

intent:esports_240hz:
  dominant_component: CPU
  weights:
    fps_1pct_low:       0.30      # стабильность важнее среднего FPS
    cpu_single_thread:  0.20
    ram_latency:        0.15
    frametime_variance: 0.15
    gpu_raw:            0.05      # даже mid GPU даёт 300+ FPS
    input_latency:      0.10
    acoustic_load:      0.03
    thermal_margin:     0.02
  note: "CPU + RAM определяют esports. GPU — любой mid-tier достаточен."

intent:esports_144hz:
  dominant_component: CPU
  weights:
    fps_1pct_low:       0.25
    cpu_single_thread:  0.20
    ram_latency:        0.15
    frametime_variance: 0.15
    gpu_raw:            0.10
    input_latency:      0.10
    acoustic_load:      0.03
    thermal_margin:     0.02

intent:vr_gaming:
  dominant_component: GPU
  weights:
    frametime_variance: 0.30      # VR критичен к стабильности
    fps_1pct_low:       0.25
    gpu_raw:            0.20
    vram_capacity:      0.10
    cpu_single_thread:  0.10
    thermal_margin:     0.05
  note: "Frametime variance в VR = motion sickness. Стабильность > всё."
```

### Creative Intents

```yaml
intent:video_editing_4k:
  dominant_component: CPU
  weights:
    cpu_multi_thread:   0.30      # рендер — многопоточный
    ram_capacity:       0.25      # 32-64GB для комфорта
    storage_sequential: 0.15      # чтение 4K media
    gpu_encode:         0.10      # NVENC/QuickSync для экспорта
    cpu_single_thread:  0.10      # timeline responsiveness
    power_efficiency:   0.05
    acoustic_load:      0.05
  note: "CPU + RAM доминируют. GPU важен для encode, не для рендера (кроме Resolve)."

intent:video_editing_1080p:
  dominant_component: CPU
  weights:
    cpu_multi_thread:   0.25
    ram_capacity:       0.20
    cpu_single_thread:  0.15
    storage_sequential: 0.15
    gpu_encode:         0.10
    power_efficiency:   0.10
    acoustic_load:      0.05

intent:3d_rendering_cpu:
  dominant_component: CPU
  weights:
    cpu_multi_thread:   0.45
    ram_capacity:       0.25
    storage_sequential: 0.10
    power_efficiency:   0.10
    thermal_margin:     0.10    # sustained load → throttling risk
  note: "CPU rendering — чисто многопоточная задача. GPU не участвует."

intent:3d_rendering_gpu:
  dominant_component: GPU
  weights:
    gpu_cuda_cores:     0.35
    vram_capacity:      0.30    # сцены могут требовать 16-24GB
    cpu_multi_thread:   0.15    # подготовка сцены
    ram_capacity:       0.10
    thermal_margin:     0.10    # sustained GPU load
  note: "GPU rendering (Octane/Redshift/Cycles GPU). VRAM критичен для больших сцен."

intent:music_production:
  dominant_component: CPU
  weights:
    cpu_single_thread:  0.30
    ram_capacity:       0.20
    storage_latency:    0.15    # загрузка семплов
    audio_latency:      0.15
    acoustic_idle:      0.10    # тишина в студии
    power_efficiency:   0.05
    thermal_margin:     0.05
  note: "Single-thread для плагинов + audio latency + абсолютная тишина."

intent:photography:
  dominant_component: CPU
  weights:
    cpu_single_thread:  0.25
    ram_capacity:       0.25    # панорамы / HDR — 32-64GB
    storage_sequential: 0.20
    cpu_multi_thread:   0.15    # batch export
    vram_capacity:      0.10    # AI-фильтры (Lightroom Denoise)
    acoustic_idle:      0.05
```

### AI / Compute Intents

```yaml
intent:ai_inference_local:
  dominant_component: GPU
  weights:
    vram_capacity:      0.45    # модель должна влезть в VRAM
    gpu_bandwidth_GBs:  0.20    # tokens/sec
    sys_ram_capacity:   0.15    # offload fallback
    cpu_multi_thread:   0.10    # prompt processing (может быть CPU)
    power_efficiency:   0.05
    acoustic_load:      0.05
  note: "VRAM = король. Модель не влезла → utility обрушивается."

intent:ai_training:
  dominant_component: GPU
  weights:
    vram_capacity:      0.30
    gpu_cuda_cores:     0.25
    gpu_bandwidth_GBs:  0.15
    sys_ram_capacity:   0.10
    psu_wattage:        0.10    # multi-GPU требует мощности
    thermal_margin:     0.10    # sustained 24/7 load
  note: "Multi-GPU training. Тепло и питание — ограничители."

intent:simulation:
  dominant_component: CPU
  weights:
    cpu_multi_thread:   0.40
    ram_capacity:       0.25
    ram_bandwidth:      0.15
    storage_latency:    0.10
    power_efficiency:   0.05
    thermal_margin:     0.05
  note: "CFD/FEA симуляции. CPU cores + RAM bandwidth."

intent:data_engineering:
  dominant_component: CPU
  weights:
    ram_capacity:       0.30
    cpu_multi_thread:   0.25
    storage_latency:    0.20
    ram_bandwidth:      0.10
    power_efficiency:   0.10
    acoustic_load:      0.05
  note: "Обработка данных — RAM объём и storage latency."
```

### Mixed / Specialized Intents

```yaml
intent:gaming_streaming:
  dominant_component: "CPU + GPU"
  weights:
    fps_1pct_low:       0.20
    cpu_multi_thread:   0.20    # OBS + игра
    gpu_encode_nvenc:   0.15    # аппаратный энкодер
    ram_capacity:       0.15    # OBS + браузер + игра
    fps_avg:            0.10
    vram_capacity:      0.10
    acoustic_load:      0.05
    thermal_margin:     0.05
  note: "Стриминг = gaming + content creation одновременно."

intent:gaming_creation:
  dominant_component: "GPU + CPU"
  weights:
    fps_avg:            0.20
    cpu_multi_thread:   0.20
    vram_capacity:      0.15
    fps_1pct_low:       0.15
    ram_capacity:       0.10
    gpu_raw:            0.10
    acoustic_load:      0.05
    upgrade_path:       0.05

intent:silent_build:
  dominant_component: Cooling
  weights:
    acoustic_idle:      0.35    # тишина = главная цель
    acoustic_load:      0.25
    thermal_margin:     0.15
    power_efficiency:   0.15    # меньше TDP = меньше шума
    fps_avg:            0.05    # производительность вторична
    vram_capacity:      0.05
  note: "Silent — utility function почти игнорирует производительность."

intent:compact_build:
  dominant_component: "Form Factor"
  weights:
    gpu_length_mm:      0.30    # физическая совместимость
    cooler_height_mm:   0.20
    thermal_margin:     0.20    # ITX = restricted airflow
    psu_form_factor:    0.10
    power_efficiency:   0.10
    fps_avg:            0.05
    acoustic_load:      0.05
  note: "Compact — физические ограничения доминируют над производительностью."

intent:energy_efficient:
  dominant_component: "PSU + GPU"
  weights:
    power_efficiency:   0.40
    thermal_margin:     0.20
    acoustic_load:      0.15
    fps_per_watt:       0.15
    vram_capacity:      0.05
    upgrade_path:       0.05
  note: "Эффективность = главная ось. Производительность на ватт."

intent:upgrade_friendly:
  dominant_component: Platform
  weights:
    upgrade_path:       0.35    # longevity платформы
    platform_lifetime:  0.25    # AM5 vs dead-end LGA1700
    cpu_multi_thread:   0.15    # стартовый CPU может быть слабее
    ram_capacity_now:   0.10    # можно докупить позже
    psu_headroom:       0.10    # запас для будущего GPU
    vram_capacity:      0.05
  note: "Сейчас — слабее, но платформа позволяет мощный апгрейд."
```

---

## Как LLM использует utility functions

```yaml
DecisionProcedure:
  step_1: "Загрузить utility function для intent из онтологии"
  step_2: "Для каждого candidate вычислить utility score по каждой метрике"
  step_3: "U(candidate) = Σ(w_i × score_i(candidate))"
  step_4: "Выбрать candidate с max U, если он проходит все BLOCK constraints"
  step_5: "В Decision указать: 'U(selected) = X, U(rejected_1) = Y'"

  utility_scoring:
    # LLM оценивает каждый candidate по шкале 0-1 для каждой метрики
    vram_capacity:
      "16GB → 1.0"
      "12GB → 0.8"
      "8GB  → 0.4"
      "6GB  → 0.1"

    acoustic_load:
      "A1_Ambient → 1.0"
      "A2_LowHum  → 0.7"
      "A3_Noticeable → 0.3"
      "A4_Loud      → 0.0"

    # LLM НЕ придумывает score — она оценивает candidate против метрики
    # Шкала и пороги определены в соответствующих L3 моделях
```

### Пример использования

```yaml
# Intent: ai_inference_local
# Candidates: RTX 4090 (24GB), RTX 3090 (24GB), RTX 4070 Ti (12GB)

utility_calculation:
  rtx_4090_24gb:
    vram_capacity:      { score: 1.0, weight: 0.45, contribution: 0.450 }
    gpu_bandwidth_GBs:  { score: 1.0, weight: 0.20, contribution: 0.200 }
    sys_ram_capacity:   { score: 0.8, weight: 0.15, contribution: 0.120 }
    cpu_multi_thread:   { score: 0.8, weight: 0.10, contribution: 0.080 }
    power_efficiency:   { score: 0.4, weight: 0.05, contribution: 0.020 }
    acoustic_load:      { score: 0.5, weight: 0.05, contribution: 0.025 }
    total: 0.895

  rtx_3090_24gb:
    vram_capacity:      { score: 1.0, weight: 0.45, contribution: 0.450 }
    gpu_bandwidth_GBs:  { score: 0.95, weight: 0.20, contribution: 0.190 }
    sys_ram_capacity:   { score: 0.8, weight: 0.15, contribution: 0.120 }
    cpu_multi_thread:   { score: 0.8, weight: 0.10, contribution: 0.080 }
    power_efficiency:   { score: 0.3, weight: 0.05, contribution: 0.015 }
    acoustic_load:      { score: 0.5, weight: 0.05, contribution: 0.025 }
    total: 0.880

  rtx_4070ti_12gb:
    vram_capacity:      { score: 0.4, weight: 0.45, contribution: 0.180 }  # КЛЮЧЕВОЕ
    gpu_bandwidth_GBs:  { score: 0.5, weight: 0.20, contribution: 0.100 }
    sys_ram_capacity:   { score: 0.8, weight: 0.15, contribution: 0.120 }
    cpu_multi_thread:   { score: 0.8, weight: 0.10, contribution: 0.080 }
    power_efficiency:   { score: 0.6, weight: 0.05, contribution: 0.030 }
    acoustic_load:      { score: 0.6, weight: 0.05, contribution: 0.030 }
    total: 0.540

  selected: RTX 4090 (U=0.895)
  rejected:
    - "RTX 3090: U=0.880. Сопоставим по VRAM, чуть хуже bandwidth и efficiency."
    - "RTX 4070 Ti: U=0.540. 12GB VRAM = фатально для 70B модели (offload penalty)."
```

---

## Контекстные модификаторы весов

MOD-CTX из L1 context могут сдвигать веса. Это **единственный** разрешённый механизм изменения весов — и он declarative, не LLM-driven:

```yaml
ContextModifiers:
  MOD-CTX-01:  # Высокая стоимость электричества
    condition: "context.electricity_cost_kwh > 0.20"
    action:
      - "power_efficiency *= 1.5"
      - "normalize all weights после модификации"

  MOD-CTX-02:  # Жаркий климат
    condition: "context.ambient_temp_celsius > 30"
    action:
      - "thermal_margin *= 1.5"
      - "normalize all weights"

  MOD-CTX-03:  # Строгое акустическое ограничение
    condition: "context.noise_constraint IN [strict, silent]"
    action:
      - "acoustic_load *= 2.0"
      - "acoustic_idle *= 2.0 (если присутствует)"
      - "normalize all weights"

  MOD-CTX-04:  # Низкий бюджет + длинный horizon
    condition: "context.budget_ceiling < 600 AND context.expected_lifespan_years >= 4"
    action:
      - "upgrade_path *= 2.0"
      - "normalize all weights"

  MOD-CTX-05:  # ITX
    condition: "context.form_factor = ITX"
    action:
      - "gpu_length_mm активируется как критерий (weight = 0.25)"
      - "cooler_height_mm активируется (weight = 0.20)"
      - "normalize all weights"
```

---

## Антипаттерны использования utility functions

### ANTI-UT-01 — LLM придумывает веса

```
ANTI-PATTERN: LLM пишет "VRAM важен → вес 0.4"
PROBLEM: LLM не должна назначать веса — они из онтологии.
CORRECT: "Веса из pcbo:ontology/L3_behavior/utility_functions#ai_inference_local: VRAM=0.45"
```

### ANTI-UT-02 — Игнорирование контекстного сдвига

```
ANTI-PATTERN: "Веса из онтологии: power_efficiency = 0.05"
PROBLEM: При стоимости электричества $0.40/кВт·ч вес должен быть выше.
CORRECT: "База: 0.05. MOD-CTX-01 (+50%): 0.075. После нормализации: 0.078."
```

### ANTI-UT-03 — Выбор без utility comparison

```
ANTI-PATTERN: "Выбираю RTX 4090 — лучшая карта"
PROBLEM: Нет численного сравнения utility scores.
CORRECT: "U(4090)=0.895, U(3090)=0.880, U(4070Ti)=0.540. Выбрана 4090."
```
