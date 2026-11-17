---
uri: "pcbo:ontology/L2_constraint/structural"
type: "OntologyDocument"
layer: "L2"
version: "3.0.0-draft"
provenance:
  source: "LLM_ESTIMATE"
  model: "gemini-3.1-pro"
  date: "2026-06-02"
  confidence: "estimated"
  calibration_status: "partial"
  note: >
    Физические ограничения (сокеты, размеры) основаны на спецификациях
    производителей и являются vendor_spec. Правила совместимости поколений —
    инженерная оценка, требующая верификации при выходе новых платформ.
    severity: info
relations:
  uses:
    - "pcbo:ontology/L1_intent/context"        # form_factor, case dimensions
  feedsInto:
    - "pcbo:ontology/L4_decision/decision"      # Platform Decision, MB Decision
    - "pcbo:ontology/L5_validation"             # VAL-STRUCT-01..07
  seealso:
    - "pcbo:ontology/L2_constraint/operational" # Operational constraints
tags: ["constraint", "compatibility", "physical", "socket", "form-factor", "L2"]
---

# L2 · Structural Constraints — физическая совместимость

> Компоненты должны физически соединяться и помещаться в корпус.
> Это жёсткие BLOCK constraints — нарушение любого = сборка невалидна.

---

## Platform Compatibility Matrix

```yaml
SocketCompatibility:
  AMD:
    AM5:
      supported_cpu_generations: ["Ryzen 7000", "Ryzen 8000", "Ryzen 9000"]
      ram_type: "DDR5"
      ram_channels: 2
      pcie_generation: "Gen5 (CPU lanes) + Gen4 (chipset)"
      upgrade_path: "Активен. Поддержка как минимум до 2027+."
      status: CURRENT

    AM4:
      supported_cpu_generations: ["Ryzen 1000–5000"]
      ram_type: "DDR4"
      ram_channels: 2
      pcie_generation: "Gen4 (B550/X570) или Gen3 (B450/A320)"
      upgrade_path: "DEAD END. Ryzen 5000 — последнее поколение."
      status: LEGACY

  Intel:
    LGA1851:
      supported_cpu_generations: ["Core Ultra 200"]
      ram_type: "DDR5"
      ram_channels: 2
      pcie_generation: "Gen5 (CPU) + Gen4 (chipset)"
      upgrade_path: "Неопределён. Intel исторически меняет сокет каждые 2 поколения."
      status: CURRENT

    LGA1700:
      supported_cpu_generations: ["12th Gen", "13th Gen", "14th Gen"]
      ram_type: "DDR5 / DDR4 (зависит от MB)"
      ram_channels: 2
      pcie_generation: "Gen5 (CPU) + Gen4 (chipset)"
      upgrade_path: "DEAD END. 14th Gen — последнее на LGA1700."
      status: LEGACY
```

### Platform Selection Rules

```yaml
PlatformRules:
  - id: "STRUCT-PLAT-01"
    condition: "context.budget_ceiling < 800 AND context.expected_lifespan_years >= 4"
    constraint: "Platform = AM5"
    reason: "AM5 — единственная платформа с гарантированным upgrade path"

  - id: "STRUCT-PLAT-02"
    condition: "context.expected_lifespan_years >= 5"
    constraint: "Platform != LGA1700 AND Platform != AM4"
    reason: "Dead-end платформы неоптимальны при длинном горизонте"

  - id: "STRUCT-PLAT-03"
    condition: "intent = upgrade_friendly"
    constraint: "Platform = AM5"
    reason: "AM5 обещает поддержку до 2027+"
```

---

## RAM Compatibility

```yaml
RAMConstraints:
  # От платформы
  - id: "STRUCT-RAM-01"
    condition: "platform.ram_type = DDR5"
    constraint: "ram.type = DDR5"
    block: true

  - id: "STRUCT-RAM-02"
    condition: "platform.ram_type = DDR4"
    constraint: "ram.type = DDR4"
    block: true

  # Конфигурация
  - id: "STRUCT-RAM-03"
    constraint: "ram.sticks IN [2, 4]"
    reason: "Dual-channel обязателен. 1 stick = single channel (запрещено)."
    block: true

  - id: "STRUCT-RAM-04"
    constraint: "ram.sticks = 2 PREFERRED"
    reason: "DDR5 нестабилен на 4 sticks при высоких частотах"
    severity: WARN  # не BLOCK, но настоятельная рекомендация

  # Совместимость с CPU IMC
  - id: "STRUCT-RAM-05"
    condition: "platform = AM5"
    constraint: "ram.speed_mhz ≤ 6400"
    reason: "AMD IMC стабилен до 6400 MT/s (6000 — sweet spot)"
    severity: WARN

  - id: "STRUCT-RAM-06"
    condition: "platform = LGA1851"
    constraint: "ram.speed_mhz ≤ 7200"
    reason: "Intel IMC стабилен до ~7200 MT/s"
    severity: WARN

  # Объём
  - id: "STRUCT-RAM-07"
    constraint: "ram.capacity_GB IN [16, 32, 48, 64, 96, 128]"
    reason: "Реалистичные конфигурации DDR5"
    note: "48/96GB возможны с новыми 24/48GB модулями"
```

---

## GPU Compatibility

