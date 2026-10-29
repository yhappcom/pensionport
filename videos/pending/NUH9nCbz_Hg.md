# NUH9nCbz_Hg — 채권을 폰으로 사보겠습니다

- type: long_form
- content_tag: 따라하기
- source_status: indexed practical record
- knowledge_change: EXTEND, TIME_SENSITIVE

## 핵심 분석
채권의 이론을 모바일 증권사에서 실제 매수하는 과정으로 연결한다. 채권을 예금처럼 '금리 숫자'만 보고 사는 것이 아니라 발행자, 만기, 가격, 표면금리, 세전/세후 수익률, 신용위험을 확인해야 한다.

## 실행
채권 메뉴 → 종목검색 → 발행자/신용등급 → 만기 → 매수가격/수익률 → 최소매수단위 → 주문 순으로 확인한다.

## 위험
만기 전 매도 시 시장금리 변화로 손실이 날 수 있고 회사채는 부도위험이 있다. 앱 화면·판매채권·수익률은 TIME_SENSITIVE다.

## 프레임워크
채권 자산군 → 개별채권 due diligence → 증권사 execution으로 구체화한다.
