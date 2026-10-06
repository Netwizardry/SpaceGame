"""Ship Model and 5-Zone Damage System for Fleet Tactical Sandbox
References: SPEC v1.0 Section 3.0 & 3.3, 3.4
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from fleet_sandbox.models.vector2d import Vector2D, normalize_angle_deg


@dataclass
class DamageZones:
    """5-Zone Damage System: Front, Left, Right, Rear, Core (SPEC 3.3)"""
    front: float = 100.0
    left: float = 100.0
    right: float = 100.0
    rear: float = 100.0
    core: float = 100.0
    max_hp_per_zone: float = 100.0

    @property
    def core_damage_rate(self) -> float:
        """Damage rate of core from 0.0 (healthy) to 1.0 (destroyed)."""
        rate = (self.max_hp_per_zone - max(0.0, self.core)) / self.max_hp_per_zone
        return min(1.0, max(0.0, rate))

    @property
    def total_hp(self) -> float:
        return (
            max(0.0, self.front)
            + max(0.0, self.left)
            + max(0.0, self.right)
            + max(0.0, self.rear)
            + max(0.0, self.core)
        )

    @property
    def is_all_destroyed(self) -> bool:
        return (
            self.front <= 0.0
            and self.left <= 0.0
            and self.right <= 0.0
            and self.rear <= 0.0
            and self.core <= 0.0
        )

    def damage_zone(self, zone_name: str, damage_amount: float) -> float:
        """Apply damage to named zone. Returns actual damage dealt."""
        if not hasattr(self, zone_name):
            zone_name = "core"
        current = getattr(self, zone_name)
        actual = min(current, damage_amount)
        setattr(self, zone_name, max(0.0, current - actual))
        return actual

    def to_dict(self) -> Dict[str, float]:
        return {
            "front": round(self.front, 2),
            "left": round(self.left, 2),
            "right": round(self.right, 2),
            "rear": round(self.rear, 2),
            "core": round(self.core, 2),
            "core_damage_rate": round(self.core_damage_rate, 4),
        }


@dataclass
class Ship:
    """Destroyer Ship Model for Fleet Tactical Sandbox"""
    ship_id: int          # 1: Flagship, 2: Escort A, 3: Escort B
    faction: str          # "Friendly" or "Enemy"
    role: str             # "Flagship", "Escort A", "Escort B"

    # Physics State
    position: Vector2D = field(default_factory=lambda: Vector2D(0.0, 0.0))
    heading: float = 90.0  # Angle in degrees [0, 360), +X=0°, +Y=90°
    speed: float = 0.0

    # Base Stats (SPEC 3.2)
    base_max_speed: float = 2.0
    slow_speed: float = 1.0
    base_max_accel: float = 0.5
    max_turn_rate: float = 45.0
    collision_radius: float = 1.0
    weapon_range: float = 20.0
    reload_time: int = 3
    base_hit_rate: float = 0.70
    detection_range: float = 30.0
    base_damage: float = 10.0

    # Health & Combat State
    zones: DamageZones = field(default_factory=DamageZones)
    reload_cooldown: int = 0
    shots_fired: int = 0
    hits_landed: int = 0
    damage_dealt: float = 0.0
    damage_received: float = 0.0

    # Formation Tracking
    formation_target: Optional[Vector2D] = None
    formation_error: float = 0.0
    is_out_of_formation: bool = False
    departure_reason: Optional[str] = None
    time_in_formation_tolerance: int = 0  # Count of consecutive ticks within tolerance <= 2.0

    # Collision & Anomaly Tracking
    collision_count: int = 0
    collision_ticks: int = 0

    @property
    def is_flagship(self) -> bool:
        return self.role == "Flagship"

    @property
    def is_destroyed(self) -> bool:
        """
        격침 조건 (SPEC 3.4):
        - 코어 손상률 100% 도달 (Core HP <= 0)
        - 또는 전체 5구역이 모두 100% 손상
        """
        return self.zones.core <= 0.0 or self.zones.is_all_destroyed

    @property
    def effective_max_speed(self) -> float:
        """코어 손상률에 비례한 최대 속도 감속 (SPEC 3.3)"""
        factor = 1.0 - self.zones.core_damage_rate
        return max(0.0, self.base_max_speed * factor)

    @property
    def effective_max_accel(self) -> float:
        """코어 손상률에 비례한 가속도 저하 (SPEC 3.3)"""
        factor = 1.0 - self.zones.core_damage_rate
        return max(0.0, self.base_max_accel * factor)

    @property
    def can_fire(self) -> bool:
        return not self.is_destroyed and self.reload_cooldown <= 0

    def tick_reload(self) -> None:
        if self.reload_cooldown > 0:
            self.reload_cooldown -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ship_id": self.ship_id,
            "faction": self.faction,
            "role": self.role,
            "is_flagship": self.is_flagship,
            "is_destroyed": self.is_destroyed,
            "x": round(self.position.x, 3),
            "y": round(self.position.y, 3),
            "heading": round(normalize_angle_deg(self.heading), 2),
            "speed": round(self.speed, 3),
            "zones": self.zones.to_dict(),
            "reload_cooldown": self.reload_cooldown,
            "formation_target": (
                {"x": round(self.formation_target.x, 3), "y": round(self.formation_target.y, 3)}
                if self.formation_target
                else None
            ),
            "formation_error": round(self.formation_error, 3),
            "is_out_of_formation": self.is_out_of_formation,
            "departure_reason": self.departure_reason,
        }
