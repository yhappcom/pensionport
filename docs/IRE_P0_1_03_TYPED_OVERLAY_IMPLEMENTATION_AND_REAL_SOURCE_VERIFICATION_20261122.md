# P0-1-03 — ETF 21 교차 원자 / 49 typed edge / B0013 전체 부모 문맥 정식 입력 연계

기준 2026-11-22 · 허용 작업 ID P0-1-03 · 실물 금융 의미 승인이 아닌 **E1 typed-source input** 범위

## 실제 결함과 원인

V238 자식 V6 스키마는 자식 구간 바깥의 조건·문맥·숫자를 보존할 수 없어 21개 cross 원자를 미승인 sidecar로 분리한다. B0013의 C00057(primary cue 246)은 이 때문에 원래의 인덱스 ETF 적용 제한 조건 45–47을 잃지 않도록 B0003 부모 원문을 계승해야 한다. V244는 원본 출처 그래프를 복원했으나, 정식 V243 E4 진입의 원문 검토 입력에는 전체 부모 typed 원자가 항상 연결되지 않았다.

## 수정된 실행 계약

1. `v245_e1_typed_parent_review_overlay.py`: 비공개 원본 SRT/V6/250 cue/E3 task/2,278 pairs를 외부 SHA 핀으로 V244 전수 재검증하고, 68개 **원본 부모 원자 전체**와 모든 source/context/condition/exception/numeric 필드를 수정하지 않고 각 검토 자식에 전달한다. 자식 13개 입력마다 로컬 원문, 원자 전체, 다른 자식의 정확한 원문·역할·원자 SHA를 포함한다. 원문은 Git에 업로드하지 않는다.
2. V245는 원본 V6 원자 배열 순서로 49개 외부 cue edge를 정렬하여 V244의 실제 그래프와 정확히 동일한지 검문한다. 원자·조건·역할·숫자·예외·출처가 하나라도 변경되면 **거부**한다.
3. 공식 `v243_canonical_e1_e5_route.py`는 **13개 이상의 자식**이 있는 원본에 V245 typed overlay와 바이트·부모 SHA 핀을 필수로 받는다. 정확한 child source scope가 다르거나 overlay가 없으면 승인 이전에 차단한다.
4. V243이 검토를 실행하는 경우 원본 그대로의 V128 **정확히 4필드** child packet을 유지하고, typed context SHA 확인은 **별도 (packet, acknowledgement) 이중 반환**으로 처리한다. 승인 패킷에 임의 필드를 주입하지 않는다.
5. 21개 cross 원자는 현재 E2/E3 의미 결정이 없으므로 **전부 OPEN**이다. 따라서 실제 ETF 입력은 `HOLD_PARENT_CROSS_CHILD_SEMANTIC_REVIEW_REQUIRED`와 비공개 `formal_child_review_inputs_private`만 출력하고 E4/E5를 호출하지 않는다. *무조건 HOLD를 임의로 PASS로 만드는 방식이 아니라 E1 의미 보존 입력을 실제로 완성한 것이다.* 이후 E2/E3에서는 원문 선행 의미검토 및 공식근거 판단을 별도 수행해야 한다.

## 실제 원본 재검증

- 사용자 Library V228 비공개 ZIP SHA: `9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397`; 원본 SRT SHA `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`. V244 출처 그래프 SHA `4f4ab61ddfdc7c1d9d4d7ef7b07568911ab198629d9299284fbd05fa73db5a8f`.
- 원본 250/250 cue, 자식 13/13, 부모 원자 68/68, 21 cross 원자, 외부 source edge 49/49. 역할별: context 49, condition 29, numeric 3, exception 0, external primary 0. 정확한 원문 바이트와 SHA를 비공개 독립 재검토했다.
- B0013 C00057 원본 부모 원자 SHA `88f8d07be8844f1715e921faaa6c16950bd666fa99690f23038fbf51f20a7644`. primary cue 246, 외부 condition 45·46·47(B0003), local condition 244·245, 원본 numeric/exception = 빈 목록을 그대로 보존했다.
- 13개 자식별 원문·부모 원자 포함 검토 입력의 SHA와 통합 typed overlay SHA `9d4b32d0850cf6f188b9bd77fd0cfc72d009c540422a9a2ae6b58b4dbdbd1662`는 [SHA-only 영수증](IRE_P0_1_03_OWNER_ETF250_TYPED_OVERLAY_SHA_ONLY_20261122.json)에만 노출한다. 원문이나 투자관련 민감한 발언은 공개하지 않는다.

## 시험 범위와 승인 한계

- V245 신규 소프트웨어 회귀 9/9; V243 구조/거부/실제 frozen V166→V128 SQLite 테스트 25/25; V200~V245 전체 동결 cohort 891건 PASS.
- 원본 실물 재검토는 **별도 개인 실행 영역에서 V245 입력·출력 해시 알고리즘을 독립적으로 재생**해 확인했다. 정식 GitHub CI는 공개 가능한 **합성 입력**을 사용하며, 실물 원본을 GitHub CI에서 실행했다고 주장하지 않는다.
- 기존 보고서의 V242 한 자식 미승인 로컬 projection을 정식 의미 원자 또는 E3 PASS로 승격하지 않았다. 실제 ETF E3=0/13, E4 owner 0, E5=0, 독립 정답 gold 없음, 개인 투자자문 HOLD.
- 이전 실패 이력: core CLI 스캔의 CORE[-1] 고정 가정, V245 edge 순서 차이, V128 엄격 child packet에 추가 필드를 넣던 결함을 각각 원인 수정·재검증했다. **결함 수정 후 전체 6-job GitHub CI와 이후 상태 원장 커밋의 CI까지 최종 재검증**해야만 P0-1-03 종료 보고를 확정한다.
