# 박곰희TV 선택적 추가검증 24건 — 증거 접근성 재점검 (2026-10-17)

## 이번 점검 결과

2026-10-17 GitHub 최신 [검증 상태 원장](../data/subtitles/optional_verification_register_20261012.json) 내 기존 **38건 중 RESOLVED 14건 / OPEN 24건**을 다시 대조했다. 이번에 **24건 상태를 증거 없이 종결한 사례는 없음(신규 RESOLVED 0)**. HIGH 9 / MEDIUM 9 / LOW 6. **이 24건은 전체 교육 V3 승인 99편/1,790건을 뒤집거나, 이미 진행 중인 #101 이후 영상 연구를 정지시키는 전역 게이트가 아님.**

확인한 차단사유별 건수:

| 추가 입증이 필요한 증거 종류 | OPEN | 조치 |
|---|---:|---|
| 원음/원화면 또는 별도 전사 | 6 | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` 원자료가 확인된 건만 개별 종결 |
| 개별 계약/계좌/신고증빙 | 10 | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` 원자료가 확인된 건만 개별 종결 |
| 상품별 해당일 시세·수수료/공시 | 5 | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` 원자료가 확인된 건만 개별 종결 |
| 백테스트 원시계열·도서 판본/원표 | 2 | `NEEDS_DEFINED_COMPARABLE_HISTORICAL_DATA_OR_ORIGINAL_PUBLICATION` 원자료가 확인된 건만 개별 종결 |
| 비교 가능한 통계의 정의·분모 | 1 | `SOURCE_AND_CONTEXT_NOT_SPECIFIED` 원자료가 확인된 건만 개별 종결 |

## 이번에 외부에서 확인했으나 종결하지 않은 증거

**`WGFPHeM6-6I-2026_FIVE_YEAR_GOVERNMENT_BOND_YTM` (MEDIUM):** [재정경제부 2026-09-21 5년물 국고채 경쟁입찰 고시목록](https://mofe.go.kr/st/fnancstats/ktb50201.do?bbsId=MOSFBBS_000000000049&menuNo=6050300)에 `국고04125-3109` 발행이 식별되고, 2026-09-28 비경쟁인수 관련 결과도 나타난다. **종목명 안의 4.125 또는 표면금리·발행시장 입찰수익률과 해당 영상 발언의 촬영일/잔존만기별 2차 유통 YTM은 다르다.** 발언 당시가 언제인지 및 동일 종목 시장 시세원표가 없어 영상의 ‘5년물 약 5%’를 참/거짓으로 확정하지 않음. 기존 영상원장에는 2026-09-30 유통 5년 YTM 4.203% 관련 과거 출처도 기록돼 있으나 촬영일 특정이 빠졌다.

**개인 계약 범주 10건:** 실제 증여약정·보험 해약환급표·가계 대출/매매원장·공제회 지급표 등은 당사자의 개별 자료 없이 복원하거나 공개통계로 대체할 수 없다. **관련 서류가 확보되기 전에는 세액·해지환급액·은퇴 월수령액 확정금지**.

**영상 수치 원음/슬라이드 범주 6건:** 기존 원본 자동자막과 별도의 직접 원음·화면 비교가 없으므로 인식오류 가능성을 완전히 해소하지 못했다. 단순 수학반증은 교육용으로 유지: 연7% 월30만원 적립 7년과 10년, 4.4억원 연6%/월6%, 3.0848억원을 30년 연4%로 월말 인출하는 예시의 계산은 [기존 원표 검산](OPEN_24_EVIDENCE_GATE_REVIEW_20261013.md)에 상세 기록됐으나 **영상의 실제 표시수치/상품 약정과 동일하다는 뜻이 아니다**.

## 24개 OPEN 항목별 정확한 종결 조건

| # | 항목 ID | 우선순위 | 증거문턱 | 누락된 독립 검증 원본 |
|---|---|---|---|---|
| 1 | `sz5N9WJS310-AUDIO_OR_FRAME_NUMERIC` | HIGH | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | 07:46~08:05 실제 오디오와 7년·10년 원본 시뮬레이션 화면. |
| 2 | `keu5SvpD7KE-AUDIO_NUMERIC` | MEDIUM | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| 3 | `3MyhYE2jmuE-LEGAL_TRANSACTION_FACTS` | HIGH | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 권리증여 약정·해지시 일시금·이전 10년 증여내역 |
| 4 | `OfkY343OaNs-PRODUCT_TAX_EFFECTIVE_RATE` | HIGH | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | 상품 법적 구조 및 배당·매매별 브로커 세금명세·한일미 조약 적용·거주자/계좌 조건. |
| 5 | `YNOSY15ppf8-HISTORICAL_QUOTE_AND_FEE` | LOW | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| 6 | `uiauof6tOFk-ORIGINAL_BACKTEST_SOURCE_DATA` | HIGH | `NEEDS_DEFINED_COMPARABLE_HISTORICAL_DATA_OR_ORIGINAL_PUBLICATION` | 1972~2022 월간 원시 총수익 시계열·배당/롤/리밸런싱/비용 입력과 도서 원표 |
| 7 | `LVE7XN_esTc-SCREEN_EXAMPLE` | LOW | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | Video actual audio/frames, official primary legal notice, or original source data is newly available and could change the affected claim. |
| 8 | `oxMpNgnbISw-ORIGINAL_MODEL_PERFORMANCE` | MEDIUM | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | Video screen of simulation/table or source time series becomes available and precise historical return comparison is needed. |
| 9 | `6VEfKF7BzZU-CMA_PRODUCT_SPECIFIC_COSTS` | LOW | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | The referenced institution and exact CMA product and disclosure effective on recommendation date are identified. |
| 10 | `cSNjKKdtp6M-DATED_CMA_RATE_SLIDE` | LOW | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | 영상 2026-07-22 원화면과 해당 금융기관 상품별 금리 공시 |
| 11 | `ZTlLcC4gE0M-PERSONAL_TAX_PROOF` | MEDIUM | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 세액공제 확인서 및 연금납입/출금 계좌 원장 |
| 12 | `oMs4-3ZOevE-ORIGINAL_RETIREMENT_COMPOUNDING_SLIDE` | MEDIUM | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | The relevant video slide/source spreadsheet becomes accessible and materially affects investment choice |
| 13 | `4CQ4FjGT2gA-HISTORICAL_COMPILATION_ACCOUNT_RETURNS` | MEDIUM | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 사연 당사자 동의하 매입/매도·입출금·대출 원장 |
| 14 | `nCXWFko0TaA-ANNUAL_VS_MONTHLY_6PCT_AUDIO` | HIGH | `NEEDS_ORIGINAL_AUDIO_VIDEO_OR_DISTINCT_PUBLIC_ASR` | 00:48~01:02 실제 음성 및 원래 화면의 연/월 단위. |
| 15 | `HfrBi5mzm8w-MINOR_PENSION_SAVINGS_ELIGIBILITY` | MEDIUM | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 금융사별 2026 미성년자 연금저축계좌 개설 업무지침/약관과 대리인 서류. |
| 16 | `zi9x_q2fYoc-MUTUAL_AID_30YEAR_2130000_CONTRACT` | HIGH | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 영상 사용 공제회·상품명·전환기준일·실제 30년 분할수령표와 원본 화면. |
| 17 | `zi9x_q2fYoc-MUTUAL_AID_PAYOUT_TAX_HEALTH` | HIGH | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 정확한 기관·상품 유형·가입시기·공식 원천징수/건보료 판정 문서. |
| 18 | `WGFPHeM6-6I-2026_FIVE_YEAR_GOVERNMENT_BOND_YTM` | MEDIUM | `NEEDS_DATED_PRODUCT_MARKET_PRICE_OR_ISSUER_DISCLOSURE` | 영상 실제 발언일 및 동일 5년 국고채 공식 유통 YTM |
| 19 | `33HPIrzl6xI-PERIODIC_GIFT_ACTUAL_CONTRACT` | HIGH | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 월18.9만원 120회 증여계약 원본·취소권·실제 이행·기존 10년 합산 |
| 20 | `yDt8Ki7d_Yk-GIFT_240M_ELIGIBILITY_TIMING` | MEDIUM | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 개별 증여일/수증자 가족관계/혼인신고·출산·수증자의 이전 공제를 확인할 때 |
| 21 | `OdR6ICkcthc-2025_RETIREMENT_SUBGROUP_RETURN_CHART` | MEDIUM | `SOURCE_AND_CONTEXT_NOT_SPECIFIED` | 2025 투자 백서 상세 원표에서 동일한 분모·업권·실적형 기준과 영상 38:24~38:46 원화면 확인. |
| 22 | `i32DeJPzsfE-SUBSCRIBER_LOAN_INVESTMENT_CUSTODY` | LOW | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 본인 제공의 대출약정/상환장부/월별 자산가치·순납입 자료를 명시적 승인하에 수령할 때 |
| 23 | `835_phhMGM8-KOSTOLANY_BOOK_EXACT_TEXT_AND_9MONTH_LAG` | LOW | `NEEDS_DEFINED_COMPARABLE_HISTORICAL_DATA_OR_ORIGINAL_PUBLICATION` | 구체 도서판본과 인용 페이지·측정 가능한 시장 금리/주가표를 입수할 때 |
| 24 | `lWWz4i7vIX4-INSURANCE_SURRENDER_POLICY_FACTS` | HIGH | `NEEDS_ACTUAL_ACCOUNT_CONTRACT_OR_HOLDER_FACTS` | 보험사 발급 유지·해지환급표, 약관, 보험계약대출, 대체 보장/인수 조건. |

## 연구 진행 분리

- **#81~93 13편/311교육 주장 V3 완료**, 증권사 판촉 3건 제외, 2026-10-16 CI 완료. 원본 SRT(13편)와 공개 자동전사 비교는 해당 영상 분석 내 관리.
- **#71 새로 확보:** 이전에는 사용자 SRT가 없어 `SOURCE_SRT_UNAVAILABLE`만 남아 있었지만 2026-10-17 공개 한국어 전사 **21,424 정규화 문자 SHA256 `75c5344077f5ee0aacac242903f8b07ed523a1ba991fd80732a8ff8dc199736c`**를 확보, 공개전사 기반 후보 13개를 별도 예비 보고서로 작성함. 원본 SRT/밀리초 큐가 없어 **#71 V3 미승인**([출처 기록](../data/subtitles/source_acquisition/video71_public_asr_precheck_20261017.json), [후보 검토](VIDEO71_PUBLIC_ASR_PRELIMINARY_20261017.md)).
- 다음 고유 증빙이 없는 동안 OPEN 24건은 억지 종결하지 않고, 추가 진행은 **#71 시각있는 원본 전사 확보 또는 #101 이후 새 영상 출처 확보**로 전환할 수 있다.

**보안·품질:** 개인 계약 문서는 소유자의 승인 없이 외부에서 구하지 않으며, 사용자 제공 전체 SRT/ZIP 전문을 공개저장소에 등록하지 않는다. 원음·영상 프레임을 직접 보지 않은 작업은 그런 검증을 했다고 기록하지 않는다.
