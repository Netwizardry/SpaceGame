"""Unit tests for Commander & Crew Coupling Logic
Spec References:
- docs/spec/entities.md 3.1
- docs/spec/units.md 2.1 & 2.2
"""

import unittest
from spacegame.core.models import Commander, Fleet, ShipInstance
from spacegame.core.constants import CREW_RANK_MODIFIERS


class TestCommanderCoupling(unittest.TestCase):

    def test_fleet_max_stat_extraction(self):
        """사령관 + 참모 5인 중 최고 능력치(Max_Stat) 추출 검증 (docs/spec/entities.md 3.1)"""
        commander = Commander(name="Admiral", atk=40.0, ldr=70.0)
        staff1 = Commander(name="Staff Gunner", atk=85.0, ldr=30.0)  # ATK가 더 높음
        staff2 = Commander(name="Staff Navigator", atk=20.0, mob=90.0)

        fleet = Fleet(
            commander=commander,
            staff=[staff1, staff2],
        )

        # ATK는 staff1의 85.0이 선택되어야 함
        self.assertEqual(fleet.get_max_stat("atk"), 85.0)
        # LDR은 commander의 70.0이 선택되어야 함
        self.assertEqual(fleet.get_max_stat("ldr"), 70.0)
        # MOB은 staff2의 90.0이 선택되어야 함
        self.assertEqual(fleet.get_max_stat("mob"), 90.0)

    def test_crew_rank_multipliers(self):
        """승무원 숙련도 계수 검증 (docs/spec/units.md 2.2)"""
        # Green: 80% (0.8)
        self.assertEqual(CREW_RANK_MODIFIERS["Green"]["performance"], 0.8)
        # Regular: 100% (1.0)
        self.assertEqual(CREW_RANK_MODIFIERS["Regular"]["performance"], 1.0)
        # Veteran: 110% (1.1)
        self.assertEqual(CREW_RANK_MODIFIERS["Veteran"]["performance"], 1.1)
        # Elite: 125% (1.25)
        self.assertEqual(CREW_RANK_MODIFIERS["Elite"]["performance"], 1.25)
        # Heroic: 150% (1.5)
        self.assertEqual(CREW_RANK_MODIFIERS["Heroic"]["performance"], 1.5)

    def test_officer_stat_boundary(self):
        """5인 초과 참모는 보정에 포함되지 않음을 검증"""
        commander = Commander(atk=50.0)
        # 5명의 일반 참모
        staff_normal = [Commander(atk=60.0) for _ in range(5)]
        # 6번째 참모 (초과)
        staff_overflow = Commander(atk=99.0)

        fleet = Fleet(commander=commander, staff=staff_normal + [staff_overflow])

        # 상위 5인까지만 반영되므로 60.0이 최고치여야 함 (99.0 제외)
        self.assertEqual(fleet.get_max_stat("atk"), 60.0)


if __name__ == "__main__":
    unittest.main()
