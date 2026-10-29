# 박곰희TV #111~117 집중 재검증 — 원본 SRT 2,016큐·영상별 V3 49건

**작성·검증일:** 2026-10-18 KST  
**범위:** 791개 공식 영상 로스터의 #111~117만. 기존 교육 승인 영상 7편 재검증. 추가 발견 위험진술 1건만 신규 V3 교육 주장으로 기록했으며 승인된 영상 수는 중복 계산하지 않음.  
**연구 브랜치:** `feat/subtitles-incremental-registry-20261009`, `main` 수정 금지.

## 1. 원본 비공개 SRT와 공개 YouTube 자동자막 전문 대조

원본 `101-129.zip` 비공개 파일 477,242바이트, SHA-256 `3e3e7cbbccd95262ba43506ac642ff78d78afeb54de718bf574b4f78cb650951`. 7개 각 SRT 개별 ZIP CRC와 SHA256 모두 기존 영상별 등록부 값과 정확 일치. `full original SRT`의 공개 GitHub 업로드 없음.

| 영상 | 영상 및 원본 ID | 원본 SRT 큐 | 기존 V3 | 재검증 V3 | 원본 파일 SHA256 | 개인/공개 공백제거 전문 문자수 | 전사 대조 |
|---|---|---:|---:|---:|---|---|---|
| #111 | [`zDcF_zPTSYE`](https://www.youtube.com/watch?v=zDcF_zPTSYE) | 923 | 14 | **15** | `fc54c5435784ce95c402d5f30b5027ec328d85b0842dec28ed0e922f2048e99b` | 12,112 / 12,104 | 한국어 전문 SHA **불일치** |
| #112 | [`IEXJKYkJD3o`](https://www.youtube.com/watch?v=IEXJKYkJD3o) | 31 | 4 | 4 | `53cc8bcf900146e6b79477c10294fc5f5a4a59655cf4dc8ce3a8c4f5bad8e0db` | 427 / 427 | 일치 |
| #113 | [`OqfSl1FZhgk`](https://www.youtube.com/watch?v=OqfSl1FZhgk) | 25 | 4 | 4 | `9e498c1d5c1b601ad7f3765d90cf7dd89f21046e2847a08b11b80543aa83838f` | 355 / 355 | 일치 |
| #114 | [`etEBw7oWAzw`](https://www.youtube.com/watch?v=etEBw7oWAzw) | 21 | 4 | 4 | `8863078711508ac61cc57ede59a40a3a75491fd241def6ec4fb412841ab68eb5` | 296 / 296 | 일치 |
| #115 | [`Yr2yMyGLsX0`](https://www.youtube.com/watch?v=Yr2yMyGLsX0) | 937 | 13 | 13 | `3863a2d973539dade7758b4c34d14c2e2ed8abeff240ffaeb3c68b3820ef3bb9` | 12,204 / 12,190 | 한국어 전문 SHA **불일치** |
| #116 | [`2ATBmntaEaE`](https://www.youtube.com/watch?v=2ATBmntaEaE) | 47 | 5 | 5 | `7672a298fb706e0de8ff34f0b071e7263d70c9de400060d3e0567d9a305e0d33` | 661 / 661 | 일치 |
| #117 | [`cxotin638g4`](https://www.youtube.com/watch?v=cxotin638g4) | 32 | 4 | 4 | `26462dc3c33253ca95ad498ae67d7c0f590c46fb99d9e912584aee4673eeda92` | 460 한국어 / 1,064 **영어** | **언어 불일치: 비교불가** |
| **합계** | **7편** | **2,016** | **48** | **49** | **개별 원본 7/7 SHA 통과** | | **한국어 일치 4편, 불일치 2편, 언어다름 1편** |

