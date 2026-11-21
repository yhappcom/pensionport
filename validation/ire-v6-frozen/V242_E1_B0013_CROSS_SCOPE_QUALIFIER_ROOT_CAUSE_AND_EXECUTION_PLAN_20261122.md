# V242 E1 재분석 및 보수적 수선 계획 — B0013 교차조건 구조 호스트 (2026-11-22)

## 실제 원본에서 확인한 직접 원인
V241 B0013은 자막 241–250, 원자 후보 C00057 1개를 보유한다. 이 원자의 실제 primary cue 246과 cue 244–247은 B0013에 있지만 **인덱스 ETF에만 적용**된다는 원문 45–47의 제한 조건을 `condition_cue_indices` 및 `context_cue_indices`에서 참조한다. `v238_e1_child_native_scope_draft.py`는 외부 cue가 한 건이라도 있는 모든 원자를 child V6 exchange에서 제외한다. 그래서 B0013 원자 배열이 빈 상태에서 `host_batch.py`의 `HOST_BATCH_EMPTY_WINDOW_NOT_EXPLICITLY_NO_ATOM`에 도달한다. 원자 의미가 없다는 뜻이 아니라 **호스트 저장 계약과 부모 문맥 보존 계약 사이의 표현 결손**이다.

## 변경하지 않는 불변 조건
1. V228 original `native.json`의 C00057 **원본 전체 구조·43–47? 아니다, 정확히 45–47** external restrictions·원문 SHA는 변경하지 않는다.
2. `UNRESOLVED` stance, `UNKNOWN` speaker, `RECOMMENDATION` kind, primary source ref 246 및 진술 내용은 원본과 일치한다.
3. 외부 조건 45–47을 **분리된 원본 바이트 핀에 항상 보관**하고, child host가 보유하는 것은 semantic verdict가 아닌 **로컬 앵커에 대한 구조적 미승인 표시**다. 이 임시 부분 표현을 V123 완료 원자·E4 적격 승인·E5 통합 지식으로 재사용할 수 없도록 별도 schema/진입점/부모 정책 차단을 둔다.
4. 기존 동결 `ire/v6/*`, V123/V127/V128/E4, `main`, 기존 V241 DB 12개를 수정하지 않는다. 새 private DB를 생성한다.
5. V231 수동 2턴 ref는 실제 호스트 암호학적 메시지 증명이 아니다. E2/E3 승인 0 유지. 지식 발행 0 유지.

## 실행 단계
A. **원본 재검증**: V228 250개, C00057의 source/context/condition, V237 task·V238 draft·V239 review, V234 parent escrow, V233 checkpoint의 SHA를 외부 pinned 값과 대조. C00057 외부 참조가 정확히 45,46,47이고 이 3개가 condition이며, parent atom 68개를 그대로 보존했는지 확인. 다른 원자에 자동 일반화하지 않는다.

B. **두 객체의 명시적 분리**: (1) 네이티브 V6 child-local 구조 앵커 후보: source cue 246, local context 244–247, local conditions 244–245, 나머지 atom 필드 원본 동일, 항상 UNRESOLVED. (2) 원본 보존된 부모 문맥 참조 sidecar: 전체 parent C00057 원자, outside 45–47 quote + SHA/roles, parent escrow SHA, review task SHA, child native digest, 원본 source SHA, 영상/구간 ID. 전체 계약 해시 SHA-256을 불변 신뢰 경계로 사용한다. 분리 전후 원본 재구성이 단 하나라도 다르면 사전 차단한다.

C. **정식 호스트 *구조적* 저장**: V6의 기존 `TransactionStore.submit_host_atomic_batch`를 변경하지 않고, B0013의 구조적 미승인 앵커 후보만 실제 native host 모델/검증으로 기록한다. V6 scope ID에 부모 sidecar의 전 SHA-256을 포함해 원본 참조가 이벤트 체인에 영속 결박되게 한다. 원본/qualifier/source note/turn2/prior-OPEN 불일치 시 SQLite 입력 전에 차단한다. 13개 자식 **구조 영수증**이 확보돼도 의미 정답 13/13이라고 선언하지 않는다.

D. **회귀 및 실물 검증**: 정상 입력, 조건 45/46/47 하나 누락, quote 변경, parent atom 변조, local 조건 삭제, 불완전 source note, 가짜 사용자 2턴 ID, 사전 pin 불일치, 사전 허가 없음, V6 DB 변조, 재실행 idempotency, E4 미승인 발행 금지까지 적대 검사. 실제 V241 12개 SQLite 불변, 신규 B0013 개인 DB 재개봉 SHA 통과, 최종 E4/E5 0.

E. **합격 정의**: `B0013 V6 구조적 host staged`는 PASS 가능한 목표. `21 cross atom 전수 의미 수선/E2 독립 정확도/E3 13구간 정식 승인/E4 공식근거/E5 발행`은 독립 채팅 검토 없이는 **HOLD**. 실패를 성공으로 표현하지 않는다.

## 진행 중 새롭게 확인한 범위 제한
- C00057의 외부 source_refs 자체는 **없다**. 외부 cue 45–47은 문맥과 조건이다. 따라서 source anchor를 바꿀 필요 없이 검토 대기 중인 조건을 parent sidecar로 분리할 수 있다.
- 이 방식은 **C00057 1건 전용으로만 시작**한다. 다른 20개 교차 원자는 외부 numeric 또는 source refs가 있을 수 있어 자동 변환 금지.
- 최종 E4 게이트는 `cross_atoms_waiting_for_semantics=21`에서 계속 거부해야 한다. native host 증빙은 금융 내용 승인 증빙으로 사용할 수 없다.
