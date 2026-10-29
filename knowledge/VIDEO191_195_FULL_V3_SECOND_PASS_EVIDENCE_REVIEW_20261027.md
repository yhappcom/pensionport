# 박곰희TV #191~195 — 비공개 원본 SRT·공식자료 V3 2차 주장별 검증 (2026-10-27)

**배치 결과: 원본 5편 확인, 그중 #191 공공 금융서비스 이용 홍보 Shorts는 비교육 이벤트로 제외, 교육 4편 정식 V3 87개 주장 검증.** 전체 원본 SRT **3,264 cues · 254,723 bytes**의 SHA256, 시작시각, cue 번호를 원표와 대조했다. 교육 주장 분류 **PRIMARY_CONFIRMED 33 / QUALIFIED 44 / CONTRADICTED 1 / HYPOTHETICAL 8 / SPEAKER_OPINION 1**. 개인 성과·기기 화면·2025 역사 금리·원음/화면의 2차 인증이 없다는 제한을 보존한다.

## 1. 사용자 원본·프라이버시·교육 제외

- 원본 개인제공 ZIP: `101-200.zip`, Google Drive `박곰희TV_SRT_원본보관함`, archive SHA256 `ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e`, 2,273,410 bytes. 다섯 원본 파일 SHA256/bytes/cue 번호를 `data/subtitles/registry_191_195_20261027.json` 및 해시가 독립적으로 고정된 `scripts/audit_subtitle_review_gate.py`에서 검증. 원본 SRT/ZIP 전문은 GitHub에 게시하지 않는다.
- **#191 `h1VSdD5XeO4`, 20 cues, 1분16초:** 서울시/KB·우리·신한 은행의 청년 금융타임머신 5년 예상 자산 조회 앱 소개·사용법 안내이다. 2025-08-29 [KB국민은행 첫 당사자 보도자료](https://omoney.kbstar.com/quics?articleClass=&articleId=140742&bbsMode=view&boardId=647&compId=b031438&page=C017648&searchCondition=title&searchStr=&viewPage=1)에서 서비스 존재·미래 추정치를 확인했다. 이는 실제 미래 자산 수익이 보장되거나 투자방법을 검증하는 교육이 **아니므로 별도 비교육 홍보영상으로 분류**. 원본 출처만 보존하며 pilot/canonical 교육 승인 또는 0건짜리 실적에 추가하지 않는다.
- **#192~195 네 편:** 원본 비공개 자동한국어 자막 전문을 읽었으나 개인 실제 금융계좌·2025년 화면의 주문 처리·녹음 음원·정지화면·공개 한국어 자막 본문의 독립 2차 대조는 수행하지 않았음. V3 승인 의미는 해당 **주장들의 공식증빙/조건/정정 및 교육 활용 범위를 확정**한 것으로 전 영상 발언의 진위를 보증하지 않는다.

## 2. 시급한 법정·수치 정정 및 제한

1. **#192 ISA 만기 → 연금계좌:** 적격 중개형 ISA의 세제상 3년 최소유지 조건과 금융사 계약 만기일·신규 ISA 재가입 가능 시점을 구분한다. ISA 손익통산은 과세대상 손익 범위 내에서만 적용하고 서민형 비과세 한도 **400만원**, 일반형 **200만원**, 초과 순수익 **9.9% 분리과세**는 영상 당시 기준으로 제시. [ISA 상품 안내](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView). ISA 만기금은 계약기간 만료일부터 **60일 이내** 적격 연금계좌로 전환하고 금융사에 전환용 납입임을 확인해야 한다. **추가 세액공제 300만원이란 환급액이 아닌 공제대상 납입금 한도**임. 개인 화면의 실제 출금·연금전환 전체 완료는 원본 SRT만으로 입증 불가. [한국투자증권 전환 실무안내](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) / [소득세법 시행령 제118조의2](https://law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=126655).
2. **#193 연금부자수업 EP.01:** 장기투자·정기적 소액적립·리츠 간접투자 원리는 조건부 유효하나, 화자의 부모님 연금 계좌 성과는 증빙되지 않은 개인 사례이며 리츠 월분배를 원금보장으로 해석 불가. 특히 **푸른씨앗 대상은 2025년 30인 이하 → 2026.7부터 50인 미만 → 2027.1부터 100인 미만**으로 변경/예정되어 역사 시점으로 명시. [고용노동부 2026-03-25 발표](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19130).
3. **#194 주택연금:** 2025 영상은 주택 담보 55세/부부합산 공시가격 12억원 이하 등 기본요건을 설명한다. **가입가능성 판정의 공시가격**과 **월지급금 산정의 시세·감정평가액**은 다르다. 2026-03-01 신규신청자는 일반형 **초기보증료 1.5%→1.0%, 연보증료 0.75%→0.95%**로 변경되었으며, 기존 2025 월지급금/예시 금액은 현재 신청자 수령액으로 재사용 금지. [금융위원회 개선](https://www.fsc.go.kr/po010106/86211). **한 가지 직접 반증:** #194 cue **1065 / 00:32:43.960**, 4억원짜리 집이므로 혼합방식에서 집값의 50%=2억원을 곧바로 인출할 수 있다는 산술은 틀림. 50% 일반 인출한도는 주택시가가 아닌 **공사가 산정한 대출한도** 기준이다. [주금공 법규와 인출한도](https://www.hf.go.kr/ko/sub03/sub03_01_01_04.do). 정액형의 물가 구매력 하락은 정기증가형/초기증액형 등 영상에서 뒤에 소개된 다른 지급유형까지 부정하는 발언으로 오인하지 않도록 정정.
4. **#195 연금 세액공제 이월:** `소득세법 시행령 제118조의3`는 전년도 등의 **세액공제 받지 않은 적격 원금**을 본인 신청과 법정 요건에 따라 **당해 연도 납입액으로 전환**하는 특례. [법령](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167), [국세청 2022 사전답변](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000515824&wnkey=faec7a02-7c00-4925-b0c4-40c16397f6db). ISA 만기 연금전환의 **300만원은 추가 공제대상 납입액 한도이지 세금 환급액 300만원이 아니다.** 1억원 전환 후 가정상 미공제액 9700만원을 매년 연금저축 600만원씩 적용하면 16.17년이라는 **산술적 시나리오**일 뿐 장래 매년 공제 실현을 보장하지 않는다. 개인의 결정세액 0이면 공제 한도가 있어도 실제 환급은 없을 수 있다.

