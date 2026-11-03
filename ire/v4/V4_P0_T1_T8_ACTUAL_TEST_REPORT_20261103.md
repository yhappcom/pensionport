# IRE V4 P0 T1–T8 실제 원본 검증 실행 기록 — 2026-11-03

## 판정
**P0 NO_GO_NOT_END_TO_END.** 설계 확인은 실전 단일 명령 완주를 대체하지 않는다. 이번 시험은 원본 ZIP/12개 기존 잠정 창/실제 공식자료 일부를 기반으로 한 현재 실행 가능 범위의 시험이며, 아직 81개 전체의 독립 모델 의미 판단, 공식자료·지식 통합 완주를 수행하지 못했다.

## 입력 및 관찰
- 원본: #1 `sz5N9WJS310`, source SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`
- 원본 자막: 1,195, V3 adaptive 총 81 창, 1,195/1,195 cue의 창 소유권 검증
- 기존 별도 비공개 잠정 초안: W00009–W00020, **12/81** 창, 182개 primary cue, 잠정 주장 44, 원문 인용 179, 3 비주장 후보
- **남은 미처리 창: 69개.** 미처리는 OPEN claim으로 둔갑할 수 없으며 완료 아님.
- 이번 실행 정식 V3 `ConversationResearchSession.accept` 접수: 0, 신규 독립 금융 사실 승인: 0, 투자자 자문 승인: 0.

## T1–T8 결과
| Test | Status | Evidence |
|---|---|---|
| T1 source | PASS | 1195 cues, 81 adaptive windows, SHA and all cue owners |
| T2 meaning | FAIL_INCOMPLETE | 12 draft windows only; 69 unprocessed |
| T3 official evidence | FAIL_INCOMPLETE | Confirmed one official NPS public general-rule page; full per-claim validity and scope not checked |
| T4 correction | PARTIAL_PASS | Reverse link, primary quote, planner boundary, numeric literal checks, plus altered quote/window rejected. Independent financial semantics not complete |
| T5 prior knowledge | NOT_VERIFIED | No full approved knowledge-claim join |
| T6 knowledge integration | NOT_RUN | No approved diff/write |
| T7 one command | FAIL_INCOMPLETE | 81-window end-to-end model/search/review/relation/final report loop not demonstrated |
| T8 completion safety | PASS_NEGATIVE | Gate rejects unprocessed windows, missing research evidence, relation audit or report seal. Positive fully populated fixture is synthetic only |

## 검증한 제한적 공식 근거
국민연금공단 공식 설명: 연기연금은 월 0.6%, 연 7.2%, 최대 5년 36% 가산을 설명하며 수급 개인별 적용·세금/건보료 영향은 추가 검토. `https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0100M0.do`. 실제 문서 바이트 해시, 법조문 버전 대조, 개별 44 주장 대응은 수행되지 않음.

## 회귀 시나리오
현재 별도 로컬 검증 스크립트에서 원본과 다른 문맥 경계, 변조된 직접 인용을 거절하고 80/81, 근거 누락, 이전 지식 대조 누락, 최종 보고 누락에 각각 완료 거부 확인. 실제 전체 연구 전수 성공으로 해석 금지.

## 수정 우선순위
1. **Chat Research Controller**가 81개 원본 패킷을 실제 모델이 해석하도록 한 사용자 명령 아래 연속 수행할 수 있는 작업 실행 계약 구현/실증.
2. 각 window reply를 V3 adaptive 정식 validator에 접수, 품질/수치/인과 error를 창별 교정.
3. claim별 공식 근거 조회 및 적용성/시점 판단, OPEN 의무 기록.
4. 기존 지식 ledger를 원본 revision으로 잠그고 전체 신규 claim과 관계 및 누적 diff 검수.
5. UNPROCESSED=0인 경우만 최종 보고 seal; 한도가 발생하면 남은 작업을 보고하고 실패로 기록.

원본 및 개별 청구내용을 GitHub에 업로드하지 않음. `main` 및 기존 v003 불변.
