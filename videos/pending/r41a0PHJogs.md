# r41a0PHJogs — 미국ETF를 소개합니다

- published_at: 2021-11-26
- type: long_form
- source_status: public metadata/indexed educational record
- knowledge_change: EXTEND, REINFORCE, TIME_SENSITIVE

## 핵심 분석
미국 ETF를 해외주식 투자의 구현수단으로 소개한다. ETF는 미국시장·섹터·채권·원자재 등 다양한 노출을 한 종목처럼 거래할 수 있게 하지만, 미국 상장이라는 이유만으로 분산·저위험 상품이 되는 것은 아니다.

## 판단 구조
투자목적 → 기초자산 → 추종지수 → 구성종목/집중도 → 보수/추적 → 거래통화/환율 → 세금 순으로 본다. 국내상장 해외ETF와 미국상장 ETF는 동일 기초자산이라도 거래·세금·환전 구조가 다르다.

## 위험/시간의존성
배당 원천징수, 양도소득 과세, 거래비용·환전조건은 TIME_SENSITIVE다. 특정 ETF의 과거 보수·규모를 현재값으로 재사용하지 않는다.

## 프레임워크
기존 ETF implementation framework에 상장시장·통화·국가간 세금 레이어를 추가한다.
