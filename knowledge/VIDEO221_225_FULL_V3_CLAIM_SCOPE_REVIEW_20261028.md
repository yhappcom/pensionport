# 박곰희TV #221–225 — 비공개 SRT·공식자료 V3 주장별 검증 (2026-10-28)

## 검증 결론

**선별 투자교육 V3 승인 5편, 65개 주장.** 판정: PRIMARY_CONFIRMED 8 / QUALIFIED 46 / HYPOTHETICAL 6 / CONTRADICTED 5 (정정문 필수). 반증된 발언은 **원문을 정당화하거나 추천으로 사용하지 않는다.** 출처 인증은 5편 5,259cue (408,124바이트) 비공개 SRT이며 원음·프레임·공개 한글 전문 독립 대조 없음. 특히 #223은 제작자가 과거 ISA 설명을 스스로 정정하므로 **과거 주장과 최신 정정 설명의 구분**이 핵심이다.

**승인 범위 제한:** 자막 전문 모든 발언이나 개인 수익률 인증은 아니다. 역사적 특정일 시총·주가는 시점별 KRX 원표 대조 미확정이며 영상 숫자를 독립 통계처럼 재사용할 수 없다. 투자전망, 기업 계약과 증권사별 과세원장 처리의 장담 역시 제외한다.

## 원본 증빙

- Google Drive 비공개: https://drive.google.com/file/d/1CJvWcNyjcMM5xrjio_YFWSbr57-1J--1/view?usp=drivesdk
- 이번 ZIP SHA256 `9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10`, ZIP 2,913,470 bytes / 99 SRT. 기존 #216–220 ZIP SHA256 `b5674d1a3e07b3ab40d4ca9b548dd6378916105bfb91f287247d4dd85242832d`와 **상이함**; #216·#220 개별 SRT는 동일한 것으로 표본 검사됐으나 전체 아카이브 동등성 미확정.
- 개별 SRT의 SHA, cues, timestamp and text-derived paraphrase are captured in `data/subtitles/registry_221_225_20261028.json` and `data/subtitles/pilots/*.json`. ZIP/SRT 전문은 공개 GitHub 저장하지 않음.

| No | Video ID | SRT cues | Claimed assertions | Primary | Qualified | Hypothetical | Contradicted | V3 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| #221 | `6BUwcadctCE` | 1118 | 12 | 2 | 9 | 0 | 1 | 승인 |
| #222 | `xrArQWWHkGg` | 1117 | 12 | 0 | 8 | 4 | 0 | 승인 |
| #223 | `-4tqIxeViZ4` | 962 | 14 | 2 | 10 | 0 | 2 | 승인 |
| #224 | `CYGtiwmucw0` | 1074 | 13 | 0 | 9 | 2 | 2 | 승인 |
| #225 | `loKj0LccKTA` | 988 | 14 | 4 | 10 | 0 | 0 | 승인 |
| **Total** | | **5259** | **65** | **8** | **46** | **6** | **5** | **5** |

## 중대 내용 정정 / 투자 위험 유보
1. **#221 퇴직연금 DB·DC 전환**: DC적립금의 DB 이전 불허와 향후 기간에 적용하는 DB 제도 변경 가능성은 별개. [고용노동부](https://www.moel.go.kr/info/publicdata/qnrinfo/qnrInfoView.do?qnr_uid=2016030300000007)
2. **#221 ELB**: 예금과 같은 원금·예금자 보호로 일반화 불가, 발행사 신용위험 및 중도상환손실 가능. [한국거래소 공시](https://kind.krx.co.kr/external/2026/04/29/000571/20260429001672/10603.htm)
3. **#223 ISA 연금이전**: ISA 만기이전금액의 10%, 최대 300만원은 추가 세액공제 **대상 납입액**이지 환급받는 세액 300만원이 아님. 기존 300+2700 이전 설명은 300만원 전액 공제를 달성하지 못한다는 영상 정정을 인정. [국세청](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439)
4. **#223 이월 공제**: 국세청 유권해석 근거가 있지만 개별 금융회사 과세재원 자동분류·원금 인출·다년도 공제 절차를 모두 공통규칙으로 단정할 수 없음. [국세청 세법해석](https://taxlaw.nts.go.kr/pd/USEPDA002P.do?ntstDcmId=200000000000006505)
5. **#224 의약품 특허**: 통상 10년으로 단정은 부정확, 국내 일반 특허 출원일 기준 20년 및 조건부 연장. [특허청](https://www.kipo.go.kr/)
6. **#224 SC 주사**: SC 피하주사와 IM 근육주사는 분류상 별개. [미 FDA 경로](https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration)
7. **#225 IPO**: 항상 신주만 발행하는 공모는 아님; 구주매출 가능, 영상 후반 구주매출 설명도 있으므로 문맥간 불일치 보정. [SEC Investor.gov](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-17)

