---
id: "amd-rx-7600"
type: "gpu"
title: "AMD Radeon RX 7600 8GB"
vendor: "amd"
status: "verified"
last_updated: "2026-06-03"
tags: ["amd", "rdna3", "1080p", "8gb-vram", "pcie4.0-x8", "165w-tbp"]
profiles:
  mainstream_efficiency_tgp_150w:
    criteria_met: true
    steel_man_desc: "Массовые игровые ПК среднего класса: 1080p/1440p. БП 500–550W. Минимальные требования к вентиляции, низкий шум."
    failure_mode_desc: "Нативный 4K-гейминг. Недостаток вычислительных блоков не позволяет 60 FPS — снижение до Medium/Low."
    optimal_for_intents: ["aaa_1080p_ultra", "aaa_1440p_high", "esports_1080p_240hz", "silent_build", "sff_build"]
    failure_for_intents: ["aaa_4k_ultra", "aaa_4k_path_tracing"]
    failure_severity: "BLOCK"
specs:
  gpu: "Navi 33 XL (RDNA 3)"
  vram: "8 GB GDDR6 (128-bit)"
  tbp: "165W"
  pcie: "PCIe 4.0 x8"
---

# AMD Radeon RX 7600 8GB

Сокращённая карточка для примеров PCBO. Полная версия и источник данных —
публичный репозиторий `kaizin-lab/pc_hardware_knowledge_base`.

Карта интересна тем, что её профиль `mainstream_efficiency_tgp_150w` является
`optimal` для киберспорта 1080p/240Hz, но `BLOCK` для 4K. Это ровно тот случай,
когда «слабая» карта оказывается правильным решением под конкретный intent.
