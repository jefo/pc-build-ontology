'''
PCBOv2 Config Loader — единая точка чтения YAML-конфигов.
Загружает 5 YAML-файлов один раз при импорте.
Все валидаторы используют этот модуль вместо хардкода.
'''

import yaml
from pathlib import Path

ENGINE_DIR = Path(__file__).parent

def _load_yaml(name: str) -> dict:
    with open(ENGINE_DIR / name, encoding='utf-8') as f:
        return yaml.safe_load(f)

# Загрузка при импорте (один раз)
CHIPSET_PROFILES = _load_yaml('chipset_profiles.yaml')
CPU_VRM_TIERS     = _load_yaml('cpu_vrm_tiers.yaml')
GPU_PCIE_TIERS    = _load_yaml('gpu_pcie_tiers.yaml')
INTENT_FLOORS     = _load_yaml('intent_floors.yaml')
BUDGET_TIERS      = _load_yaml('budget_tiers.yaml')
DOMAIN_IMPACT     = _load_yaml('domain_impact_matrix.yaml')

# ═══ Удобные аксессоры ═══

def get_chipset(chipset_name: str) -> dict:
    """Получить профиль чипсета: pcie_gen, vrm_tier, m2_slots_range, bifurcation."""
    return CHIPSET_PROFILES.get('chipsets', {}).get(chipset_name, {})

def get_chipset_pcie_gen(chipset_name: str) -> int:
    return get_chipset(chipset_name).get('pcie_gen', 4)

def get_chipset_vrm_tier(chipset_name: str) -> str:
    return get_chipset(chipset_name).get('vrm_tier', 'basic_stable')

def get_vrm_tier_rank() -> dict:
    return CHIPSET_PROFILES.get('vrm_tier_rank', {})

def get_bifurcation_chipsets() -> list[str]:
    return [k for k, v in CHIPSET_PROFILES.get('chipsets', {}).items()
            if v.get('bifurcation', False)]

def get_full_x16_chipsets() -> list[str]:
    return [k for k, v in CHIPSET_PROFILES.get('chipsets', {}).items()
            if not v.get('bifurcation', False) and v.get('pcie_gen', 4) >= 4]

def get_cpu_vrm_requirements() -> list[dict]:
    return CPU_VRM_TIERS.get('tdp_to_vrm', [])

def get_gpu_pcie_requirements() -> list[dict]:
    return GPU_PCIE_TIERS.get('gpu_pcie_slot_requirements', [])

def get_gpu_pcie_ai_modifier() -> dict:
    return GPU_PCIE_TIERS.get('ai_modifier', {})

def get_intent_floor(intent_id: str) -> dict | None:
    return INTENT_FLOORS.get('intents', {}).get(intent_id)

def get_intent_floors_all() -> dict:
    return INTENT_FLOORS.get('intents', {})

def get_budget_tier(budget: int) -> dict | None:
    for tier_id, tier in BUDGET_TIERS.get('budget_tiers', {}).items():
        if tier['budget_min'] <= budget <= tier['budget_max']:
            return tier
    return None

# ═══ Domain Impact Matrix accessors ═══

def get_component_domains(component_type: str) -> dict:
    """Возвращает словарь доменных флагов для типа компонента.
    Пример: get_component_domains('psu') → {thermal_emitter: true, power_provider: true, ...}"""
    return DOMAIN_IMPACT.get('component_impacts', {}).get(component_type, {})

def get_acoustic_emitter_types() -> list[str]:
    """Возвращает список типов компонентов, являющихся источниками шума.
    Используется L3-симуляторами для enumeration."""
    impacts = DOMAIN_IMPACT.get('component_impacts', {})
    return [ctype for ctype, flags in impacts.items() if flags.get('acoustic_emitter')]

def get_completeness_rule(domain: str) -> dict:
    """Возвращает правило completeness check для домена.
    Пример: get_completeness_rule('acoustic_emitter') → {default_profile, severity, message}"""
    return DOMAIN_IMPACT.get('completeness_rules', {}).get(domain, {})
