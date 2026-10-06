#!/usr/bin/env python3
"""SpaceGame v0.1 Tactical Combat Simulation Test Program
Simulates a multi-turn tactical space battle between two fleets.
Prints detailed turn-by-turn salvo exchanges, ordnance usage, and victory outcomes.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from spacegame.core.models import Fleet, ShipInstance, Commander, Position
from spacegame.core.combat_engine import CombatEngine


def run_fleet_battle_simulation():
    print("=" * 80)
    print(" SpaceGame v0.1 우주함대전 교전 시뮬레이션 테스트 프로그램")
    print("=" * 80)

    # 1. 제국 함대 (Red Faction) 구성
    red_admiral = Commander(
        name="Reinhard von Lohengramm",
        ldr=98.0,
        atk=95.0,
        def_stat=90.0,
        mob=92.0,
        personality="Brave",
    )
    red_flagship = ShipInstance(
        ship_class="Doom Star",
        is_flagship=True,
        aggressiveness=120.0,
        position=Position(50, 10),
    )
    red_escort_1 = ShipInstance(
        ship_class="Battleship",
        aggressiveness=110.0,
        position=Position(48, 12),
    )
    red_escort_2 = ShipInstance(
        ship_class="Battleship",
        aggressiveness=110.0,
        position=Position(52, 12),
    )

    fleet_red = Fleet(
        name="Imperial 1st Expeditionary Fleet",
        faction="Red",
        commander=red_admiral,
        ships=[red_flagship, red_escort_1, red_escort_2],
        shared_ordnance=500,
        is_grand_admiral=True,
    )

    # 2. 동맹 함대 (Blue Faction) 구성
    blue_admiral = Commander(
        name="Yang Wen-li",
        ldr=96.0,
        atk=88.0,
        def_stat=98.0,
        mob=94.0,
        personality="Cool",
    )
    blue_flagship = ShipInstance(
        ship_class="Titan",
        is_flagship=True,
        aggressiveness=100.0,
        position=Position(50, 85),
    )
    blue_cruisers = [
        ShipInstance(ship_class="Cruiser", aggressiveness=100.0, position=Position(45 + i * 2, 83))
        for i in range(4)
    ]
    blue_destroyers = [
        ShipInstance(ship_class="Destroyer", aggressiveness=100.0, position=Position(44 + i * 3, 81))
        for i in range(4)
    ]

    fleet_blue = Fleet(
        name="Alliance 13th Fleet",
        faction="Blue",
        commander=blue_admiral,
        ships=[blue_flagship] + blue_cruisers + blue_destroyers,
        shared_ordnance=500,
        is_grand_admiral=True,
    )

    print(f"[Fleet Red] {fleet_red.name} | 기함: {fleet_red.flagship.ship_class} | 함선수: {fleet_red.alive_count} | 군수품: {fleet_red.shared_ordnance}")
    print(f"[Fleet Blue] {fleet_blue.name} | 기함: {fleet_blue.flagship.ship_class} | 함선수: {fleet_blue.alive_count} | 군수품: {fleet_blue.shared_ordnance}")
    print("-" * 80)

    # 3. 전술 교전 시뮬레이션 실행 (최대 12 전술턴 = 1 전략턴)
    engine = CombatEngine(fleet_red, fleet_blue, max_tactical_turns=12)

    while not engine.check_victory():
        turn = engine.current_turn + 1
        print(f"\n>>> [전술 턴 {turn} (경과 시간: {turn * 6}시간)] 교전 개시 <<<")

        log = engine.execute_tactical_turn(distance=4.0)

        salvo = log.salvo_result
        print(f" - Fleet Red 화력: {salvo.effective_firepower_a:.1f} (방어: {salvo.effective_defense_a:.1f}) -> 타격 데미지: {salvo.damage_inflicted_on_b:.1f}")
        print(f" - Fleet Blue 화력: {salvo.effective_firepower_b:.1f} (방어: {salvo.effective_defense_b:.1f}) -> 타격 데미지: {salvo.damage_inflicted_on_a:.1f}")
        print(f" - 군수품 소모: Red {log.ordnance_consumed_a} / Blue {log.ordnance_consumed_b}")
        print(f" - 잔여 군수품: Red {fleet_red.shared_ordnance} / Blue {fleet_blue.shared_ordnance}")

        if log.destroyed_ships_a:
            print(f" ! Fleet Red 격침 함선: {log.destroyed_ships_a}")
        if log.destroyed_ships_b:
            print(f" ! Fleet Blue 격침 함선: {log.destroyed_ships_b}")

        print(f" - 생존 함선 현황: Red {log.remaining_count_a}척 vs Blue {log.remaining_count_b}척")

    report = engine.check_victory()
    print("\n" + "=" * 80)
    print(" [전투 최종 결과 보고서]")
    print(f" - 종결 여부: {report.is_ended}")
    print(f" - 승자: {report.winner}")
    print(f" - 승리 방식: {report.victory_type}")
    print(f" - 진행 턴 수: {report.total_turns} 턴 ({report.total_turns * 6}시간)")
    print(f" - 최종 승점: Fleet Red {report.vp_a} VP vs Fleet Blue {report.vp_b} VP")
    print(f" - 손실 목록 Red: {report.lost_ships_a}")
    print(f" - 손실 목록 Blue: {report.lost_ships_b}")
    print("=" * 80)


if __name__ == "__main__":
    run_fleet_battle_simulation()
