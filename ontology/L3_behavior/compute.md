---
uri: "pcbo:ontology/L3_behavior/compute"
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
    Threshold values для tokens/sec и FPS являются инженерной оценкой.
    Не верифицированы инструментальными бенчмарками.
    VRAM→speed penalty model упрощена (0.1× при overflow).
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"         # Intent определяет релевантные compute outcomes
    - "pcbo:ontology/L4_decision/decision"      # GPU/CPU/RAM decisions определяют compute
  feedsInto:
    - "pcbo:ontology/L5_validation"             # compute thresholds проверяются при валидации
  seealso:
    - "pcbo:ontology/L3_behavior/power"         # compute load → power draw
    - "pcbo:ontology/L3_behavior/thermal"       # compute load → heat
tags: ["compute", "performance", "fps", "llm", "behavior", "L3", "physical-model"]
---

# L3 · Compute Model — вычислительная модель

> Уходим от бинарного «Тянет / Не тянет» к измеримым outcomes:
> tokens per second, 1% low FPS, encode throughput.
> Ответ не «да/нет», а «в каком режиме будет работать».

---

## Таксономия вычислительных outcomes

```
ComputeOutcomes
├── Gaming
│   ├── AAA_Gaming          ← 1% Low FPS + avg FPS
│   ├── Esports_Gaming      ← frametime consistency, input latency
│   └── VR_Gaming           ← frametime stability, reprojection ratio
│
├── Creative
│   ├── VideoEditing        ← encode throughput, timeline scrubbing
│   ├── 3D_Rendering        ← render time per frame
│   └── Photography         ← batch processing time
│
├── AI / Compute
│   ├── Local_LLM           ← tokens per second, interaction mode
│   ├── AI_Training         ← batches per second, VRAM utilisation
│   └── Simulation          ← solve time, RAM bandwidth
│
└── General
    ├── Code_Compilation    ← build time
    └── Data_Engineering    ← query throughput, RAM utilisation
```

---

## 1. Local LLM Inference

### Модель предсказания

```yaml
LLM_Inference:
  input:
    model_size_GB:        Float       # размер модели в VRAM (Q4_K_M квантизация)
    model_context_GB:     Float       # дополнительно под KV cache (±2GB на 8K контекст)
    gpu_vram_GB:          Integer     # VRAM видеокарты
    gpu_bandwidth_GBs:    Float       # пропускная способность памяти GPU
    system_ram_GB:        Integer     # системная RAM (для offload)

  calculation:
    fits_in_vram:         Boolean     # model_size ≤ gpu_vram_GB
    offload_required:     Boolean     # model_size > gpu_vram_GB

    tokens_per_second:
      fully_in_vram:      "gpu_bandwidth_GBs / model_size_GB × 0.7"
      partial_offload:    "gpu_bandwidth_GBs / model_size_GB × 0.1"
      note: "Частичный offload в RAM = ~10× медленнее"

  thresholds:
    interactive:       "> 15 t/s"     # чат в реальном времени
    reading_speed:     "5-15 t/s"     # читаем ответ как текст
    background_batch:  "< 5 t/s"      # пакетная обработка, не интерактивно

  interaction_mode:
    classification: Enum[interactive, reading_speed, background_batch]
```

### Threshold Matrix: Популярные модели

```yaml
LLM_ModelDB:
  # Параметры — оценка, не бенчмарк
  llama3_70b_q4:
    size_GB: 40
    min_vram_GB: 42
    bandwidth_per_token_GBs: 0.007

  llama3_8b_q4:
    size_GB: 5
    min_vram_GB: 6
    bandwidth_per_token_GBs: 0.0015

  mixtral_8x22b_q4:
    size_GB: 80
    min_vram_GB: 82
    bandwidth_per_token_GBs: 0.008

  qwen2_72b_q4:
    size_GB: 42
    min_vram_GB: 44
    bandwidth_per_token_GBs: 0.0075

  deepseek_v3_q4:
    size_GB: 370
    min_vram_GB: 380
    bandwidth_per_token_GBs: 0.012
    note: "MoE модель — часть весов в RAM, CPU offload практически обязателен"
```

### Пример симуляции

```yaml
# GPU: RTX 4090 (24GB VRAM, 1008 GB/s bandwidth)
# Model: llama3_70b_q4 (40GB)

llm_prediction:
  model: llama3_70b_q4
  model_size_GB: 40
  gpu_vram_GB: 24

  load:
    status: FAIL           # 40GB > 24GB — не помещается полностью
    offload_required: true

  inference:
    tokens_per_second:
      expected: "1.2-2.8"
      note: "Частичный offload в RAM (~16GB). Скорость памяти GPU / model × 0.1."
    bandwidth_bottleneck: "PCIe 4.0 x16 = 32 GB/s"

  interaction_mode:
    classification: reading_speed
    note: "Медленнее интерактивного, но читаемо. Не чат в реальном времени."

  alternative:
    recommendation: "RTX 3090 24GB даёт тот же результат. RTX A6000 48GB — модель влезает полностью."
```

