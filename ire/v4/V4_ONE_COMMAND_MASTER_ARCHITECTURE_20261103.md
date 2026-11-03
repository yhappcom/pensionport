# IRE V4 단일 명령 투자 연구 엔진 — 재설계 기준 2026-11-03
상태: 설계 완료 / 실제 단일 명령 영상 전수 실증은 미완료.

## 제품 요구
한 번의 사용자 채팅 명령으로 원본 확보, 의미 분석, 공식 근거 검색, 오류/누락 검수, 기존 지식 대조, 누적 지식 반영, 최종 보고까지 **같은 요청 안에서** 수행한다. 각 문맥마다 '진행'을 요구하는 것은 제품 실패. 채팅 종료 후 호스트 자동 재시작은 **요구하지 않음**. 별도 모델 API도 사용하지 않음. 시스템 한도 초과시 완료를 허위 선언하지 않고 미처리 작업과 한계를 명시한다.

## 구성 및 책임
**Chat 실행 컨트롤러:** 현재 ChatGPT 모델이 실제 SRT 읽기, 완전한 원자 명제 해석, 공식 출처 검색/비교, 검토 결정을 수행하고 다음 단계로 이어 간다. 호스트가 실제로 계속 실행되는 범위는 실측으로 증명해야 한다.
**결정적 V4 코어:** V3의 source/v3_adaptive/chat_bridge/semantics/numeric/evidence/relations/release 기능을 검증된 어댑터로 재사용한다. 오직 원문 무결성, 입력 스키마, 인용, 수치 연산, 작업 큐, 누락 감지, append-only 영수증, 지식 diff/승인 차단을 수행하며 Python이 모델 의미 판단을 자체 생성한 것처럼 꾸미지 않는다.
**독립 검토자:** 사전에 봉인한 미노출 원자 주장 정답/판정 및 금융 적용성 검토. 같은 모델의 자기 평가는 독립 골드가 아님.

## 실행 파이프라인
1. SOURCE_LOCK: 원본 SHA, 영상 ID, V3 adaptive planner 버전 및 primary cue 전수 배정, 기존 지식 revision 잠금.
2. QUEUE: 미처리 창·주장·근거·관계 조사 큐 생성. 이미 저장된 내용은 hash/원본 일치 검사 후에만 재사용.
3. SEMANTIC: ChatGPT가 실제 primary cue를 읽고 복합 발언을 원자 명제로 분해. 조건/단위/시점/부정/예외/가정 분리, 매 cue LINKED/NONCLAIM/UNRESOLVED 작성.
4. GROUNDING: 정식 V3 accept, 인용 부분문자열·수치·인과/문맥 이탈 검증. 거절된 창은 재해석/정정하고 결과 이력 저장. halo cue 인용 금지.
5. EVIDENCE: 주장별 금융 규정/상품/실증/수치 의무 생성. 공식 원문 검색+원본 bytes SHA+발행기관+효력일+대상·예외까지 검토. 미확정 주장 OPEN, URL 하나만으로 사실 인증하지 않음.
6. RELATION: 기존 지식 원장과 SAME/EXTENDS/CONFLICTS/TIME_SUPERSEDED/DIFFERENT_SCOPE/PENDING을 원문 및 적용조건별로 비교. 검증되지 않은 동치 병합 금지.
7. CLOSURE: 모든 요청 영상/창/primary cue 처리, 필요한 조사 시도·관계 검토·OPEN 사유, 기존 지식 변경 diff, 연구 보고의 증거 해시 봉인.
8. ADVISORY: 확인된 범위만 자문 검색 대상으로 제시; 질문별 최신성·적합성 미확정이면 권고 보류. 학습 보고 완결이 개인 투자 자문 승인과 같지 않음.

## 소프트웨어 계약
Request: request_id, 원본 셀렉터, 소스 SHA, planner revision, 기준일, 기존 knowledge digest, user_request_count.
Window: session_id, window_id, primary/halo IDs, primary text hash, packet SHA.
Answer: 정확한 cue quote, 금융 frame, 숫자·단위·부정/조건, cue disposition 전수.
Evidence: issuer, URL, verified original hash, effective date, jurisdiction, scope, quote, checked_at, OPEN reasons.
Relation: 양쪽 claim ID/SHA, prior knowledge revision, relation type, condition/effective-date delta, reason.
Closure: expected/actual cues/windows, UNPROCESSED 수, OPEN 사유, verified scope, relation audit, knowledge diff, report seal, host constraints.

## 완료 게이트
- **UNPROCESSED 창이 하나라도 있으면 REPORT_COMPLETE 금지.**
- 분석 완료 이후 공식 근거가 부족한 **개별 주장**은 OPEN 가능. 조사 의무를 실제 수행하지 않은 것을 OPEN으로 둔갑 금지.
- SOURCE_COVERAGE, RESEARCH_REPORT_COMPLETE_WITH_OPEN, FACT_VERIFIED_IN_SCOPE, ADVISORY_ELIGIBLE은 서로 다른 승인 수준.
- 합성 CI·Python 복구 테스트는 실제 금융 의미 재현율이나 단일 명령 완주 증거가 아님.
- 호스트 실행 한도에 따른 중단은 STOPPED_LIMIT+잔여 큐+실행 영수증으로 남긴다. 자동 재시작으로 위장하지 않는다.

## 개발·시험 순서
P0: #1 원본 **V3 adaptive 81문맥**에서 사용자 최초 요청 한 번으로 의미→근거→관계→최종 보고 전수 실증. P0 GO는 81/81, 원본 cue 누락 0, 사용자 추가 진행 0, 실제 신규 모델 의미 판단 및 근거/지식 diff/최종 보고 기록이 있을 때만.
P1: 실증된 실행 계약을 지속 상태/정식 V3 접수·검증 코어로 제품화.
P2: #1 전수 연구의 독립 재현, 신뢰도/OPEN 정리.
P3: #1~#5 **총 346문맥** 교차 주장/누적 지식 통합.
P4: 신규 미노출 인간 독립 골드/자문 안전성 검증.
기존 v003·개인 원본·main 수정 금지.

## 기준 관계
2026-11-03의 사용자가 정정한 요구사항이 최우선이다. 이전 **P0-R 사후 자동재시작 필수** 문서와 **12문맥 P0-C GO=전체 P0 GO** 문서는 현행 제품·릴리스 승인 근거가 아니다. [상세 시험 계획](V4_ONE_COMMAND_IMPLEMENTATION_AND_TEST_PLAN_20261103.md)과 [실패·승인 정책](V4_ONE_COMMAND_FAILURE_AND_RELEASE_MATRIX_20261103.md)을 함께 적용한다.
