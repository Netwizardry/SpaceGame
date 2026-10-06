"""Unit tests for Ordnance Consumption & Logistics
Spec References:
- docs/spec/combat.md 2.1
- docs/spec/ships.md 4.1
"""

import unittest
from spacegame.core.models import Fleet, ShipInstance
from spacegame.core.combat_engine import CombatEngine
from spacegame.core.salvo import SalvoEngine
from spacegame.core.constants import ORDNANCE_PER_VOLLEY


class TestOrdnanceLogistics(unittest.TestCase):

    def setUp(self):
        self.ship_a = ShipInstance(ship_class="Destroyer", ordnance_stock=0)
        self.ship_b = ShipInstance(ship_class="Destroyer", ordnance_stock=0)
        self.fleet_a = Fleet(ships=[self.ship_a], shared_ordnance=25)
        self.fleet_b = Fleet(ships=[self.ship_b], shared_ordnance=100)

    def test_ordnance_consumption_per_turn(self):
        """1회 일제 사격 시 [군수품] 10단위 소모 검증 (docs/spec/combat.md 2.1)"""
        engine = CombatEngine(self.fleet_a, self.fleet_b, max_tactical_turns=5)

        # 1턴 실행: shared_ordnance 25 -> 15 (10 소모)
        log1 = engine.execute_tactical_turn()
        self.assertEqual(log1.ordnance_consumed_a, ORDNANCE_PER_VOLLEY)
        self.assertEqual(self.fleet_a.shared_ordnance, 15)

        # 2턴 실행: 15 -> 5 (10 소모)
        log2 = engine.execute_tactical_turn()
        self.assertEqual(log2.ordnance_consumed_a, ORDNANCE_PER_VOLLEY)
        self.assertEqual(self.fleet_a.shared_ordnance, 5)

        # 3턴 실행: 잔여 5 소모 -> 0
        log3 = engine.execute_tactical_turn()
        self.assertEqual(log3.ordnance_consumed_a, 5)
        self.assertEqual(self.fleet_a.shared_ordnance, 0)

    def test_zero_ordnance_disables_firepower(self):
        """군수품 고갈 시 Attack Power = 0 검증 (docs/spec/combat.md 2.1)"""
        self.fleet_a.shared_ordnance = 0
        raw_alpha, eff_alpha, eff_y = SalvoEngine.calculate_effective_firepower(self.fleet_a)

        self.assertEqual(eff_alpha, 0.0)


if __name__ == "__main__":
    unittest.main()
