"""Simulation Invariants Unit Tests for Fleet Tactical Sandbox
References: SPEC v1.0 Section 14.0 (12 Invariants) & Section 18.0
"""

import unittest
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import MoveAction, AttackAction
from fleet_sandbox.engine.formation import FormationSystem
from fleet_sandbox.engine.movement import MovementEngine
from fleet_sandbox.engine.combat import CombatEngine
from fleet_sandbox.engine.world_state import WorldState
from fleet_sandbox.experiment.scenarios import build_scenario


class TestSandboxInvariants(unittest.TestCase):

    def setUp(self):
        self.formation_system = FormationSystem()
        self.movement_engine = MovementEngine(100.0, 100.0)
        self.combat_engine = CombatEngine(hit_seed=42, zone_seed=142)

    def test_invariant_1_speed_does_not_exceed_max_speed(self):
        """Invariant 1: 함선 속도는 최대 속도(2.0)를 초과하지 않는다."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", speed=1.8)
        # Apply FAST_N (target 2.0) over 10 ticks
        for _ in range(10):
            pos, heading, speed = self.movement_engine.simulate_next_position(ship, MoveAction.FAST_N)
            ship.position = pos
            ship.heading = heading
            ship.speed = speed
            self.assertLessEqual(ship.speed, ship.effective_max_speed + 1e-6)
            self.assertLessEqual(ship.speed, 2.0 + 1e-6)

    def test_invariant_2_turn_rate_does_not_exceed_max_turn_rate(self):
        """Invariant 2: 선회량은 최대 선회율(45°/초)을 초과하지 않는다."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", heading=0.0)
        # Command FAST_W (180°) which requires a 180° turn
        pos, next_heading, speed = self.movement_engine.simulate_next_position(ship, MoveAction.FAST_W, dt=1.0)
        from fleet_sandbox.models.vector2d import shortest_angular_difference_deg
        turn_amount = abs(shortest_angular_difference_deg(next_heading, ship.heading))
        self.assertLessEqual(turn_amount, 45.0 + 1e-6)

    def test_invariant_3_damage_rate_within_0_to_100_percent(self):
        """Invariant 3: 손상률은 0~100% 범위를 벗어나지 않는다."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship")
        ship.zones.damage_zone("front", 150.0)  # Overkill
        self.assertGreaterEqual(ship.zones.front, 0.0)
        self.assertLessEqual(ship.zones.front, 100.0)
        self.assertGreaterEqual(ship.zones.core_damage_rate, 0.0)
        self.assertLessEqual(ship.zones.core_damage_rate, 1.0)

    def test_invariant_4_destroyed_ship_does_not_move_or_attack(self):
        """Invariant 4: 격침된 함선은 공격하거나 이동하지 않는다."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), speed=1.5)
        ship.zones.core = 0.0  # Destroyed
        self.assertTrue(ship.is_destroyed)

        # Movement check
        pos, heading, speed = self.movement_engine.simulate_next_position(ship, MoveAction.FAST_N)
        self.assertEqual(pos, ship.position)
        self.assertEqual(speed, 0.0)
        self.assertFalse(ship.can_fire)

    def test_invariant_5_cannot_fire_before_reload_complete(self):
        """Invariant 5: 재장전 이전에 다시 발사할 수 없다 (reload_time = 3초)."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 50.0), heading=90.0)
        target = Ship(ship_id=4, faction="Enemy", role="Flagship", position=Vector2D(50.0, 60.0))
        self.assertTrue(ship.can_fire)

        # Fire once
        events = self.combat_engine.execute_batch_combat([ship, target], {1: (AttackAction.FRONT, 4)})
        self.assertEqual(len(events), 1)
        self.assertEqual(ship.reload_cooldown, 3)
        self.assertFalse(ship.can_fire)

        # 1 tick pass
        ship.tick_reload()
        self.assertEqual(ship.reload_cooldown, 2)
        self.assertFalse(ship.can_fire)

    def test_invariant_6_cannot_hit_outside_weapon_range(self):
        """Invariant 6: 사거리(20.0) 밖의 목표를 명중시킬 수 없다."""
        ship = Ship(ship_id=1, faction="Friendly", role="Flagship", position=Vector2D(50.0, 10.0), heading=90.0)
        # Enemy at y=35 (distance 25 > 20)
        target = Ship(ship_id=4, faction="Enemy", role="Flagship", position=Vector2D(50.0, 35.0))
        in_arc = self.combat_engine.is_target_in_firing_arc(ship, target.position, AttackAction.FRONT)
        self.assertFalse(in_arc)

        events = self.combat_engine.execute_batch_combat([ship, target], {1: (AttackAction.FRONT, 4)})
        self.assertEqual(len(events), 0)

    def test_invariant_7_cannot_target_undetected_enemy(self):
        """Invariant 7: 탐지하지 못한 적(거리 > 30.0)을 직접 조준할 수 없다."""
        ws = build_scenario("S8", seed=42)
        # In S8, enemies start at y=85, friendly at y=15 (distance 70 > 30)
        ws.step()
        # No attacks should be possible or declared
        self.assertEqual(len(ws.combat_events_history), 0)

    def test_invariant_8_formation_targets_rotate_accurately_with_flagship(self):
        """Invariant 8: 기함의 회전(0°, 90°, 180°, 270°)에 따라 진형 목표가 정확히 회전한다."""
        flag_pos = Vector2D(50.0, 50.0)
        offset = Vector2D(0.0, -6.0)  # Behind flagship by 6 units

        # Heading 90° (North) -> Behind is South (0, -6) -> (50, 44)
        tgt_90 = FormationSystem.calculate_world_target(flag_pos, 90.0, offset)
        self.assertAlmostEqual(tgt_90.x, 50.0, places=4)
        self.assertAlmostEqual(tgt_90.y, 44.0, places=4)

        # Heading 0° (East) -> Behind is West (-6, 0) -> (44, 50)
        tgt_0 = FormationSystem.calculate_world_target(flag_pos, 0.0, offset)
        self.assertAlmostEqual(tgt_0.x, 44.0, places=4)
        self.assertAlmostEqual(tgt_0.y, 50.0, places=4)

        # Heading 180° (West) -> Behind is East (+6, 0) -> (56, 50)
        tgt_180 = FormationSystem.calculate_world_target(flag_pos, 180.0, offset)
        self.assertAlmostEqual(tgt_180.x, 56.0, places=4)
        self.assertAlmostEqual(tgt_180.y, 50.0, places=4)

        # Heading 270° (South) -> Behind is North (0, +6) -> (50, 56)
        tgt_270 = FormationSystem.calculate_world_target(flag_pos, 270.0, offset)
        self.assertAlmostEqual(tgt_270.x, 50.0, places=4)
        self.assertAlmostEqual(tgt_270.y, 56.0, places=4)

    def test_invariant_9_deterministic_reproducibility_with_fixed_seed(self):
        """Invariant 9: 동일한 시드와 동일한 설정이면 100% 동일한 결과가 나온다."""
        ws1 = build_scenario("S1", seed=123)
        ws2 = build_scenario("S1", seed=123)

        res1 = ws1.run_simulation()
        res2 = ws2.run_simulation()

        self.assertEqual(res1["winner"], res2["winner"])
        self.assertEqual(res1["total_ticks"], res2["total_ticks"])
        self.assertEqual(res1["friendly_hp"], res2["friendly_hp"])
        self.assertEqual(res1["enemy_hp"], res2["enemy_hp"])
        self.assertEqual(len(ws1.combat_events_history), len(ws2.combat_events_history))

    def test_invariant_10_symmetric_rules_for_both_factions(self):
        """Invariant 10: 양측 진영의 계산 규칙은 동일하다."""
        f_ship = Ship(ship_id=1, faction="Friendly", role="Flagship")
        e_ship = Ship(ship_id=4, faction="Enemy", role="Flagship")
        self.assertEqual(f_ship.base_max_speed, e_ship.base_max_speed)
        self.assertEqual(f_ship.base_damage, e_ship.base_damage)
        self.assertEqual(f_ship.weapon_range, e_ship.weapon_range)
        self.assertEqual(f_ship.reload_time, e_ship.reload_time)

    def test_invariant_11_no_teleportation_on_formation_update(self):
        """Invariant 11: 진형 목표가 변경되어도 함선이 순간이동하지 않는다 (1틱 이동거리 <= max_speed)."""
        ws = build_scenario("S0", seed=42)
        # Advance 10 ticks, then suddenly switch formation from column to line
        for _ in range(10):
            ws.step()

        prev_pos = {s.ship_id: s.position for s in ws.friendly_ships}
        ws.change_formation("Friendly", "line")
        ws.step()

        for s in ws.friendly_ships:
            step_dist = s.position.distance_to(prev_pos[s.ship_id])
            self.assertLessEqual(step_dist, s.base_max_speed + 1e-4)


if __name__ == "__main__":
    unittest.main()
