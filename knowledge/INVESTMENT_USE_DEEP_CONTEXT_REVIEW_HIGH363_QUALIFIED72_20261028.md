# 박곰희TV #201~260 — 투자영향 HIGH 363건·오분류 후보 72건 원본 문맥 재심사 (2026-10-28)

> **검증 단계:** 원본 SRT SHA/cue 재대조 **363/363**, 이 중 단정 표현 후보 **72/72건 원본 앞뒤 문맥 심층재심사**(72건 중 HIGH 47건). 공식 1차자료는 세제·IRP·금융상품·ETF·연금정책 등의 공통 규칙을 대조했다. **363개 개별 주장의 모든 계약·법령·원표까지 최종 확정한 상태가 아니며, 원본 음성·영상 화면은 미확인이다.** 최종 개인 투자 자동 신호 승인 **0건**.

## 1. 기존 판정과 재심사 단계

- 로스터 #201~260 60편 중 원본 SRT 59편, 원본없는 #204 제외. 투자교육 V3 55편. #219·241·253·254 비투자 범위 제외.
- 전체 기존 주장 896건 중 HIGH 363건: `QUALIFIED` 231, `PRIMARY_CONFIRMED` 103, `HYPOTHETICAL` 25, `CONTRADICTED` 4. 이 HIGH 363개는 모두 비공개 SRT 원본의 **개별 SHA·cue 번호 무결성을 다시 확인**하고 주변 자막을 짧게 추출하여 내부에 보존. 그 자체로 교육 주장의 참·거짓을 입증하지는 않는다.
- 단정 표현을 자동탐지한 조건부 후보 72건은 **모든 건을 원본 SRT ±인접 5~8 cues 범위에서 다시 읽고** 원문에서 무조건 단정을 실제로 했는지, 화자가 반박했는지, 사례인지 분리했다. 72건 중 47건이 투자 영향 HIGH, 25건이 MEDIUM/LOW.
- 출력 원장 `data/subtitles/investment_use_high_363_context_audit_20261028.json`: HIGH 363개 전부의 기존 판정, cue, 원본 SHA, 주제, 투자 활용차단/보류 상태, 72건 재심사 결과 연계. `data/subtitles/investment_use_qualified72_context_adjudication_20261028.json`: 72개 원문맥 재심사 판정·사유.

### 72건 결과

| 재심사 결과 | 건수 | 처리 의미 |
|---|---:|---|
| 원문 단정·수정 검토 | 21 | 영상의 단정 또는 일반화가 실제 존재하며 법령·상품위험 교정 필요 |
| 원표·약관 추가 확인 | 5 | 원본 계약·화면·증권사별 공시 미확보 |
| 조건부 설명 유지 | 12 | 원본 조건부 설명을 유지하고 자동매매 판단 근거로는 제한 |
| 부정·정정 누락 | 14 | 영상에는 부정·반대·정정이 있는데 기존 요약에서 누락 |
| 개인 사례·가정 | 6 | 개인 의견·특정 계좌 사례·복리 가정 분리 |
| 적용시점 재검증 | 2 | 2025 촬영 당시 제도와 2026 현행 제도를 별도로 표시 |
| 원문보다 강한 의역 | 12 | 실제 영상보다 단정적으로 요약; 작성 표현 바로잡기 |
| **합계** | **72** | **원본 맥락 분석 완료 / 개인용 자동 투자 신호 승인 0건** |

**중요:** 위 21건은 *원문상 위험한 단정 또는 핵심 예외가 빠진 설명*이지 모두 단순 오보로 확정된 항목은 아니다. 14+12건은 영상 자체보다 **기존 V3의 서술이 부정확해 투자 활용 시 오해를 낳는 항목**이다. 이들은 우선적으로 기존 서술을 교정하거나 반영 전 차단해야 한다.

## 2. 정확성에 중대한 사례

