---
id: "nvidia-rtx-4090"
type: "gpu"
title: "NVIDIA GeForce RTX 4090 24GB"
vendor: "nvidia"
status: "verified"
last_updated: "2026-06-03"
tags: ["nvidia", "ada", "4k", "24gb-vram", "450w-tgp", "atx3.0"]
profiles:
  halo_4k_path_tracing:
    criteria_met: true
    steel_man_desc: "4K-гейминг с трассировкой лучей на максимальных настройках. БП ATX 3.0 от 850W, корпус с хорошим продувом."
    failure_mode_desc: "Малый корпус и слабый БП: карта физически не встаёт или вызывает срабатывание OCP на transient spikes."
    optimal_for_intents: ["aaa_4k_ultra", "aaa_4k_path_tracing"]
    failure_for_intents: ["sff_build"]
    failure_severity: "BLOCK"
specs:
  gpu: "AD102 (Ada Lovelace)"
  vram: "24 GB GDDR6X"
  tbp: "450W"
  pcie: "PCIe 4.0 x16"
---

# NVIDIA GeForce RTX 4090 24GB

Сокращённая карточка для примера «маркетплейс-ловушка». Полная карточка
в публичном репозитории `kaizin-lab/pc_hardware_knowledge_base`.

Сама по себе карта корректна для 4K. Проблема возникает не в профиле GPU,
а в физике: длина, толщина, питание и корпус.
