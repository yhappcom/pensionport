# V228 — V193 실제 사용자 2턴 연구·검증 운영 계약: 실행 관문 강제 및 ETF250 실제 1턴 비공개 동결 (2026-11-21)

## 0. 최상위 운영 계약 — 기존 합의의 정확한 적용

**기준 원문: [V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md](V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md).**

- **TURN 1:** 사용자의 첫 연구 지시 아래 원본 전체 → 원자·발언 의미·조건·예외·위험·기존 연구와의 대조 → **비공개 고정 체크포인트**. ChatGPT가 같은 응답 안에서 어떠한 2차 평가를 수행해도 이것은 TURN 2가 아니다. 원문·연구 파일 SHA, 전수 범위, 동결 head를 바꾸면 2턴 검증 무효화.
- **TURN 2:** **다음 별도 실제 사용자 명령**에서 동결 체크포인트를 복원하고 원본만 먼저 보는 ChatGPT 의미 검토 → 과거 원자/숫자/문맥/화자/조건/예외·현재 공식 금융근거 대조 → 승인/보류/격리의 **제안 및 검증 영수증**. 불확실하면 HOLD; 법령·원음·화면·독립 정답 근거 없는 E3 PASS 금지.
- **승인 분리:** 실제 ChatGPT TURN2 연구 검토는 **E3 최종 승인**, E4 적법한 승인, E5 통합 지식 저장과 다르다. 현재 E2 정밀도/재현율 미측정, 금융 공식 원문 효력·시점 검증 및 원음/화면 미확보로 **E1 PASS / E2 HOLD / E3 최종 NOT_RUN / E4-E5 NOT_RUN**.
- **턴 증빙 제한:** ChatGPT 내부에서 별도 실제 사용자 명령을 관찰할 수 있지만 API가 제공한 실제 메시지 ID/순서를 이 엔진이 암호학적으로 확인하지 못한다. 따라서 `host_two_turns_verified=false`이고 사용자 참조는 수동 명명이다. 서로 다른 가상 ref를 만들거나 같은 사용자의 명령을 나눠서 실제 TURN2 완료라고 표시하면 안 된다.
- **실패 교정:** TURN2에서 발견한 오류는 동결 TURN1을 수정하지 않는 append-only 교정 원장으로 보존. 변경해야 하는 원천 주장이 새 연구 결과를 요구할 때만 새 TURN1→TURN2. 이전 실패를 소급 PASS로 바꾸는 작업 금지.

## 1. V206~V227이 실제 2턴 규칙을 따르지 않은 근본 원인 및 교정

**검사된 코드 사실:** V193의 운영 문서, `v193_e3_two_user_turn_contract.py` 구현, 루트 README에 필수 2턴이 명시돼 있었다. 그러나 `ire-v206-e2-source-census.yml`은 V206~V227 E2/Census의 합성 회귀시험을 전부 통과시키면서도 **V193 테스트를 포함하지 않았고**, V223~V227의 E3 *검토 패킷 준비 함수*도 `validate_manual_turn_receipt`를 호출하지 않았다.

그 결과 코드와 출처 연결 PASS가 실제 사용자 TURN2 final semantic review 완료인 것처럼 운영상 혼동되는 오류가 반복됐다. E2 HOLD라는 단계상 제한을 E3의 **검토 진입 자체**를 금지하는 것으로 해석한 점도 절차 교착을 만들었다.

**V228 조치:**

