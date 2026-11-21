# V242 E1 재분석·개선 실증: B0013 실제 원본 구조 저장 통과, 조건 의미승인 HOLD (2026-11-22)

## 1. 재검증된 근본 원인

실제 비공개 ETF `LVE7XN_esTc` 원본 250 cues와 V228 원자 68개, V237 13개 검토 입력, V238 부분 V6 교환, V234 교차 문맥 원장, V241 B0001–B0012 12개 SQLite를 **다시 검문**했다.

B0013(241–250)의 원자 C00057은 primary source 246, local context·conditions 244–247/244–245, **부모 영상의 외부 적용제한 45–47(인덱스 ETF 대상)**을 참조한다. 기존 V238은 범위 밖 조건을 가진 21개 원자를 미승인 sidecar로 전부 격리하므로 B0013 child V6 atoms=0, cue246 포함 미해결 문맥 10개가 남는다. 기존 frozen V6 `host_batch.py`는 미해결 cue를 내포한 empty model을 `HOST_BATCH_EMPTY_WINDOW_NOT_EXPLICITLY_NO_ATOM`으로 거절한다. 따라서 *원자 누락*이 아니라 **native V6 scope와 부모 제한 조건 운반 계약 사이의 표현 결손**이 B0013 직접 원인이었다.

### 직접 확인한 원문 관계
- 45–47: 여섯 비교 기준은 **인덱스 ETF**를 위한 것임
- 244–247: 여섯 상대지표로 같은 시점 여러 ETF를 비교하고 선택하라는 조언
- C00057 original atom: `RECOMMENDATION / UNRESOLVED / UNKNOWN`, source cue 246, external conditions 45–47 + local conditions 244–245

원본 C00057 전체 claim 구조와 45–47 원문 바이트/조건 역할을 변경하거나 삭제하지 않았다.

## 2. 실제 변경 및 안전한 승인 경계

먼저 [V242 실행계획](V242_E1_B0013_CROSS_SCOPE_QUALIFIER_ROOT_CAUSE_AND_EXECUTION_PLAN_20261122.md)을 GitHub에 고정하고 아래 코드를 추가했다.

- `v242_e1_cross_scope_unapproved_host_projection.py`: **원본 부모 C00057 full atom / 외부 조건 45–47 sidecar**와 **B0013 local V6 source-anchor-only 후보**를 명시적으로 분리. 외부 원문·조건 role·SHA·부모 원자 SHA·V237 task·V238 draft·V234 escrow·V231 미승인 2턴 근거를 재생 검문한다. 원래 stance=UNRESOLVED이고 외부 조건이 context+condition뿐인 **한 건에만** 허용한다. 다른 교차원자 20개 자동 승인/이관 금지.
- V6의 `TransactionStore.submit_host_atomic_batch` 자체는 수정하지 않았다. 기존 동결 V6 API로 실제 B0013 **모델/구조 증빙/REVIEW_PROPOSED** 이벤트를 기록했다. native V6 scope id는 전체 원본 부모 sidecar SHA-256 `v242_<full64hex>`로 고정돼, sidecar의 보존 없이는 현재 사건을 정식 심사 원자로 해석할 수 없다.
- stage 호출 시 **전 원본·원자·검토 증빙을 처음부터 다시 확인**하고 사건 기록 직후 SQLite를 재개봉한다. 다른 source/ref/조건/원문 SHA, 승인 위조, 오래된 pin은 write 이전 차단. 원본 및 기존 12개 DB 불변.
- 결과물은 명확히 `v242_forbidden_as_v123_formal_child_atom=True`, `parent_external_semantics_resolved=False`이다. 로컬 부분 표현은 **의미 완결 V6 원자 아님**. E3 최종 심사·E4 봉인·E5 지식 발행의 권한을 부여하지 않는다.
- `test_v242_e1_cross_scope_unapproved_host_projection.py`: 합성 원본을 이용한 10개 긍정·적대 시험(외부조건 인용문 변조, 조건 삭제, 거짓 승인, 외부 SHA 변경, 명시적 stage 허가 누락, 소스별 2턴 quote 변조, SQLite 사건 변조, 중복 호출 등).

동일 브랜치의 기존 별도 실험적 `v242_e1_condition_linked_host_bridge.py`도 regression CI에 포함돼 있다. **실물 감사에 사용한 canonical path는 full parent SHA를 scope-id에 영구 결박하고 staging 시 원본을 재검증하는 `v242_e1_cross_scope_unapproved_host_projection.py`**이다. 두 실험 경로를 정식 V123 승인 API로 사용해선 안 된다.

## 3. 실제 ETF 읽기·쓰기 결과