1. **#205 `EdRzQmddbHE-31` — 기존 V3가 선택권을 누락.** 원본 자막 20,256번 주변에서 사적연금 1,500만원 초과시 종합과세뿐 아니라 **16.5% 분리과세 선택**을 바로 설명한다. 기존 주장 의역 "모두 종합과세"는 원문 일부만 반영. 국세청은 15%(국세 기준) 분리과세 선택을 명시한다. **재심사: 원문 반대·정정 누락, 원장 교정 필요.** https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6608
2. **#213 `2c23EQgwdMA-11` — 원문의 부정표현 누락.** 화자는 공제 때문에 **무조건 분리과세가 유리하다고 볼 수 없다고** 설명한다. 기존 "무조건 분리과세가 낫다" 의역은 반대 의미. 종합소득과 다른 소득·공제의 조합에 따라 선택한다. https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6608
3. **#213 `2c23EQgwdMA-16` — 65세와 11년차 혼동.** 영상은 65세를 이유로 인출한도가 없다고 설명한다. 국세청에 따르면 연금수령한도 소멸의 기준은 **연금수령 11년차 이후**이지 만 65세 자체가 아니다. 연차는 최초 연금수령 가능 과세기간 등의 요건으로 산정한다. https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6449
4. **#238 `574Oi3Jn_KQ-17`·#250 `2bLy034D5LA-15` — 10년 분할수령 절대 규정은 부정확.** 원본은 반드시 10년 이상으로 나눠야 한다고 말하지만 세법상 연금수령한도, 연금수령 연차, 연금외 수령 과세를 구분해야 한다. 연금외 일시인출은 불법이 아니라 세제상 효과가 달라질 수 있는 거래다. https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6449
5. **#250 `2bLy034D5LA-14`, `-19` — IRP 5년 예외 및 일시인출.** 기본적인 만 55세·가입 5년 요건에는 이연퇴직소득 예외가 있고, 55세 후 인출도 일시금과 연금으로 분류해 과세가 달라진다. 원본의 전면 금지·전원 5년 필수 설명은 정정 필요. https://securities.koreainvestment.com/pension/nwSysGuide/EmplRetire.jsp?cmd=A_NW_32000
6. **#250 `2bLy034D5LA-10` — 화자의 실제 수치 이원화.** 원본 자막은 900만원의 16.5%면 148만5천원, 13.2%면 118만8천원이라는 **두 경우를 모두** 설명한다. 기존 "항상 148만5천원" 의역은 과도함. 실제 결정세액에 따른 차이도 존재한다. https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439
7. **#260 `4jwM9YUfq7Q-17` — 발언 의미 역전.** 영상 원본은 특정 SOFR ETF를 **위험자산으로 분류하여 70% 한도**라고 설명한다. 기존 "SOFR ETF는 모두 IRP에서 100% 안전자산" 요약은 원본의 반대 의미. 현재 적용 가능 종목·편입한도는 ETF 종목코드와 퇴직연금 사업자 2026 취급목록을 대조해야 한다. https://securities.koreainvestment.com/pension/nwEtcinfo/Notice.jsp?cmd=A_NW_33030View&num=47729&subFlag=1
8. **#260 `4jwM9YUfq7Q-11` — 신용위험 경시.** 원문은 증권사 발행어음이 위험하지 않다는 취지로 설명한다. 발행어음은 예금보호 대상이 아니며 발행사의 신용위험을 부담한다. 원문대로 투자위험이 없다고 사용할 수 없다. https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/
9. **#258 `WwqijmLsIWg-13` — 출처보다 강한 의역.** 원본은 푸른씨앗 기금의 채권 비중이 높아 '상대적으로 안정적'이라고 설명한다. '원금손실 없이'라고 절대 보장하지 않음. 원래 교육용 요약의 과잉 의역을 고쳐야 한다. 채권 투자도 원금손실 가능. https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19130
10. **#259 `u6TxgssGsas-11` — 국가분산 문맥을 수익보장으로 과장.** 미국과 중국을 둘 다 담는다고 했을 뿐 한쪽은 반드시 수익난다고 말하지 않았다. 두 국가 시장이 함께 하락할 수 있으므로 예측 신호가 아니다. https://www.investor.gov/introduction-investing/getting-started/asset-allocation
11. **#205 `EdRzQmddbHE-33` — 연금자산 이전 손실 0 절대화.** 화자는 이전 프로모션에서 손실이 없다고 직접 설명하지만 일부 자산은 현금화·중도해지 금리·매매 타이밍 손실이 발생할 수 있다. 2024 실물이전 도입 이후에도 이전유형/동일상품 라인업/수관사 조건이 충족돼야 한다. https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=17141
12. **#207 `05JCQ8-v6zc-07` — TR ETF 정책 최신화.** 국내 주식형 TR ETF 등 예외를 구분해야 하며 2025-07-01부터 대상 TR ETF 이자·배당 보유 범위가 변경되었다. 과거 영구 미분배 이연 설명 재사용 금지. https://plusetf.co.kr/customer/notice/detail?n=29585

