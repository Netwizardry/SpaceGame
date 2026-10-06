"""SpaceGame v0.1 Salvo Combat Calculus
References:
- docs/spec/combat.md 7.0
- docs/spec/ships.md 4.0
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from spacegame.core.models import Fleet, ShipInstance
from spacegame.core.constants import SHIP_SALVO_PARAMS


@dataclass
class SalvoResult:
    """살보 교전 결과 데이터"""
    # Fleet A (Attacker / Side A)
    raw_firepower_a: float
    effective_firepower_a: float
    raw_defense_a: float
    effective_defense_a: float
    damage_inflicted_on_b: float
    losses_b: float  # ΔB (B 함선의 손실 척수 또는 손실 분율)

    # Fleet B (Defender / Side B)
    raw_firepower_b: float
    effective_firepower_b: float
    raw_defense_b: float
    effective_defense_b: float
    damage_inflicted_on_a: float
    losses_a: float  # ΔA (A 함선의 손실 척수 또는 손실 분율)

    distance: float
    hit_prob_a: float
    hit_prob_b: float


class SalvoEngine:
    """웨인 휴즈의 살보 모델 연산 엔진 (docs/spec/combat.md 7.0)"""

    @staticmethod
    def calculate_distance_hit_probability(distance: float, weapon_type: str = "Beam") -> float:
        """무기 체계 물리 특성에 따른 거리별 명중률 (docs/spec/ships.md 1.0 & combat.md 7.2)"""
        if distance <= 0.0:
            return 1.0

        if weapon_type == "Beam":
            # 최적 사거리 3 ~ 5 Grid, 거리 무관 일정하나 원거리(>10) 시 감쇄
            if distance <= 5.0:
                return 1.0
            elif distance <= 15.0:
                return max(0.2, 1.0 - (distance - 5.0) * 0.06)
            else:
                return max(0.05, 0.4 - (distance - 15.0) * 0.02)
        elif weapon_type == "Missile":
            # 원거리 최적 (30% 기본 보정), 장거리 유효
            if distance >= 5.0:
                return 0.9
            else:
                return 0.7  # 근거리 패널티
        elif weapon_type in ("Railgun", "Railcannon"):
            # 1~2 Grid 초근접 전용
            if distance <= 2.0:
                return 1.0
            else:
                return max(0.0, 1.0 - (distance - 2.0) * 0.3)
        return 1.0

    @classmethod
    def calculate_effective_firepower(
        cls,
        fleet: Fleet,
        distance: float = 0.0,
        weapon_type: str = "Beam",
    ) -> Tuple[float, float, float]:
        """
        함대의 실효 공격 화력(α_eff * A) 및 실효 방어 화력(y_eff * A) 연산.
        - α_eff = α_base * (1 + ATK_adm / 100) * (Aggressiveness / 100)
        - y_eff = y_base * (1 + DEF_adm / 100) * (Aggressiveness / 100)
        - 거리 보정: α_eff * Ph(d)
        낙오(Out of Range) 시 적극성 및 참모 능력치 보정 0% 적용.
        군수품 고갈 시 공격 화력 0.
        """
        alive_ships = fleet.alive_ships
        if not alive_ships:
            return 0.0, 0.0, 0.0

        # 지휘관 능력치 보정치 산출
        if fleet.is_out_of_range:
            # 낙오 패널티: 적극성 및 참모 보정 0% (docs/spec/combat.md 5.1)
            atk_adm_bonus = 0.0
            def_adm_bonus = 0.0
            aggressiveness_factor = 0.0
        else:
            atk_stat = fleet.get_max_stat("atk")
            def_stat = fleet.get_max_stat("def_stat")
            atk_adm_bonus = atk_stat / 100.0
            def_adm_bonus = def_stat / 100.0
            # 평균 적극성 (0~200) -> 100 기준 1.0
            avg_agg = sum(s.aggressiveness for s in alive_ships) / len(alive_ships)
            aggressiveness_factor = avg_agg / 100.0

        # 잔탄 확인: 군수품이 0이면 공격 불가 (Attack Power = 0)
        has_ordnance = fleet.shared_ordnance > 0 or any(s.ordnance_stock > 0 for s in alive_ships)

        total_raw_alpha = 0.0
        total_raw_y = 0.0

        for ship in alive_ships:
            params = SHIP_SALVO_PARAMS.get(ship.ship_class, {})
            base_alpha = params.get("alpha", 5.0)
            base_y = params.get("y", 2.0)
            total_raw_alpha += base_alpha
            total_raw_y += base_y

        hit_prob = cls.calculate_distance_hit_probability(distance, weapon_type)

        if has_ordnance:
            eff_alpha_total = total_raw_alpha * (1.0 + atk_adm_bonus) * aggressiveness_factor * hit_prob
        else:
            eff_alpha_total = 0.0  # 잔탄 부족 시 화력 0

        eff_y_total = total_raw_y * (1.0 + def_adm_bonus) * aggressiveness_factor

        return total_raw_alpha, eff_alpha_total, eff_y_total

    @classmethod
    def execute_salvo(
        cls,
        fleet_a: Fleet,
        fleet_b: Fleet,
        distance: float = 0.0,
        weapon_type_a: str = "Beam",
        weapon_type_b: str = "Beam",
    ) -> SalvoResult:
        """
        양측 함대 간 1회 살보 교전 연산 (docs/spec/combat.md 7.1)
        ΔA = -max(0, β_eff * B - y_eff * A) * u
        ΔB = -max(0, α_eff * A - z_eff * B) * v
        u = 1 / w_A, v = 1 / w_B
        """
        # A 화력 및 방어력
        raw_alpha, eff_alpha_a, eff_y_a = cls.calculate_effective_firepower(
            fleet_a, distance, weapon_type_a
        )
        # B 화력 및 방어력
        raw_beta, eff_beta_b, eff_z_b = cls.calculate_effective_firepower(
            fleet_b, distance, weapon_type_b
        )

        hit_p_a = cls.calculate_distance_hit_probability(distance, weapon_type_a)
        hit_p_b = cls.calculate_distance_hit_probability(distance, weapon_type_b)

        # 방어 상쇄 규칙: 공격 화력 <= 방어 화력일 경우 데미지 0 (음수 불허)
        net_dmg_on_b = max(0.0, eff_alpha_a - eff_z_b)
        net_dmg_on_a = max(0.0, eff_beta_b - eff_y_a)

        # 파손 계수 (u, v): 생존 함선들의 평균 w 또는 총 w의 역수
        alive_a = fleet_a.alive_ships
        alive_b = fleet_b.alive_ships

        # 평균 단일 함선 생존력 w
        avg_w_a = sum(s.staying_power for s in alive_a) / len(alive_a) if alive_a else 1.0
        avg_w_b = sum(s.staying_power for s in alive_b) / len(alive_b) if alive_b else 1.0

        u = 1.0 / avg_w_a if avg_w_a > 0.0 else 1.0
        v = 1.0 / avg_w_b if avg_w_b > 0.0 else 1.0

        losses_b = net_dmg_on_b * v
        losses_a = net_dmg_on_a * u

        return SalvoResult(
            raw_firepower_a=raw_alpha,
            effective_firepower_a=eff_alpha_a,
            raw_defense_a=sum(SHIP_SALVO_PARAMS.get(s.ship_class, {}).get("y", 2.0) for s in alive_a),
            effective_defense_a=eff_y_a,
            damage_inflicted_on_b=net_dmg_on_b,
            losses_b=losses_b,
            raw_firepower_b=raw_beta,
            effective_firepower_b=eff_beta_b,
            raw_defense_b=sum(SHIP_SALVO_PARAMS.get(s.ship_class, {}).get("y", 2.0) for s in alive_b),
            effective_defense_b=eff_z_b,
            damage_inflicted_on_a=net_dmg_on_a,
            losses_a=losses_a,
            distance=distance,
            hit_prob_a=hit_p_a,
            hit_prob_b=hit_p_b,
        )
