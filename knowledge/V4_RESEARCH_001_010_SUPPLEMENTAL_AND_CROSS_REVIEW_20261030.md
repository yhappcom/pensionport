# 박곰희TV #1~#10 V4 추가 검증·정량 개정·누적 재감사

기준일: 2026-10-30. **기존 V3/V4 역사 기록은 변경하지 않고 새 개정 오버레이를 추가했다.** 본 연구는 공식 법령·운용사 자료 및 저장된 V3/V4의 근거/주장 ID에 기반한 재감사이며, 이번 회차에 사적 원본 ZIP 전체 바이트의 SHA-256을 다시 산출하거나 원음/프레임을 독립 전수 검증하지 않았다.

## 범위와 중복 집계 방지

- 총 **10편, 기존 V3 122개 주장**(1–5편 62개, 6–10편 60개), 신규 V3 승인 0개.
- 이전 V4 '핵심 근거/수학 재검토' 표시 **69건**(1–5편 34개, 6–10편 35개), V3 판정만 유지된 주장 **53건**. 이 회차는 122개 모두를 기존 원장과 대조해 누락·신규 승인·반박 전파를 감사했지만, **122건을 모두 원본/공식자료에 새로 독립 검증한 것으로 계수하지 않는다.**
- 기존 #1–#5 영상별 외부 OPEN 합계 **12건**인데 기존 최종 종합 기록은 **13건**으로 기재되어 있어 미조정 `OPEN_COUNT_RECONCILIATION=1`로 남겼다. #6–#10 OPEN 합계 14건. 이를 합쳐 26개 '영상별 분류 OPEN'이며, 13이라는 과거 종합 수치를 임의로 12로 덮어쓰지 않는다.
- 기존 1~10 정량모형과 ID/역사 주장 원장은 그대로 유지. 이번에 새 **6개 시나리오**를 추가하여 법적/경제적 민감도만 계산.

## #10 — 연금저축 세후 모형 실질 보완

2026-10-01 시행 소득세법 시행령 제40조의3: (1) 입증된 과세제외금액 (2) 이연퇴직소득 (3) 공제받은 납입원금·운용수익 등 과세재원의 법정 인출순서를 적용한다. 공제받지 않은 원금의 과세제외는 제201조의10에 따른 증빙 확인 시점도 중요하다. 적격 연금수령은 제40조의2의 55세, 가입기간/퇴직소득 예외, 수령한도 조건을 각각 충족해야 한다.

- 사례 A: 1,800만원(증빙된 미공제 원금 1,000만원 + 공제 원금 500만원 + 운용수익 300만원) 중 1,200만원 인출 시, 다른 우선 재원 없음 조건에 한하여 1,000만원 과세제외 + 200만원 과세재원. 해당 200만원에 대한 가상 세율 5.5%=11만원 / 16.5%=33만원으로 민감도 분리. 두 세율이 동일 지급에 자동 적용된다는 의미는 아니다.
- 사례 B: 1,000만원 원금 15년/연 5% = **2,078만 9,282원**(가상). 원금 전액이 미공제이면 과세재원은 수익 약 1,078만 9,282원, 원금 전액이 공제되었으면 과세재원이 원금+수익 약 2,078만 9,282원으로 달라진다. 같은 5.5% 가상 세율을 적용하면 각각 **2,019만 5,871원**, **1,964만 5,871원**으로 55만원 차이가 난다. **가상 일시청산에 실제 적격 연금 5.5%를 적용할 수 있다는 뜻이 아니다.** 소득/과세연도/거주자/과세·세액공제 내역, 연금소득 합산·분리 과세를 개별 판단해야 한다.
- 원래 `V4_010_ORDINARY_PENSION_TAX`는 **전체 원금을 과세제외한 구조에만 맞는 단순 민감도**다. 범용 '일반계좌 15.4% vs 연금 5.5%' 비교로 재사용하지 않는다. 기존 `VKr060rIirM-05`의 `CONTRADICTED`는 유지한다.

근거: [시행령 제40조의3](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1029964673), [시행령 제40조의2](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1032953507), [국세청 원천징수 세율 분류](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7703&mi=2415).

## #6 — 자녀 증여 정기금 평가 검증

- 월 18만 9천원×120개월 명목 **2,268만원**. 연 3%로 각 연도 말 226.8만원 지급된다고 가정하는 현재가치는 약 **1,934만 6,500원**이고, 연초 지급은 약 **1,992만 6,895원**이다.
- 경제학적 월지급 현금흐름 PV(연 3% 유효율로 월단위 할인)는 약 **1,961만 1,095원**(매월 말). **이는 법정 유기정기금 평가방법을 대체하지 않는다.** 실제 권리의 지급계약 조항과 받는 정기금의 연도별 지급권리가 우선한다.
- 시행령 제62조의 일시금 평가 하한을 별도 반영: 해지 시 지급받을 수 있는 일시금이 2,100만원이면, 법적 사실관계가 일치할 경우 해당 금액이 단순 PV보다 커진다. 과거 10년간 직계존속 증여공제 500만원 사용 시 기본 남은 한도는 1,500만원에 불과하다. 부모별 2,000만원 중복공제가 아니다.
- 계약 원본, 철회/해지/해제 가능성, 권리 귀속일, 기존 증여이력, 수증자 거주·연령, 혼인·출산 특례 적용 연도 없이는 '비과세 확정' 금지. 

