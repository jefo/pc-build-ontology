---
uri: "pcbo:ontology/L1_intent/workload"
type: "OntologyDocument"
layer: "L1c"
version: "3.0.0-draft"
provenance:
  source: "LLM_ESTIMATE"
  model: "gemini-3.1-pro"
  date: "2026-06-02"
  confidence: "estimated"
  calibration_status: "none"
  note: >
    Профили нагрузки — синтетические сценарии, представляющие типичное
    использование для каждого Intent. Не калиброваны на телеметрии реальных
    пользователей. Параметры (часы в день, % нагрузки) — оценка.
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"         # Каждый workload привязан к Intent
  feedsInto:
    - "pcbo:ontology/L3_behavior/compute"      # Compute simulation
    - "pcbo:ontology/L3_behavior/power"        # Power simulation
    - "pcbo:ontology/L3_behavior/thermal"      # Thermal simulation
    - "pcbo:ontology/L4_decision/decision"      # Decision Chain зависит от primary workload
  seealso:
    - "pcbo:ontology/L1_intent/context"        # Context модифицирует workload
tags: ["workload", "profile", "benchmark", "simulation-input", "L1c"]
---

# L1c · Workload Profiles — профили нагрузки

> Workload — это не Intent (зачем), а конкретная нагрузка, с помощью которой
> мы симулируем поведение системы. Одна сборка может обслуживать несколько
> workload profiles — но primary workload определяет Decision Chain.

---

## Класс WorkloadProfile

```yaml
WorkloadProfile:
  id:               String
  label:            String
  intent_ref:       URI              # к какому Intent привязан
  description:      String           # что делает пользователь

  # Параметры симуляции
  duration_hours_per_day: Float      # сколько часов в день эта нагрузка
  intensity:         Enum[burst, intermittent, sustained, continuous]

  # Распределение нагрузки по компонентам
  component_load:
    cpu_load_pct:        Float       # % от TDP
    cpu_threads_used:    Integer     # сколько ядер активно
    gpu_load_pct:        Float       # % от TGP
    vram_usage_GB:       Float       # ожидаемое потребление VRAM
    ram_usage_GB:        Float       # ожидаемое потребление RAM
    storage_read_MBs:    Float       # чтение с накопителя
    storage_write_MBs:   Float       # запись

  # Метрики успеха для этого workload
  success_metrics:
    primary_metric:     String       # "fps_1pct_low" | "tokens_per_sec" | "export_time_ratio"
    target_value:       Float
    minimum_value:      Float
```

---

## Каталог Workload Profiles

### Gaming Workloads

```yaml
workload:aaa_1440p_ultra:
  intent_ref: "aaa_gaming_1440p"
  description: "AAA игра на 1440p ultra settings (Cyberpunk 2077, Alan Wake 2)"
  duration_hours_per_day: 3
  intensity: sustained

  component_load:
    cpu_load_pct: 0.50          # Игры не нагружают все ядра
    cpu_threads_used: 6
    gpu_load_pct: 0.95
    vram_usage_GB: 10
    ram_usage_GB: 16
    storage_read_MBs: 50        # Подгрузка ассетов

  success_metrics:
    primary_metric: "fps_1pct_low"
    target_value: 60
    minimum_value: 45

workload:aaa_4k_high:
  intent_ref: "aaa_gaming_4k"
  description: "AAA игра на 4K high settings"
  duration_hours_per_day: 3
  intensity: sustained

  component_load:
    cpu_load_pct: 0.35          # 4K — GPU bound, CPU почти не нужен
    cpu_threads_used: 4
    gpu_load_pct: 0.98
    vram_usage_GB: 14
    ram_usage_GB: 16
    storage_read_MBs: 50

  success_metrics:
    primary_metric: "fps_1pct_low"
    target_value: 60
    minimum_value: 40           # 4K — ниже порог

workload:esports_competitive:
  intent_ref: "esports_240hz"
  description: "CS2/Valorant competitive settings (1080p low)"
  duration_hours_per_day: 4
  intensity: sustained

  component_load:
    cpu_load_pct: 0.65          # CPU-bound при 1080p low
    cpu_threads_used: 4         # esports используют мало ядер
    gpu_load_pct: 0.60          # low settings = низкая нагрузка GPU
    vram_usage_GB: 4
    ram_usage_GB: 10
    storage_read_MBs: 10

  success_metrics:
    primary_metric: "fps_1pct_low"
    target_value: 240
    minimum_value: 200
    secondary_metric: "frametime_sigma_ms"
    secondary_target: 1.5
```

### Creative Workloads

