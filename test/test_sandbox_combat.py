"""Unit tests for Combat Mechanics in Fleet Tactical Sandbox
References: SPEC v1.0 Section 3.2, 3.3, 4.2, 8.3, 18.0
"""

import unittest
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import AttackAction
from fleet_sandbox.engine.combat import CombatEngine


class TestSandboxCombat(unittest.TestCase):

    def setUp(self):
        self.engine = CombatEngine(hit_seed=42, zone_seed=142)

    def test_firing_arcs(self):
        """무장 사각(±45°) 판정 검증"""
        attacker = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), heading=90.0)

        # 1. Target directly North (0° offset from heading 90°) -> in FRONT arc
        target_north = Vector2D(50.0, 60.0)
        self.assertTrue(self.engine.is_target_in_firing_arc(attacker, target_north, AttackAction.FRONT))
        self.assertFalse(self.engine.is_target_in_firing_arc(attacker, target_north, AttackAction.REAR))

        # 2. Target directly West (+90° offset) -> in LEFT arc
        target_west = Vector2D(40.0, 50.0)
        self.assertTrue(self.engine.is_target_in_firing_arc(attacker, target_west, AttackAction.LEFT))
        self.assertFalse(self.engine.is_target_in_firing_arc(attacker, target_west, AttackAction.RIGHT))

        # 3. Target directly East (-90° offset) -> in RIGHT arc
        target_east = Vector2D(60.0, 50.0)
        self.assertTrue(self.engine.is_target_in_firing_arc(attacker, target_east, AttackAction.RIGHT))

        # 4. Target directly South (180° offset) -> in REAR arc
        target_south = Vector2D(50.0, 40.0)
        self.assertTrue(self.engine.is_target_in_firing_arc(attacker, target_south, AttackAction.REAR))

    def test_core_damage_degrades_speed_and_acceleration(self):
        """코어 손상률에 따른 최대 속도 및 가속도 감속 검증 (SPEC 3.3)"""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship")
        # 100% Core -> full speed (2.0) and full accel (0.5)
        self.assertEqual(ship.effective_max_speed, 2.0)
        self.assertEqual(ship.effective_max_accel, 0.5)

        # 25% damage to Core (HP = 75) -> 75% performance (1.5 speed, 0.375 accel)
        ship.zones.core = 75.0
        self.assertAlmostEqual(ship.zones.core_damage_rate, 0.25, places=4)
        self.assertAlmostEqual(ship.effective_max_speed, 1.5, places=4)
        self.assertAlmostEqual(ship.effective_max_accel, 0.375, places=4)

        # 100% damage to Core (HP = 0) -> Destroyed, 0 speed
        ship.zones.core = 0.0
        self.assertEqual(ship.effective_max_speed, 0.0)
        self.assertTrue(ship.is_destroyed)

    def test_simultaneous_combat_mutual_destruction(self):
        """동일 틱에서의 동시 공격 및 상호 격침 판정 검증 (SPEC 8.3 & Invariant 10)"""
        s1 = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), heading=90.0)
        s2 = Ship(ship_id=4, faction="Enemy", role="Flagship", position=Vector2D(50.0, 60.0), heading=270.0)

        # Set both cores to 5 HP (1 shot of 10 damage will destroy both)
        s1.zones.core = 5.0
        s2.zones.core = 5.0
        s1.base_hit_rate = 1.0
        s2.base_hit_rate = 1.0

        # Guarantee zone determination hits core directly
        engine = CombatEngine(hit_seed=1, zone_seed=1)
        engine.determine_hit_zone = lambda a, t, *args: "core"

        actions = {
            1: (AttackAction.FRONT, 4),
            4: (AttackAction.FRONT, 1),
        }
        events = engine.execute_batch_combat([s1, s2], actions)

        self.assertEqual(len(events), 2)
        # Both must be destroyed in the same batch
        self.assertTrue(s1.is_destroyed)
        self.assertTrue(s2.is_destroyed)


if __name__ == "__main__":
    unittest.main()