## Claim-by-claim independent official review

### #221 — DB·DC형 퇴직연금 선택·전환·운용의 실제 조건 (12 claims; 1118 SRT cues)

| Claim ID / cue | Time | Verdict | Educational claim (paraphrased) | Evidence and limitation | Official source |
|---|---|---|---|---|---|
| `6BUwcadctCE-01` / 92 | 00:02:42.760 | QUALIFIED | 퇴직연금 상품 선택은 은퇴자금의 장기 목적과 함께 판단 | 근속기간·임금추세·개인 위험수용도와 퇴직급여규약에 따라 적합 유형이 달라짐 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-02` / 226 | 00:06:35.960 | PRIMARY_CONFIRMED | 퇴직급여 관련 금액은 근속기간과 임금을 바탕으로 산정 | 법정 퇴직급여 계산과 DB·DC 적립액 산식은 구분해야 함 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-03` / 301 | 00:08:47.880 | QUALIFIED | DB형은 기업의 퇴직급여 지급 책임이 핵심 | 사용자가 운용책임을 지되 사용자·사업장 지급능력과 제도 규정도 고려 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-04` / 380 | 00:11:04.600 | CONTRADICTED | DC에서 DB로는 일절 변경할 수 없다 | DC 적립금 자체의 DB 이전은 허용되지 않는 것이 원칙이나 이후 기간부터 DB를 적용해 기간별 퇴직급여를 별도로 산정하는 제도변경 가능성이 있음 | [자료](https://www.moel.go.kr/info/publicdata/qnrinfo/qnrInfoView.do?qnr_uid=2016030300000007) |
| `6BUwcadctCE-05` / 400 | 00:11:37.560 | QUALIFIED | DB와 DC 간 전환은 언제나 개인이 자유롭게 되돌릴 수 있다 | 규약·집단적 절차 및 과거 가입기간 귀속이 관건이며 자유로운 개인 선택권 보장 아님 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-06` / 426 | 00:12:23.680 | QUALIFIED | 임금 상승이 빠르면 DB 퇴직급여가 유리할 수 있다 | 임금상승, 임금피크, 근속기간, 실적수익률의 비교에 따른 조건부 사례 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-07` / 471 | 00:13:47.160 | PRIMARY_CONFIRMED | DB 퇴직급여는 퇴직 전 평균임금 개념에 연동된다 | 법정 평균임금 기준과 실제 취업규칙상 유리한 산식 확인 | [자료](https://www.moel.go.kr/retirementpay.do) |
| `6BUwcadctCE-08` / 544 | 00:15:52.399 | QUALIFIED | 퇴직급여를 IRP에 수령하면 세제이연을 검토할 수 있다 | 적격 이전과 연금수령·일시수령 시점에 따라 퇴직소득세 실현 및 감면이 달라짐 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `6BUwcadctCE-09` / 754 | 00:21:59.360 | QUALIFIED | DC형에서 운용 지시 없이 현금성 자산을 방치하면 기회비용이 생길 수 있다 | 예금성 운용과 실적배당 운용의 위험·수수료·투자기간을 비교해야 하며 투자수익 보장 없음 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `6BUwcadctCE-10` / 788 | 00:22:55.000 | QUALIFIED | 은행·증권사 퇴직연금 상품은 수익률과 위험이 동일하다 | 취급기관보다 개별 상품의 보장 여부·예금자보호·수수료·운용구조가 중요 | [자료](https://www.fsc.go.kr/po020201/84975) |
| `6BUwcadctCE-11` / 914 | 00:26:24.440 | QUALIFIED | ELB는 예금처럼 원금이 확실히 보장된다 | ELB는 발행사 신용위험 및 조기상환 손실 가능성이 있고 예금자보호 상품과 다름 | [자료](https://kind.krx.co.kr/external/2026/04/29/000571/20260429001672/10603.htm) |
| `6BUwcadctCE-12` / 978 | 00:28:14.000 | QUALIFIED | 채권·안전자산 상품은 신용위험을 전혀 걱정할 필요 없다 | 채권에도 발행사 신용·시장금리·유동성 위험 존재 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |

### #222 — 국내 업종별 시가총액과 주도기업 비교·역사적 순위 (12 claims; 1117 SRT cues)

| Claim ID / cue | Time | Verdict | Educational claim (paraphrased) | Evidence and limitation | Official source |
|---|---|---|---|---|---|
| `xrArQWWHkGg-01` / 24 | 00:00:48.559 | HYPOTHETICAL | SMR 관련 기업의 2025년 시가총액이 약 43조원이라는 비교 | 2025년 해당 거래일·상장주식수·종목코드 원표가 없어 수치 미확정 | [자료](https://data.krx.co.kr/) |
| `xrArQWWHkGg-02` / 84 | 00:02:36.840 | HYPOTHETICAL | HMM 당시 시가총액이 약 23조원이었다는 설명 | 특정 기준일의 종목별 공식 시총 원표를 확보하지 않아 숫자를 확정하지 않음 | [자료](https://data.krx.co.kr/) |
| `xrArQWWHkGg-03` / 97 | 00:03:03.040 | QUALIFIED | 해운업 주가는 운임과 경기 사이클에 영향받는다 | 운임·유가·선복 공급·부채 등 복수 변수가 작용하며 단순 인과·상승보장 금지 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-04` / 119 | 00:03:43.799 | QUALIFIED | 운송업 전체가 예외 없이 과점 산업이라는 표현 | 세부 해운·항공·육상 물류의 경쟁구조와 시장을 구별해야 함 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-05` / 179 | 00:05:33.360 | QUALIFIED | 해운 운임지수는 업황을 보는 지표 중 하나 | 지수 종류·운임계약 형태에 따라 개별 기업 이익과 시차·괴리가 발생 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-06` / 241 | 00:07:27.240 | HYPOTHETICAL | 보험업종 합산 시총이 당시 63조원이라는 수치 | 업종 구성·상장 범위·기준일별 합산 확인 전 숫자 인용 제한 | [자료](https://data.krx.co.kr/) |
| `xrArQWWHkGg-07` / 272 | 00:08:25.319 | QUALIFIED | 생명보험과 손해보험은 사업구조와 수익요인이 다르다 | 상품별 보험부채·금리·손해율 등에 대한 별도 비교 필요 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-08` / 307 | 00:09:25.839 | QUALIFIED | 식품업종 대장주 주가와 기업가치를 연결해 설명 | 주당 가격과 발행주식수·기업가치는 구분해야 하며 개별 과거 평가 미확정 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization) |
| `xrArQWWHkGg-09` / 391 | 00:11:55.399 | HYPOTHETICAL | 미국 관세가 국내 식품 수출기업 이익을 일정 비율 감소시킨다 | 기업별 수출계약·환율·가격전가·해당 연도 관세표 미확보로 정량효과 미확정 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-10` / 451 | 00:13:43.199 | QUALIFIED | 통신사 시가총액 순위는 기간에 따라 변한다 | 당시 순위·수치는 거래일과 기업행위 반영한 KRX 원표 확인 필요 | [자료](https://data.krx.co.kr/) |
| `xrArQWWHkGg-11` / 604 | 00:18:20.600 | QUALIFIED | SMR 관련 사업 참여만으로 건설사의 실적 증가가 확정된다 | 프로젝트 수주·실현 매출·원가율과 투자테마를 분리해야 함 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `xrArQWWHkGg-12` / 830 | 00:25:28.799 | QUALIFIED | 업종 대장주 투자는 업종 성장과 같은 수익을 보장한다 | 대형주 집중·주가 선반영·밸류에이션 위험, 지수와 개별 종목 차이 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |

### #223 — ISA 만기 연금이전 전략 정정 — 300만원 세액공제 한도와 원금 재원분리 (14 claims; 962 SRT cues)

| Claim ID / cue | Time | Verdict | Educational claim (paraphrased) | Evidence and limitation | Official source |
|---|---|---|---|---|---|
| `-4tqIxeViZ4-01` / 82 | 00:02:33.000 | QUALIFIED | 월 50만원 연금저축·월 167만원 ISA 적립 사례를 제시 | 개인 소득·현금흐름·당해 납입한도·공제한도에 따라 최적 납입액이 다름 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-02` / 159 | 00:05:03.759 | PRIMARY_CONFIRMED | ISA 만기 자금을 연금계좌로 옮겨 추가 세액공제를 활용할 수 있다 | 만기일부터 60일 이내 적격 이전과 소득세법상 인정 요건 필요 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-03` / 168 | 00:05:24.240 | QUALIFIED | ISA 이전금액의 10%, 최대 300만원을 추가 세액공제 받는다고 표현 | 300만원은 추가 세액공제 대상 납입액의 상한이고 직접 세금 환급액은 아님 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-04` / 176 | 00:05:40.360 | CONTRADICTED | ISA 3000만원을 공제 계좌 300만원·미공제 계좌 2700만원으로 옮겨도 300만원 전체 공제대상으로 자동 인정 | 적격 전환 납입액의 10%로 추가 공제대상 한도를 계산하므로 300만원만 옮기면 원칙상 30만원만 관련 추가 공제대상; 영상 자체가 과거 설명 정정 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-05` / 206 | 00:06:42.639 | CONTRADICTED | 300만원만 별도 계좌로 전환하면 추가 공제 한도 300만원을 달성한다 | 전환한 실제 ISA 만기자금이 300만원이라면 10%인 30만원까지만 추가 공제대상으로 산정 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-06` / 257 | 00:08:19.199 | PRIMARY_CONFIRMED | 연금계좌 미공제 납입원금은 운용수익과 다른 과세재원 | 실제 공제 이력·금융기관 원천구분 확인 필요; 운용수익은 별도 과세 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `-4tqIxeViZ4-07` / 347 | 00:11:11.399 | QUALIFIED | 사적연금 1500만원 기준은 모든 연금 출금의 절대 한도 | 특정 과세대상 사적연금소득 세금처리 기준일 뿐 절대 출금 한도가 아님 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `-4tqIxeViZ4-08` / 424 | 00:13:31.880 | QUALIFIED | 이전금액 3000만원 중 비공제 2700만원을 즉시 인출할 수 있다 | 재원별 인출 우선순위·금융기관 원장 반영·계좌 상태에 따라 인출가능 시기 다름 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `-4tqIxeViZ4-09` / 440 | 00:14:02.839 | QUALIFIED | ISA 이전 후 비과세 원금 인출시점이 금융회사마다 다를 수 있다 | 취급기관의 실제 업무흐름·증빙 반영 전에 즉시 인출 가능하다고 일반화 금지 | [자료](https://www.samsungpop.com/ux/kor/finance/isa/isainfo/intro.do) |
| `-4tqIxeViZ4-10` / 450 | 00:14:22.480 | QUALIFIED | 연금계좌 납입액의 미사용 세액공제 한도 이월 적용 가능 | 국세청 유권해석상 조건부 가능하나 과거 납입 이력·연도별 한도 및 신청처리 확인 필요 | [자료](https://taxlaw.nts.go.kr/pd/USEPDA002P.do?ntstDcmId=200000000000006505) |
| `-4tqIxeViZ4-11` / 615 | 00:19:27.320 | QUALIFIED | ISA 이전 미공제원금으로 다음 여러 해 공제를 적용할 수 있다 | 초과납입액 소급공제 선택·잔여한도·신청기간 및 2026 당시 세법을 개인별 확인해야 함 | [자료](https://taxlaw.nts.go.kr/pd/USEPDA002P.do?ntstDcmId=200000000000006505) |
| `-4tqIxeViZ4-12` / 654 | 00:20:41.000 | QUALIFIED | ISA 전환금의 추가 공제와 일반 연금 공제는 완전히 동일한 한도다 | ISA 전환 특별 추가 공제대상과 일반 연금저축·IRP의 세액공제 한도를 별도 관리 | [자료](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439) |
| `-4tqIxeViZ4-13` / 672 | 00:21:15.679 | QUALIFIED | 공제확인서를 다음 해 7월 이후 제출하면 모든 기관이 동일하게 자동 정정 | 국세청 서류 발급시기·기관별 등록·연금계좌 소득원천구분 처리 절차 확인 필요 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `-4tqIxeViZ4-14` / 813 | 00:25:41.840 | QUALIFIED | 미공제 납입원금의 과세재원 전환은 어느 경우에도 영구 불가능하다 | 실제 세액공제 선택·경정 및 납입한도 구분은 과세내역·기관처리 따라 변하므로 영구 불가로 단정하지 않음 | [자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |

### #224 — 은행·바이오·조선·자동차·방산 산업구조와 주식 위험 (13 claims; 1074 SRT cues)

| Claim ID / cue | Time | Verdict | Educational claim (paraphrased) | Evidence and limitation | Official source |
|---|---|---|---|---|---|
| `CYGtiwmucw0-01` / 30 | 00:00:51.840 | QUALIFIED | 국내 은행주가 가장 안전한 투자라는 일반 비교 | 안정성은 예금상품과 상장주식 투자에 동일 적용할 수 없음; 은행주 역시 손실가능 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `CYGtiwmucw0-02` / 76 | 00:02:11.640 | HYPOTHETICAL | 특정 시점 KB금융 시가총액이 약 43조원 | 기준일 종목 원표 미확보, 역사적 시총 숫자는 미확정 | [자료](https://data.krx.co.kr/) |
| `CYGtiwmucw0-03` / 93 | 00:02:47.159 | QUALIFIED | 메리츠금융지주와 금융사 구조 재편 사례 | 기업별 합병·지주회사 편입 실제 공시와 시점 확인 전 일반 구조 설명만 사용 | [자료](https://data.krx.co.kr/) |
| `CYGtiwmucw0-04` / 234 | 00:07:07.520 | QUALIFIED | 배터리 산업은 설비투자가 크고 업황에 민감하다 | CAPEX·판매가격·보조금·원자재 가격 등에 따라 개별 기업 손익 차이 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `CYGtiwmucw0-05` / 340 | 00:10:18.480 | QUALIFIED | 제약·바이오 기업은 약품 수요가 성장할 수 있다 | 규제 승인, 임상 성공·실패, 보험약가, 경쟁 출시가 투자수익에 중요 | [자료](https://www.fda.gov/drugs/biosimilars/biosimilars-basics-patients) |
| `CYGtiwmucw0-06` / 382 | 00:11:44.200 | CONTRADICTED | 의약품 특허보호기간은 보통 10년이라는 설명 | 한국 특허권의 일반 존속기간은 출원일부터 20년이고 의약품은 요건 충족시 연장제도가 존재; 단순 10년으로 일반화 불가 | [자료](https://www.kipo.go.kr/) |
| `CYGtiwmucw0-07` / 395 | 00:12:04.800 | QUALIFIED | 특허 만료 의약품과 제네릭의 관계 | 신약 특허 만료·독점권과 제네릭 허가요건을 혼동하지 않도록 구별 | [자료](https://www.fda.gov/drugs/biosimilars/biosimilars-basics-patients) |
| `CYGtiwmucw0-08` / 403 | 00:12:18.920 | QUALIFIED | 바이오시밀러는 일반 합성의약품 제네릭과 동일하다 | 바이오시밀러는 복잡한 생물학적 제제에 고도의 유사성을 입증하는 별도 경로 | [자료](https://www.fda.gov/drugs/biosimilars/biosimilars-basics-patients) |
| `CYGtiwmucw0-09` / 407 | 00:12:26.839 | QUALIFIED | 바이오의약품 위탁개발생산(CDMO) 구조 | 위탁개발·생산의 계약수주, 실제 가동률과 의약품 규제 허가별로 차이 | [자료](https://www.fda.gov/drugs/biosimilars/biosimilars-basics-patients) |
| `CYGtiwmucw0-10` / 472 | 00:14:24.959 | CONTRADICTED | 피하주사(SC)와 근육주사(IM)는 같은 투여경로라는 혼용 | SC는 피하조직 주입, IM은 근육 내 주입으로 FDA 경로 분류상 명백히 다른 투여경로 | [자료](https://www.fda.gov/drugs/data-standards-manual-monographs/route-administration) |
| `CYGtiwmucw0-11` / 525 | 00:16:03.160 | HYPOTHETICAL | 조선 2025년 상장사 시총 합계 약 160조원 | 2025 특정 기준일·업종기업 포함범위를 재구성한 공식 원표 없음 | [자료](https://data.krx.co.kr/) |
| `CYGtiwmucw0-12` / 615 | 00:18:50.240 | QUALIFIED | 특정 완성차 회사 과거 배당률을 미래 수익으로 기대 | 과거 배당은 향후 배당금 지급·수익률 보장과 다름 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `CYGtiwmucw0-13` / 808 | 00:24:35.360 | QUALIFIED | 방산업종 기업가치는 국가 예산과 수주에 연동될 수 있다 | 국가별 수출허가·사업 수주·주가 선반영 여부가 중요 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |

### #225 — 주가·주식수·시가총액·IPO와 업종별 대장주 판단 (14 claims; 988 SRT cues)

| Claim ID / cue | Time | Verdict | Educational claim (paraphrased) | Evidence and limitation | Official source |
|---|---|---|---|---|---|
| `loKj0LccKTA-01` / 14 | 00:00:26.519 | QUALIFIED | 시가총액이 큰 회사는 업종 내 대표 기업으로 분류되곤 한다 | 시가총액이 산업 지배력·미래 수익이나 품질의 완전한 대리변수는 아님 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization) |
| `loKj0LccKTA-02` / 73 | 00:02:17.000 | PRIMARY_CONFIRMED | 시가총액은 주가에 상장주식수를 곱해 산출 | 시가총액의 기본 산식; 유통주식수와 총 발행주식수의 차이 유의 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization) |
| `loKj0LccKTA-03` / 91 | 00:02:51.400 | PRIMARY_CONFIRMED | 주가가 낮다는 이유만으로 기업이 저평가된 것은 아니다 | 주당 가격은 분할·발행주식수 영향을 받음, 기업가치 측정과 분리 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization) |
| `loKj0LccKTA-04` / 96 | 00:03:01.000 | PRIMARY_CONFIRMED | 주식분할은 발행주식수와 1주 가격을 조정한다 | 기업 펀더멘털·전체 시가총액을 자동으로 증가시키지는 않음 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split) |
| `loKj0LccKTA-05` / 158 | 00:04:46.720 | QUALIFIED | 자본금과 시가총액은 동일하다 | 자본금은 액면가 및 발행주식수 등 회계·상법 기준, 시가총액은 현재 주식시장 가격 곱 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization) |
| `loKj0LccKTA-06` / 165 | 00:05:00.360 | QUALIFIED | 무상증자는 주식수가 늘어나 기업 전체 가치가 자동 상승 | 기업가치는 무상증자만으로 실질적으로 증가하지 않으며 가격 조정 가능 | [자료](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split) |
| `loKj0LccKTA-07` / 223 | 00:06:44.919 | QUALIFIED | PER은 기업 이익에 비례한 주가 평가 보조지표 | 일회성 손익·이익 적자·업종·회계정책 차이를 고려, 저PER 무조건 저평가 아님 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `loKj0LccKTA-08` / 310 | 00:09:17.440 | QUALIFIED | 비상장 스타트업 가치평가는 예상 성장에 영향을 받는다 | 유동성·후속자금조달 희석·추정 모형 불확실성 커 투자손실 가능 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `loKj0LccKTA-09` / 391 | 00:11:41.760 | QUALIFIED | 벤처캐피털 투자는 일반 상장주식과 위험 구조가 다르다 | 회수기간, 비상장 가격측정, 유동성, 손실확률을 구별 | [자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `loKj0LccKTA-10` / 427 | 00:12:46.160 | QUALIFIED | IPO는 비상장 주식이 일반 투자자를 상대로 증시 공모·상장되는 과정 | 발행시장 투자와 상장 이후 거래를 구별; 공모구조는 구주매출도 가능 | [자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-17) |
| `loKj0LccKTA-11` / 469 | 00:13:57.880 | QUALIFIED | IPO 공모는 항상 신규주식 발행만으로 진행된다 | 신주모집과 기존 주주의 구주매출이 혼합될 수 있음; 영상 후반 구주매출 별도 언급도 고려 | [자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-17) |
| `loKj0LccKTA-12` / 481 | 00:14:22.560 | QUALIFIED | 기관 수요예측은 공모가 결정 과정에 중요한 역할 | 실제 수요예측 결과·확약·최종 공모조건과 투자자 청약 위험 확인 | [자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-17) |
| `loKj0LccKTA-13` / 587 | 00:17:29.919 | PRIMARY_CONFIRMED | IPO에서 구주매출이 존재할 수 있다 | 신주와 구주 비중에 따라 모집자금의 기업 유입 효과가 다름 | [자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-17) |
| `loKj0LccKTA-14` / 695 | 00:20:49.120 | QUALIFIED | 시가총액 금액만으로 소형·중형·대형주를 법적으로 일률 구분 | 지수 편입·시장·기관별 사이즈 구분 체계가 달라 단일 법정금액 아님 | [자료](https://data.krx.co.kr/) |

## 불변 항목
기존 #1~220 기록, 기존 OPEN 24건, #204 예외, #219 비투자 제외를 수정하지 않는다. `main` 미변경. 자동검사는 이 기록을 재조회할 때만 PASS로 보고한다.
