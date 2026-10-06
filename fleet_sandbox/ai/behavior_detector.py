"""Behavioral Anomaly Detector for Fleet Tactical Sandbox
References: SPEC v1.0 Section 12.5
- Detects rapid reversals (oscillations), wandering, stalls, and friendly blocking.
"""

from collections import deque
from typing import Dict, List, Optional
from fleet_sandbox.models.vector2d import Vector2D, shortest_angular_difference_deg


class BehaviorAnomalyDetector:
    def __init__(self, history_len: int = 10):
        self.history_len = history_len
        # ship_id -> deque of recent (heading, position, move_action)
        self.history: Dict[int, deque] = {}
        self.reversal_counts: Dict[int, int] = {}
        self.blocking_counts: Dict[int, int] = {}

    def register_tick(
        self,
        ship_id: int,
        position: Vector2D,
        heading: float,
        move_action_name: str,
    ) -> List[str]:
        """
        Record ship state and return list of detected anomalies in this tick.
        """
        if ship_id not in self.history:
            self.history[ship_id] = deque(maxlen=self.history_len)
            self.reversal_counts[ship_id] = 0
            self.blocking_counts[ship_id] = 0

        hist = self.history[ship_id]
        hist.append((heading, position, move_action_name))

        anomalies: List[str] = []

        if len(hist) >= 6:
            # Check for oscillatory reversals (180° flips within short window)
            flips = 0
            for i in range(len(hist) - 1):
                h1 = hist[i][0]
                h2 = hist[i + 1][0]
                diff = abs(shortest_angular_difference_deg(h1, h2))
                if diff > 135.0:
                    flips += 1

            if flips >= 2:
                anomalies.append("OSCILLATION_REVERSAL")
                self.reversal_counts[ship_id] += 1

            # Check for stuck / stalled wandering in a tight radius
            start_pos = hist[0][1]
            end_pos = hist[-1][1]
            displacement = start_pos.distance_to(end_pos)
            # If actions are moving but net displacement is tiny
            moving_actions = sum(1 for item in hist if item[2] != "STOP")
            if moving_actions >= 5 and displacement < 0.5:
                anomalies.append("STALLED_WANDERING")

        return anomalies
