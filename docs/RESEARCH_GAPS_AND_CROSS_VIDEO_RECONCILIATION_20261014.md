# 박곰희TV 누적 연구 부족분·교차검증 점검 — 2026-10-14

> **연구 심사 현황 정리와 오류 정정 문서**. 1~70 이전 승인 V3 및 #72~77 승인 V3를 소급 취소하거나 재승인한 문서가 아니다. 공식 법령·상품 시행일을 확인해 필요한 비정식 교정만 신규 기록했다. **main 수정 금지, 원본 SRT/ZIP 전문 공개 금지, 기존 원장을 제거하지 않음**.

## 1. 판정과 출처의 층위

| 연구범위 | 기존 승인 | 이번 변경 | 정확한 한계 |
|---|---:|---:|---|
| 기존 #1~#70 70편 | 1,052 주장 | 기존 승인 건수 그대로 | 실제 사용자 원본 SRT 해시 대조된 이력은 존재하나 원음·전체 독립 ASR 정확대조 별도 |
| #71~#100 30편 | #72~#77 6편·178 주장 | **0편 추가 승인** | #71 원본 SRT 미확보 |
| #78~#91 14편 | 0편 | **360개 공개전사 잠정 분석의 한계 재분류** | 원본 14개 비공개 SRT 접근·재해시/ASR Diff **0/14**, 일부 영어번역 ASR |
| 새 #92 쇼츠 | 0편 | **11개 공개 영어번역 ASR 잠정 주장** | 동일 풀영상 ETF자동매수 주제를 다룬 #85와 중복, 독립 실증으로 중복 계수하면 안 됨 |

- **증거 단위 불일치 방지:** `PRIMARY_CONFIRMED`은 해당 조문 또는 산식이 근거가 있다는 주장별 좁은 의미이고 공개 자동전사 화자 원문·고객 실제 계좌·과거 수익률·개별 세금 적용에 대한 검증완료를 뜻하지 않는다. 공개 ASR 원본이 **번역된 영어 전사**인 #87, #88, #92는 한국어 직접인용으로 사용할 수 없다.
- 정확한 영상·자막 스냅샷에 의존하는 과거 체결가/과거 운용사 보수/수익률은 날짜 붙은 1차자료가 없으면 **OPEN/QUALIFIED**, AI 검색이나 SEC 투자자 위험안내만 연결한 것은 사실확정 자료 아님.
- #79 미래 로봇주 상승·코스피 지수목표·가상 계좌, #82 보험 적립식 개인 IRR 및 노후 7%·6% 시나리오는 실증·원본 계좌 없는 개인 전망/산술 예시이며 **원금보장·개인수익 확정으로 사용 금지**.
- #89 푸른씨앗과 #90 ISA 외국세액공제 등 **시행일 조건**이 바뀌는 제도는 영상 촬영일/공식 발표일/적용개시일/현재 활용일을 분리해야 한다.

## 2. 기존 자료 상충 발견 및 실제 정정

### 시정 1: 정기금 증여 189,000원 × 10년 할인액 1,993만원 — 산술 불일치 취소