1. 새로운 공통 엔진 `v228_v193_actual_two_turn_runtime_gate.py`: 원본 SRT·native V6·250cue triage·E3 68 task·2,278쌍 전수 행·실제 1턴 연구 원장에 대한 바이트/조건/발언 인용/동결 V6 검사 후 `O_EXCL`로 비공개 ZIP 원자적 작성.
2. `freeze_turn1_private`에서 V193 `validate_manual_turn_receipt(first,second=None)` **필수 호출**. 1턴 종료 상태는 항상 `AWAIT_SEPARATE_USER_VERIFICATION_COMMAND`; 첫 턴에서 E3/E4/E5 승인 코드 반환 금지.
3. `verify_turn1_frozen`에서 원본 source·ZIP·manifest·연구 head의 **별도 보관 해시 4종을 필수 입력**으로 사용해 모든 ZIP 멤버 재검문 및 frozen V6·250cue·68 task·2,278쌍 다시 검증. 파일이 없거나 SHA/권한/소스/윈도 크기가 틀리면 **이전 상태를 새로 만들지 않고 즉시 실패**.
4. `prepare_turn2_source_only_review`는 별도 사용자 명령이 **이번에는 실제로 관찰됐다는 수동 조건**, 첫 수동 ref와 다른 명령 ref 및 외부 핀을 모두 요구. 과거 원자 명제를 숨긴 **원문만 포함한 재판정 입력**을 다음 턴에서 생성하도록 준비. 코드는 호스트 메시지 ID를 갖고 있지 않으므로 `host_two_turns_verified=false`; **실제 TURN2 결과가 없으면 승인하지 않는다**.
5. 최종 허위 승인 우회는 `InvalidInput`으로 차단. 기존 V193 합성 14개 및 문서 계약 5개 회귀시험을 신규 E2 workflow의 **MANDATORY V193 선행 단계**로 추가하고 V228 합성 29개 시험도 함께 실행한다. 검토 자료 자체는 GitHub에 올리지 않는다.
6. **E1 보호 규칙에 따라 루트 README.md는 수정하지 않고 바이트 단위로 원상 복구했다.** README의 과거 'E2 READY/NOT_RUN' 문장은 역사적 안내이며 최신 상태 판정은 이 V228 검증 보고서와 `V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json`을 우선한다. **E2 HOLD일 때 E3 준비·별도 실제 사용자 2턴의 원문 검토는 가능하지만 E3 최종 승인·E4/E5는 금지**한다. V193 본문과 frozen V6/V123/V126/V127/V128는 변경하지 않는다.

> 범위 경계: 이번 새 관문은 **신규 V228 운영 진입점에 강제 연결**한 것이다. V223~V227의 과거 연구 보조 함수들을 제거·재작성하거나 frozen 승인 경로를 직접 수정한 것은 아니며, 이전 작성된 내부 E3 packets를 2턴 검증 완료로 소급 인정하지 않는다. GitHub 합성 CI 자체가 실제 ChatGPT 사용자 2턴을 증명한다고 주장하지 않는다.

## 2. 이번 실제 사용자 지시에서 수행한 TURN1 연구·동결

현재 대화의 사용자 메시지 **“정확히 명시하고 작업을 이어서 진행해 주세요”**를 **TURN1 연구·동결 요청**으로 수동 기록했다. 이 메시지는 호스트가 제공한 메시지 ID가 아니며 `user:observed-20261121-v228-turn1-request-manual-unverified`라는 수동 참조만 붙였다.

원본 `LVE7XN_esTc`를 사용자 전용 ZIP에서 다시 읽고 frozen V6 엔진으로 **250/250 cue**, V226 원자 **68/68**, 각 원자의 모든 source_context **68/68**, V227 `nC2` **2,278/2,278** source-anchored lexical review rows를 재검사했다. 전역 인덱스 ETF 적용 범위, 4개 금융 개념 충돌 격리, 2개 추적용어 보류, 11 AV 위험 cue와 24개 후속 source cue 검문 항목을 보존했다. 과거 V227 후보 판정·검토 결과를 참고한 새로운 완주 재검사이며 **새로운 블라인드 정답셋이나 기존 연구와 독립된 분석은 아니다**.

**동결된 개인 자료:**

