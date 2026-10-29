# 박곰희TV #181~185 비공개 원본 자막·공식 근거 V3 검증 보고 (2026-10-27)

**정식 검증 범위:** 5편 / 총 3,959개 원본 한국어 SRT cue / 304,346 원본 SRT bytes / 주장 84개. 각 원본 SRT SHA-256은 독립 로스터 및 원본 ZIP SHA256과 대조해 고정했다. **판정:** PRIMARY_CONFIRMED 18건, QUALIFIED 46건, CONTRADICTED 5건, HYPOTHETICAL 13건, SPEAKER_OPINION 2건. 정식 V3은 주장별 교육 지식 심사와 정정 기록 승인으로, 화자의 원음·화면·개인계좌·2025년 상품 금리표 또는 미래수익률 인증은 아니다.

## 1. 자료 출처·범위

- 비공개 사용자 소스: Google Drive `박곰희TV_SRT_원본보관함/101-200.zip` (Drive id `1izqktxhhndKSfqrKAJo_aACrx_O0Mt50`), 전체 ZIP SHA-256 `ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e`. 이 연구 배치의 다섯 원본 `data/subtitles/registry_181_185_20261027.json`에 cue·byte·각 파일 SHA 고정.
- 영상은 2025-11-09~2025-11-19 게시. 2026-10-27 현재의 퇴직급여법·예금자보호·국민연금 제도와 영상 당시 상황을 구분. 원본 실제 음성/프레임과 공개 동일 영상 한국어 자막 본문 전문의 독립 2차 대조는 수행하지 않음.
- 개인정보·가계 명세·실제 증권계좌·영상 화면 금리표는 제공되지 않았으며, 원본 SRT/ZIP 파일은 GitHub에 업로드하지 않음.

## 2. **우선 핵심 정정 ① #181 임금피크·퇴직급여**

**원본 기준:** `N0ZLjtGbHX4` cue #7 [00:00:12.920] 중간정산 필수 권유 → **CONTRADICTED**. cue #20 [00:00:44.000] DB→DC 필수 전환 권유 → **CONTRADICTED**.

