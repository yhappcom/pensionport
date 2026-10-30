# 누적 연구 비교·통합 엔진 v1 — 설계·운영 규약

기존 V3/V4/V5 원장을 읽기 전용으로 보존하면서 신규 주장 또는 연구 결과를 **추가 이벤트**로 수집한다. 기준 지식은 `data/synthesis/investment_knowledge_001_260/curated_recurring_concepts_16.json`의 **16개 검토된 개념, 55개 독립 증거 주장**이며, 이 인덱스는 변경하지 않는다. 기존 4,120건은 별도 통합 교차원장에 남고, 이 엔진은 **16개 고위험 대표 개념에 대한 의미 병합을 위한 1차 안전 계층**이다. 즉, 39개 주제군·4,120건 전체의 의미 유사도를 모두 검증한 시스템은 아니다.

## 연구 명령이 들어왔을 때
1. 기존 영상/주장 ID·해시와 새 `data/analysis_events/<video_id>.json` 또는 `v5/videos/`를 확인. 이미 승인된 같은 원본/조건의 검증은 재사용하고 새 증거의 유효기간을 검사.
2. 기존 16개 개념과 관련된 후보를 생성한다. **완전히 일치하는 기존 claim ID+concept ID+relation은 `ALREADY_INDEXED`로 판정하고 중복 집계하지 않는다.**
3. 유사한 텍스트·동일한 ETF·같은 세제 명칭은 관계 후보일 뿐이다. 신규 주장과의 관계를 `SUPPORTS_UNDER_CONDITIONS`, `QUALIFIES_SCOPE`, `CONTRADICTS`, `CORRECTION_ONLY`, `SUPERSEDES`, `TOPIC_ONLY`, `NEW_CONCEPT`으로 분류한다. 같은 주장에 대해 기존 관계와 충돌하면 **심사 대기**.
4. 신규 연구의 원본·독립 근거·계산·실증 및 [V5 완결성 게이트](../RESEARCH_COMPLETION_GATE.md)를 통과한 주장만 **사람 또는 독립적 검토자의 관계 심사** 후 승인할 수 있다. 아직 정량/출처가 부족하면 `PENDING_REVIEW`; GitHub CI 성공으로 자동 승인하지 않는다.
5. 승인 관계는 **immutable source link + reviewed overlay**로만 생성한다. 기존 claim/판정 삭제·변경 불가. 정정·법령 개정은 `CORRECTION_ONLY`/ `SUPERSEDES`의 추가 이벤트를 만들고 기존 기록과 영향을 받는 개념의 모든 증거 ID를 연결한다. 충돌이 해소되지 않으면 해당 지식/결정을 차단한다.
6. [누적 검증 스크립트](../../scripts/verify_v5_knowledge_integration.py)가 단계별 이벤트·원본 Git blob SHA·기존 16개 개념·중복·상충·증거 참조 및 미래 연구 인증서를 검증하고 GitHub Actions에서 실행한다.

## 승인 상태
- `ALREADY_INDEXED`: 새 증거 0, 기존 검증 결과 재사용
- `PENDING_REVIEW`: 중복이 아닌 새 보강 또는 조건부 연결 후보. 정식 통합 0
- `CONFLICT_REVIEW_REQUIRED`: 원래 관계와 불일치, 상충 또는 정정. 기존 결론의 사용 제한을 검토
- `TOPIC_ONLY`: 단순 키워드/주제 유사. 의미 병합 절대 금지
- `APPROVED_OVERLAY`: **새 영상의 완결성 증빙·의미 관계 심사를 통과한 경우에만** 인덱스에 새 참조를 덧붙인다. 원본 불변, 신규 개념은 별도 등록
- `SUPERSEDES`: 이전 claim ID에 조건·법 개정·발효일과 이유를 연결하고 과거 버전을 유지하며 의존 지식을 재검토

## 실물 회귀테스트
`v5/integration/pilot_001_205_candidate_queue.json`은 기존 #1과 #205를 재수집했을 때 중복된 4건을 재집계하지 않고, #1의 계산 오류/과세 한계 및 ISA 주제 일치 후보를 정식 지식으로 승격하지 않는지 검증한다. 테스트에서는 *합성 완료 인증서 입력*으로 승인된 관계의 누적 보강·중복 재처리 안정성·정정 영향전파를 시험하되 **실제 연구 완결 편수가 늘었다고 보고하지 않는다.**

## 한계
GitHub Actions는 입력 파일에 존재하지 않는 같은 뜻의 자연어 주장을 자동으로 완전 인식하지 못한다. 별도 ChatGPT High 심사로 의미 비교/반례를 제출하되 승인 기준은 결정적인 Python 게이트가 강제한다. 공식자료의 진위를 CI가 자체 보장하는 것도 아니다. 개인자료·비공개 자막 본문·API 키를 GitHub에 올리지 않는다.
