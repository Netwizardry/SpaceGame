"""Metrics Collector and Statistical Analysis for Fleet Tactical Sandbox
References: SPEC v1.0 Section 12.0 & 13.0
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


def calculate_confidence_interval_95(wins: int, total: int) -> Tuple[float, float]:
    """Calculate 95% Wilson Score Interval for win rate proportion."""
    if total <= 0:
        return 0.0, 0.0
    z = 1.96  # 95% confidence
    p = wins / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


@dataclass
class SimulationMetrics:
    scenario_id: str
    seed: int
    winner: str
    total_ticks: int
    friendly_survivors: int
    enemy_survivors: int
    friendly_hp: float
    enemy_hp: float
    friendly_damage_dealt: float
    enemy_damage_dealt: float
    shots_fired_friendly: int
    hits_landed_friendly: int
    collision_count: int
    anomaly_count: int

    # Formation error stats (excluding flagship)
    mean_formation_error: float
    median_formation_error: float
    p95_formation_error: float
    formation_achieved_tick: Optional[int] = None


class MetricsCollector:
    """Collects and computes aggregate metrics over multiple simulation runs."""

    @staticmethod
    def extract_run_metrics(world_state) -> SimulationMetrics:
        # Formation errors for friendly escorts (ship_id != 1)
        escort_errors: List[float] = []
        achieved_tick: Optional[int] = None

        for record in world_state.tick_logs:
            tick = record["tick"]
            all_in_tol = True
            for s_info in record["friendly"]:
                if s_info["ship_id"] != 1 and not s_info["is_destroyed"]:
                    err = s_info["formation_error"]
                    escort_errors.append(err)
                    if err > 2.0:
                        all_in_tol = False

            # Check 5 consecutive ticks in tolerance
            if all_in_tol and achieved_tick is None and tick >= 5:
                # verify past 5 ticks
                streak = True
                for past_r in world_state.tick_logs[max(0, tick - 5):tick]:
                    for s_info in past_r["friendly"]:
                        if s_info["ship_id"] != 1 and not s_info["is_destroyed"] and s_info["formation_error"] > 2.0:
                            streak = False
                if streak:
                    achieved_tick = tick

        escort_errors.sort()
        if escort_errors:
            mean_err = sum(escort_errors) / len(escort_errors)
            med_err = escort_errors[len(escort_errors) // 2]
            p95_idx = int(len(escort_errors) * 0.95)
            p95_err = escort_errors[min(len(escort_errors) - 1, p95_idx)]
        else:
            mean_err = med_err = p95_err = 0.0

        friendly_alive = [s for s in world_state.friendly_ships if not s.is_destroyed]
        enemy_alive = [s for s in world_state.enemy_ships if not s.is_destroyed]

        friendly_dmg = sum(s.damage_dealt for s in world_state.friendly_ships)
        enemy_dmg = sum(s.damage_dealt for s in world_state.enemy_ships)
        shots = sum(s.shots_fired for s in world_state.friendly_ships)
        hits = sum(s.hits_landed for s in world_state.friendly_ships)

        friendly_hp = sum(s.zones.total_hp for s in world_state.friendly_ships)
        enemy_hp = sum(s.zones.total_hp for s in world_state.enemy_ships)

        if len(friendly_alive) > len(enemy_alive):
            winner = "Friendly"
        elif len(enemy_alive) > len(friendly_alive):
            winner = "Enemy"
        else:
            if friendly_hp > enemy_hp:
                winner = "Friendly"
            elif enemy_hp > friendly_hp:
                winner = "Enemy"
            else:
                winner = "Draw"

        return SimulationMetrics(
            scenario_id="scenario",
            seed=world_state.seed,
            winner=winner,
            total_ticks=world_state.current_tick,
            friendly_survivors=len(friendly_alive),
            enemy_survivors=len(enemy_alive),
            friendly_hp=friendly_hp,
            enemy_hp=enemy_hp,
            friendly_damage_dealt=friendly_dmg,
            enemy_damage_dealt=enemy_dmg,
            shots_fired_friendly=shots,
            hits_landed_friendly=hits,
            collision_count=len(world_state.collision_pairs_history),
            anomaly_count=len(world_state.detected_anomalies_history),
            mean_formation_error=mean_err,
            median_formation_error=med_err,
            p95_formation_error=p95_err,
            formation_achieved_tick=achieved_tick,
        )

    @staticmethod
    def aggregate_results(metrics_list: List[SimulationMetrics]) -> Dict[str, Any]:
        n = len(metrics_list)
        if n == 0:
            return {}

        wins = sum(1 for m in metrics_list if m.winner == "Friendly")
        draws = sum(1 for m in metrics_list if m.winner == "Draw")
        losses = sum(1 for m in metrics_list if m.winner == "Enemy")

        win_rate = wins / n
        ci_low, ci_high = calculate_confidence_interval_95(wins, n)

        mean_err = sum(m.mean_formation_error for m in metrics_list) / n
        mean_ticks = sum(m.total_ticks for m in metrics_list) / n
        mean_friendly_hp = sum(m.friendly_hp for m in metrics_list) / n
        mean_enemy_hp = sum(m.enemy_hp for m in metrics_list) / n
        mean_collisions = sum(m.collision_count for m in metrics_list) / n
        mean_anomalies = sum(m.anomaly_count for m in metrics_list) / n

        formation_times = [m.formation_achieved_tick for m in metrics_list if m.formation_achieved_tick is not None]
        formation_success_rate = len(formation_times) / n
        mean_formation_time = sum(formation_times) / len(formation_times) if formation_times else None

        mean_surv_f = sum(m.friendly_survivors for m in metrics_list) / n
        mean_surv_e = sum(m.enemy_survivors for m in metrics_list) / n
        mean_hits_f = sum(m.hits_landed_friendly for m in metrics_list) / n
        mean_dmg_f = sum(m.friendly_damage_dealt for m in metrics_list) / n
        mean_dmg_e = sum(m.enemy_damage_dealt for m in metrics_list) / n
        all_p95 = [m.p95_formation_error for m in metrics_list]
        mean_p95 = sum(all_p95) / len(all_p95) if all_p95 else 0.0

        return {
            "total_runs": n,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_count_friendly": wins,
            "win_count_enemy": losses,
            "draw_count": draws,
            "win_rate": round(win_rate, 4),
            "win_rate_friendly": round(win_rate, 4),
            "win_rate_enemy": round(losses / n, 4),
            "draw_rate": round(draws / n, 4),
            "ci_95": (round(ci_low, 4), round(ci_high, 4)),
            "mean_formation_error": round(mean_err, 3),
            "p95_formation_error": round(mean_p95, 3),
            "formation_success_rate": round(formation_success_rate, 4),
            "mean_formation_achieved_tick": round(mean_formation_time, 2) if mean_formation_time else None,
            "mean_formation_time": round(mean_formation_time, 2) if mean_formation_time else None,
            "mean_battle_duration_ticks": round(mean_ticks, 2),
            "mean_ticks": round(mean_ticks, 2),
            "mean_friendly_hp": round(mean_friendly_hp, 2),
            "mean_enemy_hp": round(mean_enemy_hp, 2),
            "mean_friendly_survivors": round(mean_surv_f, 2),
            "mean_enemy_survivors": round(mean_surv_e, 2),
            "mean_hits_friendly": round(mean_hits_f, 2),
            "mean_friendly_dmg": round(mean_dmg_f, 2),
            "mean_enemy_dmg": round(mean_dmg_e, 2),
            "mean_collisions_per_run": round(mean_collisions, 2),
            "mean_collisions": round(mean_collisions, 2),
            "mean_anomalies_per_run": round(mean_anomalies, 2),
            "mean_anomalies": round(mean_anomalies, 2),
        }