```yaml
GPUConstraints:
  # Физические
  - id: "STRUCT-GPU-01"
    constraint: "gpu.length_mm ≤ case.max_gpu_mm"
    block: true
    note: "Учитывать зазор 5-10mm для удобства установки"

  - id: "STRUCT-GPU-02"
    constraint: "gpu.width_slots ≤ case.pcie_slots_available"
    block: true
    note: "2.5-слотовые карты требуют 3 слота пространства"

  # PCIe
  - id: "STRUCT-GPU-03"
    constraint: "gpu.pcie_generation ≤ mb.pcie_generation"
    note: "GPU PCIe 4.0 работает в PCIe 5.0 слоте (обратная совместимость)"
    severity: INFO

  - id: "STRUCT-GPU-04"
    constraint: "gpu.pcie_width = x16"
    note: "Все consumer GPU используют x16 физически (x8 электрически на бюджетных)"
    severity: INFO

  # Питание
  - id: "STRUCT-GPU-05"
    constraint: "psu.pcie_8pin_connectors ≥ gpu.required_8pin_count"
    block: true
    note: "12VHPWR (12+4 pin) коннектор требует 2×8pin на стороне PSU"
```

---

## Cooling Compatibility

```yaml
CoolingConstraints:
  - id: "STRUCT-COOL-01"
    constraint: "cooler.socket_support INCLUDES cpu.socket"
    block: true
    note: "Большинство кулеров поддерживают AM4/AM5/LGA1700 через mounting kit"

  - id: "STRUCT-COOL-02"
    constraint: "cooler.height_mm ≤ case.max_cooler_mm"
    block: true
    note: "Учитывать зазор 3-5mm до стеклянной панели"

  - id: "STRUCT-COOL-03"
    constraint: "cooler.ram_clearance_mm ≥ ram.module_height_mm"
    note: "Актуально для двухбашенных air кулеров"

  - id: "STRUCT-COOL-04"
    condition: "cooler_type = AIO_240mm"
    constraint: "case.radiator_support INCLUDES 240mm"
    block: true

  - id: "STRUCT-COOL-05"
    condition: "cooler_type = AIO_360mm"
    constraint: "case.radiator_support INCLUDES 360mm"
    block: true
```

---

## PSU Compatibility

```yaml
PSUConstraints:
  - id: "STRUCT-PSU-01"
    constraint: "psu.form_factor IN case.psu_form_factor_support"
    block: true
    note: "ATX PSU в ATX/mATX корпусах. SFX/SFX-L в ITX."

  - id: "STRUCT-PSU-02"
    constraint: "psu.length_mm ≤ case.psu_max_length_mm"
    block: true

  - id: "STRUCT-PSU-03"
    constraint: "psu.connectors INCLUDES cpu_8pin × cpu.required_eps_count"
    block: true
```

---

## Motherboard Selection Rules

```yaml
MotherboardConstraints:
  # MB — последний выбор в Decision Chain. Должен удовлетворять всем предыдущим.

  - id: "STRUCT-MB-01"
    constraint: "mb.socket = cpu.socket"
    block: true

  - id: "STRUCT-MB-02"
    constraint: "mb.ram_type = ram.type"
    block: true

  - id: "STRUCT-MB-03"
    constraint: "mb.ram_slots ≥ ram.sticks"
    block: true

  - id: "STRUCT-MB-04"
    constraint: "mb.pcie_x16_slots ≥ 1"
    note: "Для одиночного GPU всегда выполняется"

  - id: "STRUCT-MB-05"
    constraint: "mb.m2_slots ≥ storage.m2_drive_count"
    block: true

  - id: "STRUCT-MB-06"
    constraint: "mb.form_factor ≤ case.form_factor"
    block: true
    note: "mATX MB помещается в ATX корпус. ATX MB не помещается в mATX."

  - id: "STRUCT-MB-07"
    constraint: "mb.chipset соответствует требованиям CPU"
    note: >
      AMD: B650/B650E/X670/X670E/X870/X870E — все поддерживают PBO и EXPO.
      B650 достаточно для большинства сборок. X670E для extreme OC.
      Intel: Z890 для K-series разгона. B860 для non-K.

  # BIOS
  - id: "STRUCT-MB-08"
    condition: "mb.chipset старше CPU на одно поколение"
    constraint: "mb.usb_flashback = true"
    note: "Необходим BIOS update без CPU для совместимости с новым поколением"
    severity: WARN
```

---

## Storage Compatibility

```yaml
StorageConstraints:
  - id: "STRUCT-STG-01"
    constraint: "storage.interface IN mb.storage_interfaces"
    block: true
    note: "M.2 NVMe / SATA — не перепутать слоты"

  - id: "STRUCT-STG-02"
    constraint: "storage.form_factor IN mb.m2_slot_key"
    note: "M.2 2280 — стандарт. 22110 для enterprise."

  - id: "STRUCT-STG-03"
    constraint: "mb.m2_slots_available ≥ storage.drive_count"
    block: true
    note: "Учитывать что некоторые M.2 слоты отключают SATA порты"
```

---

## Constraint Propagation

При выборе компонента в Decision Chain, constraints распространяются на последующие Decisions:

```yaml
ConstraintPropagation:
  # Выбрали платформу AM5 → сузили CPU, RAM, MB
  Platform_selected:
    propagates_to: [CPU, RAM, MB]
    constraints:
      - "cpu.socket = AM5"
      - "ram.type = DDR5"
      - "mb.socket = AM5"

  # Выбрали GPU длиной 320mm → сузили корпус
  GPU_selected:
    propagates_to: [Case, PSU]
    constraints:
      - "case.max_gpu_mm ≥ 320"
      - "psu.wattage ≥ gpu.tgp_W × 1.5 + cpu.tdp_W + 100"

  # Выбрали CPU с TDP 170W → сузили кулер
  CPU_selected:
    propagates_to: [Cooler, PSU]
    constraints:
      - "cooler.max_tdp_W ≥ 170"
      - "psu.wattage ≥ gpu.tgp_W + 170 + 100"
```
