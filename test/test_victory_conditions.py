"""Unit tests for Combat Victory Conditions
Spec References:
- docs/spec/combat.md 6.0
"""

import unittest
from spacegame.core.models import Fleet, ShipInstance
from spacegame.core.combat_engine import CombatEngine


class TestVictoryConditions(unittest.TestCase):

    def test_total_victory_by_grand_admiral_flagship_destruction(self):
        """적 총사령함대 격침 시 즉시 완전 승리(Total Victory) 달성 검증 (docs/spec/combat.md 6.0)"""
        # Fleet B is Grand Admiral Fleet
        flagship_b = ShipInstance(ship_class="Battleship", is_flagship=True)
        escort_b = ShipInstance(ship_class="Frigate")
        fleet_b = Fleet(
            name="Enemy Imperial Grand Fleet",
            is_grand_admiral=True,
            ships=[flagship_b, escort_b],
        )

        fleet_a = Fleet(
            name="Allied Task Force",
            ships=[ShipInstance(ship_class="Titan")],
        )

        engine = CombatEngine(fleet_a, fleet_b)

        # 기함이 아직 살아있으면 종료되지 않음
        self.assertIsNone(engine.check_victory())

        # 적 기함 파괴
        flagship_b.current_structure = 0.0

        report = engine.check_victory()
        self.assertIsNotNone(report)
        self.assertTrue(report.is_ended)
        self.assertEqual(report.winner, "Fleet A")
        self.assertEqual(report.victory_type, "Total Victory")

    def test_partial_victory_by_vp_comparison(self):
        """제한 턴 종료 시 VP 가중치에 따른 판정 승리(Partial Victory) 검증 (docs/spec/combat.md 6.2)
        가중치: Doom Star(100), Titan(50), Battleship(20), Frigate(5)
        """
        fleet_a = Fleet(ships=[ShipInstance(ship_class="Battleship")])
        fleet_b = Fleet(ships=[ShipInstance(ship_class="Titan")])

        engine = CombatEngine(fleet_a, fleet_b, max_tactical_turns=12)
        engine.current_turn = 12  # 시간 종료

        # 아군 손실: Frigate 2척 (2 * 5 = 10)
        # 적군 격침: Battleship 1척 (20)
        engine.lost_ships_a = ["Frigate", "Frigate"]
        engine.lost_ships_b = ["Battleship"]

        # A의 VP = 적 격침 20 - 아군 손실 10 = +10
        # B의 VP = 적 격침 10 - 아군 손실 20 = -10
        vp_a = engine.calculate_vp(engine.lost_ships_a, engine.lost_ships_b)
        vp_b = engine.calculate_vp(engine.lost_ships_b, engine.lost_ships_a)

        self.assertEqual(vp_a, 10)
        self.assertEqual(vp_b, -10)

        report = engine.check_victory()
        self.assertIsNotNone(report)
        self.assertTrue(report.is_ended)
        self.assertEqual(report.winner, "Fleet A")
        self.assertEqual(report.victory_type, "Partial Victory")
        self.assertEqual(report.vp_a, 10)
        self.assertEqual(report.vp_b, -10)


if __name__ == "__main__":
    unittest.main()
