"""Formation System for Fleet Tactical Sandbox
References: SPEC v1.0 Section 2.2 & 5.0, 6.0
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List

from fleet_sandbox.models.vector2d import Vector2D, normalize_angle_deg


DEFAULT_FORMATIONS_PATH = Path(__file__).resolve().parent.parent / "config" / "formations.json"


class FormationDefinition:
    def __init__(self, formation_id: str, name: str, description: str, offsets: Dict[str, Tuple[float, float]]):
        self.formation_id = formation_id
        self.name = name
        self.description = description
        # offsets: {"1": (0.0, 0.0), "2": (dx, dy), "3": (dx, dy)}
        self.offsets = offsets

    def get_offset(self, ship_id: int) -> Vector2D:
        slot = ((ship_id - 1) % 3) + 1
        key = str(slot)
        if key in self.offsets:
            ox, oy = self.offsets[key]
            return Vector2D(ox, oy)
        key_raw = str(ship_id)
        if key_raw in self.offsets:
            ox, oy = self.offsets[key_raw]
            return Vector2D(ox, oy)
        return Vector2D(0.0, 0.0)


class FormationSystem:
    """Manages relative formation coordinates and world coordinate transformations."""

    def __init__(self, config_path: Optional[Path] = None):
        self.formations: Dict[str, FormationDefinition] = {}
        path = config_path or DEFAULT_FORMATIONS_PATH
        self._load_formations(path)

    def _load_formations(self, path: Path) -> None:
        if not path.exists():
            # Fallback defaults matching SPEC 5.0
            self.formations["column"] = FormationDefinition(
                "column", "종대", "기함 선두 일렬", {"1": (0.0, 0.0), "2": (0.0, -6.0), "3": (0.0, -12.0)}
            )
            self.formations["line"] = FormationDefinition(
                "line", "횡대", "기함 중앙 횡렬", {"1": (0.0, 0.0), "2": (-8.0, 0.0), "3": (8.0, 0.0)}
            )
            self.formations["flank"] = FormationDefinition(
                "flank", "포위", "3척 측면 전개", {"1": (0.0, 0.0), "2": (-10.0, 8.0), "3": (10.0, 8.0)}
            )
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for fid, finfo in data.items():
            offsets = {k: (float(v[0]), float(v[1])) for k, v in finfo["offsets"].items()}
            self.formations[fid] = FormationDefinition(
                fid, finfo.get("name", fid), finfo.get("description", ""), offsets
            )

    def get_formation(self, formation_id: str) -> Optional[FormationDefinition]:
        return self.formations.get(formation_id)

    @staticmethod
    def calculate_world_target(
        flagship_position: Vector2D,
        flagship_heading_deg: float,
        formation_offset: Vector2D,
    ) -> Vector2D:
        """
        Transform formation offset to world coordinate (SPEC 2.2):
        target_world = flagship_position + R(heading - 90°) * formation_offset
        Where +Y is forward (along flagship heading), +X is starboard (right).
        """
        # When flagship heading is 90° (North), rotation angle is 0° (Offset +Y points North)
        rot_angle = flagship_heading_deg - 90.0
        rotated_offset = formation_offset.rotate_deg(rot_angle)
        return flagship_position + rotated_offset

    def get_ship_world_target(
        self,
        formation_id: str,
        ship_id: int,
        flagship_position: Vector2D,
        flagship_heading_deg: float,
        flank_enemy_pos: Optional[Vector2D] = None,
    ) -> Vector2D:
        """Calculate desired world target for a given ship in a formation."""
        slot = ((ship_id - 1) % 3) + 1
        if slot == 1:
            # Flagship target is its own position (or guidance path, not tracking itself)
            return flagship_position

        formation = self.formations.get(formation_id)
        if not formation:
            return flagship_position

        base_offset = formation.get_offset(ship_id)

        # SPEC 5.3: Flank formation updates targets based on observed enemy position
        if formation_id == "flank" and flank_enemy_pos is not None:
            # Direct lateral flanking relative to line of sight to enemy
            to_enemy = flank_enemy_pos - flagship_position
            if to_enemy.length > 1e-5:
                enemy_bearing = to_enemy.angle_deg
                # Base offset for Escort A (2): (-10, 8) -> left flank
                # Escort B (3): (10, 8) -> right flank
                return self.calculate_world_target(flagship_position, enemy_bearing, base_offset)

        return self.calculate_world_target(flagship_position, flagship_heading_deg, base_offset)
