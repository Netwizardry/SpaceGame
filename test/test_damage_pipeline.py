"""Unit tests for 3-Tier Defense & Damage Pipeline
Spec References:
- docs/spec/ships.md 4.1 & 5.2
"""

import unittest
from spacegame.core.models import ShipInstance, Fleet
from spacegame.core.damage import DamagePipeline


class TestDamagePipeline(unittest.TestCase):

    def setUp(self):
        # Battleship: Shield=100, Armor=150, Structure=50, Total w = 300
        self.ship = ShipInstance(
            ship_class="Battleship",
            max_shield=100.0,
            current_shield=100.0,
            max_armor=150.0,
            current_armor=150.0,
            max_structure=50.0,
            current_structure=50.0,
        )

    def test_shield_only_damage(self):
        """Shield 잔량 내 데미지 흡수 검증"""
        result = DamagePipeline.apply_damage_to_ship(self.ship, 50.0)

        self.assertEqual(result["shield_absorbed"], 50.0)
        self.assertEqual(result["armor_absorbed"], 0.0)
        self.assertEqual(result["structure_damage"], 0.0)
        self.assertEqual(self.ship.current_shield, 50.0)
        self.assertEqual(self.ship.current_armor, 150.0)
        self.assertEqual(self.ship.current_structure, 50.0)
        self.assertFalse(self.ship.is_destroyed)

    def test_shield_break_and_armor_damage(self):
        """Shield 관통 후 Armor 피해 전이 검증 (120 데미지: 실드 100 흡수, 아머 20 흡수)"""
        result = DamagePipeline.apply_damage_to_ship(self.ship, 120.0)

        self.assertEqual(result["shield_absorbed"], 100.0)
        self.assertEqual(result["armor_absorbed"], 20.0)
        self.assertEqual(result["structure_damage"], 0.0)
        self.assertEqual(self.ship.current_shield, 0.0)
        self.assertEqual(self.ship.current_armor, 130.0)
        self.assertEqual(self.ship.current_structure, 50.0)
        self.assertFalse(self.ship.is_destroyed)

    def test_full_penetration_and_ship_destruction(self):
        """Armor 전소 후 Structure 타격 및 함선 격침 판정 검증 (320 데미지: 100 쉴드 + 150 아머 + 50 선체 + 20 잉여)"""
        result = DamagePipeline.apply_damage_to_ship(self.ship, 320.0)

        self.assertEqual(result["shield_absorbed"], 100.0)
        self.assertEqual(result["armor_absorbed"], 150.0)
        self.assertEqual(result["structure_damage"], 50.0)
        self.assertEqual(result["remaining_damage"], 20.0)
        self.assertEqual(self.ship.current_shield, 0.0)
        self.assertEqual(self.ship.current_armor, 0.0)
        self.assertEqual(self.ship.current_structure, 0.0)
        self.assertTrue(self.ship.is_destroyed)

    def test_shield_regeneration(self):
        """턴 종료 시 실드 자동 회복 검증 (docs/spec/ships.md 5.2)"""
        # 쉴드를 25% 잔량(25.0)으로 설정 -> 최대 효율 가중치(1.5배) 적용
        self.ship.current_shield = 25.0
        fleet = Fleet(ships=[self.ship])

        DamagePipeline.regenerate_shields(fleet)
        # 기본 10% * 1.5 = 15.0 회복 -> 25 + 15 = 40.0
        self.assertEqual(self.ship.current_shield, 40.0)


if __name__ == "__main__":
    unittest.main()
