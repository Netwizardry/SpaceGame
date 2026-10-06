"""Captain AI Implementation for Fleet Tactical Sandbox
References: SPEC v1.0 Section 6.0, 7.0, 9.0 (C0, C1, C2 Control Groups)
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from fleet_sandbox.models.vector2d import (
    Vector2D,
    normalize_angle_deg,
    shortest_angular_difference_deg,
)
from fleet_sandbox.models.actions import (
    MoveAction,
    AttackAction,
    MOVE_ACTION_DATA,
    ATTACK_BEARING_OFFSET_DEG,
)
from fleet_sandbox.engine.observation import ShipObservation, EnemyObservation


class CaptainAI:
    """Rule-based tactical Captain AI evaluating candidates via multi-objective scoring."""

    def __init__(
        self,
        mode: str = "C2",  # "C0": No formation, "C1": Rigid, "C2": Flexible
        wF: float = 1.5,
        wC: float = 10.0,
        wT: float = 2.0,
        wB: float = 8.0,
        broadside_aware: bool = False,
        inertia_weight: float = 1.0,
    ):
        self.mode = mode
        self.broadside_aware = broadside_aware
        self.inertia_weight = inertia_weight
        self.last_actions: Dict[int, MoveAction] = {}

        if mode == "C0":
            self.wF = 0.0
            self.wC = wC
            self.wT = wT * 2.0
            self.wB = wB
        elif mode == "C1":
            self.wF = 50.0  # Dominant formation tracking
            self.wC = wC
            self.wT = 0.0   # Ignores tactical opportunity for formation
            self.wB = wB
        else:  # C2: Flexible
            self.wF = wF
            self.wC = wC
            self.wT = wT
            self.wB = wB

    def predict_next_position(
        self,
        obs: ShipObservation,
        action: MoveAction,
        dt: float = 1.0,
    ) -> Tuple[Vector2D, float, float]:
        """Simple kinematic prediction for AI evaluation."""
        target_speed, target_angle = MOVE_ACTION_DATA[action]
        eff_speed = min(target_speed, obs.effective_max_speed)

        heading = obs.heading
        if target_angle is not None:
            diff = shortest_angular_difference_deg(target_angle, heading)
            max_turn = 45.0 * dt
            actual_turn = max(-max_turn, min(max_turn, diff))
            next_heading = normalize_angle_deg(heading + actual_turn)
        else:
            next_heading = heading

        # Speed adjustment
        speed_diff = eff_speed - obs.speed
        max_accel = obs.effective_max_accel * dt
        actual_accel = max(-max_accel, min(max_accel, speed_diff))
        next_speed = max(0.0, min(obs.effective_max_speed, obs.speed + actual_accel))

        rad = math.radians(next_heading)
        next_x = obs.position.x + next_speed * math.cos(rad) * dt
        next_y = obs.position.y + next_speed * math.sin(rad) * dt
        return Vector2D(next_x, next_y), next_heading, next_speed

    def choose_flagship_movement(self, obs: ShipObservation) -> MoveAction:
        """
        Flagship movement: navigates towards objective / maintains engagement range (SPEC 6.2).
        Does not chase its own (0,0) relative formation point.
        """
        if obs.detected_enemies:
            closest_enemy = obs.detected_enemies[0]
            to_enemy = closest_enemy.position - obs.position
            dist = to_enemy.length
            target_angle = to_enemy.angle_deg

            # Ideal standoff engagement distance: 15.0 ~ 18.0 units
            if dist > 18.0:
                act = self._closest_8dir_action(target_angle, fast=True)
            elif dist < 12.0:
                away_angle = normalize_angle_deg(target_angle + 180.0)
                act = self._closest_8dir_action(away_angle, fast=False)
            else:
                # Maintain stance / broadside
                if self.broadside_aware:
                    side1 = normalize_angle_deg(target_angle + 90.0)
                    side2 = normalize_angle_deg(target_angle - 90.0)
                    turn1 = abs(shortest_angular_difference_deg(side1, obs.heading))
                    turn2 = abs(shortest_angular_difference_deg(side2, obs.heading))
                    best_side = side1 if turn1 <= turn2 else side2
                    act = self._closest_8dir_action(best_side, fast=False)
                else:
                    side_angle = normalize_angle_deg(target_angle + 90.0)
                    act = self._closest_8dir_action(side_angle, fast=False)
            self.last_actions[obs.ship_id] = act
            return act
        else:
            # Non-combat cruising: slow speed (1.0) so escorts (max 2.0) can assemble into formation
            advance_angle = 90.0 if obs.faction == "Friendly" else 270.0
            act = self._closest_8dir_action(advance_angle, fast=False)
            self.last_actions[obs.ship_id] = act
            return act

    def _closest_8dir_action(self, target_angle: float, fast: bool = False) -> MoveAction:
        """Helper to pick closest 8-direction move action."""
        angles = [
            (0.0, MoveAction.FAST_E if fast else MoveAction.SLOW_E),
            (45.0, MoveAction.FAST_NE if fast else MoveAction.SLOW_NE),
            (90.0, MoveAction.FAST_N if fast else MoveAction.SLOW_N),
            (135.0, MoveAction.FAST_NW if fast else MoveAction.SLOW_NW),
            (180.0, MoveAction.FAST_W if fast else MoveAction.SLOW_W),
            (225.0, MoveAction.FAST_SW if fast else MoveAction.SLOW_SW),
            (270.0, MoveAction.FAST_S if fast else MoveAction.SLOW_S),
            (315.0, MoveAction.FAST_SE if fast else MoveAction.SLOW_SE),
        ]
        best_act = angles[0][1]
        min_diff = 999.0
        for ang, act in angles:
            diff = abs(shortest_angular_difference_deg(ang, target_angle))
            if diff < min_diff:
                min_diff = diff
                best_act = act
        return best_act

    def evaluate_move_score(
        self,
        obs: ShipObservation,
        action: MoveAction,
    ) -> Tuple[float, Dict[str, float]]:
        pred_pos, pred_heading, pred_speed = self.predict_next_position(obs, action)

        # 1. Formation Error
        if self.mode == "C0":
            formation_error = 0.0
        else:
            form_dist = pred_pos.distance_to(obs.formation_target)
            # Hysteresis with slight gradient towards center (SPEC 6.3)
            if form_dist <= 2.0:
                formation_error = form_dist * 0.05  # gentle preference for center
            elif form_dist <= 4.0:
                formation_error = 0.1 + (form_dist - 2.0) * 0.5  # mild return
            else:
                formation_error = 1.1 + (form_dist - 4.0) * 1.0  # active return

        # 2. Collision Risk
        collision_risk = 0.0
        for ally_id, ally_pos in obs.friendly_positions.items():
            if ally_id == obs.ship_id:
                continue
            dist = pred_pos.distance_to(ally_pos)
            if dist < 2.2:  # Danger zone
                collision_risk += (2.2 - dist) * 10.0
            elif dist < 4.0:
                collision_risk += (4.0 - dist) * 1.5

        for enemy in obs.detected_enemies:
            dist = pred_pos.distance_to(enemy.position)
            if dist < 2.5:
                collision_risk += (2.5 - dist) * 8.0

        # 3. Tactical Value (Engagement & Weapon Coverage)
        tactical_value = 0.0
        if obs.detected_enemies:
            closest_enemy = obs.detected_enemies[0]
            dist = pred_pos.distance_to(closest_enemy.position)
            # Reward staying within optimal weapon range [12.0, 20.0]
            if 12.0 <= dist <= 20.0:
                tactical_value += 3.0
            elif dist < 12.0:
                tactical_value -= (12.0 - dist) * 0.5  # Avoid getting too close
            elif dist <= 30.0:
                tactical_value += max(0.0, 1.0 - (dist - 20.0) * 0.1)

            # Check if predicted heading allows front or broadside firing at enemy
            to_enemy = closest_enemy.position - pred_pos
            rel_bearing = shortest_angular_difference_deg(to_enemy.angle_deg, pred_heading)
            is_front = abs(rel_bearing) <= 45.0
            is_side = abs(abs(rel_bearing) - 90.0) <= 45.0

            if self.broadside_aware:
                # Broadside-aware AI heavily rewards crossing the T and side-firing stances
                if is_side:
                    tactical_value += 3.5
                elif is_front:
                    tactical_value += 1.5
            else:
                if is_front or is_side:
                    tactical_value += 1.5

        # 4. Boundary Risk (0 <= x <= 100, 0 <= y <= 100)
        boundary_risk = 0.0
        margin = 6.0
        if pred_pos.x < margin:
            boundary_risk += (margin - pred_pos.x) * 2.0
        elif pred_pos.x > (100.0 - margin):
            boundary_risk += (pred_pos.x - (100.0 - margin)) * 2.0

        if pred_pos.y < margin:
            boundary_risk += (margin - pred_pos.y) * 2.0
        elif pred_pos.y > (100.0 - margin):
            boundary_risk += (pred_pos.y - (100.0 - margin)) * 2.0

        # 5. Action Inertia / Reversal Penalty (SPEC 12.5 & Oscillation damping)
        inertia_penalty = 0.0
        last_act = self.last_actions.get(obs.ship_id)
        if last_act is not None and last_act != MoveAction.STOP and action != MoveAction.STOP:
            last_ang = MOVE_ACTION_DATA[last_act][1]
            act_ang = MOVE_ACTION_DATA[action][1]
            if last_ang is not None and act_ang is not None:
                ang_diff = abs(shortest_angular_difference_deg(last_ang, act_ang))
                if ang_diff > 135.0:  # Direct reversal
                    inertia_penalty = self.inertia_weight

        total_score = (
            - self.wF * formation_error
            - self.wC * collision_risk
            + self.wT * tactical_value
            - self.wB * boundary_risk
            - inertia_penalty
        )

        breakdown = {
            "formation_error": formation_error,
            "collision_risk": collision_risk,
            "tactical_value": tactical_value,
            "boundary_risk": boundary_risk,
            "inertia_penalty": inertia_penalty,
            "total_score": total_score,
        }
        return total_score, breakdown

    def decide_movement(self, obs: ShipObservation) -> Tuple[MoveAction, str, Dict[str, Any]]:
        """Choose best move action using multi-objective scoring (SPEC 7.2 & 7.3)."""
        if obs.is_flagship:
            action = self.choose_flagship_movement(obs)
            return action, "FLAGSHIP_OBJECTIVE", {}

        best_action = MoveAction.STOP
        best_score = -float("inf")
        best_breakdown: Dict[str, Any] = {}

        # Evaluate all 17 move actions with symmetric tie-break
        for act in MoveAction:
            score, breakdown = self.evaluate_move_score(obs, act)
            if score > best_score + 1e-5:
                best_score = score
                best_action = act
                best_breakdown = breakdown
            elif abs(score - best_score) <= 1e-5:
                # Tie-break: prefer action that requires minimal turn from current heading
                act_ang = MOVE_ACTION_DATA[act][1]
                best_ang = MOVE_ACTION_DATA[best_action][1]
                diff_act = abs(shortest_angular_difference_deg(act_ang, obs.heading)) if act_ang is not None else 0.0
                diff_best = abs(shortest_angular_difference_deg(best_ang, obs.heading)) if best_ang is not None else 0.0
                if diff_act < diff_best:
                    best_action = act
                    best_breakdown = breakdown

        self.last_actions[obs.ship_id] = best_action

        # Determine departure reason if out of tolerance (SPEC 6.4)
        reason = "IN_FORMATION"
        if obs.formation_error > 2.0:
            if best_breakdown.get("collision_risk", 0.0) > 1.0:
                reason = "COLLISION_AVOIDANCE"
            elif best_breakdown.get("tactical_value", 0.0) > 2.0:
                reason = "TACTICAL_ENGAGEMENT"
            elif best_breakdown.get("boundary_risk", 0.0) > 1.0:
                reason = "BOUNDARY_AVOIDANCE"
            elif obs.effective_max_speed < 1.5:
                reason = "CORE_DAMAGED"
            else:
                reason = "APPROACHING_FORMATION"

        return best_action, reason, best_breakdown

    def decide_attack(self, obs: ShipObservation) -> Tuple[AttackAction, Optional[int]]:
        """Choose target and attack arc (SPEC 7.4)."""
        if not obs.can_fire or not obs.detected_enemies:
            return AttackAction.NONE, None

        # Check candidate targets within weapon range 20.0
        candidate_targets = [e for e in obs.detected_enemies if e.distance <= 20.0]
        if not candidate_targets:
            return AttackAction.NONE, None

        # Nearest target
        target = candidate_targets[0]
        to_target = target.position - obs.position
        bearing = to_target.angle_deg

        # Test arcs: FRONT (0°), LEFT (+90°), RIGHT (-90°), REAR (180°)
        arcs = [
            (AttackAction.FRONT, 0.0),
            (AttackAction.LEFT, 90.0),
            (AttackAction.RIGHT, -90.0),
            (AttackAction.REAR, 180.0),
        ]

        for action, offset in arcs:
            mount_heading = normalize_angle_deg(obs.heading + offset)
            diff = abs(shortest_angular_difference_deg(bearing, mount_heading))
            if diff <= 45.0:
                return action, target.ship_id

        return AttackAction.NONE, None
