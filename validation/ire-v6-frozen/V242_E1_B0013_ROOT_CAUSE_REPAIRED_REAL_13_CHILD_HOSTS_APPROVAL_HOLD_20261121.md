# V242 — B0013 원인 재진단 후 조건 연계형 V6 실제 호스트 수선 결과 (2026-11-21)

## 0. 실행 순서

**코드 수정 이전** `V242_B0013_CONDITION_LINKED_CHILD_HOST_ROOT_CAUSE_AND_REPAIR_PLAN_20261121.md`를 별도 선행 Git commit `d81d54965c67b5f6cb5692e7a82521d449b3bc0d`에 고정했다. 이 문서 순서대로 실제 원본 확인 → 출처 결합형 미승인 자식 투영 검증 → V6 실제 SQLite 커밋 → 13개 DB 원장 감사 → 적대 합성시험을 수행했다. 이 작업은 E2·E3 의미 판정이나 금융 사실 승인을 대신하지 않는다.

## 1. 무엇이 원인이었는가 — 이전 가설보다 구체적인 재진단

- B0013 자막 **241–250**의 `C00057`은 `source_refs=[246]`, `context=[45,46,47,244,245,246,247]`, `conditions=[45,46,47,244,245]`. `kind=RECOMMENDATION`, `speaker=UNKNOWN`, `stance=UNRESOLVED`. 기존 V6 원래 전체 parent atom SHA-256 `88f8d07be8844f1715e921faaa6c16950bd666fa99690f23038fbf51f20a7644`.
- 원문 45·46·47은 **이 여섯 기준이 인덱스 ETF용**임을 제한한다. 244·245는 **동일 시점 여러 ETF를 상대 비교**한다는 내부 적용 조건이며 246·247은 활용·선택 발언이다.
- **V6 PARTIAL의 허용 범위가 241–250**이라 45–47을 V6 atom body의 `condition_cue_indices`에 포함하면 grammar violation. 기존 V238은 교차 원자가 하나라도 있으면 그 원자를 통째로 미승인 sidecar로 이동한다. 따라서 B0013의 host local atom 0 → `V241_E1_EMPTY_CHILD_LOCAL_ATOMS_REQUIRE_SOURCE_MEANING_REPAIR`. 원본 부재·화자 검토 불가가 직접적인 host 실패 원인이 아니다.
- 실제 E3 승인과 별개로 **구조 등록만을 위한 source-bound provisional child projection**을 만들 수 있었는데, 기존 로직은 이 경우도 제공하지 않았다. 문제는 `all-or-nothing` 투영 정책의 과잉 차단이고, 의미 정확도 불확정은 별도의 후속 문제다.

## 2. 구현 — frozen V6를 수정하지 않는 V242 두 계층 계약

새 `validation/ire-v6-frozen/v242_e1_condition_linked_host_bridge.py` 및 `test_v242_e1_condition_linked_host_bridge.py` 추가.

- parent `C00057` **불변**, 전체 V228 ZIP SHA, V231 별도 턴의 실제 source note와 V145 원문격리, V234 전체 source escort, V237 task, V238 child 원장 pin 재검문
- 자식 구조 전용 provisional atom: **기존 claim ID·원문 246·원래 명제·추천 유형·화자 UNKNOWN·입장 UNRESOLVED를 유지**, 내부 조건 `[244,245]`, 내부 문맥 `[244,245,246,247]`만 PARTIAL grammar로 기록
- 따로 `PARENT_EXTERNAL_QUALIFIER_PENDING` provenance sidecar: 외부 **45·46·47 각각 원문 인용·SHA·CONTEXT/CONDITION 역할**, parent original atom SHA, V234 escrow SHA, parent exchange SHA, child projection SHA, V237 task SHA, child source/manifest SHA를 전수 보존. 외부 condition과 자식-local atom을 재결합하면 **원래 parent atom과 딕셔너리 전체가 바이트 동일하게 재구성**되어야 진행 가능
- **외부 source quote/숫자/exception/ref가 있거나, 내부 조건 앵커가 없거나, E3 승인이라고 주장하면 즉시 차단**. `stage_verified_condition_linked_host`가 원본+외부 조건을 다시 재생 검증하고 사용자 명시적인 *미승인 구조 호스트 staging 권한* 및 별도 pin을 요구한다.
- 이 함수에는 **V123 승인, E4 금융근거, E5 발행 기능이 아예 없다**. 이후 정식 의미·발행 관문은 외부 45–47 적용 조건을 별도로 검토하지 않으면 PASS를 부여할 수 없다. `B0013`이 원문 의미상 완결됐다고 선언하지 않는다.

## 3. 실제 ETF 원본·V6 호스트 결과

