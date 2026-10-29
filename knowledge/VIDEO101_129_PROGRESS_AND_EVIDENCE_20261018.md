# 박곰희TV 정식 로스터 #101~129 — 원본 SRT 전편 수집 및 V3 근거 분석 진행 기록

> **2026-10-18 후속 완료:** 이 문서는 23/29편 승인 당시의 이전 진행현황을 보존한 것이다. 이후 나머지 #120·#124~127·#129의 94개 추가 교육 주장을 심사해 **101~129 총 29편·289건 V3 승인, 미승인 0편**으로 마감했다. 최신 [최종 검증 보고서](VIDEO101_129_V3_COMPLETE_EVIDENCE_20261018.md) 및 [진행 원장](../data/subtitles/research_progress_batch_101_129_20261018.json), [원본 SHA 등록부](../data/subtitles/registry_101_129_20261018.json)가 우선한다. 이전 23편·195건의 아래 표기는 마감 전 역사적 상태다. 전체 누적 **129편·2,092건**, 선택추가검증 OPEN24는 변경하지 않았다.

**검토일:** 2026-10-18 (KST)  
**GitHub:** `yhappcom/pensionport` / `feat/subtitles-incremental-registry-20261009`  
**비공개 원본:** 사용자 제공 `101-129.zip` (477,242바이트, ZIP SHA-256 `3e3e7cbbccd95262ba43506ac642ff78d78afeb54de718bf574b4f78cb650951`); **원문 공개 GitHub 업로드 금지 준수.**

## 현재 산출물 및 엄격한 분모

- 정확한 로스터 ID #101~129 **29편 자막 파일/29편** 일치, **누락 0·중복 0**. 사용자 ZIP CRC PASS, 총 **17,701개 자막 큐 / 1,352,355바이트**. macOS 보조파일 29개는 별도 제외.
- **정식 V3 승인: 17편 · 103개 선별 교육 주장**, 직접 검토한 원본 큐는 이 중 **3,590개**. 나머지 **12편은 원본 SRT 파일과 구조 및 SHA만 확인한 미승인 대기**로 남는다. 소스 등록을 V3 교육 승인으로 간주하지 않는다.
- 기존 #1~100 **100편·1,803건**에서 누적 **117편·1,906건**. 로스터 총 791편 중 V3 미승인 674편. 기존 추가검증 원장 **OPEN 24건 / RESOLVED 14건** 수치는 변경하지 않는다.
- 검증 스크립트 [audit gate](../scripts/audit_subtitle_review_gate.py)는 출처 ZIP SHA/총 크기/전체 레코드 29개를 검사하고, `PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3` 및 원본 전문 검토 상태를 명시한 파일만 분석 등록부에 추가한다. 기존 #71 특례 및 #1~100, `main` 변경 없음.

## 29편 진행현황 및 출처 메타데이터

