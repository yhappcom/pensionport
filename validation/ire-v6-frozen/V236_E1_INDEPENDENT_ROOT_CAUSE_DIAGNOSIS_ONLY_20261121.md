# V236 — E1 최종 HOLD의 독립 원인 분석 (2026-11-21)

> **원인 분석 전용.** 본 보고서는 엔진이나 정책 코드를 수정하지 않고, 실제 비공개 ETF 원본·SQLite·승인 관문과 V235 소스 코드를 상호 대조한 결과다. 개별 금융 주장을 승인하거나 사용자 메시지 ID를 위조하지 않았다.

## 최종 판정

**E1이 계속 미완료인 직접 원인은 전체 영상 V6 원자·검토 모델을 13개의 독립 V127/V123 자식 계약으로 이관하는 경로가 없고, 현재 V235가 구간 간 참조 1건이라도 있으면 그 이관을 시도하기 전에 무조건 HOLD하는 데 있다.** 두 번째 구조적 결함은 V235의 하위 긍정 경로가 실제 E4 금융근거 승인/봉인 기능과 연결되지 않았다는 것이다. 여기에 원본 데이터의 E2·E3 정식 판정 미완료가 겹쳐 있다.

### R1: 전체 원자 참조 범위와 자식 원자 검증 계약 불일치 — **구조적 원인, P0**

실제 V228 원본 250개 SRT, 68개 미승인 원자, V127 13개 자식 구간을 V234 전체 참조 원장으로 대조했다. 68개 중 21개가 자기 구간 밖 자막을 참조하며 총 49개의 외부 cue edge를 갖는다. 교차 원자 중 11개는 조건·예외 외부 참조, 3개는 외부 숫자 근거를 갖는다. 12개 자식 소유 구간에 영향을 주고, **9개 원자가 같은 45·46·47번 원문의 적용 대상 제한을 참조**한다. 일부 참조는 인접 구간이 아닌 최대 10개 구간 거리이다. 따라서 인접 경계 12개만 검사하거나 구간 길이를 조금 조정해 해결할 수 없다.

근본적으로 `ire/v6/atomic_exchange.py` 75행은 `allowed = scope_first..scope_last`로 범위를 제한하고, 145~167행의 원문·조건·예외·문맥·숫자 출처가 해당 `allowed` 안에 있어야 한다. 전체 영상에서 유효한 후보를 변경 없이 자식 V6 input으로 제출하면 범위 계약에 위배된다. 임의로 외부 ref를 버리면 E2 의미가 손상될 수 있다. **21개는 출처 참조의 구조적 사실이지, 21개 모두 실제 의미 오류임을 인증한 값이 아니다.**

### R2: V232는 전체 영상 1개 V6 scope, V127은 자식 13개 계획뿐 — **생산 경로 누락, P0**

V232 실물 V6 DB의 이벤트 30개(13개 window model, 13개 structural proof 등)는 하나의 **전체 영상 scope**에 기록됐다. V233 V127 `PrivateFullVideoCheckpoint`는 13개 자식 manifest **계획**만 생성했으며 checkpoint event는 0건, 승인 자식 0/13이다. `v1271_parent_resume_checkpoint.py` 134행 `record()`와 `v128_host_continuous_video.py` 21~110행은 각 자식마다 고유한 child manifest/source/inventory/exchange/V6 host receipt/ChatGPT V123 final review/official bytes/legacy relations를 요구한다. 기존 전체 영상 V6 event 1건을 13개의 실제 child host receipt로 간주할 수 없다.

현재 엔진에 전체 68 원자의 의미를 무손실로 13개 분할·재소유/상위조건 참조·재해시·개별 검토하여 제출하는 정식 adapter가 없으므로, V127 13계획 생성 PASS는 V127 13 자식 검토 PASS가 아니다.

### R3: V235의 전제조건이 실행의 선행 단계를 봉쇄 — **운영 교착, P0**

