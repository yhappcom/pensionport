# 71번 주장검토 완료 이후 — 선택적 추가검증 OPEN 24건 후속 실행 원장

**기준일:** 2026-10-17  
**작업 순서:** #71 내용심사 및 근거 기록 완료 → **본 OPEN 24건 증빙 요구사항 정리** → 사용자 지시 전까지 #101 신규 V3 분석 착수하지 않음.  
**검토 대상:** [기존 개별 검증 원장](../data/subtitles/optional_verification_register_20261012.json) / [기존 24건 근거 재점검](../knowledge/OPTIONAL_24_EVIDENCE_GATE_REFRESH_20261017.md).

## 1. 재집계

- 전체 선택적 검증 항목 **38건**: **RESOLVED 14건**, **OPEN 24건**.
- OPEN 중요도: **HIGH 9, MEDIUM 9, LOW 6**.
- 증빙 게이트: 원음/프레임 6건, 개인 계약/계좌 10건, 날짜 지정 상품/호가 5건, 과거 모델/원자료 2건, 통계 분모/원표 1건(합계 24건).
- #81~93 잠정 314개 검토 항목은 별도 정식 교육 판정이 끝나 **본 24건과 혼합하지 않음**.
- **#71 `V3_SOURCE_GATE_OPEN`은 이 역사적 OPEN 24건과 별도**이며 원래 24건을 25건으로 늘리지 않는다.
- 이번 원장 재분류는 독립적인 원음, 개인계약서, 당시 시장 체결시세나 백테스트 원시계열을 새로 발견했다는 뜻이 아니다. **근거 없이 해결 처리한 항목 0건**, 기존 `status`와 중요도를 유지한다.

## 2. 항목별 근거 문턱 — 중복 없이 24개

### 원음/원화면/독립전사 — 6건

| 등급 | OPEN 항목 ID | 종결에 필요한 구체적 원자료 |
|---|---|---|
| HIGH | `sz5N9WJS310-AUDIO_OR_FRAME_NUMERIC` | 07:46~08:05 실제 오디오와 7년·10년 원본 시뮬레이션 화면. |
| HIGH | `nCXWFko0TaA-ANNUAL_VS_MONTHLY_6PCT_AUDIO` | 00:48~01:02 실제 음성 및 원래 화면의 연/월 단위. |
| MEDIUM | `keu5SvpD7KE-AUDIO_NUMERIC` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| MEDIUM | `oxMpNgnbISw-ORIGINAL_MODEL_PERFORMANCE` | Video screen of simulation/table or source time series becomes available and precise historical return comparison is needed. |
| MEDIUM | `oMs4-3ZOevE-ORIGINAL_RETIREMENT_COMPOUNDING_SLIDE` | The relevant video slide/source spreadsheet becomes accessible and materially affects investment choice |
| LOW | `LVE7XN_esTc-SCREEN_EXAMPLE` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |

### 개별 계약/계좌/권리사실 — 10건

| 등급 | OPEN 항목 ID | 종결에 필요한 구체적 원자료 |
|---|---|---|
| HIGH | `3MyhYE2jmuE-LEGAL_TRANSACTION_FACTS` | 권리증여 약정·해지시 일시금·이전 10년 증여내역 |
| HIGH | `zi9x_q2fYoc-MUTUAL_AID_30YEAR_2130000_CONTRACT` | 영상 사용 공제회·상품명·전환기준일·실제 30년 분할수령표와 원본 화면. |
| HIGH | `zi9x_q2fYoc-MUTUAL_AID_PAYOUT_TAX_HEALTH` | 정확한 기관·상품 유형·가입시기·공식 원천징수/건보료 판정 문서. |
| HIGH | `33HPIrzl6xI-PERIODIC_GIFT_ACTUAL_CONTRACT` | 월18.9만원 120회 증여계약 원본·취소권·실제 이행·기존 10년 합산 |
| HIGH | `lWWz4i7vIX4-INSURANCE_SURRENDER_POLICY_FACTS` | 보험사 발급 유지·해지환급표, 약관, 보험계약대출, 대체 보장/인수 조건. |
| MEDIUM | `ZTlLcC4gE0M-PERSONAL_TAX_PROOF` | 세액공제 확인서 및 연금납입/출금 계좌 원장 |
| MEDIUM | `4CQ4FjGT2gA-HISTORICAL_COMPILATION_ACCOUNT_RETURNS` | 사연 당사자 동의하 매입/매도·입출금·대출 원장 |
| MEDIUM | `HfrBi5mzm8w-MINOR_PENSION_SAVINGS_ELIGIBILITY` | 금융사별 2026 미성년자 연금저축계좌 개설 업무지침/약관과 대리인 서류. |
| MEDIUM | `yDt8Ki7d_Yk-GIFT_240M_ELIGIBILITY_TIMING` | 개별 증여일/수증자 가족관계/혼인신고·출산·수증자의 이전 공제를 확인할 때 |
| LOW | `i32DeJPzsfE-SUBSCRIBER_LOAN_INVESTMENT_CUSTODY` | 본인 제공의 대출약정/상환장부/월별 자산가치·순납입 자료를 명시적 승인하에 수령할 때 |

