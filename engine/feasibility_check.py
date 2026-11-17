"""
PCBO Feasibility Model — pre-synthesis gate.
Оценивает выполнимость интента до начала подбора компонентов.

Основан на: бенчмарках Intel Arc B580 (июнь 2026), экстраполяции на другие GPU tiers.
Модель консервативна: если данных нет — считаем невыполнимым.

GPU tiers (L1-L3) × resolution → достижимый FPS (AAA, high/ultra, native):
  L1 (mainstream):     1080p@60fps
  L2 (balanced):       1080p@120fps, 1440p@60fps
  L3 (enthusiast):     1440p@120fps, 4K@60fps

Модификаторы:
  + upscaling (XeSS/DLSS Quality): +1 resolution tier at same FPS
  + frame_gen: ×1.5-1.8 effective FPS
  + RT ON: −1 FPS tier (L2 RT ≈ L1 native)
  + path_tracing: L3 minimum, only at 1080p/1440p with upscaling + FG

Бюджетные пороги (июнь 2026, РФ):
  L1 GPU build:  80-100K
  L2 GPU build: 100-140K
  L3 GPU build: 150-220K
  L3+ (5090):    300K+
"""

from dataclasses import dataclass
from typing import Optional

# Native (no upscaling, no FG) FPS reach per GPU tier × resolution × settings
# Format: tier → resolution → settings → achievable_fps
# Based on B580 benchmarks + extrapolation
NATIVE_FPS = {
    "L1_mainstream": {
        "1080p": {"medium": 90, "high": 70, "ultra": 55},
        "1440p": {"medium": 55, "high": 40, "ultra": 30},
        "4K":    {"medium": 25, "high": 18, "ultra": 12},
    },
    "L2_balanced": {
        "1080p": {"medium": 160, "high": 120, "ultra": 90},
        "1440p": {"medium": 100, "high": 75, "ultra": 55},
        "4K":    {"medium": 45, "high": 35, "ultra": 25},
    },
    "L3_enthusiast": {
        "1080p": {"medium": 240, "high": 180, "ultra": 140},
        "1440p": {"medium": 160, "high": 120, "ultra": 85},
        "4K":    {"medium": 85, "high": 65, "ultra": 50},
    },
}

# Budget estimates: GPU tier → typical build cost range
GPU_TIER_BUDGET = {
    "L1_mainstream":     (80000, 100000),
    "L2_balanced":       (100000, 140000),
    "L3_enthusiast":     (150000, 220000),
}

# Frame Gen multiplier (conservative)
FG_MULTIPLIER = 1.6
# Upscaling: effectively moves you up one resolution tier
# e.g., 1440p with upscaling ≈ 1080p native performance

# Minimum acceptable FPS for "playable"
MIN_PLAYABLE_FPS = 30


@dataclass
class FeasibilityResult:
    feasible: bool
    required_tier: str                # GPU tier needed
    required_tier_label: str          # human-readable
    estimated_fps_native: int         # без upscaling/FG
    estimated_fps_upscaled: int       # с upscaling
    estimated_fps_fg: int             # с Frame Gen
    budget_estimate: tuple[int, int]  # (min, max) для этого тира
    strategies: list[dict]            # trade-off предложения


