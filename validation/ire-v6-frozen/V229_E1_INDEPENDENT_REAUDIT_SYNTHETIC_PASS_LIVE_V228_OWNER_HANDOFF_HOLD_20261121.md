# V229 — E1 독립 재점검: 합성 종단간 경로 재확인, V228 실제 1턴→승인·저장 이관 결손 분리 (2026-11-21)

## 1. 변경하지 않는 E1 합격 기준과 이번 정확한 판정

사용자 확정 E1 기준: **“엔진 전체 구조 — 입력·검토·승인·저장 경로가 하나로 연결.”**

**확인된 사실을 합쳐도 다음 두 주장은 다르다.**

| 범위 | 이번 독립 재평가 | 설명 |
|---|---|---|
| **V203 기존 E1 합성 엔진 경로** | **PASS 재확인** | V176 owner journal → 실제 새 V6 host transaction/receipt → ChatGPT 형식 리뷰 콜백 → 동결 V123→V127/V128→V126 SQLite를 동일 합성 소스에서 실행. 긍정/격리/중단/멱등 시험이 동작. |
| **V228의 사용자 ETF 실제 1턴 동결 결과를 동일 E1 승인·저장 경로로 전달** | **HOLD: 아직 이관 불가** | V228 ZIP에는 원본 250 cue·미승인 68 V6·E3 검토 입력·2,278쌍이 있지만, V203 함수가 필수로 요구하는 **V176 EngineChatSession의 source-first SQLite 검토 원장**과 **V127 부모 checkpoint**가 존재하지 않음. 실제 분리 사용자 TURN2 검증도 시작하지 않음. |
| **E1 통과가 E2/E3/E4/E5 실물 승인이라는 주장** | **금지** | E1의 합성 구조 PASS가 금융 사실 승인·독립 정답률·V193 실제 2턴을 인증하지 않음. |

**운영상 결론: 기존 E1 합성 구조 PASS 자체는 철회할 근거가 없으나, 최신 V228 OWNER 경로의 실제 완성도는 미입증이다.** 둘 중 하나를 다른 것으로 승격하지 않는다.

## 2. 실제 점검 근거

- [V166 단계별 불변 계약](V166_E1_E7_SEQUENTIAL_ENGINE_VERIFICATION_PLAN.md) E1: 동일 원천/host digest로 원본→ChatGPT 검토→승인 토큰→V126/128 연결. E2 의미 정확도와 별도.
- [V202 반례](V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md): 미승인 UNKNOWN/UNRESOLVED speaker/stance를 승인 리뷰로 위조하던 기존 V202 샘플이 RED를 냈음. 역사적 FAIL 보존.
- [V203 재구현](V203_E1_REAL_V176_ORIGIN_TO_NATIVE_V128_STRUCTURAL_PASS_20261120.md), `v203_e1_v176_origin_native_host_bridge.py`: 실제 `EngineChatSession` 타입, V176 checkpoint head와 모든 cue 검토 완료를 요구. 두 child host 원장에 V6 신형 native batch를 생성한 뒤 callback이 V123 검토·근거·관계를 제공하고, V127·V128·V126의 동일 원천·영수증을 검문. 합성 정상 경로는 **연구 후보 2건 저장, 부모 발행 1건**이고 동일 재실행은 신규 발행 0.
- V203 **11개**, V204 **4개**, V205 **3개** E1 구조·실패 폐쇄·TestCase.run 프리플라이트 총 **18개**, 최신 GitHub CI 재실행에서 PASS.
- **PR #75**의 기존 변경 파일 78개는 모두 `validation/ire-v6-frozen/`과 `.github/workflows/ire-v206-e2-source-census.yml`에만 있었으며, `ire/v6`, `main`, 동결 V123/V126/V127/V128 코드의 변경은 없음. root `README.md`는 기준 blob `32b059d14383a52e7dcba0e2b53abf7e8c467857` 그대로.

## 3. V228 실제 1턴 ZIP에서 발견된 운영 이관 장애

**민감한 사용자 자료를 공개 GitHub에 포함하지 않고**, 로컬 사용자 전용 `V228_PRIVATE_ETF250_REAL_TURN1_FROZEN_OWNER_SOURCE_68_ATOMS_AWAIT_TURN2.zip`의 원본 바이트·8개 압축 멤버를 다시 검문했다.

