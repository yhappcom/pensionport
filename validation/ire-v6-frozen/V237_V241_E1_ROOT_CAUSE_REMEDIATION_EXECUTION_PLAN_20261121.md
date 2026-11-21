# V237–V241 E1 구조 결함 해결 실행계획 — 승인/원본 보호 (2026-11-21)

> **이 문서는 코드 변경 전 고정한 실행 규약이다.** 범위: V236의 6개 독립 원인 R1–R6. 사용자가 요청한 순서대로 각 단계별 **구현·실물 재현·적대 시험·결과 기록**을 진행한다. 지식 승인이나 금융 사실 확정은 어떤 구조시험으로도 대체하지 않는다. 기존 `main`, V6/V123/V126/V127/V128/E4 동결 모듈과 사용자 원본은 수정하지 않는다. 새 코드는 `validation/ire-v6-frozen/v237+`의 적응 계층에 추가한다.

## 고정된 성공 정의

- **E1-구조 PASS**: 실제 ETF 원본 250 cues/68 atoms가 전체 source SHA와 13 child plan에 온전히 귀속되고, 21 cross-scope atoms/49 외부 cue 참조를 소실 없이 ChatGPT child review 입력으로 전달한다. 13개 자식마다 출처 고정된 심사 packet을 생성하고 실제 V6 child host 기록은 *각 자식의 독립 원장 영수증으로만* 인정한다. 중단·재시작·다시 실행·변조·정책 우회 차단 시험 PASS. E4 승인된 부모에 한해 E5 발행하는 경로가 실제 코드로 이어져야 한다. 구조적 긍정 경로는 합성 *정식 승인* fixture에서만 증명 가능.
- **E1-실물 금융승인 PASS**: 위 조건에 더해 13 child 모두의 별도 2턴 ChatGPT 원문 의미 정식 검토, 적용시점 금융근거 원문 SHA, V123 승인, E4 봉인·권한 확인 및 E5 원자적 저장 확인. *사용자/호스트 2턴의 암호학적 ID를 제공받지 못하면 '호스트 서명 인증' 주장은 하지 않는다.* 이 조건 전엔 실제 ETF 발행·최종 E1 PASS 금지.
- **E2·E3 독립 지표**: E2 원자 의미 정확도·독립 gold와 E3 실제 ChatGPT 승인 판단은 E1 구조 성공과 별도 측정. E2가 미완료여도 E1 구조 구현·차단 시험은 가능해야 한다.
- **절대 불변식**: 미승인 OPEN·HOLD·REQUIRES_REPAIR은 knowledge/parent_publications로 기록 불가; 공개 Git과 CI에 비공개 원본·review note·SQLite 업로드 불가; 정상 원장 불변; 무작위 64hex 문자열은 증빙 불가.

## 작업 1 — V237: 교차 문맥 검토 계약과 13 child 임무 생성 [R1, R3]

**입력:** V228 전체 original source/manifest/exchange, V233 13 child manifest, V234 external context escrow, 각각 외부에서 선행 확보한 SHA pins.

**구현:** 각 child별 `review_task`를 생성하여 child scope, 원본 SRT 원문 SHA, 원자별 부모 claim ID/원본 SHA/owner child/경계 밖 원문 인용·역할(조건·예외·숫자·문맥)·출처 SHA, 내부 자막 번호와 검토 상태를 전수 보존. 전체 원자 68개가 정확히 한 child의 소유자로 계산되고, 외부 cue edge 49개가 손실 없이 나타남을 재계산. 원본 V6 atom의 참조를 잘라내지 않음. `cross_count>0`도 ChatGPT 검토 임무 *생성*을 막지 않되 최종 release는 막는다. 검토는 실제 ChatGPT의 별도 사용자 턴 자료가 있어야만 정식 상태를 진행.

**합격:** 실제 250/68/21/49 source-custody PASS, 원문·숫자·원자 변조/누락·child 중복·미인증 2턴 claim 거부. 13개 실제 검토 임무 생성, 승인 0 유지.

## 작업 2 — V238: 정식 child V6 host case 이관 [R1, R2]

**핵심 설계:** V6 partial source scope는 외부 cue 참조를 입력으로 받지 않으므로, `child.source-bound local atom exchange`와 `cross-scope parent context review envelope`를 **두 객체로 분리**한다. lossless external context는 parent escrow에 원문 바이트 수준 보존, child local 원자는 외부 참조가 제거되었다고 '정식 의미 승인'으로 표시하지 않음. Cross atom은 검토 결과에 따라 재원자화/격리/상위조건 귀속이 되기 전 `OPEN`; 기존 전체 owner V6 영수증을 child 영수증으로 대체하지 않음.

각 child에 대해 원본 raw bytes를 그대로 사용해 별도 child manifest 및 owner inventory의 고정 SHA를 확인하고, exact 1..250 전체 SRT cue indexing을 보존한 PARTIAL manifest로 V6 source audit 실행. 안전한 local-only draft로 host `submit_host_atomic_batch`를 진행하는 경우도 **unapproved host staging만** 허용. child source manifest/owner inventory/host event/ChatGPT review/official bytes/prior relation은 V127 `record` 계약과 일치하도록 형식을 검증.