| 검증 내용 | 결과 |
|---|---|
| V228 동결 source SHA-256 | `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b` |
| parent C00057/조건 45–47 인용문·role·SHA 검문 | PASS |
| V237/238/234/231 개인 증빙 재생·SHA 검문 | PASS |
| B0013 네이티브 V6 source/model/proof 이벤트 커밋 | **6개 실제 SQLite 이벤트 / PASS** |
| B0013 native host 사건 해시 | `000fe9c30db7bb0ab8e3e893e4c136ff345dee0cf34844c06a41d45372ace1de` |
| parent 조건 포함 원본 연결 SHA-256 | `249ef1a83f569e7e5f104aab5150509ebcec878472b73e6a89efe4ab638264d0` |
| B0013 SQLite bytes SHA-256 | `5c08e810e955c3aba87038b448e0a6e5f8894c68042a48d029f0b633da1bb2b2` |
| B0013 동일 입력 재실행 | idempotent; 사건 6개 유지 |
| 12개 V241 이전 DB 재개봉·SHA chain 대조 | PASS |
| 최종 13 child structural-host 사건 | **12 완결 local + 1 미승인 잠정 local view, 총 78 이벤트 PASS** |
| B0013 사건 JSON 변조 사본 재생 | `LedgerCorrupted` 차단 |
| 실제 E4/E5 approved store events/knowledge | **0/0** |
| 실제 13 child V123 final approved | **0/13** |
| E2 독립 의미 gold/검증된 금융법령 근거 | 미확정, HOLD |
| ChatGPT 메시지의 호스트 암호학적 식별자 | 미제공 / 인증 주장 불가 |

13개 모두 **구조적인 소스/원자 연결 미승인 V6 사건**을 기록했지만, **B0013의 경우 부모 외부 조건 45–47을 native child-local atom으로 완전 표현하지 못한다.** 따라서 13/13을 **정식 V123 입력 조건 완결 13/13**, E2 의미 검증 또는 E1 승인 발행 PASS라고 발표하는 것은 잘못이다. E4는 기존 21개 교차원자 미판정 차단을 유지한다.

## 4. 테스트 및 원본 보호

- CI: [E1 V242 Actions](https://github.com/yhappcom/pensionport/actions/runs/44957375627) — 이전 167개 + 동일 브랜치 별도 V242 10개 + 본 V242 10개 = **187/187 PASS**. CI 입력은 합성, 실물 ETF는 로컬 비공개 원본으로 별도 실행.
- 실물 13개 SQLite 사건 체인 감사 JSON: `95b026b14bd5590665e71133959d0617049a13048ac96dc4def737bc18b5ebf1`.
- 실물 V242 B0013 및 부모 C00057 조건 sidecar는 개인 비공개 증빙 ZIP에만 보관. 원본 V241 ZIP SHA `d31adc4a5bc113e8f0a3dfca5f904301830dda03f58db71aee98dcb2db968c2a`와 함께 대조해야 13개 재현 가능.
- 본 변경은 기존 검증 브랜치만 사용. `main`, frozen V6·V123·V126·V127·V128/E4, V228/V241 원본과 이전 승인 지식 불변.

## 5. 잔여 결함 및 후속 완료 조건

**구조 엔진 관점에서 고친 것:** B0013에 한 개의 미해결 외부 조건만 있다고 호스트 구간 전체를 기록할 수 없던 장애. 이제 부모 원문과 조건을 전수 보존하는 *미승인 부분 표현*을 정상 native V6 구조 원장에 기록·재시작할 수 있다.

**아직 고치지 못한 것:** B0013 C00057 및 다른 20개 교차 원자의 실제 의미 확정, 모든 68 원자 speaker/stance/condition/숫자 E2 검문, V123의 13개 formal 2-turn chat review/official primary source, E4 owner seal·권한, E5 원자적 지식 발행. **원본 의미를 훼손하지 않고 정식 V123에 넘기려면 E2/E3에서 부모 원자 전체를 조건 포함해 재검토한 후 별도 승인 packet을 작성해야 한다.** 미승인 부분 표현을 그대로 E4로 보내는 것은 금지.

### 최종 판정

- E1 미승인 **13구간 구조 호스트·복구 경로**: 실물 **PASS**, 이 중 하나는 외부 조건이 남아 있는 잠정 보기.
- E1 원본 의미 보존이 필요한 **실물 최종 승인·발행 경로**: **HOLD**.
- E2/E3/E4/E5 승인: **0**.

**정확한 진전:** B0013의 이전 `EMPTY_CHILD_LOCAL_ATOMS` 저장 장애를 재현·분석해 실제 호스트 SQLite 커밋으로 해소하였으나, 검토·승인 권한은 한 건도 승격하지 않았다.