## 3. 편별 원본·판정 결과

| # | 분류 | 원본 cue | 교육 주장 | 1차 확인 | 조건부 | 반증 | 가정 | 의견 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| #191 | 비교육 서비스 안내 | 20 | 0 | 0 | 0 | 0 | 0 | 0 |
| #192 | 교육 | 784 | 20 | 8 | 12 | 0 | 0 | 0 |
| #193 | 교육 | 868 | 18 | 5 | 8 | 0 | 4 | 1 |
| #194 | 교육 | 1258 | 29 | 14 | 11 | 1 | 3 | 0 |
| #195 | 교육 | 334 | 20 | 6 | 13 | 0 | 1 | 0 |
| **합계** | **원본 5편 / V3 4편** | **3,264** | **87** | **33** | **44** | **1** | **8** | **1** |

## 4. 전체 87건 주장별 원본 SRT cue·시간코드·공식 근거

다음은 원본 SRT 전문 복제·자막 자체 공개가 아니라 투자교육 주장의 최소한 의역과 출처·범위이다. 각 `claim_id`는 `data/subtitles/pilots/<video_id>.json#claims[*].verification_evidence` 및 `data/analysis_events/<video_id>.json#core_claims`의 구조화 기록과 동일. 출처는 일반 제도/상품설명 확인에만 활용했으며 투자자 개인 계좌 실제 거래·세액공제 신고 확정을 의미하지 않는다.

### #192 ISA 만기해지·연금저축 전환 실제 절차 — 의무가입·손익통산·서민형 절세 — 20건

