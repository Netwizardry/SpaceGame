#!/usr/bin/env python3
"""Fleet Tactical Sandbox - Automated Experiment Runner & Statistical Analyzer
Runs S0~S8 scenarios across 100 seeds with paired comparisons and broadside A/B tests.
References: SPEC v1.0 Section 10.0, 11.0, 12.0, 13.0, 21.0
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fleet_sandbox.experiment.runner import ExperimentRunner


def format_ci(ci_tuple: Tuple[float, float]) -> str:
    if not ci_tuple:
        return "N/A"
    return f"[{ci_tuple[0]*100:.1f}%, {ci_tuple[1]*100:.1f}%]"


def run_all_experiments(num_seeds: int = 100):
    print("=" * 96)
    print(f" FLEET TACTICAL SANDBOX v1.0 - 100-Seed Rigorous Verification & Crossed Experiments")
    print(f" Execution Count: {num_seeds} seeds per experiment condition")
    print("=" * 96)

    runner = ExperimentRunner()
    results: Dict[str, Any] = {}

    start_time = time.time()

    # --------------------------------------------------------------------------
    # 1. Symmetry & Control Group Comparison (S1: Column vs Column)
    # --------------------------------------------------------------------------
    print("\n>>> [1/5] 대칭성 검증 및 제어군 비교 (S1 Column vs Column: C0, C1, C2)...")

    print(" - Running S1 C0 (No Formation, wF=0)...")
    results["S1_C0"] = runner.run_batch_experiment("S1", num_seeds=num_seeds, friendly_ai_mode="C0", enemy_ai_mode="C0")

    print(" - Running S1 C1 (Rigid Formation Tracking, wF=50)...")
    results["S1_C1"] = runner.run_batch_experiment("S1", num_seeds=num_seeds, friendly_ai_mode="C1", enemy_ai_mode="C1")

    print(" - Running S1 C2 (Flexible Formation Tracking, wF=1.5)...")
    results["S1_C2"] = runner.run_batch_experiment("S1", num_seeds=num_seeds, friendly_ai_mode="C2", enemy_ai_mode="C2")

    # --------------------------------------------------------------------------
    # 2. Paired Crossed Formation Comparison (Line vs Column, Flank vs Column, Line vs Flank)
    # --------------------------------------------------------------------------
    print("\n>>> [2/5] 진형 간 양방향 완전 교차실험 (Paired Crossed Comparison)...")

    print(" - Pairing 1A: Friendly Line vs Enemy Column...")
    results["Line_vs_Column"] = runner.run_batch_battle("line", "column", num_seeds=num_seeds)
    print(" - Pairing 1B: Friendly Column vs Enemy Line (Reversed)...")
    results["Column_vs_Line"] = runner.run_batch_battle("column", "line", num_seeds=num_seeds)

    print(" - Pairing 2A: Friendly Flank vs Enemy Column...")
    results["Flank_vs_Column"] = runner.run_batch_battle("flank", "column", num_seeds=num_seeds)
    print(" - Pairing 2B: Friendly Column vs Enemy Flank (Reversed)...")
    results["Column_vs_Flank"] = runner.run_batch_battle("column", "flank", num_seeds=num_seeds)

    print(" - Pairing 3A: Friendly Line vs Enemy Flank...")
    results["Line_vs_Flank"] = runner.run_batch_battle("line", "flank", num_seeds=num_seeds)
    print(" - Pairing 3B: Friendly Flank vs Enemy Line (Reversed)...")
    results["Flank_vs_Line"] = runner.run_batch_battle("flank", "line", num_seeds=num_seeds)

    # --------------------------------------------------------------------------
    # 3. Dynamic Convergence & Maneuvering Scenarios (S0, S6)
    # --------------------------------------------------------------------------
    print("\n>>> [3/5] 진형 수렴(S0) 및 선회 추종(S6) 동적 검증...")

    print(" - Running S0 (Scattered Start Convergence Test)...")
    results["S0_Scattered"] = runner.run_batch_experiment("S0", num_seeds=num_seeds)

    print(" - Running S6 (Flagship 90-deg Turn Following Test)...")
    results["S6_Turn"] = runner.run_batch_experiment("S6", num_seeds=num_seeds)

    # --------------------------------------------------------------------------
    # 4. Tactical Scenarios & Edge Cases (S5, S7, S8)
    # --------------------------------------------------------------------------
    print("\n>>> [4/5] 동적 진형 전환 및 예외 시나리오 (S5, S7, S8)...")

    print(" - Running S5 (Mid-combat Formation Change at Tick 100)...")
    results["S5_Mid_Change"] = runner.run_batch_experiment("S5", num_seeds=num_seeds)

    print(" - Running S7 (Damaged Escort Core 50%)...")
    results["S7_Damaged"] = runner.run_batch_experiment("S7", num_seeds=num_seeds)

    print(" - Running S8 (Sensor Detection Range Limit)...")
    results["S8_Sensor_Limit"] = runner.run_batch_experiment("S8", num_seeds=num_seeds)

    # --------------------------------------------------------------------------
    # 5. Broadside-aware Tactical AI A/B Testing
    # --------------------------------------------------------------------------
    print("\n>>> [5/5] Broadside-aware AI 전술 기동 A/B 테스트...")

    print(" - Running Baseline Line vs Line (Both Front-only)...")
    results["AB_Base_Line"] = runner.run_batch_battle("line", "line", num_seeds=num_seeds, friendly_broadside=False, enemy_broadside=False)

    print(" - Running Line vs Line (Friendly Broadside-aware vs Enemy Front-only)...")
    results["AB_Broadside_Line"] = runner.run_batch_battle("line", "line", num_seeds=num_seeds, friendly_broadside=True, enemy_broadside=False)

    print(" - Running Column vs Column (Friendly Broadside-aware vs Enemy Front-only)...")
    results["AB_Broadside_Column"] = runner.run_batch_battle("column", "column", num_seeds=num_seeds, friendly_broadside=True, enemy_broadside=False)

    duration = time.time() - start_time
    print(f"\n>> 모든 실험 완료 (총 소요 시간: {duration:.2f}초)")

    # --------------------------------------------------------------------------
    # Statistical Summary Reporting
    # --------------------------------------------------------------------------
    print("\n" + "=" * 96)
    print(" FLEET TACTICAL SANDBOX v1.0 - 최종 통계 결과 보고서")
    print("=" * 96)

    # 1. Symmetry & Control Groups
    print("\n[1] 대칭성 검증 및 제어군 (S1: Column vs Column 100 Seeds)")
    print(f"{'제어군':<10} | {'Friendly승':<11} | {'Enemy승':<10} | {'무승부':<8} | {'F_HP':<8} | {'E_HP':<8} | {'진형오차':<8} | {'충돌수':<7} | {'이상기동':<8}")
    print("-" * 96)
    for k, label in [("S1_C0", "C0 (무진형)"), ("S1_C1", "C1 (경직)"), ("S1_C2", "C2 (유연)")]:
        res = results[k]
        f_win = f"{res['win_rate_friendly']*100:.1f}%"
        e_win = f"{res['win_rate_enemy']*100:.1f}%"
        draw = f"{res['draw_rate']*100:.1f}%"
        f_hp = f"{res['mean_friendly_hp']:.1f}"
        e_hp = f"{res['mean_enemy_hp']:.1f}"
        err = f"{res['mean_formation_error']:.2f}"
        coll = f"{res['mean_collisions']:.2f}"
        anom = f"{res['mean_anomalies']:.2f}"
        print(f"{label:<10} | {f_win:<11} | {e_win:<10} | {draw:<8} | {f_hp:<8} | {e_hp:<8} | {err:<8} | {coll:<7} | {anom:<8}")

    # 2. Paired Crossed Formation Comparison
    print("\n[2] 진형 간 양방향 완전 교차실험 (Paired Crossed Comparison 100 Seeds)")
    print(f"{'대진 편성':<26} | {'Friendly승':<11} | {'Enemy승':<10} | {'무승부':<8} | {'F_HP':<8} | {'E_HP':<8} | {'순 HP 마진':<10}")
    print("-" * 96)
    pairs = [
        ("Line_vs_Column", "Friendly Line vs Enemy Column"),
        ("Column_vs_Line", "Friendly Column vs Enemy Line"),
        ("Flank_vs_Column", "Friendly Flank vs Enemy Column"),
        ("Column_vs_Flank", "Friendly Column vs Enemy Flank"),
        ("Line_vs_Flank", "Friendly Line vs Enemy Flank"),
        ("Flank_vs_Line", "Friendly Flank vs Enemy Line"),
    ]
    for k, label in pairs:
        res = results[k]
        f_win = f"{res['win_rate_friendly']*100:.1f}%"
        e_win = f"{res['win_rate_enemy']*100:.1f}%"
        draw = f"{res['draw_rate']*100:.1f}%"
        f_hp = f"{res['mean_friendly_hp']:.1f}"
        e_hp = f"{res['mean_enemy_hp']:.1f}"
        net_hp = f"{res['mean_friendly_hp'] - res['mean_enemy_hp']:+.1f}"
        print(f"{label:<26} | {f_win:<11} | {e_win:<10} | {draw:<8} | {f_hp:<8} | {e_hp:<8} | {net_hp:<10}")

    # Pairwise Net Win Rate
    print("\n >> 양방향 통합 순수 진형 승률 (진영 편향 소거 200전 종합):")
    # Line vs Column: Line as F (Line_vs_Column F_win) + Line as E (Column_vs_Line E_win)
    l_v_c_wins = results["Line_vs_Column"]["win_count_friendly"] + results["Column_vs_Line"]["win_count_enemy"]
    l_v_c_draws = results["Line_vs_Column"]["draw_count"] + results["Column_vs_Line"]["draw_count"]
    print(f"    * 횡대(Line) vs 종대(Column): Line 승률 {l_v_c_wins/200*100:.1f}%, 무승부 {l_v_c_draws/200*100:.1f}%")

    fl_v_c_wins = results["Flank_vs_Column"]["win_count_friendly"] + results["Column_vs_Flank"]["win_count_enemy"]
    fl_v_c_draws = results["Flank_vs_Column"]["draw_count"] + results["Column_vs_Flank"]["draw_count"]
    print(f"    * 포위(Flank) vs 종대(Column): Flank 승률 {fl_v_c_wins/200*100:.1f}%, 무승부 {fl_v_c_draws/200*100:.1f}%")

    l_v_fl_wins = results["Line_vs_Flank"]["win_count_friendly"] + results["Flank_vs_Line"]["win_count_enemy"]
    l_v_fl_draws = results["Line_vs_Flank"]["draw_count"] + results["Flank_vs_Line"]["draw_count"]
    print(f"    * 횡대(Line) vs 포위(Flank): Line 승률 {l_v_fl_wins/200*100:.1f}%, 무승부 {l_v_fl_draws/200*100:.1f}%")

    # 3. Dynamic Convergence & Turn Following
    print("\n[3] 수렴 및 추종 지표 (S0, S6)")
    print(f"{'시나리오':<25} | {'형성 성공률':<11} | {'평균 형성 시간':<14} | {'평균 진형 오차':<12} | {'P95 진형 오차':<12}")
    print("-" * 96)
    for k, label in [("S0_Scattered", "S0 (흩어진 위치 수렴)"), ("S6_Turn", "S6 (기함 90도 선회 추종)")]:
        res = results[k]
        succ = f"{res['formation_success_rate']*100:.1f}%"
        t_form = f"{res['mean_formation_time']:.1f} ticks" if res['mean_formation_time'] else "N/A"
        err = f"{res['mean_formation_error']:.2f}"
        p95 = f"{res['p95_formation_error']:.2f}"
        print(f"{label:<25} | {succ:<11} | {t_form:<14} | {err:<12} | {p95:<12}")

    # 4. Tactical Edge Cases (S5, S7, S8)
    print("\n[4] 특수 전술 시나리오 (S5, S7, S8)")
    print(f"{'시나리오':<30} | {'Friendly승':<11} | {'평균 틱수':<10} | {'생존자(F/E)':<12} | {'진형 오차':<10}")
    print("-" * 96)
    for k, label in [("S5_Mid_Change", "S5 (Tick 100 진형전환)"), ("S7_Damaged", "S7 (코어 50% 손상함선)"), ("S8_Sensor_Limit", "S8 (센서 탐지 제한)")]:
        res = results[k]
        f_win = f"{res['win_rate_friendly']*100:.1f}%"
        ticks = f"{res['mean_ticks']:.1f}"
        surv = f"{res['mean_friendly_survivors']:.1f} / {res['mean_enemy_survivors']:.1f}"
        err = f"{res['mean_formation_error']:.2f}"
        print(f"{label:<30} | {f_win:<11} | {ticks:<10} | {surv:<12} | {err:<10}")

    # 5. Broadside A/B Test
    print("\n[5] Broadside-aware AI 전술 기동 A/B 테스트 결과 (100 Seeds)")
    print(f"{'실험 조건':<36} | {'Friendly승':<11} | {'Enemy승':<10} | {'F_명중수':<10} | {'F_피해량':<10} | {'E_피해량':<10}")
    print("-" * 96)
    for k, label in [
        ("AB_Base_Line", "Line vs Line (Both Front-only)"),
        ("AB_Broadside_Line", "Line vs Line (F: Broadside vs E: Front)"),
        ("AB_Broadside_Column", "Column vs Column (F: Broadside vs E: Front)"),
    ]:
        res = results[k]
        f_win = f"{res['win_rate_friendly']*100:.1f}%"
        e_win = f"{res['win_rate_enemy']*100:.1f}%"
        f_hits = f"{res['mean_hits_friendly']:.1f}"
        f_dmg = f"{res['mean_friendly_dmg']:.1f}"
        e_dmg = f"{res['mean_enemy_dmg']:.1f}"
        print(f"{label:<36} | {f_win:<11} | {e_win:<10} | {f_hits:<10} | {f_dmg:<10} | {e_dmg:<10}")

    print("=" * 96)
    return results


if __name__ == "__main__":
    run_all_experiments(100)
