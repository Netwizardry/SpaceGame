"""SpaceGame v0.1 Core Data Models
References:
- docs/spec/units.md
- docs/spec/entities.md
- docs/spec/combat.md
- docs/spec/ships.md
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid

from spacegame.core.constants import (
    SHIP_SALVO_PARAMS,
    CREW_RANK_MODIFIERS,
)


@dataclass
class Position:
    x: int
    y: int

    def distance_to(self, other: "Position") -> float:
        """Euclidean distance in grid units."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class Commander:
    """인물 데이터 모델 (docs/spec/entities.md 2.1 & units.md 2.1)"""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unknown Commander"
    # 8대 핵심 능력치 (0~100)
    ldr: float = 50.0  # 통솔
    mng: float = 50.0  # 운영
    inf: float = 50.0  # 정보
    mob: float = 50.0  # 기동
    atk: float = 50.0  # 공격
    def_stat: float = 50.0  # 방어 (DEF)
    gnd: float = 50.0  # 육전
    air: float = 50.0  # 공전

    # 추가 5대 기본 속성 / 세부 인지 (docs/spec/entities.md 5.1 & units.md 2.1)
    per: float = 50.0  # 인지 (명중률 보정)
    tac: float = 50.0  # 전술 (회피율 보정)

    # 3대 공작 포인트 (AP)
    pol: int = 4000
    int_ap: int = 4000
    mil: int = 4000

    personality: str = "Normal"  # Rush, Brave, Normal, Cool, Cautious


@dataclass
class ShipInstance:
    """유닛 인스턴스 구조 (docs/spec/units.md 1.0)"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ship_class: str = "Frigate"
    hull_id: str = "Standard_Hull"
    captain_id: Optional[str] = None
    crew_rank: str = "Regular"
    aggressiveness: float = 100.0  # 0 ~ 200
    morale: float = 100.0

    current_shield: float = 0.0
    max_shield: float = 0.0

    current_armor: float = 0.0
    max_armor: float = 0.0

    current_structure: float = 0.0
    max_structure: float = 0.0

    current_capacitor: float = 500.0
    max_capacitor: float = 500.0

    ordnance_stock: int = 100
    position: Position = field(default_factory=lambda: Position(0, 0))
    is_flagship: bool = False

    def __post_init__(self):
        # 만약 초기 내구도가 지정되지 않았다면 함급 기본 스펙으로 초기화
        if self.ship_class in SHIP_SALVO_PARAMS:
            spec = SHIP_SALVO_PARAMS[self.ship_class]
            if self.max_shield == 0.0:
                self.max_shield = spec["shield"]
                self.current_shield = spec["shield"]
            if self.max_armor == 0.0:
                self.max_armor = spec["armor"]
                self.current_armor = spec["armor"]
            if self.max_structure == 0.0:
                self.max_structure = spec["structure"]
                self.current_structure = spec["structure"]

    @property
    def is_destroyed(self) -> bool:
        return self.current_structure <= 0.0

    @property
    def staying_power(self) -> float:
        """w = Shield + Armor + Structure (docs/spec/ships.md 4.1)"""
        return max(0.0, self.current_shield) + max(0.0, self.current_armor) + max(0.0, self.current_structure)

    @property
    def max_staying_power(self) -> float:
        return self.max_shield + self.max_armor + self.max_structure

    @property
    def damage_fraction(self) -> float:
        """u = 1 / w (docs/spec/combat.md 7.1.1)"""
        w = self.staying_power
        return 1.0 / w if w > 0.0 else 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Instance_ID": self.instance_id,
            "Ship_Class": self.ship_class,
            "Hull_ID": self.hull_id,
            "Captain_ID": self.captain_id,
            "Aggressiveness": self.aggressiveness,
            "Morale": self.morale,
            "Current_Shield": self.current_shield,
            "Current_Armor": self.current_armor,
            "Current_Structure": self.current_structure,
            "Current_Capacitor": self.current_capacitor,
            "Ordnance_Stock": self.ordnance_stock,
            "Position": {"x": self.position.x, "y": self.position.y},
            "Is_Flagship": self.is_flagship,
        }


@dataclass
class Fleet:
    """함대 데이터 구조 (docs/spec/combat.md & units.md)"""
    fleet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Fleet"
    faction: str = "Red"
    commander: Optional[Commander] = None
    staff: List[Commander] = field(default_factory=list)  # 최대 5인 참모
    ships: List[ShipInstance] = field(default_factory=list)
    is_grand_admiral: bool = False  # 적 총사령함대 여부 (docs/spec/combat.md 6.1)
    is_out_of_range: bool = False  # 낙오 상태 여부 (docs/spec/combat.md 5.1)
    shared_ordnance: int = 1000  # 함대 공용 군수품 보관고

    @property
    def alive_ships(self) -> List[ShipInstance]:
        return [s for s in self.ships if not s.is_destroyed]

    @property
    def alive_count(self) -> int:
        return len(self.alive_ships)

    @property
    def is_annihilated(self) -> bool:
        return len(self.alive_ships) == 0

    @property
    def original_flagship(self) -> Optional[ShipInstance]:
        for s in self.ships:
            if s.is_flagship:
                return s
        return self.ships[0] if self.ships else None

    @property
    def is_flagship_destroyed(self) -> bool:
        f = self.original_flagship
        return f is None or f.is_destroyed

    @property
    def flagship(self) -> Optional[ShipInstance]:
        f = self.original_flagship
        if f and not f.is_destroyed:
            return f
        return None

    def get_max_stat(self, stat_name: str) -> float:
        """사령관 + 참모 5인 중 해당 항목의 최고치(Max_Stat) (docs/spec/entities.md 3.1)"""
        all_officers = []
        if self.commander:
            all_officers.append(self.commander)
        all_officers.extend(self.staff[:5])

        if not all_officers:
            return 0.0

        values = [getattr(officer, stat_name, 0.0) for officer in all_officers]
        return max(values) if values else 0.0