공백제거 전문 개별 증빙 SHA:
- #111 원본 `d209c8973d4700307d65a0dcb0607f89d93bcf10e78e563b104a0f8113b637ef`, 공개 `b066a5edd4f44d70c42408a1c6739dad83c5c6bcddf84b6689c5fd3515cf2326`.
- #112 양쪽 `0cf2439fd5e397185b36ee94588b5e1d37e52158b6dcabac8cc2027402d4b956`.
- #113 양쪽 `42ef8ba1f88aee39021c23789cbd6b86acdd9a50c4fd476fd6a97a629cb9ef97`.
- #114 양쪽 `813dbbc4ef1ca8d341c30434d35c645955f0cef4d0c4dfa5aa1cbfe132579656`.
- #115 원본 `1788d5c0dc1a65c9b622c11e342e29df11da4948ef98b3473a34f6ddd9faa66e`, 공개 `6f39a3266143635b2e9c0952a6b5d4bde53373467e24606ef03bcf2a7a71dd44`.
- #116 양쪽 `71fdc3ae07b8c22e85046e2362c43ca1f8f3c053685c088fe2015ae4a597d01a`.
- #117 원본 한국어 `d0c5971717c7b9d6c3729178e61641a23893eda9c271dd0f029c013afa060ab9`; YouTube 페이지는 `hl=ko&cc_lang_pref=ko` 설정 시도에도 영어 번역전사 `b91cd1d9b3cddd14febfdcfd0b25a82d00db4ffeb806be2d2e6868f08b58e493`만 응답해 두 언어의 문자열 SHA 비교는 의미 없음.

**원본 출처의 충실도 한계:** 사용자 업로드 원본의 해시 유효성은 확인되었으나, YouTube에서 자동자막 추출 방식이 달라 #111/#115 글자가 약간 다르며 원본 프레임/원음을 독립 재생하지 않았다. #117의 한국어/영어 **다언어 비교 불가**는 한국어 두 전사 간 불일치 판정이 아님. 동영상의 실제 밀리초 발화·투자 계좌주체·증권사 앱 버전 등은 인증되지 않음.

## 2. 중대한 위험진술 정정: #111 신규 V3 **CONTRADICTED** 교육 주장 1건

기존 #111 14건에서 **15건**. 추가된 `zDcF_zPTSYE-15`는 원본 자동자막 **cue555 시작 00:18:15.480** (인접 cue554~558): 진행자는 매매에서 시장가 주문을 내면 비싸더라도 사실상 **'무조건' 체결**되는 취지로 설명한다. 기초 개념을 단순화한 표현이지만 모든 수량이 항상 체결되는 법적/시장 메커니즘은 아니다.