## 3. HIGH 363건 개인투자 활용 제한 및 추가 증거

- 재검토 우선등급 HIGH **363건**, 그 안에 기존 1차 확인 **103건**, 조건부 **231건**, 미확정 **25건**, 반증 **4건**.
- 이 363개 원장의 **원본 SRT cue 번호가 실 파일에 존재하고 해당 원본 SHA와 등록부가 일치함을 확인**했다. 다만 그 가운데 **47건**의 문맥상 의미심사를 새로 완료했으며, 나머지 316건은 초벌 위험분류/정책 주제 대응/개별 원표 및 원음 대조 대기다. 363건 모두를 `투자에 사용 가능`으로 올리지 않았다.
- 세법·연금 인출: 국세청 2026 시행 제도 및 금융기관 계좌별 과세원천 재대조가 끝나기 전 해당 숫자를 개인 연금 인출액 결정에 직접 사용하지 않는다.
- RP·발행어음·ELB: 원금보장 표현과 실제 발행사 신용·예금보호·보증범위·만기 조건을 분리한다.
- ETF: 상품코드/기초지수/보수/분배원천/매수가능계좌 및 70/100% 취급한도를 개별 상품 원장으로 확인한다.
- 과거 수익률·시장 원표: 정해진 거래일, 배당 재투자, 환율, 세금, 비용, 자산비중 원자료를 확보하지 못하면 개인 투자 지표에 편입하지 않는다.

## 4. 72건 전체 심사표 (기존 주장 의역을 그대로 증거로 간주하지 말 것)