`v235_e1_real_parent_release_gateway.py` 131~132행은 `context["cross_segment_atom_count"]>0`이면 즉시 `HOLD_CROSS_SEGMENT_CONTEXT_NOT_REPRESENTABLE_AS_CHILD_ATOMS`를 반환하고 이후 `review_or_load_child`, `review_seams`, `review_parent` 콜백에 접근하지 않는다. V234 `verify_escrow_bytes`는 변경 불가능한 전체 원본 `exchange`와 정확히 일치하도록 교차 원장을 재구성한다. 결론적으로 **원본을 재구성하지 않으면 교차 개수를 줄일 수도 없고, 교차 참조를 의미 판정할 콜백도 도달할 수 없는** 교착 상태다.

비공개 실제 ETF V235 실행을 개인 SQLite DB 사본에서 재현하면서 child/seam/parent 콜백을 모두 전달했으나 호출 기록은 **[]**였고, 결과는 `HOLD_CROSS_SEGMENT_CONTEXT_NOT_REPRESENTABLE_AS_CHILD_ATOMS`, 교차 21, 자식 PASS 0, `knowledge/events/parent_publications = 0/0/0` 유지였다. 이 HOLD는 **안전한 차단으로서는 정상**, 그러나 양성 경로의 완성 증거는 아니다.

### R4: V235의 양성 경로가 정식 E4 인증·봉인 저장과 분리 — **승인 경로 결함, P0**

`v235_e1_real_parent_release_gateway.py` 69행은 저장소에 `type(knowledge_store) is PrivateKnowledgeStore`를 강제한다. 실제 E4 가드 저장소인 `E4SealedKnowledgeStore`는 PrivateKnowledgeStore 하위 클래스이지만 **정확한 타입은 다르므로 거부**된다. 또한 171행은 `run_full_video_with_e3_decisions`로 직행하고, `run_e4_guarded_parent`나 `assess_e4_primary_authority_gate`를 호출하지 않는다.

정식 E4는 `v166_e4_primary_approval_gate.py`의 `assess_e4_primary_authority_gate`와 `run_e4_guarded_parent`에서 공식 HTTPS 원문·시점·적용범위·ChatGPT 의미근거 검증과 별도 승인 봉인 경로로 처리된다. `v173_e4_only_parent.py`의 별도 검증 영수증 역시 **E5 자동 승인권이 없는 `e5_authorized=false` 기록**이다.

V235가 교차 참조 없는 입력에서 V128/V126으로 연구 후보를 발행하더라도 코드 결과에 `e4_authorized=false`가 명시돼 있다. 이것을 E4를 통과한 E1 종단간 PASS로 취급하면 안 된다. **실제 ETF에서 부적합 지식이 발행된 증거는 없고, 현재 경로가 E4 승인 통합을 증명하지 못한다는 구조적 결론이다.**

### R5: V231 2턴 내부 원자 판정은 V123 정식 final review 형식이 아님 — **자료·프로토콜 미완, P0**

실제 V228 `native.json` cue disposition은 `UNRESOLVED=177, CANDIDATES=72, NO_ATOM=1`; 원자 68개의 `stance`는 **전부 UNRESOLVED**다. V231 별도 사용자 메시지 후 비공개 내부 검토에는 250 cue 및 68 원자 행이 있으나, 판정은 48개 `REQUIRES_SOURCE_MEANING_REPAIR`, 20개 `HOLD`이고 전 항목 E3 최종 승인=false다. V123 필수 `chat_review`에는 full `source_cues`/ `atom_verdicts`, 각 원자별 speaker/stance/condition/numeric/counterexample, 금융 primary body SHA·시행일·범위·quarantine, V6 **child host event pin** 등이 요구된다. V231 `turn2_review` 구조 자체는 이 정식 스키마가 아니고 승인을 증명하지 않는다.

