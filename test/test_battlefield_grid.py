"""Unit tests for Battlefield Grid & Terrain Mechanics
Spec References:
- docs/spec/battlefield.md 1.0 & 2.0
- docs/spec/combat.md 5.1
"""

import unittest
from spacegame.core.models import Position, Fleet, ShipInstance, Commander
from spacegame.core.grid import TacticalGrid
from spacegame.core.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    TERRAIN_EFFECTS,
)


class TestBattlefieldGrid(unittest.TestCase):

    def setUp(self):
        self.grid = TacticalGrid()

    def test_grid_dimensions(self):
        """100 x 100 전술 사각 그리드 규격 검증"""
        self.assertEqual(self.grid.width, 100)
        self.assertEqual(self.grid.height, 100)
        self.assertTrue(self.grid.is_valid_position(Position(0, 0)))
        self.assertTrue(self.grid.is_valid_position(Position(99, 99)))
        self.assertFalse(self.grid.is_valid_position(Position(100, 100)))

    def test_deployment_zones(self):
        """배치 영역: 공격측 Top 20% (y: 0~19), 방어측 Bottom 20% (y: 80~99) 검증"""
        self.assertTrue(self.grid.is_attacker_deployment_zone(Position(50, 0)))
        self.assertTrue(self.grid.is_attacker_deployment_zone(Position(50, 19)))
        self.assertFalse(self.grid.is_attacker_deployment_zone(Position(50, 20)))

        self.assertFalse(self.grid.is_defender_deployment_zone(Position(50, 79)))
        self.assertTrue(self.grid.is_defender_deployment_zone(Position(50, 80)))
        self.assertTrue(self.grid.is_defender_deployment_zone(Position(50, 99)))

    def test_terrain_modifiers(self):
        """지형별 이동 비용 및 명중률 보정치 검증 (docs/spec/battlefield.md 2.0)"""
        # 성운 (Nebula)
        self.grid.set_terrain(10, 10, "Nebula")
        self.assertEqual(self.grid.get_movement_cost(Position(10, 10)), 1.5)
        self.assertEqual(self.grid.get_hit_modifier(Position(10, 10)), -0.25)

        # 소행성대 (Asteroid)
        self.grid.set_terrain(20, 20, "Asteroid")
        self.assertEqual(self.grid.get_movement_cost(Position(20, 20)), 2.0)
        self.assertEqual(self.grid.get_hit_modifier(Position(20, 20)), -0.10)

    def test_black_hole_pull(self):
        """블랙홀 5 Grid 이내 견인 로직 검증 (docs/spec/battlefield.md 2.0)"""
        # 블랙홀을 (50, 50)에 배치
        self.grid.set_terrain(50, 50, "Black Hole")

        # 함선이 (50, 48)에 위치 (거리 2 Grid <= 5 Grid)
        ship = ShipInstance(position=Position(50, 48))
        new_pos = self.grid.apply_black_hole_gravitation(ship)

        # 블랙홀 방향(y 증가)으로 1칸 당겨져야 함 -> (50, 49)
        self.assertIsNotNone(new_pos)
        self.assertEqual(ship.position.y, 49)

    def test_command_radius_and_out_of_range(self):
        """기함 LDR에 따른 지휘 반경 및 낙오 판정 검증 (docs/spec/combat.md 5.1)"""
        admiral = Commander(ldr=50.0)  # LDR 50 -> 반경 max(5.0, 50 * 0.2) = 10.0
        flagship = ShipInstance(is_flagship=True, position=Position(10, 10))
        wing_ship_near = ShipInstance(position=Position(15, 10))  # 거리 5 <= 10
        wing_ship_far = ShipInstance(position=Position(30, 10))   # 거리 20 > 10

        fleet = Fleet(
            commander=admiral,
            ships=[flagship, wing_ship_near, wing_ship_far],
        )

        out_of_range = self.grid.update_command_and_control(fleet)

        self.assertIn(wing_ship_far, out_of_range)
        self.assertNotIn(wing_ship_near, out_of_range)
        # 낙오 패널티: 적극성 0, 사기 저하
        self.assertEqual(wing_ship_far.aggressiveness, 0.0)
        self.assertLessEqual(wing_ship_far.morale, 50.0)


if __name__ == "__main__":
    unittest.main()