| 실증 항목 | 확인된 값 |
|---|---|
| 비공개 SRT 원본 SHA-256 | `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b` |
| B0013 original parent atom | `C00057`, 외부 조건 3개 [45,46,47] |
| B0013 local V6 provisional atom | **1건** (`UNRESOLVED`) |
| B0013 local 조건 / 문맥 | [244,245] / [244,245,246,247] |
| Original parent atom SHA-256 | `88f8d07be8844f1715e921faaa6c16950bd666fa99690f23038fbf51f20a7644` |
| New child-only provisional projection SHA-256 | `b26ee20905e858da2897b2be3325a2137c6fc236c41ef5d190ccfab38c321a3b` |
| Source-qualifier provenance SHA-256 | `4fb10f740f1c11f7b7a892f3b5ef729d415556874afb86d52d83c2208365cff6` |
| B0013 V6 host SQLite | **실제 커밋 6 events**, 재개봉 `integrity_check=ok` |
| B0013 호스트 ledger head | `19751ef9f0d994e0289ca4b1a07895a228d472d9f2a89b8b3d978cde12d926b5` |
| B0013 SQLite **봉인 사본** SHA-256 | `c4caf67edde22367fc8a49e74c4c0dc209e2dc72aacc83c9a861cf3fbc2a72d9` |
| 13개 각각 다른 자식 V6 원장 재개봉 | **13/13**, 전체 **78 events**, 모두 ledger head 일치 |
| 이전 V241 12개 각 원장 ledger head | 전부 이전 기록과 일치 |
| V6 검증된 의미 proof/ E3 승인 / E4 승인 / E5 발행 | **0 / 0 / 0 / 0** |
| owner/platform cryptographic identity | **미확보** (operator-held source pin과 명확히 구별) |

**실물 출처 원장과 실제 SQLite backup은 개인 ZIP에서만 제공**한다. 파일 실행 중 live SQLite file SHA는 WAL checkpoint 과정에 따라 달라질 수 있으므로, 운영 무결성은 각 scope **이벤트 해시 chain**으로 판정하고 독립적인 정적 바이트 고정이 필요할 때는 `sqlite3.backup`으로 만든 봉인 DB의 SHA만 고정한다. 잠깐 관측한 live 파일 SHA를 immutable owner proof로 사용하지 않는다.

## 4. 검증·보호 범위

- V242 신규 synthetic adversarial 10건: 기존 V241 empty child HOLD 재현, 외부 조건 완전 재구성, **실제 V6 SQLite 커밋/재개봉**, stage 무권한 차단, 외부 pin 불일치·원문 quote 변경·조건 역할 조작·기존 부모 원문 변경·가짜 V123 승인·내부 조건 소실 차단.
- V241까지 기존 167건을 그대로 유지하므로 **총 177개 CI 회귀시험**. 합성 검증과 실제 ETF 오프라인 실증은 서로 다른 증거다. CI에서는 synthetic 2턴만 stub으로 격리하며 실제 ETF에서 직접 `verify_real_turn2_private_custody`를 실행했다.
- 원본 250개 cue·68개 parent atoms·21개 cross atoms·49개의 외부 cue 역할 불변. V241은 변조하지 않았고 B0001–B0012 12개 저장소는 기존 ledger heads가 모두 동일.
- `main`, 기존 frozen V6·V123·V127·V128·V126/E4, 승인 지식과 지식 발행 0건 변경 없음. 비공개 원문/DB는 GitHub 업로드 금지.

## 5. 실제 E1 합격 경계와 잔여 과제

| 기준 | 판정 |
|---|---|
| 실제 영상 13개 구간 source-bound 검토 task | PASS |
| 원래 외부 source reference 21개 / 49 edge 전수 보존 | PASS (미승인) |
| **실제 13개 별도 V6 SQLite 호스트 구조 커밋** | **PASS: 12 local-only + 1 parent-qualified provisional** |
| B0013 완결된 금융 의미 원자·원문 적용범위의 ChatGPT 최종 검증 | **HOLD** |
| 68 parent atoms 정식 speaker/stance/condition/숫자 검증·정답 | **HOLD** |
| 13 child + seam + parent 정식 V123 승인 | **0/13 HOLD** |
| 공식 HTTPS 금융근거/시점/대상범위 E4 seal | **0 HOLD** |
| E5 최종 지식 통합 발행 | **0 HOLD** |
| **E1 승인→적법 저장 전체 종단간 최종 PASS** | **HOLD** |

**판정:** 12/13에 머물던 **V6 구조적 호스트 등록 장애는 해결**했다. 별도 parent-qualifier source escrow가 실제 승인 자격을 부여하는 것은 아니며, E1 전체 종단간 합격은 미달이다. 다음 순서는 E2 원문 의미 재원자화·정식 E3 2턴 판정 후 E4/E5 승인 path 양성+음성 실증이다.