- 「근로자퇴직급여 보장법」 제8조 제2항은 퇴직금 중간정산에 법정 사유·근로자 신청이 필요하고 사용자가 '지급할 수 있다'고 규정한다. 임금피크를 앞두었다고 근로자 누구나 무조건 중간정산이 의무·자동 허용되는 것이 아니다. [법령 원문](https://www.law.go.kr/lsInfoP.do?lsId=009883)
- 같은 법 제4조 제3항 및 고용노동부 상담에 따르면 DB/DC 제도의 도입과 변경은 회사·근로자대표 동의·사업장 규약에 의존한다. 회사가 해당 두 제도를 운영하지 않으면 개인이 즉시 전환할 수도 없다. [고용노동부 공식 상담](https://1350.moel.go.kr/rtmview.do?id=1000261136&page=1&type=ALL)
- **정정 및 활용:** 임금피크 전 중간정산/DB→DC는 사업장 적용규약·중간정산 사유·개인 세금·퇴직연금 운용능력을 확인해 필요시 비교한다. 개인별 보편 권고 금지. IRP '1만원 연금 수령신청'도 조건에 따라 세금감면 기산이 달라 일률적 자동 이익 단정 금지.

## 3. **우선 핵심 정정 ② #182 RP·CMA·발행어음의 원금위험**

**원본 기준:** `UKDhdcn3AUk` cue #215 [00:06:34.639] RP 원금손실 거의 불가능 → **CONTRADICTED**. cue #251 [00:07:38.919] 국가부도 수준에만 RP 원금손실 발생 → **CONTRADICTED**. cue #569 [00:17:39.919] MMF 기관간 거래이므로 걱정할 위험이 없음 → **CONTRADICTED**.

- 일반 증권사 **RP형·발행어음형·MMF형·MMW형 CMA는 예금자보호 비대상**으로, RP는 담보채권이 있더라도 지급상대방 신용·담보시가·회수지연, 발행어음은 증권사 신용, MMF/MMW는 운용자산 위험이 존재. [한국투자증권 CMA 위험안내](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) / [한국투자증권 MMF형 CMA 설명서](https://file.koreainvestment.com/Storage/customer/guide/regards/%EC%84%A4%EB%AA%85%EC%84%9C70%ED%98%B8.MMF%ED%98%95CMA%EC%84%A4%EB%AA%85%EC%84%9C.pdf).
- **예외:** 법정 보호대상인 종금형 CMA 등 일부 적격 예금은 보호될 수 있다. 2025-09-01부터 보호 대상 금융회사별 1인당 원리금 1억원으로 상향된 한도는 예금자보호 *대상 상품에만* 적용하며 RP·발행어음·MMF 등 증권성 상품을 자동 보호하지 않는다. [금융위원회 보호한도 공식 고시](https://www.fsc.go.kr/po010106/85200).
- 원화 RP 연 2.25~4.2%, 달러 RP 약3.65%, 발행어음 연3.4% 등 **2025년 영상 특판 금리 원표·모집기간/개인별 요건 미확보**: 공식 금리·수익확정으로 사용금지, 2026 현재 금리표로 재활용 금지.

## 4. **우선 핵심 정정 ③ #185 2026 국민연금 개정 적용연도**

**원본 기준:** `V7H65oaoflo` cue #135 [00:04:55.560] 2026년 소득대체율 43% 인상 → **QUALIFIED(수치 및 시행 사실 확인; 적용기간 명시)**.

- 국민연금 보험료율 2025년 9%, **2026년 9.5%**, 매년 0.5%p 단계적 인상으로 **2033년 13%**. 명목 소득대체율은 2025년 41.5% → **2026년 43%**. [국민연금공단 개혁 FAQ](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do).
- 43% 개정률은 **2026-01-01 이후 가입기간**에만 적용. 2025-12-31까지의 가입기간에는 종전 규정이 적용되고, 현재 이미 연금을 수령하는 사람에게도 소급 적용되지 않음. 소득대체율 43%는 개인 생활비의 43%를 자동지급한다는 뜻도 아니며 가입기간·소득이력에 따라 연금액이 달라진다. [보건복지부 2025년 개혁 안내](https://www.mohw.go.kr/menu.es?mid=a10714060000).
- 장기투자의 20% 상승 뒤 10% 하락은 **+8%**, 10% 상승 연속 두 회는 **+21%**. 개인연금 3억원에 월100~200만원 현금분배를 가정한 예시는 연4~8% 분배율에 해당하나 실제 원금·총수익·분배액은 보장 불가.

## 5. 배치별 판정·주요 이슈

| 영상 | 원본 cue | 교육 주장 | 확정 | 조건부 | 반증 | 가정 | 의견 | 대표 활용 제한 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| #181 | 32 | 9 | 0 | 7 | 2 | 0 | 0 | 중간정산/DB→DC 보편 의무 권고 금지 |
| #182 | 1495 | 23 | 9 | 8 | 3 | 3 | 0 | 2025 특판금리·RP 무손실 주장 금지 |
| #183 | 948 | 14 | 1 | 9 | 0 | 3 | 1 | 구독자 부부 실제 소득·계좌 미검증 |
| #184 | 528 | 15 | 2 | 11 | 0 | 2 | 0 | 사회초년생 사적 잔고·월배당 총수익 미검증 |
| #185 | 956 | 23 | 6 | 11 | 0 | 5 | 1 | 43% 소급적용 금지, 개인연금3억원 월분배 보장 금지 |
| **합계** | **3,959** | **84** | **18** | **46** | **5** | **13** | **2** | **원본·공식자료 주장별 판정** |

## 6. 전체 84건 원본 자막 cue·시간코드·공식자료 근거

원본 텍스트 전문은 비공개 보존. 각 `claim_id`는 `data/subtitles/pilots/<video>.json#claims[*].verification_evidence`의 검증 증빙, `data/analysis_events/<video>.json#core_claims`의 정식 교육 분석 주장과 일치하며, 요약 의역으로 표시한다. 각 링크는 일반 제도/교육 원리를 입증하며, 개인 계좌 잔고나 영상 속 실제 특판 상품원표 인증이 아님.

### #181 임금피크제 퇴직금 중간정산과 DB·DC 전환 — Shorts (9건)

| claim_id / cue | 영상 시간 | 판정 | 주장 내용 의역 | 공식 근거와 정정·한계 | URL |
|---|---|---|---|---|---|
| `N0ZLjtGbHX4-01` / 3 | 00:00:04.200 | QUALIFIED | 임금피크제 후 평균임금 감소로 일부 DB/퇴직금제 수급액이 감소할 수 있다 | 평균임금 중심 산식에는 위험이 있으나 사업장 별 퇴직급여 산정 보전조치와 근로계약 규약에 따른 예외. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `N0ZLjtGbHX4-02` / 7 | 00:00:12.920 | CONTRADICTED | 퇴직금제 근로자는 임금피크 이전 퇴직금 중간정산을 반드시 해야 한다 | 퇴직급여법 제8조제2항은 법정 사유가 있을 때 중간정산해 지급할 수 있다고 정함. 근로자의 신청으로 의무 지급되지 않으며 자금 사용·과세 유불리 개별 검토. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `N0ZLjtGbHX4-03` / 9 | 00:00:18.600 | QUALIFIED | 퇴직금은 퇴직 직전 3개월 평균임금 × 근속연수로 계산한다 | 실제 법정 기준은 계속근로 1년당 30일분 이상 평균임금. 3개월 산정과 상여·수당 등 평균임금 구성 및 산입기간의 개별 적용이 필요. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `N0ZLjtGbHX4-04` / 14 | 00:00:30.040 | QUALIFIED | 급여가 높을 때 중간정산 뒤 IRP로 옮겨 두면 미래 퇴직급여를 방어할 수 있다 | 법정 사유·사용자 동의·이전 가능 퇴직급여 원천·중간정산 세제와 투자손실 위험 전제가 있어 보편적 무조건 이득은 아님. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `N0ZLjtGbHX4-05` / 15 | 00:00:33.640 | QUALIFIED | IRP에 1만원 연금수령 신청만 하면 퇴직소득세 감면연차가 자동으로 시작된다 | 적격 연금수령 나이·계좌·연금수령한도·기산시점 확인을 생략한 단정. 1만원 신청만으로 전원 감면 보장은 불가. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `N0ZLjtGbHX4-06` / 20 | 00:00:44.000 | CONTRADICTED | 임금피크제 전에 DB형 가입자는 반드시 DC형으로 전환해야 한다 | 퇴직급여법 제4조제3항 및 고용부 유권상담: 회사 퇴직연금제도 도입/전환은 근로자대표 동의 등 절차가 필요. 개인의 의무가 아니며 반드시 허용되지도 않는다. | [근거](https://1350.moel.go.kr/rtmview.do?id=1000261136&page=1&type=ALL) |
| `N0ZLjtGbHX4-07` / 22 | 00:00:49.039 | QUALIFIED | DB에서 DC로 변경 시 높은 급여 시점의 과거 근속분을 확정할 수 있다 | 허용된 회사 규약·이전 적립금 산정방식에 따라 가능하지만 특정 높은 급여 산식이 모든 근로자에 자동 적용된다고 볼 수 없음. | [근거](https://www.kcie.or.kr/guide/22/28/web_view?content_idx=916) |
| `N0ZLjtGbHX4-08` / 26 | 00:00:57.080 | QUALIFIED | DB형 과거 적립분은 전환 시 무조건 DC계좌에 일괄 이전된다 | 과거근로기간 인정, 적립금 이관 여부와 계산법은 사전에 합의된 퇴직연금규약의 구체적 내용에 좌우. | [근거](https://1350.moel.go.kr/rtmview.do?id=1000261136&page=1&type=ALL) |
| `N0ZLjtGbHX4-09` / 27 | 00:00:59.480 | QUALIFIED | DC 전환 뒤 회사 부담금은 감소된 임금에 맞춰 적립된다 | DC 사용자 부담금은 임금총액 12분의 1 이상을 원칙으로 하되 실제 산정·수령 적립금은 임금과 운용손익, 규약에 좌우. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |

### #182 증권사별 파킹상품 비교 — RP·MMF·CD ETF·발행어음과 예금자보호 (23건)

| claim_id / cue | 영상 시간 | 판정 | 주장 내용 의역 | 공식 근거와 정정·한계 | URL |
|---|---|---|---|---|---|
| `UKDhdcn3AUk-01` / 70 | 00:02:17.480 | PRIMARY_CONFIRMED | 증권사 파킹상품으로 RP·MMF·발행어음·단기채 ETF를 제시 | 상품군은 실재하지만 환매조건·예금자보호·신용/시장위험과 유통구조가 서로 다름. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-02` / 90 | 00:02:56.080 | PRIMARY_CONFIRMED | 파킹상품마다 확정 또는 변동수익률 여부가 다르다 | RP/발행어음은 일반적으로 약정수익률형, MMF·MMW 및 채권 ETF는 실적·시가 변동형; 특정 계약 예외 가능. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-03` / 155 | 00:04:45.400 | PRIMARY_CONFIRMED | RP는 환매조건부채권 거래를 뜻한다 | 환매조건부매매에서 특정 시점/가격으로 다시 사는 계약을 기반으로 함. 은행 정기예금과 동일 계약은 아님. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-04` / 170 | 00:05:10.720 | QUALIFIED | RP는 증권사 예금과 같을 만큼 안전하다는 인상 | RP는 거래 자산과 매수기관의 환매의무가 있지만 예금자보호가 아닌 투자성거래. 보험대상인 은행예금과 동일시 불가. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-05` / 215 | 00:06:34.639 | CONTRADICTED | RP 담보채권이 우량이면 실질적으로 원금 손실 확률이 거의 0% | 우량담보만으로 원금손실 가능성을 0으로 단정할 수 없음. 담보의 시가·처분/회수지연·거래상대방 지급불능 위험이 남음. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-06` / 235 | 00:07:09.800 | QUALIFIED | RP 담보가 예탁결제원에 있으므로 증권사 파산해도 언제나 즉시 전액 회수 | 증권의 보관과 투자자에게 법정 지급보증되는 것은 다르며 담보권 실행·가치 평가·집행시간은 개별 계약과 도산절차 확인 필요. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-07` / 251 | 00:07:38.919 | CONTRADICTED | 국가부도급 위기가 아니면 RP에서 원금손실이 발생할 수 없다는 설명 | 특정 국가 전체 파산 없이도 개별 증권사 부실, 담보매각 손실 또는 회수지연이 가능. 예금자보호 대상 아님. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-08` / 282 | 00:08:40.680 | PRIMARY_CONFIRMED | 수시형과 기간약정 RP는 만기와 금리 조건이 다르다 | 수시형 금리와 약정만기형은 조건·중도환매 지급이율이 다름. 2025 화면 조건을 2026년 현행으로 사용 금지. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-09` / 302 | 00:09:21.800 | HYPOTHETICAL | 2025년 특정 한국투자·신한 ISA RP 2.5~3.5% 특판금리 | 영상 당시 원표·특판 공지 조건, 한도, 신규가입·ISA 자격 미확인. 당시 예시이고 현재 유효 금리·시장 최상단 아님. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-10` / 350 | 00:10:49.639 | HYPOTHETICAL | ISA 1년 RP 특판 연4.2% 가능, 계좌잔고 100만원 이하·매수한도1000만원 | 2025년 특정 기간 이벤트 약정 원표 미확보. 영상 제시 혜택을 보편적 금리로 확정하거나 현시점 재활용 불가. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-11` / 390 | 00:12:05.360 | PRIMARY_CONFIRMED | 미국 달러 RP는 환전 후 미달러 기반으로 투자 가능 | 달러 RP는 상품/증권사별 미국 달러 거래가 가능하나 환전스프레드·환율변동·신용위험 존재. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-12` / 430 | 00:13:18.760 | QUALIFIED | 2025년 달러 RP 1년 약정 연3.65%를 모든 투자자에게 권유 | 해당 금리는 촬영 당시 특정 상품 조건이며 환율이 변하면 원화 손익은 크게 달라짐. 예금자보호와 별개. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-13` / 478 | 00:14:50.560 | PRIMARY_CONFIRMED | MMF는 Money Market Fund, 단기금융시장 상품을 담는 펀드 | MMF는 단기채·CP 등 단기 금융상품에 투자하며 예금과 달리 기준가·운용실적 및 원금손실 가능. | [근거](https://file.koreainvestment.com/Storage/customer/guide/regards/%EC%84%A4%EB%AA%85%EC%84%9C70%ED%98%B8.MMF%ED%98%95CMA%EC%84%A4%EB%AA%85%EC%84%9C.pdf) |
| `UKDhdcn3AUk-14` / 560 | 00:17:22.199 | PRIMARY_CONFIRMED | MMF는 RP와 달리 운용실적에 따라 수익률이 변한다 | MMF형 CMA는 고정 약정금리가 아니며 시장 상황·기초자산·보수에 따라 수익률 변동. | [근거](https://file.koreainvestment.com/Storage/customer/guide/regards/%EC%84%A4%EB%AA%85%EC%84%9C70%ED%98%B8.MMF%ED%98%95CMA%EC%84%A4%EB%AA%85%EC%84%9C.pdf) |
| `UKDhdcn3AUk-15` / 569 | 00:17:39.919 | CONTRADICTED | MMF는 큰 금융기관 단기거래이므로 위험성을 걱정할 필요가 없다 | 공식 MMF 투자설명서에 원금 전부 또는 일부 손실가능성이 명시. 기관 거래라고 무위험 아님. | [근거](https://file.koreainvestment.com/Storage/customer/guide/regards/%EC%84%A4%EB%AA%85%EC%84%9C70%ED%98%B8.MMF%ED%98%95CMA%EC%84%A4%EB%AA%85%EC%84%9C.pdf) |
| `UKDhdcn3AUk-16` / 675 | 00:20:50.280 | QUALIFIED | MMF 최근 1년 수익률은 향후 1년 수익률 예고와 같다 | 지난 1년 수익률은 과거 시장금리 반영치이며 2026 이후 실제·예상수익률과 동일하지 않음. 영상 화자도 구별. | [근거](https://file.koreainvestment.com/Storage/customer/guide/regards/%EC%84%A4%EB%AA%85%EC%84%9C70%ED%98%B8.MMF%ED%98%95CMA%EC%84%A4%EB%AA%85%EC%84%9C.pdf) |
| `UKDhdcn3AUk-17` / 788 | 00:24:09.520 | QUALIFIED | CD 금리 연동형 ETF는 단기금리·시장가격에 연동 | ETF 기준가와 보수·추적오차·환매/결제일 등 차이 존재. CD 금리 자체가 세후 확정금리 보장 의미는 아님. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `UKDhdcn3AUk-18` / 915 | 00:28:02.960 | PRIMARY_CONFIRMED | 발행어음은 증권사가 신용으로 발행하는 단기금융상품 | 발행어음형 CMA는 발행사의 지급능력과 신용위험을 부담하고 예금자보호대상 아님. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-19` / 990 | 00:30:20.399 | QUALIFIED | IMA 자기자본 8조원 사업자와 발행어음 사업자는 업역이 다르다 | 2025 제도상 인가 및 자기자본 문턱은 구분되나 신규 제도 및 개별 발행사 상태는 발표일/인가일에 따라 확인. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-20` / 1110 | 00:33:57.960 | HYPOTHETICAL | 발행어음 특판 연3.4% 수익률이 지속된다고 볼 수 있다 | 개별 증권사 2025년 특별우대 금리의 모집공고·한도·예치기간 원표 없이 미래 보장금리로 확정 불가. | [근거](https://blog.kbsec.com/cma/%EB%B0%9C%ED%96%89%EC%96%B4%EC%9D%8C-rp-cma-%EC%98%88%EA%B8%88%EC%9E%90%EB%B3%B4%ED%98%B8/) |
| `UKDhdcn3AUk-21` / 1230 | 00:37:47.480 | QUALIFIED | 잔존만기 1년 이내 채권은 단기채권으로 볼 수 있다 | 짧은 듀레이션은 금리위험을 완화할 수 있으나 신용위험·유동성·매매 가격 변동이 없음은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `UKDhdcn3AUk-22` / 1300 | 00:40:11.000 | PRIMARY_CONFIRMED | 단기채 ETF는 운용사·기초자산별로 여러 종류가 있다 | 단기채 ETF는 종류와 수익률/보수·구성채권·금리민감도가 각각 다르고 예금자보호가 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `UKDhdcn3AUk-23` / 1450 | 00:44:48.960 | QUALIFIED | CD ETF·MMF ETF 매도대금 출금에 결제기한이 존재 | 국내 ETF 결제 T+2 등 거래소·증권사 규정/휴장일 및 담보대출 가능 여부에 따라 실제 현금화 시각 다름. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |

### #183 예비 신혼부부 재무계획 — 공동저축·퇴직연금·소득공백 상담 (14건)

| claim_id / cue | 영상 시간 | 판정 | 주장 내용 의역 | 공식 근거와 정정·한계 | URL |
|---|---|---|---|---|---|
| `3iDRSQnDQco-01` / 50 | 00:01:37.320 | HYPOTHETICAL | 결혼해 가계가 합쳐지면 생활비가 줄고 저축 여력이 커질 수 있다 | 공동생활 고정비 분담은 가능하나 실제 저축 증가액은 주거비·결혼비용·출산·생활패턴·가계 합의에 따라 다름. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-02` / 100 | 00:03:11.000 | QUALIFIED | 외벌이 가정 소득과 투자계좌가 한 명에게 집중되면 세테크상 유리하다 | 개인별 소득·법률혼/계좌소유/명의와 증여 관련 소득세·세액공제 등이 달라 절대적 절세 우위는 아님. | [근거](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7873&mi=2227) |
| `3iDRSQnDQco-03` / 150 | 00:04:42.600 | QUALIFIED | 맞벌이와 자영업 병행은 시간부담·예측하지 못한 사업경영 위험이 존재 | 실제 소득 변동과 사업운영비·부채·보험 고려; 영상 사연 속 미래 사업성공·유지 여부는 확인되지 않음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-04` / 190 | 00:05:55.919 | QUALIFIED | 부부가 똑같은 투자에 집중하기보다 서로의 장단점을 보완하는 공동 자산관리가 효과적 | 중복투자 위험과 부채·계좌 명의 점검은 유익할 수 있으나 개인 금융자율성·위험허용도를 보장할 것은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-05` / 300 | 00:08:59.800 | QUALIFIED | 신혼부터 부부의 연금 개시시점을 계획하는 전략 | 국민연금의 법정 개시연령, 퇴직급여 이연·개인연금 조건이 다르고 지금 고정한 수령일이 미래 법령/소득변화를 보장하지 않음. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `3iDRSQnDQco-06` / 410 | 00:12:19.600 | QUALIFIED | 주택 구입을 위해 퇴직금 중간정산·연금저축 인출·ISA 해지를 종합해야 한다 | 주택 취득 때 퇴직금 중간정산은 법정 조건과 회사 지급 가능 여부가 있고, 연금외수령 세금·연금 노후소득 훼손·ISA 의무유지기간을 함께 고려. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `3iDRSQnDQco-07` / 460 | 00:14:06.000 | HYPOTHETICAL | 공공기관에 재직하면 장기근속이 확정되어 퇴직금과 연금이 반드시 늘어난다 | 공공기관 근속도 인사·소득·고용환경·퇴직연금규약 영향을 받으므로 사연만으로 미래 근속을 보장하지 않음. | [근거](https://www.law.go.kr/lsInfoP.do?lsId=009883) |
| `3iDRSQnDQco-08` / 500 | 00:15:20.360 | QUALIFIED | 부부의 퇴직연금·개인연금의 개시시점을 현재 하나로 고정해 놓아야 한다 | 정확한 인출시점은 은퇴·소득·조기퇴직·물가·연금세제 변화에 맞춰 단계적으로 수정할 수 있음. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `3iDRSQnDQco-09` / 580 | 00:18:00.159 | QUALIFIED | 25년 뒤 소득공백보다 현재 두 계좌의 투자·저축 실행에 집중하라는 조언 | 근미래 지출과 장기연금을 병행 계획하는 것은 합리적일 수 있으나 예상 노후소득 부족분을 무시하지 않아야 함. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-10` / 625 | 00:19:21.760 | HYPOTHETICAL | 미래 소득공백은 ETF 배당·보유주식 일부 매도로 충당 가능 | 미래 분배금·주가·세후 출금액은 예측이며 생활비 완전 충당/원금 방어가 보장되지 않음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-11` / 700 | 00:21:52.360 | SPEAKER_OPINION | 노후만 목표로 저축하는 가구는 많지 않고 현재 재무목표를 병행해야 한다 | 가입자 분포 조사 원표 없는 사회적 관찰로, 전체 한국 가계가 그러하다고 검증된 인구통계가 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-12` / 785 | 00:24:29.919 | PRIMARY_CONFIRMED | 월200만원의 공동 저축만으로도 1년2400만원을 모을 수 있다 | 월200만원×12=연2400만원 명목 납입 합계, 실제 저축 지속 가능 여부는 부부 수입·지출에 좌우. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-13` / 830 | 00:25:59.480 | QUALIFIED | 정기적 공동저축 계좌를 만들고 장기 투자 습관을 형성 | 자동이체와 저축습관은 실행을 도울 수 있지만 가족 재무합의·비상자금·시장손실·수입변동 가능성 존재. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `3iDRSQnDQco-14` / 900 | 00:28:12.799 | QUALIFIED | 연금수령 시점만 고민하기보다 지금 절약·저축·투자 실행량을 늘린다 | 저축률은 중요한 노후자금 변수이나 현재 주택자금·채무·출산비 등 목적을 희생하며 무조건 투자액 확대해선 안 됨. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |

### #184 사회초년생 투자목표 — 예적금·연금·채권·월배당 포트폴리오 (15건)

| claim_id / cue | 영상 시간 | 판정 | 주장 내용 의역 | 공식 근거와 정정·한계 | URL |
|---|---|---|---|---|---|
| `QKDR6b3cuHY-01` / 55 | 00:01:44.360 | HYPOTHETICAL | 적금 월60만원·연금저축 월5만원·유동 투자 월1만~30만원 사례 | 가입자 사연 속 납입 내역이며 명세서·월수입·부채 미확인. 개인 원장 증거로 확정 불가. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-02` / 75 | 00:02:29.680 | HYPOTHETICAL | 사회초년생이 투자와 예금을 병행해 목돈 5000만원 보유했다는 사례 | 당사자 잔고는 개인 서술이며 투자원금/평가액 기준 원표 미확인. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-03` / 105 | 00:03:21.120 | QUALIFIED | 잦은 단기매매는 장기 자산형성을 방해할 수 있다 | 잦은 거래는 거래비용·추격매수·시장타이밍 위험을 유발할 수 있지만 단기매매가 언제나 음의 수익률이라는 뜻은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-04` / 135 | 00:04:13.120 | QUALIFIED | 현금성 예·적금 비중이 큰 사회초년생 포트도 합리적일 수 있다 | 근미래 주거자금·비상예비자금이 필요하면 낮은 변동성이 유리할 수 있으나 장기 목표에는 인플레이션 손실 가능. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-05` / 155 | 00:04:43.639 | QUALIFIED | 투자하지 않을 때 예금과 적금은 가장 좋은 선택이다 | 은행 예금·적금은 법정예금자보호에 해당하는 경우 원금 안정성이 있으나 금리·기회비용·목표기간별로 무조건 최상 상품 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-06` / 180 | 00:05:21.680 | QUALIFIED | 월5만원 연금저축을 소득 증대에 따라 월75만원까지 늘려 세제혜택 극대화 | 월75만원×12=연900만원. 다만 연금저축 단독 세액공제 대상 최대 600만원, IRP 포함 합산 900만원이며 실제 환급액은 개인 소득세 조건에 좌우. | [근거](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7873&mi=2227) |
| `QKDR6b3cuHY-07` / 215 | 00:06:18.120 | QUALIFIED | 20대 초반 큰 목돈의 보수적 포트가 장기적으로 언제나 유리하다 | 단기 현금목표와 낮은 손실허용도에서는 보수적 배분이 적합할 수 있지만 수십년 장기 실질수익 확보에 불리할 수도 있음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-08` / 245 | 00:07:15.479 | PRIMARY_CONFIRMED | 주식·채권 투자 비중을 분리해 관리하는 전략적 자산배분 | 주식·채권 등 상관이 완전히 같지 않은 자산군을 분산하고 위험허용도를 점검하는 자산배분 원리. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-09` / 280 | 00:08:14.039 | QUALIFIED | 사회초년생 경험을 위해 곧바로 고위험 공격형 투자로 전환할 필요 없다 | 초기 투자경험은 소액·분산·명확한 손실감내금액 범위에서 적합성 평가해야 하며 공격형 전략으로 자동 전환할 의무 없음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-10` / 320 | 00:09:25.399 | QUALIFIED | 주식 상승 후 추격 전환, 하락 후 채권 전환하는 행태는 손실 위험 | 최근 성과 추종으로 매수/매도 타이밍이 나빠질 수 있으나 실제 투자자 사례 실현손익은 증빙되지 않음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-11` / 360 | 00:10:30.200 | QUALIFIED | 예적금 중 일부를 월배당 ETF로 옮겨 투자경험을 넓히자는 제안 | 월분배율은 총수익률과 다르며 ETF 가격하락·기초자산 손실 가능. 긴급현금과 단기 목표액은 보전해야 함. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-12` / 395 | 00:11:34.000 | QUALIFIED | 미국 주식시장이 나빠져도 월배당·채권·파킹자금은 전혀 손실이 나지 않는다 | 상품별 채권 금리·발행사 신용위험·ETF 시장가격 변동을 구분. 자막 속 조건부 언급이지 투자원금 전체 무손실 보증 아님. | [근거](https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm) |
| `QKDR6b3cuHY-13` / 435 | 00:12:47.240 | QUALIFIED | 주식 투자원금 300만원 정도의 손실은 20대에게 무조건 감내 가능 | 300만원 손실의 체감은 월생활비·부채·주택목표·수입 지속성에 따라 크게 달라 보편 손실감내액 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-14` / 465 | 00:13:38.079 | QUALIFIED | 채권·배당·지수 ETF를 경험해 투자자 위험성향을 학습 | 교육용 소액 투자는 가능하지만 월분배금을 받는 체험이 안정적 수익 보장이라는 뜻은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `QKDR6b3cuHY-15` / 490 | 00:14:22.079 | PRIMARY_CONFIRMED | 여러 자산군으로 배분하는 전략은 특정 자산군 편중을 완화한다 | 분산과 목표자산배분은 집중위험을 완화할 수 있으나 동시하락과 손실 위험은 여전히 존재. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |

### #185 연금부자수업 EP.02 — 잃지 않는 투자·인플레이션·장기투자 원칙 (23건)

| claim_id / cue | 영상 시간 | 판정 | 주장 내용 의역 | 공식 근거와 정정·한계 | URL |
|---|---|---|---|---|---|
| `V7H65oaoflo-01` / 60 | 00:02:14.959 | HYPOTHETICAL | 2025년 퇴직연금+개인연금 적립금 합계 약600조원이라는 인용 | 영상 당시 발표 통계표, 기준일, 퇴직연금/개인연금 중복 및 금융기관 포함 범위 원표 미확보. 규모 수치 확정 금지. | [근거](https://kostat.go.kr/) |
| `V7H65oaoflo-02` / 110 | 00:04:01.760 | PRIMARY_CONFIRMED | 국민연금은 개인 계좌 잔액을 그대로 되돌려주는 적립식 상품이 아니다 | 공적 확정급여 산식에 기초한 사회보험; 사적 퇴직연금 계좌와 동일 개인 원리금 예금 구조가 아님. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-03` / 135 | 00:04:55.560 | QUALIFIED | 2026년 국민연금 명목 소득대체율이 43%로 오른다 | 2025 41.5%, 2026부터 43%로 인상은 법적 사실. 다만 2026-01-01 이후 가입기간에 적용, 기존 가입기간·현재 수급자에게 일률 소급되지 않음. 43%는 모든 생활비 지출의 보장 비율도 아님. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-04` / 160 | 00:05:47.120 | HYPOTHETICAL | 영상 출연자 부모가 매월 국민연금 약40만원을 수령한다 | 가족 사례 개인 수급이력·소득과 기간 원표 미확인; 국민연금 평균 수급액 근거 아님. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-05` / 200 | 00:06:59.160 | PRIMARY_CONFIRMED | 국민연금 보험료와 급여에는 소득상한·하한이 있다 | 국민연금 기준소득월액 상·하한과 연금급여 산식이 존재. 개인 소득이 무한정 보험료에 반영되지 않음. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-06` / 255 | 00:08:48.120 | QUALIFIED | 고령층의 소득빈곤 위험을 예방하려면 공적연금 외에도 준비가 중요하다 | 노후 부족 위험은 존재하나 영상 내 특정 통계표/조사시점/빈곤율 원표 미확인. 일반적 다층 노후준비의 필요를 설명. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-07` / 310 | 00:10:50.160 | QUALIFIED | 성공확률 높은 장기투자라면 누구나 특정 연금 전략에 성공한다 | 시간·적립·분산은 위험관리 장치이나 장기 보유가 투자 손실을 0%로 만들지 않으며 시장·인플레·인출 리스크 존재. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-08` / 355 | 00:12:24.800 | QUALIFIED | 채권 연2~3%·주식 연10~13%가 장기적으로 확정 수익률처럼 설명 | 평균 장기 실적·기대수익은 금리/평가시점/국가·기간에 따라 달라. 예시 구간 고정 보장금리가 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-09` / 390 | 00:13:29.959 | PRIMARY_CONFIRMED | 노후자금에는 레버리지·인버스 등 높은 변동성 집중투자가 부적합할 수 있다 | 레버리지·인버스는 복리 효과·변동성 드래그·일일 추종 차이로 장기 목표와 맞지 않을 수 있음. 특정 투자금지의 법률명령과 구분. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-10` / 470 | 00:16:09.759 | QUALIFIED | 연금계좌 안에서는 기대수익률보다 장기 실패위험 최소화가 중요 | 적정 위험수준·목표수익·노후소득은 투자기간과 포트 구성에 따라 달라, 최저 위험자산만이 정답은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-11` / 510 | 00:17:35.960 | SPEAKER_OPINION | 영국과 미국의 교육성과 국민성을 비교해 창의성·학업 수준을 단정 | 인구·교육 통계 출처 없는 문화적 비유로, 투자수익률 입증 또는 국가별 객관 교육수준 순위 자료가 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-12` / 541 | 00:18:44.400 | QUALIFIED | 연금계좌에서는 ETF만 가능하고 개별주식은 불가능하다는 표현 | 한국 연금저축펀드·IRP 투자 가능 범위는 개별상품과 연금계좌/브로커 규정에 따름. 연금계좌 상품군 전체가 '오직 ETF만'이라는 표현은 부정확; 펀드·예금 등 적격상품 가능. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-13` / 560 | 00:19:26.880 | QUALIFIED | 노후투자 세 원칙 첫째는 큰 손실을 회피하는 분산투자 | 분산과 손실관리 원칙은 타당하나 원금무손실 전략이 아니고 장기 수익률 보장 불가. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-14` / 580 | 00:20:07.840 | HYPOTHETICAL | 연금의 7%·5% 등 꾸준한 수익과 일시적 50% 수익 비교 | 여러 해의 수익률 경로 가정일 뿐 실제 상품 성과·장기 평균수익률 7% 약정 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-15` / 595 | 00:20:44.000 | PRIMARY_CONFIRMED | 20% 상승 뒤 10% 하락한 누적수익률은 +8%, 10% 연속 두 번이면 +21% | 1.2×0.9−1=+8%; 1.1×1.1−1=+21%. 영상이 대비한 복리 손익 계산이 단순 덧셈 10%보다 정확. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-16` / 615 | 00:21:28.200 | PRIMARY_CONFIRMED | 현금 장기 보유는 인플레이션으로 실질 구매력을 줄일 수 있다 | 물가가 상승하고 현금 이자가 충분하지 않다면 실질 구매력 감소. 예금·단기채가 무조건 구매력 훼손이라는 뜻은 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-17` / 650 | 00:22:37.200 | QUALIFIED | 주가·아파트·음식가격 상승이 모두 인플레이션만으로 설명된다 | 주가는 이익·할인율·성장·환율, 주택은 공급·금리·규제도 중요. 명목자산 상승이 전부 실질 수익 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-18` / 670 | 00:23:17.640 | HYPOTHETICAL | 한국 생활물가 상승률이 과거 평균 연6%로 볼 수 있다는 설명 | 물가지수 품목·기간·지표에 따른 공식 소비자물가 상승률을 6%로 획일화할 근거 원표 미확인. 개인 체감물가와 공식 지표는 다름. | [근거](https://kostat.go.kr/) |
| `V7H65oaoflo-19` / 710 | 00:24:31.240 | QUALIFIED | 20~30년 장기투자하면 누구나 충분한 노후자금을 마련한다 | 정기적 장기저축은 복리 기간을 확보하지만 실질 생활비, 저축액, 수익률, 조기 인출과 장수위험에 따라 부족할 수 있음. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-20` / 735 | 00:25:29.760 | PRIMARY_CONFIRMED | 지수·ETF 분산은 개별기업 파산 위험을 완화할 수 있다 | 여러 종목·산업·국가 자산에 분산하면 특정 기업 집중위험 감소하나 전시장 동반하락 위험 유지. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-21` / 780 | 00:27:12.200 | QUALIFIED | 국민연금·퇴직연금·개인연금 세 층을 합산해 노후 현금흐름 계획 | 다층 노후소득은 유용한 계획 기초이나 국민연금 납입원금 예상 1~2억원과 개인연금 목표3억원은 영상의 개인별 추정이며 보장액 아님. | [근거](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0104M0.do) |
| `V7H65oaoflo-22` / 840 | 00:29:28.399 | HYPOTHETICAL | 개인연금 3억원이면 월분배금 100만~200만원을 원금 훼손 없이 얻을 수 있다 | 연4~8% 현금분배에 해당하며 분배금·NAV·세제·원금 수준은 가변. 3억원과 공적/퇴직연금만으로 모든 사람 월300만원 보장 아님. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `V7H65oaoflo-23` / 850 | 00:29:51.720 | QUALIFIED | 늦지 않게 연금저축·ETF 투자 시작이 장기 자산축적에 도움 | 조기 적립기간은 유리할 수 있지만 긴급예비금과 금융지식, 위험허용도를 무시한 즉시매수는 부적절. | [근거](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |

## 7. 남은 보완·기존 OPEN 원장 정책

- 추가 확인 필요: #181 실제 회사 퇴직연금규약/IRP 소액 연금지급 연차 효과, #182 2025-11 증권사 특판 RP·발행어음 공고 원표 및 당시 담보권 구체 계약, #183 부부 실제 금전정보, #184 투자잔액/수익원표, #185 역사적 적립금 통계·체감물가 지표 원표. 이들은 주장별 QUALIFIED/HYPOTHETICAL 및 제한으로 남겨 추정 사실 승격 금지.
- 이전 **OPEN 24건은 변경하지 않음**. 이 배치의 미확인 개인 명세·역사 통계는 기존 OPEN으로 임의 합산·해결했다고 주장하지 않는다. 퇴직급여법 최신 시행일(2026-09-18)과 영상 2025-11 시점 차이는 명시한다.
- 기존 정식 **179편·2,879건** + 이번 **5편·84건** = **184편·2,963건**. 전체 791편 중 607편 남음. 실제 GitHub 단일 원자적 커밋 및 Push/PR 자동검사 성공 후 최종 누적으로 인정한다.
- GitHub `main` 브랜치, 과거 연구 분석 원장과 비공개 원본 자막은 수정하지 않는다.