---

## 2. AAA Gaming

### Модель предсказания

```yaml
AAA_Gaming:
  primary_metric: "1% Low FPS"
  secondary_metric: "Average FPS"
  tertiary_metric: "Frametime Variance (σ ms)"

  input:
    gpu_tier:             Tier         # T0 (90-class) … T4 (60-class)
    gpu_vram_GB:          Integer
    cpu_single_thread_score: Integer   # Cinebench 1T / PassMark ST
    cpu_thread_count:     Integer
    ram_capacity_GB:      Integer
    ram_bandwidth_GBs:    Float
    resolution:           Resolution
    settings_preset:      Enum[low, medium, high, ultra]

  thresholds:
    smooth:       "1% Low > 60 FPS"
    playable:     "1% Low 30-60 FPS"
    stutter_heavy: "1% Low < 30 FPS"

  calculation:
    # Оценка на основе GPU tier + разрешения (эвристика, не бенчмарк)
    fps_avg_estimated: >
      GPU tier baseline × resolution_modifier × settings_modifier
    fps_1pct_estimated: >
      fps_avg × (1.0 - cpu_bottleneck_factor - vram_pressure_factor)
    cpu_bottleneck_factor: >
      0.05-0.30 depending on CPU tier vs GPU tier mismatch
    vram_pressure_factor: >
      0.0 if vram_GB ≥ threshold else 0.15-0.40
```

### VRAM Threshold Matrix

```yaml
VRAM_Thresholds:
  1080p:
    low:      { safe: 6,  warning: 4 }
    medium:   { safe: 6,  warning: 5 }
    high:     { safe: 8,  warning: 6 }
    ultra:    { safe: 10, warning: 8 }

  1440p:
    low:      { safe: 8,  warning: 6 }
    medium:   { safe: 8,  warning: 6 }
    high:     { safe: 10, warning: 8 }
    ultra:    { safe: 12, warning: 10 }

  4K:
    low:      { safe: 10, warning: 8 }
    medium:   { safe: 12, warning: 10 }
    high:     { safe: 14, warning: 12 }
    ultra:    { safe: 16, warning: 14 }
```

### Пример симуляции

```yaml
# GPU: RTX 4070 (12GB), CPU: Ryzen 7800X3D, RAM: 32GB DDR5-6000
# Resolution: 1440p, Settings: high

aaa_gaming_prediction:
  resolution: "2560×1440"
  settings: high

  fps:
    avg_expected: "85-110"
    fps_1pct_expected: "55-70"
    mode: smooth

  bottleneck_analysis:
    cpu_bottleneck_factor: 0.05    # 7800X3D — топ CPU, минимальный bottleneck
    vram_pressure_factor:  0.05    # 12GB ≥ 10GB safe threshold
    gpu_limit_factor:      0.90    # GPU основной ограничитель (нормально для 1440p)

  vram_status:
    threshold_safe_GB: 10
    actual_GB: 12
    status: OK
    headroom_GB: 2
    note: "2GB headroom — достаточно для 2024, но к 2026 может быть на грани"
```

---

## 3. Esports Gaming

```yaml
Esports_Gaming:
  primary_metric: "1% Low FPS"      # важнее avg — стабильность критична
  secondary_metric: "Frametime σ ms"

  input:
    cpu_single_thread_score: Integer
    cpu_cache_L3_MB:        Integer  # X3D кэш даёт +15-25% в CS2/Valorant
    ram_latency_CL:         Integer
    ram_bandwidth_GBs:      Float
    gpu_tier:               Tier     # даже mid GPU даёт 300+ FPS в esports

  thresholds:
    competitive:
      fps_1pct_min: 240
      frametime_sigma_ms_max: 1.5
    serious:
      fps_1pct_min: 144
      frametime_sigma_ms_max: 3.0
    casual:
      fps_1pct_min: 60

  game_specific_factors:
    CS2:           { cpu_bound: 0.8, cache_sensitive: true }
    Valorant:      { cpu_bound: 0.7, cache_sensitive: true }
    Apex_Legends:  { cpu_bound: 0.5, gpu_impact: moderate }
    Dota2:         { cpu_bound: 0.6, cache_sensitive: false }
    LoL:           { cpu_bound: 0.4, gpu_impact: low }
```