### 기준시점 금융상품 공시/시장호가 — 5건

| 등급 | OPEN 항목 ID | 종결에 필요한 구체적 원자료 |
|---|---|---|
| HIGH | `OfkY343OaNs-PRODUCT_TAX_EFFECTIVE_RATE` | 상품 법적 구조 및 배당·매매별 브로커 세금명세·한일미 조약 적용·거주자/계좌 조건. |
| MEDIUM | `WGFPHeM6-6I-2026_FIVE_YEAR_GOVERNMENT_BOND_YTM` | 영상 실제 발언일 및 동일 5년 국고채 공식 유통 YTM |
| LOW | `YNOSY15ppf8-HISTORICAL_QUOTE_AND_FEE` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| LOW | `6VEfKF7BzZU-CMA_PRODUCT_SPECIFIC_COSTS` | The referenced institution and exact CMA product and disclosure effective on recommendation date are identified. |
| LOW | `cSNjKKdtp6M-DATED_CMA_RATE_SLIDE` | 영상 2026-07-22 원화면과 해당 금융기관 상품별 금리 공시 |

### 원본 백테스트/도서 계열 — 2건

| 등급 | OPEN 항목 ID | 종결에 필요한 구체적 원자료 |
|---|---|---|
| HIGH | `uiauof6tOFk-ORIGINAL_BACKTEST_SOURCE_DATA` | 1972~2022 월간 원시 총수익 시계열·배당/롤/리밸런싱/비용 입력과 도서 원표 |
| LOW | `835_phhMGM8-KOSTOLANY_BOOK_EXACT_TEXT_AND_9MONTH_LAG` | 구체 도서판본과 인용 페이지·측정 가능한 시장 금리/주가표를 입수할 때 |

### 동일 분모 비교통계/화면 — 1건

| 등급 | OPEN 항목 ID | 종결에 필요한 구체적 원자료 |
|---|---|---|
| MEDIUM | `OdR6ICkcthc-2025_RETIREMENT_SUBGROUP_RETURN_CHART` | 2025 투자 백서 상세 원표에서 동일한 분모·업권·실적형 기준과 영상 38:24~38:46 원화면 확인. |



## 3. 실행 우선순위와 차단선

1. **HIGH 9건을 먼저 재평가:** 숫자 음성/원화면에 따른 산술 결론 뒤집힘, 과거 백테스트 성과, 세금·계약·실제 수령액 오인 위험에 중점. 다른 공식자료가 '일반 원리'만 뒷받침하는 경우 실제 거래·계약을 `PRIMARY_CONFIRMED`로 승격하지 않는다.
2. **공개적으로 회수 가능한 객관 증거 검토:** 금융상품의 발언 당시 *정확한* 발행사·상품·기간·시세·보수/규정과 공식 원표, 책의 실제 판본과 입력자료, 표본 정의가 같은 통계원표. 관련 식별자가 없으면 `OPEN`으로 남기고 단순 최신 금리/유사상품 수치를 대입하지 않는다.
3. **제3자 개인 계약/계좌 자료 10건:** 공개 인터넷으로 추정·복원하거나 사용자에게 타인의 민감 문서를 무단 수집시키지 않는다. 자료 접근 권한이 존재하지 않으면 `OPEN` 유지하고 해당 개인의 세율·환급금·원금·실현성과를 확정하지 않는다.
4. **원음/화면 6건:** 원본 영상 실제 오디오·슬라이드/계산식 또는 독립적인 고품질 전사로 불명확 수치만 선택 확인한다. 자동자막끼리 본문이 일치하는 것은 원음 인증이 아니다.
5. **정식 종결 요건:** 항목마다 새로운 1차 증거의 URL 또는 보관 식별자, 원문 해당 시각/수치, 적용 날짜·조건, 검산/반례, 해결 사유를 등록한 뒤 `RESOLVED`로 변경한다. 미발견은 해결이 아니다.

## 4. #101 착수 여부

현재 결과는 **OPEN 목록의 재집계 및 필요한 증거 정리 완료**, **OPEN 24건 전체 해결 완료가 아님**. 전체 연구 운영 기준상 과거 비핵심 OPEN은 다른 영상 교육 연구의 전역 차단조건이 아니지만, 이번 사용자 지시는 **#71 → OPEN 정리 → #101** 순서이다. 따라서 본 검토 회차에서는 **#101의 자막 확보/분석 및 V3 승인 기록을 생성하지 않는다**. 사용자에게 미해결 원인을 공개한 뒤 후속 진행 범위를 결정한다.

**보안:** `main`·개인 자산/KIS/Apps Script·비공개 자막 전문 및 기존 V3 승인 수치 불변.