| 로스터 | YouTube ID | 원본 큐 | V3 상태 | 이번 교육 주장 |
|---:|---|---:|---|---:|
| #101 | [`_gyLWp83OMU`](https://www.youtube.com/watch?v=_gyLWp83OMU) | 1,449 | **APPROVED** | 16 |
| #102 | [`Xgjhy0HKqcQ`](https://www.youtube.com/watch?v=Xgjhy0HKqcQ) | 33 | **APPROVED** | 5 |
| #103 | [`TB_H7_oJlAs`](https://www.youtube.com/watch?v=TB_H7_oJlAs) | 22 | **APPROVED** | 4 |
| #104 | [`0R34RYiwDC4`](https://www.youtube.com/watch?v=0R34RYiwDC4) | 25 | **APPROVED** | 4 |
| #105 | [`-3iNxrjeQak`](https://www.youtube.com/watch?v=-3iNxrjeQak) | 785 | **APPROVED** | 13 |
| #106 | [`sYybI-K5o0o`](https://www.youtube.com/watch?v=sYybI-K5o0o) | 1,536 | SOURCE_ONLY / PENDING | — |
| #107 | [`Gk3-ZC9W3vw`](https://www.youtube.com/watch?v=Gk3-ZC9W3vw) | 719 | SOURCE_ONLY / PENDING | — |
| #108 | [`AX1AAZVOnJU`](https://www.youtube.com/watch?v=AX1AAZVOnJU) | 29 | **APPROVED** | 4 |
| #109 | [`Hv7WZ0APt1o`](https://www.youtube.com/watch?v=Hv7WZ0APt1o) | 23 | **APPROVED** | 4 |
| #110 | [`8tTh8bRc4OI`](https://www.youtube.com/watch?v=8tTh8bRc4OI) | 1,519 | SOURCE_ONLY / PENDING | — |
| #111 | [`zDcF_zPTSYE`](https://www.youtube.com/watch?v=zDcF_zPTSYE) | 923 | **APPROVED** | 14 |
| #112 | [`IEXJKYkJD3o`](https://www.youtube.com/watch?v=IEXJKYkJD3o) | 31 | **APPROVED** | 4 |
| #113 | [`OqfSl1FZhgk`](https://www.youtube.com/watch?v=OqfSl1FZhgk) | 25 | **APPROVED** | 4 |
| #114 | [`etEBw7oWAzw`](https://www.youtube.com/watch?v=etEBw7oWAzw) | 21 | **APPROVED** | 4 |
| #115 | [`Yr2yMyGLsX0`](https://www.youtube.com/watch?v=Yr2yMyGLsX0) | 937 | SOURCE_ONLY / PENDING | — |
| #116 | [`2ATBmntaEaE`](https://www.youtube.com/watch?v=2ATBmntaEaE) | 47 | **APPROVED** | 5 |
| #117 | [`cxotin638g4`](https://www.youtube.com/watch?v=cxotin638g4) | 32 | **APPROVED** | 4 |
| #118 | [`VhKiK706i2I`](https://www.youtube.com/watch?v=VhKiK706i2I) | 29 | **APPROVED** | 5 |
| #119 | [`Uyab8p3HaRE`](https://www.youtube.com/watch?v=Uyab8p3HaRE) | 980 | SOURCE_ONLY / PENDING | — |
| #120 | [`BEUvOl-expQ`](https://www.youtube.com/watch?v=BEUvOl-expQ) | 995 | SOURCE_ONLY / PENDING | — |
| #121 | [`ySbuYun5mNw`](https://www.youtube.com/watch?v=ySbuYun5mNw) | 36 | **APPROVED** | 4 |
| #122 | [`1oT08MK04Jw`](https://www.youtube.com/watch?v=1oT08MK04Jw) | 34 | **APPROVED** | 5 |
| #123 | [`GzrRt18o2Jc`](https://www.youtube.com/watch?v=GzrRt18o2Jc) | 46 | **APPROVED** | 4 |
| #124 | [`iCApyfb2CzI`](https://www.youtube.com/watch?v=iCApyfb2CzI) | 1,539 | SOURCE_ONLY / PENDING | — |
| #125 | [`2q6MwCgIRnY`](https://www.youtube.com/watch?v=2q6MwCgIRnY) | 937 | SOURCE_ONLY / PENDING | — |
| #126 | [`CLlGTnbfQuI`](https://www.youtube.com/watch?v=CLlGTnbfQuI) | 1,171 | SOURCE_ONLY / PENDING | — |
| #127 | [`RokBHHg3UAM`](https://www.youtube.com/watch?v=RokBHHg3UAM) | 1,238 | SOURCE_ONLY / PENDING | — |
| #128 | [`Ctg-Q3haZAE`](https://www.youtube.com/watch?v=Ctg-Q3haZAE) | 844 | SOURCE_ONLY / PENDING | — |
| #129 | [`mZnhZM3Wc88`](https://www.youtube.com/watch?v=mZnhZM3Wc88) | 1,696 | SOURCE_ONLY / PENDING | — |

## 이번 회차 확인한 주요 근거·정정

