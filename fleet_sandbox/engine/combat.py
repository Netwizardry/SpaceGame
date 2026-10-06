"""Combat Engine for Fleet Tactical Sandbox
References: SPEC v1.0 Section 3.2, 4.2, 8.3, 8.4
"""

import math
import random
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

from fleet_sandbox.models.vector2d import (
    Vector2D,
    normalize_angle_deg,
    shortest_angular_difference_deg,
)
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import AttackAction, ATTACK_BEARING_OFFSET_DEG


@dataclass
class CombatEvent:
    attacker_id: int
    attacker_faction: str
    target_id: int
    target_faction: str
    attack_action: AttackAction
    distance: float
    is_hit: bool
    hit_zone: str
    damage: float
    target_destroyed: bool


class CombatEngine:
    """Handles targeting, firing arcs, hit rolls, 5-zone damage distribution, and destruction."""

    def __init__(self, hit_seed: int = 42, zone_seed: int = 142):
        # Dedicated independent random streams per faction to eliminate order bias (SPEC 8.4)
        self.hit_rng_f = random.Random(hit_seed)
        self.hit_rng_e = random.Random(hit_seed)
        self.zone_rng_f = random.Random(zone_seed)
        self.zone_rng_e = random.Random(zone_seed)

    def reseed(self, hit_seed: int, zone_seed: int) -> None:
        self.hit_rng_f.seed(hit_seed)
        self.hit_rng_e.seed(hit_seed)
        self.zone_rng_f.seed(zone_seed)
        self.zone_rng_e.seed(zone_seed)

    def is_target_in_firing_arc(
        self,
        attacker: Ship,
        target_pos: Vector2D,
        attack_action: AttackAction,
    ) -> bool:
        """
        Check if target is within weapon range (20) and firing arc (±45° relative to mount bearing).
        """
        if attack_action == AttackAction.NONE:
            return False

        dist = attacker.position.distance_to(target_pos)
        if dist > attacker.weapon_range:
            return False

        to_target = target_pos - attacker.position
        bearing_to_target = to_target.angle_deg

        mount_offset = ATTACK_BEARING_OFFSET_DEG.get(attack_action, 0.0)
        mount_bearing = normalize_angle_deg(attacker.heading + mount_offset)

        arc_diff = abs(shortest_angular_difference_deg(bearing_to_target, mount_bearing))
        return arc_diff <= 45.0  # ±45° weapon arc

    def determine_hit_zone(self, attacker_pos: Vector2D, target: Ship, attacker_faction: str = "Friendly") -> str:
        """
        Determine which zone is struck based on incoming vector relative to target heading:
        Front, Left, Right, Rear, or internal Core.
        """
        to_attacker = attacker_pos - target.position
        incoming_angle = to_attacker.angle_deg
        rel_angle = shortest_angular_difference_deg(incoming_angle, target.heading)

        zone_rng = self.zone_rng_f if attacker_faction == "Friendly" else self.zone_rng_e

        # 20% chance of critical core penetration roll (SPEC 3.3)
        if zone_rng.random() < 0.20:
            return "core"

        if abs(rel_angle) <= 45.0:
            return "front"
        elif 45.0 < rel_angle <= 135.0:
            return "left"
        elif -135.0 <= rel_angle < -45.0:
            return "right"
        else:
            return "rear"

    def execute_batch_combat(
        self,
        ships: List[Ship],
        attack_actions: Dict[int, Tuple[AttackAction, Optional[int]]],
    ) -> List[CombatEvent]:
        """
        Execute simultaneous firing for all ships in current tick (SPEC 8.3).
        attack_actions: {attacker_id: (AttackAction, target_ship_id)}
        """
        events: List[CombatEvent] = []
        ship_lookup = {s.ship_id: s for s in ships}

        # Step 1: Collect valid firing declarations
        pending_attacks = []
        for attacker in ships:
            if not attacker.can_fire:
                continue

            action_info = attack_actions.get(attacker.ship_id, (AttackAction.NONE, None))
            attack_action, target_id = action_info

            if attack_action == AttackAction.NONE or target_id is None:
                continue

            target = ship_lookup.get(target_id)
            if not target or target.is_destroyed:
                continue

            # Target must be within detection range and firing arc
            dist = attacker.position.distance_to(target.position)
            if dist > attacker.detection_range:
                continue

            if not self.is_target_in_firing_arc(attacker, target.position, attack_action):
                continue

            pending_attacks.append((attacker, target, attack_action, dist))

        # Step 2: Roll hits and compute damages simultaneously
        damage_buffer: List[Tuple[Ship, str, float, CombatEvent]] = []

        for attacker, target, attack_action, dist in pending_attacks:
            attacker.shots_fired += 1
            attacker.reload_cooldown = attacker.reload_time  # Trigger reload (3 ticks)

            hit_rng = self.hit_rng_f if attacker.faction == "Friendly" else self.hit_rng_e
            # Hit check: base 70% ± 5% random jitter (0.65 ~ 0.75)
            stat_mod = (hit_rng.random() - 0.5) * 0.10  # [-0.05, +0.05]
            eff_hit_prob = max(0.05, min(0.95, attacker.base_hit_rate + stat_mod))
            is_hit = hit_rng.random() < eff_hit_prob

            if is_hit:
                attacker.hits_landed += 1
                hit_zone = self.determine_hit_zone(attacker.position, target, attacker.faction)
                dmg = attacker.base_damage  # 10.0 base damage
                event = CombatEvent(
                    attacker_id=attacker.ship_id,
                    attacker_faction=attacker.faction,
                    target_id=target.ship_id,
                    target_faction=target.faction,
                    attack_action=attack_action,
                    distance=dist,
                    is_hit=True,
                    hit_zone=hit_zone,
                    damage=dmg,
                    target_destroyed=False,  # Updated after batch resolution
                )
                damage_buffer.append((target, hit_zone, dmg, event))
            else:
                event = CombatEvent(
                    attacker_id=attacker.ship_id,
                    attacker_faction=attacker.faction,
                    target_id=target.ship_id,
                    target_faction=target.faction,
                    attack_action=attack_action,
                    distance=dist,
                    is_hit=False,
                    hit_zone="none",
                    damage=0.0,
                    target_destroyed=False,
                )
                events.append(event)

        # Step 3: Apply damage simultaneously
        for target, hit_zone, dmg, event in damage_buffer:
            actual_dmg = target.zones.damage_zone(hit_zone, dmg)
            target.damage_received += actual_dmg
            # Attribute damage to attacker
            attacker = ship_lookup[event.attacker_id]
            attacker.damage_dealt += actual_dmg
            event.target_destroyed = target.is_destroyed
            events.append(event)

        return events
