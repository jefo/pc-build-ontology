---
uri: "pcbo:ontology/L3_behavior/latency"
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
    Latency thresholds (input < 4.2ms, audio < 10ms, etc.) — инженерная оценка.
    Не верифицированы инструментальными замерами (LDAT, ASIO loopback).
    severity: warning
relations:
  uses:
    - "pcbo:ontology/L1_intent/intent"         # esports / music_production — latency-critical
    - "pcbo:ontology/L4_decision/decision"      # cpu, ram, storage decisions
  feedsInto:
    - "pcbo:ontology/L5_validation"             # latency thresholds проверяются
    - "pcbo:ontology/L3_behavior/compute"       # latency affects compute outcomes (frametime)
  seealso:
    - "pcbo:ontology/L3_behavior/thermal"       # throttling → latency spikes
tags: ["latency", "input-lag", "audio", "storage", "behavior", "L3", "physical-model"]
---

# L3 · Latency Model — модель задержек

> Критично для esports, стриминга, аудио-продакшена.
> Разные виды задержек имеют разных «владельцев» среди компонентов.

---

## Таксономия задержек

```yaml
LatencyClasses:
  InputLatency:
    label: "End-to-end input latency"
    path: "Мышь/клавиатура → CPU → GPU → дисплей"
    unit: "ms"
    owners: [CPU, GPU, RAM, Monitor]
    critical_for: [esports_gaming, vr_gaming]

  RenderLatency:
    label: "Frame time"
    path: "CPU (draw calls) → GPU (render) → display"
    unit: "ms"
    owners: [CPU, GPU]
    critical_for: [esports_gaming, aaa_gaming]

  AudioLatency:
    label: "Audio buffer latency"
    path: "Аудио-интерфейс → CPU → плагины → выход"
    unit: "ms (при заданном buffer size)"
    owners: [CPU, Audio_Interface, RAM]
    critical_for: [music_production, streaming]

  StorageLatency:
    label: "Storage access latency"
    path: "Приложение → OS → файловая система → NVMe"
    unit: "µs (4K random read)"
    owners: [Storage, CPU, Chipset]
    critical_for: [video_editing, data_engineering]

  RAMLatency:
    label: "Memory access latency"
    path: "CPU → IMC → DRAM"
    unit: "ns (CAS latency in clock cycles)"
    owners: [RAM, CPU_IMC]
    critical_for: [esports_gaming, simulation, data_engineering]

  NetworkLatency:
    label: "Network round-trip"
    path: "Игровой клиент → сервер → клиент"
    unit: "ms (ping)"
    owners: [Network_Adapter, ISP]
    critical_for: [esports_gaming, streaming]
    note: "Вне зоны контроля PCBO. Упоминается для полноты."
```

---

## 1. Input Latency

```yaml
InputLatency:
  definition: "Время от физического действия (клик) до визуального результата на экране."

  components:
    mouse_latency_ms:    "1-8ms (зависит от polling rate: 1000Hz = 1ms, 125Hz = 8ms)"
    cpu_pipeline_ms:     "2-5ms (обработка ввода + game logic + draw calls)"
    gpu_render_ms:       "frame_time_ms (зависит от FPS: 60 FPS = 16.7ms, 240 FPS = 4.2ms)"
    display_latency_ms:  "1-15ms (OLED: 1-3ms, IPS: 4-8ms, VA: 8-15ms)"

  total_ms: "mouse + cpu_pipeline + gpu_render + display"

  thresholds:
    competitive_pro:    "< 20ms total"
    competitive_serious: "< 30ms total"
    casual:             "< 50ms total"

  reduction_strategies:
    - "Высокий FPS (240+) снижает gpu_render до 4.2ms"
    - "Reflex / Anti-Lag снижает cpu_pipeline на 30-50%"
    - "OLED монитор снижает display до 1-3ms"
    - "1000Hz+ мышь (Razer 8K / Viper) снижает mouse до 0.125ms"

  # Что PCBO может контролировать
  controllable_by_PCBO: [cpu_pipeline_ms, gpu_render_ms]
```

---

## 2. Render Latency (Frametime)

```yaml
RenderLatency:
  definition: "Время рендеринга одного кадра."
  formula: "frametime_ms = 1000 / fps"

  thresholds:
    esports_competitive:
      frametime_ms_max: 4.2      # 240 FPS
      frametime_sigma_ms_max: 1.5
    esports_serious:
      frametime_ms_max: 6.9      # 144 FPS
      frametime_sigma_ms_max: 3.0
    aaa_comfortable:
      frametime_ms_max: 16.7     # 60 FPS
      frametime_sigma_ms_max: 5.0

  frametime_variance_causes:
    cpu_bottleneck:       "Нерегулярная поставка draw calls → джиттер"
    ram_bandwidth:        "Недостаточная пропускная способность → задержки"
    vram_spilling:        "Текстуры в RAM → stutter при подгрузке"
    background_contention: "OBS/Discord прерывают рендеринг"
    shader_compilation:   "Stutter при первой загрузке шейдеров (Unreal Engine)"

  mitigation:
    - "Reflex / Anti-Lag 2: снижает render queue, выравнивает frametime"
    - "G-Sync / FreeSync: маскирует небольшие колебания frametime"
    - "Dual-channel RAM: снижает frametime σ на 15-25% vs single-channel"
    - "Shader pre-compilation: исключает compilation stutter"
```

---

## 3. Audio Latency