1. **#101 프리랜서 수입·경비·국민연금·ISA:** 복식부기 의무를 프리랜서 전원에게 **전년도 매출 7,500만원**이라고 단정하는 문장은 정확하지 않다. 국세청 기준은 사업 업종별 **7,500만원/1억5,000만원/3억원** 등으로 구분한다. [국세청 복식부기 자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7669&mi=2229). 프리랜서 약 420만명 규모는 정확한 조사 시점·정의 미확정. 일반 용역사업소득 **3% 원천징수(+통상 지방소득세 0.3%)**가 최종 세율을 뜻하지 않으며, 개인별 종합소득세 결과는 별도.
2. **#102 IRP:** 2026년 소득세법상 퇴직소득에 대한 적격연금 수령 시 과세징수 기준은 최초 10년 **70%**, 11~20년 **60%**, 21년부터 **50%**. 퇴직급여 이연세금과 세액공제 개인 납입금·운용수익의 중도인출세금은 서로 다른 재원으로 분리. [관련 법령](https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1030666693).
3. **#103 손실관리:** 50% 하락했다면 손실 전 금액을 복구하는 데 **100% 상승** 필요(100 → 50 → 100). 분산투자·장기투자도 원금손실 가능.
4. **#104·#108·#112·#113 투자기초:** TDF 목표연도는 은퇴연도에 대한 운용 기준이지 원금보장기간이 아님. 배당 재투자로 주식/펀드 보유좌수가 늘어도 미래 분배금이 증가한다는 보장은 없음. S&P500 한 종목 ETF는 미국 대형주 **기업별 주식 분산**이지만 전세계·채권·현금 자산군분산은 아님. [SEC TDF 안내](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/target-date-funds-investor-bulletin).
5. **#109 ISA 중도인출:** 현금배당을 출금하더라도 ISA 중도인출의 세제상 **납입원금 한도 및 기인출 누계**를 따지므로, 배당금 전액이 언제나 추가 세금 없이 인출 가능하다고 단정할 수 없음. [운용사 공식 안내](https://www.samsungfund.com/etf/pension/isa.do).
6. **#114·#116~#118·#121:** 일반 직장가입자와 지역가입자의 보험료 및 급여 요건 구분. CMA 유형별 상품 리스크, 대출금리 확정액과 불확실한 투자 기대수익 구별. 계좌를 4개 개설하고 50:50 비중을 고정하는 것도 누구에게나 최적의 투자법은 아님. [SEC 고금리부채 상환 안내](https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/pay-credit-cards-or-other-high-interest).
7. **#122 ISA 만기 연금계좌 이전:** 금융사 공식 안내 기준 만기 후 **60일 이내** 적격 이전, **전환금액 10%·최대 300만원 추가 세액공제 *한도***. 이는 실제 세액공제 환급액 300만원을 뜻하지 않으며, 이전 신청과 현금화·해지·재개설 절차가 증권사/계좌 조건에 따라 다름. [한국투자증권 공식 안내](https://securities.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp).
8. **#123 두루누리·푸른씨앗:** 근로자수·월평균보수·신규가입자 자격이 중요한 두루누리의 고용보험·국민연금 보험료 **80% 지원**은 모든 근로자 무조건 지급이 아니다. 푸른씨앗의 조건부 **사용자 부담금 10% 추가적립 지원**은 별개 퇴직기금 제도. [두루누리 공식](https://insurancesupport.or.kr/durunuri/intro.php), [근로복지공단 푸른씨앗 안내](https://mybiz.pay.naver.com/contentsGuide/1188/COMWEL/exposureOrder).
9. **#105 J.L. Collins 저비용 인덱스·4% 인출률:** [저자 공식 2025 개정판](https://jlcollinsnh.com/2025/04/18/a-new-edition-of-the-simple-path-to-wealth/) 확인. 미국 전시장 ETF 약 **3,507종목(2026-08-31 VTI)**은 실증되나 S&P500 1975~2024 연평균 **12.2%**, 상승기간 **82%**, 2002~2022 액티브펀드 초과성과 **17%**는 동일 원표/집계분모 재현이 없어 `QUALIFIED` 처리. 4% 인출은 평생 원금보장이나 모든 국가에 통하는 법칙이 아니다. [VTI 공식](https://advisors.vanguard.com/investments/products/vti/vanguard-total-stock-market-etf), [SPIVA 공식](https://www.spglobal.com/spdji/en/spiva/article/spiva-us-year-end-2024/).
10. **#111 ETF 자동주문:** 이체/매수 약정을 구별하고, ETF 시장가·지정가 주문은 체결가격 또는 체결유무의 위험이 서로 다름. 정액 매수는 가격이 낮을 때 더 많은 좌수를 취득하는 **DCA** 원리지만 수익을 보장하지 않는다. 증권사 앱 메뉴·최유리/최우선 화면은 **영상 원프레임 별도 미대조**. [SEC 시장가·지정가](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders), [정액매수](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging).

## 남은 12편과 연구 우선순위

**이번 회차에서 로스터 순서로 남은 원본 검증 영상:** #106 `sYybI-K5o0o`, #107 `Gk3-ZC9W3vw`, #110 `8tTh8bRc4OI`, #115 `Yr2yMyGLsX0`, #119 `Uyab8p3HaRE`, #120 `BEUvOl-expQ`, #124 `iCApyfb2CzI`, #125 `2q6MwCgIRnY`, #126 `CLlGTnbfQuI`, #127 `RokBHHg3UAM`, #128 `Ctg-Q3haZAE`, #129 `mZnhZM3Wc88`.

이 12편은 자막 미확보 문제가 없다. **주장별 전체 문맥 분석, 공식 법령/발언 당시 세제 및 상품 공시 확인, 산술 재검산, 우려되는 표·계약·원음 OPEN 분리가 완료되기 전까지 교육 V3 승인으로 변경하지 않음.** 특히 #107의 해외배당 ISA 세액정산, #120의 월배당 ETF 실현 수익률, #124의 소득·보험료 정부지원, #128의 과거 ISA 출시 이벤트 등 날짜·계좌별 사실을 현재 사실로 확대하지 않는다.

**다음 실행:** 해당 12편은 장편 영상이므로 로스터 번호 우선 #106·#107부터 차례대로 원문 전체 검토 및 공식근거 검증. 긴 영상에서는 적어도 필요한 모든 *주요 교육 주제*를 주장별로 선정하고, 실제 계약/성과가 없는 부분은 HYPOTHETICAL/QUALIFIED/OPEN으로 표시한다. 기존 장기 연구 완결기록, `main`, 개인 포트폴리오·KIS·Apps Script에 손대지 않는다.

[기계 판독 원장](../data/subtitles/research_progress_batch_101_129_20261018.json) · [29편 인입 출처별 해시](../data/subtitles/registry_101_129_20261018.json).