**합격:** 13 child의 실제 owner/source plan 감사; child별 증빙 전수, 68 original candidate custody, 21 unresolved 격리; 별도 독립 테스트에서 가짜 child receipt 거절 및 발행 0.

## 작업 3 — V239: V123 child/seam/parent 실제 2턴 경계 [R3, R5, R6]

검토 packet이 만들어진 뒤 사용자에게 확인 가능한 별도 ChatGPT 턴으로 semantic verdict를 수집하고 source+parent atom SHA에 고정한다. 수동 ref는 'manual observed'로, platform-signed ref는 인증 증빙이 있을 경우에만 별도 신뢰 필드로 표시. 250 cue/68 atoms/21 cross set의 결함·조치 전수 평가. 출처가 확정된 처리 결과만 child formal `chat_review` 형식으로 전달하고, 다른 형식은 explicit HOLD. child/seam/parent 실제 review callback은 E2 판정 전에도 **실행 가능**하지만 PASS 승격은 전수 금융 검문 이후에만 허용.

**합격:** 콜백 도달성 + 불일치/가짜 turn2/미완료 정식 리뷰의 발행 0, source-annotated 리뷰의 재개봉 SHA 재검증.

## 작업 4 — V240: E4 봉인 승인 필수, E5 원자적 지식 발행 [R4]

기존 동결 `assess_e4_primary_authority_gate`, `run_e4_guarded_parent`, E4 봉인 저장소와 V128/V126의 권한 계약을 분석하여 **우회 불가능한 한 경로**로 연결. 기존 V235 `type(store) is PrivateKnowledgeStore`만으로 봉인 E4 store를 거절하는 문제를 수정하되 `isinstance`만 바꾸어 무조건 발행을 허용하지 않음. 공식 HTTPS 본문 SHA/시행일/대상/범위/ChatGPT 최종 결론/owner 봉인과 parent 13 child PASS를 각각 검증하고 E4가 E5에 승인 권한을 주지 않는 경우 금지.

**합격:** 합성 정식 긍정 시나리오 1개 이상에서 E4 gate + E5 원자적 커밋 PASS; 승인 위조·지식원장 사전변조·중단/중복/재실행 0 leakage. 실제 ETF는 승인 0 상태이면 반드시 HOLD.

## 작업 5 — V241: 실제 ETF 재실행·정량 보증·보고 [R1–R6]

- 원본 250 cues, 68 candidate atoms, 21 cross atoms, 49 outside edges, 13 child scope source pins를 원장으로 읽어 **변경 전후 값 비교**.
- 긍정 합성 E4/E5 경로 + 실제 ETF 부정 검문을 각각 고정. CI PASS는 실제 ETF 승인 PASS를 뜻하지 않는다.
- 소프트웨어 연결 합격 여부와 실제 금융 의미 정확도/E3 승인/E4 공식 근거/원자 지식 발행 여부를 분리 보고.
- 모든 재현 가능한 결함에 fail-closed 수선과 부정시험을 추가. 원본 파일, Git SHA, 재실행 영수증과 테스트 실행 ID 기록.

## 단계별 보고·변경 규칙

1. 이 계획을 첫 Git commit에 저장하고 SHA를 기록한다.
2. V237→V238→V239→V240→V241 순서대로 **개별 커밋 + 회귀시험 + 실제 원본 오프라인 시험**을 수행한다. 각 단계 산출물이 미완료라면 후속 단계의 '성공'으로 표현하지 않는다.
3. 작업 중 발생한 새로운 결함은 이 문서의 '변경 이력'에 원인·영향·시험 추가 형태로 기록하고 변경 승인 근거를 명시한다. 무근거 성공 판정·임의 승인·실물 원본 누출 금지.
4. 실제 2턴 ChatGPT 검토를 한 번의 코드 호출·동일 메시지의 중복 사용으로 대신하지 않는다. V236 원인은 2턴 프로토콜과 구조적 연결 결함이므로 순서를 왜곡하지 않는다.

## 시작 당시 상태와 지표

| 지표 | V236 시작 값 | 구조 합격 조건 |
|---|---:|---|
| 전체 원본 cues | 250 | 250 변조/누락 0 |
| V6 원자 후보 | 68 | 모든 원자 단일 child owner 및 출처 보존 |
| 자식 V127 scope | 13 | 13 child source+검토任务 생성 |
| cross-scope atoms | 21 | 21 전수 구조 보존, E2 전까진 미승인 |
| 외부 cue edges | 49 | 49 외부 원문·역할·숫자 해시 보존 |
| 실제 child E3 formal PASS | 0 | 승인 없이는 발행 0 |
| 기존 실제 E5 knowledge | 0 | E4 미승인 상태 발행 0 |
| E1 기존 CI | 129 tests PASS | 새로운 적대 테스트 추가 후 PASS |

**반드시 구분:** `unapproved external context escrow`를 단지 정식 `V123 chat_review`라고 이름 바꾼 산출물은 실패다. 호스트 USER ID, E4 봉인, E5 지식 commit을 문서 문구만으로 대체하는 것도 실패다.
