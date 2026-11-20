# V212 E2 — V182 실물 원본 OPEN 17건과 V211 위험 원장 교차검증

**시점:** 2026-11-20 KST  
**판정:** E1 합성 구조 PASS 유지 / **E2 실제 금융 의미 검증 HOLD** / E3·E4·E5 현재 경로 미실행

## 확인한 증거와 중요한 구분

- 사용자 소유 ETF 영상 `LVE7XN_esTc`의 실제 SRT 원본 250개, **SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`**를 개인 Library의 `1-70.zip`에서 재확인했다.
- 과거 GitHub [V182 출처 보고서](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-v179-real-two-turn-source-firstpass-20261119/validation/ire-v6-frozen/V182_CROSS_CHAT_CONTEXT_OPEN_AND_E2_SEMANTIC_LOSS_HOLD_20261120.md)의 **동결 V176 owner `effective OPEN 17` 개별 자막 번호**를 확보했다. 이는 **V179의 별도 24 OPEN·68 NO_ATOM 경고 수치와 동일한 원장이 아니다**. V179 24/68 개별 사건은 아직 미복구, 종료 또는 감소 판정을 하지 않는다.
- 원본 실제 17개 자막의 전체 인용·SHA·전후 2개 자막·V210 57 후보 문맥·V211 61개 위험항목·V211.1 32개 기존 관계를 소스에서 검증했다.

| V182 잔여 OPEN 증거 분류 | 원본 cue 번호 | 건수 |
|---|---|---:|
| 음성·ASR 원음 필요 | 19,23,52,133,149,150,153,160,171 | **9** |
| 원본 영상·차트 화면 필요 | 163,166,230,232,233 | **5** |
| 촬영시점·과거 통계 원표 필요 | 8 | **1** |
| 서술 범위 일반화·금융 사실 관계 재심 필요 | 123,126 | **2** |
| **합계** | **17개** | **17** |

**교차검사 결과:** 17개 중 이전 V211 위험 원장 61건에 포함된 자막은 **12개**, 해당 원장에서 누락됐던 자막은 **126,149,153,160,232번 5개**. 이 5개에는 기존 V211.1의 32개 교차 자막 관계도 등록되지 않아, 미해결 내용을 문맥만으로 승인할 수 없는 지점이다. V212의 **새 비공개 crosswalk**에는 5개를 실제 원문 인용·SHA와 함께 모두 보존했다. 이 5개는 더 이상 E2 위험 검토 대기열에서 식별되지 않는 상태는 아니지만, **의미 판정이 해결된 5개는 아니다**.

## 의미 검토: 추가로 관찰한 실제 과장·근거 부족

- Cue **123**의 괴리율이 ETF에만 존재한다는 절대 문구는 다른 상장지수증권 ETN의 가격-지표가치 괴리율과 구분해야 한다. KRX [ETN 지표가치 설명](https://www.krx.co.kr/contents/OPN/01/01030302/OPN01030302.jsp)은 ETN에도 별도 괴리율 개념을 표시한다. ETF NAV 공식과 ETN 지표가치 공식을 같은 지표라고 오해하면 안 된다. **원문 유지·범위 과장 리스크 표기**, 정정 확정 아님.
- Cue **126**의 ETF를 모든 주식 묶음으로 표현한 문장은 **주식 ETF 사례**와 **ETF 자산 범주의 일반 정의**를 구별해야 한다. KRX [ETF·ETN 기초자산별 조회](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp)에는 주식 외 채권·원자재·통화·혼합자산 등 분류가 있다. 따라서 **모든 ETF=주식 묶음**이라는 금융 사실은 승인 불가.
- Cues **149·153·160**은 문맥상 NAV 가격 사례·추적오차 설명·연간 코스피 20%와 ETF 18% 비교를 연결하지만 ASR 원음을 확정하지 않은 채 원문 문구를 조용히 교정하지 않는다. **232**는 지수 대비 ETF의 수익률 차트 화면이 현재 없으므로 차트로만 입증 가능한 진술을 승인하지 않는다.

원문·검토자 발언은 분리했다. 현재 ChatGPT 내부 재검토 결과를 외부 독립 골드로 사용하지 않는다. KRX 페이지 조회는 시점·금융 규정의 E4 원문 바이트 인증 및 개별 ETF 투자판단 승인을 의미하지 않는다.

## 비공개·소프트웨어 입증

- 비공개 개인 Library `V212_PRIVATE_ETF_V182_17OPEN_V211_FIVE_GAPS_SOURCE_CROSSWALK_20261120.json`, 원장 SHA-256 `22e3fdb9157b7fb9012691299b40385b67a768b9195f22331fd27528dee07dbd`, 실제 소스 250개 대조 **17/17·기존 12·신규 공백 5** 검문 PASS.
- 기존 `V210_PRIVATE_ETF_250_REAL_SOURCE_FIRST_DRAFT_20261120.json`, `V211_PRIVATE_ETF_250_CUE_SOURCE_RISK_ADJUDICATION_DOCKET_20261120.json`, `V211_1_PRIVATE_ETF_CROSS_CUE_CONDITION_EXCEPTION_REBUTTAL_LINKS_20261120.json`의 원문·파일 SHA 연결을 검사했다. 모든 사유증거는 GitHub에 공개하지 않았다.
- 공개 `v212_e2_private_historical_open_crosswalk.py`: **기존 3개 비공개 원장 바이트의 실제 재검문, 원본 17개 인용·SHA·전후 2 cue·후보 맵·관계 맵·필요 증거 종류**를 검문하는 일반화 가능한 source-bound 관문과 해당 영상 전용 고정 17개 OPEN wrapper. 분실/위조/검증 승인 위장 입력은 fail-closed.
- `test_v212_e2_private_historical_open_crosswalk.py`는 **합성 SRT**로 진행한 회귀 15건. 첫 RED는 테스트가 하위 예외 문구를 기대했지만 앞단의 개인 원장 SHA 가드가 먼저 차단한 이유이며, 승인 기준 변경 없이 기대 오류를 정정했다. [최신 CI run 44746802146](https://github.com/yhappcom/pensionport/actions/runs/44746802146) **236/236 PASS** (현행 E2 165/165 + 과거 E2/V176 53/53 + E1 18/18).

## E2 완료까지 남은 실제 요건

1. **V179의 24 OPEN·68 NO_ATOM** 원자별 비공개 V176 owner journal/원본·재개 head와 개별 사례를 확보해 현재 V210·V211·V212를 일대일/일대다 의미 단위로 재판정. 원본 없을 때 과거 owner 상태를 V182의 다른 원장으로 대체 금지.
2. 현재 V182의 9건 음성·5건 화면·1건 역사통계·2건 범위 과장을 **필요한 독립 증거별 HOLD**로 유지하고, 증거가 확보되면 ChatGPT가 원문 인용·조건·예외·반박을 재심. 자동 전사 추정·과장 사실 승격 금지.
3. 실물 원자 수정이 확정되면 V176 native append-only 영수증과 V6 정식 qualifier/speaker/stance 필드를 손실 없이 갱신·재검문. 현재 V212는 **검토 대기열 완전성의 개선**이지 정식 V6 승인은 아니다.
4. 외부 독립 고정 원자 정답셋이 없으므로 precision≥95%/recall≥98%/고위험 누락0 **미측정**. E2 HOLD, E3–E5 NOT RUN, 실제 지식 발행0.

`main`과 동결 V123/V126/V127/V128 무수정; PR #75 Draft 미병합.
