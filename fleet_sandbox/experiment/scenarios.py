"""Scenario Definitions for Fleet Tactical Sandbox
References: SPEC v1.0 Section 10.0 (S0 to S8)
"""

from typing import Tuple, List, Optional
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship, DamageZones
from fleet_sandbox.engine.formation import FormationSystem
from fleet_sandbox.engine.world_state import WorldState


def create_standard_fleet(
    faction: str,
    base_pos: Vector2D,
    heading_deg: float,
    formation_id: str = "column",
) -> List[Ship]:
    """
    Creates 3 destroyers (1: Flagship, 2: Escort A, 3: Escort B)
    matching SPEC 3.1 & 3.2. Initial positions match relative formation offsets rotated by heading.
    """
    fs = FormationSystem()
    flag_id = 1 if faction == "Friendly" else 4
    escort_a_id = 2 if faction == "Friendly" else 5
    escort_b_id = 3 if faction == "Friendly" else 6

    flagship = Ship(
        ship_id=flag_id,
        faction=faction,
        role="Flagship",
        position=base_pos,
        heading=heading_deg,
        speed=0.0,
    )

    pos_a = fs.get_ship_world_target(formation_id, escort_a_id, base_pos, heading_deg)
    pos_b = fs.get_ship_world_target(formation_id, escort_b_id, base_pos, heading_deg)

    escort_a = Ship(
        ship_id=escort_a_id,
        faction=faction,
        role="Escort A",
        position=pos_a,
        heading=heading_deg,
        speed=0.0,
    )
    escort_b = Ship(
        ship_id=escort_b_id,
        faction=faction,
        role="Escort B",
        position=pos_b,
        heading=heading_deg,
        speed=0.0,
    )
    return [flagship, escort_a, escort_b]


def build_scenario(
    scenario_id: str,
    seed: int = 42,
    friendly_ai_mode: str = "C2",
    enemy_ai_mode: str = "C2",
    friendly_broadside: bool = False,
    enemy_broadside: bool = False,
) -> WorldState:
    """Build WorldState for specified scenario S0~S8."""
    # Base starting coordinates (Friendly South heading North, Enemy North heading South)
    f_base = Vector2D(50.0, 25.0)
    e_base = Vector2D(50.0, 75.0)

    f_heading = 90.0   # North
    e_heading = 270.0  # South

    if scenario_id == "S0":
        # S0: Non-combat formation convergence test (SPEC 10.0 & User Feedback)
        # Escorts start intentionally scattered: (8, -2) and (-7, -15) relative to flagship
        flagship = Ship(
            ship_id=1,
            faction="Friendly",
            role="Flagship",
            position=f_base,
            heading=f_heading,
            speed=0.0,
        )
        escort_a = Ship(
            ship_id=2,
            faction="Friendly",
            role="Escort A",
            position=Vector2D(58.0, 23.0),  # scattered offset (8, -2)
            heading=f_heading,
            speed=0.0,
        )
        escort_b = Ship(
            ship_id=3,
            faction="Friendly",
            role="Escort B",
            position=Vector2D(43.0, 10.0),  # scattered offset (-7, -15)
            heading=f_heading,
            speed=0.0,
        )
        return WorldState(
            friendly_ships=[flagship, escort_a, escort_b],
            enemy_ships=[],
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S0",
            seed=seed,
            battle_limit_ticks=100,
        )

    elif scenario_id == "S1":
        # S1: Head-on engagement (Column vs Column)
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "column")
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S1",
            seed=seed,
        )

    elif scenario_id == "S2":
        # S2: Line vs Column
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "line")
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="line",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S2",
            seed=seed,
        )

    elif scenario_id == "S3":
        # S3: Flank vs Column
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "flank")
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="flank",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S3",
            seed=seed,
        )

    elif scenario_id == "S4":
        # S4: Line vs Flank
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "line")
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "flank")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="line",
            enemy_formation_id="flank",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S4",
            seed=seed,
        )

    elif scenario_id == "S5":
        # S5: Formation change in combat (Column -> Line at tick 100)
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "column")
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S5",
            seed=seed,
        )

    elif scenario_id == "S6":
        # S6: Flagship 90-degree turn following test
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=[],
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S6",
            seed=seed,
            battle_limit_ticks=100,
        )

    elif scenario_id == "S7":
        # S7: Damaged ship (Escort A core HP set to 50% -> 50 HP)
        f_ships = create_standard_fleet("Friendly", f_base, f_heading, "column")
        f_ships[1].zones.core = 50.0  # Core damage rate = 50%
        e_ships = create_standard_fleet("Enemy", e_base, e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S7",
            seed=seed,
        )

    elif scenario_id == "S8":
        # S8: Detection range limit (Enemy outside 30 units initially, e.g. at y=85)
        f_ships = create_standard_fleet("Friendly", Vector2D(50.0, 15.0), f_heading, "column")
        e_ships = create_standard_fleet("Enemy", Vector2D(50.0, 85.0), e_heading, "column")
        return WorldState(
            friendly_ships=f_ships,
            enemy_ships=e_ships,
            friendly_formation_id="column",
            enemy_formation_id="column",
            friendly_ai_mode=friendly_ai_mode,
            enemy_ai_mode=enemy_ai_mode,
            friendly_broadside=friendly_broadside,
            enemy_broadside=enemy_broadside,
            scenario_id="S8",
            seed=seed,
        )

    else:
        raise ValueError(f"Unknown scenario ID: {scenario_id}")


def build_custom_battle(
    friendly_formation: str,
    enemy_formation: str,
    seed: int = 42,
    friendly_ai_mode: str = "C2",
    enemy_ai_mode: str = "C2",
    friendly_broadside: bool = False,
    enemy_broadside: bool = False,
    battle_limit_ticks: int = 300,
) -> WorldState:
    """Build paired/crossed battle between arbitrary formations."""
    f_base = Vector2D(50.0, 25.0)
    e_base = Vector2D(50.0, 75.0)
    f_heading = 90.0
    e_heading = 270.0

    f_ships = create_standard_fleet("Friendly", f_base, f_heading, friendly_formation)
    e_ships = create_standard_fleet("Enemy", e_base, e_heading, enemy_formation)
    return WorldState(
        friendly_ships=f_ships,
        enemy_ships=e_ships,
        friendly_formation_id=friendly_formation,
        enemy_formation_id=enemy_formation,
        friendly_ai_mode=friendly_ai_mode,
        enemy_ai_mode=enemy_ai_mode,
        friendly_broadside=friendly_broadside,
        enemy_broadside=enemy_broadside,
        seed=seed,
        battle_limit_ticks=battle_limit_ticks,
    )
