"""WorldState Simulation Manager for Fleet Tactical Sandbox
References: SPEC v1.0 Section 2.0, 8.0, 16.0
"""

from typing import List, Dict, Optional, Tuple, Any
from fleet_sandbox.models.vector2d import Vector2D
from fleet_sandbox.models.ship import Ship
from fleet_sandbox.models.actions import MoveAction, AttackAction
from fleet_sandbox.engine.formation import FormationSystem
from fleet_sandbox.engine.observation import ObservationSystem
from fleet_sandbox.engine.movement import MovementEngine
from fleet_sandbox.engine.combat import CombatEngine, CombatEvent
from fleet_sandbox.ai.captain_ai import CaptainAI
from fleet_sandbox.ai.behavior_detector import BehaviorAnomalyDetector


class WorldState:
    """Central Tactical Sandbox World State coordinating step-by-step batch execution."""

    def __init__(
        self,
        friendly_ships: List[Ship],
        enemy_ships: List[Ship],
        friendly_formation_id: str = "column",
        enemy_formation_id: str = "column",
        friendly_ai_mode: str = "C2",
        enemy_ai_mode: str = "C2",
        friendly_broadside: bool = False,
        enemy_broadside: bool = False,
        scenario_id: Optional[str] = None,
        seed: int = 42,
        battle_limit_ticks: int = 300,
        world_width: float = 100.0,
        world_height: float = 100.0,
    ):
        self.friendly_ships = friendly_ships
        self.enemy_ships = enemy_ships
        self.friendly_formation_id = friendly_formation_id
        self.enemy_formation_id = enemy_formation_id
        self.friendly_broadside = friendly_broadside
        self.enemy_broadside = enemy_broadside
        self.scenario_id = scenario_id
        self.battle_limit_ticks = battle_limit_ticks
        self.current_tick = 0
        self.seed = seed

        # Subsystems
        self.formation_system = FormationSystem()
        self.movement_engine = MovementEngine(world_width, world_height)
        self.combat_engine = CombatEngine(hit_seed=seed, zone_seed=seed + 100)
        self.anomaly_detector = BehaviorAnomalyDetector()

        # AIs per faction
        self.friendly_ai = CaptainAI(mode=friendly_ai_mode, broadside_aware=friendly_broadside)
        self.enemy_ai = CaptainAI(mode=enemy_ai_mode, broadside_aware=enemy_broadside)

        # Telemetry & History
        self.tick_logs: List[Dict[str, Any]] = []
        self.combat_events_history: List[CombatEvent] = []
        self.collision_pairs_history: List[Tuple[int, int]] = []
        self.detected_anomalies_history: List[Tuple[int, int, str]] = []  # (tick, ship_id, anomaly)

    @property
    def all_ships(self) -> List[Ship]:
        return self.friendly_ships + self.enemy_ships

    @property
    def is_finished(self) -> bool:
        if self.current_tick >= self.battle_limit_ticks:
            return True
        friendly_alive = any(not s.is_destroyed for s in self.friendly_ships)
        if not friendly_alive:
            return True
        if self.enemy_ships:
            enemy_alive = any(not s.is_destroyed for s in self.enemy_ships)
            if not enemy_alive:
                return True
        return False

    @property
    def friendly_flagship(self) -> Optional[Ship]:
        for s in self.friendly_ships:
            if s.is_flagship and not s.is_destroyed:
                return s
        return None

    @property
    def enemy_flagship(self) -> Optional[Ship]:
        for s in self.enemy_ships:
            if s.is_flagship and not s.is_destroyed:
                return s
        return None

    def change_formation(self, faction: str, new_formation_id: str) -> None:
        """Dynamically switch formation in mid-battle (SPEC 10.0 S5)."""
        if faction == "Friendly":
            self.friendly_formation_id = new_formation_id
        else:
            self.enemy_formation_id = new_formation_id

    def step(self) -> Dict[str, Any]:
        """Execute one simulation tick using strict batch isolation (SPEC 8.1)."""
        self.current_tick += 1

        # Scenario dynamic hooks (S5, S6)
        if self.scenario_id == "S5" and self.current_tick == 100:
            self.change_formation("Friendly", "line")

        if self.scenario_id == "S6":
            f_flag = self.friendly_flagship
            if f_flag and not f_flag.is_destroyed:
                if self.current_tick == 15:
                    f_flag.heading = 45.0
                elif self.current_tick == 16:
                    f_flag.heading = 0.0

        # 1. Update weapon reload timers
        for ship in self.all_ships:
            ship.tick_reload()

        # 2. Compute formation target points for all ships
        flank_enemy_pos_f = self.enemy_flagship.position if self.enemy_flagship else None
        flank_enemy_pos_e = self.friendly_flagship.position if self.friendly_flagship else None

        f_flag = self.friendly_flagship
        e_flag = self.enemy_flagship

        # Friendly targets
        for s in self.friendly_ships:
            if f_flag and not f_flag.is_destroyed:
                target = self.formation_system.get_ship_world_target(
                    self.friendly_formation_id,
                    s.ship_id,
                    f_flag.position,
                    f_flag.heading,
                    flank_enemy_pos=flank_enemy_pos_f,
                )
            else:
                target = s.position  # Formation base lost
            s.formation_target = target
            s.formation_error = s.position.distance_to(target)
            if not s.is_flagship and s.formation_error <= 2.0:
                s.time_in_formation_tolerance += 1
            else:
                s.time_in_formation_tolerance = 0

        # Enemy targets
        for s in self.enemy_ships:
            if e_flag and not e_flag.is_destroyed:
                target = self.formation_system.get_ship_world_target(
                    self.enemy_formation_id,
                    s.ship_id,
                    e_flag.position,
                    e_flag.heading,
                    flank_enemy_pos=flank_enemy_pos_e,
                )
            else:
                target = s.position
            s.formation_target = target
            s.formation_error = s.position.distance_to(target)
            if not s.is_flagship and s.formation_error <= 2.0:
                s.time_in_formation_tolerance += 1
            else:
                s.time_in_formation_tolerance = 0

        # 3. AI Decisions (Separate Observation per Ship)
        move_actions: Dict[int, MoveAction] = {}
        attack_actions: Dict[int, Tuple[AttackAction, Optional[int]]] = {}
        ai_explanations: Dict[int, Dict[str, Any]] = {}

        for s in self.friendly_ships:
            if s.is_destroyed:
                move_actions[s.ship_id] = MoveAction.STOP
                attack_actions[s.ship_id] = (AttackAction.NONE, None)
                continue

            obs = ObservationSystem.generate_observation(
                s, self.friendly_ships, self.enemy_ships, self.friendly_formation_id, s.formation_target
            )
            move_act, reason, breakdown = self.friendly_ai.decide_movement(obs)
            atk_act, target_id = self.friendly_ai.decide_attack(obs)

            s.departure_reason = reason
            s.is_out_of_formation = s.formation_error > 2.0
            move_actions[s.ship_id] = move_act
            attack_actions[s.ship_id] = (atk_act, target_id)
            ai_explanations[s.ship_id] = {"move": move_act.name, "reason": reason, "attack": atk_act.name, "breakdown": breakdown}

        for s in self.enemy_ships:
            if s.is_destroyed:
                move_actions[s.ship_id] = MoveAction.STOP
                attack_actions[s.ship_id] = (AttackAction.NONE, None)
                continue

            obs = ObservationSystem.generate_observation(
                s, self.enemy_ships, self.friendly_ships, self.enemy_formation_id, s.formation_target
            )
            move_act, reason, breakdown = self.enemy_ai.decide_movement(obs)
            atk_act, target_id = self.enemy_ai.decide_attack(obs)

            s.departure_reason = reason
            s.is_out_of_formation = s.formation_error > 2.0
            move_actions[s.ship_id] = move_act
            attack_actions[s.ship_id] = (atk_act, target_id)
            ai_explanations[s.ship_id] = {"move": move_act.name, "reason": reason, "attack": atk_act.name, "breakdown": breakdown}

        # 4. Batch Physical Movement & Collision Resolution (SPEC 8.1)
        collision_pairs = self.movement_engine.apply_batch_movements(self.all_ships, move_actions)
        self.collision_pairs_history.extend(collision_pairs)

        # 5. Batch Combat Resolution (SPEC 8.3)
        combat_events = self.combat_engine.execute_batch_combat(self.all_ships, attack_actions)
        self.combat_events_history.extend(combat_events)

        # 6. Behavioral Anomaly Detection (SPEC 12.5)
        for s in self.all_ships:
            if not s.is_destroyed:
                act_name = move_actions.get(s.ship_id, MoveAction.STOP).name
                anomalies = self.anomaly_detector.register_tick(s.ship_id, s.position, s.heading, act_name)
                for anom in anomalies:
                    self.detected_anomalies_history.append((self.current_tick, s.ship_id, anom))

        # 7. Record Tick State
        tick_record = {
            "tick": self.current_tick,
            "friendly": [s.to_dict() for s in self.friendly_ships],
            "enemy": [s.to_dict() for s in self.enemy_ships],
            "ai_explanations": ai_explanations,
            "collisions": collision_pairs,
            "combat_events": [
                {
                    "attacker": e.attacker_id,
                    "target": e.target_id,
                    "action": e.attack_action.name,
                    "hit": e.is_hit,
                    "zone": e.hit_zone,
                    "damage": e.damage,
                    "destroyed": e.target_destroyed,
                }
                for e in combat_events
            ],
        }
        self.tick_logs.append(tick_record)
        return tick_record

    def run_simulation(self) -> Dict[str, Any]:
        """Run until completion or tick limit."""
        while not self.is_finished:
            self.step()

        # Compute summary
        friendly_alive = [s for s in self.friendly_ships if not s.is_destroyed]
        enemy_alive = [s for s in self.enemy_ships if not s.is_destroyed]

        friendly_hp = sum(s.zones.total_hp for s in self.friendly_ships)
        enemy_hp = sum(s.zones.total_hp for s in self.enemy_ships)

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

        return {
            "winner": winner,
            "total_ticks": self.current_tick,
            "friendly_survivors": len(friendly_alive),
            "enemy_survivors": len(enemy_alive),
            "friendly_hp": friendly_hp,
            "enemy_hp": enemy_hp,
            "friendly_losses": len(self.friendly_ships) - len(friendly_alive),
            "enemy_losses": len(self.enemy_ships) - len(enemy_alive),
            "collisions_count": len(self.collision_pairs_history),
            "anomalies_count": len(self.detected_anomalies_history),
        }
