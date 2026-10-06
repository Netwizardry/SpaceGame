"""2D CLI ANSI Renderer for Fleet Tactical Sandbox
References: SPEC v1.0 Section 15.0
"""

import os
from typing import Dict, Any, List, Optional
from fleet_sandbox.models.vector2d import Vector2D


class CLIRenderer:
    """Renders 100x100 continuous battlefield onto a 40x20 character grid with full debugging HUD."""

    def __init__(self, grid_w: int = 40, grid_h: int = 20):
        self.grid_w = grid_w
        self.grid_h = grid_h

    def render_tick(self, tick_record: Dict[str, Any], focus_ship_id: int = 1) -> str:
        tick = tick_record["tick"]
        friendly = tick_record["friendly"]
        enemy = tick_record["enemy"]
        ai_explanations = tick_record.get("ai_explanations", {})
        combat_events = tick_record.get("combat_events", [])

        # Create blank 2D grid
        grid = [["." for _ in range(self.grid_w)] for _ in range(self.grid_h)]

        # Map 100x100 world coordinates to character grid
        def world_to_screen(x: float, y: float) -> (int, int):
            # Screen y: 0 at top, self.grid_h - 1 at bottom (+Y is up in world)
            sx = int(max(0.0, min(99.9, x)) / 100.0 * self.grid_w)
            sy = int((100.0 - max(0.0, min(99.9, y))) / 100.0 * self.grid_h)
            return sx, min(self.grid_h - 1, max(0, sy))

        # 1. Draw formation targets (+)
        for s in friendly:
            if s.get("formation_target") and not s["is_destroyed"]:
                tx, ty = world_to_screen(s["formation_target"]["x"], s["formation_target"]["y"])
                grid[ty][tx] = "+"

        for s in enemy:
            if s.get("formation_target") and not s["is_destroyed"]:
                tx, ty = world_to_screen(s["formation_target"]["x"], s["formation_target"]["y"])
                grid[ty][tx] = "x"

        # 2. Draw ships
        for s in friendly:
            if s["is_destroyed"]:
                sx, sy = world_to_screen(s["x"], s["y"])
                grid[sy][sx] = "D"
            else:
                sx, sy = world_to_screen(s["x"], s["y"])
                grid[sy][sx] = "F" if not s["is_flagship"] else "★"

        for s in enemy:
            if s["is_destroyed"]:
                sx, sy = world_to_screen(s["x"], s["y"])
                grid[sy][sx] = "d"
            else:
                sx, sy = world_to_screen(s["x"], s["y"])
                grid[sy][sx] = "E" if not s["is_flagship"] else "▲"

        # Build output string
        lines = []
        lines.append("=" * 72)
        lines.append(f" [FLEET TACTICAL SANDBOX] Tick: {tick:03d} / 300")
        lines.append("-" * 72)

        for row in grid:
            lines.append("".join(row))

        lines.append("-" * 72)
        # Fleet Status
        f_alive = [s for s in friendly if not s["is_destroyed"]]
        e_alive = [s for s in enemy if not s["is_destroyed"]]
        lines.append(f" Friendly 생존: {len(f_alive)}/3 | Enemy 생존: {len(e_alive)}/3")

        # Focus Ship Debug Inspector (SPEC 15.0)
        focus_s = next((s for s in friendly if s["ship_id"] == focus_ship_id), None)
        if focus_s:
            lines.append(f" [선택 함선 F{focus_ship_id} ({focus_s['role']}) 디버그 정보]")
            lines.append(f"  - 현재 위치: ({focus_s['x']:.1f}, {focus_s['y']:.1f}) | 헤딩: {focus_s['heading']}° | 속도: {focus_s['speed']:.2f}")
            tgt = focus_s["formation_target"]
            tgt_str = f"({tgt['x']:.1f}, {tgt['y']:.1f})" if tgt else "N/A"
            lines.append(f"  - 목표 위치: {tgt_str} | 진형 오차: {focus_s['formation_error']:.2f}")
            expl = ai_explanations.get(focus_ship_id, {})
            lines.append(f"  - AI 이동: {expl.get('move', 'N/A')} | 판단 근거: {expl.get('reason', 'N/A')} | 사격: {expl.get('attack', 'NONE')}")
            zones = focus_s["zones"]
            lines.append(f"  - 손상 상태: 전{zones['front']:.0f} 좌{zones['left']:.0f} 우{zones['right']:.0f} 후{zones['rear']:.0f} 코어{zones['core']:.0f} (코어손상률: {zones['core_damage_rate']*100:.1f}%)")

        if combat_events:
            lines.append(f" [교전 이벤트: {len(combat_events)}건]")
            for ev in combat_events[:3]:
                hit_str = f"HIT ({ev['zone']}) -{ev['damage']}" if ev['hit'] else "MISS"
                lines.append(f"  * {ev['attacker']} -> {ev['target']} ({ev['action']}): {hit_str}")

        lines.append("=" * 72)
        return "\n".join(lines)
