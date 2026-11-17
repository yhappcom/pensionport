# V166 E1 — 엔진 전체 구조 실측 검증: FAIL, 다음 단계 진입 금지

**2026-11-17 KST | 대상 E1: 입력·검토·승인·저장 경로가 하나로 연결**

**결론: E1 FAIL.** 기존 동결 V123의 합성 승인 경로는 실제 V128 지식 저장까지 이어지지만, 영상 #1에서 실제 사용되는 **V164 유형별 ChatGPT 의미 검토 경로는 최종 승인과 저장 경로에 연결되지 않았다.** 이 사실을 E1 성공으로 포장하지 않는다.

## 1. 실제 실행 증거

- 검증 브랜치: `verify/ire-v6-v166-e1-e7-sequential-gates-20261117`.
- CI 실행: https://github.com/yhappcom/pensionport/actions/runs/44021729254
- 커밋: `dcb625e9b2568da49263c2ecb2e6fad14fd5a4e1`.
- CI 결과: **3개 검증 job success**. 아래 셋은 *각각 다른 성질*의 시험이다.

| 시험 | 실행 결과 | 올바른 해석 |
|---|---|---|
| `ordered-status-ledger` | SUCCESS | E1이 FAIL인데 E2를 시작하거나 완료증거 없이 PASS로 기록하면 반려됨 |
| `e1-existing-synthetic-native-path` | SUCCESS | **합성** native V6→V123→V127.1→V128→V126 SQLite 실제 `events=3, knowledge=3, parent_publications=1` 경로. **2개 자식 시험**이며 실물 영상 #1 13개 자식 아님 |
| `e1-typed-contract-connection-diagnostic` | SUCCESS (결함 탐지) | 아래 구조적 불연결을 재현; **E1 합격이 아니라 실패 원인 확인** |

## 2. 실패 원인의 코드상 증거

| 관문 | 원인 | E1 영향 |
|---|---|---|
| V164 typed | `typed_final_knowledge_release_authorized=False` 및 `v128_parent_publication_authorized=False` 고정 | source-only 검토가 정식 승인으로 이동할 수 없음 |
| V127 / V127.1 | `assess_chat_final_gate`만 호출 | 자식 체크포인트는 유형별 최종 판정을 소비하지 못함 |
| V126 | `require_chat_final_release` 원형만 호출 | 상위 승인 버전에서 검토한 타입은 지식 저장 시 다시 HOLD |
| V128 | `staging.add_chat_final_batch`로 V126 경유 | 13자식 전체 승인·원자적 발행 경로의 실제 진입 막힘 |

V164가 다섯 발언의 **원문 발화 유형만** 확인했다는 것은 금융 사실이나 그 전략 유효성을 승인했다는 의미가 아니다. 그 다섯 원자를 안전하게 `SOURCE_SPEECH_ONLY`로 분류하되 **지식 저장 대상으로 승격하지 않는** 유형별 계약이 필요하다. 역사 사실 C00002·C00009·C00010 세 건은 별도 원전 확인 전 승인할 수 없다.

## 3. 지금은 E1 합격할 수 없는 이유

기존 합성 2자식 경로가 구조적으로 성공했다는 사실만으로는 새로운 공식 의미 검토 경로의 input→review→approve→store가 연결되었음을 증명할 수 없다. 또한 기존 V164의 고위험 `12`는 실제 미검출 위험 12사건이 아닌 과거 OPEN 위험 원자 12개의 잔존 집계다. 이를 임의 0으로 고치거나 가짜 사건 12개를 첨부해 승인시키는 방법은 불허한다.

## 4. E1에서만 허용되는 최소 수정 범위

1. **공식 V166 버전형 최종 ChatGPT 승인 계약**을 하나 정의한다. 객관적 금융 사실, 인용된 발언/질문, 제한적 가설, 원전 미확인 사실, 명시 격리를 별도 처분으로 구분하고 source/cue/atom/host/근거 digest를 검증한다. 의견·질문은 금융 사실이나 자문으로 승격 금지.
2. 해당 계약을 V127 child checkpoint, V127 full-parent, V126 지식 저장, V128 parent proof가 **동일한 검증 결과/버전/원본 SHA**로 소비하도록 연결한다. 서로 다른 관문이 임의로 자체 `PASS`를 재생성하지 못하게 한다.
3. 기존 V123 경로는 byte-frozen으로 보존. V164 사전검문 `True`나 `False` 값을 임의 수정하여 기존 HOLD를 PASS라고 주장하지 않는다.
4. 새 소스 타입 구분 경로에서 **합성 정상 1회 이상 실제 격리 SQLite에 지식 저장**, 같은 입력의 누락된 원전·허위 리뷰·다른 호스트 digest에 대해 **지식·이벤트 증가 0**을 실행 검증한다. 이들 관문 중 하나라도 불일치면 E1 FAIL.
5. 단계 합격 이후에만 E2를 시작하며, 실제 원문 의미 정합성의 별도 진실성 평가는 E2~E4에서 검증한다. E1 합성 통과만으로 실물 B0001/영상 #1/791편 GO를 주장하지 않는다.

## 5. 다음 턴 재개 위치

- 공식 문서: `V166_E1_E7_SEQUENTIAL_ENGINE_VERIFICATION_PLAN.md`.
- 상태 원장: `V166_E1_E7_STATUS.json`.
- 검증 코드: `v166_gate_sequence.py`, `test_v166_gate_sequence.py`, `v166_e1_connectivity_audit.py`.
- **재개 단계 = E1**, 현재 `FAIL`, 원인은 버전형 의미 승인과 V126/V127/V128 소비 계약 단절.
- **E2~E7 절대 시작 금지**. E1 실제 합격 영수증이 만들어진 뒤 E1 PASS·E2 IN_PROGRESS 상태 전환을 같은 커밋에 기록.
- `main`, 동결 V123, Master116/P4, 비공개 소유자 SRT/SQLite, 사용자 포트폴리오 변경 없음.

**회귀가 녹색인 것은 단계 완료가 아니다. 기능·실물 의미·지식 발행·개인 자문 승인 여부는 각각 별도 판정한다.**
