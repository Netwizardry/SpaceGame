"""Unit tests for Captain AI and Decision Making in Fleet Tactical Sandbox
References: SPEC v1.0 Section 7.0, 9.0, 18.0
"""

import unittest
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import MoveAction, AttackAction
from fleet_sandbox.engine.observation import ObservationSystem
from fleet_sandbox.ai.captain_ai import CaptainAI


class TestSandboxAI(unittest.TestCase):

    def setUp(self):
        self.ai = CaptainAI(mode="C2")

    def test_formation_tracking_move_selection(self):
        """호위함이 진형 목표 좌표를 향해 접근하는 이동 행동을 선택하는지 검증"""
        # Escort A at (50, 40) heading 90°, target at (50, 50) directly North. Current speed 1.0.
        ship = Ship(ship_id=2, faction="Friendly", role="Escort A", position=Vector2D(50.0, 40.0), heading=90.0, speed=1.0)
        target = Vector2D(50.0, 50.0)

        obs = ObservationSystem.generate_observation(
            ship=ship,
            all_friendly_ships=[ship],
            all_enemy_ships=[],
            formation_id="column",
            formation_target=target,
        )

        move_act, reason, breakdown = self.ai.decide_movement(obs)
        # Should choose FAST_N to approach target to the North
        self.assertEqual(move_act, MoveAction.FAST_N)

    def test_collision_avoidance_overrides_formation(self):
        """충돌 위험이 높을 때 진형보다 충돌 회피가 우선 평가되는지 검증 (SPEC 0.0 원칙 3)"""
        # Escort A at (50, 50), target at (50, 55).
        # An ally is blocking at (50, 51.5) directly in front!
        ship = Ship(ship_id=2, faction="Friendly", role="Escort A", position=Vector2D(50.0, 50.0), heading=90.0)
        ally = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 51.5), heading=90.0)
        target = Vector2D(50.0, 55.0)

        obs = ObservationSystem.generate_observation(
            ship=ship,
            all_friendly_ships=[ship, ally],
            all_enemy_ships=[],
            formation_id="column",
            formation_target=target,
        )

        move_act, reason, breakdown = self.ai.decide_movement(obs)
        # Moving FAST_N directly into ally should be rejected due to collision risk
        self.assertNotEqual(move_act, MoveAction.FAST_N)
        self.assertGreater(breakdown["collision_risk"], 0.0)

    def test_attack_selection_in_firing_arc(self):
        """사거리 내에 적이 있을 때 적절한 사각 공격을 선택하는지 검증 (SPEC 7.4)"""
        # Ship heading 90° (North), Enemy at (50, 65) (15 units North)
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), heading=90.0)
        enemy = Ship(ship_id=4, faction="Enemy", role="Flagship", position=Vector2D(50.0, 65.0))

        obs = ObservationSystem.generate_observation(
            ship=ship,
            all_friendly_ships=[ship],
            all_enemy_ships=[enemy],
            formation_id="column",
            formation_target=Vector2D(50.0, 50.0),
        )

        atk_act, target_id = self.ai.decide_attack(obs)
        self.assertEqual(atk_act, AttackAction.FRONT)
        self.assertEqual(target_id, 4)

    def test_non_omniscience_enemy_outside_detection_ignored(self):
        """탐지 거리(30.0) 밖의 적은 AI 관측에 포함되지 않음을 검증 (SPEC 0.0 원칙 6 & 18.0)"""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 20.0))
        # Enemy at y=60 (distance 40 > 30)
        enemy = Ship(ship_id=4, faction="Enemy", role="Flagship", position=Vector2D(50.0, 60.0))

        obs = ObservationSystem.generate_observation(
            ship=ship,
            all_friendly_ships=[ship],
            all_enemy_ships=[enemy],
            formation_id="column",
            formation_target=Vector2D(50.0, 20.0),
        )

        self.assertEqual(len(obs.detected_enemies), 0)
        atk_act, target_id = self.ai.decide_attack(obs)
        self.assertEqual(atk_act, AttackAction.NONE)
        self.assertIsNone(target_id)


if __name__ == "__main__":
    unittest.main()