def evaluate(intent: dict) -> FeasibilityResult:
    """
    intent fields:
      - resolution: "1080p" | "1440p" | "4K"
      - settings: "medium" | "high" | "ultra" | "path_tracing"
      - target_fps: int
      - budget: int
      - allow_upscaling: bool (default True)
      - allow_frame_gen: bool (default True)
      - allow_rt: bool (default False)
    """
    resolution = intent.get("resolution", "1440p")
    settings = intent.get("settings", "high")
    target_fps = intent.get("target_fps", 60)
    budget = intent.get("budget", 999999)
    allow_upscaling = intent.get("allow_upscaling", True)
    allow_frame_gen = intent.get("allow_frame_gen", True)
    allow_rt = intent.get("allow_rt", False)

    # Path tracing requires special handling
    if settings == "path_tracing":
        settings = "ultra"
        allow_rt = True

    strategies = []

    # Find minimum GPU tier that can hit target
    best_tier = None
    best_native = 0

    for tier_name, tier_data in NATIVE_FPS.items():
        res_data = tier_data.get(resolution, {})
        native_fps = res_data.get(settings, 0)

        if allow_rt and tier_name == "L1_mainstream":
            native_fps = int(native_fps * 0.6)  # RT penalty for L1
        elif allow_rt and tier_name == "L2_balanced":
            native_fps = int(native_fps * 0.75)

        upscaled_fps = native_fps
        if allow_upscaling:
            # Upscaling: use one resolution tier lower's FPS
            lower_res = {"4K": "1440p", "1440p": "1080p", "1080p": "1080p"}[resolution]
            upscaled_fps = tier_data.get(lower_res, {}).get(settings, native_fps)

        fg_fps = int(upscaled_fps * FG_MULTIPLIER) if allow_frame_gen else upscaled_fps

        # Can this tier hit target with any strategy?
        can_native = native_fps >= target_fps
        can_upscaled = upscaled_fps >= target_fps
        can_fg = fg_fps >= target_fps

        if can_native or can_upscaled or can_fg:
            best_tier = tier_name
            best_native = native_fps
            break

    if best_tier is None:
        # Nothing can do it — even L3 can't
        l3_data = NATIVE_FPS["L3_enthusiast"][resolution]
        max_native = l3_data.get(settings, 0)
        max_fg = int(max_native * FG_MULTIPLIER)

        return FeasibilityResult(
            feasible=False,
            required_tier="beyond_L3",
            required_tier_label="Выше L3 (RTX 5090 или Multi-GPU)",
            estimated_fps_native=max_native,
            estimated_fps_upscaled=max_native,
            estimated_fps_fg=max_fg,
            budget_estimate=(300000, 999999),
            strategies=[
                {
                    "type": "reduce_requirements",
                    "label": "Снизить требования",
                    "description": f"Снизить target FPS с {target_fps} до {max_fg} (максимум для L3 с Frame Gen). "
                                   f"Или снизить resolution до 1080p.",
                    "new_intent": {**intent, "target_fps": max_fg},
                },
                {
                    "type": "expand_budget",
                    "label": "Увеличить бюджет",
                    "description": f"RTX 5090 (~260K одна карта) + сборка ~350K+. "
                                   f"Текущий бюджет: {budget:,}₽.",
                    "new_intent": {**intent, "budget": 350000},
                },
            ],
        )

    # Check budget
    budget_range = GPU_TIER_BUDGET.get(best_tier, (0, 0))
    budget_ok = budget >= budget_range[0]

    # Calculate actual achievable FPS
    lower_res = {"4K": "1440p", "1440p": "1080p", "1080p": "1080p"}[resolution]
    upscaled_fps = NATIVE_FPS[best_tier].get(lower_res, {}).get(settings, best_native)
    fg_fps = int(upscaled_fps * FG_MULTIPLIER) if allow_frame_gen else upscaled_fps

    feasible = budget_ok and best_native >= target_fps

    if not feasible:
        # Build trade-off strategies
        if not budget_ok:
            strategies.append({
                "type": "expand_budget",
                "label": "Увеличить бюджет",
                "description": f"GPU tier {best_tier} требует бюджет {budget_range[0]:,}–{budget_range[1]:,}₽. "
                               f"Текущий: {budget:,}₽. Не хватает ~{budget_range[0] - budget:,}₽.",
                "new_intent": {**intent, "budget": budget_range[0]},
            })

        if best_native < target_fps:
            # Can we do it with technology?
            if upscaled_fps >= target_fps:
                strategies.append({
                    "type": "tech_cheat_upscaling",
                    "label": "Включить XeSS/DLSS/FSR (Quality)",
                    "description": f"С upscaling: ~{upscaled_fps} fps на {best_tier}. "
                                   f"Качество картинки: 85-90% нативного. Для 1440p → рендер 1080p.",
                    "new_intent": {**intent, "allow_upscaling": True, "target_fps": target_fps},
                })
            elif fg_fps >= target_fps:
                strategies.append({
                    "type": "tech_cheat_fg",
                    "label": "Frame Generation",
                    "description": f"С FG: ~{fg_fps} fps. Input lag +15-20ms. "
                                   f"Нежелательно для киберспорта, допустимо для AAA.",
                    "new_intent": {**intent, "allow_frame_gen": True, "target_fps": target_fps},
                })
            else:
                strategies.append({
                    "type": "reduce_requirements",
                    "label": "Снизить требования",
                    "description": f"С {target_fps} fps до {best_native} fps (native) "
                                   f"или {fg_fps} fps (с FG) на {best_tier}.",
                    "new_intent": {**intent, "target_fps": min(best_native, fg_fps)},
                })

        # Always offer budget expansion
        next_tier_name = {"L1_mainstream": "L2_balanced", "L2_balanced": "L3_enthusiast"}.get(best_tier)
        if next_tier_name and next_tier_name in GPU_TIER_BUDGET:
            next_budget = GPU_TIER_BUDGET[next_tier_name]
            strategies.append({
                "type": "expand_budget",
                "label": f"Перейти на {next_tier_name}",
                "description": f"GPU tier {next_tier_name}: бюджет {next_budget[0]:,}–{next_budget[1]:,}₽.",
                "new_intent": {**intent, "budget": next_budget[0]},
            })

    return FeasibilityResult(
        feasible=feasible and budget_ok,
        required_tier=best_tier,
        required_tier_label={"L1_mainstream": "L1 (RTX 4060 / RX 7600)",
                             "L2_balanced": "L2 (RTX 5070 / RX 9070 / Arc B580)",
                             "L3_enthusiast": "L3 (RTX 5080 / RX 9070 XT)"}.get(best_tier, best_tier),
        estimated_fps_native=best_native,
        estimated_fps_upscaled=upscaled_fps,
        estimated_fps_fg=fg_fps,
        budget_estimate=budget_range,
        strategies=strategies[:3],  # top 3
    )


if __name__ == "__main__":
    import json, sys
    intent = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    result = evaluate(intent)
    print(json.dumps({
        "feasible": result.feasible,
        "required_tier": result.required_tier,
        "required_tier_label": result.required_tier_label,
        "estimated_fps_native": result.estimated_fps_native,
        "estimated_fps_upscaled": result.estimated_fps_upscaled,
        "estimated_fps_fg": result.estimated_fps_fg,
        "budget_estimate": list(result.budget_estimate),
        "strategies": result.strategies,
    }, ensure_ascii=False, indent=2))
