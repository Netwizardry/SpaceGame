"""SpaceGame v0.1 Tactical Battlefield Grid & Command Radius
References:
- docs/spec/battlefield.md 1.0 & 2.0
- docs/spec/combat.md 5.1
"""

from typing import Dict, Tuple, Optional, List
from spacegame.core.models import Position, Fleet, ShipInstance
from spacegame.core.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    ATTACKER_DEPLOYMENT_Y_MIN,
    ATTACKER_DEPLOYMENT_Y_MAX,
    DEFENDER_DEPLOYMENT_Y_MIN,
    DEFENDER_DEPLOYMENT_Y_MAX,
    TERRAIN_EFFECTS,
)


class TacticalGrid:
    """100 x 100 전술 사각 그리드 시스템"""

    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.terrain_map: Dict[Tuple[int, int], str] = {}
        self.black_hole_centers: List[Tuple[int, int]] = []

    def set_terrain(self, x: int, y: int, terrain_type: str) -> None:
        """특정 좌표에 지형 설정 (Empty, Nebula, Asteroid, Black Hole, Space Current)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Coordinate ({x}, {y}) out of grid bounds.")
        if terrain_type not in TERRAIN_EFFECTS:
            raise ValueError(f"Unknown terrain type: {terrain_type}")
        self.terrain_map[(x, y)] = terrain_type
        if terrain_type == "Black Hole" and (x, y) not in self.black_hole_centers:
            self.black_hole_centers.append((x, y))

    def get_terrain(self, x: int, y: int) -> str:
        return self.terrain_map.get((x, y), "Empty")

    def is_valid_position(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def is_attacker_deployment_zone(self, pos: Position) -> bool:
        """공격측 배치 영역: Top 20% (y: 0 ~ 19)"""
        return 0 <= pos.x < self.width and ATTACKER_DEPLOYMENT_Y_MIN <= pos.y <= ATTACKER_DEPLOYMENT_Y_MAX

    def is_defender_deployment_zone(self, pos: Position) -> bool:
        """방어측 배치 영역: Bottom 20% (y: 80 ~ 99)"""
        return 0 <= pos.x < self.width and DEFENDER_DEPLOYMENT_Y_MIN <= pos.y <= DEFENDER_DEPLOYMENT_Y_MAX

    def get_movement_cost(self, pos: Position) -> float:
        """지형별 이동 비용 계산"""
        terrain = self.get_terrain(pos.x, pos.y)
        return TERRAIN_EFFECTS[terrain]["move_cost"]

    def get_hit_modifier(self, pos: Position) -> float:
        """지형별 명중률 보정 (Nebula: -25%, Asteroid: -10%)"""
        terrain = self.get_terrain(pos.x, pos.y)
        return TERRAIN_EFFECTS[terrain]["hit_modifier"]

    def apply_black_hole_gravitation(self, ship: ShipInstance) -> Optional[Position]:
        """
        블랙홀 견인 로직 (docs/spec/battlefield.md 2.0):
        반경 5 Grid 이내 진입 시 매 턴 중앙으로 견인
        """
        for bh_x, bh_y in self.black_hole_centers:
            bh_pos = Position(bh_x, bh_y)
            dist = ship.position.distance_to(bh_pos)
            if 0 < dist <= 5.0:
                # 1칸 중앙 방향으로 당겨짐
                dx = 1 if bh_x > ship.position.x else (-1 if bh_x < ship.position.x else 0)
                dy = 1 if bh_y > ship.position.y else (-1 if bh_y < ship.position.y else 0)
                new_x = max(0, min(self.width - 1, ship.position.x + dx))
                new_y = max(0, min(self.height - 1, ship.position.y + dy))
                ship.position = Position(new_x, new_y)
                return ship.position
        return None

    @staticmethod
    def calculate_command_radius(fleet: Fleet) -> float:
        """
        기함의 [지휘(LDR)] 수치에 비례하여 함대 지휘 반경 결정 (docs/spec/combat.md 5.1)
        """
        flagship = fleet.flagship
        if not flagship:
            return 0.0

        ldr = fleet.get_max_stat("ldr")
        # 기본 반경: LDR * 0.2, 최소 반경 5.0 Grid
        return max(5.0, ldr * 0.2)

    @classmethod
    def update_command_and_control(cls, fleet: Fleet) -> List[ShipInstance]:
        """
        지휘 반경 및 낙오(Out of Range) 판정 (docs/spec/combat.md 5.1)
        낙오 함선 목록 반환 및 패널티 부여.
        """
        flagship = fleet.flagship
        if not flagship:
            # 기함 부재 시 전원 낙오
            for s in fleet.alive_ships:
                s.morale = min(s.morale, 50.0)  # 사기 저하
            fleet.is_out_of_range = True
            return fleet.alive_ships

        radius = cls.calculate_command_radius(fleet)
        out_of_range_ships: List[ShipInstance] = []

        for ship in fleet.alive_ships:
            if ship.instance_id == flagship.instance_id:
                continue
            dist = ship.position.distance_to(flagship.position)
            if dist > radius:
                out_of_range_ships.append(ship)
                # 낙오 패널티 적용
                ship.morale = min(ship.morale, 50.0)  # 노란색 경고/사기 저하
                ship.aggressiveness = 0.0  # 적극성 0%
            else:
                pass

        fleet.is_out_of_range = len(out_of_range_ships) > 0 and (len(out_of_range_ships) == len(fleet.alive_ships) - 1)
        return out_of_range_ships
