"""Observation System for Fleet Tactical Sandbox
References: SPEC v1.0 Section 7.1 & 14.7 (Non-omniscience)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship, DamageZones


@dataclass
class EnemyObservation:
    """Observed enemy contact. Only includes position, heading estimate, and distance."""
    ship_id: int
    faction: str
    position: Vector2D
    distance: float
    bearing_deg: float  # Absolute angle from observer to enemy


@dataclass
class ShipObservation:
    """Information visible to CaptainAI (SPEC 7.1)"""
    ship_id: int
    faction: str
    is_flagship: bool
    position: Vector2D
    speed: float
    heading: float
    effective_max_speed: float
    effective_max_accel: float
    can_fire: bool
    reload_cooldown: int

    # Friendly fleet observations (Positions and alive status)
    friendly_positions: Dict[int, Vector2D]
    flagship_position: Optional[Vector2D]
    flagship_heading: Optional[float]

    # Sensor contacts (Only within detection_range)
    detected_enemies: List[EnemyObservation]

    # Formation targets
    formation_id: str
    formation_target: Vector2D
    formation_error: float

    # Self damage status (internal only to self)
    zones: DamageZones


class ObservationSystem:
    """Filters true world state into ship-specific observations."""

    @staticmethod
    def generate_observation(
        ship: Ship,
        all_friendly_ships: List[Ship],
        all_enemy_ships: List[Ship],
        formation_id: str,
        formation_target: Vector2D,
    ) -> ShipObservation:
        friendly_pos: Dict[int, Vector2D] = {}
        flagship_pos: Optional[Vector2D] = None
        flagship_head: Optional[float] = None

        for ally in all_friendly_ships:
            if not ally.is_destroyed:
                friendly_pos[ally.ship_id] = ally.position
                if ally.is_flagship:
                    flagship_pos = ally.position
                    flagship_head = ally.heading

        # Detect enemies within detection_range (SPEC 3.2: 30 units)
        detected: List[EnemyObservation] = []
        for enemy in all_enemy_ships:
            if enemy.is_destroyed:
                continue
            dist = ship.position.distance_to(enemy.position)
            if dist <= ship.detection_range:
                vec_to_enemy = enemy.position - ship.position
                bearing = vec_to_enemy.angle_deg
                detected.append(
                    EnemyObservation(
                        ship_id=enemy.ship_id,
                        faction=enemy.faction,
                        position=enemy.position,
                        distance=dist,
                        bearing_deg=bearing,
                    )
                )

        # Sort detected enemies by distance (closest first)
        detected.sort(key=lambda e: e.distance)

        form_err = ship.position.distance_to(formation_target)

        return ShipObservation(
            ship_id=ship.ship_id,
            faction=ship.faction,
            is_flagship=ship.is_flagship,
            position=ship.position,
            speed=ship.speed,
            heading=ship.heading,
            effective_max_speed=ship.effective_max_speed,
            effective_max_accel=ship.effective_max_accel,
            can_fire=ship.can_fire,
            reload_cooldown=ship.reload_cooldown,
            friendly_positions=friendly_pos,
            flagship_position=flagship_pos,
            flagship_heading=flagship_head,
            detected_enemies=detected,
            formation_id=formation_id,
            formation_target=formation_target,
            formation_error=form_err,
            zones=ship.zones,
        )
