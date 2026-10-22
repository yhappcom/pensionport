# ETF 베이직 3편 — 공식근거 검증 지식 카드 (2026-10-12)

**대상:** 63번 [ETF 선택 6기준](../data/analysis_events/LVE7XN_esTc.json) / 66번 [ETF 종류](../data/analysis_events/k9O79HeMOp0.json) / 61번 [ETF 분배금](../data/analysis_events/7RRWNL0V6As.json). 원본 SRT 250·222·152구간 등록 해시 일치. 실제 원음·화면/제3자 공개자막 전체 비교는 수행하지 않았으며 사후 정밀검증이 의사결정에 필요한 숫자/문구만 OPEN으로 분리한다.

## A. ETF 선택 — 6요소 체크리스트이지 6개 만능 공식은 아님

- 순자산 총액 규모는 지속성·투자수요의 참고지표이지 미래 수익률이나 원금보장 지표가 아니다.
- 거래량 외에도 스프레드·호가 깊이·LP 호가 제출 상황을 점검한다. LP가 반드시 존재하더라도 원하는 체결가와 수량을 언제나 보장하지 않는다. 출처: [KRX LP 규정](https://regulation.krx.co.kr/contents/RGL/03/03060103/RGL03060103.jsp).
- **괴리율**은 ETF 거래가격↔좌당 순자산가치(NAV)의 가격 차이. **추적차이(tracking difference)**는 특정 기간 ETF NAV 수익률↔기초지수 수익률의 차이. **추적오차(tracking error)**는 엄밀하게는 구간별 상대수익률 차이의 변동성(표준편차)으로 정의될 수 있다. 국내 거래소의 기초 교육 자료에서는 종종 '추적오차'로 넓게 안내하므로, 표/정량 분석 시 정의를 명확히 쓴다. 출처: [KRX NAV 및 괴리율](https://www.krx.co.kr/contents/OPN/01/01030203/OPN01030203T1.jsp), [KRX 지수 추적 안내](https://m.krx.co.kr/contents/02/0204/020401/JHPETP020401M01.jsp).
- 동일 지수라도 투자기간·통화·환헤지·분배 재투자 반영 기준을 맞춘 **총수익률**로 비교한다. 과거 수익률은 미래 우위 보장이 아니다.
- 광고 총보수 외 **기타비용·매매중개수수료·실제 거래 스프레드**까지 본다. 출처: [KB자산운용 실부담비용 설명, 2026-07-13](https://kbam.co.kr/insights/guide/etf-total-expense-ratio-vs-actual-cost).

## B. ETF 유형 — 레버리지·채권·원자재·커버드콜의 위험을 분리

- 시장대표/섹터/스타일/테마 ETF는 이름만으로 편입자산이나 투자 분산 정도를 확정하지 않는다. 특정 산업이나 테마에 집중된 ETF를 '시장 전체 분산'이라고 평가하지 않는다.
- 채권 ETF는 금리·신용·듀레이션·환율 위험이 있고 개별 만기 채권의 약속된 상환액과 다르게 가격이 움직일 수 있다.
- **레버리지/인버스의 목표배수는 대개 하루 단위**다. 2일 지수 +10%, 그다음 -9.0909% → 지수 약 0%에 복귀하나, 일일 2배 ETF 가상 모델에서는 +20%, -18.1818% → 약 **-1.818%**(수수료·추적차이 제외). 2배라는 이름을 1년 수익률에 곱하지 않는다. 출처: [SEC 레버리지/인버스 투자자 공고](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec).
- 금/원자재 선물형은 현물과 달리 만기 교체·롤오버·보수 및 선물곡선 영향이 있으며 원금보장형이 아니다.
- 커버드콜은 옵션 프리미엄을 수령하는 대신 상승 참여가 제한될 수 있고 **분배율 ≠ 총수익률**이다. 출처: [SEC 옵션 기본](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-63), [SEC 펀드 분배금 공고(2026-08-19)](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/fund-distributions-investor-bulletin).

## C. PR/TR와 현금 분배 — 61번 교육 영상의 중요한 정정

- **PR(Price Return)**은 지수에서 분배금을 재투자한 효과를 반영하지 않은 가격수익률 기준이고, **TR(Total Return)**은 배당 등 현금흐름의 재투자를 가정한 총수익률 기준이다. 이것만으로 실제 ETF가 투자자에게 현금을 지급/유보하는지가 결정되지 않는다. **영상의 'PR 지수면 지급/TR 지수면 무조건 재투자' 일반화는 `CONTRADICTED`.**
- 한국의 2025-07-01 이후 이자·배당분에 관한 TR ETF 유보범위 조정으로 일부 해외주식·채권 TR ETF의 분배 정책이 변경됐다. **국내 주식형 TR ETF는 일정 조건에서 예외**다. 'TR ETF는 전부 사라졌다'는 단정도 금지. 출처: [삼성자산운용 공식 공지](https://m.samsungfund.com/etf/lounge/notice-view.do?no=67815&searchText=2025), [RISE ETF 공지](https://www.riseetf.co.kr/cust/notice/123?page=1).
- 배당·이자·매매차익·원금반환 등 다양한 재원이 분배금을 이룬다. 분배 지급 시 NAV가 그 금액에 상당해 줄어드는 현상이 통상적이며, 지급일 주가와 받는 현금을 합친 **총수익**을 비교한다. 월분배금은 금액·지속가능성이 보장되지 않는다. 출처: [SEC 펀드 분배금 투자자 자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/fund-distributions-investor-bulletin).

## D. 근거 이력과 지식 재사용 규칙

- 모든 세부 영상 주장 ID·원문 앵커·1차 근거·정정·한계는 각 `data/subtitles/pilots/<ID>.json`과 `data/analysis_events/<ID>.json`이 정본이다.
- **검증 완료 범위:** 원본 등록/내용 + 주장별 일반 규칙. **추가 선택 검증:** #63 당시 모의 ETF 화면 수치는 [선택 검증 목록](../data/subtitles/optional_verification_register_20261012.json)에 `OPEN` 기록.
- 이 파일은 투자상품 추천 목록이 아니다. 구체 ETF 매수 판단·세금·연금/ISA 매매가능 상품은 최신 개별 공시·설명서에 따라 달라진다. 신규 공식 해석이 나오면 영향을 받는 주장 원장, 단일 V3 분석, 이 지식 카드, 전체 검증 대기열을 함께 업데이트한다.
