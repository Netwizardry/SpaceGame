"""Unit tests for Salvo Combat Calculus
Spec References:
- docs/spec/combat.md 7.0
- docs/spec/ships.md 4.0
"""

import unittest
from spacegame.core.models import Fleet, ShipInstance, Commander, Position
from spacegame.core.salvo import SalvoEngine
from spacegame.core.constants import SHIP_SALVO_PARAMS


class TestSalvoEngine(unittest.TestCase):

    def setUp(self):
        # 1 Battleship: alpha=120, y=30, w=300 (Shield: 100, Armor: 150, Structure: 50)
        self.battleship = ShipInstance(
            ship_class="Battleship",
            aggressiveness=100.0,
            ordnance_stock=100,
        )
        # 1 Cruiser: alpha=40, y=15, w=80 (Shield: 30, Armor: 30, Structure: 20)
        self.cruiser = ShipInstance(
            ship_class="Cruiser",
            aggressiveness=100.0,
            ordnance_stock=100,
        )

        self.fleet_a = Fleet(
            name="Red Battleship Fleet",
            faction="Red",
            ships=[self.battleship],
            shared_ordnance=1000,
        )
        self.fleet_b = Fleet(
            name="Blue Cruiser Fleet",
            faction="Blue",
            ships=[self.cruiser],
            shared_ordnance=1000,
        )

    def test_salvo_base_parameters(self):
        """명세의 함급별 살보 기본 파라미터가 정확히 매핑되는지 검증"""
        bs_spec = SHIP_SALVO_PARAMS["Battleship"]
        self.assertEqual(bs_spec["alpha"], 120.0)
        self.assertEqual(bs_spec["y"], 30.0)
        self.assertEqual(bs_spec["w"], 300.0)
        self.assertEqual(bs_spec["shield"], 100.0)
        self.assertEqual(bs_spec["armor"], 150.0)
        self.assertEqual(bs_spec["structure"], 50.0)

    def test_salvo_formula_execution(self):
        """살보 기본 방정식 및 결과값 연산 검증:
        ΔB = -(alpha_eff * A - z_eff * B) * v
        A = 1 Battleship (alpha=120, y=30, w=300), Agg=100, no commander bonus
        B = 1 Cruiser (beta=40, z=15, w=80), Agg=100, no commander bonus
        net_dmg_on_b = 120 - 15 = 105.0
        v = 1 / 80.0 = 0.0125
        losses_b = 105 * (1/80) = 1.3125
        net_dmg_on_a = 40 - 30 = 10.0
        u = 1 / 300.0
        losses_a = 10 * (1/300) = 0.0333...
        """
        result = SalvoEngine.execute_salvo(self.fleet_a, self.fleet_b, distance=0.0)

        self.assertAlmostEqual(result.effective_firepower_a, 120.0, places=4)
        self.assertAlmostEqual(result.effective_defense_b, 15.0, places=4)
        self.assertAlmostEqual(result.damage_inflicted_on_b, 105.0, places=4)
        self.assertAlmostEqual(result.losses_b, 105.0 / 80.0, places=4)

        self.assertAlmostEqual(result.effective_firepower_b, 40.0, places=4)
        self.assertAlmostEqual(result.effective_defense_a, 30.0, places=4)
        self.assertAlmostEqual(result.damage_inflicted_on_a, 10.0, places=4)
        self.assertAlmostEqual(result.losses_a, 10.0 / 300.0, places=4)

    def test_defense_offset_rule(self):
        """방어 상쇄 연산 규칙 검증 (docs/spec/combat.md 7.2):
        공격 화력이 방어 화력보다 낮을 경우 (alpha*A <= z*B), 해당 턴의 데미지는 0이며 음수 불허.
        """
        # Weak Frigate (alpha=5, y=2) vs Strong Titan (beta=350, z=80)
        frigate = ShipInstance(ship_class="Frigate", aggressiveness=100.0)
        titan = ShipInstance(ship_class="Titan", aggressiveness=100.0)

        weak_fleet = Fleet(ships=[frigate], shared_ordnance=100)
        strong_fleet = Fleet(ships=[titan], shared_ordnance=100)

        # Frigate alpha=5, Titan z=80 -> 5 <= 80 -> damage on Titan must be 0
        result = SalvoEngine.execute_salvo(weak_fleet, strong_fleet, distance=0.0)
        self.assertEqual(result.damage_inflicted_on_b, 0.0)
        self.assertEqual(result.losses_b, 0.0)

    def test_commander_influence_formula(self):
        """지휘관 보정 공식 검증 (docs/spec/combat.md 7.1.1):
        alpha_eff = alpha_base * (1 + ATK_adm / 100) * (Aggressiveness / 100)
        y_eff = y_base * (1 + DEF_adm / 100) * (Aggressiveness / 100)
        """
        # 지휘관: ATK = 50, DEF = 40
        commander = Commander(atk=50.0, def_stat=40.0)
        self.fleet_a.commander = commander
        self.battleship.aggressiveness = 120.0  # 적극성 120

        raw_alpha, eff_alpha, eff_y = SalvoEngine.calculate_effective_firepower(self.fleet_a, distance=0.0)

        # 예상: 120 * (1 + 50/100) * (120/100) = 120 * 1.5 * 1.2 = 216.0
        expected_alpha = 120.0 * 1.5 * 1.2
        # 예상 DEF: 30 * (1 + 40/100) * (120/100) = 30 * 1.4 * 1.2 = 50.4
        expected_y = 30.0 * 1.4 * 1.2

        self.assertAlmostEqual(eff_alpha, expected_alpha, places=4)
        self.assertAlmostEqual(eff_y, expected_y, places=4)

    def test_out_of_range_penalty_on_firepower(self):
        """낙오 시 보정 0% 패널티 검증 (docs/spec/combat.md 5.1)"""
        commander = Commander(atk=100.0, def_stat=100.0)
        self.fleet_a.commander = commander
        self.fleet_a.is_out_of_range = True

        raw_alpha, eff_alpha, eff_y = SalvoEngine.calculate_effective_firepower(self.fleet_a, distance=0.0)
        # 낙오 시 적극성 및 보정 0% 적용 -> eff_alpha = 0.0, eff_y = 0.0
        self.assertEqual(eff_alpha, 0.0)
        self.assertEqual(eff_y, 0.0)


if __name__ == "__main__":
    unittest.main()
