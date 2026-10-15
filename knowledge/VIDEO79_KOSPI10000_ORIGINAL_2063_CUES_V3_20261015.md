# 박곰희TV #79 — 효라클 「코스피 1만 투자지도」 인터뷰 33개 핵심 검증 · 원본 2,063큐 V3 교육승인 (2026-10-15)

**영상:** [`mRRev963GaA`](https://www.youtube.com/watch?v=mRRev963GaA) · 박곰희TV · 2026-05-17 게시 · 69분 31초. 기존 [2026-10-14 공개 자막 기반 잠정 보고서](./KOSPI10000_NEW_FRONTIER_HYORACLE_VIDEO79_PROVISIONAL_20261014.md)는 역사적 초안으로 보존하고 본 보고서와 [정식 canonical 분석](../data/analysis_events/mRRev963GaA.json)을 최신 검증 기준으로 사용한다.

## 1. 비공개 원본 SRT 전체와 공개 전사의 차이 검증

- 업로드 비공개 ZIP `71-100.zip` **517,466 bytes**, CRC **PASS**, SHA-256 `69be8639162f8e00bfa09f0d4b8a6fe95db0a07054ad370709ce0d4e53628b5f`.
- 원본 SRT `71-100/youtube-transcript-mRRev963GaA.srt` **2,063개(번호연속) / 157,457 bytes / raw SHA-256 `eccfbf426105e0873af73c2f38ec470de0ed8b35096e17aef6b190845a34f99a`**, 등록부 일치. 마지막 자막 `01:09:27.157~01:09:29.177`.
- **원본 공백 제거 전문 26,628자** SHA `417a8b73d81bc67b2b70c7d7c99691d5613df8d65afa6c56370e40448afd879a`, 별도로 확보한 유튜브 공개 한국어 자동전사 **26,624자** SHA `3738665c069c048d4b1178ca9a74276eecb348486c8597e7ab0e22ef20f0f8b6` 차이가 있었음.
- 원본 SRT 마지막 #2062·#2063 두 큐는 중복된 **비언어 `[음악]`** 표기. **원본을 건드리지 않고 비교할 때만 마지막 #2063 한 개 토큰 4자 제외**, 공백 제거 **26,624자 SHA `3738665c069c048d4b1178ca9a74276eecb348486c8597e7ab0e22ef20f0f8b6`이 공개 전사 전문과 완전 일치**. 나머지 자막 본문에 차이 없음. 이 결과는 **자동전사 본문 일치**이지 음성 파일 재청취나 영상프레임 인증이 아님.
- 기존 33항목 중 **32건 화자 발언·표현은 개인 SRT cue 번호/밀리초 시각**으로 정확히 재배치. **1건(18번)**은 영상에서 화자가 하지 않은 규제상의 주의사항으로 시각 없이 `RESEARCHER_CONTEXT_NOT_IN_VIDEO` 명시.

## 2. 중요한 사실 정정 · 이전 잠정 분석 자체의 오류

1. **ChatGPT가 '2024년 정도에 나왔다'는 발언** 원본 **#330, 00:11:04.399**. OpenAI [최초 공개 공식 발표](https://openai.com/index/chatgpt/)는 **2022-11-30**이므로 정확한 출시연도 주장은 **CONTRADICTED**. 2024년경 AI가 보급·체감되었다는 뉘앙스는 별도 해석 가능하나 '처음 공개' 연도로 쓰면 안 된다.
2. **구대륙 7 : 신대륙 3** 원본 **#1572, 00:53:17.440**. 진행자의 '10년 직장인 1억원' 가상 상황에 게스트가 말한 비율은 **기존 산업 70% : 신산업 30%**다. 이전 잠정안의 **'조선업 7 : 현대차그룹 3'은 발언을 잘못 좁힌 연구자 오류**이므로 명시적 정정. 조선업의 상대적 매력 평가는 별도 **#1598(00:54:14.280)** 이후 대화다.
3. **한국 제조업 로봇밀도 1,220대 / 근로자1만명**은 [IFR 2026-04 발표](https://ifr.org/ifr-press-releases/news/robot-density-surges-in-europe-asia-and-americas)의 **2024년 산업용 로봇 지표**. 영상 **#264, 00:08:43.440**은 로봇밀도가 높다는 일반적 언급이며 **1,220이라는 숫자를 강사가 직접 말하지는 않았다**. 휴머노이드 설치 통계도 아님.
4. **2027 상용화 전망의 현실 기준**: [현대자동차그룹 CES 2026 공식 계획](https://www.hyundaimotorgroup.com/en/news/hyundai-motor-group-announces-ai-robotics-strategy--to-lead-human-centered-robotics-era-at-ces-2026)은 Atlas 제조현장 **2028년 부품 시퀀싱·2030년 조립 공정 확대**를 목표로 명시. [Waymo 2026-02 공식 발표](https://waymo.com/blog/2026/02/waymo-raises-usd16-billion-investment-round/)는 당시 **주당 40만회 이상 완전자율 유료 운행**을 보고했다. 따라서 2027년에 모든 피지컬AI가 처음 상용화되거나 특정 국가·기업 수익률이 확정된다는 해석은 불가. 현대차 [모셔널 2026 로보택시 계획](https://www.hyundaimotorgroup.com/ko/story/hmg-tech-talent-forum-laura-major-level-4-autonomy)은 2026년말 라스베이거스 상용 무인운행 목표이며 2026-07의 후속 발표로 영상 당시 발언과 분리.
5. **배송 드론 규제 및 배송시장**: #805(00:27:04.640) 게스트가 내년 드론배송 가속화를 예상하지만 허가·운항·규제는 국가·지역별 사안이다. [미국 FAA](https://www.faa.gov/uas/advanced_operations/package_delivery_drone)는 상업배송을 면허·BVLOS 조건으로 명시한다. 해당 미국 자료만으로 한국 2027 규제 완화·주가 수혜가 공식 확정되는 것은 아니다.
6. **데이터센터 선박엔진 수주**: #1604(00:54:28.839) 이후 게스트 발언은 존재한다. 하지만 어떤 제조사의 2026년 계약·원금액·납기·마진인지 **원본 수주/공시 자료를 독립 조회하지 못했다**. `QUALIFIED` 유지하고 실제 수주 확정 투자신호로 활용하지 않는다.
7. **인터뷰의 협찬 도서**: 책 제목·저자 출연은 영상 원문에서, 출판사 제작지원·도서 판매 링크는 제작자 설명란에서 각각 확인. 후자의 홍보 메타데이터를 화자의 실시간 발언이나 책 예측·백테스트의 독립 성과 근거로 오인하지 않는다. 증권사별 이벤트/리워드 참여 규정은 분석 범위 밖.

## 3. 핵심 학습

- **구대륙/신대륙·문명 5단계는 저자의 교육상 비유이자 예측 프레임**이며 보편적 투자법/공식 산업분류/검증된 가격 법칙이 아니다. 투자하기 좋은 지점을 '건설 직전'으로 지정하더라도 이미 주가에 기대가 반영되거나 실패 확률과 경쟁이 남을 수 있다.
- 반도체·조선·방산·원전 및 로보틱스/자율주행·드론을 편입할 때 **산업 성장률, 상장기업 매출의 실현, 이익률, 가치평가, 포트폴리오 집중, 시점**을 각각 확인한다. '피지컬AI 상용화'와 '해당 회사 주가 상승'을 동의어로 사용하지 않는다.
- **언론 기사·실적 발표·재벌 총수 사건·파업의 과거 주가 영향**은 영상 후반 **#1808(01:00:59.680)** 및 **#1822(01:01:27.000)** 발언이다. 이전 잠정 목차 40분대에 뭉뚱그린 것은 잘못된 위치. 사건과 시장전체 변동·비교기업·배당조정·시간창·비용을 통제한 인과연구나 원본 수익률 백테스트는 완료하지 않았다. 기업/실적 공시는 [SEC 원문자료 가이드](https://www.investor.gov/introduction-investing/getting-started/researching-investments/using-edgar-research-investments)와 해당 한국 사업자 DART 등에서 확인해야 한다.
- **AI 도구 활용** 발언은 **#1874(01:03:05.440)**, **선크림/아이스크림 계절성 탐색**은 **#1917(01:04:34.440)**에 있다. 생성형 AI의 정확도·표본선택·계절성 수익은 별도 검증. [SEC 생성형 AI 사기경보](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/artificial-intelligence-fraud).
- **미검증**: 실제 코스피 1만 도달 시점/확률, 제시한 도서 수익률 백테스트 원본, 특정 선박엔진 업체 데이터센터 신규 수주액, 2027 전국 피지컬 AI 보급 속도, 영상의 원음과 시각 자료, 특정 투자자의 세후 수익률.

## 4. 원본 33항목 전체 개별 근거와 발언 귀속

| ID | 원본 SRT cue / 시작시각 | 기존 잠정 검토 취지(수정 포함, 의역) | 근거분류 | 공식자료·반례·조건 |
|---|---|---|---|---|
| 01 | #19 00:00:40.559 | '코스피 1만 투자지도'라는 게스트의 책과 투자전망을 다루는 광고 협찬 대담 | `PRIMARY_CONFIRMED` | 책 제목·게스트 초청은 #19. 유노북스 경제적 지원 사실은 원음이 아닌 제작자 설명란 표시로 검증; 책에 실린 수익률을 승인하지 않는다. [근거](https://www.youtube.com/watch?v=mRRev963GaA) |
| 02 | #77 00:02:27.680 | 2026년 코스피 1만은 성취 가능하고 지속 추세라는 견해 | `HYPOTHETICAL` | 게스트는 책 제목을 최초 2만으로 제안한 후 출판사 논의를 거쳐 1만으로 바꿨다고 서술. 특정 2026년 달성 사실 아닌 전망. [근거](https://www.goldmansachs.com/insights/articles/koreas-stock-market-is-forecast-to-set-fresh-highs) |
| 03 | #170 00:05:30.800 | 반도체·조선·방산·원전·2차전지 등을 구대륙으로 분류한다 | `HYPOTHETICAL` | 도서 저자 특유의 산업교육 비유. 한국거래소·법령의 공식 산업구분 아님 [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 04 | #179 00:05:48.039 | 로봇·자율주행·드론·우주·전고체전지 등은 신대륙으로 분류한다 | `HYPOTHETICAL` | 저자의 미래산업 서사적 분류로 검증된 자산군·수익률 분류가 아님 [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 05 | #202 00:06:40.680 | 제국·왕국·개척·탐험·건설·발전·번영 구분으로 산업 단계와 경쟁력을 설명 | `HYPOTHETICAL` | 비유적 단계. 제조성숙도/기술성숙도(TRL)와 직접 동일시 금지 [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 06 | #243 00:08:06.960 | 건설기 진입 직전이 모든 첨단산업의 최적 주식 매수 시점 | `QUALIFIED` | '건설기 직전 최적 투자'는 게스트의 투자시점 의견이며 기술경쟁/자금조달/증자/밸류에이션에 따라 달라지는 비보편적 가설. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 07 | #330 00:11:04.399 | 게스트가 ChatGPT가 2024년 무렵 처음 나왔다고 설명한 연도 오류 | `CONTRADICTED` | 원본 #330에서 ChatGPT가 '2024년 정도' 나왔다고 말함. OpenAI 최초 공개는 2022-11-30: 시점 오류 확정. [근거](https://openai.com/index/chatgpt/) |
| 08 | #336 00:11:19.279 | 화면 안 AI에서 피지컬 AI로 활용이 확장되는 추세 | `QUALIFIED` | 현대차 CES 2026 발표는 AI/로보틱스의 실제 산업 응용 계획을 설명. 기술 도입 속도/개별기업 투자 수익률은 보장하지 않음. [근거](https://www.hyundai.com/worldwide/en/brand-journal/mobility-solution/ces-2026-robotics-mediaday) |
| 09 | #341 00:11:33.040 | 2027년 피지컬AI 대량상용화·로봇·자율주행·드론 산업 확산은 게스트의 시장 전망 | `HYPOTHETICAL` | 2027 상용화는 미래 전망. Hyundai Atlas 공장 2028 sequencing/2030 assembly 일정과 구분하고 Waymo 2026 기존 완전자율 영업은 인정. [근거](https://www.hyundai.com/worldwide/en/newsroom/detail/0000001109) |
| 10 | #361 00:12:15.519 | 2000년 닷컴 초기 과열처럼 피지컬AI 관련 전 종목 상승장이 재현된다 | `HYPOTHETICAL` | 2000년 닷컴 과열을 미래 테마에 비유한 가설; 원본 2000년 종목 수익률·향후 전 종목 상승 추론은 재현되지 않았다. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 11 | #264 00:08:43.440 | 게스트는 한국의 높은 산업용 로봇 밀도를 설명한다(1만명당 1,220대는 영상에 없고 IFR 2024 제조업 통계로 연구자가 덧붙인 숫자) | `PRIMARY_CONFIRMED` | 원본 #264 한국의 로봇 밀도가 세계적으로 높다고 말할 뿐 1만명당 1220이라는 숫자는 말하지 않음; IFR 2024 제조업 1만명당 1220대 세계 최고는 연구자 별도 확인. [근거](https://ifr.org/ifr-press-releases/news/robot-density-surges-in-europe-asia-and-americas) |
| 12 | #428 00:14:26.720 | 테슬라·현대차가 휴머노이드 선두 2개 회사라는 평가 | `QUALIFIED` | 게스트의 현대차·테슬라 톱2 주관평가, 글로벌 정량 순위·평가지표 미확인. [근거](https://www.hyundai.com/worldwide/en/newsroom/detail/0000001109) |
| 13 | #437 00:14:42.279 | 현대차는 보스턴다이내믹스 기반 제조업용 휴머노이드 상용화를 추진 | `PRIMARY_CONFIRMED` | 현대차 보스턴다이내믹스·Atlas 기업전략은 현대차 공식 IR의 발표/계획이지 완료된 주식 수익률 아님. [근거](https://www.hyundaimotorgroup.com/en/news/hyundai-motor-group-announces-ai-robotics-strategy--to-lead-human-centered-robotics-era-at-ces-2026) |
| 14 | #419 00:14:08.440 | 게스트는 현대차 Atlas 사례로 2027년 피지컬AI 상용화 방향을 설명 | `QUALIFIED` | 영상의 2027 피지컬 AI 포괄적 전망과 현대차 공식 Atlas 순차 2028/2030년 사업 계획은 다름. [근거](https://www.hyundaimotorgroup.com/en/news/hyundai-motor-group-announces-ai-robotics-strategy--to-lead-human-centered-robotics-era-at-ces-2026) |
| 15 | #287 00:09:32.800 | 화자는 로봇 양산 기대가 주가에 선행할 수 있다는 의견을 제시하며, 미래 관련주 전부의 급등을 보장하지 않는다 | `HYPOTHETICAL` | 공장 신설/양산 직전 기대감이 최고인 기간이라는 개인 전략이며 모든 관련주 상승을 보장한다는 발언이 아님. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 16 | #730 00:24:31.279 | 2027년 자율주행 서비스의 추가 지역 확산 전망 | `QUALIFIED` | #730 2027 대중화 원년이라는 게스트 기대. Waymo는 이미 2026-02 주간 40만 건 이상 실제 운행 서비스 발표; 첫 상용화와 지역 확대 구분. [근거](https://waymo.com/blog/2026/02/waymo-raises-usd16-billion-investment-round/) |
| 17 | #593 00:19:57.799 | 현대차·테슬라 자율주행 개발 경쟁이 향후 큰 투자 테마 | `QUALIFIED` | #593 자동차그룹과 자율주행 신기술 경쟁. 사업화 수익률과 차량·지역별 무인운행 허가 여부는 개별 확인. [근거](https://waymo.com/blog/2026/02/waymo-raises-usd16-billion-investment-round/) |
| 18 | **영상 발언 없음 / 연구자 규제 보충** | 연구자 보충: 특정 지역 완전자율주행 실증이나 무인 서비스가 모든 국가·지역에서 자율주행을 무제한 허가한다는 뜻은 아니다 | `QUALIFIED` | 원본 화자 발언 아님. 연구자 규제 주의: 어떤 지역의 무인운행 사례도 타 지역/차량/사업자의 무제한 허가를 뜻하지 않음. [근거](https://waymo.com/blog/2026/02/ro-on-6th-gen-waymo-driver/) |
| 19 | #805 00:27:04.640 | 드론 배송은 2027년을 기점으로 일반 가정에 급속히 보급될 것 | `HYPOTHETICAL` | 게스트 #805 내년 드론배송 확산 예상. FAA의 면허·BVLOS 조건은 외국 사례, 한국 2027 보급 수치 검증 아님. [근거](https://www.faa.gov/uas/advanced_operations/package_delivery_drone) |
| 20 | #869 00:28:58.919 | 드론 시장 발전의 수혜주를 과거 테마와 유사하게 찾을 수 있다 | `QUALIFIED` | 게스트 한국 대단지 아파트 배송 효율성 가설; 입주자 수와 수혜 상장기업의 순이익·주가 실현은 다른 문제. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 21 | #983 00:32:58.760 | 미래산업 투자는 과거 산업순환·사이클 흐름을 참고한다 | `QUALIFIED` | 과거 산업사이클·AI 전력 병목을 전망 도구로 활용하나 유사 사건 가격 흐름은 자동 반복되지 않음. [근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/artificial-intelligence-fraud) |
| 22 | #1004 00:33:48.240 | 신대륙 신산업의 주식 가치보다 상용화 기대가 선행할 수 있다 | `QUALIFIED` | AI 오프라인 산업 진출 기대가 이미 주가에 반영됐는지는 독립 밸류에이션 검증 필요. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 23 | #1822 01:01:27.000 | 재벌총수 수감·기업파업 등 뉴스 충격을 과거 사례로 확인한다 | `QUALIFIED` | 기존 잠정 40분대는 잘못된 챕터. 실제 61분대 #1822 재벌총수 수감/석방 날짜와 차트 대조, #1879 파업 뉴스 대응. 역사적 상관을 인과로 확정 금지. [근거](https://www.investor.gov/introduction-investing/getting-started/researching-investments/using-edgar-research-investments) |
| 24 | #1808 01:00:59.680 | 실적이 좋으면 무조건 주가가 오른다는 고정관념을 검증할 필요 | `PRIMARY_CONFIRMED` | 기존 잠정 40분대는 잘못된 시각. 실제 #1808~1820 실적이 좋으면 주가 오른다는 가정을 의심하고 과거 발표 때 차트 비교. [근거](https://www.investor.gov/introduction-investing/getting-started/researching-investments/how-read-10-k) |
| 25 | #1458 00:49:32.880 | 사회초년생 투자도 기간·투입원금과 위험감내 수준에 맞게 설계해야 한다 | `PRIMARY_CONFIRMED` | #1458~1464 초보 직장인에게 적립식 지수 ETF 논의. 뒤이은 코스닥 정책 기대나 지수상승 보장과 구분. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 26 | #1572 00:53:17.440 | 1억원 가상 직장인 투자에서 구대륙 70%·신대륙 30%를 제안하며 구대륙 안에서는 조선을 상대적으로 선호 | `HYPOTHETICAL` | 원본 #1572 '구대륙7:신대륙3' 포트폴리오 구성; 잠정 원장 '조선7:현대차3'은 잘못된 재구성. 영상은 조선 선호 별도 제시. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 27 | #1604 00:54:28.839 | 화자는 선박용 중속엔진의 데이터센터 육상발전 수요 및 당시 수주 사례를 언급하며 조선업계 추가 기회로 전망한다 | `QUALIFIED` | #1604~1614 데이터센터 발전에 선박 엔진 이용 및 수주 사례 게스트 설명. 기업별 계약공시·수주금액·납기·실적 1차증빙 부족, 특정 발주 사례 자체 미확정. [근거](https://www.investor.gov/introduction-investing/investing-basics/glossary/corporate-reports) |
| 28 | #1668 00:56:31.200 | 아기 명의 1000만원 투자 계좌 장기보유와 미래산업 교육을 논의 | `HYPOTHETICAL` | #1668~1670 진행자가 자녀 명의 약 천만원 증여계좌 가정 제시, 실제 개인 증여세 신고/주식 매매와 관련 없는 시나리오. [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| 29 | #1705 00:57:40.000 | AI 때문에 한국 사교육이 사라지거나 새 형태로 교체될 것 | `HYPOTHETICAL` | #1705~1724 한국 사교육이 AI로 대체·전환 가능성을 논의한 주관적 예측이며 정책/교육시장 객관 전망으로 인증 불가. [근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/artificial-intelligence-fraud) |
| 30 | #1847 01:02:10.279 | 공시/과거 시계열로 뉴스 주장과 사건 전후 가격 움직임을 검증하는 습관 | `PRIMARY_CONFIRMED` | #1847~1849 사건 뉴스와 주가 과거기록 직접 조사. 정식 백테스트나 인과 추정 재현한 것은 아님. [근거](https://www.investor.gov/introduction-investing/getting-started/researching-investments/using-edgar-research-investments) |
| 31 | #1874 01:03:05.440 | AI 도구로 과거 시계열 정보와 사건 사례를 손쉽게 찾아 투자에 활용할 수 있다 | `PRIMARY_CONFIRMED` | #1874~1894 AI를 통한 데이터 검색 용이성 설명; 생성 AI 결과는 SEC·원천 공시로 재검증 필요. [근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/artificial-intelligence-fraud) |
| 32 | #1917 01:04:34.440 | 화자는 여름 기온예보를 계기로 선크림·아이스크림 기업의 과거 주가를 찾아보는 탐색 습관을 제안한다 | `HYPOTHETICAL` | #1917~1942 선크림/아이스크림·날씨 테마 아이디어 탐색 제안, 백테스트 수익률은 미검증. [근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/artificial-intelligence-fraud) |
| 33 | #1996 01:07:06.200 | 게스트의 코스피1만 전망과 산업 지도에 관한 정량적 설명은 협찬 도서에 추가되어 있다고 안내한다 | `QUALIFIED` | #1995~2001 게스트 저서에 상세 자료/수치가 있다고 안내. 책 원문·원시데이터 및 성과는 연구에서 재현하지 않았음. [근거](https://www.youtube.com/watch?v=mRRev963GaA) |

**분류 합계:** PRIMARY_CONFIRMED **7**, QUALIFIED **13**, CONTRADICTED **1**, HYPOTHETICAL **12** = **33건**. 지수 1만과 2027 기술/주가 시나리오를 사실 확정으로 승인하지 않음.

## 5. 정식 승인 범위

- **원본 SRT 전체의 바이트 SHA·자막번호·발언본문+공개전사 SHA**, 32개 발언의 **원본 cue 시작시각**, 개별 공식 출처·제한조건·정정을 완료한 *교육 콘텐츠 학습*만 승인.
- 연구자 규제 보충 1건은 별도 역할·비영상 시간 태그로 기록. 구체 상장기업 미래수익, 도서 백테스트 원본, 원음·영상 프레임, 개인별 투자 적합성의 승인은 아님.
- 2026-05 영상의 예상과 **2026-07/09/10 자료상 사후 확정된 기업 계획**은 구분한다. 비공개 ZIP/SRT 전문을 GitHub에 공개하지 않는다.
- 기존 잠정 보고서/33개 주장 정렬은 보존하되 #79를 승인하면 기존 잠정 분모에서 **33건을 이동**, 새로운 33건으로 이중계산하지 않는다.

참조: [개별 주장·원본 시간·증거 pilot](../data/subtitles/pilots/mRRev963GaA.json) · [V3 정식분석](../data/analysis_events/mRRev963GaA.json) · [검증 등록부](../data/subtitles/registry_71_100_20261013.json).