- 소유자 SRT `LVE7XN_esTc` **250 cues**, SHA `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- 개인 동결 ZIP SHA `9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397`, manifest SHA `497f1d03987e59deec92066b6b68a528838230617e49ac98f208f2a85249820c`.
- V228 1턴 freeze head `c7edf0a2ffffcdb2654c6f6006efe16254ee06afa5cd16b5481b8d2edee620d2`은 **V228 bundle hash이지 V176 원장 head가 아니다**.
- 동결 구성: `source.srt`, `native.json`, `cue250.json`, `e3_tasks.json`, `atom_pairs.json`, `first_turn_research.json`, `turn1_manual_receipt.json`, `freeze_manifest.json`. 68 미승인 원자·68 E3 검토 task·2,278 lexical pairs 및 250cue 전수 자료 존재. 해시·phase·금융 비승인 12가지 로컬 검사 PASS.
- **동결 ZIP에 실제 V176 owner `.sqlite`/`.db`와 V127 부모 checkpoint가 포함되지 않는다.** 현재 확인한 것은 **이 ZIP 안의 부재**이며, 다른 과거 개인 파일 저장소 전체에서 존재하지 않는다고 단정하지 않는다.
- 실제 V193 두 번째 사용자 메시지로 원문·동결 명제 전수 최종 검증한 기록은 없음. V228 연구 턴1을 자동으로 둘로 나누거나 참인 원자 승인 기록으로 변환하지 않는다.

**결론:** V228의 새로운 owner-private 1턴 자료를 `run_origin_native_e1`의 `owner: EngineChatSession` 인수로 그대로 넘길 수 없다. V201도 같은 실제 V176 타입/원장 검문을 요구한다. ZIP→owner 검문을 빠뜨리고 `EngineChatSession`을 자동 생성하면 **기존 V202 계보 바꿔치기 결함을 재발**시킬 수 있다.

## 4. 이번 차단 보완 — V229 read-only 운영 이관 프리플라이트

`v229_e1_v228_operational_handoff_preflight.py`를 검증 브랜치에 추가했다. E1 실제 소유자 경로를 자동 PASS로 승격하는 대신 다음을 검문한다.

1. `verify_turn1_frozen`의 실제 4가지 외부 SHA로 원본·동결 ZIP·manifest·첫 턴 head를 재확인한다.
2. V176 소유자 `EngineChatSession` 및 실제 동일 원본 `V127` checkpoint가 없으면 **`HOLD_NO_GENUINE_V176_JOURNAL_OR_PARENT_CHECKPOINT`** 반환. 임의 빈 SQLite 생성, 승인·저장 호출 금지.
3. 실제 V176이 공급됐더라도 별도로 핀한 V176 journal head, 동일 원본 250cue, 전수 심사 완료, 동결된 68개 원자와 **완전한 atom 구조 동치** 없으면 fail closed. 68→69/원자 종류/화자/stance/조건/예외를 조용히 수정해 통과시키지 않는다.
4. 새로운 별도 사용자 TURN2 검증 영수증 없이는 owner real E1 release-ready를 주장하지 않는다. 이 가드는 read-only 사전검사이고 실제 `run_origin_native_e1`·V123/E4/E5를 호출하지 않는다.
5. **12개** 새로운 합성 원본 V228 ZIP 부정/정상 HOLD 회귀시험을 현행 CI의 기존 E1 18개 **앞에서 별도 강제 실행**하도록 연결했다. 기존 E1 18개·V193 58개·E2 658개는 변경하지 않았다.

개인 재점검 영수증 `V229_PRIVATE_E1_REAL_ETF250_TURN1_OWNER_HANDOFF_REAUDIT_HOLD.json`, SHA `8ed1e30fd372f382a451bbf7bca4312e640c1becc815b91037768ad078085a8f`. **원문/원자 전문 없는 해시·상태 요약**이며 사용자 전용 Library에 append-only 저장.

## 5. 최신 실행 상태

새 소스에서는 기존 **734개** (V193 58 + E2 605 + 기존 E2 53 + E1 18)에 V229 E1 운영 이관 검사 **12개**를 추가해 **746개** 합성 자동검사로 구성했다.

- [새 V229 E1 검사 최초 전체 Actions run 44864574523](https://github.com/yhappcom/pensionport/actions/runs/44864574523) — **746/746 PASS** (로그 58+605+53+12+18).
- **이 PASS는 새 이관 코드가 미검증 실물 owner를 거부하는 것을 포함한 코드 안전성 검증이며, 실물 ETF 영상에서 E1 승인·저장 성공을 의미하지 않는다.**
- 사용자 E1 단계에 대해 **합성 구조 PASS와 실제 이관 HOLD를 별도 상태로 관리**, E2 독립 gold 및 E3 공식 최종 승인 상태 변경 없음.
- `main`과 frozen V6/V123/V126/V127/V128, 지난 1턴 동결 archive는 변경하지 않았고 PR #75는 DRAFT다.

## 6. 다음 실제 해결에 필요한 이관 증거

실제 V176 owner(SQLite와 audit chain/head)가 존재하는 경우 원본 SRT SHA·cue/atom·review head를 V228 freeze와 대조한다. **없으면 기존 V228 원자를 'V176에서 판정한 원자'로 위조하지 않는다.** 장래 연구 턴1의 비공개 체크포인트에는 원본+native 전체 외에 **실제 V176 owner journal 및 부모 plan/checkpoint head**를 포함하도록 1턴 운영 경로를 보강해야 한다. 2턴에서 승인·보류·격리 검증을 끝낸 후에만 정식 V123/E4/E5로 이관한다.

**최종 E1 재평가: 역사적 E1 합성 구조 PASS 유지 / V228 실물 운영 종단간 연결 HOLD / E2 의미 정확도 HOLD / E3 실제 2턴 최종 검증 NOT_RUN / E4·E5 NOT_RUN.**