실제 V123에 chat_review 미제출로 호출했을 때 `HOLD_MISSING_CHAT_FINAL_REVIEW`는 기능상 올바른 결과였다. E2 의미 근거와 E3 실물 검토 없이는 모든 13 child를 승인하는 것이 안전하지 않다.

### R6: ChatGPT 호스트 2턴의 암호학적 신원증빙은 현재 인터페이스에서 확보되지 않음 — **외부 신뢰 한계, P1**

`v193_e3_two_user_turn_contract.py` 자체가 caller-supplied `user:` ref를 형식상 비교할 뿐 호스트 메시지 ID를 검증하지 않는다고 명시한다. 별도의 실제 사용자 턴이 있다는 대화 관찰과 호스트 암호학적 서명은 서로 다른 증거다. 이것을 코드 내부에서 문자열만 늘려 해결할 수 없다. 실현 가능한 검토 운영 증빙 수준을 별도로 명시해야 하며, 수동 참조를 신원 인증으로 승격하지 않아야 한다.

## 검사 성공의 정확한 해석

V235 GitHub CI 129/129 성공은 source/hash/격리/중단 보호용 테스트의 성공이다. 특히 `test_v235_e1_real_parent_release_gateway.py`의 'actual v128 child boundary'는 **허위 child 콜백에 대한 InvalidInput 발생을 기대하는 부정시험**이며, V235를 통해 E4 인증된 합법적 13-child 최종 지식 **긍정 발행**에 성공한 테스트가 아니다. 129개라는 개수로 E1 전체 PASS를 주장하면 이전 오류를 반복한다.

## 선행 수정의 논리적 순서 (이번 분석 단계에서는 미시행)

1. **정식 '상위 원문-자식 원자' 연결 계약 설계**: 전체 소스 해시/원자 ID·부모 조건을 고정하고, 원자별 child 소유권과 cross-scope ref를 lossless로 운반하며, 실제 ChatGPT 판정으로 삭제/격리/재소유/공통 조건 참조를 구분. 단순 ref 절단 금지.
2. **13개 real child V6+V123 cases 생성·재생 경로**: 기존 전체 host receipt를 개별 child receipt로 위조하지 않고 실물 child source scope/manifest/inventory/host event + prior knowledge relation + E3 검토를 독립 등록.
3. **V235 선행 차단 로직을 명시적 source-bound 결론 검증으로 변경**: 무조건 `cross_count>0` 차단 대신, 전수 의미 판정 완료·미완료/격리·상위조건 연결을 검증. 미해결은 계속 HOLD.
4. **E4 guarded/sealed parent를 E5 원자적 발행 전에 필수 연결**: 공식원문·시점·범위 승인과 외부 owner 봉인 검증. 정식 E4가 없으면 양성 지식 최종승인 불가.
5. **실제 2턴 ChatGPT 검토에서 정식 V123 리뷰와 공식 근거 생성**: 동결 1턴·별도 2턴 의미 승인, 조건·숫자·화자 재검토. 현재 48 repair/20 HOLD를 실제 판정 후에만 변환.
6. **양성·음성 검증을 별도 합격판정**: E1 구조 연결 합성 양성, 실제 ETF 부정 차단, E2/E3 검토 후 실제 ETF 양성 E4/E5 발행을 구분하고 매 단계 사전 합격 기준 고정.

**최종 원인 판단:** 현 V235 E1이 계속 HOLD인 것은 단순 검증 부족이 아니라 **(R1) 범위 계약 불일치 + (R2) 13 real child 증빙 생성 누락 + (R3) 선행 무조건 차단 + (R4) E4 승인 경로 미연결**이라는 최소 4개의 구조적 문제와 **(R5) 실제 승인 데이터 미완료**, **(R6) 플랫폼 메시지 출처 한계**가 복합 작용하기 때문이다. 해결 전까지 승인/발행 0 유지가 옳다. 본 문서 작성 외에는 엔진 코드, 동결 원본, main, 기존 DB를 수정하지 않았다.
