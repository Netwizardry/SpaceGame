"""SpaceGame v0.1 Mechanical Constants and Specifications
References:
- docs/spec/combat.md
- docs/spec/ships.md
- docs/spec/battlefield.md
- docs/spec/units.md
- docs/spec/entities.md
"""

from typing import Dict, Any

# ==============================================================================
# 1. 함급별 살보 매개변수 (Salvo Parameters) - docs/spec/ships.md 4.0
# ==============================================================================
SHIP_SALVO_PARAMS: Dict[str, Dict[str, Any]] = {
    "Frigate": {
        "alpha": 5.0,
        "y": 2.0,
        "w": 10.0,
        "shield": 2.0,
        "armor": 3.0,
        "structure": 5.0,
    },
    "Destroyer": {
        "alpha": 15.0,
        "y": 25.0,
        "w": 30.0,
        "shield": 10.0,
        "armor": 10.0,
        "structure": 10.0,
    },
    "Cruiser": {
        "alpha": 40.0,
        "y": 15.0,
        "w": 80.0,
        "shield": 30.0,
        "armor": 30.0,
        "structure": 20.0,
    },
    "Battleship": {
        "alpha": 120.0,
        "y": 30.0,
        "w": 300.0,
        "shield": 100.0,
        "armor": 150.0,
        "structure": 50.0,
    },
    "Titan": {
        "alpha": 350.0,
        "y": 80.0,
        "w": 1200.0,
        "shield": 400.0,
        "armor": 600.0,
        "structure": 200.0,
    },
    "Doom Star": {
        "alpha": 1500.0,
        "y": 400.0,
        "w": 8000.0,
        "shield": 3000.0,
        "armor": 4000.0,
        "structure": 1000.0,
    },
}

# ==============================================================================
# 2. 판정 승리 함급 승점 가중치 (Victory Point Weights) - docs/spec/combat.md 6.2
# ==============================================================================
VP_SHIP_WEIGHTS: Dict[str, int] = {
    "Doom Star": 100,
    "Titan": 50,
    "Battleship": 20,
    "Cruiser": 15,
    "Destroyer": 10,
    "Frigate": 5,
}

# ==============================================================================
# 3. 군수품 소모 규칙 (Ordnance Rules) - docs/spec/combat.md 2.1 & ships.md 4.1
# ==============================================================================
ORDNANCE_PER_VOLLEY = 10  # 1개 부대가 1회 일제 사격 시 즉시 소모하는 군수품 단위

# ==============================================================================
# 4. 전술 그리드 규격 (Tactical Grid) - docs/spec/battlefield.md 1.0
# ==============================================================================
GRID_WIDTH = 100
GRID_HEIGHT = 100
GRID_RESOLUTION_KM = 1000

# 배치 영역 (Top 20%, Bottom 20%)
ATTACKER_DEPLOYMENT_Y_MIN = 0
ATTACKER_DEPLOYMENT_Y_MAX = 19
DEFENDER_DEPLOYMENT_Y_MIN = 80
DEFENDER_DEPLOYMENT_Y_MAX = 99
NEUTRAL_ZONE_Y_MIN = 20
NEUTRAL_ZONE_Y_MAX = 79

# ==============================================================================
# 5. 지형 효과 (Terrain Effects) - docs/spec/battlefield.md 2.0
# ==============================================================================
TERRAIN_EFFECTS: Dict[str, Dict[str, Any]] = {
    "Empty": {
        "move_cost": 1.0,
        "hit_modifier": 0.0,
        "stealth": False,
        "hazard_damage": 0.0,
        "traversable": True,
    },
    "Nebula": {
        "move_cost": 1.5,
        "hit_modifier": -0.25,
        "stealth": True,
        "hazard_damage": 0.0,
        "traversable": True,
    },
    "Asteroid": {
        "move_cost": 2.0,
        "hit_modifier": -0.10,
        "stealth": False,
        "hazard_damage": 5.0,
        "traversable": True,
    },
    "Black Hole": {
        "move_cost": float("inf"),
        "hit_modifier": 0.0,
        "stealth": False,
        "hazard_damage": float("inf"),
        "traversable": False,
        "pull_radius": 5,
    },
    "Space Current": {
        "move_cost": 0.5,  # 순방향 기준 기본값
        "hit_modifier": 0.0,
        "stealth": False,
        "hazard_damage": 0.0,
        "traversable": True,
    },
}

# ==============================================================================
# 6. 승무원 숙련도 (Crew Rank Modifiers) - docs/spec/units.md 2.2
# ==============================================================================
CREW_RANK_MODIFIERS: Dict[str, Dict[str, float]] = {
    "Green": {"performance": 0.8, "morale_loss_reduction": 0.0, "ap_discount": 0.0},
    "Regular": {"performance": 1.0, "morale_loss_reduction": 0.0, "ap_discount": 0.0},
    "Veteran": {"performance": 1.1, "morale_loss_reduction": 0.10, "ap_discount": 0.0},
    "Elite": {"performance": 1.25, "morale_loss_reduction": 0.25, "ap_discount": 0.0},
    "Heroic": {"performance": 1.5, "morale_loss_reduction": 0.25, "ap_discount": 0.20},
}