| claim_id / cue | 시간 | 판정 | 영상 요지 | 독립 검증·정정·한계 | 공식자료 |
|---|---|---|---|---|---|
| `iy7_HMMSLGc-01` / 57 | 00:01:43.640 | PRIMARY_CONFIRMED | ISA의 세제혜택을 위해 최소 의무가입기간 3년을 지켜야 한다 | 일반적 ISA 세제우대는 계약일로부터 3년 최소 보유기간을 전제로 한다. 계약만기일과 세제혜택 충족일은 다르다. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-02` / 63 | 00:01:53.880 | PRIMARY_CONFIRMED | ISA의 선택한 계약만기와 의무가입기간 3년을 구별한다 | 세제상 3년 기준과 회사에 등록한 만기계약일은 별개. 만기연장·계약 해지/재가입은 금융회사 약관과 계좌상태 확인. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-03` / 99 | 00:02:59.519 | QUALIFIED | ISA의 자산을 현물로 옮기면 언제나 모든 세제혜택이 소멸한다 | ISA 안에서의 보유자산 이전·계좌 외 인출·적격 중도인출·해지는 다른 행위다. 영상 사례는 만기 청산을 위한 매각이며 모든 자산 이전에 보편 적용 금지. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-04` / 131 | 00:03:52.200 | QUALIFIED | 의무가입 종료일 당일 만기해지 신청이 가능하다는 시연 | 실제 허용 일시와 혜택 계산은 계약일·영업일·금융사 시스템 산정기준에 좌우. 사적 계좌 화면이나 거래 승인은 원본 SRT만으로 확인되지 않음. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-05` / 150 | 00:04:27.759 | QUALIFIED | ETF를 만기 전에 현금화하려면 적어도 2영업일 전에 팔아야 한다 | 국내 주식/ETF 현물거래의 통상 T+2 결제에는 영업일·휴일·시장종류·브로커 조건이 적용. 계좌 해지 시점에 현금가용성 확인. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-06` / 185 | 00:05:34.960 | PRIMARY_CONFIRMED | ISA 만기해지 후 신규 ISA에 다시 가입할 수 있다 | 적격 만기 해지 후 ISA 재가입이 가능하나 가입 제한·기존계좌 종료·세제혜택 산정 별도. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-07` / 200 | 00:06:02.800 | QUALIFIED | 동일 과세연도에 기존 ISA와 신규 ISA에 각각 납입해 연간 2천만원을 초과하는 사례 | 기존 ISA의 미사용 납입한도 이월 및 만기 후 신규 ISA 납입 가능성을 구분. 모든 투자자에게 동일해 연간 4천만원이 보장되는 것은 아님. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-08` / 219 | 00:06:39.800 | QUALIFIED | 3년간 ISA에 8천만원까지 납입할 수 있다는 표현 | 매년 신규 납입한도 발생 시점과 3년 경과시점에 따라 4개 역년 2천만원씩 적격 납입 가능한 예시는 있음. 정확히 36개월마다 8천만원 보장 아님. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-09` / 266 | 00:08:00.479 | QUALIFIED | ISA 화면의 27만원 절세표시는 개인의 수익액 그 자체가 아니다 | 상품별 세제 혜택 표시액은 예시/증권사 계산 방식으로 손익통산·원래 과세액과 비교해야 하며 사적 스크린 확인 없음. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-10` / 280 | 00:08:27.520 | QUALIFIED | ISA 해외지수·국내상장 ETF의 차익은 모두 똑같이 15.4% 과세된다는 인상 | 일반계좌 국내주식형 ETF·해외주식형 국내상장 ETF·국내주식 직접 매매는 과세 분류가 다름. 영상 앞뒤 설명의 특정 ETF에 대한 세금과 전체 ETF를 혼동 금지. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-11` / 293 | 00:08:51.000 | PRIMARY_CONFIRMED | ISA 서민형/농어민형의 세제비과세 한도 400만원 | 요건 충족한 서민/농어민형은 순이익 비과세 400만원, 일반형 200만원을 적용하는 영상 당시 세제 규정이며 초과금액에 분리과세. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-12` / 307 | 00:09:20.720 | PRIMARY_CONFIRMED | ISA 과세대상 이익 천만원과 손실 500만원을 통산하면 순이익 500만원 | 동일 계좌의 적격 과세 손익통산 허용 범위에 한해 산술 1000-500=500만원. 비과세 국내주식 매매차손의 통산 등 자산별 제한에 주의. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-13` / 320 | 00:09:43.760 | PRIMARY_CONFIRMED | 서민형 ISA 순이익 500만원에서 400만원 비과세 후 100만원만 9.9% 과세 | 적격 손익통산 후 서민형 순수익 500만원 예시는 비과세 400만원·초과 100만원의 9.9% 분리과세(지방소득세 포함) 산술이 맞음. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-14` / 364 | 00:11:01.839 | QUALIFIED | 국내상장 국내주식형 ETF 매매차익은 일반계좌에서 과세가 다르다 | 국내주식형 ETF의 매매차익 일반 비과세와 배당소득 과세는 구별해야 함. ISA 계좌 효과가 모든 주식형 ETF에서 동일하지 않음. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-15` / 421 | 00:12:51.360 | QUALIFIED | ISA 안에서 평가손실 상품을 청산해 세금 계산에 반영한다 | 적격과세손익 범위에 따라 손익통산할 수 있지만 단지 매도했다고 모든 손실이 동일하게 세제 공제되는 것은 아님. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-16` / 479 | 00:14:29.759 | PRIMARY_CONFIRMED | 3년 의무가입 전에 ISA를 해지하면 세제 혜택을 잃을 수 있다 | 법령상 부득이한 사유 등 예외를 제외하면 3년 미충족 중도해지에서 혜택을 추징·배제할 수 있어 가입조건 확인. | [근거](https://www.kiwoom.com/mobwm/isa/ia010/MobISAInfoView) |
| `iy7_HMMSLGc-17` / 510 | 00:15:25.639 | PRIMARY_CONFIRMED | ISA 만기자금 일부·전부를 연금저축에 전환하기 위해 연금 금융회사에 신청 | 만기일로부터 60일 이내 전환하고 금융사에 ISA 만기전환 납입임을 사전 알리는 절차 필요. 별도 연금계좌 단순 입금과 구별. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `iy7_HMMSLGc-18` / 526 | 00:15:54.000 | QUALIFIED | ISA 현금화와 해지 완료 이후 연금계좌 전환을 신청한다 | 영상 특정 거래 순서는 합리적일 수 있으나 ISA 종료 및 증권사 결제확인·연금회사 입금 식별 방식은 회사별로 다름. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `iy7_HMMSLGc-19` / 654 | 00:19:30.159 | QUALIFIED | ISA 해지자금 연금전환은 이체계좌를 반드시 직접 연결해야만 인정된다 | ISA 만기전환 인정을 위해 수령회사에서 ISA 해지 사실·만기자금임을 확인해야 하며 계좌번호·증빙·직접 송금 방식은 금융사별로 다름. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `iy7_HMMSLGc-20` / 745 | 00:22:55.520 | QUALIFIED | ISA 매도 현금화와 만기해지, 연금전환 신청을 순서대로 정리 | 상품매도 결제·만기해지·60일 이내 지정 연금계좌 납입 확인이 핵심. 영상에서 고객센터 전화연결 실패로 전환 전체 완료 사실까지는 실증되지 않음. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |

### #193 연금부자수업 EP.01 — 연금·자산배분·리츠·푸른씨앗 — 18건

| claim_id / cue | 시간 | 판정 | 영상 요지 | 독립 검증·정정·한계 | 공식자료 |
|---|---|---|---|---|---|
| `KgiwKdha6F4-01` / 130 | 00:04:37.360 | HYPOTHETICAL | 2010년대 연금 투자 관심이 낮았다는 화자 경험 | 개인 회고로 당시 전체 투자자의 공식 조사 원표 미확보 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-02` / 177 | 00:06:24.319 | QUALIFIED | 절세계좌·연금·자산배분에 대한 관심이 커졌다는 관찰 | 시점별 금융기관 통계 없이는 정확한 증가율을 검증할 수 없음 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-03` / 210 | 00:07:30.759 | QUALIFIED | 소액 적립이 연금투자 입문에 도움이 될 수 있다 | 투자경험을 얻더라도 원금손실 위험은 남음 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-04` / 245 | 00:08:45.560 | HYPOTHETICAL | 미래 세대 노후자산 형태가 달라질 전망 | 미래세대 자산·수급구조는 확정되지 않은 예측 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-05` / 265 | 00:09:29.040 | PRIMARY_CONFIRMED | 증권투자 상품은 소액 적립·자산배분 가능 | 소액 펀드/ETF 분산매수가 가능하나 모든 상품의 조건이 같지는 않음 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-06` / 295 | 00:10:26.640 | PRIMARY_CONFIRMED | 회사 퇴직연금 도입 시 근로자대표 동의·제도설정 | 퇴직급여제도의 적법한 도입·변경에는 근로자대표 절차가 관여 | [근거](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19130) |
| `KgiwKdha6F4-07` / 320 | 00:11:19.600 | QUALIFIED | 회사 퇴직연금 변경 당시 과거 근속분이 개인 계좌에 바로 들어온다는 설명 | DB/DC 및 사업장 규약에 따라 적립금 귀속과 과거근속 반영이 달라짐 | [근거](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19130) |
| `KgiwKdha6F4-08` / 353 | 00:12:24.320 | SPEAKER_OPINION | 부동산 매수보다 주식투자에 큰 금액을 투입하기 어렵다는 심리 | 대담 중 개인 위험심리에 관한 의견으로 사회 전체 통계 아님 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-09` / 410 | 00:14:13.560 | QUALIFIED | 목돈 일부 주식매수와 나머지 분산 운용 | 투자기간·현금수요·손실감내도별 조정 필요 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-10` / 445 | 00:15:19.199 | QUALIFIED | 임대부동산은 월세 현금흐름을 제공 | 공실·유지비·차입금 이자·세금으로 순현금흐름이 달라짐 | [근거](https://kareit.or.kr/invest/page2.php?boardid=reit&mode=list) |
| `KgiwKdha6F4-11` / 470 | 00:16:08.040 | PRIMARY_CONFIRMED | 임대수익 계산에는 대출이자와 관리비 반영 | 세후/비용차감 순수익을 기준으로 투자성을 평가해야 함 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-12` / 485 | 00:16:38.600 | PRIMARY_CONFIRMED | 리츠는 직접 관리 대신 부동산에 간접투자 | 리츠는 부동산 집합투자 및 상장 거래가 가능한 간접투자 수단 | [근거](https://kareit.or.kr/invest/page2.php?boardid=reit&mode=list) |
| `KgiwKdha6F4-13` / 499 | 00:17:04.640 | QUALIFIED | 리츠 가격하락 때 추가매수하면 회복한다는 권유 | 금리·공실·자산가격과 배당 변동으로 회복 보장 불가 | [근거](https://kareit.or.kr/invest/page2.php?boardid=reit&mode=list) |
| `KgiwKdha6F4-14` / 580 | 00:19:33.400 | HYPOTHETICAL | 부모의 사적 연금계좌가 장기운용으로 큰 수익을 거둔 사례 | 개인 계좌·시점별 원장 미인증 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-15` / 625 | 00:21:04.720 | HYPOTHETICAL | 과거 특정 펀드 장기투자로 큰 성과를 낸 사례 | 개별 상품 원표 및 생존편향 검증 불가 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-16` / 660 | 00:22:16.400 | QUALIFIED | 큰 금융위기 발생시점을 정확히 예측하기는 어렵다 | 미래 충격의 시점·규모 불확실성을 분산·유동성 관리에 반영 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-17` / 690 | 00:23:11.960 | PRIMARY_CONFIRMED | 위기를 예상해 분산투자와 장기 위험관리 시행 | 자산배분·분산은 투자기간·손실감내에 맞춘 위험관리 원리 | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `KgiwKdha6F4-18` / 791 | 00:26:30.799 | QUALIFIED | 푸른씨앗을 30인 이하 사업장 대상 퇴직연금기금으로 소개 | 2025 설명으로는 타당하나 2026.7부터 50인 미만, 2027.1부터 100인 미만으로 단계 확대 | [근거](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19130) |

### #194 주택연금 총정리 ver.2025 — 가입·보증료·수령·상속·중도인출 — 29건

| claim_id / cue | 시간 | 판정 | 영상 요지 | 독립 검증·정정·한계 | 공식자료 |
|---|---|---|---|---|---|
| `IfpexqB1IGA-01` / 135 | 00:04:16.239 | PRIMARY_CONFIRMED | 주택연금은 주택을 담보로 제공하고 집에서 계속 살며 정기 지급을 받는 제도 | 국가보증 역모기지 형태의 담보대출이며 월지급금·이자·보증료가 대출잔액에 누적된다. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do) |
| `IfpexqB1IGA-02` / 180 | 00:05:36.039 | PRIMARY_CONFIRMED | 주택연금 이용 중 은행에 매월 원리금을 상환하지 않는다 | 일반형은 생전 정기 원리금 현금 상환의무 없이 사후/종료 정산하지만 대출이자와 보증료는 부채에 누적. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-03` / 205 | 00:06:22.880 | HYPOTHETICAL | 주택가격 4억원이 시간이 흘러도 일정하게 유지된다는 가정 | 담보주택 시장가격·유지보수·지역거래환경은 변하며 집값 4억원 고정은 시나리오. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-04` / 240 | 00:07:26.800 | QUALIFIED | 집값을 쪼개어 평생 월연금으로 지급하는 구조 | 월지급금은 단순 집값/기대생존개월 산술이 아니라 담보평가액·연소자 나이·금리·보증료·연금모형에 따라 산정. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-05` / 280 | 00:08:44.920 | PRIMARY_CONFIRMED | 주택연금 지급액에는 대출이자가 더해져 복리로 부채가 커질 수 있다 | 지급금·수시인출금·초기/연 보증료와 이자 누적이 주택연금 대출잔액을 구성. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_05.do) |
| `IfpexqB1IGA-06` / 320 | 00:09:53.079 | QUALIFIED | 집값이 올라 주택연금을 중도 해지하면 언제나 자유롭게 다시 가입할 수 있다 | 중도해지 시 대출잔액 상환이 필요하며 같은 집의 3년 내 재가입은 원칙적으로 제한되고 예외 조건만 인정. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_05_04.do?mode=list&pager.offset=20&pagerLimit=10) |
| `IfpexqB1IGA-07` / 345 | 00:10:41.639 | PRIMARY_CONFIRMED | 부부 중 어린 사람의 나이를 기준으로 주택연금 월지급액을 산정 | 신청 자격은 부부 중 한 명 55세 이상, 월지급금은 부부 중 연소자 연령을 기준으로 평가. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-08` / 395 | 00:12:11.800 | PRIMARY_CONFIRMED | 지급 누적 원리금이 최종 주택처분대금보다 클 수 있다 | 오랜 생존 및 이자/보증료 적립으로 최종 대출잔액이 담보가치보다 커질 수 있음. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_05.do) |
| `IfpexqB1IGA-09` / 415 | 00:12:52.720 | QUALIFIED | 주택연금 가입자·상속인은 사망 후 집값을 넘는 부족금 전액을 추가 납부해야 한다는 오해 | 국가보증 비소구 대출로 부족분을 상속인에게 추가 청구하지 않음; 반대로 잔여처분대금은 상속인에게 돌아감. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_05.do) |
| `IfpexqB1IGA-10` / 450 | 00:13:49.440 | PRIMARY_CONFIRMED | 담보권 설정형 주택연금은 집 소유권을 그대로 유지한다 | 근저당권 방식은 명의를 유지하지만 담보권 및 거주요건 등이 부과되며 매각시 상환 필요. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-11` / 475 | 00:14:35.959 | QUALIFIED | 주택연금 대출 기준금리는 CD 또는 COFIX 등을 사용하고 가산금리 부과 | 2025 영상 상품과 현재 공사 고시의 기준금리 선택·가산금리 조건 차이를 반영해야 하며 금리가 변동될 수 있음. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-12` / 500 | 00:15:24.480 | QUALIFIED | 과거 금리 추이만 비교하면 앞으로의 주택연금 유리한 기준금리를 알 수 있다 | 미래 CD·COFIX 금리는 확정되지 않아 과거 평균만으로 최적선택 보장 불가. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-13` / 523 | 00:16:10.480 | PRIMARY_CONFIRMED | 월 주택연금 지급액과 누적 이자·보증료를 최종 담보청산에서 비교 | 주택처분가액과 연금지급금 누계·인출금·보증료·이자 누적액을 정산한다. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_05.do) |
| `IfpexqB1IGA-14` / 545 | 00:16:53.319 | QUALIFIED | 2025년 주택연금 연보증료율 0.75%로 소개 | 2025 당시 일반형 연보증료 0.75%는 기간 귀속으로 유효하지만 2026-03-01 신규 신청부터 0.95%로 상향, 초기보증료는 1.5%에서 1.0%로 하향. | [근거](https://www.fsc.go.kr/po010106/86211) |
| `IfpexqB1IGA-15` / 563 | 00:17:28.480 | QUALIFIED | 주택연금 근저당형과 신탁형은 소유권·배우자 승계 절차가 다르다 | 근저당 방식은 소유자 명의 유지, 신탁은 명의 공사 이전 및 수익권 보전; 배우자 승계/채무인수 등 절차가 달라 계약별 확인 필요. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-16` / 575 | 00:17:47.919 | QUALIFIED | 근저당형을 선택하면 모든 주택 소유권 제한·추가 비용이 사라진다 | 근저당권 설정·부기등기·상환의무, 초기/연 보증료 및 유지 비용은 존재. 신탁형 대비 대리권·상속 절차상 유불리 다름. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |
| `IfpexqB1IGA-17` / 690 | 00:21:26.600 | PRIMARY_CONFIRMED | 주택연금 종신지급과 확정기간방식을 선택할 수 있다 | 종신지급은 생존기간 동안 지급되며 확정기간 지급은 정해진 기간 종료 후에도 적격 거주가 유지될 수 있음. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-18` / 704 | 00:21:53.279 | PRIMARY_CONFIRMED | 확정기간 방식의 지급기간은 가입연령에 따른 제한을 받는다 | 연소자 연령별 선택 가능한 확정기간이 다르고 무제한 단축해 주택가치를 전액 선취할 수는 없음. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-19` / 729 | 00:22:43.080 | QUALIFIED | 확정기간 지급 종료 후에도 담보주택 계속 거주가 가능하다 | 확정기간 지급은 종료돼도 주택연금 조건·실거주 및 담보대출의 정상 상태를 유지해야 거주 지속이 가능. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-20` / 761 | 00:23:39.919 | QUALIFIED | 주택연금 정액형은 매월 같은 금액을 지급하므로 물가상승에 따른 실질구매력 감소 가능 | 이 대화는 정액형의 명목 고정금액 설명에 한정해야 함. 영상 후반에서 초기증액형/정기증가형을 직접 소개하므로 모든 주택연금이 고정이라는 독립 주장은 성립하지 않음. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-21` / 770 | 00:23:55.600 | PRIMARY_CONFIRMED | 종신지급방식에는 정액형·초기증액형·정기증가형이 있다 | HF 공식 지급유형표에 세 가지 지급유형이 기재돼 있다. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-22` / 775 | 00:24:06.520 | HYPOTHETICAL | 가입자 중 70%가 정액형을 택한다는 영상 통계 | 2025 신청자 구성비 70% 원표·모집단·집계시점 미확인. 제도 일반원리와 별도로 미확정 유지. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do?tlink=vtab02) |
| `IfpexqB1IGA-23` / 813 | 00:25:13.200 | HYPOTHETICAL | 60세·주택가격 5억원으로 월지급금 100만원대라는 추정 | 개별 2025 월지급액 공식표·부부 연소자/감정가/지급형태 원표 없이 영상 수치 재확정 불가, 2026 지급표는 변경됨. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-24` / 870 | 00:27:00.399 | PRIMARY_CONFIRMED | 집값과 가입연령이 월지급금의 핵심 결정요인 | HF 산식상 부부 중 연소자 나이와 인정되는 주택가격, 지급방식에 따라 차등. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-25` / 891 | 00:27:42.799 | PRIMARY_CONFIRMED | 주택연금의 지급산정 주택가격은 한국부동산원·KB 시세·감정평가 순으로 확인 | 공사 예상연금 조회 공시는 한국부동산원 인터넷시세, 국민은행 시세, 공시가격, 감정평가의 순서를 명시. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-26` / 910 | 00:28:14.600 | PRIMARY_CONFIRMED | 부부 중 연소자 연령 기준으로 월지급액 결정 | 가입기준과 별개로 월지급금은 연소자 연령에 따른 공식표로 결정. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-27` / 945 | 00:29:17.760 | PRIMARY_CONFIRMED | HF 공식 홈페이지에서 예상지급액 조회·온라인 가입신청 가능 | 한국주택금융공사에서 예정 금액 산정/신청 후 보증심사·담보설정·은행 대출취급을 진행. | [근거](https://www.hf.go.kr/ko/sub03/sub03_02_02.do) |
| `IfpexqB1IGA-28` / 1065 | 00:32:43.960 | CONTRADICTED | 4억원짜리 집은 주택연금 혼합 방식으로 주택가격 절반 2억원을 즉시 인출할 수 있다 | 인출한도 50%는 통상 주택 '시가'의 절반이 아니라 공사가 산정한 '대출한도'의 50%를 기준으로 하므로 4억원 주택=2억원 인출 공식은 오류. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_04.do) |
| `IfpexqB1IGA-29` / 1125 | 00:34:38.200 | QUALIFIED | 집값이 오르지 않을 것 같으면 주택연금에 무조건 가입해야 한다 | 현금흐름·수명·비소구 보호 외에도 보증료, 대출이자, 거주/상속 계획, 중도해지 비용, 재가입 제한을 비교해야 하며 가격 전망만으로 무조건 결론 불가. | [근거](https://www.hf.go.kr/ko/sub03/sub03_01_01_06.do) |

### #195 연금저축 세액공제 이월 — 미공제 납입액 전환·ISA 만기전환·공제확인서 — 20건

| claim_id / cue | 시간 | 판정 | 영상 요지 | 독립 검증·정정·한계 | 공식자료 |
|---|---|---|---|---|---|
| `pbDPZUwogeQ-01` / 9 | 00:00:23.640 | PRIMARY_CONFIRMED | 과거 연금저축 미공제 납입액을 올해 공제대상 납입액으로 전환할 수 있다 | 소득세법 시행령 제118조의3은 적격 미공제 연금보험료를 전환 신청하는 특례를 명시한다. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-02` / 22 | 00:00:48.360 | PRIMARY_CONFIRMED | 연금저축 단독 세액공제 대상 납입한도 600만원, IRP 포함 900만원 | 총급여·납부세액 등에 따라 적용세율 12% 또는 15%(지방세 별도), 실제 세액공제는 연금저축 600만원/합산 900만원 한도. | [근거](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=2238) |
| `pbDPZUwogeQ-03` / 29 | 00:01:04.280 | PRIMARY_CONFIRMED | 연금계좌 납입 가능액 1800만원과 세액공제 900만원 한도는 다르다 | 일반 연금저축/IRP 통합 연 납입한도 1800만원은 세액공제대상액 한도와 다르고 ISA 만기전환은 별도 요건. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=126655) |
| `pbDPZUwogeQ-04` / 36 | 00:01:19.040 | QUALIFIED | 연900만원 납입한도 초과액은 세액공제 미사용 원금으로 계좌에 남을 수 있다 | 연금계좌 세액공제받지 않은 개인 납입원금이 과세제외액으로 분류되는 조건이 있고 소득공제 이력의 입증이 필요. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-05` / 57 | 00:02:07.960 | QUALIFIED | 2025년 소득 없이 연금저축에 돈을 넣지 않았어도 과거 미공제 잔액이 있으면 누구나 환급받을 수 있다 | 전환 신청으로 당해 연도 적격 납입으로 볼 수 있으나 최종 결정세액이 없으면 세액공제를 적용해도 실제 환급이 발생하지 않을 수 있다. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-06` / 64 | 00:02:24.959 | QUALIFIED | 전년도 공제를 못 받은 원금 900만원을 2025년 공제대상으로 전환 | 전년도 미공제 원금의 적격 납입금 전환은 가능하지만 연금저축 단독 한도는 600만원, IRP 포함 900만원·결정세액과 요건에 맞게 분할해야 한다. | [근거](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000515824&wnkey=faec7a02-7c00-4925-b0c4-40c16397f6db) |
| `pbDPZUwogeQ-07` / 71 | 00:02:44.400 | PRIMARY_CONFIRMED | 이전 과세기간의 미공제 납입금을 현재 연도 납입처럼 취급 | 취급자에 신청하고 법정 요건 충족시 신청일에 해당 연도 연금보험료로 재납입한 것으로 봄. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-08` / 78 | 00:02:59.560 | QUALIFIED | 세액공제 이월은 무기한이므로 앞으로 어떤 해에나 세금환급이 보장 | 현행 제도상 이전 과세기간 미공제분의 전환특례가 있지만 장래 개정 가능성과 연도별 공제한도·납세세액 조건 때문에 무조건 환급 아님. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-09` / 99 | 00:03:48.120 | QUALIFIED | ISA 만기 연금전환금액의 10% 최대 300만원을 추가로 세액공제 받는다 | 300만원은 추가 '세액공제 대상 납입액 한도'이지 세금 300만원 직접 환급이 아니다. 적격 ISA 계약만료 후 60일 이내 연금납입 및 연도별 소득세 요건 확인. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `pbDPZUwogeQ-10` / 118 | 00:04:33.360 | QUALIFIED | ISA 만기금액이 연금계좌로 넘어오면 300만원 공제대상액 외 잔액은 과세제외 원금 | 세액공제를 받지 않은 적격 개인납입금과 ISA 전환금의 원천, 실제 전환공제 대상액 및 기존 납입이력에 따라 계좌 과세재원 구분 필요. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-11` / 128 | 00:04:54.880 | PRIMARY_CONFIRMED | ISA 만기전환금액은 연금계좌 연1800만원 한도를 넘어 납입할 수 있다 | ISA 만기 전환은 일반 연1800만원 납입한도와 별도 적격 납입특례이되 만기일·60일·잔액 한도 조건 충족. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=126655) |
| `pbDPZUwogeQ-12` / 144 | 00:05:27.880 | QUALIFIED | ISA 만기금 전액 연금전환 후 매년 미공제 원금을 납입으로 전환하는 전략 | 과거 ISA 전환 잔액에 대한 특례 대상성은 국세청 유권해석이 확인하지만 계좌별 세무자료·전환자격·공제 한도 및 수령시 과세를 확인. | [근거](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000515824&wnkey=faec7a02-7c00-4925-b0c4-40c16397f6db) |
| `pbDPZUwogeQ-13` / 155 | 00:05:52.960 | QUALIFIED | ISA 만기자금 1억원 이전·300만원 공제대상 처리 후 미공제 원금 9700만원 예시 | 1억원-300만원=9700만원은 조건부 장부상 예시. 실제 300만원 공제대상 여부는 전환 특례와 사용한 공제액·계좌별 과세재원 확인 필요. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `pbDPZUwogeQ-14` / 161 | 00:06:05.880 | HYPOTHETICAL | 9700만원을 연600만원씩 세액공제 전환하면 16년 넘게 공제 가능 | 9700÷600=16.17년 산술상 가능액이나 매년 소득·결정세액·개인계좌 잔액·법령이 동일하다는 가정이 필요. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-15` / 168 | 00:06:22.800 | QUALIFIED | 세액공제 안 받은 연금저축 납입원금은 언제든 인출할 수 있다 | 적격 미공제원금은 연금저축 인출시 원칙 과세제외지만 인출순서·원천증빙·계좌상품 환매제한·인출 후 공제가능 잔액 감소 등을 확인. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-16` / 176 | 00:06:39.680 | QUALIFIED | 연금계좌에 과세제외 원금을 보유하면 운용수익에 과세이연을 받을 수 있다 | 계좌내 운용수익은 인출시 과세분류와 세액공제 이력에 따라 과세, 연금외 수령 시 기타소득세 등 불이익이 생길 수 있음. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=126655) |
| `pbDPZUwogeQ-17` / 218 | 00:08:07.639 | QUALIFIED | 증권사마다 앱에서 세액공제 전환 신청을 지원하는지는 다르다 | 앱 메뉴·지원 화면은 2025 당시 회사별로 다르며 최신 금융사 정책/이용약관 확인 필요. | [근거](https://advisor.koreainvestment.com/pension/nwInvestment/_static/Product_A_NW_32770.jsp?type=target) |
| `pbDPZUwogeQ-18` / 244 | 00:09:04.320 | PRIMARY_CONFIRMED | 전환 가능 금액은 신청계좌 과세제외 원금·과거 공제내역으로 확인 | 전환액은 과거 미공제 납입원금을 입증해 취급기관에 신청하는 적격 금액으로 판단. | [근거](https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1024234167) |
| `pbDPZUwogeQ-19` / 268 | 00:10:00.360 | QUALIFIED | 연금보험료 등 소득·세액공제 확인서 제출을 통해 과거 공제 여부 확인 | 국세청 공제확인서로 과거 납입·공제 내역을 입증할 수 있고 증권사별 구비서류·처리시점이 다름. 매년 7월 이후 확정이라는 보편 규칙은 아님. | [근거](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=2238) |
| `pbDPZUwogeQ-20` / 301 | 00:11:13.839 | QUALIFIED | 전년도 미공제 연금저축 납입액을 본인이 신청해 올해 공제대상으로 처리 | 본인 신청과 금융사 승인, 적격 금액, 연도별 결정세액을 충족해야 세액공제 실익이 발생하며 자동 적용되지 않음. | [근거](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000515824&wnkey=faec7a02-7c00-4925-b0c4-40c16397f6db) |

## 5. 미확정·기존 OPEN·승인 및 재현 경계

- #191 2025 당시 서비스 출시 자체는 확인하되 미래자산 예측 신뢰구간·성과 원표 검증 대상이 아님.
- #192 사적 ISA 원장 및 금전적 세제혜택 실현, #193 가족 펀드·연금 원표, #194 2025 개인 주택시가/연금예상표와 신탁계약, #195 납입·과세제외금액 증빙 및 실효환급은 **미확정·활용 제한**으로 유지.
- 원본 음성 및 영상 프레임, 독립 공개 한국어 전문 동등성 검증 미완료. 기존 OPEN **24건 그대로 유지**하며 영상별 미확정 조건은 주장별 QUALIFIED/HYPOTHETICAL로 관리해 허위 확정승격 금지.
- 이번 #191~195 5편 모두 비공개 원본 해시·시간 구간 검증. **#191 교육 제외 1편**, **#192~195 교육 V3 4편·87건**만 추가. 기존 누적 **189편/3,039건**에서 최종 **193편/3,126건**, 총791편 중 **598편 남음**. 이 합계는 파일 저장·승인 게이트·GitHub Push 및 PR CI 성공 이후에만 확정.
- GitHub `main`·기존 분석·사적 원본 SRT/ZIP은 수정하지 않고 단일 커밋으로 연구 브랜치에만 기록.
