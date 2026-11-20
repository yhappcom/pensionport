# V213 E2 — V182에서 확인된 실제 의미 손실의 정식 V6 투영 경로 수정

**검증일:** 2026-11-20 KST. **판정:** 소프트웨어 결함의 재현·출처 기반 수정 경로 PASS / 실물 ETF 전체 E2 품질 **HOLD**.

## 1. 해결하려는 실측 결함

V182는 V176 실제 원장에 존재하는 조건·예외 서술이, `compile_native_v6_stage()` 호출 시 정식 V6의 `condition_cue_indices`, `exception_cue_indices`로 전달되지 않는 결함을 확인했다. 실제 예에서 69개 원자 후보의 조건·예외 기록 69/69에도 불구하고 동결 V6 출력 인덱스는 빈 배열이었다. 이는 **자막 원문 어디에 조건/예외가 존재하는지 E2 검토자의 출처 판정이 검증되지 않았기 때문**이다. 조용히 자막 인덱스를 만들어 채우면 거짓 문맥이 되므로 빈 배열 차단 자체는 유지한다.

## 2. V213 E2 전용 개선

새 코드 `v213_e2_source_qualifier_native_bridge.py`는 동결된 V176 원본과 `ire/v6/atomic_exchange.py`를 수정하지 않고 다음 실제 승인 전 경로를 연결한다.

1. **V176 실제 엔진** `EngineChatSession.progress()`와 해시사슬 `_audit()`로 **원본 SRT·V176 체크포인트 head·전수 검토 완료** 여부를 고정.
2. 원자 순번·조건·예외 필드의 모든 서술을 `term_id`, `term_sha256`, `owner_claim_sha256`, 원자 문맥 cue 목록으로 전수 등록.
3. **E2 전용 `E2QualifierCustody.prepare()`**는 현재 원본에 존재하는 해당 cue 문장을 사용자 비공개 채팅 검토 패킷으로 발행. 기존 원자의 조건·예외는 모델이 SOURCE_EXPLICIT / SOURCE_CONTEXT / REVIEWER_ADDED / UNRESOLVED로 **직접 의미 판정**한다. ChatGPT가 내놓지 않은 자동 판정은 금지.
4. **`submit()`**은 해당 `source_quote`가 실제 인용된 cue에 있는지, 그 cue가 원래 claim context에 있는지, 의미 설명·원본 SHA·기존 원자 SHA·소유자 head에 연결되는지 검문. 원본 출처가 없는 `REVIEWER_ADDED`·`UNRESOLVED`는 V6 조건/예외로 승격 불가.
5. **E2 비공개 `0600` SQLite append-only SHA 이벤트**로 소유자 이벤트를 변경하지 않고 저장·재개. 해시 위조, 오래된 체크포인트, 중복·변조, 잘못된 payload 형식을 차단.
6. **`compile_e2_safe_native_stage()`**는 기존 `EngineChatSession.compile_native_v6_stage(qualifier_provenance=...)`를 그대로 호출하므로, 실제 frozen V6의 스키마와 `audit_host_atomic_exchange`를 통과한 **원래 native V6 원자 구조**만 출력. 모든 SOURCE_EXPLICIT 조건/예외 자막 인덱스가 E2의 검증된 원문 출처와 일치하는지 claim ordinal까지 재검문.

`SOURCE_CONTEXT`와 검토자 임의 주의사항은 비공개 원장에서 보존하되 화자가 발언한 `condition_cue_indices`/ `exception_cue_indices`로 자동 투영하지 않는다. 정식 `speaker=UNKNOWN`, `stance=UNRESOLVED` 상태를 **유지**하며 V123/E4/E5 승격도 차단한다. *현재 chat role 확인 플래그는 증명서가 아니며 독립 골드 인증이 아니다.*

## 3. 실제 V176→native V6 회귀 실행과 RED→GREEN

합성 ETF 원본으로 실제 `EngineChatSession.submit()`을 실행해 조건/예외를 가진 native V176 원자를 만든 후, 같은 원자를 정식 V6 변환기에 통과시켰다.

| 시험 | 수정 전(native V6) | V213 출처 검증 후(native V6) |
|---|---|---|
| 조건 서술의 출처 자막 | `condition_cue_indices=[]` | `[1]` |
| 예외 서술의 출처 자막 | `exception_cue_indices=[]` | `[2]` |
| 검토자만 추가한 예외 | 잘못된 Source/Reviewer 구별 없음 | 비공개 검토자로 표시, V6 인덱스 제외 |
| 원본 V176 원장 | 조건·예외 서술 유지 | **수정하지 않음** |
| V6 원자 영수증 | 구조 검증 PASS이지만 빈 문맥 | 실제 원문에 연결된 문맥 PASS |
| E2/E3/E4/E5 | 승인 안 됨 | **계속 승인 안 됨** |

V213에는 긍정·적대적 테스트 19개를 추가하고 E2 합격 오판을 막는 단계 보호시험 1개를 추가했다. 원문 외 가짜 조건 인용, 원자 문맥 밖 자막, E2/금융 승인 위장, 비공개 SQLite 변조, 불안전한 DB 권한, 잘못된 필드 타입 및 Python TypeError 위험, 독립적인 재개·헤드 고정, 모든 출처가 매핑돼도 E2가 자동 PASS 되지 않는지를 검사했다.

**최신 개발 CI:** [run 44755058801](https://github.com/yhappcom/pensionport/actions/runs/44755058801) **256/256 PASS** (E2 185, 이전 E2/V176 53, E1 18). 테스트 대상은 실제 네이티브 코드와 **합성 원문**이고 사용자 원본 SRT·SQLite를 공개 CI로 전송하지 않았다.

## 4. E2 완성까지 남은 일

1. **실제 원본 250 cue가 연결된 기존 V176 원장**(V179/V181)과 당시 개인 파일 체크포인트를 복구해 V213의 실제 대상에 적용해야 한다. 원본 SRT 바이트는 개인 Library에서 확보했지만, 해당 기존 판정 SQLite의 현재 세션 실물 연결·재개는 이번 V213에서 이루어지지 않았다.
2. 누락/중복 원자 문제를 해결해야 한다. V179 24 OPEN/68 suspicious NO_ATOM 개별 원장과 V182 17 OPEN은 서로 다른 역사 상태다. V210 57 · V181 69 · V188 71 미승인 후보는 동치·분할·조건 차이 판정이 필요하다.
3. `speaker` 및 `stance`는 여전히 UNKNOWN/UNRESOLVED이다. 실제 원음·화면·기준시점 및 출처/화자 검증 없이 임의 확정하지 않는다.
4. 프리징된 독립 의미 정답셋 없이 precision≥95%, recall≥98%, 고위험 누락0을 주장하지 않는다.

**최종 공식 판정:** E1 **PASS (합성 구조)** / E2 **실제 의미 정보 투영 경로 개선 PASS, 연구 품질 HOLD** / E3·E4·E5 **현행 경로 NOT RUN**. `main`·동결 V6/V123/V126/V127/V128·개인 SRT/기존 원장 미수정, PR #75는 Draft로 유지.
