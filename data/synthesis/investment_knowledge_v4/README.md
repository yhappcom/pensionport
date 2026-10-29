# 박곰희TV V4 — 투자 의사결정 지식 연구 프로토콜

기준일: 2026-10-29  
작업 브랜치: `feat/subtitles-incremental-registry-20261009`  
전체 연구 목표: 791편

> **2026-10-29 V4 end-to-end closure clarification:** The [canonical research and decision-use standard, section 6.1](https://github.com/yhappcom/pensionport/blob/main/docs/RESEARCH_DECISION_USE_STANDARD_20261029.md) now requires **feasible follow-up verification and meaningful decision-model research during each video cycle** before claiming V4 deep-research completion. V3 approval, claim-index integration or a short supplemental overlay alone is insufficient. Studies 002–005 retain V3 approval, but their deep V4 work remains `V4_DEEP_RESEARCH_IN_PROGRESS` pending full material claim verification, model work, and bounded closure. External evidence gaps remain `OPEN` and block the relevant investment action. Preserve historical records and CI/evidence safeguards.

## V4의 목적
V3의 영상별 교육 주장과 영상 요약을 그대로 유지하면서, 실제 투자 의사결정 시 **검증 가능한 투자 원칙·적용 조건·반례·실행 전 확인사항**을 조회할 수 있는 별도 지식 원장을 구축한다.

## 고정 안전 원칙
1. 기존 V3 원본, 4,120개 주장, 원본 ZIP·SRT·SHA, `main` 브랜치는 변경하지 않는다.
2. 원본 발화의 **사실·조건부 주장·시나리오·화자 의견**을 구분한다.
3. 오류가 발견되어도 원본 판정을 덮어쓰지 않고, V4 정정 오버레이로 기록한다.
4. 법령·세제·상품조건은 해당 판단일의 공신력 있는 자료로 확인한다. 출처 링크만 있다는 이유로 검증 완료로 기록하지 않는다.
5. 사적연금 과세 기준과 연금계좌 법정 인출 한도 등 서로 다른 개념을 혼동하지 않는다.
6. 영상의 수익률 가정과 분배율 예시는 보장수익으로 사용하지 않는다.
7. 공식자료 근거가 확인된 일반 원칙도 자동으로 개인별 매수·매도·계좌 변경 승인에 해당하지 않는다.
8. 원본 SRT가 부족하거나 개인별 보증금리·계약조건이 필요한 경우 `OPEN`과 활용 제한을 기록한다. 영상의 교육 연구는 조건부로 종료할 수 있으나 해당 미해결 주장은 자동 승인되지 않는다.
9. 영상별 완료 시 GitHub 기록 저장, 해시/주장 ID 무결성 확인, CI 확인을 각각 보고한다.

## 영상별 필수 절차
- **근거 계보:** 영상 ID, 원본 SRT SHA-256, 발화 시간/자막 인덱스, V3 주장 ID 및 원본 판정
- **구조화:** 전체 영상의 실질 투자 논점과 교육용 사례/의견을 분리
- **검증:** 공식자료 원문·시행일·모델 수식·숫자와 원본 발화를 대조
- **원칙화:** 투자에 재사용할 규칙, 적용 조건, 제외 사례와 추가로 필요한 개인 자료 명시
- **통합:** 기존 V4 원칙과 동일/보강/조건충돌/서로 다른 원칙 여부 판단. 동일성을 확인하기 전 자동병합 금지
- **결과:** `VERIFIED_RULE`, `CONDITIONAL_FRAMEWORK`, `SCENARIO_ONLY`, `OPEN`, `CORRECTION_REQUIRED` 등과 별도 개인 활용 상태
- **품질 게이트:** 영상 기록 저장 + CI 결과 + 남은 OPEN과 적용금지 항목 보고

## 첫 파일 — #1
- 영상: `sz5N9WJS310` (2026-10-05)
- V4: `data/synthesis/investment_knowledge_v4/videos/v4_001_sz5N9WJS310_20261029.json`
- 사적 원본 SRT 1,195개 구간, 등록된 SHA와 일치
- 기존 23개 주장 모두 연결하고 9개 원칙으로 재구성
- 수치 오류: 월 30만원/연 7% 가정, 7년 후 약 3,240만원 vs 10년 후 약 5,193만원(월복리 가정). 영상의 약 5,100만원은 10년 시점과 유사
- 제한: 개인별 국민연금 추납 예상액과 오래된 연금저축보험의 실제 보증금리는 추가 자료가 필요
- V4 영상 원칙은 검증/조건부 교육용으로 유지. **개인 매매·인출 변경 승인 0건**

## 다음 순서
1. #1의 조건부 및 OPEN 항목은 별도 검증 대기열로 유지한다.
2. #2부터 번호 순으로 동일한 V4 기준을 적용한다.
3. #1–260 연구를 V4로 전환하고, 이후 #261–791을 동일한 기준으로 확장한다.
4. 검증된 지식만 통합 원칙 원장에 보강하며, 법령 변경 시 최신 확인일을 갱신한다.

이 문서는 기존 연구 기록과 별개의 V4 운영 규칙이다.

## 2026-10-30 후속 품질 게이트 (#11 이후 필수)

[연구 품질·의사결정 활용 규약](../../../docs/V4_RESEARCH_SYSTEM_QUALITY_GATE_20261030.md), [차단 원장](research_quality_controls_20261030.json), [자동검사](../../../scripts/verify_v4_research_governance.py)를 신규 V4 심층 검토에 적용한다. 기존 V3/V4 사실·해시·승인을 덮어쓰지 않는다. #6~#10의 재검토 35/60, 기존 판정 유지 25/60, OPEN 14를 구별한다. 반박된 세율 일반화와 제한된 #10 가상 세후 계산은 개인 투자 의사결정으로 전파하지 않는다. 교육용 연구 완료와 L3/L4 승인·법령 해석은 독립 단계다.