| 영상 / 주장 ID / SRT cue | 원본 문맥 재심사 | 조치 |
|---|---|---|
| #201 `ATMJeH2TyxE-20` / 2804 | 원문 단정·수정 검토 — 원본에서 1,500만원을 넘으면 종합소득세로 들어간다고 단정하는 구간. 사적연금의 분리과세 선택권 누락 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #202 `sUtOQJH-wgc-19` / 2585 | 원표·약관 추가 확인 — 낙인 미도달이면 수익이 난다고 말하지만 만기상환 조건과 발행사 신용위험을 원본 구조별로 확인해야 함 | `HOLD_FOR_INDEPENDENT_CONTRACT_OR_DATA` |
| #202 `sUtOQJH-wgc-21` / 2931 | 조건부 설명 유지 — 배당수익률과 주가/배당 성장의 차이를 질문하고 설명하는 문맥으로 확정 수익 보장은 아님 | `CONDITIONAL_EDUCATION_ONLY` |
| #203 `CFZNyQ8pRUE-01` / 114 | 조건부 설명 유지 — 단순 계좌 개설·예수금 보유에 수수료가 없을 수 있다는 문맥. 상품 운용·거래 수수료는 별도 | `CONDITIONAL_EDUCATION_ONLY` |
| #203 `CFZNyQ8pRUE-07` / 1010 | 조건부 설명 유지 — 연금저축과 IRP에서 편입할 수 있는 투자상품이 다를 수 있다는 조건부 추천 | `CONDITIONAL_EDUCATION_ONLY` |
| #205 `EdRzQmddbHE-31` / 20256 | 부정·정정 누락 — 원본은 종합과세와 16.5% 분리과세 중 선택을 바로 이어 말함. 기존 요약은 한쪽 선택권을 누락 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #205 `EdRzQmddbHE-33` / 20780 | 원문 단정·수정 검토 — 증권사 연금이전 행사에서 손실은 없다고 직접 말함. 상품 매도·이전비용·불이익 점검 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #206 `qabOz6b9hlg-12` / 5737 | 개인 사례·가정 — 특정 상담자 소액 배당계좌의 약 28% 비중에 대한 개인적 안심 평가로 일반 규칙 아님 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #208 `CToQ4bXaP54-13` / 1970 | 조건부 설명 유지 — IRP가 연금저축에 비해 원리금보장형 운용 수단을 섞을 수 있다는 상품범위 설명 | `CONDITIONAL_EDUCATION_ONLY` |
| #211 `Nt2JTbBeDWM-11` / 538 | 적용시점 재검증 — 푸른씨앗 관련 근로자·사업주 지원금을 설명하는 역사적 정책. 지급조건과 현재 대상 재확인 | `RECHECK_CURRENT_EFFECTIVE_DATE` |
| #213 `2c23EQgwdMA-11` / 424 | 부정·정정 누락 — 화자는 종합소득 공제 때문에 무조건 분리과세가 유리하다고 할 수 없다고 명시 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #213 `2c23EQgwdMA-15` / 623 | 원문 단정·수정 검토 — 원본에서 1,500만원을 넘기면 안 된다는 강한 전략 조언. 법정 인출금지로 해석 불가 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #213 `2c23EQgwdMA-16` / 682 | 원문 단정·수정 검토 — 65세여서 한도가 없다고 설명. 연금수령연차 11년 이상이 기준이지 65세 자체가 기준이 아님 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #215 `9NF_P6pWWq4-14` / 374 | 부정·정정 누락 — 미국 배당주 투자 동기는 회사 안정성이라고 설명하며 국내 세제의 장점도 인정함 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #215 `9NF_P6pWWq4-17` / 499 | 원표·약관 추가 확인 — 외국납부세액 배분의 2025~2026 과도기 사례. 정확한 시행일과 적용 세액원장 필요 | `HOLD_FOR_INDEPENDENT_CONTRACT_OR_DATA` |
| #215 `9NF_P6pWWq4-19` / 577 | 원표·약관 추가 확인 — 화자 스스로 자신의 외국세액 공제 해석이라고 전제. 연금외수령 환급 법정 범위 확인 전 사용 금지 | `HOLD_FOR_INDEPENDENT_CONTRACT_OR_DATA` |
| #216 `b5OV0BEle_o-04` / 120 | 원표·약관 추가 확인 — 55세 1만원 연금수령 개시 전략을 제시. 실제 연금수령연차 기산요건과 계좌별 수령 이력 확인 필요 | `HOLD_FOR_INDEPENDENT_CONTRACT_OR_DATA` |
| #216 `b5OV0BEle_o-08` / 316 | 부정·정정 누락 — 퇴직소득세를 당장 납부한다고 말하는 게 아니라 세금 납부를 이연한다고 설명 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #216 `b5OV0BEle_o-12` / 487 | 원문 단정·수정 검토 — 서로 다른 연금소득원천을 구분하지 않고 1,500만원 한도로 합쳐 말하는 맥락이 있어 과세재원 분리 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #216 `b5OV0BEle_o-13` / 526 | 부정·정정 누락 — 수령한도 해제 후 비과세라고 하지 않고 과세대상 운용수익의 연 1,500만원 문제를 설명 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #217 `l0Q-2Ah-ba8-02` / 79 | 조건부 설명 유지 — DC/IRP에서 미운용자금의 원리금보장상품 금리를 비교하라고 권고하는 문맥 | `CONDITIONAL_EDUCATION_ONLY` |
| #217 `l0Q-2Ah-ba8-17` / 451 | 부정·정정 누락 — 1,500만원을 초과해도 이연퇴직소득 등은 별도 처리되어 인출 가능하다고 명시 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #218 `7JqAdMGokqk-07` / 452 | 원문보다 강한 의역 — 리밸런싱이 필요하다고 말하지만 반드시 자주 거래하거나 세금·비용과 무관하다고는 말하지 않음 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #220 `IK_VUi3PUIU-02` / 353 | 부정·정정 누락 — 여러 계좌로 돈이 묶이거나 관리가 복잡해지는 불편함도 인정하고 세제혜택과 비교 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #220 `IK_VUi3PUIU-08` / 601 | 개인 사례·가정 — 추후납부 제도에 관한 고소득자 사례와 사회적 인식의 비유로 보편적 고수익 보증이 아님 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #220 `IK_VUi3PUIU-13` / 801 | 개인 사례·가정 — 특정 가구의 추납 가능성/수령액에 관한 대화. 개인 가입기간·소득기준 원장 없이는 계산 불가 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #221 `6BUwcadctCE-11` / 914 | 원문 단정·수정 검토 — ELB를 예금과 유사하다고 소개하지만 은행 예금자보호와 발행사 신용위험 구별 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #221 `6BUwcadctCE-12` / 978 | 원문 단정·수정 검토 — 퇴직연금 채권 라인업은 우량해서 걱정없다고 강하게 표현. 부도·금리·유동성 위험 배제 불가 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #222 `xrArQWWHkGg-12` / 830 | 원문보다 강한 의역 — 특정 업종 기업의 가치/제품 사례이지 업종 성장과 동일한 주가수익을 약속하는 발언은 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #223 `-4tqIxeViZ4-07` / 347 | 부정·정정 누락 — 1,500만원이 모든 출금 절대 한도가 아니라 특정 사적연금 과세금액이라고 설명 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #225 `loKj0LccKTA-11` / 469 | 원문보다 강한 의역 — 상장·유상증자에서 신주발행을 예시로 설명. 모든 IPO가 구주매출 없는 신주모집이라는 단정은 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #228 `p94_t07GTKA-06` / 73 | 조건부 설명 유지 — 주식 매수는 소액도 가능하므로 큰 목돈은 필수 아니라는 교육 설명 | `CONDITIONAL_EDUCATION_ONLY` |
| #228 `p94_t07GTKA-13` / 257 | 부정·정정 누락 — 마이너스 10%라는 단일 이유만으로 매도해선 안 된다고 경계하는 문맥 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #229 `z1oZOJ3_uIk-04` / 66 | 원문 단정·수정 검토 — 미국 대형지수 ETF에서 추적오차·괴리가 거의 없다고 단정하는 경향. 실제 종목별 지표 확인 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #231 `C7KctGzg-K0-14` / 166 | 조건부 설명 유지 — 일반 국내 상장 ETF의 장내 매도에는 주식 거래세가 붙지 않는다는 제도 설명(상품별 기타 과세 별도) | `CONDITIONAL_EDUCATION_ONLY` |
| #232 `WIXWPJjhF50-11` / 150 | 부정·정정 누락 — 공모주를 무조건 청약하면 함정에 빠질 수 있다고 경고하는 발언 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #234 `iP75FC0Gg0g-04` / 82 | 원문 단정·수정 검토 — 연금 수령 연기를 수급액 증가 관점에서 유리하다고 강조. 수명·건보료·세금 등 종합 판단 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #234 `iP75FC0Gg0g-08` / 199 | 원문 단정·수정 검토 — 장기간 적립식 미국주식 투자 손실위험을 매우 낮게 시사. 통화/구간별 손실 가능성은 존재 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #235 `1Hzf1eiM-t8-18` / 686 | 원문 단정·수정 검토 — 65세 국민연금 수급 및 사적연금 자유 인출 대화. 계좌별 수급개시·인출한도·과세원천 확인 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #238 `574Oi3Jn_KQ-17` / 490 | 원문 단정·수정 검토 — 연금저축을 10년 이상 반드시 분할 수령해야 한다는 절대적 설명. 연금수령한도 산식과 과세방식으로 정정 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #239 `swuHTDAGgeE-06` / 440 | 원문보다 강한 의역 — 환헤지 사례에서 선물환 거래의 계약 및 비용을 설명. 별도의 선불 고정수수료가 반드시 있다는 문장은 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #239 `swuHTDAGgeE-12` / 710 | 개인 사례·가정 — 연금계좌 장기·단기 환율관점에 따라 환헤지 선택 선호를 설명하는 개인적 투자철학 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #239 `swuHTDAGgeE-13` / 743 | 원표·약관 추가 확인 — 환헤지의 연 1~3% 누적 비용 수치를 주장. 시기별 금리차·선물환 포인트·실제 ETF 비용 근거 재검증 필요 | `HOLD_FOR_INDEPENDENT_CONTRACT_OR_DATA` |
| #240 `ATAECPP6MJA-02` / 7 | 조건부 설명 유지 — 일반적 자산배분에서 주식·채권·원자재·유동성 조합을 소개. 모든 TDF에 전부 포함된다는 뜻 아님 | `CONDITIONAL_EDUCATION_ONLY` |
| #242 `Sx2wvsksK9A-10` / 295 | 원문보다 강한 의역 — 배당주 매도 후의 후회를 책/철학의 조언으로 인용하며 모든 수익실현이 후회라는 단언은 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #243 `PshvFd-zwuM-03` / 59 | 조건부 설명 유지 — 배당주를 매도할지 여부에 하나의 정답이 없다고 직접 말함 | `CONDITIONAL_EDUCATION_ONLY` |
| #245 `kU2Cknb8T3I-18` / 711 | 조건부 설명 유지 — 저위험 저수익만으로 인플레이션 뒤 실질자산 증가가 제한될 수 있다는 조건부 설명 | `CONDITIONAL_EDUCATION_ONLY` |
| #247 `qpnZn62UM4U-11` / 190 | 원문 단정·수정 검토 — 일반적 무의결권 우선주의 소액 배당우위를 설명하지만 모든 종류주식/기업에 적용하지 말아야 함 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #247 `qpnZn62UM4U-13` / 220 | 원문보다 강한 의역 — 우선주가 보통주만큼 상승하지 않을 수도 있다고 위험을 설명. 항상 덜 오른다고 말하지 않음 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #248 `YsXYA7Hi7qk-06` / 160 | 개인 사례·가정 — 3억원 목표 및 5% 세전 월분배는 은퇴 생활비의 예시 산술, 분배금의 지속 지급보장은 아님 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #248 `YsXYA7Hi7qk-10` / 475 | 원문보다 강한 의역 — 화자 자신의 세제원천관리용 4계좌 설계를 소개. 법적으로 2개 연금저축계좌를 반드시 개설하라는 규칙 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #249 `7V0PEzRddxs-05` / 211 | 원문보다 강한 의역 — 퇴직연금 IRP 수령의 제도적 확대 논의를 전하는 문맥이지 보유 퇴직금을 모두 즉시 인출하라는 권유 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #249 `7V0PEzRddxs-06` / 244 | 조건부 설명 유지 — 원리금보장형과 실적배당형의 운용 유형을 정확히 구별하는 설명 | `CONDITIONAL_EDUCATION_ONLY` |
| #250 `2bLy034D5LA-03` / 65 | 원문보다 강한 의역 — 조사표의 노후 적정 생활비 약 300만원을 예시로 제시. 모든 가구의 의무 지출액은 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #250 `2bLy034D5LA-10` / 244 | 부정·정정 누락 — 화자가 16.5% 148.5만원과 13.2% 118.8만원 두 공제 시나리오를 모두 설명 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #250 `2bLy034D5LA-14` / 378 | 원문 단정·수정 검토 — 만 55세와 가입 5년 조건만 강조해 이연퇴직소득의 5년 요건 예외를 설명하지 않음 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #250 `2bLy034D5LA-15` / 386 | 원문 단정·수정 검토 — 연금을 최소 10년 이상 분할 수령해야 한다고 직접 설명. 세법상 연금수령한도/연차와 혼동 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #250 `2bLy034D5LA-19` / 480 | 원문 단정·수정 검토 — 55세 후에도 일시금은 전혀 찾지 못한다고 직접 표현. 일시인출 가능성과 연금외 과세 차이 누락 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #250 `2bLy034D5LA-21` / 548 | 원문 단정·수정 검토 — 증권사 IRP는 보통 수수료 무료이므로 증권사가 유리하다고 권고. 온라인 조건·숨은 ETF 비용 검증 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #250 `2bLy034D5LA-23` / 575 | 부정·정정 누락 — 실물이전은 동일 유형 DC→DC/DB→DB/IRP→IRP 한정이라고 명시하여 모든 유형 이전 단정과 다름 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #251 `i9fXr3U-ReA-06` / 196 | 원문 단정·수정 검토 — ISA에서 예금을 피하고 채권부터 사라고 강하게 권유. 채권 신용/금리위험 및 개인자금 수요 고려 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #251 `i9fXr3U-ReA-19` / 1111 | 조건부 설명 유지 — 월배당 ETF의 수익원이 가격변화와 분배금일 수 있다는 설명. 실제 두 수익이 동시 발생한다고 보장하지 않음 | `CONDITIONAL_EDUCATION_ONLY` |
| #252 `H9KS0VTw8Mg-05` / 118 | 원문 단정·수정 검토 — 일반 ISA 초보자에게 배당주부터 시작하라고 강하게 권유. 위험성향별 분산 적합성 확인 필요 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #256 `TBDE82jnEHE-11` / 268 | 부정·정정 누락 — +30% 기계적 매도와 -2% 기계적 보유를 최악의 편향이라 경계하는 인용 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #257 `GqAA7S0uhK0-06` / 229 | 개인 사례·가정 — 특정 장기 연금 투자자의 소액 평가손실을 중요하지 않다고 평가하는 개인적 위험 판단 | `SCENARIO_OR_SPEAKER_OPINION_ONLY` |
| #257 `GqAA7S0uhK0-07` / 252 | 원문 단정·수정 검토 — 산업회복은 느리더라도 지속된다는 방향의 예측이 있으며 2차전지 반등시점은 불확실 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #258 `WwqijmLsIWg-13` / 378 | 원문보다 강한 의역 — 원본은 채권 비중이 높아 상대적으로 안정적이라고 설명. 원금손실이 없다고 단언하는 문구는 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #259 `u6TxgssGsas-07` / 461 | 원문보다 강한 의역 — 기대수익을 높이면 위험이 매우 커질 수 있다는 정성적 설명. 목표수익률에 위험이 정확히 비례한다는 공식 아님 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #259 `u6TxgssGsas-11` / 638 | 원문보다 강한 의역 — 미국과 중국 모두 담는 국가분산 발상을 설명, 어느 한쪽이 반드시 이익이라는 보장은 하지 않음 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |
| #260 `4jwM9YUfq7Q-11` / 541 | 원문 단정·수정 검토 — 증권사 발행어음의 약정금리는 예측 가능하다고 단언. 발행자 신용사건으로 원금손실 가능 | `BLOCK_ABSOLUTE_PENDING_PRIMARY_SOURCE_AND_CANONICAL_CORRECTION` |
| #260 `4jwM9YUfq7Q-15` / 803 | 적용시점 재검증 — 2025 영상 당시 연금계좌에서 달러 RP·발행어음 직접 편입이 제한됨을 설명. 2026 해당 금융사 상품 목록 다시 확인 | `RECHECK_CURRENT_EFFECTIVE_DATE` |
| #260 `4jwM9YUfq7Q-17` / 866 | 부정·정정 누락 — 원본에서는 해당 SOFR ETF가 위험자산으로 분류되어 70%까지라고 설명. 100% 안전자산이라는 의역은 반대 | `NOT_AS_STATED_REWRITE_ORIGINAL_PARAPHRASE` |

## 5. 출처·배포·유지보수
- 직접 확인한 공적 원자료: [국세청 연금소득](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6608), [국세청 연금수령한도](https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6449), [국세청 연금계좌 세액공제](https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439), [고용부 실물이전](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=17141), [한국투자증권 2026 퇴직연금 가능상품](https://securities.koreainvestment.com/pension/nwEtcinfo/Notice.jsp?cmd=A_NW_33030View&num=47729&subFlag=1), [KB증권 예금보호·발행어음](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/), [SEC 분산투자](https://www.investor.gov/introduction-investing/getting-started/asset-allocation).
- 기존 `data/analysis_events`, `data/subtitles/pilots`, V3 및 `main`은 유지한다. 별도 **사용제한 overlay**로 먼저 기록한다. 향후 완전히 검증된 교정만 정식 원장에 승격하고 CI 사전검사를 통과해야 한다.
- 민간 비공개 SRT/ZIP 전체 및 자동생성한 본문맥 원본을 GitHub에 업로드하지 않는다. 공개 파일은 짧은 주장 의역/정정 사유/해시·cue 번호만 사용한다.