```yaml
workload:video_editing_4k_export:
  intent_ref: "video_editing_4k"
  description: "Экспорт 4K H.265 10-минутного проекта в DaVinci Resolve"
  duration_hours_per_day: 0.5       # burst workload
  intensity: burst

  component_load:
    cpu_load_pct: 0.95
    cpu_threads_used: 16
    gpu_load_pct: 0.80              # CUDA encode
    vram_usage_GB: 8
    ram_usage_GB: 40                # 4K timeline + plugins
    storage_read_MBs: 500           # Чтение media files
    storage_write_MBs: 100

  success_metrics:
    primary_metric: "export_time_ratio"
    target_value: 1.0               # 1× realtime
    minimum_value: 1.5

workload:video_editing_4k_scrubbing:
  intent_ref: "video_editing_4k"
  description: "Timeline scrubbing 4K 10-bit 4:2:2 без proxy"
  duration_hours_per_day: 4
  intensity: intermittent

  component_load:
    cpu_load_pct: 0.40
    cpu_threads_used: 8
    gpu_load_pct: 0.50              # Декодирование 4:2:2
    vram_usage_GB: 6
    ram_usage_GB: 32
    storage_read_MBs: 300

  success_metrics:
    primary_metric: "timeline_dropped_frames"
    target_value: 0
    minimum_value: 5                # 5 dropped frames / час допустимо

workload:3d_render_gpu:
  intent_ref: "3d_rendering_gpu"
  description: "Рендер 4K кадра в Blender Cycles GPU"
  duration_hours_per_day: 2
  intensity: continuous

  component_load:
    cpu_load_pct: 0.30              # Подготовка сцены
    cpu_threads_used: 4
    gpu_load_pct: 1.0               # 100% compute
    vram_usage_GB: 16               # Тяжёлые сцены
    ram_usage_GB: 32                # Системная RAM для сцены
    storage_read_MBs: 100

  success_metrics:
    primary_metric: "render_time_per_frame_seconds"
    target_value: 120               # 2 минуты на кадр
    minimum_value: 300

workload:music_production_mixing:
  intent_ref: "music_production"
  description: "Сведение 48-канального проекта с плагинами"
  duration_hours_per_day: 6
  intensity: sustained

  component_load:
    cpu_load_pct: 0.60
    cpu_threads_used: 8
    gpu_load_pct: 0.05              # Аудио не использует GPU
    ram_usage_GB: 24                # Семплы + плагины
    storage_read_MBs: 50            # Чтение семплов

  success_metrics:
    primary_metric: "audio_latency_ms"
    target_value: 5                 # buffer 128 @ 48kHz
    minimum_value: 10

workload:music_production_live_monitoring:
  intent_ref: "daw_zero_dpc_latency"
  description: "Живой мониторинг через DAW с плагинами на буфере 32-64 сэмпла (Cubase, Pro Tools)"
  duration_hours_per_day: 2
  intensity: burst                  # Запись дублями

  component_load:
    cpu_load_pct: 0.40              # Легче, чем микс, но требует низкой латентности
    cpu_threads_used: 4             # Живой мониторинг — преимущественно single-thread
    gpu_load_pct: 0.0               # iGPU не участвует в аудио
    ram_usage_GB: 16                # Меньше семплов, чем при сведении
    storage_read_MBs: 100           # Чтение мультитрека (16-24 канала записи)

  success_metrics:
    primary_metric: "dpc_latency_us"
    target_value: 50                # DPC <50 μs для гарантии отсутствия дропаутов
    minimum_value: 100
    secondary_metric: "audio_latency_ms"
    secondary_target: 3             # Buffer 64 @ 48kHz = 1.33ms + driver RTT
    secondary_minimum: 5

workload:music_production_orchestral:
  intent_ref: "daw_zero_dpc_latency"
  description: "Оркестровый проект: 150+ треков Kontakt, Spitfire, Omnisphere, FX на каждом канале"
  duration_hours_per_day: 6
  intensity: sustained

  component_load:
    cpu_load_pct: 0.85              # Множество VST-инстансов, высокая polyphony
    cpu_threads_used: 12            # Kontakt и плагины хорошо масштабируются по ядрам
    gpu_load_pct: 0.0               # iGPU
    ram_usage_GB: 48                # Spitfire Symphony Orchestra ≈ 800GB (стриминг 48GB active)
    storage_read_MBs: 500           # DFD-стриминг (Direct From Disk) — множество голосов

  success_metrics:
    primary_metric: "polyphony_voices"
    target_value: 500               # 500 голосов без дропаутов
    minimum_value: 200
    secondary_metric: "dpc_latency_us"
    secondary_target: 50
    secondary_minimum: 100
```

### AI / Compute Workloads