---

## 4. Video Editing

```yaml
VideoEditing:
  primary_metric: "Export Time Ratio"
    # 1.0 = realtime (1 мин видео → 1 мин экспорта)
    # < 1.0 = быстрее realtime
    # > 1.0 = медленнее realtime

  input:
    cpu_cores:          Integer
    cpu_single_thread:  Integer
    ram_capacity_GB:    Integer
    gpu_nvenc_gen:      Integer    # NVENC generation для GPU encode
    storage_read_GBs:   Float

  thresholds:
    realtime_h265_4k:   "Export Time Ratio ≤ 1.0"
    realtime_h264_4k:   "Export Time Ratio ≤ 0.5"

  resolution_ram_requirements:
    1080p:  { min_ram_GB: 16, recommended_ram_GB: 32 }
    4K:     { min_ram_GB: 32, recommended_ram_GB: 64 }
    8K:     { min_ram_GB: 64, recommended_ram_GB: 128 }

  software_dependencies:
    davinci_resolve:  { gpu_focus: true,  vram_heavy: true }
    premiere_pro:     { cpu_focus: true,  quicksync: true }
    final_cut:        { apple_silicon: true }
```

---

## Симуляция вычислительного поведения

```yaml
ComputePrediction:
  # Для каждого релевантного workload — свой блок
  workloads:
    - workload_type: AAA_Gaming | LLM_Inference | VideoEditing | ...
      status: PASS | PASS_WITH_NOTES | FAIL
      primary_metric:
        expected: String       # "85-110 FPS" | "1.2-2.8 t/s"
        mode: String           # "smooth" | "reading_speed" | ...
      bottleneck: ComponentClass | null
      note: String

  overall_compute_fitness: Enum[EXCEEDS, MEETS, MARGINAL, FAILS]
```

### Полный пример

```yaml
compute_prediction:
  workloads:
    - type: AAA_Gaming_1440p
      status: PASS
      primary_metric:
        fps_avg_expected: "85-110"
        fps_1pct_expected: "55-70"
        mode: smooth
      bottleneck: GPU
      note: "GPU-limited at 1440p — норма. CPU имеет запас."

    - type: LLM_Inference
      status: PASS_WITH_NOTES
      model: llama3_70b_q4
      primary_metric:
        tokens_per_second: "1.2-2.8"
        mode: reading_speed
      bottleneck: VRAM
      note: "Модель не влезает в 12GB VRAM. RAM offload снижает скорость в 10×."

  overall_compute_fitness: MEETS
  # AAA gaming — отлично, LLM — работает но не интерактивно
```

---

## Взаимодействие с L5 Validation

```yaml
ComputeValidation:
  BLOCK_CHECKS:
    - condition: "fps_1pct_expected < fps_1pct_min"
      action: FAIL
      message: "1% Low FPS below minimum threshold for intent"

    - condition: "vram_GB < vram_threshold_safe AND intent = AAA_Gaming"
      action: FAIL
      message: "VRAM below safe threshold for target resolution"

  WARN_CHECKS:
    - condition: "llm_tokens_per_second < 15 AND intent INCLUDES AI_Inference"
      action: PASS_WITH_WARNINGS
      message: "LLM inference below interactive threshold"
      recommendation: "GPU with more VRAM or higher bandwidth"

    - condition: "vram_GB BETWEEN [vram_warning, vram_safe)"
      action: PASS_WITH_WARNINGS
      message: "VRAM на грани — достаточен сейчас, может стать узким местом через 1-2 года"
```

---

## Антипаттерны вычислительных утверждений

### ANTI-CP-01 — Бинарный вердикт

```
ANTI-PATTERN: "RTX 4070 тянет все игры"
PROBLEM: "Тянет" не имеет измеримого смысла.
CORRECT: "1440p high: 85-110 FPS avg, 55-70 FPS 1% low (smooth). 4K ultra: 45-60 FPS avg (playable)."
```

### ANTI-CP-02 — Игнорирование 1% Low

```
ANTI-PATTERN: "120 FPS в среднем — отлично"
PROBLEM: При 1% low = 25 FPS игра будет дёргаться несмотря на 120 avg.
CORRECT: "120 FPS avg, 55 FPS 1% low, frametime σ = 3.2ms — playable, не ideal."
```

### ANTI-CP-03 — LLM-модель без указания режима

```
ANTI-PATTERN: "70B модель работает"
PROBLEM: "Работает" = 0.5 t/s или 20 t/s?
CORRECT: "Llama 3 70B Q4: 1.2-2.8 t/s (reading speed). Для interactive нужен GPU с ≥ 48GB VRAM."
```
