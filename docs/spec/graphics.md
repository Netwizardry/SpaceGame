# 그래픽 렌더링 및 자산 명세 (Graphics Pipeline)

## 1. 인물 그래픽 처리 (Character Rendering)
AI 생성 고해상도 초상화를 DOS 환경에 맞게 실시간 변환함.
- **원본 생성:** Stable Diffusion 기반 512x512 초상화 생성.
- **다운샘플링:** 128x128 해상도로 축소 및 픽셀화(Pixelation).
- **팔레트 매핑:** ANSI 16색 또는 EGA 64색 고정 팔레트로 인덱싱(Dithering 적용).
- **감정 오버레이:** AI 에이전트의 [심리 상태]에 따라 눈/입 모양의 도트 데칼(Decal)을 레이어링하여 표정 변화 구현.

## 2. 유닛 및 조합 그래픽 (Unit & Modular Composition)
- **Base Layer:** 함급별 함체 기본 도트 스프라이트 (고정 색상).
- **Quality Palette Swap:** 부품 레벨(Lv.1~10)에 따라 ANSI 16색 중 사용하는 인덱스를 강제 지정함.
    - **Lv.1~4 (Standard):** 어두운 계열 색상 (인덱스 0~7).
    - **Lv.5~8 (Improved):** 밝은 계열 색상 (인덱스 8~15, 'Bright' 속성).
    - **Lv.9~10 (Prototype):** 금색/청색 등 고유 색상 인덱스 및 하이라이트 픽셀 밀도 증가.
- **Modification Decals:**
    - **Heavy Mount:** 무기 스프라이트 외곽선(Outline) 한 겹 추가.
    - **Point Defense:** 무기 주변에 1x1 픽셀의 터렛 점 추가.

## 3. 함대 그래픽 및 연출
- **애니메이션:** 엔진 후면 1~2픽셀의 색상 점멸(Color Cycling)로 추진 상태 표현.
- **피격 연출:** 쉴드 타격 시 피격 부위 픽셀을 흰색(Index 15)으로 1프레임간 반전 처리.

## 4. 특수 효과 (Visual Effects)
- **살보 이펙트:** 살보 연산 결과값($\Delta$)에 비례하여 쉴드 타격 스파크, 아머 파편, 선체 폭발 도트 입자 생성.
- **연료/에너지:** 엔진 출력 상태에 따라 스프라이트 후면의 배기(Exhaust) 애니메이션 프레임 속도 조절.

---
*SpaceGame-v0.1 그래픽 처리 명세*
