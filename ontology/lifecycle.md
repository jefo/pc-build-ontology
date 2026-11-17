---
uri: "pcbo:ontology/L6_lifecycle/lifecycle"
type: "OntologyDocument"
layer: "L6"
version: "2.0.0"
relations:
  uses: ["pcbo:ontology/L1_intent/context", "pcbo:ontology/L4_decision/decision"]
  seealso: ["pcbo:ontology/L4_decision/risk"]
tags: ["lifecycle", "upgrade", "depreciation", "temporal", "L6"]
---

# L6 · Lifecycle — жизненный цикл сборки

> PCBO — не статическая база, а **живая инженерная модель**.  
> Система меняется во времени: накапливается obsolescence,  
> появляются новые нагрузки, меняется Intent пользователя.

---

## Стадии жизненного цикла

```
LifecycleStage
├── InitialBuild         ← сборка и первый запуск
├── Tuning               ← оптимизация: XMP, fan curves, OC
├── Steady_Operation     ← основная жизнь системы
├── Partial_Upgrade      ← замена одного или нескольких компонентов
├── Major_Refresh        ← смена платформы (CPU+MB+RAM)
├── Repurpose            ← смена Intent (игровой → офисный)
└── Decommission         ← система устарела, замена целесообразна
```

---

## Модель obsolescence

Разные компоненты устаревают с разной скоростью:

```yaml
ObsolescenceRates:

  GPU:
    performance_halflife_years: 3.0   # через 3 года — "половина" современного уровня
    bottleneck_emergence: "GPU часто устаревает первым в gaming-сборках"
    upgrade_trigger: "Целевые игры не держат 60 FPS на medium"
    
  CPU:
    performance_halflife_years: 5.0   # CPU устаревает медленнее
    platform_lock: true               # платформа дороже самого CPU
    upgrade_trigger: "CPU создаёт BI > 30% с новым GPU"
    
  RAM:
    capacity_halflife_years: 4.0      # 16GB → 32GB как норма
    speed_obsolescence: "DDR4 → DDR5 переход; DDR4 актуален до ~2027"
    upgrade_trigger: "Frequent swap/stutter при обычных задачах"
    
  Storage:
    capacity_halflife_years: 3.0      # игры растут быстро
    speed_obsolescence: "Gen3 NVMe актуален; Gen4 стандарт к 2025"
    upgrade_trigger: "Нехватка места ИЛИ очевидные I/O bottlenecks"
    
  PSU:
    performance_halflife_years: 8.0   # PSU не устаревает функционально
    physical_degradation: "Конденсаторы деградируют ~10 лет"
    upgrade_trigger: "Новые компоненты требуют больше мощности"
    
  Motherboard:
    platform_lock: true               # MB = платформа = CPU
    upgrade_with: CPU                 # меняется одновременно с CPU
    upgrade_trigger: "Смена поколения CPU (новый сокет)"
```

---

## Модель апгрейда

### Правила приоритизации апгрейда

```
UPGRADE_PRIORITY_FUNCTION(build, time_elapsed)

INPUT:
  current_build
  elapsed_years since build
  current_target_performance
  available_upgrade_budget

EVALUATE for each component:
  bottleneck_score(component)    # насколько компонент тормозит систему
  obsolescence_score(component)  # насколько устарел относительно рынка
  upgrade_value(component)       # сколько FPS/performance даёт замена

RETURN: ranked upgrade candidates

RULES:
  1. Никогда не апгрейдь не-bottleneck
     "Замена RTX 4070 на 4090 при i3 CPU = деньги на ветер"
  
  2. Платформа меняется редко — планируй заранее
     "AM5 MB + слабый CPU сейчас → сильный CPU через 2 года"
  
  3. Marginal Value апгрейда должна быть выше порога
     MV_upgrade = delta_performance / delta_price > threshold(intent)
  
  4. Синергия апгрейда важна
     "GPU апгрейд с CPU-bottleneck = потеря половины ценности апгрейда"
```

### Дерево апгрейдов по Intent

```yaml
# Типичные апгрейд-пути

intent:aaa_gaming_1440p:
  year_1-2:
    - action: "Tuning (XMP, fan curves)"
      cost: "$0"
      gain: "3-8% производительность бесплатно"
  
  year_2-3:
    - trigger: "Новые AAA требуют 12GB+ VRAM или не держат 60 FPS"
      action: "GPU upgrade (следующий тир)"
      budget: "$200-400 (sell old + buy new)"
      
  year_3-4:
    - trigger: "CPU создаёт BI > 20% с новым GPU"
      action: "CPU upgrade (в рамках платформы AM5)"
      budget: "$200-300"
      note: "AM5 позволяет: Ryzen 5 7600 → Ryzen 7 9800X3D без смены MB"
      
  year_5+:
    - trigger: "Система отстаёт во всех бенчмарках"
      action: "Platform refresh (CPU+MB+RAM)"
      budget: "$600-900"

intent:esports_240hz:
  year_1-3:
    - "Система стареет медленно — esports-игры нетребовательны"
    - action: "Только storage расширение если нужно"
  year_3-5:
    - trigger: "Новый процессор даёт +20% FPS в CS2"
      action: "CPU upgrade"
```

---

## Репурпозинг (Repurpose)

Когда Intent пользователя меняется:

```yaml
Repurpose_Scenarios:

  Gaming → Office:
    required_changes: []            # gaming PC избыточен для офиса
    recommended_changes: ["GPU → iGPU если есть, продать GPU"]
    value_recovery: "GPU продаётся хорошо"
    
  Gaming → Content_Creation:
    required_changes: ["RAM ≥ 32GB", "Storage ≥ 2TB"]
    recommended_changes: ["CPU upgrade если < 8 cores"]
    note: "GPU часто достаточен; монтаж GPU не так зависит"
    
  Office → Gaming:
    required_changes: ["GPU добавить"]
    platform_check: "Есть ли PCIe x16 slot? Достаточен ли PSU?"
    
  Gaming → AI_Inference:
    required_changes: ["GPU с большим VRAM (≥ 16GB)"]
    note: "RTX 3090 / RTX 4090 оптимальны для локальных LLM"
    trade: "Продать gaming GPU + доплатить"
```

---

## Lifecycle в Build Artifact

Каждая верифицированная сборка включает lifecycle plan:

```yaml
# Фрагмент Build Template
lifecycle:
  initial_stage: "InitialBuild"
  
  tuning_plan:
    - "Включить XMP/EXPO в BIOS"
    - "Настроить fan curves: 40-50% при <60°C, 100% при >80°C"
    - "Prime95 stress test 30min"
  
  upgrade_horizon:
    year_2:
      trigger: "GPU BI > 20% с новым GPU поколения"
      recommended: "GPU upgrade ~$300-400"
    year_4:
      trigger: "Platform aging"
      recommended: "CPU upgrade within AM5"
    year_6:
      trigger: "Platform obsolescence"
      recommended: "Full refresh"
  
  end_of_life_indicator:
    - "Целевые игры не держат 60 FPS на low settings"
    - "Операционная система прекратила поддержку"
    - "Стоимость ремонта > 50% стоимости замены"
```
