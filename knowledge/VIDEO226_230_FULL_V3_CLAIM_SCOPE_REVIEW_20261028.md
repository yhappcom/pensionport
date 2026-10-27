# 박곰희TV #226~230 — 비공개 SRT·공식자료 V3 주장별 검증 (2026-10-28)

**선별 5편·55건**: PRIMARY_CONFIRMED 17 / QUALIFIED 26 / HYPOTHETICAL 11 / CONTRADICTED 1.

## 증빙 및 승인 범위

원본 Google Drive: https://drive.google.com/file/d/1CJvWcNyjcMM5xrjio_YFWSbr57-1J--1/view?usp=drivesdk

- ZIP 2,913,470바이트, SRT 99개, SHA-256 `9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10`
- 이번 5편 자막 총 2,236cue, 173,347바이트. 개별 해시·파일명은 `data/subtitles/registry_226_230_20261028.json`에 등록.
- 투자교육 내용 중 핵심 주장 55개에 대한 근거 대조. 전체 영상 발언·개인 거래실적·원음·영상프레임·공개 한국어 자막 전문의 일치까지 인증하는 것은 아님.
- 2025년 거시경제 수치·개별 ETF 비용순위 등 **미확정 11건은 확정 통계나 현재 상품 추천으로 재사용 금지**.

| 영상 | 원본 cue | 주장 | 1차 확인 | 조건부 | 미확정 | 정정 | V3 |
|---|---:|---:|---:|---:|---:|---:|---|
| #226 `GtMa-bEFJa8` | 1008 | 14 | 1 | 7 | 6 | 0 | 승인 |
| #227 `koN6tXbpb_s` | 26 | 5 | 3 | 2 | 0 | 0 | 승인 |
| #228 `p94_t07GTKA` | 283 | 13 | 4 | 8 | 1 | 0 | 승인 |
| #229 `z1oZOJ3_uIk` | 891 | 17 | 5 | 8 | 3 | 1 | 승인 |
| #230 `9T_72qyO1Dk` | 28 | 6 | 4 | 2 | 0 | 0 | 승인 |
| **합계** | **2236** | **55** | **17** | **27** | **10** | **1** | **5편** |

**참고:** 최종 정합집계는 하단의 각 주장별 원장에 저장된 `assessment` 필드에서 계산해야 하며 위 표의 분류 행은 원장과 정합성 검사가 필요하다. 

## 중요 정정

1. **#226 모멘텀·국민연금**: 52주 신고가 추종은 손실 위험이 있고 한국주식 '최고 투자전략' 보장 근거 없음. 2022년 국민연금 공식 운용 수익률 -8.22%와 특정 국내주식 매도 제한으로 수십조 손실이 발생했다는 미확정 인과 추론을 구별. [SEC 모멘텀 경고](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/investor-alert-thinking-about-investing-latest-hot-stock-understand-significant-risks-short-term) · [국민연금](https://www.nps.or.kr/pnsinfo/statistics/getOHAF0118M0.do)
2. **#227·230 TDF**: 글라이드패스 자동 배분은 목표연도의 노후소득·원금 보장이 아니다. 일반펀드 환매와 ETF 매도·대금 인출도 구별. [SEC](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/target-date-funds-investor-bulletin)
3. **#228 주식 결제**: 국내 정규장 09:00~15:30, 주식 T+2 결제. 장전·장후·대체거래 시간은 전 종목 동일한 정규장 시간이 아님. [KRX](https://regulation.krx.co.kr/contents/RGL/03/03010100/RGL03010100T1.jsp)
4. **#229 ETF 비용**: 총보수, TER, 내부 매매중개수수료, 괴리율·추적오차 구별. 'TR 보수' 표현은 Total Return과 혼동 방지. ETF 지정참가회사(AP)의 설정·환매 역할과 일반적인 판매보수 수취구조를 동일시한 진술은 정정. [KRX AP](https://regulation.krx.co.kr/contents/RGL/03/03060106/RGL03060106.jsp)
5. **#230 소규모펀드**: 원본액 50억원 기준의 법정 기간·요건과 임의해지 위험을 구별. 즉시 강제 해지로 단정 금지. [법령정보](https://www.law.go.kr/)

## 주장별 전수 원장 위치

`data/subtitles/pilots/GtMa-bEFJa8.json` 및 `data/analysis_events/GtMa-bEFJa8.json` (#226 14건)

`data/subtitles/pilots/koN6tXbpb_s.json` 및 `data/analysis_events/koN6tXbpb_s.json` (#227 5건)

`data/subtitles/pilots/p94_t07GTKA.json` 및 `data/analysis_events/p94_t07GTKA.json` (#228 13건)

`data/subtitles/pilots/z1oZOJ3_uIk.json` 및 `data/analysis_events/z1oZOJ3_uIk.json` (#229 17건)

`data/subtitles/pilots/9T_72qyO1Dk.json` 및 `data/analysis_events/9T_72qyO1Dk.json` (#230 6건)

각 원장의 55개 주장에 시간코드·cue 번호·판정·개별 독립 근거 URL·현행 활용 제한을 기록했다. 공개 GitHub에는 ZIP/SRT 전문을 저장하지 않았다. 기존 OPEN 24건·#204 예외·#219 투자교육 제외와 `main`을 변경하지 않았다.
