"""Replay Player for Fleet Tactical Sandbox
References: SPEC v1.0 Section 15.0 & 16.0
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fleet_sandbox.visualizer.cli_renderer import CLIRenderer


class ReplayPlayer:
    """Plays back recorded JSONL simulation telemetry."""

    def __init__(self, replay_path: Path):
        self.replay_path = replay_path
        self.records: List[Dict[str, Any]] = []
        self.renderer = CLIRenderer()
        self._load()

    def _load(self) -> None:
        if not self.replay_path.exists():
            raise FileNotFoundError(f"Replay file not found: {self.replay_path}")

        with open(self.replay_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.records.append(json.loads(line))

    @property
    def total_ticks(self) -> int:
        return len(self.records)

    def print_tick(self, tick_index: int, focus_ship_id: int = 1) -> str:
        if 0 <= tick_index < len(self.records):
            output = self.renderer.render_tick(self.records[tick_index], focus_ship_id=focus_ship_id)
            print(output)
            return output
        return ""

    def play(self, delay: float = 0.05, focus_ship_id: int = 1) -> None:
        for idx in range(len(self.records)):
            self.print_tick(idx, focus_ship_id=focus_ship_id)
            time.sleep(delay)
