"""Movement Engine and Physics for Fleet Tactical Sandbox
References: SPEC v1.0 Section 3.2, 4.1, 8.1, 8.2
"""

import math
from typing import List, Dict, Tuple, Optional
from fleet_sandbox.models.vector2d import (
    Vector2D,
    normalize_angle_deg,
    shortest_angular_difference_deg,
)
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import MoveAction, MOVE_ACTION_DATA


class MovementEngine:
    """Handles continuous kinematics, turning rate limits, acceleration, and collisions."""

    def __init__(self, world_width: float = 100.0, world_height: float = 100.0):
        self.world_width = world_width
        self.world_height = world_height

    def simulate_next_position(
        self,
        ship: Ship,
        action: MoveAction,
        dt: float = 1.0,
    ) -> Tuple[Vector2D, float, float]:
        """
        Predict next (position, heading, speed) without modifying the ship state.
        Used by AI evaluation and physics updates.
        """
        if ship.is_destroyed:
            return ship.position, ship.heading, 0.0

        target_speed, target_angle = MOVE_ACTION_DATA.get(action, (0.0, None))

        # Clamp target speed to effective maximum speed (damaged core limit)
        effective_target_speed = min(target_speed, ship.effective_max_speed)

        # 1. Turn limits (SPEC 3.2: 45°/sec max)
        current_heading = ship.heading
        if target_angle is not None:
            angle_diff = shortest_angular_difference_deg(target_angle, current_heading)
            max_turn = ship.max_turn_rate * dt
            actual_turn = max(-max_turn, min(max_turn, angle_diff))
            next_heading = normalize_angle_deg(current_heading + actual_turn)
        else:
            next_heading = current_heading

        # 2. Acceleration / Deceleration limits (SPEC 3.2: 0.5 units/sec² max)
        current_speed = ship.speed
        speed_diff = effective_target_speed - current_speed
        max_accel = ship.effective_max_accel * dt
        actual_accel = max(-max_accel, min(max_accel, speed_diff))
        next_speed = max(0.0, min(ship.effective_max_speed, current_speed + actual_accel))

        # 3. Position update along heading
        rad = math.radians(next_heading)
        dx = next_speed * math.cos(rad) * dt
        dy = next_speed * math.sin(rad) * dt
        raw_next_pos = ship.position + Vector2D(dx, dy)

        # 4. Boundary clamping (0.0 <= x <= world_width, 0.0 <= y <= world_height)
        clamped_x = max(0.0, min(self.world_width, raw_next_pos.x))
        clamped_y = max(0.0, min(self.world_height, raw_next_pos.y))
        next_pos = Vector2D(clamped_x, clamped_y)

        return next_pos, next_heading, next_speed

    def apply_batch_movements(
        self,
        ships: List[Ship],
        actions: Dict[int, MoveAction],
        dt: float = 1.0,
    ) -> List[Tuple[int, int]]:
        """
        Compute all next states simultaneously to eliminate ship ID order bias (SPEC 8.1).
        Detect collisions and adjust positions.
        Returns list of (ship_id_1, ship_id_2) collision pairs.
        """
        # Step 1: Compute proposed states
        proposed_states: Dict[int, Tuple[Vector2D, float, float]] = {}
        for ship in ships:
            if ship.is_destroyed:
                proposed_states[ship.ship_id] = (ship.position, ship.heading, 0.0)
            else:
                act = actions.get(ship.ship_id, MoveAction.STOP)
                proposed_states[ship.ship_id] = self.simulate_next_position(ship, act, dt)

        # Step 2: Check collisions among proposed positions (SPEC 8.2)
        # Collision radius = 1.0, so distance < 2.0 triggers collision
        collisions: List[Tuple[int, int]] = []
        ship_lookup = {s.ship_id: s for s in ships}

        for i in range(len(ships)):
            for j in range(i + 1, len(ships)):
                s1 = ships[i]
                s2 = ships[j]
                if s1.is_destroyed or s2.is_destroyed:
                    continue

                pos1 = proposed_states[s1.ship_id][0]
                pos2 = proposed_states[s2.ship_id][0]
                dist = pos1.distance_to(pos2)
                min_safe_dist = s1.collision_radius + s2.collision_radius

                if dist < min_safe_dist:
                    collisions.append((s1.ship_id, s2.ship_id))
                    s1.collision_count += 1
                    s1.collision_ticks += 1
                    s2.collision_count += 1
                    s2.collision_ticks += 1

                    # Separation resolution: push back slightly to prevent penetration
                    overlap = min_safe_dist - dist
                    if dist > 1e-5:
                        push_vec = (pos1 - pos2).normalized() * (overlap * 0.5)
                    else:
                        # Fallback random separation
                        push_vec = Vector2D(overlap * 0.5, 0.0)

                    new_pos1 = Vector2D(
                        max(0.0, min(self.world_width, pos1.x + push_vec.x)),
                        max(0.0, min(self.world_height, pos1.y + push_vec.y)),
                    )
                    new_pos2 = Vector2D(
                        max(0.0, min(self.world_width, pos2.x - push_vec.x)),
                        max(0.0, min(self.world_height, pos2.y - push_vec.y)),
                    )
                    proposed_states[s1.ship_id] = (new_pos1, proposed_states[s1.ship_id][1], proposed_states[s1.ship_id][2] * 0.5)
                    proposed_states[s2.ship_id] = (new_pos2, proposed_states[s2.ship_id][1], proposed_states[s2.ship_id][2] * 0.5)

        # Step 3: Batch apply all updated states
        for ship in ships:
            new_pos, new_heading, new_speed = proposed_states[ship.ship_id]
            ship.position = new_pos
            ship.heading = new_heading
            ship.speed = new_speed

        return collisions