```yaml
AudioLatency:
  definition: "Задержка между аудио-сигналом и его обработкой/воспроизведением."
  unit: "ms при заданном buffer size и sample rate"

  formula: >
    audio_latency_ms = (buffer_size / sample_rate_Hz) × 1000 × 2
    (×2 для round-trip: input → обработка → output)

  examples:
    buffer_64_44khz:    "2.9ms"
    buffer_128_44khz:   "5.8ms"
    buffer_256_44khz:   "11.6ms"
    buffer_512_44khz:   "23.2ms"

  thresholds:
    live_monitoring:    "< 5ms (buffer ≤ 128 @ 48kHz)"
    recording:          "< 10ms (buffer ≤ 256 @ 48kHz)"
    mixing:             "< 20ms (buffer ≤ 512 @ 48kHz)"

  drivers:
    ASIO:               "Профессиональный стандарт. Прямой доступ к hardware. ~2-5ms."
    WASAPI_Exclusive:   "Windows low-latency. ~5-10ms."
    WASAPI_Shared:      "С микшером Windows. ~10-30ms."
    CoreAudio:          "macOS. ~2-5ms нативно."

  pcbo_contribution:
    cpu_single_thread:  "Обработка плагинов — per-core"
    ram_latency:        "Доступ к семплам в RAM"
    dpc_latency:        "Deferred Procedure Call latency (Windows) — драйверы"
    recommendation: >
      Для music_production: CPU с высоким single-thread + низкая DPC latency.
      Избегать материнских плат с известными DPC-проблемами.
```

---

## 4. Storage Latency

```yaml
StorageLatency:
  definition: "Время доступа к данным на накопителе."
  primary_metric: "4K Random Read QD1 (µs)"

  thresholds:
    NVMe_Gen5:  "30-50 µs"
    NVMe_Gen4:  "40-70 µs"
    NVMe_Gen3:  "60-100 µs"
    SATA_SSD:   "100-200 µs"
    HDD:        "5-15 ms"

  impact_on_workloads:
    video_editing_4k:
      requirement: "NVMe Gen4 (sequential read ≥ 3.5 GB/s)"
      reason: "Проигрывание 4K 10-bit 4:2:2 без proxy"
    large_dataset:
      requirement: "NVMe Gen4/Gen5 (4K random read QD1 < 60 µs)"
      reason: "Поиск по миллионам файлов / записей БД"
    gaming:
      requirement: "NVMe Gen3 достаточен"
      reason: "DirectStorage уменьшает задержки, но разница Gen3/Gen4 < 1с загрузки"

  # L5 BLOCK если storage не соответствует Intent
  StorageValidation:
    video_editing_4k: "NVMe Gen4 MINIMUM. SATA SSD → FAIL."
    general_use: "SATA SSD MINIMUM. HDD для OS → FAIL."
```

---

## Симуляция latency поведения

```yaml
LatencyPrediction:
  relevant_for: [esports_240hz | music_production | video_editing | null]

  input_latency_ms:
    expected: Integer
    breakdown: { mouse, cpu_pipeline, gpu_render, display }
    classification: competitive_pro | serious | casual

  render_frametime_ms:
    avg: Float
    sigma_ms: Float
    classification: competitive | serious | comfortable

  audio_latency_ms:
    expected_at_buffer_64: Float
    expected_at_buffer_256: Float
    driver: ASIO | WASAPI | CoreAudio

  storage_latency_us:
    expected_4k_random_read: Integer
    meets_intent_requirements: Boolean
```

### Пример

```yaml
# Система: Ryzen 7800X3D + RTX 4070 + NVMe Gen4 + DDR5-6000 CL30
# Intent: esports_240hz

latency_prediction:
  relevant_for: esports_240hz

  input_latency:
    total_ms: 18
    breakdown:
      mouse: 1ms (1000Hz)
      cpu_pipeline: 3ms (Reflex ON)
      gpu_render: 4.2ms (240 FPS cap)
      display: 10ms (IPS 240Hz)
    classification: competitive_pro
    note: "Если OLED → display 2ms → total 10ms"

  render_frametime:
    avg_ms: 4.2
    sigma_ms: 1.2
    classification: competitive
    note: "DDR5-6000 CL30 dual-channel минимизирует frametime variance"

  storage_latency:
    expected_4k_random_read_us: 55
    meets_intent_requirements: true
    note: "NVMe Gen4 — значительно выше требований esports"
```

---

## Антипаттерны latency-утверждений

### ANTI-LT-01 — Только FPS без frametime variance

```
ANTI-PATTERN: "240 FPS — идеально для киберспорта"
PROBLEM: 240 FPS avg с σ = 6ms даёт дёрганую картинку.
CORRECT: "240 FPS avg, frametime σ = 1.2ms — competitive уровень."
```

### ANTI-LT-02 — Игнорирование полного latency pipeline

```
ANTI-PATTERN: "Высокий FPS = низкий input lag"
PROBLEM: При 500 FPS но плохом мониторе (15ms) input lag всё равно высокий.
CORRECT: "Total input latency: 18ms (mouse 1ms + CPU 3ms + GPU 4ms + display 10ms)"
```

### ANTI-LT-03 — Хранение без указания метрики

```
ANTI-PATTERN: "Быстрый SSD"
PROBLEM: "Быстрый" для игр = sequential read, для БД = 4K random QD1.
CORRECT: "NVMe Gen4: 4K random read QD1 = 55µs, sequential read = 7 GB/s"
```
