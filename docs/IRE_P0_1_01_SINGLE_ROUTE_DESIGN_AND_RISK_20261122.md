# P0-1-01 분석 — E1 입력·ChatGPT 두 턴·E4·E5 정식 경로 (2026-11-22)

## 기존 코드 직접 검사와 결함

- `ire/v6/one_turn_host.py`: V6 원본 자막을 건전한 DB에 구조적으로 적재하는 채팅 호스트 지원 경로다. V123·E4·E5 최종 승인은 포함하지 않는다.
- `validation/ire-v6-frozen/v123_chat_final_gate.py`: 원본·원자·CHATGPT 검토표에 대한 V123 관문. ChatGPT 실제 호출 기능은 없다.
- `validation/ire-v6-frozen/v193_e3_two_user_turn_contract.py`: 별도 USER 명령을 나타내는 참조문자열·동일 소스/체크포인트를 검문하지만, **별도 실제 사용자 턴의 플랫폼 출처를 인증하지 않는다**. 이 함수는 `host_separate_turns_verified=False`를 반환한다.
- `validation/ire-v6-frozen/v166_e4_primary_approval_gate.py`의 `run_e4_guarded_parent`: 기존 V123→E4 원문 관문→V128 E5 원자적 SQLite 저장을 연결한다. 공인기관 원문 바이트, 소스 유형, 외부 소유자 인증을 검사하지만 원본 ETF 승인과는 무관하다.
- `validation/ire-v6-frozen/v166_e4_sealed_knowledge.py`: **외부 핀을 갖는 E4 HMAC 서명**이 있는 데이터만 정식 연구 후보 인증 데이터로 인정한다.
- 구체적 우회: `test_v166_e4_primary_approval_gate.py::test_23_same_file_plain_legacy_reopen_still_bypasses_object_only_guard`는 `PrivateKnowledgeStore`를 직접 열면 같은 DB에 E4 없는 쓰기가 가능함을 증명한다. 미인증 내용이 **정식 E4 seal**까지 획득하는 것은 아니다. 그러나 **모든 외부 쓰기 API를 물리적으로 차단했다는 증거는 없다.**

## 이번 구현: V243 단일 지원 진입점

`validation/ire-v6-frozen/v243_canonical_e1_e5_route.py`의 공개 연구 파이프라인 함수 하나인 `run_canonical_research_route`를 추가한다.

1. 원본 source SHA·소유자 고정 체크포인트 HEAD·모든 child 범위를 검사한다.
2. V193 2개 별도 사용자 명령 검문을 원본 그대로 재사용한다. **호스트 출처 검증이 FALSE라면 E4/E5 호출 전에 HOLD**.
3. 허가된 호스트 관문이 완성됐을 때만 V166 `run_e4_guarded_parent`를 호출하도록 단일 실행 경로를 구성했다. 실제 E4 승인 뒤에만 V128의 모든 child 원자적 SQLite 발행을 호출한다.
4. `E4SealedKnowledgeStore`가 아닌 과거 `PrivateKnowledgeStore` 입력은 사전에 거부한다.
5. 금융 사실 승인·개인 자문은 이 경로의 PASS가 아니다.

**합성시험 범위:** 테스트는 V193 결과를 **모의 호스트 인증 통과로 교체**하고 기존 V166·V128 실물 SQLite 코드를 끝까지 실행한다. 이 방법은 **구조 연결 검증**일 뿐 실제 별도 ChatGPT 사용자 턴을 증명하지 않는다.

## 정식 합격 전 잔여 사항

- 현재 V193은 실제 사용자 두 턴에 대한 신뢰 가능한 host-to-engine 증명 정보를 제공하지 못한다. 채팅 내부에서 실제 독립 턴으로 검증해야 하며, 가짜 `user:` 참조나 시험용 monkeypatch는 운영에 이용하지 않는다.
- 기존 Python/CLI 직접 진입로 `V126 PrivateKnowledgeStore` 등을 **외부에 노출할 수 없도록 하는 운영/패키징 경계**가 검증되지 않았다. 소프트웨어 모듈의 `__all__`만으로 외부 우회 경로 0건을 입증하지 않는다.
- **따라서 P0-1-01 합격 계약 「실행·승인·저장 정식 경로 1종, 우회 CLI 외부 공개 0」의 모든 항목을 입증하기 전에는 HOLD가 정직한 상태**다. 신규 코드 CI의 합격은 P101 항목 완료가 아니다.
- 연구 실물 ETF E3 0/13, E4 승인 0, E5 0, 독립 정확도 미검증이며 791편 연구·자문 GO 금지.

검증 후 P0-1-01에서 문제를 완결하고 해당 **동일 항목**을 재검증할 때만 PASS·다음 체크 항목 개방.

## 수행 결과 및 현재 상태 (2026-11-22)

- 신규 V243 코드·시험 초기 커밋 `9f512fcdc66d6820b950276011d26ceed1399f24`: [GitHub Actions 44997497881](https://github.com/yhappcom/pensionport/actions/runs/44997497881)에서 V243 신규 10개 중 9개 통과, 마지막 1개는 테스트 함수의 `self` 인자를 누락한 작성 오류로 FAIL. 9개의 핵심 시험은 실제 V166 E4의 합성 정부문서 mock 및 V128/SQLite 발행·원자적 차단을 통과했다. 작성 오류는 이번 후속 커밋에서 수정한다.
- 완전한 실제 별도 ChatGPT 두 턴의 신뢰 가능한 호스트 증명과 외부 쓰기 진입로 관리가 없는 상태에서는 **P0-1-01을 PASS로 승격하지 않음**. 기존 P0-0-07 PASS는 유지하고 P0-1-01만 HOLD로 기록한다.
- 수정 후 같은 SHA의 전체 통합 CI를 별도로 성공 확인해야 한다. 구조/합성 검사를 독립 금융 사실 승인으로 보고하지 않는다.