- Private owner archive: `V228_PRIVATE_ETF250_REAL_TURN1_FROZEN_OWNER_SOURCE_68_ATOMS_AWAIT_TURN2.zip`, **원본 SRT와 자세한 원자 내용이 포함된 비암호화 비공개 ZIP**. GitHub / CI 업로드 금지. 사용자 전용 Library에만 저장.
- Private ZIP SHA-256: `9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397`.
- ZIP 내부 manifest SHA-256: `497f1d03987e59deec92066b6b68a528838230617e49ac98f208f2a85249820c`.
- TURN1 연구 head SHA-256: `c7edf0a2ffffcdb2654c6f6006efe16254ee06afa5cd16b5481b8d2edee620d2`. **이는 V228 source/native/triage/e3/pairs+turn1 메시지의 동결 digest이며 과거 V176 SQLite owner journal head가 아님.**
- Owner-original SRT SHA-256: `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- V226 draft native 68 file SHA-256: `c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb`.
- V227 canonical 68 E3 task file SHA-256: `6b60360a051cc022af138570fdd7e04e684a61636152496c727cae727cf03c14`.
- 동결 ZIP 내부 연구 단계: `RESEARCH_AND_FREEZE`, `chat_turns_completed=1`, `host_message_id_verified=false`, `e3_final_approved=false`, `e4_approved=false`, `e5_published=false`.

**1턴 실물 재개 검증 PASS:** 도구가 동결 ZIP을 다시 열어 위 4개 외부 해시를 재검사하고 원본 250cue·미승인 68 native V6·E3 68 task·2,278쌍을 다시 감사했다. ZIP 파일은 0600 mode로 원자적 배타 생성되어 이번 턴 안에서 덮어쓰지 않았다.

## 3. 이후 TURN2 진입을 위한 정확한 절차

다음 **별도의 사용자 메시지**에서 “**방금 동결한 ETF 250자막 연구를 V193의 실제 2턴 기준으로 원본·근거와 대조하여 E3 최종 의미 검증해 주세요.**”처럼 새로운 검증 명령을 받는다.

1. owner-private Library의 위 V228 ZIP 확보 → 외부 기록된 ZIP/manifest/first_head/source SHA 모두 대조. 실패 시 그 상태에서 종료; 자동으로 새 연구 원장을 생성하지 않는다.
2. `prepare_turn2_source_only_review`의 별도 실제 사용자 지시 수동 관찰 조건 확인 → **원본 250개 source-only 비교 입력** 생성. 기존 68개 원자는 source-first 판단 작성 전 리뷰어에게 정답으로 제공하지 않는다.
3. 새로운 ChatGPT 검증이 원문 근거와 조건/예외·금융 사실·화자/ASR/화면 위험을 판정. 이후 동결된 68개 V6 후보와 동치·누락·과도분할·숫자/시점/방향·4개 금융 오류·22 관계 endpoint를 대조. 원문만 제공했더라도 ChatGPT는 같은 프로젝트의 선행 내용을 기억할 수 있으므로 *독립 외부 gold*라고 부르지 않는다.
4. 각 주장에 대해 `APPROVE_CANDIDATE / HOLD / QUARANTINE` 등 **최종 제안** 및 근거를 새 2턴 원장으로 기록하되, E2 독립 gold, 원음/화면, 공식 금융근거 미확보 시 E3 **최종 승인 HOLD**. 이전 연구 TURN1 변경/삭제 불가, 별도 E4/E5가 없으면 발행 0.

이 문서는 **TURN1 실제 사용자 연구·동결을 끝낸 현재**에 작성되었다. **새 사용자 메시지는 아직 오지 않았다. TURN2 미실행**. 두 프로세스를 돌렸거나 CI가 통과했다는 이유로 실질 2턴을 완료했다고 표시해서는 안 된다.

**보호 경계 재검증:** 초기 README 수정 시 CI의 E1 `E1_FROZEN_OR_LEGACY_CHANGED` 경고를 받았으며, 보호 경계를 넓히지 않고 README를 원본 SHA `32b059d14383a52e7dcba0e2b53abf7e8c467857`로 완전히 복구했다. 해당 RunFail은 소프트웨어 의미 검증 실패가 아니라 변경 허용 경로 위반이었으며, 복구한 최신 커밋에서 전체 CI를 재확인해야 한다.\n\n**최종 상태: E1 구조 PASS / E2 원문 250cue·68 미승인 원자 저장·출처 구조 검사 PASS, 정확도 GOLD HOLD / TURN1 FROZEN / TURN2 AWAIT USER MESSAGE / E3 FINAL NOT_RUN / E4 E5 NOT_RUN.**
