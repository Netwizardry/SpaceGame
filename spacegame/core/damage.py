"""SpaceGame v0.1 3-Tier Defense & Damage Pipeline
References:
- docs/spec/ships.md 4.1 & 5.2
"""

from typing import Dict, Any, List
from spacegame.core.models import ShipInstance, Fleet


class DamagePipeline:
    """3층 방어 체계(Shield -> Armor -> Structure) 연산기"""

    @classmethod
    def apply_damage_to_ship(cls, ship: ShipInstance, incoming_damage: float) -> Dict[str, float]:
        """
        단일 함선에 대한 3층 방어 순차 데미지 적용:
        Shield (감쇄) -> Armor (저항) -> Structure (치명타)
        """
        if ship.is_destroyed or incoming_damage <= 0.0:
            return {
                "shield_absorbed": 0.0,
                "armor_absorbed": 0.0,
                "structure_damage": 0.0,
                "remaining_damage": max(0.0, incoming_damage),
            }

        rem_dmg = incoming_damage

        # 1. Shield 단계
        shield_absorbed = min(ship.current_shield, rem_dmg)
        ship.current_shield -= shield_absorbed
        rem_dmg -= shield_absorbed

        # 2. Armor 단계
        armor_absorbed = 0.0
        if rem_dmg > 0.0:
            armor_absorbed = min(ship.current_armor, rem_dmg)
            ship.current_armor -= armor_absorbed
            rem_dmg -= armor_absorbed

        # 3. Structure 단계
        structure_damage = 0.0
        if rem_dmg > 0.0:
            structure_damage = min(ship.current_structure, rem_dmg)
            ship.current_structure -= structure_damage
            rem_dmg -= structure_damage

        return {
            "shield_absorbed": shield_absorbed,
            "armor_absorbed": armor_absorbed,
            "structure_damage": structure_damage,
            "remaining_damage": rem_dmg,
        }

    @classmethod
    def distribute_fleet_damage(cls, fleet: Fleet, total_damage: float) -> List[Dict[str, Any]]:
        """
        함대 단위로 가해진 살보 데미지를 생존 함선들에게 배분하여 적용.
        생존 함선 수만큼 균등 분산 타격.
        """
        alive_ships = fleet.alive_ships
        if not alive_ships or total_damage <= 0.0:
            return []

        dmg_per_ship = total_damage / len(alive_ships)
        results = []

        for ship in alive_ships:
            res = cls.apply_damage_to_ship(ship, dmg_per_ship)
            res["ship_id"] = ship.instance_id
            res["ship_class"] = ship.ship_class
            res["is_destroyed"] = ship.is_destroyed
            results.append(res)

        return results

    @classmethod
    def regenerate_shields(cls, fleet: Fleet) -> None:
        """
        매 턴 쉴드 자동 회복 로직 (docs/spec/ships.md 5.2):
        매 턴 기본 회복(예: 최대 실드의 10%), 잔량이 25% 부근일 때 효율 최대 (가중치 1.5배).
        """
        for ship in fleet.alive_ships:
            if ship.max_shield <= 0.0:
                continue

            ratio = ship.current_shield / ship.max_shield
            # 25% 잔량일 때 회복 효율 극대화 (정규 분포 곡선 유사 가중치)
            bonus = 1.5 if 0.20 <= ratio <= 0.30 else 1.0
            base_regen = ship.max_shield * 0.10 * bonus
            ship.current_shield = min(ship.max_shield, ship.current_shield + base_regen)
