"""SpaceGame v0.1 Tactical Combat Engine & Victory Evaluation
References:
- docs/spec/INDEX.md 2.1 (Tactical Turn = 6 hours)
- docs/spec/combat.md 2.1, 6.0, 7.0
- docs/spec/ships.md 4.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from spacegame.core.models import Fleet, ShipInstance
from spacegame.core.salvo import SalvoEngine, SalvoResult
from spacegame.core.damage import DamagePipeline
from spacegame.core.grid import TacticalGrid
from spacegame.core.constants import (
    ORDNANCE_PER_VOLLEY,
    VP_SHIP_WEIGHTS,
)


@dataclass
class TurnLog:
    turn_number: int  # 1 tactical turn = 6 hours
    salvo_result: SalvoResult
    ordnance_consumed_a: int
    ordnance_consumed_b: int
    destroyed_ships_a: List[str]
    destroyed_ships_b: List[str]
    remaining_count_a: int
    remaining_count_b: int


@dataclass
class CombatReport:
    is_ended: bool
    winner: Optional[str]  # "Fleet A", "Fleet B", "Draw", or None
    victory_type: Optional[str]  # "Total Victory", "Partial Victory", None
    total_turns: int
    vp_a: int
    vp_b: int
    lost_ships_a: List[str]
    lost_ships_b: List[str]
    turn_logs: List[TurnLog] = field(default_factory=list)


class CombatEngine:
    """전술 교전 시뮬레이션 및 승패 판정 엔진"""

    def __init__(
        self,
        fleet_a: Fleet,
        fleet_b: Fleet,
        grid: Optional[TacticalGrid] = None,
        max_tactical_turns: int = 12,  # 12 전술턴 = 1 전략턴 (INDEX.md 2.1)
    ):
        self.fleet_a = fleet_a
        self.fleet_b = fleet_b
        self.grid = grid or TacticalGrid()
        self.max_tactical_turns = max_tactical_turns
        self.current_turn = 0

        self.initial_ships_a = [s.ship_class for s in fleet_a.ships]
        self.initial_ships_b = [s.ship_class for s in fleet_b.ships]

        self.lost_ships_a: List[str] = []
        self.lost_ships_b: List[str] = []
        self.lost_ship_ids_a: Set[str] = set()
        self.lost_ship_ids_b: Set[str] = set()
        self.turn_logs: List[TurnLog] = []

    def calculate_vp(self, friendly_lost: List[str], enemy_lost: List[str]) -> int:
        """
        VP = (적 함선 격침 수 * 함급 가중치) - (아군 손실 수 * 함급 가중치)
        (docs/spec/combat.md 6.2)
        """
        enemy_vp = sum(VP_SHIP_WEIGHTS.get(ship_class, 5) for ship_class in enemy_lost)
        friendly_vp = sum(VP_SHIP_WEIGHTS.get(ship_class, 5) for ship_class in friendly_lost)
        return enemy_vp - friendly_vp

    def check_victory(self) -> Optional[CombatReport]:
        """승리 조건 판정 (docs/spec/combat.md 6.0)"""
        # 1. 완전 승리 (Total Victory): 적 총사령함대 격침 혹은 전멸
        # Check Fleet B annihilation or Grand Admiral death
        b_flagship_dead = self.fleet_b.is_grand_admiral and self.fleet_b.is_flagship_destroyed
        b_annihilated = self.fleet_b.is_annihilated

        a_flagship_dead = self.fleet_a.is_grand_admiral and self.fleet_a.is_flagship_destroyed
        a_annihilated = self.fleet_a.is_annihilated

        vp_a = self.calculate_vp(self.lost_ships_a, self.lost_ships_b)
        vp_b = self.calculate_vp(self.lost_ships_b, self.lost_ships_a)

        if (b_flagship_dead or b_annihilated) and (a_flagship_dead or a_annihilated):
            return CombatReport(
                is_ended=True,
                winner="Draw",
                victory_type="Mutual Annihilation",
                total_turns=self.current_turn,
                vp_a=vp_a,
                vp_b=vp_b,
                lost_ships_a=self.lost_ships_a,
                lost_ships_b=self.lost_ships_b,
                turn_logs=self.turn_logs,
            )
        elif b_flagship_dead or b_annihilated:
            return CombatReport(
                is_ended=True,
                winner="Fleet A",
                victory_type="Total Victory",
                total_turns=self.current_turn,
                vp_a=vp_a,
                vp_b=vp_b,
                lost_ships_a=self.lost_ships_a,
                lost_ships_b=self.lost_ships_b,
                turn_logs=self.turn_logs,
            )
        elif a_flagship_dead or a_annihilated:
            return CombatReport(
                is_ended=True,
                winner="Fleet B",
                victory_type="Total Victory",
                total_turns=self.current_turn,
                vp_a=vp_a,
                vp_b=vp_b,
                lost_ships_a=self.lost_ships_a,
                lost_ships_b=self.lost_ships_b,
                turn_logs=self.turn_logs,
            )

        # 2. 판정 승리 (Partial Victory): 시나리오 제한 시간(max_turns) 종료 시 VP 비교
        if self.current_turn >= self.max_tactical_turns:
            winner = "Fleet A" if vp_a > vp_b else ("Fleet B" if vp_b > vp_a else "Draw")
            return CombatReport(
                is_ended=True,
                winner=winner,
                victory_type="Partial Victory",
                total_turns=self.current_turn,
                vp_a=vp_a,
                vp_b=vp_b,
                lost_ships_a=self.lost_ships_a,
                lost_ships_b=self.lost_ships_b,
                turn_logs=self.turn_logs,
            )

        return None

    def execute_tactical_turn(self, distance: float = 0.0) -> TurnLog:
        """단일 전술 턴(6시간) 교전 시퀀스 실행 (docs/spec/combat.md 7.2)"""
        self.current_turn += 1

        # 1. 지휘 통제 및 낙오 판정
        self.grid.update_command_and_control(self.fleet_a)
        self.grid.update_command_and_control(self.fleet_b)

        # 2. 군수품 소모 처리 (일제 사격 시 부대당 10단위 소모)
        ordnance_spent_a = 0
        if self.fleet_a.alive_count > 0:
            if self.fleet_a.shared_ordnance >= ORDNANCE_PER_VOLLEY:
                self.fleet_a.shared_ordnance -= ORDNANCE_PER_VOLLEY
                ordnance_spent_a = ORDNANCE_PER_VOLLEY
            else:
                ordnance_spent_a = self.fleet_a.shared_ordnance
                self.fleet_a.shared_ordnance = 0

        ordnance_spent_b = 0
        if self.fleet_b.alive_count > 0:
            if self.fleet_b.shared_ordnance >= ORDNANCE_PER_VOLLEY:
                self.fleet_b.shared_ordnance -= ORDNANCE_PER_VOLLEY
                ordnance_spent_b = ORDNANCE_PER_VOLLEY
            else:
                ordnance_spent_b = self.fleet_b.shared_ordnance
                self.fleet_b.shared_ordnance = 0

        # 3. 살보 방정식 연산
        salvo_res = SalvoEngine.execute_salvo(self.fleet_a, self.fleet_b, distance=distance)

        # 4. 3층 방어 체계 데미지 적용
        DamagePipeline.distribute_fleet_damage(self.fleet_b, salvo_res.damage_inflicted_on_b)
        DamagePipeline.distribute_fleet_damage(self.fleet_a, salvo_res.damage_inflicted_on_a)

        # 5. 격침된 함선 추적
        newly_destroyed_a = []
        for s in self.fleet_a.ships:
            if s.is_destroyed and s.instance_id not in self.lost_ship_ids_a:
                self.lost_ship_ids_a.add(s.instance_id)
                self.lost_ships_a.append(s.ship_class)
                newly_destroyed_a.append(s.ship_class)

        newly_destroyed_b = []
        for s in self.fleet_b.ships:
            if s.is_destroyed and s.instance_id not in self.lost_ship_ids_b:
                self.lost_ship_ids_b.add(s.instance_id)
                self.lost_ships_b.append(s.ship_class)
                newly_destroyed_b.append(s.ship_class)

        # 6. 실드 자동 회복 (docs/spec/ships.md 5.2)
        DamagePipeline.regenerate_shields(self.fleet_a)
        DamagePipeline.regenerate_shields(self.fleet_b)

        turn_log = TurnLog(
            turn_number=self.current_turn,
            salvo_result=salvo_res,
            ordnance_consumed_a=ordnance_spent_a,
            ordnance_consumed_b=ordnance_spent_b,
            destroyed_ships_a=newly_destroyed_a,
            destroyed_ships_b=newly_destroyed_b,
            remaining_count_a=self.fleet_a.alive_count,
            remaining_count_b=self.fleet_b.alive_count,
        )
        self.turn_logs.append(turn_log)
        return turn_log

    def run_simulation(self, distance: float = 0.0) -> CombatReport:
        """전투가 종결될 때까지 턴 자동 진행"""
        while self.current_turn < self.max_tactical_turns:
            rep = self.check_victory()
            if rep:
                return rep
            self.execute_tactical_turn(distance=distance)

        final_rep = self.check_victory()
        if not final_rep:
            # Fallback for turn limit
            vp_a = self.calculate_vp(self.lost_ships_a, self.lost_ships_b)
            vp_b = self.calculate_vp(self.lost_ships_b, self.lost_ships_a)
            winner = "Fleet A" if vp_a > vp_b else ("Fleet B" if vp_b > vp_a else "Draw")
            return CombatReport(
                is_ended=True,
                winner=winner,
                victory_type="Partial Victory",
                total_turns=self.current_turn,
                vp_a=vp_a,
                vp_b=vp_b,
                lost_ships_a=self.lost_ships_a,
                lost_ships_b=self.lost_ships_b,
                turn_logs=self.turn_logs,
            )
        return final_rep
