# V173: E4 독립 완결 경로 — E5 완전 차단

검증 기준: 2026-11-19. 목표는 E4에 필요한 원본·원자·금융 공식 근거·13구간·경계 문맥·최종 채팅 의미 판정과 별도 소유자 영수증의 독립적 검증이며 E5 지식 발행은 수행하지 않는다.

## 기존 E4 병목 진단

- V172 `run_exhaustive_full_video`는 모든 E4 사전검문이 합격하면 같은 호출 안에서 `run_e4_guarded_parent`와 V128 지식 발행을 곧바로 시행했다. 따라서 E4 완료 영수증을 독립적으로 고정하여 E5를 별도로 시작하는 운영 흐름이 없었다.
- 동결 V166 E4는 공식 원전 HTTPS 원문 바이트, 발행기관, 시행일, 문맥 조건, 원자 출처와 V123 결과를 검증한다. 기존 E4 guard/SQLite 인증은 동결 유지한다.
- 실제 V166 최신 민간 보충 원장 SHA `92f57de943ce79dfa75cad2186fc17c3008ad521aa56bc9cd73f5b70916a6921`의 바이트가 현재 실행환경에서 **복구되지 않음**. 비공개 V166 메타기록의 공식 요약은 후보 70, OPEN 193, 제외 30, 13구간 HOLD. 이전 V162 ZIP은 원본 1,481 cues, 13구간 292 atoms 중 OPEN 245/승인후보 47이며 **최신 원장으로 대체 금지**.

## 구현: `v173_e4_only_parent.py`

1. 단일 명령으로 전체 구간 수·원본 SHA·부모 매니페스트 고정. 정확히 13개 스코프를 제공하지 않으면 동작 거부 (`expected_scope_count=13`).
2. 모든 child를 동결 `assess_e4_primary_authority_gate`로 검사. 첫 실패에도 다른 구간은 검사하며, 한 개라도 HOLD라면 그대로 `E4_HOLD_ALL_SEGMENTS_EXAMINED`, 지식 발행 0건.
3. **모두 E4 합격한 경우에만** 동결 V127.1 checkpoint에 연구 검토 PASS를 기록하고 `checkpoint.assemble`로 원본 전체 구간 seam/parent 정합성을 재검증. 동결 V128의 `_validate_release`로 실제 ChatGPT 부모 판정 기록의 원본·근거 SHA 및 조건·예외·반박 검토를 확인하되, 출판 함수 `publish_parent_once`, E3→V128 발행 함수 및 지식 SQLite는 전혀 호출하지 않음.
4. 부모까지 실제 PASS하면 `E4_ALL_CHILDREN_AND_PARENT_VERIFIED_AWAIT_OWNER_SEAL` 영수증 생성. 별도 소유자가 관리하는 32바이트 이상 signing key 및 외부 원본 SHA가 명시적으로 공급됐을 때만 `seal_e4_only`로 HMAC 서명 및 외부 PIN 생성. 입력 원장에는 절대 signing key 저장하지 않음.
5. 모든 반환값에 `e5_authorized=false`, `knowledge_published=false`. 원자 `OPEN`을 `PASS`로 바꾸는 동작 없음.

## 증명 한계

- 별도 API 없이 Python이 ChatGPT 모델을 자동 호출하지 못하므로, 실제 채팅 호스트가 검색·의미 검토·부모 판정을 넘겨줘야 한다.
- GitHub CI의 가짜 정부 원문·부모 채팅 판정은 전부 **합성 테스트**. 원본 금융 근거나 실제 최신 V166 13구간 승인은 인증되지 않았다.
- E4 실제 프로젝트 운영 상태 **FAIL**, E5~E7 **NOT_RUN**, 승인 지식 0건. `main`/동결 V123/V126/V128 변경 없음.