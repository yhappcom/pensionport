# C3 신규 주제 지식 원장 — T001 (2026-11-28)

상태: T001 제한적 내부 운영 PASS / C4 착수 가능. 개인 자문 승인 아님.

## 저장 및 조회
- registry.json은 C2 고정 검토 커밋과 v2/v3 blob을 참조하며 ChatGPT가 8개 카드 범위 승인. 원문 위치·근거·제한·의존성·별도 보류를 보존.
- ledger.json은 주제 단위 승인 이벤트. ledger.mjs는 전체 검증 후 새로운 원장을 반환하고 입력을 변형하지 않음. Git 단일 커밋에 registry/ledger/code 저장. query(ledger,registry,'T001','2026-11-28')로 8개 조회.
- 모든 28쌍 관계를 수동 검토 분류: 보완 11, 구별 17. 동치·충돌은 처리 전 전체 승인 차단. 같은 이벤트 재실행은 멱등.
- 모든 카드 2026-12-31 재검토 기한; 2027년부터 재승인 전 조회0. 계산 카드 03/04 의존. 과거 행사 근거는 일반 조회 근거에서 제외.

## 실행 결과 27/27
- PASS actual 8 cards
- PASS actual rule exact
- PASS actual source exact
- PASS idempotent
- PASS serialization restart
- PASS no historical evidence in active lookup
- PASS last day
- PASS expired
- PASS before review
- PASS invalid date
- PASS unknown topic
- PASS unpublished
- PASS hold rejected
- PASS partial rejected
- PASS missing evidence rejected
- PASS missing pair rejected
- PASS conflict rejected
- PASS equivalent pending merge rejected
- PASS duplicate text rejected
- PASS missing dependency
- PASS cycle
- PASS dependent expiry
- PASS rollback on invalid revision
- PASS bad event pin
- PASS synthetic revision
- PASS lookup mutation isolated
- PASS complement actual relation

재현 명령: `node topic_knowledge/test_ledger.mjs` (Node 18+; 이번 턴에는 동일 함수 V8 직접 실행, Node 명령 자체 미실행).

## 제한
- 승인 registry는 신뢰된 운영자 입력이다. Git 커밋·blob은 이번 읽기에서 확인했으나 코드 자체가 외부 원본 또는 승인자 서명을 인증하지 않는다.
- 동치 자동 병합 미구현: 동치·충돌 모두 승인 전 차단. 실제 두 번째 주제와 실제 법령 개정 갱신은 미검증.
- 모든 카드 2026-12-31까지 조회 허용은 보수적 운영 결정이며 모든 법령의 만료일이 아니다.
- 신규 버전은 합성 시험만 수행. 과거 버전 조회는 Git 이력 필요.
- Git 원자적 커밋 및 ref lease 사용; 네트워크·서버 장애 주입 시험 미실행.
- V8에서 동일 함수 몸체 실행; Node CLI 및 CI 미실행. 첫 실행 structuredClone 미지원으로 중단되어 JSON clone으로 변경 후 전체 재실행.
- 독립 금융 정확도·자문 성능 미측정. C2 근거 제한 유지.

C4: 사전에 질문·필수 조건·반례를 고정하고 실제 원장 조회에서 투자 답변을 작성해 비교 평가. 기존 엔진/원장/F3 STOP 유지.