근거: [시행령 제62조](https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1032487389), [시행규칙 제19조의2 연 3%](https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0019&lsiSeq=284609&urlMode=lsScJoRltInfoR), [국세청 10년 증여재산공제](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7960&mi=2762).

## #8 + #9 — 같은 원화 원금·기간 비교

새 통합 모형은 원금 1,000만원/1년, 엔화 등락 -10/0/+10%를 동일하게 가정한다. 직접 엔화 환전은 양방향 가상 스프레드 각 1.75%, 90% 우대 시 각 0.175%를 적용한다. ETF는 엔화 단기채 +1%, 공시 연 0.19%, **가상** 추가 추적차이 0.30%와 양방향 거래마찰 각 0.15%를 설정한다.

| 엔화 등락 | 현찰/외화 직접 환전 (우대 없음) | 직접 환전 (가상 90% 우대) | 엔화 ETF (가상 비용 포함) |
|---|---:|---:|---:|
| -10% | 869.0만원 | 896.9만원 | 901.8만원 |
| 0% | 965.6만원 | 996.5만원 | 1002.0만원 |
| 10% | 1062.2만원 | 1096.2만원 | 1102.2만원 |

**모두 세전·가정값**이며 은행 실제 호가나 PLUS 489000의 실현수익률이 아니다. PLUS 공시의 0.19%는 증권사 거래비용 등 전체 비용이 아니며 실제 NAV 추적차이에는 일부 비용이 반영되므로 **과거 NAV/실제 ETF 성과 계산에서 보수 중복 차감을 금한다.** 일본 상장 달러 기초자산 ETF는 엔화 표시 매매라는 이유만으로 순수 엔화 상승 베팅이 되지 않는다.

근거: [PLUS 489000 운용사 공시](https://www.plusetf.co.kr/product/detail?n=006369). 직접 현찰환전 vs 은행 외화예금/온라인 매매는 별도 상품·수수료·세법이므로 하나로 일반화하지 않는다.

## #1~#10 개별 영상 재감사 요약

| 영상 | V3 주장 | 이전 V4 핵심 재검토 / 기존 판정 유지 | 영상별 OPEN | 중대 확인·활용 제한 |
|---|---:|---|---:|---|
| #1 | 23 | 9 / 14 | 3 | NPS projection and pension excluded-basis not equivalent to account balance; monthly 7% effective-vs-nominal convention and source diagram OPEN |
| #2 | 9 | 7 / 2 | 2 | CMA issuer/insurance protection depends on contract; 50:50 portfolio preference not optimum; tax credit is base not automatic refund |
| #3 | 15 | 9 / 6 | 3 | IRP pension payment start depends on statutory receipt years; 2e8/4.5m monthly pacing differs from annual salary; covered-call distributions are not risk-free |
| #4 | 6 | 5 / 1 | 2 | 40% drawdown needs 66.67% recovery; historical current-account/GDP near 20% unsupported; issuer insolvency risk precludes blind holding |
| #5 | 9 | 4 / 5 | 2 | 50/40/10 nominal 1m monthly requires actual surplus after debt; TDF target year not insured return; employee-stock concentration risk |
| #6 | 14 | 6 / 8 | 3 | Legally conditioned annuity rights and 3% PV; contract cancellation floor can exceed 20m; past 10y gift deductions lower remaining allowance |
| #7 | 14 | 8 / 6 | 3 | 4e8 to 7e8 is not an investment IRR absent deposits/withdrawals; leverage and source-selection risk; original individual statements unavailable |
| #8 | 12 | 7 / 5 | 3 | 489000 0.19% stated not all-in; swap risks, hedging and Japanese-listed USD equity cross-rate; missing 2 ASR cues |
| #9 | 12 | 6 / 6 | 2 | Direct JPY spread/90% preference examples not actual bank quote; Japanese currency cash gain tax ruling not ETF blanket benefit |
| #10 | 8 | 8 / 0 | 3 | Credited/noncredited principal and withdrawal order, annuity eligibility and ordinary-account tax classes; CONTRADICTED broad tax claim; original 34-cue SRT unavailable |

**추가 확인 결과:** #1 적립 시점·원금과 계좌평가액 불일치, #2 CMA 안전성 표현, #3 IRP 수령 연차와 월납입 투자기간, #4 미확인 거시 비율, #5 예산·TDF 전제가 기존 제한과 일치하는지 다시 감사했다. #7 개인 사례는 수익률 증명이 아닌 일화, #8은 공개 ASR 두 구간 누락, #10은 사적 34-cue 원본 SRT 해시 부재로 유지한다.

## 판정과 후속 게이트

- **완료:** 법정 구조 정정 모형 #10, 계약 하한 민감도 #6, 동일 비용기준 엔화 세전 비교 #8/#9, 122개 주장 ID·이전 V4 검토 범위·OPEN·승인 상태에 대한 레지스트리 전수 정합성 검사.
- **미완료/OPEN:** 122개 원본 전수 **새로운 독립 재검증**; #10 실제 세액공제 이력 및 개인 연금수령 자격; #6 실제 계약·기존 증여; #8/#9 특정 시점 거래호가·현지 과세; #7 개인 실제 계좌 증거; #1~#5 OPEN 수 불일치 확인. 실제 L3/L4 승인 **0건**.
- 신규 자동 CI는 가상 모형 수학과 원장 연결·반박 주장 제한을 검사한다. 세법·상품의 진실과 개인 투자 적합성을 전부 자동 인증하지는 않는다. 이전 모형 결과를 수정하거나 과거 승인 수를 늘리지 않는다.
