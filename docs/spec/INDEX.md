# SpaceGame: 은하 영웅의 재건 (Galactic Legacy) - 시스템 명세서 v0.1

## 1. 프로젝트 목적 및 데이터 정의
- **목적:** 강화학습 AI 기반의 전략 시뮬레이션 엔진 구축 및 정밀 공급망 경제 모델링.
- **아키텍처:** 2D DOS 스타일 그리드 렌더링 + 상태 머신 기반 AI + 선형 회귀 물류 모델.
- **핵심 원칙:** "모든 현상은 수치화(Digitization)된다". UI는 단순 출력을 담당하며, 모든 핵심 로직은 정밀한 계산 결과값에 의존함.

## 2. 시스템 엔진 구성 (Mechanical Logic)
1.  **Dual-Scale Time Resolution:**
    - **전략 턴 (Strategic Turn):** 1턴 = 3일. 국가 경영, 함대 이동, 자원 정산 수행.
    - **전술 턴 (Tactical Turn):** 1턴 = 6시간. 함대 간 교전, 행성 점령 시퀀스 작동. 12전술 턴 = 1전략 턴.
2.  **Proposal-Based Authority:** 플레이어의 권한은 계급(Rank)과 보직에 따라 제한되며, 권한 밖의 명령은 상급자에게 [제안]하여 승인을 얻어야 함. 승인 확률은 `f(Rank, Achievement, Affinity)`에 의존.
3.  **Entity-Role State Machine:** 개체(Player/AI)의 권한(Permission)은 보직 데이터(Rank_ID)에 종속되며, 전역 상태(Global State)에 따라 실시간으로 변화함.
2.  **3-Layer Value Chain Calculus:** 1st(Raw) -> 2nd(Intermediate) -> 3rd(Final)로 이어지는 자원 변환 함수. 모든 산출량은 행성 변수와 기술 계수의 곱으로 산정.
3.  **Logical Logistics Network:** 노드(Node)와 간선(Edge) 기반의 물류망. 손실률(Loss_Rate)은 사략선(Privateer) 밀도와 함대 배치값의 차이로 계산됨.
4.  **RL-Based Psychometrics AI:** 강화학습 에이전트의 의사결정은 `f(Intelligence, Greed, Fear)` 확률 밀도 함수를 따르며, 무작위성을 배제한 기계적 최적화를 지향함.

## 3. 명세서 카탈로그 (Data Specs)
- **[천문 데이터](astronomy.md):** 항성/행성별 고정 상수, 변수 및 산출 계수.
- **[경제 로직](economy.md):** 가치 사슬 연산, 제품 레벨링 공식, 자원 정산 순서.
- **[인프라 슬롯](infrastructure.md):** 지상/궤도 슬롯 배열, 시설 건설 비용 및 소모 전력 수치.
- **[물류 알고리즘](logistics.md):** 라인 연결 로직, 손실률 계산식, 운송 우선순위.
- **[함선 모델링](ships.md):** 모듈별 스펙, 건조 자원 소모량, 기술 트리에 따른 성능 변량.
- **[개체 및 AI 프로필](entities.md):** 계급 데이터 테이블, AI 가중치 상수, 정치적 의사결정 트리.
- **[전투 연산](combat.md):** 데미지 계산식, 그리드 이동 로직, 지휘관 보너스 합산 방식.
- **[위기 상태 정의](crises.md):** 셧다운 임계값, 이벤트 발생 확률 테이블, 시스템 복구 트리.
- **[기술 아키텍처](architecture.md):** 데이터 스키마, AI API 규격, 상태 동기화 프로토콜.

---
*본 문서는 SpaceGame 프로젝트의 절대적 기계 명세이며, 모든 코드는 이 수치를 1.0의 오차 없이 반영해야 한다. 감성적 서술 및 모호한 표현을 엄격히 금지함.*
