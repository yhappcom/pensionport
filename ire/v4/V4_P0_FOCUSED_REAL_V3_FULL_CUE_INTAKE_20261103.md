# IRE V4 P0 — 단일 명령 집중 실험: #1 전체 V3 적응형 문맥 실제 접수 완료
**기준일:** 2026-11-03  **판정:** `P0_NO_GO_EVIDENCE_AND_PRIOR_KNOWLEDGE_PENDING` (최종 GO 아님)

## 1. 이번 실제 실행으로 해결한 부분
과거 13/81 문맥·49개 잠정 주장 수준에서 출발하여, **한 번의 사용자의 진행 요청 안에서 모델이 추가 #1 영상 원문을 직접 해석**하고 기존 V3의 정식 source-bound validator에 접수했다.
- 비공개 #1 영상 `sz5N9WJS310`, 원본 SRT SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`
- 전수 자막 **1,195/1,195**, V3 adaptive **81/81** 원본 문맥 정식 접수, 미접수 **0**, 잠정 원자 주장 **209**, 비주장 후보 **76 cues**.
- 정식 `ConversationResearchSession.accept` 및 실제 `ChatBatchQueue.audit_semantic_coverage` / `completion_gate` 재실행: 원문 구조·인용 치명검사 **0**, cross-window 품질 위험 **0**, **해석 경고 83**.
- 정식 V3 81개 체크포인트 중복 재생 방지: 전수 재실행에서 **81개 기존 접수로 식별·신규 쓰기 0**.
- 실제 기존 V3 연구 엔진 **310개 테스트 PASS** 및 신규 어댑터 국소 회귀시험 **9개 PASS**. GitHub CI 성공은 별도로 확인되지 않음.
- 모든 원문·주장 본문·실험 체크포인트는 별도 0700/0600 비공개 저장. 기존 main 및 v003 수정 안 함.

## 2. 실제 V3 원장 통합 결과 (격리된 실험 저장소)
- 실제 V3 `ChatBatchQueue.finalize` 실행은 `SOURCE_ANALYSIS_COMPLETE_EVIDENCE_PENDING`.
- 신규 IRE만 포함하는 분리된 잠정 knowledge version 1에 **209건을 UNREVIEWED 상태로 등록**. 스냅샷 SHA256 `c279a3509cabc79c2be84f65597e08b1963dc136abc0f77d78f0a86fec580ad2`.
- 정식 V3 Evidence ledger 버전 0/실제 증거 평가 0건. 공식 금융 사실 승인 0건, 자동 투자자 자문 승인 0건.
- **중요 제한**: 이 실험용 지식 스냅샷은 기존 역사적 승인 지식 원장을 불러오지 않았다. 즉, 새 #1 주장과 기존 영상/기존 연구의 교차 비교·누적 변경(diff)은 수행되지 않았다. 교차영상 관계 후보 0은 일치·충돌이 없다는 결론이 아니라 과거 원장이 없어서 산출되지 않은 것임.

## 3. 추가 실제 공식 검색·검수
- 국민연금공단/국세청/한국거래소 공식 웹페이지 직접 조회 및 별도 외부 웹 수집 확인.
- 공식 자료 후보 **46건 / 서로 다른 잠정 주장 37건**. 그중 규정·상품의 공식 적용성 의무가 있는 103개 주장 중 공식 후보가 연결된 것은 **26개**. 일반 법령 설명을 개인별 적용과 같은 것으로 승인하지 않음.
- 출처 URL·발언자 주장·효력일 검토의 불확실성을 보존한 별도 OPEN dossier 생성. 원본 공식 웹페이지 전체 바이트 SHA와 V3 `LIVE_NETWORK_FETCH` 검증 영수증은 아직 0건; 웹검색 후보를 정식 공식 증거 원장 완료로 표시하지 않음.
- 위험 사례: 연 1,500만원 초과 사적연금이 **무조건 전액 종합과세**라는 단정은 국세청이 설명하는 15% 분리과세 선택 제도와 충돌. 연기연금 월 0.6%, 연 7.2%는 공단 일반설명과 부합하나 개별적용 유보.
- 산술/전사 검사: 100억원 x (1-16.5%) = **83.5억원**, ASR의 **84.6억원**과 불일치; 월 400만원 x 12 x 16 = **7.68억원**, ASR **400억**과 불일치. 음성/슬라이드 원본 대조 없이 어느 설명이 맞는지 단정 금지.

## 4. T1–T8 실측 재평가
| T | 판정 | 설명 |
|---|---|---|
| T1 원본 무결성 | PASS | 1195 SRT cue / 81 V3 창 |
| T2 전수 의미 초안·출처 접수 | PASS_STRUCTURAL / OPEN_QUALITY | 81/81 정식 V3 접수, 주장 209, 경고 83; 독립 의미 완전성 인증 아님 |
| T3 공식 금융 근거 조사 | INCOMPLETE | 후보 46/37개 주장, 요구 103개 중 26개에 후보; 0 정식 증거 원장 |
| T4 오류·누락 검수 | PARTIAL | V3 critical 0, warnings 83, 세제 오류·산술·ASR 후보 OPEN |
| T5 이전 연구 원장 대조 | NOT_RUN | 기존 승인 knowledge revision 미확보 |
| T6 누적 지식 통합 | PARTIAL_ISOLATED | 신규 잠정 지식 209건 안전 격리 저장, 기존 원장 diff 없음 |
| T7 명령 1회 최종 연구 완주 | FAIL_INCOMPLETE | 사용자 재지시는 없었지만 공식 검증·기존 지식·최종 연구 승인까지 완결하지 못함 |
| T8 완료 판정 | PASS_FAIL_CLOSED | 실제 V3 release = STRUCTURAL_SOURCE_COMPLETE_EVIDENCE_PENDING, P0 GO 거부 |

## 5. 실제 소프트웨어 통합
- 신규 `ire/v4_chat_accept.py`: Chat 작성 원자답변과 V3 adaptive source packet/halo/cue ownership/quote/numeric check/semantic critical 검사 연결, 실 V3 accept 및 재접수 idempotency.  
- 신규 `tests/test_v4_chat_accept.py`: 실제 V3 계약 기반 회귀시험.
- 신규 `.github/workflows/ire_v4_chat_intake.yml`: 브랜치 CI 진입점. 아직 GitHub workflow run 성공 증거 없음.
- 실험용 private data와 소프트웨어 회귀 경로는 분리함.

## 6. 다음 필수 해결
(1) 권한 있는 기존 누적 승인 지식 원장 revision 확보, #1 209 신규 주장과 조건·시점·범위별 관계 review/diff.
(2) 공식 규정 조사 의무 103건 중 미대조 항목을 실제 문서 원문에 연결, issuer·시행일·계좌·자금원천·예외 구분, V3 evidence ledger에 정식 접수.
(3) V3 경고 83건을 원본 및 실질 독립 판단으로 해소, 중요 수치·자막 ASR 정정.
(4) T3–T6 및 최종 단일 요청 종결까지 완주 후 T1–T8 재승인.

**단일 명령 원본 전수 의미 초안·V3 정식 접수까지는 실제로 성공했다. P0 전체 연구 완결까지 성공했다고 주장하지 않는다.**
