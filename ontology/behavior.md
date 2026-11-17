---
uri: "pcbo:ontology/L3_performance/behavior"
type: "OntologyDocument"
layer: "L3"
version: "3.0.0-draft"
role: "TAXONOMY_OVERVIEW"
relations:
  details: ["pcbo:ontology/L3_behavior/acoustic", "pcbo:ontology/L3_behavior/thermal",
            "pcbo:ontology/L3_behavior/compute", "pcbo:ontology/L3_behavior/power",
            "pcbo:ontology/L3_behavior/latency", "pcbo:ontology/L3_behavior/reliability",
            "pcbo:ontology/L3_behavior/utility_functions"]
  usedBy: ["pcbo:ontology/L4_decision/risk", "pcbo:reasoning/synthesis"]
tags: ["behavior", "bottleneck", "throttling", "system-dynamics", "taxonomy", "L3"]
---

# L3 · SystemBehavior — таксономия системного поведения

> **Роль этого документа**: обзорная карта (taxonomy overview) концепций системного поведения.  
> **Детальные модели** — в `L3_behavior/` (acoustic, thermal, compute, power, latency, reliability, utility_functions).  
> Этот документ определяет *какие бывают* поведения; `L3_behavior/*` определяет *как их считать*.

Хорошая сборка — это не просто совместимая сборка.  
Это сборка, которая **ведёт себя нужным образом** в реальной нагрузке.

Поведенческие концепции — это то, что происходит *между* компонентами  
в динамике реальной работы. Их нельзя вычислить из спецификаций статически.

---

## Таксономия системного поведения

```
SystemBehavior
│
├── ResourceContention         ← конкуренция за общий ресурс
│   ├── CPU_Bottleneck         ← GPU простаивает, ждёт кадры от CPU
│   ├── GPU_Bottleneck         ← CPU простаивает, GPU не успевает
│   ├── VRAM_Pressure          ← GPU спилловер в системную RAM
│   ├── RAM_Pressure           ← свопинг на диск
│   └── Storage_Queue_Depth    ← I/O очередь насыщена
│
├── ThermalBehavior            ← влияние температуры
│   ├── ThermalThrottling      ← снижение частоты при перегреве
│   ├── ThermalSoak            ← деградация после длительной нагрузки
│   └── AmbientTemperatureEffect ← влияние окружающей среды
│
├── PowerBehavior              ← поведение под нагрузкой по питанию
│   ├── PowerLimiting          ← PL1/PL2 ограничение у Intel
│   ├── PSU_Instability        ← нестабильность при пиковой нагрузке
│   └── PowerSpike             ← мгновенные пики (GPU load step)
│
├── FrametimeBehavior          ← качество рендеринга во времени
│   ├── FrametimeVariance      ← джиттер, неравномерность FPS
│   ├── MicrostutterPattern    ← регулярные микрозависания
│   └── BackgroundContention   ← фоновые задачи мешают игре
│
└── LatencyBehavior            ← задержки в системе
    ├── InputLatency           ← мышь/клавиатура → экран
    ├── StorageLatency         ← время загрузки ассетов
    └── RAMLatency             ← влияние CL на отдельные workloads
```

---

## Поведенческие концепции в деталях

### CPU_Bottleneck

```
CONCEPT: CPU_Bottleneck

DEFINITION:
  GPU простаивает (GPU utilization < 95%) потому что CPU
  не успевает подготовить draw calls / игровую логику.
  
SYMPTOM: GPU% < 95, CPU% ≈ 100 на одном/нескольких ядрах

MEASUREMENT:
  BI (Bottleneck Index) = max(0, cpu_frame_time - gpu_frame_time) / gpu_frame_time × 100

RESOLUTION_DEPENDENCY:
  CPU bottleneck = f(resolution)⁻¹
  На 4K GPU берёт намного больше времени → CPU bottleneck исчезает
  На 1080p CPU важнее чем на 1440p/4K

GAME_SENSITIVITY:
  high:   ["CS2", "Valorant", "Escape from Tarkov", "MSFS 2024"]
  medium: ["Cyberpunk 2077", "Hogwarts Legacy"]
  low:    ["Red Dead Redemption 2", "God of War"]

TRIGGER_IN_DECISION:
  IF cpu.tier < gpu.tier - 1 AND resolution = "1080p"
  → RAISE CPU_Bottleneck risk WITH severity = MEDIUM|HIGH
```

### VRAM_Pressure

