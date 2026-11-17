---
uri: "pcbo:ontology/L1_intent/intent"
type: "OntologyDocument"
layer: "L1"
version: "2.0.0"
relations:
  feedsInto: ["pcbo:ontology/L2_constraint", "pcbo:ontology/L3_performance"]
  usedBy: ["pcbo:reasoning/synthesis", "pcbo:system/goals"]
tags: ["intent", "goal", "use-case", "L1", "ontology"]
---

# L1 · Intent — целевая функция системы

> Intent отвечает не на вопрос "какой ПК", а на вопрос  
> "**для выполнения какой задачи** существует эта система".

Intent — не тип компьютера в бытовом смысле. Это формальная **целевая функция**,  
которая определяет, какие метрики релевантны, какие ограничения активны,  
и как интерпретировать каждый TradeOff.

---

## Таксономия Intent

```
BuildIntent
├── Gaming
│   ├── AAA_Gaming             ← максимальный FPS в тяжёлых играх
│   ├── Esports_Gaming         ← стабильный высокий FPS, низкий latency
│   ├── VR_Gaming              ← устойчивость фреймтайма, GPU-приоритет
│   └── Retro_Gaming           ← лёгкие нагрузки, компактность
│
├── Creative
│   ├── VideoEditing           ← CPU-cores, RAM, быстрый storage
│   ├── 3D_Rendering_CPU       ← максимальный multithread
│   ├── 3D_Rendering_GPU       ← GPU-cores, VRAM
│   ├── Music_Production       ← latency, storage IOPS
│   └── Photography            ← RAM, storage, CPU-burst
│
├── Compute
│   ├── AI_Inference_Local     ← VRAM, CUDA/ROCm
│   ├── AI_Training            ← GPU × N, power, NVLink
│   ├── Simulation             ← CPU-multithread, RAM
│   └── Data_Engineering       ← RAM, fast storage, CPU
│
├── Mixed
│   ├── Gaming_Streaming       ← GPU + CPU balance, NVENC
│   ├── Gaming_Creation        ← GPU-first + strong CPU
│   └── Office_Gaming          ← сбалансированная mid-tier
│
└── Specialized
    ├── Silent_Build            ← noise constraint = primary
    ├── Compact_Build           ← form factor = primary
    ├── Energy_Efficient        ← power draw = primary
    └── Upgrade_Friendly        ← platform longevity = primary
```

---

## Класс BuildIntent

```yaml
BuildIntent:
  id:             String            # URI-совместимый идентификатор
  label:          String            # человекочитаемое название
  primary_axis:   Axis              # главная ось оптимизации
  secondary_axes: [Axis]            # вторичные оси
  irrelevant:     [Axis]            # что явно не важно
  
  primary_component: ComponentClass # компонент-доминант
  upgrade_path_priority: Boolean    # важна ли долгосрочность платформы

Axis:
  fps_ceiling
  fps_stability         # frametime variance
  render_throughput
  encode_throughput
  memory_bandwidth
  storage_latency
  thermal_envelope
  acoustic_envelope
  power_efficiency
  platform_longevity
  vram_headroom
```

---

## Примеры Intent-инстанций

### `intent:aaa_gaming_1440p`

```yaml
id: "aaa_gaming_1440p"
label: "AAA Gaming 1440p"

primary_axis: fps_ceiling
secondary_axes: [fps_stability, vram_headroom, thermal_envelope]
irrelevant: [encode_throughput, render_throughput]

primary_component: GPU
upgrade_path_priority: true   # монитор 1440p живёт долго

performance_targets:
  fps_avg_min: 60
  fps_avg_target: 100
  fps_1pct_min: 45
  vram_safe_floor_GB: 10
  resolution: "2560×1440"

notes:
  - "При 1440p GPU важнее CPU чем при 1080p — больше пикселей снимают CPU bottleneck"
  - "DLSS/FSR меняют уравнение: mid-tier GPU + upscaling может обойти следующий тир"
```

### `intent:esports_240hz`

```yaml
id: "esports_240hz"
label: "Esports 240Hz"

primary_axis: fps_ceiling       # FPS должен стабильно превышать Hz монитора
secondary_axes: [fps_stability, storage_latency]
irrelevant: [vram_headroom, render_throughput, acoustic_envelope]

primary_component: CPU          # CS2/Valorant CPU-bound при 240+ FPS
upgrade_path_priority: false    # esports-игры не требуют апгрейда

performance_targets:
  fps_avg_min: 240
  fps_avg_target: 360
  fps_1pct_min: 200
  frametime_variance_ms_max: 1.5

notes:
  - "CPU-bottleneck при 240+ FPS более критичен чем при 60-144 FPS"
  - "RAM скорость влияет на FPS больше чем в AAA-сценарии"
  - "GPU tier: mid достаточно — RX 7600 / RTX 4060 для 1080p low"
```

### `intent:silent_build`

```yaml
id: "silent_build"
label: "Silent Build"

primary_axis: acoustic_envelope
secondary_axes: [thermal_envelope, power_efficiency]
irrelevant: []                  # silent всё ещё должен работать

primary_component: Cooling      # система охлаждения доминирует в выборе

constraints:
  dba_under_load_max: 35        # dB(A) на расстоянии 1м
  dba_idle_max: 25

notes:
  - "CPU TDP должен быть ограничен PL1 если стандартный TDP > 95W"
  - "Большие вентиляторы на малых оборотах тише маленьких на больших"
  - "Fanless PSU при мощности системы < 150W"
```

### `intent:video_editing_4k`

```yaml
id: "video_editing_4k"
label: "Video Editing 4K"

primary_axis: render_throughput
secondary_axes: [encode_throughput, storage_latency, memory_bandwidth]
irrelevant: [fps_ceiling, acoustic_envelope]

primary_component: CPU          # многопоточный рендер доминирует
secondary_component: RAM        # 32-64GB для комфортного монтажа
tertiary_component: Storage     # быстрый NVMe для media assets

performance_targets:
  export_4k_h265_realtime: true   # экспорт не медленнее реального времени
  ram_gb_min: 32
  ram_gb_target: 64
  storage_read_gbps_min: 3.5      # Gen4 NVMe

notes:
  - "GPU encoding (NVENC/QuickSync) кратно ускоряет экспорт"
  - "Для DaVinci Resolve GPU важнее чем для Premiere"
  - "HDD для архива OK, NVMe только для активного проекта"
```

---

## Матрица: Intent → Primary Component

| Intent | Доминант | Второй | Третий |
|---|---|---|---|
| AAA Gaming 1080p | GPU | CPU | Storage |
| AAA Gaming 1440p | GPU | VRAM | CPU |
| AAA Gaming 4K | GPU | VRAM | — |
| Esports 144Hz | CPU | GPU | RAM speed |
| Esports 240Hz | CPU | RAM | GPU |
| Video Editing | CPU (multi) | RAM | Storage |
| 3D Render CPU | CPU (multi) | RAM | — |
| 3D Render GPU | GPU (CUDA) | VRAM | — |
| AI Inference | GPU | VRAM | RAM |
| Gaming + Stream | CPU + GPU | NVENC | RAM |
| Silent Build | Cooling | CPU TDP | — |
| Compact Build | Form Factor | Cooling | PSU |
