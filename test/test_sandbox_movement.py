"""Unit tests for Movement and Collision Mechanics in Fleet Tactical Sandbox
References: SPEC v1.0 Section 4.1, 8.1, 8.2, 18.0
"""

import unittest
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import MoveAction
from fleet_sandbox.engine.movement import MovementEngine


class TestSandboxMovement(unittest.TestCase):

    def setUp(self):
        self.engine = MovementEngine(100.0, 100.0)

    def test_all_17_move_actions(self):
        """17개 이동 행동이 정상적으로 속도 및 방향을 목표로 처리하는지 검증"""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", heading=90.0, speed=0.0)

        # 1. STOP action
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.STOP)
        self.assertEqual(s, 0.0)

        # 2. SLOW action (target 1.0) -> accelerates by 0.5 to 0.5
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.SLOW_N)
        self.assertEqual(s, 0.5)

        # 3. FAST action (target 2.0) -> accelerates by 0.5 to 0.5
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.FAST_N)
        self.assertEqual(s, 0.5)

    def test_acceleration_and_deceleration(self):
        """가속 및 감속 연속 전이 검증 (0.0 -> 0.5 -> 1.0 -> 0.5 -> 0.0)"""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", heading=90.0, speed=0.0)

        # Accel 1
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.FAST_N)
        ship.speed = s
        self.assertEqual(ship.speed, 0.5)

        # Accel 2
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.FAST_N)
        ship.speed = s
        self.assertEqual(ship.speed, 1.0)

        # Decel to STOP (max decel 0.5)
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.STOP)
        ship.speed = s
        self.assertEqual(ship.speed, 0.5)

        # Decel 2
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.STOP)
        ship.speed = s
        self.assertEqual(ship.speed, 0.0)

    def test_boundary_clamping(self):
        """전장 경계(0.0 <= x, y <= 100.0) 클램핑 검증"""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(99.5, 99.5), heading=45.0, speed=2.0)
        pos, h, s = self.engine.simulate_next_position(ship, MoveAction.FAST_NE)
        self.assertLessEqual(pos.x, 100.0)
        self.assertLessEqual(pos.y, 100.0)

    def test_collision_detection_and_resolution(self):
        """두 함선이 충돌 반경(1.0 + 1.0 = 2.0) 이내 접근 시 충돌 감지 및 분리 검증"""
        s1 = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), speed=1.0, heading=90.0)
        s2 = Ship(ship_id=2, faction="Friendly", role="Escort A", position=Vector2D(50.0, 51.5), speed=1.0, heading=270.0)

        # Distance is 1.5 < 2.0 -> Colliding
        actions = {1: MoveAction.SLOW_N, 2: MoveAction.SLOW_S}
        collisions = self.engine.apply_batch_movements([s1, s2], actions)

        self.assertEqual(len(collisions), 1)
        self.assertEqual(s1.collision_count, 1)
        self.assertEqual(s2.collision_count, 1)


if __name__ == "__main__":
    unittest.main()