```
CONCEPT: VRAM_Pressure

DEFINITION:
  Видеопамять GPU насыщена. GPU начинает спилловать текстуры в системную RAM
  через PCIe — что в 10-30× медленнее. Результат: stutters, texture pop-in.

CRITICAL INSIGHT:
  VRAM-ceiling — жёсткий предел. Нельзя "компенсировать" разгоном или настройками
  (кроме снижения качества текстур / разрешения).

THRESHOLD_MATRIX:
  resolution="1080p", settings="ultra" → pressure_zone = 6-8GB
  resolution="1440p", settings="ultra" → pressure_zone = 8-10GB
  resolution="4K",    settings="high"  → pressure_zone = 10-12GB

SOFT_CEILING_EFFECT:
  При pressured VRAM: FPS не падает линейно — происходят резкие stutters
  при подгрузке новых текстур в сценах с большим asset diversity.

UPSCALING_MITIGATION:
  DLSS/FSR снижают рабочее разрешение → меньше VRAM на framebuffer
  НО текстуры всё равно загружаются в нативном разрешении → VRAM не освобождается
```

### ThermalThrottling

```
CONCEPT: ThermalThrottling

DEFINITION:
  CPU/GPU снижает тактовую частоту при достижении T_junction_max
  для предотвращения повреждения.

EFFECT:
  Производительность деградирует нелинейно:
  - При throttle 10%: -10% производительность (линейно)
  - При throttle 30%: -20-35% (нелинейно из-за pipeline stall)
  
AMBIENT_INTERACTION:
  T_effective = T_junction - T_ambient
  При ambient = 35°C: koolering margin уменьшается на ~15°C
  → 250W CPU в 35°C требует AIO 360mm где при 22°C хватало 240mm

TRIGGER_IN_DECISION:
  IF cpu.tdp_W > 150 AND cooler.type = "Air_120mm"
  → RAISE ThermalThrottling risk WITH severity = HIGH

  IF context.ambient_temp > 30
  → UPGRADE cooler recommendation BY one tier
```

### FrametimeVariance (1% Low)

```
CONCEPT: FrametimeVariance

DEFINITION:
  Неравномерность времени рендеринга кадров.
  Более важна для субъективного качества, чем средний FPS.

METRICS:
  frametimeσ     = стандартное отклонение frametime в мс
  fps_1pct       = FPS в нижних 1% (минимальный комфорт)
  fps_01pct      = FPS в нижних 0.1% (абсолютные минимумы)

SUBJECTIVE_IMPACT:
  avg=120 FPS, σ=2ms → плавно, комфортно
  avg=120 FPS, σ=8ms → заметные рывки, дискомфорт
  
CAUSES:
  - CPU bottleneck (нерегулярная поставка кадров GPU)
  - RAM bandwidth saturation
  - Background process interference
  - VRAM spilling
  - Driver overhead (relevant для DX11 игр)

TRIGGER_IN_DECISION:
  IF intent = Esports_Gaming
  → fps_1pct_target BECOMES primary metric (важнее avg FPS)
  
  IF ram.channels = 1
  → WARN "Single-channel RAM увеличивает frametime variance на 15-25%"
```

### BackgroundContention

```
CONCEPT: BackgroundContention

DEFINITION:
  Фоновые задачи (OBS, браузер, антивирус, Discord) конкурируют
  за CPU/RAM с основной задачей.

QUANTIFIED_IMPACT:
  OBS software encode (x264 slow):  -15-25% FPS
  OBS hardware encode (NVENC):      -2-5% FPS
  Discord + browser (20 вкладок):   -3-8% FPS, +2-4GB RAM

MITIGATION:
  - NVENC вместо CPU-encode: CPU освобождается
  - 32GB RAM вместо 16GB: устраняет memory pressure при многозадачности
  - CPU с 12+ потоками: фоновые задачи уходят на отдельные ядра

TRIGGER_IN_DECISION:
  IF intent = Gaming_Streaming
  → ACTIVATE BackgroundContention risk
  → RECOMMEND cpu.threadCount >= 12
  → RECOMMEND gpu.nvenc_gen >= 7 (Ada Lovelace NVENC)
```

---

## Матрица поведений × Intent

| Поведение | AAA 1080p | Esports 240 | Video Edit | Gaming+Stream |
|---|---|---|---|---|
| CPU_Bottleneck | Высокий риск | Критичен | Низкий | Средний |
| VRAM_Pressure | Средний | Низкий | Средний | Средний |
| ThermalThrottling | Средний | Низкий | Высокий | Высокий |
| FrametimeVariance | Средний | Критична | Нерелевантна | Средний |
| BackgroundContention | Низкий | Средний | Низкий | Критична |
| RAM_Pressure | Низкий | Низкий | Высокий | Средний |

---

## Связь с Decision Layer

Каждое поведение может стать `Risk` в Decision:

```yaml
Risk:
  behavior:   "VRAM_Pressure"
  trigger:    "gpu.vram_GB < threshold(resolution, settings)"
  severity:   HIGH
  probability: 0.85   # если threshold нарушен
  mitigation:
    - "Снизить настройки текстур"
    - "Включить DLSS/FSR"
    - "Upgrade GPU tier"
  residual_risk: "Stutters в asset-heavy сценах возможны даже с DLSS"
```
