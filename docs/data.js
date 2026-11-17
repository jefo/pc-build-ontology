window.PCBO_DEMO = {
  "scenarios": [
    {
      "slug": "esports-240hz",
      "label": "Киберспорт 240 Hz",
      "caseId": "CASE 001",
      "tagline": "CS2 и Valorant. 1080p. Стабильные 240+ FPS.",
      "note": "Каждый рубль выше RX 7600 уходит впустую: сценарий CPU-bound.",
      "total": "101 800 ₽",
      "components": [
        [
          "CPU",
          "Ryzen 7 7800X3D",
          "120 W",
          "cache_dominant_gaming"
        ],
        [
          "GPU",
          "Radeon RX 7600 8GB",
          "165 W",
          "balanced_performance"
        ],
        [
          "MB",
          "B650E",
          "—",
          "sweet_spot_stable"
        ],
        [
          "RAM",
          "32 GB DDR5-6000",
          "—",
          "dual channel"
        ],
        [
          "SSD",
          "1 TB NVMe",
          "—",
          "PCIe 4.0 x4"
        ],
        [
          "PSU",
          "650 W",
          "—",
          "headroom 1.94×"
        ],
        [
          "Cooler",
          "Air tower 155 mm",
          "—",
          "120 mm fan"
        ],
        [
          "Case",
          "GPU до 350 mm",
          "—",
          "high airflow"
        ]
      ],
      "build": {
        "id": "esports-240hz",
        "intent": "esports_1080p_240hz",
        "budget": {
          "actual_cost": 101800,
          "ceiling": 120000
        },
        "case": {
          "max_gpu_mm": 350,
          "max_cooler_mm": 165,
          "supported_form_factors": [
            "ATX",
            "mATX"
          ]
        },
        "gpu": {
          "length_mm": 240,
          "width_slots": 2.0
        },
        "cooler": {
          "height_mm": 155,
          "cooler_type": "air",
          "layout_type": "tower",
          "horizontal_outlay_radius_mm": 55
        },
        "motherboard": {
          "form_factor": "mATX",
          "ram_slots": 4,
          "m2_slots": 2,
          "vrm_heatsink_height_max_mm": 30,
          "ram_slot_offset_x_mm": 50
        },
        "ram": {
          "module_height_mm": 31
        },
        "pcie": {
          "platform": "AM5",
          "motherboard_chipset": "B650E",
          "m2_drives_count": 1,
          "gpu": {
            "pcie_width": 8,
            "pcie_gen": 4
          }
        },
        "thermal": {
          "ambient_temp_C": 25,
          "case": {
            "airflow_class": "high"
          },
          "cpu": {
            "tdp_W": 120,
            "load_factor": 0.8
          },
          "gpu": {
            "tgp_W": 165,
            "load_factor": 0.9
          },
          "cooler": {
            "cooler_type": "air",
            "efficiency_class": "air_tower_120mm"
          }
        },
        "power": {
          "cpu_tdp_W": 120,
          "gpu_tgp_W": 165,
          "platform_overhead_W": 50,
          "psu": {
            "wattage": 650,
            "specification": "ATX2.4"
          }
        },
        "acoustic": {
          "system_power_W": 258,
          "components": {
            "cooler_type": "air_single_tower",
            "gpu_cooler": "open_air_2fan",
            "psu_acoustic": "semi_passive",
            "rgb_ecosystems": []
          },
          "noise_constraint": "moderate"
        },
        "profile_check": {
          "components": [
            {
              "id": "amd-ryzen-7-7800x3d",
              "type": "cpu",
              "file": "examples/kb/catalog/cpu/amd-ryzen-7-7800x3d.md"
            },
            {
              "id": "amd-rx-7600",
              "type": "gpu",
              "file": "examples/kb/catalog/gpu/amd-rx-7600.md"
            }
          ],
          "user_intents": [
            "esports_1080p_240hz"
          ],
          "primary_intent": "esports_1080p_240hz"
        },
        "physical_check": {
          "components": {
            "gpu": {
              "id": "amd-rx-7600",
              "specs": {
                "length_mm": 240,
                "thickness_slots": 2.0
              }
            },
            "cooler": {
              "id": "deepcool-ak400",
              "specs": {
                "height_mm": 155
              }
            },
            "psu": {
              "id": "deepcool-pf650",
              "physical_stereotypes": {
                "atx_form_factor": true
              }
            }
          },
          "constraints": {
            "gpu_max_length_mm": 350,
            "gpu_max_thickness_slots": 2.5,
            "cooler_max_height_mm": 165
          }
        },
        "cpu_vrm": {
          "cpu": {
            "tdp_w": 120,
            "id": "amd-ryzen-7-7800x3d",
            "title": "AMD Ryzen 7 7800X3D"
          },
          "motherboard": {
            "chipset": "B650E",
            "id": "asus-b650e",
            "title": "ASUS B650E"
          }
        },
        "gpu_pcie": {
          "gpu": {
            "pcie": "PCIe 4.0 x8",
            "id": "amd-rx-7600"
          },
          "motherboard": {
            "chipset": "B650E",
            "id": "asus-b650e"
          },
          "intent": "esports"
        },
        "component_floor": {
          "intent_id": "esports_competitive_360hz",
          "cpu": {
            "cores": 8,
            "id": "amd-ryzen-7-7800x3d"
          },
          "gpu": {
            "vram_gb": 8,
            "fp32_tflops": 21.5,
            "id": "amd-rx-7600"
          },
          "ram": {
            "capacity_gb": 32,
            "id": "gskill-ripjaws-s5-32gb"
          },
          "storage": {
            "capacity_gb": 1000,
            "sustained_write": true,
            "id": "kingston-nv3-1tb"
          }
        },
        "cpu_mvs": {},
        "ram_mvs": {}
      },
      "result": {
        "structural_clearance": {
          "is_compatible": true,
          "failures": [],
          "tolerances": {
            "gpu_clearance_mm": 110,
            "cooler_clearance_mm": 10
          }
        },
        "envelope_collision_3d": {
          "is_compatible": true,
          "conflicts": [],
          "tolerances": {
            "ram_collision_gap_mm": 9
          }
        },
        "pcie_topology": {
          "gpu_effective_pcie_lanes": 8,
          "gpu_pcie_gen_effective": 4,
          "gpu_pcie_gen_original": 4,
          "slot_pcie_gen": 5,
          "generation_degraded": false,
          "effective_bandwidth_gbs": 15.8,
          "bandwidth_warning": "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen4 ×8) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур.",
          "intent": "",
          "offload_bandwidth_gbs": null,
          "storage_sustained_write_compliant": true,
          "dram_warning": null,
          "warnings": [
            "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen4 ×8) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур."
          ],
          "original_gpu_lanes": 8,
          "lane_loss": 0
        },
        "thermal_profile": {
          "ambient_temp_C": 25,
          "case_delta_C": 8.0,
          "case_airflow_class": "high",
          "case_exhaust_capacity_W": 300,
          "total_heat_generation_W": 244.5,
          "thermal_soak_active": false,
          "thermal_soak_penalty_C": 0.0,
          "internal_case_ambient_C": 33.0,
          "predicted_cpu_temp_C": 57.0,
          "predicted_gpu_temp_C": 30.6,
          "cpu_thermal_state": "T_Warm",
          "gpu_thermal_state": "T_Cool",
          "is_mutual_heating_active": false
        },
        "power_state": {
          "gaming_power_W": 258,
          "full_load_power_W": 335,
          "psu_headroom_factor": 1.94,
          "gaming_headroom_factor": 2.51,
          "atx_3_spec_required": false,
          "atx_3_spec_satisfied": true,
          "status": "PASS",
          "messages": [
            "PASS: Энергобаланс в норме."
          ]
        },
        "acoustic_class": {
          "predicted_acoustic_class_idle": "A1",
          "predicted_acoustic_class_load": "A2",
          "high_dpc_latency_risk": false,
          "is_compliant": true,
          "warnings": []
        },
        "profile_conflicts": {
          "profile_validation_status": "PASS",
          "profile_action": "proceed",
          "optimal_matches": [
            {
              "component": "amd-rx-7600",
              "profile": "mainstream_efficiency_tgp_150w",
              "matched_intents": [
                "esports_1080p_240hz"
              ],
              "steel_man": "Массовые игровые ПК среднего класса: 1080p/1440p. БП 500–550W. Минимальные требования к вентиляции, низкий шум."
            }
          ],
          "blocks": [],
          "warnings": [],
          "summary": {
            "optimal_count": 1,
            "block_count": 0,
            "warn_count": 0
          }
        },
        "physical_constraints": {
          "pass": true,
          "checks": [
            {
              "component": "gpu",
              "check": "length",
              "status": "PASS",
              "detail": "240mm ≤ 350mm"
            },
            {
              "component": "gpu",
              "check": "thickness",
              "status": "PASS",
              "detail": "2.0 slots ≤ 2.5 slots"
            },
            {
              "component": "cooler",
              "check": "height",
              "status": "PASS",
              "detail": "155mm ≤ 165mm"
            }
          ],
          "blocking_failures": 0,
          "warnings": 0
        },
        "mvs_allocation": {
          "mvs_status": "PASS",
          "tier_label": "Средний сегмент (90–150K ₽)",
          "summary": "Тир: Средний сегмент (90–150K ₽) (90,000–150,000₽). Нарушений: 0.",
          "violations": []
        },
        "cpu_vrm": {
          "cpu_vrm_status": "PASS",
          "summary": "CPU 120W (требует ≥sweet_spot_stable) → MB B650E (sweet_spot_stable): совместимо.",
          "violations": [],
          "cpu_tdp_w": 120,
          "required_vrm": "sweet_spot_stable",
          "actual_vrm": "sweet_spot_stable"
        },
        "gpu_pcie": {
          "gpu_pcie_status": "PASS",
          "summary": "GPU Gen4_x8 → MB B650E (Gen5-слот): совместимо.",
          "violations": [],
          "gpu_class": "Gen4_x8",
          "gpu_pcie_gen": 4,
          "gpu_pcie_lanes": 8,
          "required_mb_gen": 4,
          "actual_mb_gen": 5,
          "ai_modifier": false
        },
        "component_floor": {
          "floor_status": "PASS",
          "summary": "Floor check для esports_competitive_360hz (бутылка: cpu). Нарушений: 0.",
          "violations": [],
          "intent_id": "esports_competitive_360hz",
          "bottleneck": "cpu"
        },
        "l5_validation": {
          "validation_status": "PASS_WITH_WARNINGS",
          "action_required": "proceed_to_document",
          "failed_check_ids": [],
          "warnings": [
            "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen4 ×8) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур."
          ],
          "summary": "Есть предупреждения. Сборка допустима, но с оговорками."
        }
      }
    },
    {
      "slug": "xeon-rtx4090-trap",
      "label": "Ловушка с маркетплейса",
      "caseId": "CASE 002",
      "tagline": "Xeon + RTX 4090. «Игровой монстр 4K» за 132 000 ₽.",
      "note": "Каждый компонент по отдельности знаком. Вместе — не собирается.",
      "total": "132 000 ₽",
      "components": [
        [
          "CPU",
          "Xeon E5-2670 v3",
          "135 W",
          "X99, DDR3"
        ],
        [
          "GPU",
          "RTX 4090 24GB",
          "320 W",
          "348 mm, 3.5 слота"
        ],
        [
          "MB",
          "X99",
          "—",
          "1 × M.2, Gen4"
        ],
        [
          "RAM",
          "32 GB DDR3 ECC",
          "—",
          "серверная"
        ],
        [
          "SSD",
          "1 TB SATA",
          "—",
          "без sustained write"
        ],
        [
          "PSU",
          "450 W",
          "—",
          "ATX 2.4"
        ],
        [
          "Cooler",
          "Air tower 160 mm",
          "—",
          "лимит 155 мм"
        ],
        [
          "Case",
          "GPU до 300 mm",
          "—",
          "normal airflow"
        ]
      ],
      "build": {
        "id": "xeon-rtx4090-trap",
        "intent": "aaa_4k_ultra",
        "budget": {
          "actual_cost": 132000,
          "ceiling": 120000
        },
        "case": {
          "max_gpu_mm": 300,
          "max_cooler_mm": 160,
          "supported_form_factors": [
            "ATX"
          ]
        },
        "gpu": {
          "length_mm": 348,
          "width_slots": 3.5
        },
        "cooler": {
          "height_mm": 160,
          "cooler_type": "air",
          "layout_type": "tower",
          "horizontal_outlay_radius_mm": 60
        },
        "motherboard": {
          "form_factor": "ATX",
          "ram_slots": 4,
          "m2_slots": 1,
          "vrm_heatsink_height_max_mm": 30,
          "ram_slot_offset_x_mm": 50
        },
        "ram": {
          "module_height_mm": 31
        },
        "pcie": {
          "platform": "LGA2011-3",
          "motherboard_chipset": "X99",
          "m2_drives_count": 1,
          "gpu": {
            "pcie_width": 16,
            "pcie_gen": 3
          }
        },
        "thermal": {
          "ambient_temp_C": 25,
          "case": {
            "airflow_class": "normal"
          },
          "cpu": {
            "tdp_W": 135,
            "load_factor": 0.9
          },
          "gpu": {
            "tgp_W": 320,
            "load_factor": 0.9
          },
          "cooler": {
            "cooler_type": "air",
            "efficiency_class": "air_tower_120mm"
          }
        },
        "power": {
          "cpu_tdp_W": 135,
          "gpu_tgp_W": 320,
          "platform_overhead_W": 50,
          "psu": {
            "wattage": 450,
            "specification": "ATX2.4"
          }
        },
        "acoustic": {
          "system_power_W": 505,
          "components": {
            "cooler_type": "air_single_tower",
            "gpu_cooler": "open_air_3fan",
            "psu_acoustic": "active",
            "rgb_ecosystems": []
          },
          "noise_constraint": "moderate"
        },
        "profile_check": {
          "components": [
            {
              "id": "nvidia-rtx-4090",
              "type": "gpu",
              "file": "examples/kb/catalog/gpu/nvidia-rtx-4090.md"
            }
          ],
          "user_intents": [
            "aaa_4k_ultra"
          ],
          "primary_intent": "aaa_4k_ultra"
        },
        "physical_check": {
          "components": {
            "gpu": {
              "id": "nvidia-rtx-4090",
              "specs": {
                "length_mm": 348,
                "thickness_slots": 3.5
              }
            },
            "cooler": {
              "id": "deepcool-ak620",
              "specs": {
                "height_mm": 160
              }
            },
            "psu": {
              "id": "generic-450w",
              "physical_stereotypes": {
                "atx_form_factor": true
              }
            }
          },
          "constraints": {
            "gpu_max_length_mm": 320,
            "gpu_max_thickness_slots": 3.0,
            "cooler_max_height_mm": 155,
            "power_budget_max_w": 750
          }
        },
        "component_floor": {
          "intent_id": "aaa_gaming_base",
          "cpu": {
            "cores": 4,
            "id": "intel-xeon-e5-2670-v3"
          },
          "gpu": {
            "vram_gb": 24,
            "fp32_tflops": 82.6,
            "id": "nvidia-rtx-4090"
          },
          "ram": {
            "capacity_gb": 32,
            "id": "ddr3-ecc-32gb"
          },
          "storage": {
            "capacity_gb": 1000,
            "sustained_write": false,
            "id": "sata-ssd-1tb"
          },
          "intent_params": {
            "resolution": "4K"
          }
        },
        "cpu_mvs": {},
        "ram_mvs": {}
      },
      "result": {
        "structural_clearance": {
          "is_compatible": false,
          "failures": [
            "GPU (348mm) не влезает в корпус (макс: 300mm, нужен зазор 10mm). Дефицит: 58mm.",
            "Кулер (160mm) не влезает в корпус (макс: 160mm, нужен зазор 5mm). Дефицит: 5mm."
          ],
          "tolerances": {
            "gpu_clearance_mm": -48,
            "cooler_clearance_mm": 0
          }
        },
        "envelope_collision_3d": {
          "is_compatible": true,
          "conflicts": [],
          "tolerances": {
            "ram_collision_gap_mm": 9
          }
        },
        "pcie_topology": {
          "gpu_effective_pcie_lanes": 16,
          "gpu_pcie_gen_effective": 3,
          "gpu_pcie_gen_original": 3,
          "slot_pcie_gen": 4,
          "generation_degraded": false,
          "effective_bandwidth_gbs": 15.8,
          "bandwidth_warning": "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen3 ×16) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур.",
          "intent": "",
          "offload_bandwidth_gbs": null,
          "storage_sustained_write_compliant": true,
          "dram_warning": null,
          "warnings": [
            "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen3 ×16) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур."
          ],
          "original_gpu_lanes": 16,
          "lane_loss": 0
        },
        "thermal_profile": {
          "ambient_temp_C": 25,
          "case_delta_C": 8.0,
          "case_airflow_class": "normal",
          "case_exhaust_capacity_W": 300,
          "total_heat_generation_W": 409.5,
          "thermal_soak_active": true,
          "thermal_soak_penalty_C": 5.5,
          "internal_case_ambient_C": 52.9,
          "predicted_cpu_temp_C": 83.2,
          "predicted_gpu_temp_C": 33.9,
          "cpu_thermal_state": "T_Hot",
          "gpu_thermal_state": "T_Cool",
          "is_mutual_heating_active": true
        },
        "power_state": {
          "gaming_power_W": 406,
          "full_load_power_W": 505,
          "psu_headroom_factor": 0.89,
          "gaming_headroom_factor": 1.11,
          "atx_3_spec_required": true,
          "atx_3_spec_satisfied": false,
          "status": "BLOCK",
          "messages": [
            "BLOCK: БП 450W недостаточен. Full load: 505W, нужно минимум 556W.",
            "BLOCK: GPU 320W требует БП ATX 3.0/3.1 (защита от transient spikes). Текущий: ATX2.4."
          ]
        },
        "acoustic_class": {
          "predicted_acoustic_class_idle": "A2",
          "predicted_acoustic_class_load": "A4",
          "high_dpc_latency_risk": false,
          "is_compliant": false,
          "warnings": [
            "ACOUSTIC: Класс шума A4 превышает ограничение moderate (макс: A3)."
          ]
        },
        "profile_conflicts": {
          "profile_validation_status": "PASS",
          "profile_action": "proceed",
          "optimal_matches": [
            {
              "component": "nvidia-rtx-4090",
              "profile": "halo_4k_path_tracing",
              "matched_intents": [
                "aaa_4k_ultra"
              ],
              "steel_man": "4K-гейминг с трассировкой лучей на максимальных настройках. БП ATX 3.0 от 850W, корпус с хорошим продувом."
            }
          ],
          "blocks": [],
          "warnings": [],
          "summary": {
            "optimal_count": 1,
            "block_count": 0,
            "warn_count": 0
          }
        },
        "physical_constraints": {
          "pass": false,
          "checks": [
            {
              "component": "gpu",
              "check": "length",
              "status": "FAIL",
              "detail": "GPU length 348mm > 320mm limit"
            },
            {
              "component": "gpu",
              "check": "thickness",
              "status": "FAIL",
              "detail": "GPU thickness 3.5 slots > 3.0 slots limit"
            },
            {
              "component": "cooler",
              "check": "height",
              "status": "FAIL",
              "detail": "Cooler height 160mm > 155mm limit"
            }
          ],
          "blocking_failures": 3,
          "warnings": 0
        },
        "mvs_allocation": {
          "mvs_status": "FAIL",
          "tier_label": "Средний сегмент (90–150K ₽)",
          "summary": "Тир: Средний сегмент (90–150K ₽) (90,000–150,000₽). Нарушений: 3.",
          "violations": [
            {
              "check": "m2_slots",
              "severity": "WARN",
              "message": "MVS: плата имеет 1 M.2 слотов, тир требует ≥2. Ограничено расширение хранилища.",
              "required": "≥2",
              "actual": "1"
            },
            {
              "check": "pcie_gen",
              "severity": "BLOCK",
              "message": "MVS: чипсет X99 поддерживает PCIe Gen4, тир требует Gen5. Карты Gen5 будут работать на пониженной скорости.",
              "required": "Gen5",
              "actual": "Gen4"
            },
            {
              "check": "vrm_tier",
              "severity": "WARN",
              "message": "MVS: чипсет X99 имеет VRM уровня «basic_stable», тир требует «sweet_spot_stable». Под sustained нагрузкой возможен троттлинг.",
              "required": "sweet_spot_stable",
              "actual": "basic_stable"
            }
          ]
        },
        "component_floor": {
          "floor_status": "PASS",
          "summary": "Floor check для aaa_gaming_base (бутылка: gpu). Нарушений: 0.",
          "violations": [],
          "intent_id": "aaa_gaming_base",
          "bottleneck": "gpu"
        },
        "l5_validation": {
          "validation_status": "FAIL",
          "action_required": "rollback",
          "failed_check_ids": [
            "STRUCTURAL: Компоненты физически несовместимы.",
            "POWER: BLOCK: БП 450W недостаточен. Full load: 505W, нужно минимум 556W.",
            "MVS: MVS: чипсет X99 поддерживает PCIe Gen4, тир требует Gen5. Карты Gen5 будут работать на пониженной скорости.",
            "BUDGET: 132,000₽ превышает потолок 120,000₽ на 12,000₽."
          ],
          "warnings": [
            "THERMAL: CPU 83.2°C — близко к пределу.",
            "THERMAL SOAK: Корпус (normal) не справляется с отводом 410W тепла (exhaust capacity: 300W). При sustained нагрузке температуры будут расти (+5.5°C penalty).",
            "ACOUSTIC: Класс шума A4 превышает ограничение moderate (макс: A3).",
            "BANDWIDTH WARNING: Effective PCIe bandwidth 15.8 GB/s (Gen3 ×16) ниже рекомендованного уровня для 1440p+ гейминга (20.0 GB/s). Возможны микрофризы при потоковой подгрузке текстур.",
            "MVS: MVS: плата имеет 1 M.2 слотов, тир требует ≥2. Ограничено расширение хранилища.",
            "MVS: MVS: чипсет X99 имеет VRM уровня «basic_stable», тир требует «sweet_spot_stable». Под sustained нагрузкой возможен троттлинг."
          ],
          "summary": "Критические ошибки. Необходим rollback и пересмотр."
        }
      }
    }
  ]
};
