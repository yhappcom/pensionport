# P205 연구 엔진 V3 재설계 — 2026-11-24

## 실패 사실과 변경 범위

#271 V1: 53/93, 53/94, 고위험 FN35. #270 V2: 60/133, 60/146, 고위험 FN77. 두 독립적이지 않은 내부 평가 원점수와 실패 cohort를 그대로 유지. 비교 불가능한 영상의 점수 차이를 개선폭으로 해석하지 않는다. #270 V2 화자·입장 28개 불일치 중 14개 역할만 다름; 원문 의미범위26; 조건14; 종류13; 숫자7. 동일 스키마가 의미 단위 일관성을 보장하지 않는다.

최근 CI 45349799786 job 138293268207에서 2692개 검사 중 test_v166_e4_live_official_origin 한 개 실패. NTS와 MOLEG HTTPS timeout. 5개 다른 job 성공. 실제 공식 근거 접근 실패는 보존하며 E4 승인이나 CI 통과로 대체하지 않는다. 코드 검증과 온라인 공식 출처 접근성을 구분해 기록한다. 재실행으로 성공하더라도 실패 원인은 사라지지 않는다.

## V3 구조

1. S0: 원본 SHA와 manifest/cue census에 결합한 고정 좌표 그리드. cue + Unicode codepoint start/end. 원문 문자를 수정하지 않는다. 기계 좌표는 의미 정답이 아니다.
2. S1: TURN1 ChatGPT가 독립 판단 가능 predicate, 직접 근거 span, 조건/예외 edge, 참가자 ID·불명확 상태·발화 기능·인용 대상·극성·양태, 문자 위치 수치 binding을 작성한다. 원문 잔여 부분은 명시 NONCLAIM 또는 OPEN. 엔진은 source coordinates에서 전체 구간의 기계적 연결 검증.
3. S2: 첫 graph 및 실제 원문/판정 기준 hash 동결, 원본만 읽는 TURN2 별도 그래프 작성. 같은 compiler. 발화자 텍스트 추정과 실제 정체 분리. 모델 내적 독립성 보장 안 함.
4. S3: 소스 span overlap connected component로 1:1, 1:N, N:1, N:M, 미대응 진단. 이는 원문 범위 중복의 후보일 뿐 의미 등가나 TP가 아니다. 분할·결합 후보의 의미 보존, 조건·숫자·화자·반박을 ChatGPT가 별도 판정. 양쪽 그래프가 틀릴 수 있다. 최초 점수는 수정하지 않는다.
5. S4: 명시된 9축의 1:1 일치만 TP. 95/98/0 그대로; 고위험/중대 미대응 및 OPEN/unbound numeric 차단. 참가자 alias는 명시 근거와 리뷰 이유를 요구, unknown 자동 동일 금지. 과거 V1/V2 실패를 새로운 평가로 덮지 않는다.
6. S5: TURN2의 정정안 및 분할/결합 계보는 별도 append-only revision, 최초 동결 자료 변경 금지. E3의 의미 판정/공식 근거 E4/원자적 E5의 native projection 및 cross-cue numeric 지원은 추가 구현 필수. 단순 legacy projection으로 숫자·발언 역할을 잃은 자료를 승인하지 않는다.

## 현재 구현/한계

ire/v6/semantic_source_graph.py: S0-S4의 좌표 그리드, private graph compiler, 문자별 근거 census, cross-cue numeric literal binding, source overlap components, explicit 9축 내부 진단 산술. 자동 의미 추론이나 금융 참값 판정은 아니다. 부분 회귀와 합성 테스트로 검증할 수 있지만, 두 실제 전체 리뷰의 판정 일관성 향상은 아직 미측정. 신규 preregistration/actual distinct turn freeze/protected store/E3-E5 adapter와 V3 공개 승인 관문은 미구현. 기존 V1/V2 live PASS 경로 차단; 기존 독립 인증 그대로. 완전한 S5 경로 검증 전에 새 holdout 사용 금지. 기존 277/288 미착수 자료 보존.

## 순차 작업

R3-01 기존 두 실패 보존·CI 원인 기록; R3-02 고정 좌표와 source graph compiler; R3-03 실제 두 실패 전체의 source overlap 진단 및 실제 cross-cue 수치/분할 회귀; R3-04 명시 semantic dispute/분할·결합 계보와 양방향 원문 검증, two-turn freeze; R3-05 native E3-E5 무손실 연계 및 승인 차단; R3-06 미노출 새 cohort 사전 등록 및 실제 두 턴 운영 평가. 각 단계의 실제 증명 없으면 다음 단계 진입 금지. P205 HOLD, 16/60 PASS, 43 BLOCKED. 기준 완화·독립 인증·금융 승인 없음.
