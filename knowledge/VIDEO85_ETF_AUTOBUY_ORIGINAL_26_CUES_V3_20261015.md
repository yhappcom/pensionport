# 박곰희TV #85 ETF 자동매수 — 원본 SRT V3 학습검증 (2026-10-15)

**영상:** https://www.youtube.com/watch?v=BwbFnc0-yFc · 약 58초, 2026-05-06 게시.

**원본 검사:** 개인 SRT 26개 큐 / 2,021 bytes / 원시 SHA256 `387cc34c863f3875017312895816398a5ec017f7494c0c96501f84be95b6f324`; 사용자 ZIP SHA256 `69be8639162f8e00bfa09f0d4b8a6fe95db0a07054ad370709ce0d4e53628b5f` (CRC PASS). 별도 공개 유튜브 전체 한국어 ASR과 개인 SRT 전부를 공백 제거하고 비교한 364자 SHA256 `034ccc6346efa4ca78afb090209357805995c9180806f8ef94a5ffcf246573ea`가 정확히 일치. 양측 모두 자동자막이므로 음성·프레임 검증한 것은 아님.

## 핵심 교육 및 경계

영상은 ETF 선정 → 월급 다음날 자동이체 → 그다음날 ETF 정액 자동매수라는 **별개 실행 단계**를 설명한다. [미 SEC Investor.gov DCA 정의](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging)에 따르면 고정금액 정기투자는 낮은 가격에 더 많은 수량, 높은 가격에 더 적은 수량을 매입할 수 있으나 **원금이나 장래 수익을 보장하지 않는다**. 반복주문은 휴일·예수금 부족·중개사 지원 상품·체결 조건의 영향을 받는다.

기존 잠정 12개 항목 가운데 **10건을 영상 원본 cue 번호와 밀리초 시작시각에 연결**, 한국거래소 거래 최소단위/별도 리밸런싱 등 **2건은 연구자가 덧붙인 조건으로 분리**. 스피커가 언급하지 않은 사항은 스피커 발언으로 승인하지 않는다.

## 전체 12건

| ID | 원본 시각 또는 연구자 보충 | 주장 의역 | 판정 | 1차 확인 |
|---|---|---|---|---|
| 01 | #4 00:00:06.240 | ETF 가격이 오르거나 내릴 때 투자자가 심리적으로 정기매수를 미루는 현상 | QUALIFIED | 원본 #4~8: 가격의 오르내림을 보고 정기매수를 미루는 심리 사례, 보편 실증 통계가 아님. [공식근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 02 | #9 00:00:17.640 | 정기 자동매수는 달러코스트애버리징(DCA) 전략을 실행하는 도구로 활용 가능 | PRIMARY_CONFIRMED | 원본 #9 자동매수를 제안, #17~20 반복적 금액 주문; Investor.gov 정액정기매수(DCA) 정의와 합치. [공식근거](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging) |
| 03 | #19 00:00:39.600 | 장기 정기적 같은 금액 투자에서는 가격이 낮을 때 더 많은 수량, 높을 때 적은 수량 매수 | PRIMARY_CONFIRMED | 원본 #19 '정해진 금액만큼' 주문은 DCA이며 동일 금액은 가격 낮을 때 더 많은 수량. 실제 1주 주문 제한 있음. [공식근거](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging) |
| 04 | #11 00:00:22.439 | 6:4 또는 연구/꼬미 포트폴리오 중 하나를 먼저 고르고 자동화하라는 권유 | QUALIFIED | 원본 #11~14의 6:4·연구포트·꼬미포트는 영상 속 예시. ETF 개별 종목·실제 비중이 없어 보편 투자추천 아님. [공식근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 05 | #15 00:00:30.599 | 월급이 들어온 다음날 증권계좌로 투자금을 자동이체 설정 | PRIMARY_CONFIRMED | 원본 #15~17 월급 이후 계좌 자동이체 설정. 은행·증권사 실제 서비스 신청, 잔액 및 일정 유효 조건. [공식근거](https://www.investor.gov/introduction-investing/getting-started/investing-your-own/direct-investing) |
| 06 | #18 00:00:37.480 | 그다음날 ETF 자동매수 주문을 걸어 매월 매수가 실행되도록 설정 | QUALIFIED | 원본 #17~20 자동이체 다음날 ETF 자동매수 별도 약정. 매일 유동성, 잔액부족, 장외시간, 미체결 가능. [공식근거](https://regulation.krx.co.kr/contents/RGL/03/03060101/RGL03060101.jsp) |
| 07 | 연구자 보충 / 영상 발언 없음 | 한국거래소 상장 ETF는 최소 1주 단위 일반 현물 시장 거래 상품 | PRIMARY_CONFIRMED | 연구자 독립 보충: 한국거래소 ETF 통상 1주 거래단위이고 판매사 정액/소수점 매수 서비스에 따라 실수량 상이; 화자가 직접 설명하지 않음. [공식근거](https://regulation.krx.co.kr/contents/RGL/03/03060101/RGL03060101.jsp) |
| 08 | #21 00:00:44.520 | 자동매수는 투자자가 매수 시점 매번 가격을 보지 않아도 투자계획을 실행하도록 돕는다 | QUALIFIED | 원본 #21~22 자동화는 매번 가격 확인할 부담 감소. 계좌 상태·자산위험·잔고 확인은 필요. [공식근거](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging) |
| 09 | #22 00:00:46.640 | 적립식 자동매수는 가격 변동과 타이밍 위험을 완전히 없앤다 | QUALIFIED | 원본 #22 타이밍 고민 없다는 비유는 정기주문 실행 부담을 줄임; 가격변동·손실·매매시점 위험 제거 아님. [공식근거](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging) |
| 10 | #23 00:00:48.719 | 투자기간과 총납입액의 증가가 중요한 장기투자 구성요소라는 조언 | QUALIFIED | 원본 #23~24 오랫동안 납입하는 것이 투자 구성요소라는 조언; 시장수익률/적합성 보증 아님. [공식근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 11 | #15 00:00:30.599 | 강사는 계좌 자동이체 설정과 ETF 자동매수 주문을 별도 단계로 설명한다 | PRIMARY_CONFIRMED | 원본 #14~19 별도의 자금이체와 ETF 자동매수 설정을 순서대로 말함. 이체만으로 자동주문 실행 불가. [공식근거](https://www.youtube.com/watch?v=BwbFnc0-yFc) |
| 12 | 연구자 보충 / 영상 발언 없음 | 자동매수는 일정 금액마다 동일 ETF에 규칙적 투자하는 한 방법일 뿐 만능 리밸런싱·세금조정 시스템은 아님 | QUALIFIED | 연구자 독립 보충: 단순 반복 자동매수만으로 위험비중 리밸런싱이나 원금 보호·세금 최적화가 자동 수행되지는 않음. [공식근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |

**합계:** PRIMARY_CONFIRMED 5 / QUALIFIED 7. 영상 원음·증권사 실제 자동매수 설정화면·계좌 기능·개별 수익/세금은 미검증. 자막 전문/ZIP은 공개 저장하지 않음.

[자료파일](../data/subtitles/pilots/BwbFnc0-yFc.json) · [정식 V3 기록](../data/analysis_events/BwbFnc0-yFc.json).