```yaml
workload:llm_inference_70b:
  intent_ref: "ai_inference_local"
  description: "Инференс Llama 3 70B Q4_K_M с контекстом 8K"
  duration_hours_per_day: 4
  intensity: intermittent

  component_load:
    cpu_load_pct: 0.15
    cpu_threads_used: 4
    gpu_load_pct: 1.0               # 100% compute
    vram_usage_GB: 42               # Модель + KV cache
    ram_usage_GB: 48                # Остаток модели при offload
    storage_read_MBs: 0             # Модель уже в RAM/VRAM

  success_metrics:
    primary_metric: "tokens_per_second"
    target_value: 15                # interactive
    minimum_value: 5                # reading speed

workload:llm_inference_8b:
  intent_ref: "ai_inference_local"
  description: "Инференс Llama 3 8B Q4_K_M — лёгкая модель"
  duration_hours_per_day: 8
  intensity: intermittent

  component_load:
    cpu_load_pct: 0.10
    gpu_load_pct: 1.0
    vram_usage_GB: 6                # 5GB модель + 1GB KV cache
    ram_usage_GB: 16
    storage_read_MBs: 0

  success_metrics:
    primary_metric: "tokens_per_second"
    target_value: 30
    minimum_value: 15

workload:data_engineering_spark:
  intent_ref: "data_engineering"
  description: "Обработка датасета 500GB в Spark локально"
  duration_hours_per_day: 2
  intensity: burst

  component_load:
    cpu_load_pct: 0.90
    cpu_threads_used: 16
    gpu_load_pct: 0
    ram_usage_GB: 64                # Spark executors
    storage_read_MBs: 1000
    storage_write_MBs: 500

  success_metrics:
    primary_metric: "query_completion_time_minutes"
    target_value: 30
    minimum_value: 60
```

### Mixed Workloads

```yaml
workload:gaming_streaming:
  intent_ref: "gaming_streaming"
  description: "AAA игра + OBS стрим 1080p60 NVENC + Discord + 20 вкладок браузера"
  duration_hours_per_day: 4
  intensity: sustained

  component_load:
    cpu_load_pct: 0.70              # Игра + OBS + фоновые задачи
    cpu_threads_used: 12
    gpu_load_pct: 0.90              # Игра + NVENC encode
    vram_usage_GB: 10
    ram_usage_GB: 28                # Игра (16) + OBS (2) + браузер (6) + Discord (2)
    storage_read_MBs: 50

  success_metrics:
    primary_metric: "fps_1pct_low"
    target_value: 60
    minimum_value: 45
    secondary_metric: "stream_dropped_frames_pct"
    secondary_target: 0.1
```

### General Workloads

```yaml
workload:office_productivity:
  intent_ref: "office_gaming"
  description: "Офисные приложения, браузер, видеоконференции"
  duration_hours_per_day: 8
  intensity: intermittent

  component_load:
    cpu_load_pct: 0.20
    cpu_threads_used: 4
    gpu_load_pct: 0.10              # Видео декодинг
    vram_usage_GB: 2
    ram_usage_GB: 12
    storage_read_MBs: 20

  success_metrics:
    primary_metric: "responsiveness"
    target_value: "no_lag"
    minimum_value: "occasional_lag_acceptable"

workload:idle:
  intent_ref: "*"                   # Все Intent
  description: "Система включена, рабочий стол, без активных задач"
  duration_hours_per_day: 10
  intensity: idle

  component_load:
    cpu_load_pct: 0.05
    gpu_load_pct: 0.03
    vram_usage_GB: 1
    ram_usage_GB: 6
    storage_read_MBs: 5

  success_metrics:
    primary_metric: "power_W"
    target_value: 60
    minimum_value: 100
```

---

## Workload × Intent Matrix

Какие workload profiles актуальны для каждого Intent:

```yaml
WorkloadIntentMatrix:
  aaa_gaming_1440p:
    primary:   [aaa_1440p_ultra]
    secondary: [idle, office_productivity]
    irrelevant: [llm_inference, video_editing]

  esports_240hz:
    primary:   [esports_competitive]
    secondary: [idle, office_productivity]

  video_editing_4k:
    primary:   [video_editing_4k_export, video_editing_4k_scrubbing]
    secondary: [idle]

  ai_inference_local:
    primary:   [llm_inference_70b, llm_inference_8b]
    secondary: [idle]

  gaming_streaming:
    primary:   [gaming_streaming]
    secondary: [idle, office_productivity]

  music_production:
    primary:   [music_production_mixing]
    secondary: [idle]
    note: "Устаревший интент. Заменён на daw_zero_dpc_latency."

  daw_zero_dpc_latency:
    primary:   [music_production_orchestral, music_production_live_monitoring]
    secondary: [music_production_mixing, idle]

  silent_build:
    primary:   [idle]                            # Шум в idle — главный критерий
    secondary: [office_productivity]
    note: "Silent build не предъявляет требований к compute"
```

---

## Использование Workload в симуляции

```yaml
SimulationInput:
  # L3 симуляция запускается для primary workload + idle
  workloads_to_simulate:
    - "primary_workload (из Intent)"
    - "idle (всегда)"

  # Если primary workload PASS, симулируются secondary
  if_primary_pass:
    - "secondary_workloads"

  # Параметры передаются в L3 модели:
  compute:
    input: "{workload.component_load + success_metrics}"
  power:
    input: "{workload.component_load.cpu_load_pct, gpu_load_pct}"
  thermal:
    input: "{workload.component_load + ambient_C}"
  acoustic:
    input: "{power_prediction + cooling_type}"
  latency:
    input: "{workload.component_load + success_metrics если latency-релевантно}"
```
