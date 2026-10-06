"""Unit tests for Formation System in Fleet Tactical Sandbox
References: SPEC v1.0 Section 5.0, 6.0, 18.0
"""

import unittest
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.engine.formation import FormationSystem
from fleet_sandbox.experiment.scenarios import build_scenario


class TestSandboxFormation(unittest.TestCase):

    def setUp(self):
        self.fs = FormationSystem()

    def test_formation_definitions_loaded(self):
        """종대, 횡대, 포위 배치 정의가 명세대로 로드되는지 검증"""
        column = self.fs.get_formation("column")
        self.assertIsNotNone(column)
        self.assertEqual(column.offsets["1"], (0.0, 0.0))
        self.assertEqual(column.offsets["2"], (0.0, -6.0))
        self.assertEqual(column.offsets["3"], (0.0, -12.0))

        line = self.fs.get_formation("line")
        self.assertIsNotNone(line)
        self.assertEqual(line.offsets["1"], (0.0, 0.0))
        self.assertEqual(line.offsets["2"], (-8.0, 0.0))
        self.assertEqual(line.offsets["3"], (8.0, 0.0))

        flank = self.fs.get_formation("flank")
        self.assertIsNotNone(flank)
        self.assertEqual(flank.offsets["1"], (0.0, 0.0))
        self.assertEqual(flank.offsets["2"], (-10.0, 8.0))
        self.assertEqual(flank.offsets["3"], (10.0, 8.0))

    def test_flagship_rotation_coordinates(self):
        """기함 방향각에 따른 상대좌표 회전 변환 검증 (SPEC 2.2)"""
        flag_pos = Vector2D(50.0, 50.0)
        # Escort A in Line: (-8.0, 0.0) -> left wing
        # When Flagship heading is 90° (North), left wing should be West: (42.0, 50.0)
        target_90 = self.fs.calculate_world_target(flag_pos, 90.0, Vector2D(-8.0, 0.0))
        self.assertAlmostEqual(target_90.x, 42.0, places=4)
        self.assertAlmostEqual(target_90.y, 50.0, places=4)

        # When Flagship heading is 0° (East), left wing should be North: (50.0, 58.0)
        target_0 = self.fs.calculate_world_target(flag_pos, 0.0, Vector2D(-8.0, 0.0))
        self.assertAlmostEqual(target_0.x, 50.0, places=4)
        self.assertAlmostEqual(target_0.y, 58.0, places=4)

    def test_s0_non_combat_formation_convergence(self):
        """S0 비전투 시나리오에서 호위함들이 진형에 수렴하고 유지하는지 검증 (SPEC 10.0 & 19.0)"""
        ws = build_scenario("S0", seed=42)
        # Run 80 ticks
        for _ in range(80):
            ws.step()

        # At tick 80, both Escort A (2) and Escort B (3) should be within tolerance <= 2.0
        escort_a = ws.friendly_ships[1]
        escort_b = ws.friendly_ships[2]

        self.assertLessEqual(escort_a.formation_error, 2.0)
        self.assertLessEqual(escort_b.formation_error, 2.0)


if __name__ == "__main__":
    unittest.main()
