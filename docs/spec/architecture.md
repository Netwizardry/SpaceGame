# 기술 아키텍처 (Technical Architecture)

## 1. 강화학습 기반 AI 엔진 (RL-based AI Engine)
- **에이전트 (Agents):** 각 제독과 장관 NPC는 독립적인 RL 에이전트로 작동.
- **보상 함수 (Reward Functions):** 보직에 따라 다른 보상 체계(재무장관: 자글 최대화, 사령관: 승률 최대화).
- **심리 필터 (Psychological Filter):** 지능, 탐욕, 공포 수치를 가중치로 사용하여 RL의 최적 판단을 확률적으로 왜곡.

## 2. 데이터 기반 공급망 및 경제 엔진
- **Event-Driven Logistics:** 턴 정산 시 로지컬 라인을 따라 창고 데이터 동기화.
- **JSON Data Models:** 3단계 산업 가열 사슬과 제품 레벨(Lv.1~10) 스키마 정의.
- **Dynamic Market Price Engine:** 은하계 전체의 수요/공급을 취합하여 가격 변동률 계산.

## 3. 2D 도트 UI 및 AI 자산 관리
- **Window-based UI:** 90년대 도스(DOS) 감성을 재현한 윈도우 창 시스템.
- **AI Art Pipeline:** 스테이블 디퓨전(또는 유사 엔진)으로 생성된 고해상도 초상화 및 배경을 2D 레이어로 합성.
- **레트로 쉐이더:** 현대적인 해상도에서도 고전 도트의 느낌을 살리는 후처리 기법 적용.

## 4. 모듈 및 상태 관리 (State Management)
- **Central State Store:** 은하계 지도, 인물 DB, 시장 가격, 물류 노선을 통합 관리.
- **Undo/Redo (Strategic Turn):** 턴 종료 전까지의 명령을 되돌릴 수 있는 히스토리 관리.

---
*FHDL-SG-v0.1 기술 아키텍처 명세*
