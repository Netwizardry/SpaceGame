"""Experiment Runner for Fleet Tactical Sandbox
References: SPEC v1.0 Section 11.0, 16.0
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from fleet_sandbox.experiment.scenarios import build_scenario, build_custom_battle
from fleet_sandbox.experiment.metrics import MetricsCollector, SimulationMetrics


LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


class ExperimentRunner:
    """Executes multi-seed scenario runs, records JSONL telemetry, and aggregates metrics."""

    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = logs_dir or LOGS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run_single_simulation(
        self,
        scenario_id: str,
        seed: int,
        friendly_ai_mode: str = "C2",
        enemy_ai_mode: str = "C2",
        friendly_broadside: bool = False,
        enemy_broadside: bool = False,
        save_replay: bool = False,
    ) -> SimulationMetrics:
        ws = build_scenario(
            scenario_id,
            seed=seed,
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
        )
        ws.run_simulation()

        metrics = MetricsCollector.extract_run_metrics(ws)
        metrics.scenario_id = scenario_id

        if save_replay:
            replay_file = self.logs_dir / f"replay_{scenario_id}_{friendly_ai_mode}_seed{seed}.jsonl"
            with open(replay_file, "w", encoding="utf-8") as f:
                for log_item in ws.tick_logs:
                    f.write(json.dumps(log_item) + "\n")

        return metrics

    def run_batch_experiment(
        self,
        scenario_id: str,
        num_seeds: int = 100,
        friendly_ai_mode: str = "C2",
        enemy_ai_mode: str = "C2",
        friendly_broadside: bool = False,
        enemy_broadside: bool = False,
        save_replays: bool = False,
    ) -> Dict[str, Any]:
        metrics_list: List[SimulationMetrics] = []
        for s in range(1, num_seeds + 1):
            save_this = save_replays or (s == 1)
            m = self.run_single_simulation(
                scenario_id,
                seed=s,
                friendly_ai_mode=friendly_ai_mode,
                enemy_ai_mode=enemy_ai_mode,
                friendly_broadside=friendly_broadside,
                enemy_broadside=enemy_broadside,
                save_replay=save_this,
            )
            metrics_list.append(m)

        summary = MetricsCollector.aggregate_results(metrics_list)
        summary["scenario_id"] = scenario_id
        summary["friendly_ai_mode"] = friendly_ai_mode
        summary["enemy_ai_mode"] = enemy_ai_mode
        summary["friendly_broadside"] = friendly_broadside
        summary["enemy_broadside"] = enemy_broadside
        return summary

    def run_batch_battle(
        self,
        friendly_formation: str,
        enemy_formation: str,
        num_seeds: int = 100,
        friendly_ai_mode: str = "C2",
        enemy_ai_mode: str = "C2",
        friendly_broadside: bool = False,
        enemy_broadside: bool = False,
    ) -> Dict[str, Any]:
        """Runs paired/crossed battle between arbitrary formations across seeds."""
        metrics_list: List[SimulationMetrics] = []
        for s in range(1, num_seeds + 1):
            ws = build_custom_battle(
                friendly_formation=friendly_formation,
                enemy_formation=enemy_formation,
                seed=s,
                friendly_ai_mode=friendly_ai_mode,
                enemy_ai_mode=enemy_ai_mode,
                friendly_broadside=friendly_broadside,
                enemy_broadside=enemy_broadside,
            )
            ws.run_simulation()
            m = MetricsCollector.extract_run_metrics(ws)
            m.scenario_id = f"{friendly_formation}_vs_{enemy_formation}"
            metrics_list.append(m)

        summary = MetricsCollector.aggregate_results(metrics_list)
        summary["friendly_formation"] = friendly_formation
        summary["enemy_formation"] = enemy_formation
        summary["friendly_ai_mode"] = friendly_ai_mode
        summary["enemy_ai_mode"] = enemy_ai_mode
        summary["friendly_broadside"] = friendly_broadside
        summary["enemy_broadside"] = enemy_broadside
        return summary