- 기존 초기 #86 검토에서 **120개월 각각 월말 지급·연 3% 유효연복리**로 할인해 약 1,961.11만원을 얻었고 강사의 1,993만원과 '불일치'라 기록했다. 그러나 **#6 `3MyhYE2jmuE-07`에는 이미 정기금 권리를 연도별 금액으로 산정하는 법정 모형이 검증·저장**되어 있었다. #86 작성 당시 이전 연구와 교차조회하지 않아 잘못된 오류신고를 한 것이므로 정정함.
- [상증세법 시행령 §62](https://law.go.kr/LSW/lsLinkCommonInfo.do?lspttninfSeq=75955) · [시행규칙 §19의2](https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0019&lsiSeq=284609&urlMode=lsScJoRltInfoR): 1년 지급분 2,268,000원, 연3% 할인 가정. `2,268,000 × Σ_{n=0..9} (1.03)^(-n) = 19,926,895원`이므로 **영상 약1,993만원 재현**. 첫 연도를 다음연도로 기산하면 `n=1..10` 약1,934.65만원, 월별 금융수학 예시와 각각 다름.
- 교정한 곳: [#86 pilot `-34`](../data/subtitles/pilots/kdiFNJADwzI.json) 및 [#86 보고서](../knowledge/VIDEO86_CHILD_GIFT_TAX_PROVISIONAL_20261014.md); #6 [이전 선택검증 OPEN 원장](../data/subtitles/optional_verification_register_20261012.json)의 상호 참조를 추가. **계약 일시금 가치·약정해지·기존10년 증여/실행 상태는 여전히 OPEN**, 제시 숫자의 계산재현과 세액0원 법적 승인 별개.

### 시정 2: #89 푸른씨앗 1인 사업장 가입 불가 표현의 범위

- 2026-03-27 영상은 당시 **사업주가 퇴직급여를 부담하는 사업장 기금제도**를 설명. [고용노동부 2026-07-22 발표](https://moel.go.kr/news/enews/report/enewsView.do?news_seq=19679)와 [2026-04-02 시행예고](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19175): **2026-07부터 50인 미만 사업장**, 그리고 **자영업자·노무제공자 등 본인부담 개인 IRP 가입자부담금계정**도 허용. **2027-01부터 100인 미만 기업형**. 영상의 '1인 사업장 불가'를 **자영업자·혼자 일하는 모든 국민이 2026-10에도 가입할 수 없다는 현재법 일반명제**로 옮기면 오류.
- 단, 사업장의 퇴직급여 근로자 고용구조에 따른 기업형 적격성은 구체적 사실확인 필요. 재정지원 요건(30인 이하, 월보수 281만원 미만)은 가입할 수 있는 기업규모 확대와 별개.
- 교정한 곳: [#89 pilot `-04`](../data/subtitles/pilots/qzGqHzKfs18.json), [#89 보고서](../knowledge/VIDEO89_GREEN_SEED_RETIREMENT_2026_PROVISIONAL_20261014.md).

### 추가 보존: 이미 적법한 제한규칙

- #83 ISA 만기 해외원천세 정산 vs 연금계좌 **새 과세이연**, ISA 만기일로부터 60일, 세액공제 대상 전환액의10% 최대300만원과 세액300만원 환급은 다른 개념.
- #90 ISA 외국납부세액공제는 2025-07 도입, ISA 보유 **국내 상장** 외국투자 ETF와 미국 직접상장 주식 혼동금지.
- #84 4% 룰 원금유지 아님, #91 3.4억원에서 월170만원은 초기연6% 인출로 영구 수익확정 불가.
- #87·#92는 #85와 정기매수(DCA) 원리를 중복 설명하며 **동일 풀영상 `zDcF_zPTSYE`**로 이어지므로 영상 수는 별개지만 실증근거 건수로 중복계수하지 않는다.

## 3. 오래된 1~70 선택검증 24 OPEN 실제 재감사

2026-10-13 기존 선택 검증원장 총 **38개 중 해결 14, OPEN 24**. 중요도별 **HIGH 9, MEDIUM 9, LOW 6**. #78~#92의 원본 누락·개인상품 불확실성은 이 24건에 들어 있지 않은 **별개 검증 대기열**. 이 문서 정리 자체로 기존 24건의 실제 증거 입증을 완료했다고 판단하지 않았다.

| 증거 미확보 유형 | OPEN |
|---|---:|
| `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | 6 |
| `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 10 |
| `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | 5 |
| `NEEDS_DEFINED_COMPARABLE_HISTORICAL_DATA_OR_ORIGINAL_PUBLICATION` | 2 |
| `SOURCE_AND_CONTEXT_NOT_SPECIFIED` | 1 |

### 높은 우선순위 9건

| 검증 항목 | 필요한 독립 증거·종료조건 | 이번 판정 |
|---|---|---|
| `sz5N9WJS310-AUDIO_OR_FRAME_NUMERIC` | 07:46~08:05 실제 오디오와 7년·10년 원본 시뮬레이션 화면. | OPEN 유지 |
| `3MyhYE2jmuE-LEGAL_TRANSACTION_FACTS` | 권리증여 약정·해지시 일시금·이전 10년 증여내역 | OPEN 유지 |
| `OfkY343OaNs-PRODUCT_TAX_EFFECTIVE_RATE` | 상품 법적 구조 및 배당·매매별 브로커 세금명세·한일미 조약 적용·거주자/계좌 조건. | OPEN 유지 |
| `uiauof6tOFk-ORIGINAL_BACKTEST_SOURCE_DATA` | 1972~2022 월간 원시 총수익 시계열·배당/롤/리밸런싱/비용 입력과 도서 원표 | OPEN 유지 |
| `nCXWFko0TaA-ANNUAL_VS_MONTHLY_6PCT_AUDIO` | 00:48~01:02 실제 음성 및 원래 화면의 연/월 단위. | OPEN 유지 |
| `zi9x_q2fYoc-MUTUAL_AID_30YEAR_2130000_CONTRACT` | 영상 사용 공제회·상품명·전환기준일·실제 30년 분할수령표와 원본 화면. | OPEN 유지 |
| `zi9x_q2fYoc-MUTUAL_AID_PAYOUT_TAX_HEALTH` | 정확한 기관·상품 유형·가입시기·공식 원천징수/건보료 판정 문서. | OPEN 유지 |
| `33HPIrzl6xI-PERIODIC_GIFT_ACTUAL_CONTRACT` | 월18.9만원 120회 증여계약 원본·취소권·실제 이행·기존 10년 합산 | OPEN 유지 |
| `lWWz4i7vIX4-INSURANCE_SURRENDER_POLICY_FACTS` | 보험사 발급 유지·해지환급표, 약관, 보험계약대출, 대체 보장/인수 조건. | OPEN 유지 |

### 나머지 15건 (보통 9·낮음 6)

| 우선순위 | 검증 항목 | 자료 미확보 사유 |
|---|---|---|
| MEDIUM | `keu5SvpD7KE-AUDIO_NUMERIC` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| MEDIUM | `oxMpNgnbISw-ORIGINAL_MODEL_PERFORMANCE` | Video screen of simulation/table or source time series becomes available and precise historical return comparison is needed. |
| MEDIUM | `ZTlLcC4gE0M-PERSONAL_TAX_PROOF` | 세액공제 확인서 및 연금납입/출금 계좌 원장 |
| MEDIUM | `oMs4-3ZOevE-ORIGINAL_RETIREMENT_COMPOUNDING_SLIDE` | The relevant video slide/source spreadsheet becomes accessible and materially affects investment choice |
| MEDIUM | `4CQ4FjGT2gA-HISTORICAL_COMPILATION_ACCOUNT_RETURNS` | 사연 당사자 동의하 매입/매도·입출금·대출 원장 |
| MEDIUM | `HfrBi5mzm8w-MINOR_PENSION_SAVINGS_ELIGIBILITY` | 금융사별 2026 미성년자 연금저축계좌 개설 업무지침/약관과 대리인 서류. |
| MEDIUM | `WGFPHeM6-6I-2026_FIVE_YEAR_GOVERNMENT_BOND_YTM` | 영상 실제 발언일 및 동일 5년 국고채 공식 유통 YTM |
| MEDIUM | `yDt8Ki7d_Yk-GIFT_240M_ELIGIBILITY_TIMING` | 개별 증여일/수증자 가족관계/혼인신고·출산·수증자의 이전 공제를 확인할 때 |
| MEDIUM | `OdR6ICkcthc-2025_RETIREMENT_SUBGROUP_RETURN_CHART` | 2025 투자 백서 상세 원표에서 동일한 분모·업권·실적형 기준과 영상 38:24~38:46 원화면 확인. |
| LOW | `YNOSY15ppf8-HISTORICAL_QUOTE_AND_FEE` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| LOW | `LVE7XN_esTc-SCREEN_EXAMPLE` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| LOW | `6VEfKF7BzZU-CMA_PRODUCT_SPECIFIC_COSTS` | The referenced institution and exact CMA product and disclosure effective on recommendation date are identified. |
| LOW | `cSNjKKdtp6M-DATED_CMA_RATE_SLIDE` | 영상 2026-07-22 원화면과 해당 금융기관 상품별 금리 공시 |
| LOW | `i32DeJPzsfE-SUBSCRIBER_LOAN_INVESTMENT_CUSTODY` | 본인 제공의 대출약정/상환장부/월별 자산가치·순납입 자료를 명시적 승인하에 수령할 때 |
| LOW | `835_phhMGM8-KOSTOLANY_BOOK_EXACT_TEXT_AND_9MONTH_LAG` | 구체 도서판본과 인용 페이지·측정 가능한 시장 금리/주가표를 입수할 때 |

## 4. 다음 영상 확장의 품질 문턱

1. **같은 주제 재등장 시 예전 주장 ID와 숫자 계산을 반드시 교차 조회**: #6↔#86 같은 산식 충돌 금지. 원본 SHA 등록메타는 실제 바이트 검증으로 착각하지 않음.
2. 최신 금융 규정은 촬영일·게시일·제도 공포/적용일 구별, 현재 금융회사 상품/실제 고객 계좌와 혼동 금지.
3. '도구 규정·정기매수는 불변개념'과 '영상의 사실관계' 분리. 일반 SEC 리스크 안내 링크만으로 투자 성과·미래전망을 PRIMARY_CONFIRMED로 승인하지 않음.
4. 자동화/정액매수 공통 원칙이 #85·#92에 반복 등장할 때 영상마다 주장목록은 독립하되 **독립된 경험적 입증 횟수로 추가하지 않는다**.
5. 선택검증 고위험 항목 9건은 개인 보험/공제회 계약·원음 장면·상품 과세명세/원본 백테스트 시계열이 도착할 때만 입증/해결 판정. 현재는 원본 접근 없음.

**적용 브랜치:** `feat/subtitles-incremental-registry-20261009`; 기본 `main` 변경 불가. 이 문서는 연구자료의 오류 정정/품질 게이트이지 개인 투자·세무신고 또는 금융상품 주문 지시가 아니다.
