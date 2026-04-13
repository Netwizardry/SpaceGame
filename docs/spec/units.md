# 유닛 인스턴스 및 데이터 결합 (Unit Objects & Coupling)

## 1. 유닛 인스턴스 구조 (Unit Object Schema)
함대는 `Fleet` 객체 아래 여러 `Ship_Instance`를 포함하며, 각 인스턴스는 다음 데이터를 가짐.

```json
{
  "Instance_ID": "UUID",
  "Ship_Class": "Battleship",
  "Hull_ID": "Blueprint_Ref",
  "Captain_ID": "Entity_ID",  // 인물 데이터 결합
  "Aggressiveness": 100,      // 실시간 가변 수치
  "Morale": 100,
  "Current_Shield": 100,
  "Current_Armor": 150,
  "Current_Structure": 50,
  "Current_Capacitor": 500,
  "Ordnance_Stock": 200,
  "Position": {"x": 10, "y": 20}
}
```

## 2. 인물 데이터 결합 로직 (Coupling)
함선의 최종 성능은 **[함선 기본 스펙] + [지휘관 보정] + [승무원 숙련도]**의 합으로 결정됨.

### 2.1 지휘관(Captain) 보정
- **명중률:** `Base_Acc * (1 + Captain.PER / 200)`
- **회피율:** `Base_Eva * (1 + Captain.TAC / 200)`
- **전술 기동:** `Base_Speed * (1 + Captain.MOB / 100)`

### 2.2 승무원 숙련도 (Crew Rank)
함선은 교전 횟수에 따라 5단계 숙련도를 가짐.
- **신병 (Green):** 성능 80%
- **일반 (Regular):** 성능 100%
- **베테랑 (Veteran):** 성능 110%, 사기 저하 10% 감소
- **엘리트 (Elite):** 성능 125%, 사기 저하 25% 감소
- **에이스 (Heroic):** 성능 150%, 특수 전술(AP) 소모량 -20%

---
*SpaceGame-v0.1 유닛 설계 명세*
