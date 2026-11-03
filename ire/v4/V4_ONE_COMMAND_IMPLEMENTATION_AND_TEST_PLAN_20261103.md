# IRE V4 — 단일 명령 연구 엔진 구현·검증 작업 명세
**구현 명세 / 기능 구현·테스트가 완료됐다는 뜻 아님.** 2026-11-03.

## A. 우선순위 및 선행관계
`P0 설계 계약 고정 → P0 실원본 #1 폐쇄형 완주 실증 → P1 검증기·상태·정식 접수 통합 → P2 단일 영상 다른 범위 재현 → P3 5편 지식 통합 → P4 독립 정확도/자문 평가 → P5 791편 배치 확장`.
P0 완주를 구현하는 데 필요한 최소 프로토타입 코드/어댑터를 P0 안에서 작성할 수 있지만, 테스트 전에 P1을 운영 준비 완료라 보고하지 않는다.

## B. 통제 흐름 명세
| ID | 구현 책임 | 실제 출력 | 합격/거절 |
|---|---|---|---|
| P0-01 | source lock과 V3 adaptive planner pin | source_manifest + hash; cue/window ownership | 계획 변경 후 오래된 W000xx 답변 거절 |
| P0-02 | chat-host action/receipt protocol | 모델이 해석한 원문-원자주장 JSON + 호출 영수증 | Python만 실행된 것을 모델 재실행으로 인정 금지 |
| P0-03 | chunk dispatcher / context guard | 원본 + halo + per-primary cue 상태 | primary cue 누락=거절 |
| P0-04 | meaning audit/revision | 인용·숫자·인과 검사/재해석 trace | 단위·원인 오류가 주장을 VERIFIED로 승격하면 실패 |
| P0-05 | external official evidence service | 바이트 해시·기관·시행일·범위·예외·OPEN | 검색 결과 설명문만으로 VERIFIED면 실패 |
| P0-06 | accumulated prior knowledge join | 관계 후보+이전 버전+승인 조건 diff | 다른 시점·계좌를 SAME로 합치면 실패 |
| P0-07 | final closure/cue census | 영상/창/원자/근거/관계 표·seal checksum | UNPROCESSED > 0인데 COMPLETE면 실패 |
| P0-08 | privacy/audit/replay | 비공개 append-only receipt, 재현 가능한 해시 | 기존 v003 훼손·비공개 자료 공개=실패 |

## C. P0 실원본 수락 시험
- 고정시료: 비공개 #1 `sz5N9WJS310`, SRT 원본 `SHA256=2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`, 기존 V3 adaptive 계획 **81문맥**. 시험 시작 전에 실제 비공개 원본과 계획 버전을 재검증.
- 이전 실험: 12문맥·182 cues/44 잠정 주장/179 인용은 부분 실험만으로 인정. #1 원본 전수 완주 증거가 아님.
- 사용자 추가 지시 없이 **단일 명령으로** 전수 모델 해석 및 통제 루프 진행. 마감 보고에서 실측 model-step count, source coverage, external-search count, formal evidence acceptance, knowledge diff, OPEN/UNPROCESSED 수 분리.
- 실제 0/81 또는 일부 처리만 했는데 81/81이라고 발표 금지. **모델이 직접 원문을 읽었는지**와 CLI가 답변을 단순 수신했는지를 별도 기록.
- 상품명·계좌·수치·세제·기준일·원금·수익률·예외가 교차하는 표본에서 오류 주입과 공식 반증 확인. 사실 검증 불가시 해당 claim OPEN, 대신 전체 원본을 아예 조사하지 않았다면 연구 보고 완료 불가.
- 정식 V3 accept/semantic gate/evidence gate/knowledge diff 전부 실행·증거 저장. CI synthetic pass와 별도.
- 실패 시 `STOPPED_LIMIT`, `BLOCKED_SOURCE`, `BLOCKED_HOST`, `BLOCKED_SEMANTIC` 등의 **단일 차단 원인 + 미완료 큐** 보고. 실패는 GO가 아님.

## D. 회귀 및 적대적 시험
1. 실제 V3 adaptive 81창 vs 구형 V2 120창 ID 충돌 감지.
2. 해시 일치하지만 halo cue를 주장 근거로 사용한 위조 인용 거절.
3. primary cue를 무조건 비주장으로 채워 전수 처리인 척하는 오류 감지.
4. 인과관계: 추납 효과와 추가 납부 효과 혼동 감지.
5. 세율 %/원·연간/월간·수익률·연금 가산율 단위 검증.
6. 공식 기관 도메인의 폐지/개정 조항을 현행 적용이라고 오인한 경우 OPEN.
7. 기존 지식과 새 원문 간 다른 적용 범위를 SAME로 잘못 병합한 경우 거절.
8. 중복/기존 체크포인트 변경·로그 변조·source SHA 교체 거절.
9. 80/81 완료 후 COMPLETE 플래그가 들어오면 거절.
10. 독립 골드가 없는 상태에서 의미 재현율 95% 승인하는 오류 거절.

**평가기준**: 소프트웨어 회귀 통과와 실전 의미·공식 근거·독립평가 결과는 서로 다른 계층으로 보고한다.

## E. 운영 보고 표준
`{request_id, execution_host, source_sha, planner_version, expected_cues, actual_cues_accounted, expected_windows, analyzed_windows, unprocessed_windows, provisional_claim_count, official_evidence_checked, evidence_open, relation_decisions, knowledge_before_sha, knowledge_after_sha, critical_meaning_risks, user_continue_requests, external_model_api_calls, report_status, fact_release_status, advice_release_status}`

## F. 유한 실행 제약
사용자의 '한 번 지시'는 제품 UX 목표다. **호스트가 미지원인 반복 모델 추론을 Python으로 구현했다고 주장할 수 없다.** 실제 도구·모델 호출 한도에 도달하면 모든 정식 완료 flag는 false로 유지하고 최소 복구 포인터/블로커만 남긴다. 호스트에 실행 가능한 범위에서 최초 요청 안에 최대한 분석/검색/검증을 수행하되, 사용자에게 추가 요청이 없는 무조건적 완주를 보장하려면 지원 호스트에서 별도 실증이 필요하다.
