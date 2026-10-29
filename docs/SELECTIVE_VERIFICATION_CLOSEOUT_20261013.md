# 박곰희TV 연구의 5개 검증 과제 — 선택적 검증 종료 기준과 잔여 OPEN

기준일: 2026-10-13 · 연구 브랜치 전용 · **절차상 작업 종료와 개별 숫자 사실확정은 별개**

## 연구 운용 결정
- 원음/화면의 70/791편 전수검증은 교육 연구의 필수 조건에서 제외한다. 원본 SRT 등록/해시와 금융 핵심 주장별 신뢰할 수 있는 독립 근거 검토가 기본이며, 발언 숫자가 결론을 바꾸거나 표/슬라이드만이 핵심 증거인 경우 해당 구간만 원본 미디어 확인을 요청한다.
- 원본 장기 성과 시계열이 없다면 재현했다고 주장하지 않는다. 관련 수치의 사용은 보류하고 검증된 분산 원리와 가정 포트폴리오를 구분한다. 유사 데이터의 다른 백테스트를 원본 복제로 표시하지 않는다.
- 아래 5개 **연구 운용 결정은 CLOSED_WITH_OPEN_EVIDENCE**이다. 제3자 자료나 계약서가 없어 남은 개별 핵심 주장 수준의 OPEN은 유지한다. 교육용 분석 `APPROVED`를 실제 발언·실효 세금·수익률에 대한 보증으로 승격하지 않는다.

## 작업별 판정표

| 당초 과제 | 절차적 처리 | 근거·제약 및 종료 상태 |
|---|---|---|
| ① 모든 영상 원음·화면 | **GLOBAL_BLOCKER_REMOVED** | [연구 기준](INVESTMENT_RESEARCH_VERIFICATION_POLICY_20261012.md) 2절; 사용자 원본 미디어 음성·프레임 자체는 미확인. 필요한 시점만 선별적으로 재조회 |
| ② #8·#15 공개전사 | **TRANSCRIPT_DIFF_LOCATED** | #8 원본 1,039큐·공개 1,037줄 중 공개 누락: 원본 #182 05:59.400 ‘코스닥’, #802 26:11.520 ‘텔’. 다른 1,037개는 동일. #15 원본 650·공개649 중 누락: #649 24:44.902 비발화 ‘[음악]’; 다른 649개 동일. **실제 발성 여부는 별도**; [검증 대기열의 2026-10-12 추가 감사](SUBTITLE_VERIFICATION_QUEUE_20261010.md) |
| ③ #6 정기금 증여 | **STATUTORY_PRINCIPLE_VERIFIED_TRANSACTION_OPEN** | 시행규칙 제19조의2 3항에 연3% 할인율: [법령](https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0019&lsiSeq=284609&urlMode=lsScJoRltInfoR). 월18만9,000원×120=명목2,268만원. 단순 연도말 합계할인 약1,934만6,500원, 연도초 약1,992만6,895원, 월말 금융모형 약1,961만1,095원으로 **모델 가정에 따라 다르며 실제 신고가액 아님**; 지급일·계약·종전증여 필요 |
| ④ #8·#9 환전 및 ETF 과세 | **LEGAL_CLASSES_TRIAGED_PRODUCT_EFFECTIVE_RATE_OPEN** | 현물 환전, 해외주식 매매, 해외상장 ETF 분배금, 국내상장 ETF 배당소득은 별도 분류. [JPX](https://www.jpx.co.jp/english/equities/products/etfs/issues/01-08.html)의 1557 도쿄 중복상장 미국ETF와 2558 일본 운용ETF는 법적형태가 다름. [일본 NTA](https://www.nta.go.jp/taxes/shiraberu/taxanswer/gensen/2884.htm)의 단일 원천징수율을 모든 비거주자·모든 상품의 한일 간 최종 실효세금으로 대입 금지. 투자자 거주지·특정 종목·계좌·조약·원천징수 내역은 OPEN. #9 과거 은행 1.75% 스프레드는 실제 상품/날짜 자료 없으므로 가정치 |
| ⑤ #15 1972~2022 올웨더 | **REPRODUCIBILITY_PROTOCOL_DONE_ORIGINAL_RETURNS_UNREPRODUCED** | [입력 검증·계산 코드](../scripts/reproduce_all_weather_1972_2022.py)는 실제 확인된 월별 총수익률 CSV와 출처가 없으면 결과를 차단함. 도서 26% 미국주식/34% 장기국채/20% 금/20% 원자재 모델의 정확한 대리지수·배당재투자·선물 롤비용·리밸런싱·세금·통화·원표가 없어 **영상 주장 CAGR/MDD/샤프 재현하지 못했으며 HYPOTHETICAL 유지**. [Bridgewater 공식 All Weather 원리](https://www.bridgewater.com/research-and-insights/the-all-weather-story)는 별도 |

## 신규 연구 진행
- 원본 ZIP의 비공개 SRT 70개 중 기존 **45편/415개 주장**에서 **#44 09ojTPmKlQg 7개 주장**, **#46 ZCOyHZj7yFA 6개 주장**, **#48 9VLtWX1vJxg 4개 주장**을 검토해 **48편/432개 주장**의 교육 분석 기록으로 증가.
- #44는 1926년 출간 `The Richest Man in Babylon`의 조언과 역사적 실재의 차이, 저축 10%·주택 최고의 투자 같은 보편적 최적성 주장을 조건부로 기록한다. [원전 발췌](https://baratelliinstitute.com/reading-room-clason-seven-cures), [서지](https://books.google.com/books/about/The_Richest_Man_in_Babylon_Original_1926.html?id=4tc3zwEACAAJ), [CFPB 지출계획](https://www.consumerfinance.gov/consumer-tools/educator-tools/your-money-your-goals/toolkit/).
- #46은 가계부/예산/6~12개월 지출 패턴 분석을 인정하되 소비절약은 자동 결과가 아니고 계좌연동 개인정보 위험을 확인한다. [CFPB 계좌 데이터 공유](https://www.consumerfinance.gov/archive/blog/what-to-consider-when-sharing-your-financial-data/).
- #48은 2차 클래스 모집을 알리는 **과거 홍보영상**임. 실제 수강료·현행 모집 상태·배당수익 등을 근거 없이 투자지식으로 승격하지 않는다. 투자 강의의 금융상품과 절세 효과는 따로 심사한다.
- 3편 모두 원본 자동 SRT 전체 읽기·바이트 SHA 확인. **원음·화면 직접 대조 0건** 및 **독립 공개전사 전구간 대조 미실시**를 명시하며 `source_audit`/법적 한계는 영상별 pilot 및 V3에 보존한다.

## 향후 작업의 재개 조건
새로운 원영상 구간, 정기금 증여 계약·지급일, 일본 ETF 실제 세금 지급명세, 올웨더 도서의 동일 원시 월별 총수익률을 확보하면 해당 `optional_verification_register_20261012.json`의 OPEN만 재심사한다. **기타 원본 22편 분석을 이 자료 없이 중단하지 않는다.** 일상적인 연구진행 상태와 정량 수익률의 사실성 여부는 독립하여 기록한다.
