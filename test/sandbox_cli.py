#!/usr/bin/env python3
"""Fleet Tactical Sandbox - Interactive CLI Battlefield Viewer & Simulator
References: SPEC v1.0 Section 15.0 & 21.0
"""

import sys
import time
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fleet_sandbox.experiment.scenarios import build_scenario
from fleet_sandbox.visualizer.cli_renderer import CLIRenderer
from fleet_sandbox.visualizer.replay_player import ReplayPlayer


def main():
    parser = argparse.ArgumentParser(description="Fleet Tactical Sandbox 2D CLI Simulator")
    parser.add_argument("--scenario", type=str, default="S1", help="Scenario ID (S0~S8)")
    parser.add_argument("--seed", type=int, default=42, help="Random integer seed")
    parser.add_argument("--mode", type=str, default="C2", help="Friendly AI mode (C0, C1, C2)")
    parser.add_argument("--delay", type=float, default=0.08, help="Tick rendering delay in seconds")
    parser.add_argument("--replay", type=str, default=None, help="Path to JSONL replay file to play")
    parser.add_argument("--inspect", type=int, default=1, help="Ship ID to inspect in HUD (1~3)")
    args = parser.parse_args()

    if args.replay:
        print(f">> Playing recorded replay from: {args.replay}")
        player = ReplayPlayer(Path(args.replay))
        player.play(delay=args.delay, focus_ship_id=args.inspect)
        return

    print(f">> Starting Live Tactical Simulation: Scenario {args.scenario}, Mode {args.mode}, Seed {args.seed}")
    time.sleep(1.0)

    ws = build_scenario(args.scenario, seed=args.seed, friendly_ai_mode=args.mode, enemy_ai_mode=args.mode)
    renderer = CLIRenderer()

    while not ws.is_finished:
        if args.scenario == "S5" and ws.current_tick == 100:
            ws.change_formation("Friendly", "line")

        record = ws.step()
        print("\033[H\033[J", end="")  # Clear terminal
        print(renderer.render_tick(record, focus_ship_id=args.inspect))
        time.sleep(args.delay)

    # Final summary
    summary = ws.run_simulation()
    print("\n" + "=" * 72)
    print(" [전투 시뮬레이션 종결 보고]")
    print(f" - 승자: {summary['winner']}")
    print(f" - 진행 틱: {ws.current_tick} 틱")
    print(f" - Friendly 잔여 HP: {summary['friendly_hp']:.1f} (생존: {summary['friendly_survivors']}/3)")
    print(f" - Enemy 잔여 HP: {summary['enemy_hp']:.1f} (생존: {summary['enemy_survivors']}/3)")
    print(f" - 충돌 횟수: {summary['collisions_count']} 건")
    print(f" - 비정상 이상행동 탐지: {summary['anomalies_count']} 건")
    print("=" * 72)


if __name__ == "__main__":
    main()
