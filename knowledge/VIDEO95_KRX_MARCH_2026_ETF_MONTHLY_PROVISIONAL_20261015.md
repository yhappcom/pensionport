# 박곰희TV #95 — 868개 원본 SRT·공개 한국어 전사 전수 대조 및 KRX 공식 월보 검증 완료

**검토일:** 2026-10-15 · **영상:** [최근에 가장 핫했던 ETF는 과연?](https://www.youtube.com/watch?v=HvXLItCOd-A) · 촬영 2026-04-08 · 공개 2026-04-22 · 원본 끝 00:27:35.720 · **정식 V3 승인:** [data/analysis_events/HvXLItCOd-A.json](../data/analysis_events/HvXLItCOd-A.json)

## 1. 사용자 제공 71-100.zip 원본 출처 검증 — 모든 필수 단계 완료

이번 채팅 사용자가 직접 업로드한 비공개 `71-100.zip` 원본을 다시 읽어 압축 전체 CRC 검사·원본 SRT 구조 및 등록 SHA를 **독립 재계산**했다. **원본 ZIP 및 자막 전문은 GitHub에 업로드하지 않으며 메타데이터·판정만 공개한다.**

| 항목 | 실제 독립 확인 값 |
|---|---|
| ZIP 이름 | `71-100.zip`; CRC 전수 테스트 `PASS` |
| ZIP SHA256 | `69be8639162f8e00bfa09f0d4b8a6fe95db0a07054ad370709ce0d4e53628b5f` |
| #95 원본 파일 | `71-100/youtube-transcript-HvXLItCOd-A.srt` |
| #95 SRT 크기 | **65,094바이트** |
| #95 원본 SHA256 | `89aa974c052fdde2d56ff2e1d4c353968e195fbd4ad359bc0a9c59f20995689a` — 등록부와 **동일** |
| 번호·시각 구조 | **1~868 연속 유효 SRT 큐**, 총 **868개** |
| 원본 마지막 시각 | **00:27:35.720** |
| 큐 본문 결합 텍스트 SHA256 (UTF-8) | `839065095394489edfa24927a2bb98f7ba5b443c2d52f8d599280632359ae065` |
| 공개 유튜브 한국어 전사 전문 SHA256 (UTF-8) | **동일** `839065095394489edfa24927a2bb98f7ba5b443c2d52f8d599280632359ae065` |
| 원문/공개텍스트 차이 | **0/868줄** — 길이 **15,488문자/868행**, 전체 순서 그대로 |
| 청각/화면 독립검증 | **미실시**. *원본·공개 전사가 같다는 사실은 원음 자체를 청취했다는 뜻이 아니다.* |
| 정밀 타임코드 | 사용자 원본 각 큐 시작 시각을 사용하며, 공개 HTML 전사에는 타임스탬프가 없어 공개 자막과 **시간 차이**를 따로 계산할 수는 없음 |

**중요한 경계:** 원본 SRT는 사용자가 제공한 자동 전사 파일이다. 공개 유튜브 자동전사가 동일한 생성원에서 왔을 수 있으므로 **전사 텍스트의 동일성은 확정**했지만 녹음의 발음오류나 화면 표기가 음성/영상 재확인 없이 모두 정확하다고 확언하지 않는다. 36개 검토 항목 중 원본 영상 외 **연구자가 추가한 역사적 맥락 1건**은 직접발언으로 인정하지 않았다. 별도 **연구자 설명·계산·오해방지 6건**에도 오귀속 경고를 붙였다.

## 2. 공식 한국거래소 ETF 통계의 기간·단위 확인

- **[KRX 2026년4월호 제178호 공식 원본](https://m.blog.naver.com/happy_krx/224247522508)**은 **2026년 3월31일 말 기준** 숫자다. 게시 2026-04-10. 3월19일 게시된 2026년3월호 제177호는 **3월말 자료가 아님**.
- **[KRX 2026년1월호 제175호 공식 원본](https://m.blog.naver.com/happy_krx/224151836839)**은 **2025년 12월31일 말 기준** 연간 실적 자료다.
- 두 공식 블로그 게시물의 첨부 PDF에서 관련 표를 직접 텍스트 추출·행/열 확인. 선택된 **18개 정량 지표** 교차검증. **PDF 바이너리 자체 SHA256 독립검증까지 수행했다는 주장은 하지 않는다**.

| 주제 | 영상 내 근사 설명 | 동기간 KRX 원표 |
|---|---|---|
| 2026년3월 ETF 순자산 | 약360조원 | **3,607,045억원 = 360조7,045억원** |
| 2026년3월 ETF 종목수 | 1,084개 | **1,084개** |
| KODEX 200 순자산 | 약16조 | **161,040억원 = 16조1,040억원** |
| TIGER 미국S&P500 순자산 | 약14.6조 | **146,553억원 = 14조6,553억원** |
| 국내주식형 | 약150조 | **1,475,862억원 = 147조5,862억원** |
| 해외주식형 | 약100조 | **997,380억원 = 99조7,380억원** |
| 국내채권형 | 약50조 | **493,230억원 = 49조3,230억원** |
| 해외채권형 | 약10조 | **97,558억원 = 9조7,558억원** |
| 2026년3월 ETF 평균수익률 | 약−7% | **−7.43% (상승217/보합2/하락849)** |
| 2026년1~3월 ETF 평균수익률 | 약+6.7% | **+6.72% (상승654/보합6/하락392)** |
| 2025년 ETF 평균수익률 | 약+34% | **+34.22% (상승727/보합1/하락157)** |
| 2025년 반도체 TOP10 레버리지 | 약+307% | **+307.1% (TIGER)** |
| 2025년 200선물인버스2X | 약−76% | **−76.2% (TIGER·KODEX)** |

ETN까지 포함한 2026년3월 ETF·ETN 전체 자산총액은 **약381.3조원**이므로 ETF만의 **360.7045조원**과 구별한다. 자산총액 증가는 가격·환율·설정/환매·분배 등의 영향을 받으며 **시장순유입액이나 개인 신규매수와 자동으로 동일하지 않다**.

**KRX 2026년3월 수익 상위/하위 실례:** KODEX WTI원유선물(H) **+61.5%**, TIGER 원유선물Enhanced(H) **+57.7%**, RISE 200선물인버스2X **+35.4%**; TIGER 200IT레버리지 **−44.9%**, TIGER 반도체TOP10레버리지 **−41.5%**, KODEX 레버리지 **−40.2%**. 자료는 당시 **1개월 과거 수익률**이지 현 시점 투자권유가 아니다. ETF 수익률 집계의 대상에는 기간 신규상장·상폐 상품 제외 조건이 있다.

## 3. 원본 발언에 대한 역사적 오류 정정 — ETF 세계 최초

영상 **SRT 323~326번 / 00:09:57~00:10:05**에서 진행자는 **SPY를 지역 구분 없이 최초 ETF처럼** 소개한다. 이 표현을 **세계 최초로 이해하면 역사적으로 틀리다.**

- [토론토증권거래소(TMX/TSX)의 공식 2015년 발표](https://www.tsx.com/en/news?id=216&year=2015)에 따르면 **캐나다 Toronto 35 Index Participation Units(TIPs)**는 **1990년** 토론토거래소에서 상장된 세계 최초 ETF 선행상품.
- [SPY 운용사 State Street 공식 설명](https://www.ssga.com/us/en/institutional/capabilities/spdr-core-equity-etfs/spy-sp-500)은 **1993-01-22 SPY가 미국 최초 거래소상장 ETF**임을 확인.
- 따라서 `HvXLItCOd-A-11` 판정은 `PRIMARY_CONFIRMED`→**`CONTRADICTED`**로 수정하고, '미국 최초 SPY(1993)'는 사실이지만 '세계 최초 SPY'로 확대하면 오류라고 교육자료에 구별한다. 한국 ETF **2002년 최초 상장**은 국내시장 별개 연혁이다.

## 4. 기존 36개 주장 — 모든 큐 번호와 정확한 원본 시작시간 재기록

**전체 36개 교육 검토항목: 확인 24 / 조건부 10 / 반증 1 / 미래의견 1.** 정확한 타임코드는 원본 SRT 해당 **큐 시작점**이며 발화한 단어의 최초 음성밀리초 인증은 아니다. **외부 연구자 설명은 강사의 문자 발언으로 잘못 인용하지 않는다**. `source_utterance_match_status`와 `claim_role`을 이용해 역할 구분.

| 주장 ID | 원본 큐·시각 | 발언 또는 교육 범위(의역) | 역할 | 분류·확인근거 |
|---|---|---|---|---|
| `01` | `#28` 00:00:52.079 | 영상이 KRX ETF·ETN Monthly 2026년 3월말 자료를 토대로 시장을 설명한다 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp) |
| `02` | `#42` 00:01:21.360 | 2026년3월말 국내 ETF 순자산 360조원이라는 영상의 근사 수치 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `03` | `#82` 00:02:29.680 | 2026년3월 ETF 종목수 약 1,084개라는 수치 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `04` | 영상 내 직접 발언 없음 | 원본 영상 외에 연구자가 추가한 2025년3월말 KRX ETF 시장 규모·종목수 비교 역사자료 | `RESEARCHER_EXTERNAL_HISTORICAL_CONTEXT_NOT_VIDEO_CLAIM` | **PRIMARY_CONFIRMED** · [주근거](https://t1.daumcdn.net/brunch/service/user/gNua/file/LeWaiDLUQM-CgNapLlCfPWegWZE.pdf) |
| `05` | `#105` 00:03:10.640 | 순자산이 큰 ETF 1위 KODEX200 약16조원이라는 2026년3월 순위 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `06` | `#116` 00:03:32.840 | TIGER 미국S&P500 약14.6조원이 2026년3월말 상위라는 주장 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `07` | `#195` 00:05:53.360 | TIGER 반도체TOP10이 2026년3월 순자산 상위 종목이라는 소개 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `08` | `#279` 00:08:36.320 | ETF 순자산가치총액을 일반주식 시가총액과 '비슷하게 보면 된다'고 한 진행자의 입문적 비유 | `SPEAKER_EXPLICIT_APPROXIMATE_ANALOGY_NOT_EXACT_IDENTITY` | **QUALIFIED** · [주근거](https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-2) |
| `09` | `#292` 00:08:59.720 | 대한민국 ETF 최초 상장 2002년 10월14일 | `SPEAKER_YEAR_WITH_INDEPENDENT_DAY_DATE` | **PRIMARY_CONFIRMED** · [주근거](https://www.samsungfund.com/upload/kodex/newsroom/20250722174437650.pdf) |
| `10` | `#304` 00:09:21.000 | 첫 상장 4개 ETF는 KOSPI200와 KOSPI50 추종상품이며 두 운용사에서 출시 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **QUALIFIED** · [주근거](https://www.samsungfund.com/upload/kodex/newsroom/20250722174437650.pdf) |
| `11` | `#323` 00:09:57.440 | 진행자가 ETF 역사 설명에서 SPY를 '최초의 ETF'라고 소개한 직접발언(지역 한정 없이 세계 최초처럼 언급) | `SPEAKER_WORLD_FIRST_ERROR_SCOPE_CHECK` | **CONTRADICTED** · [주근거](https://www.tsx.com/en/news?id=216&year=2015) |
| `12` | `#398` 00:12:26.519 | 패시브 ETF 성장에는 낮은 비용·지수추종·퇴직연금 장기저축 수요가 기여했다는 화자 해석 | `SPEAKER_CAUSAL_OPINION_NOT_ECONOMETRIC_PROOF` | **QUALIFIED** · [주근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `13` | `#174` 00:05:15.520 | 미국 S&P500 선물형 ETF는 증거금으로 지수노출을 얻고 미사용현금을 별도로 운용 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-2) |
| `14` | `#158` 00:04:47.199 | 국내 IRP 퇴직연금계좌에서는 일반적인 선물형/레버리지 ETF 편입이 제한돼 현물 ETF 선호가 강화 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **QUALIFIED** · [주근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `15` | `#274` 00:08:25.280 | ETF 종목 증가와 순자산 증가는 서로 다른 측정값 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp) |
| `16` | `#424` 00:13:23.279 | 2026년3월말 ETF 유형 국내주식형 약150조원·해외주식형 약100조원 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `17` | `#438` 00:13:52.560 | 2026년3월말 국내채권형 ETF 약50조원·해외채권형 약10조원 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `18` | `#427` 00:13:27.839 | 국내 주식형 ETF 순자산이 해외 주식형 ETF보다 커졌다는 영상 설명과 연구자의 인과관계 경계 | `SPEAKER_DOMESTIC_OVERSEAS_AUM_OBSERVATION_RESEARCH_CAUSAL_CAUTION` | **QUALIFIED** · [주근거](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp) |
| `19` | `#492` 00:15:31.120 | CD금리액티브/머니마켓 금리형 ETF를 대기자금 파킹으로 활용 가능 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **QUALIFIED** · [주근거](https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-2) |
| `20` | `#495` 00:15:37.480 | 금리형 ETF가 대기자금 보관 수단으로 소개된 발언에 대한 연구자의 별도 결제/출금 위험 경고 | `RESEARCHER_LIQUIDITY_SETTLEMENT_RISK_NOT_SPOKEN` | **QUALIFIED** · [주근거](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp) |
| `21` | `#565` 00:17:51.720 | RISE 삼성전자SK하이닉스채권혼합50은 50%가 채권이고 개별 반도체 두 회사에 지분 노출 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **QUALIFIED** · [주근거](https://kind.krx.co.kr/disclosure/disclosurebystocktype.do?method=searchDisclosureByStockTypeEtf) |
| `22` | `#631` 00:19:49.039 | 국내상장 레버리지/인버스 ETF는 투자지수가 단기 목표로 움직이면 큰 수익·손실 발생 가능 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `23` | `#561` 00:17:43.559 | 진행자가 2026년3월 '순자산 증가 ETF 상위'를 투자자가 많이 선택한 종목으로 해석한 구두 설명 | `SPEAKER_INFERS_INVESTOR_CHOICES_FROM_AUM_CHANGE` | **QUALIFIED** · [주근거](https://data.krx.co.kr/contents/MDC/EASY/main/MDCEASY008.jsp) |
| `24` | `#681` 00:21:17.360 | 2026년4월 영상에서 진행자가 리츠 시장을 '개인적으로 사기 좋은 시점'이라고 평가한 시장 전망 | `SPEAKER_MARKET_OPINION_NOT_GUARANTEED_PROFIT` | **HYPOTHETICAL** · [주근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `25` | `#711` 00:22:14.120 | 2026년3월 ETF 전체 월평균 수익률 약 -7%, 하락849개·상승 약200개 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `26` | `#719` 00:22:31.240 | 2026년3월 원유선물형 ETF 월 수익률 상위 최대60% 내외·인버스 약30% | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `27` | `#749` 00:23:30.640 | 2026년3월 레버리지 반도체 ETF 중 -40% 내외 손실이 있었다는 예시 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `28` | `#633` 00:19:51.960 | 영상의 '+10 -10' 변동성 설명을 연구자가 기초지수 연속 두 날 +10%/−10%로 구체화한 산식 | `RESEARCHER_EXPLICIT_CALCULATION_FROM_SPEAKER_10_10_EXAMPLE` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `29` | `#633` 00:19:51.960 | 영상의 '+10 -10' 변동성 예시를 연구자가 '일간 2배 ETF +20%/−20%'로 보강한 산식 | `RESEARCHER_EXPLICIT_CALCULATION_FROM_SPEAKER_10_10_EXAMPLE` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `30` | `#645` 00:20:11.520 | 영상의 변동성 훼손 설명을 무조건적 '레버리지/인버스가 언제나 손해'로 읽지 않도록 한 연구자 보완 경고 | `RESEARCHER_BOUNDED_WARNING_NOT_A_SPEAKER_ALL_CASES_ASSERTION` | **QUALIFIED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `31` | `#650` 00:20:22.080 | 원금50% 하락 후 원금복귀에는 저점 대비100% 상승 필요 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `32` | `#809` 00:25:29.120 | 2026년 1~3월 ETF 평균 수익률 약 +6.7%라는 영상 수치 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224247522508) |
| `33` | `#817` 00:25:45.600 | 2025년 전체 ETF 평균 수익률 약+34%라는 영상 수치 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224151836839) |
| `34` | `#825` 00:26:02.200 | 2025년 일부 레버리지 ETF 연간+307%·일부 인버스 ETF -76% 사례 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://m.blog.naver.com/happy_krx/224151836839) |
| `35` | `#768` 00:24:07.440 | 인버스/레버리지 일시적 수익이 가능해도 초보 장기연금 포트의 안정 수익으로 취급할 수 없다 | `VIDEO_SOURCE_BACKED_SPEAKER_STATEMENT` | **PRIMARY_CONFIRMED** · [주근거](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) |
| `36` | `#711` 00:22:14.120 | 영상의 3월 ETF 평균 마이너스·원유·인버스 ETF 양의 수익률 통계에서 연구자가 정리한 수익률 분포의 차이 | `RESEARCHER_GENERAL_DISTRIBUTION_INFERENCE_FROM_SOURCE` | **PRIMARY_CONFIRMED** · [주근거](https://m.krx.co.kr/contents/02/0204/020401/JHPETP020401M01.jsp) |

일간 레버리지 ETF의 **기초지수 +10% 후 −10% ⇒ 누적 −1%**, ETF **일간2배 +20% 후 −20% ⇒ 누적 −4%**는 수수료·오차를 제외한 **연구자가 추가한 수학적 검증**이다. 영상의 `#633~646` 큐에는 `+10 -10`·변동성 훼손 개념이 있으나 **정확히 −1%/−4%를 화자가 발언한 것은 아니다**. [SEC 일간 레버리지 ETF 투자자경고](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec)와 별도 대조.

원문 `#681~694`의 리츠 의견도 **진행자의 개인적 매수 시기 평가**이지 '반드시 고수익 보장'이라는 직접 보증은 아니다. 원문 `#560~564`에서 순자산 증가와 '선택'을 연결하지만, **AUM 증가≠실제 투자자 순매수** 경고는 분석자가 부가한 결론이다.

## 5. 승인 상태와 남은 한계

**정식 V3 근거 범위 승인**: `data/analysis_events/HvXLItCOd-A.json` (**36건**), SHA 검증 및 원본 전수 텍스트 비교를 완료. 원본 음성 재청취·영상 화면/표 프레임과의 독립 대조, 금융상품의 당시 모든 문서/법적 적격성은 별도 미완료이므로 범위 밖을 검증했다고 표시하지 않는다.

[원본 SRT·공개텍스트 검증 주장 원장](../data/subtitles/pilots/HvXLItCOd-A.json) · [KRX 18개 지표 감사 JSON](../data/subtitles/video95_krx_monthly_primary_audit_20261015.json) · [V3 정식 이벤트](../data/analysis_events/HvXLItCOd-A.json).

**사용자 원본 SRT 및 ZIP 내용은 GitHub에 비공개로 유지한다.** `main` 브랜치는 수정하지 않는다.