**공식 근거:** [한국거래소 주문 유형 원문](https://global.krx.co.kr/contents/GLB/06/0602/0602010201/GLB0602010201T2.jsp), [한국투자증권 주문 도움말](https://securities.koreainvestment.com/pro_help/8202.html):
- 시장가: 주문가격 미지정, 현재 반대편 주문호가를 가능한 신속하게 소진. 가격과 수량 전량 체결 보장 **없음**. 상대호가 부재·거래 정지·세션/잔량/가격제한 등 조건으로 전량 미체결 가능.
- 최유리지정가: **매수인 경우 반대편 최우선 매도호가**로 최초 가격을 지정. 그 가격까지의 체결만 기대; 호가 부족하면 미체결 잔량 가능.
- 최우선지정가: **매수인 경우 같은 매수편 최우선 매수호가**로 주문가 지정. 순서 대기/미체결 가능.
- 신규 위험주장은 **CONTRADICTED**로 정식 보존. 그 외 14개 기존 안전한 교육 결론 유지. 특정 자동매수 서비스 UI가 보장 가격/주문가능 시간 규칙을 어떻게 구현하는지는 원본 실제 화면 및 최신 증권사 약관 확인 전 확정하지 않음.

## 3. #115 ISA 역사·통계 공식 원본과 대조

- **2016년 3월 14일 출범:** [대한민국 정책브리핑 2016-02-12 금융위원회 ISA 활성화 브리핑](https://www.korea.kr/news/policyNewsView.do?newsId=156109166) 원문은 ISA 출시일을 2016-03-14로 명시한다. 영상 `Yr2yMyGLsX0-02`을 **QUALIFIED → PRIMARY_CONFIRMED**로 변경. 단, 은행 일임형 ISA는 등록 후 3월 말 별도 예정.
- **2026년 1월 말 전체 가입규모:** [2026-02-26 금융투자협회 발표의 뉴시스 원문 전재](https://www.newsis.com/view/NISX20260226_0003527439)는 **807만명**, **54조7천억원**, 중개형 가입자 **701만명/전체86.9%**, 중개형 자산 **37조7천억원/전체68.8%**. 영상 약806만/54조는 반올림에 가까운 **근사 표현**. 금투협 **독립 월별 기초 표 파일**과 영상의 원본 데이터 화면은 직접 대조하지 않았으므로 정확한 기준월·집계방식은 개별 재확인 필요.
- **투자중개형 ISA 자산구성:** 동일 2026-02-26 금투협 발표의 동시기 복수 보도에서 **ETF 46.8%**, **주식 34.2%**. 영상의 대략 46%/34%와 가깝다. 주의: 이 분모는 **투자중개형 계좌의 운용액**이며 신탁형·일임형 포함 모든 ISA 자산 평균치가 아니다.
- **중개형 '예금 8.7%'는 미확정:** 영상 자동 SRT 00:24:13부터 8.7%라는 언급이 있지만, 동일 KOFIA 월별 *중개형의 상품분류* 원표·예수금/RP/예금성 분류 정의를 직접 확보하지 못했다. **투자중개형 ISA에서 은행 예금을 직접 매매할 수 있다**는 결론으로 단정 금지.
- 2026년 3월 ISA 10주년 이벤트는 당시 조건부 이벤트이며 현재 2026년 10월에도 신청할 수 있는 보장 혜택으로 쓰지 않는다. ISA 이전 시 1인1계좌·이전접수/원계좌 말소 및 세제연속성 조건은 증권사에 확인.

## 4. #112~114·#116~117의 정확한 교육 범위

**#112 배당 재투자 (4건):** 기업 이익의 내부재투자가 적정수익률을 거두면 가치성장을 촉진할 수 있다. 주가 상승과 기업가치가 언제나 1:1로 비례하는 것은 아님. 배당금 재투자는 더 많은 주식을 매수할 기회이나 다음 배당액/원금/ETF의 실적이 보장되는 것은 아님. [SEC 펀드 기초정보](https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-funds-etfs/mutual-funds).

**#113 S&P500 집중과 분산 (4건):** 단일 미국 대형주 ETF라도 수백 개 기업에 나눠 투자하지만 **단일 미국 국가·주식 자산군·상위 메가캡/업종 집중**은 남아 있음. 월정액 정기매수의 저가 좌수 증가(DCA)는 수학적 특성이지 손실방지나 수익률 우월성 보장이 아님. [S&P DJI S&P500](https://www.spglobal.com/spdji/en/indices/equity/sp-500/), [SEC DCA](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging).

**#114 4대보험 (4건):** 국민연금·건강보험·고용보험·산재보험은 재원과 지급요건이 다름. 산재보험은 통상 사업주 부담, 회사와 근로자의 보험료 분담도 각 제도/가입형태별로 다르며 모든 근로자가 실업급여를 자동 수령한다는 주장이 아님. [근로복지공단](https://www.comwel.or.kr/comwel/main.jsp) / [국민연금공단](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0095M0.do?menuId=MN24001131).

**#116 CMA·ISA·연금계좌·IRP (5건):** [메리츠증권 2026 MMW CMA 직접 공시](https://www.imeritz.com/meritzcma/CmaMmw.do)는 한국증권금융 예수금 등 랩 일임형, **실적배당**, 랩 수수료 연 **0.05%**, **예금자보호 미적용**, **원금손실 가능**을 명시한다. 영상의 `MMW CMA/발행어음형 CMA에 비상금을 넣으면 은행보다 유리하다`는 설명은 **자금안전성·은행예금자보호의 대체**로 해석하면 위험. 미국 ETF의 직접 해외상장 종목은 국내 중개형 ISA에서 원칙적으로 매입가능한 국내상장 해외노출 ETF와 구분. 연금저축 50:50, IRP TDF는 선택적 예시로 위험성향·수수료·인출조건에 따라 조정. 투자성과 보장하지 않음.

**#117 채무와 투자 (4건):** 순수 비교로 대출금리와 투자 기대수익률을 비교할 수 있지만 확정적인 이자비용과 불확실한 주식 기대수익을 같은 무위험 숫자로 취급하면 안 된다. 영상의 50:50 분할은 **개인적 심리절충**이며 보편 최적화 수치가 아니다. 높은 이자 부채부터 상환하는 방향과 비상금 유지가 유리할 수 있음. [SEC 부채 상환 투자교육](https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/pay-credit-cards-or-other-high-interest). 개인 실제 부채 잔액·금리·세후 실현수익 데이터는 검증 안 됨.

## 5. 주장 단위 V3 원장과 증거게이트

| # | 원본 실측 큐 및 주장 기록 | 정식 V3 승인 기록 |
|---:|---|---|
| 111 | [pilot](../data/subtitles/pilots/zDcF_zPTSYE.json) | [canonical](../data/analysis_events/zDcF_zPTSYE.json) |
| 112 | [pilot](../data/subtitles/pilots/IEXJKYkJD3o.json) | [canonical](../data/analysis_events/IEXJKYkJD3o.json) |
| 113 | [pilot](../data/subtitles/pilots/OqfSl1FZhgk.json) | [canonical](../data/analysis_events/OqfSl1FZhgk.json) |
| 114 | [pilot](../data/subtitles/pilots/etEBw7oWAzw.json) | [canonical](../data/analysis_events/etEBw7oWAzw.json) |
| 115 | [pilot](../data/subtitles/pilots/Yr2yMyGLsX0.json) | [canonical](../data/analysis_events/Yr2yMyGLsX0.json) |
| 116 | [pilot](../data/subtitles/pilots/2ATBmntaEaE.json) | [canonical](../data/analysis_events/2ATBmntaEaE.json) |
| 117 | [pilot](../data/subtitles/pilots/cxotin638g4.json) | [canonical](../data/analysis_events/cxotin638g4.json) |

각 JSON에 49개 교육주장의 ID, 원본 큐 번호·영상 시작 초단위, 수정판정·근거 URI·적용조건 및 공개 전문 비교 SHA를 기록했다. [배치 등록부](../data/subtitles/registry_101_129_20261018.json), [진행 원장](../data/subtitles/research_progress_batch_101_129_20261018.json)에도 동일 계수로 반영.

- 본 범위 7편에 기존 교육 주장 **48건 + 정정에 따른 누락된 #111 시장가 체결 주장 1건 = 49건**.
- 전체 누적 승인 영상 **129편(변경 0)**, 누적 교육주장 **2,095 → 2,096(+1)**.
- 101~129 배치 승인 교육주장 **292 → 293(+1)**.
- 구 추가검증 원장 **38건 중 해결14/OPEN24 유지**, 본 7편 자막/원표 제약을 legacy OPEN24에 임의 결합·차감하지 않음.
- 개인 투자계좌, 원본 SRT, 2016~2026 통계 원표 원본의 허가 없는 재배포, `main` 브랜치, 다른 편수(#118~129)의 연구 기록은 건드리지 않음.

**잔여 직접검증:** #115 중개형 ISA `예금성 8.7%` 원표 분류 및 영상 원도표 픽셀 비교, #111/#115 자동자막 상이 부분 한국어 음성 확인, #117 동일 영상 한국어 공개 전사 원문 취득(현재 영어 번역만 받음), 실제 증권사별 ETF 자동매수 UI/계좌 설정 확인. 이들은 교육적 조건부 승인 상태를 전면 취소하는 게 아니라 해당 주장 정확 적용범위를 제한하는 요인이다.
