# 박곰희TV #216~220 — 원본 한국어 SRT·공식자료 V3 주장별 검증 (2026-10-27)

**결과:** 원본 5편 4,241개 SRT cue(328,612바이트) 해시·시간코드 구조 확인. **금융교육 4편에 대한 핵심 주장 65건** 승인 대상, #219는 1,036개 원본 cue의 소비자 통신비 내용으로 **투자교육 V3 제외**. 검토 판정 **PRIMARY_CONFIRMED 17 / QUALIFIED 42 / HYPOTHETICAL 6 / CONTRADICTED 0 / SPEAKER_OPINION 0**.

## 1. 원본·범위·보관
- 사용자 비공개 `201-300.zip`, SHA-256 `b5674d1a3e07b3ab40d4ca9b548dd6378916105bfb91f287247d4dd85242832d`(2,913,470바이트), 전체 99 SRT 중 이번 5편을 출처별로 확인.
- `data/subtitles/registry_216_220_20261027.json`은 5개 파일 해시/크기/영상ID와 교육 V3 4편 + 비투자 1편을 분리하고 `scripts/audit_subtitle_review_gate.py`는 그 값 고정 확인. #219 제외 사유 전문 `data/subtitles/exclusions/BxqQAqr2OA0.json`.
- GitHub나 Google Drive에 원본 SRT 전문/ZIP 저장 금지. 영상 프레임·원음/공개 한국어 자막 전문의 독립 대조는 완료하지 않음. 교육 주장 **일부 선별 검증 범위**는 원본 모든 발언·개인 실적이나 계약을 인증하지 않음.

## 2. 중대 제도·투자위험 검증

**#216 — 퇴직금 연금수령 과세개편:** 2025년 영상에서 언급된 **2026년 시행 이후** 이연퇴직소득의 실제 적격연금 수령연차 1~10년차는 퇴직소득세의 70%, 11~20년차는 60%, **21년차 이상은 50%**라는 별도 원천과세가 적용. [국세청 연금 원천징수](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605). 연금저축계좌의 법정 연금수령한도와 1500만원 사적연금소득 합산판정은 별도. 단순 IRP 1만원 인출 신청 자체로 누구나 21년차 감면을 확보할 수 있다고 단정 금지; 실제 연금수령연차와 계좌조건 확인 필요.

**#217 — 노후 연금 활용팁:** 퇴직급여/개인 연금/국민연금은 재원·운용제약/원천세가 다름. **1억원 계좌 첫해 연금수령한도 1200만원**의 일반 계산(`1억원/(11-1)×120%`)은 산술적으로 유효하나 개별 연금계좌의 가입일·수령연차/예외 확인. 미공제 원금은 연금저축계좌에 들어 있어도 과세대상 소득으로 일률 합산되지 않음. 연 1500만원은 절대 출금한도가 아니라 세법상 특정 소득 과세판정 기준. [국세청 사적연금](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605).

**#218 — 예적금에서 투자 시작한 실제 사례:** 정기적 분할매수와 목표비중 **리밸런싱은 금융자산 위험관리의 한 방법**이나 주식/채권 동반하락을 막는 보장은 없음. TDF는 은퇴연도에 가까워지며 자산혼합을 조절할 수 있지만 종신 연금을 보장하지 않음. [SEC TDF 투자자보호](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/target-date-funds-investor-bulletin). 커버드콜 분배금이 높아도 총수익률이나 원금보장은 다르며, 고객 실제 수익률은 개인계좌 원장 없음으로 확정할 수 없음. [SEC 자산배분·리밸런싱](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset).

**#219 — 투자교육 범위 제외:** 2025-09-04 스마트폰 구매·요금제·추가지원금 분석이 주요 내용이며 금융투자상품·연금에 대한 체계적 설명 아님. 로스터 '기타 투자' 카테고리와 실제 SRT 내용은 다를 수 있다. 관련 소비자법 변경 **2025-07-22 단말기유통법 폐지**로 지원금 공시의무와 유통점 추가지원금 15% 상한이 폐지됐고 25% 요금할인은 유지된다. 이 확인은 **투자교육 주장 검토 65건에 포함하지 않음**. [정부 정책브리핑](https://www.korea.kr/news/policyNewsView.do?newsId=148953626).

**#220 — 국민연금 추납·실업크레딧:** 추납은 가입자 적격이면서 납부예외/적용제외 등 대상기간이 있으면 **최대 119개월** 가입기간을 늘릴 수 있으나 일률 원금보장 재테크 수단은 아님. 실업크레딧은 적격 구직급여 수급자가 보험료 본인25% 부담시 국가75%, 생애최대12개월 지원. [국민연금공단](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0097M0.do). 가장 중요한 시행후 정정: **2026년부터 추납보험료는 신청월의 기준소득월액 × 납부기한이 속한 달의 보험료율 × 대상개월수**. 2025-11 법개정 전 영상에서 ‘신청 월만 중요하며 그 뒤 같은 금액’이라는 설명을 현재 제도로 그대로 적용 금지. [국민연금공단 추납 계산](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do).

## 3. 대상별 주요 주장 검토 수

| 영상 | 원본 cue | 주장 건수 | 1차 확인 | 조건부 | 미확정 가정 | V3 |
|---|---:|---:|---:|---:|---:|---|
| #216 | 690 | 16 | 4 | 12 | 0 | 승인 |
| #217 | 470 | 17 | 6 | 9 | 2 | 승인 |
| #218 | 937 | 14 | 3 | 10 | 1 | 승인 |
| #220 | 1108 | 18 | 4 | 11 | 3 | 승인 |
| #219 | 1036 | — | — | — | — | 제외 |
| **합계** | **4241** | **65** | **17** | **42** | **6** | **4편 승인·1편 제외** |

## 4. 주장 ID·원본 cue·타임코드 및 근거 65건

각 원본 자막은 외부에 게시하지 않고 사용자 비공개 시간코드에 연결한 금융 주장의 의역만 공개한다. 원본 구간별 판정 근거는 `data/subtitles/pilots/<video_id>.json#claims[*].verification_evidence`, 정식승인 분석은 `data/analysis_events/<video_id>.json#core_claims`에 일대일 저장.

### #216 퇴직연금 세제개편과 IRP 인출 순서 — 연금수령 실제연차·과세재원 — 16건

| 주장ID·cue | 시작시각 | 판정 | 주장 의역 | 근거 대조·활용 제한 | 근거 URL |
|---|---|---|---|---|---|
| `b5OV0BEle_o-01` / 38 | 00:01:13.360 | PRIMARY_CONFIRMED | 퇴직연금 절세와 사적연금 소득과세는 구별해야 한다 | 퇴직금 이연퇴직소득의 감면율과 개인납입 공제분·운용수익의 연금소득 과세는 서로 다른 산식 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-02` / 71 | 00:02:18.040 | QUALIFIED | 퇴직소득의 20년 초과 실제 연금수령은 원 퇴직소득세의 50%를 적용 | 2026-01-01 이후 적격 연금수령분의 실제 수령연차 21년차부터 50% 적용, 2025 영상당시 법률안과 시행 제도를 구별 | [공식자료](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1034033989) |
| `b5OV0BEle_o-03` / 106 | 00:03:26.640 | QUALIFIED | 퇴직금 실제 연금수령연차와 연금저축계좌의 연금수령연차가 동일하게 자동기산 | 이연퇴직소득 감면의 실제 연금 수령연차와 연금저축 세법상 연금수령한도의 기산은 다른 규정이며 개인계좌 조회 필요 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-04` / 120 | 00:03:56.719 | QUALIFIED | 55세에 IRP에서 1만원 수령신청만 하면 무조건 장기 감면연차가 쌓인다 | 55세·적격 개시/실수령/연금수령연차와 계좌원천요건을 충족해야 하며 신청서 자체만으로 자동 기산 확정 아님 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-05` / 142 | 00:04:29.680 | QUALIFIED | 퇴직금 IRP에 연금 수령을 시작해도 근로·계좌추가 납입을 계속하는 사례 | 직장재직 가능성과 기존 IRP 추가납입 허용·별도계좌 개설은 사업자/상품규정 확인 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-06` / 178 | 00:05:35.759 | QUALIFIED | IRP는 한 금융사에 하나만 개설 가능하다는 일반 규칙 | 금융기관별 IRP 추가계좌 취급/퇴직금·개인추가납입 구분/운용개시 상태에 따라 다르고 전체 금융기관 합산 하나만이라는 규칙 아님 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-07` / 281 | 00:08:37.760 | QUALIFIED | 퇴사와 은퇴를 같은 시점으로 간주하여 IRP 전액 일시금 수령 | 퇴사 시 퇴직급여 수령계좌와 은퇴 후 적격 연금개시는 다르며 세제 이연·퇴직소득세 경감효과가 달라짐 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-08` / 316 | 00:09:38.120 | QUALIFIED | 퇴직소득세가 IRP 입금 시점에 무조건 원천징수된다는 설명 | 적격 IRP로 퇴직금을 수령하면 일반적으로 퇴직소득세 과세를 수령 시점까지 이연 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-09` / 386 | 00:11:34.279 | PRIMARY_CONFIRMED | 이연퇴직소득 연금수령 세율은 원 세액의 70·60·50%로 단계 감소 | 2026 적격 실제 수령연차 1~10년차 70%, 11~20년차 60%, 21년차부터 50%; 다른 재원에는 일괄 적용 금지 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-10` / 421 | 00:12:33.240 | QUALIFIED | IRP에서 먼저 원금이 나오고 나중에 운용수익이 과세되는 인출순서 | 법정 과세제외 납입원금·이연퇴직소득·공제원금/운용수익 순위 확인 필요, 선입선출 임의선택 불가 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-11` / 456 | 00:13:30.839 | PRIMARY_CONFIRMED | 연금저축/IRP 계좌별 연금수령한도 초과액은 연금외수령 과세 가능 | 법정 연금수령한도는 개별 적격계좌 기준으로 판단하며 1500만원 사적연금소득 과세기준과 다름 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-12` / 487 | 00:14:23.959 | QUALIFIED | 퇴직급여 재원은 사적연금 과세소득 연1500만원에 모두 합산 | 이연퇴직소득 적격연금수령은 보통 연1500만원 공제원금/수익의 선택적 과세판정에서 구분 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-13` / 526 | 00:15:32.680 | QUALIFIED | 연금수령한도 제한이 끝나면 인출 전액 무조건 비과세 | 연금수령한도 규정 적용제외와 재원별 납부할 연금·퇴직소득세는 별개의 문제 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-14` / 561 | 00:16:35.600 | PRIMARY_CONFIRMED | IRP 이연퇴직금과 세액공제 받은 개인납입금/운용수익은 과세재원 분류가 다름 | 퇴직금은 원 퇴직소득세 경감, 공제원금·운용수익은 적격 연금소득세 또는 연금외수령 기타소득세 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `b5OV0BEle_o-15` / 596 | 00:17:46.080 | QUALIFIED | 세액공제 받지 않은 연금저축 원금도 운용수익만큼 동일 세율을 적용 | 미공제 원금은 적격 증빙시 과세제외, 해당 원금에서 발생한 운용수익은 별도 과세대상 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `b5OV0BEle_o-16` / 666 | 00:19:55.039 | QUALIFIED | 미공제원금의 무세금 인출이 퇴직소득세와 사적연금세율보다 유리 | 실제 인출순서·계좌 이력/원금 규모·향후 배분 세액을 확인해야 하며 모든 퇴직자는 같은 원천구성이 아님 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |

### #217 은퇴자를 위한 연금저축 활용팁 — 퇴직연금 운용·수령한도·1500만원 — 17건

| 주장ID·cue | 시작시각 | 판정 | 주장 의역 | 근거 대조·활용 제한 | 근거 URL |
|---|---|---|---|---|---|
| `l0Q-2Ah-ba8-01` / 27 | 00:00:56.440 | QUALIFIED | 노후준비는 퇴직연금과 개인연금 자금을 함께 점검 | 계좌별 현금화/수령시점/세액공제와 국민연금 기여를 분리한 종합계획이 적합하나 단일 최적순서 없음 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `l0Q-2Ah-ba8-02` / 79 | 00:02:45.599 | QUALIFIED | 퇴직연금 계좌 안 미운용자금은 원리금보장 상품 등 대안을 검토 | 원금보장예금도 이율·기간·예금자보호·계좌위험자산 규정을 확인, 모든 IRP현금을 예금으로 즉시 바꾸는 조언은 아님 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `l0Q-2Ah-ba8-03` / 105 | 00:03:38.640 | QUALIFIED | 현금성 자산은 당장 팔아 최고금리 상품으로 갈아타야 한다는 표현 | 투자목적·원리금보장 기간/조기인출/수수료·환매차익 확인, 단순 표면금리만으로 유불리 확정 금지 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `l0Q-2Ah-ba8-04` / 127 | 00:04:27.360 | PRIMARY_CONFIRMED | 연금저축 일반 수령요건 만55세·가입기간5년 | 일반적 적격 연금수령의 55세 이상/가입기간5년 및 예외 사항 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-05` / 132 | 00:04:38.400 | QUALIFIED | 연금저축 개설 시기가 늦어도 일정 적립기간을 가질 수 있다 | 세제혜택 가능하지만 5년만으로 원금증가와 충분한 연금액 보장되지 않음 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `l0Q-2Ah-ba8-06` / 181 | 00:06:19.000 | HYPOTHETICAL | 은퇴 직전 3년 납입계획을 연금저축에 추가 적립 | 예상 납입액·연금개시전 잔여기간·결정세액에 따라 적정성 달라짐 | [공식자료](https://j.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6596) |
| `l0Q-2Ah-ba8-07` / 209 | 00:07:17.919 | HYPOTHETICAL | 8년 투자하면 적립금 1억원을 넘는다는 사례 | 납입원금·운용수익률·과거수익/손실·수수료에 따라 달라 1억원 확정 성장 아님 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `l0Q-2Ah-ba8-08` / 235 | 00:08:12.560 | QUALIFIED | 자산을 분리해 퇴직급여/사적연금/국민연금을 각각 현금흐름 계획 | 계좌별 자산수령 규정·과세재원 및 공적연금 개시연령이 다름 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-09` / 261 | 00:09:06.680 | QUALIFIED | 월별 수령액을 평생 지급하는 연금처럼 계획 | 개인연금 펀드 인출은 잔액 고갈위험 있어 종신 지급을 보장하는 보험·공적연금과 구분 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `l0Q-2Ah-ba8-10` / 289 | 00:10:06.959 | PRIMARY_CONFIRMED | 연금저축 1억원 첫해 수령한도 1200만원 계산 | 일반 계산: 1억원/(11-1)×120%=1200만원, 실제 적용 기산연차·수령요건 확인 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-11` / 313 | 00:10:57.800 | PRIMARY_CONFIRMED | 연금수령한도는 개별 계좌 기준으로 적용 | 적격 연금수령한도와 연 1500만원 과세대상 사적연금소득 합산 기준은 별개 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-12` / 325 | 00:11:24.560 | PRIMARY_CONFIRMED | 연금저축 출금한도 초과는 연금외수령 과세 가능 | 계좌별 법정 연금수령한도 초과분에 공제원금·운용수익 과세 규정, 미공제원금은 구분 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-13` / 339 | 00:11:52.160 | PRIMARY_CONFIRMED | 연금소득 1500만원 과세기준은 사적연금 계좌 간 해당 과세재원 합산 | 과세대상 공제원금·운용수익에 적용, 이연퇴직금/과세제외 원금/공적연금과 구분 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-14` / 366 | 00:12:45.839 | QUALIFIED | 연금저축계좌에 적립된 돈 전액이 과세소득 | 미공제납입원금은 과세제외·이연퇴직금의 별도 원천세 등 적용; 계좌 명칭만으로 전액 과세 금지 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-15` / 417 | 00:14:28.959 | PRIMARY_CONFIRMED | 연금저축 해지 때 공제금액/운용수익에 16.5% 기타소득세 발생 가능 | 부득이한 사유 또는 미공제 원금·세제별 계좌는 예외, 일률 전액세액 아님 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `l0Q-2Ah-ba8-16` / 444 | 00:15:22.000 | QUALIFIED | 미공제 연금저축 납입액은 출금시 과세제외 가능 | 원천징수/세액공제 내역을 증빙하고 운용수익·인출 우선순위를 확인 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |
| `l0Q-2Ah-ba8-17` / 451 | 00:15:37.279 | QUALIFIED | 1500만원을 초과하는 수령은 무조건 불법/불가능 | 1500만원은 사적연금 과세판정 기준일 뿐 절대 출금한도가 아니며 종합과세 또는15% 선택분리과세 가능 | [공식자료](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605) |

### #218 예적금 투자자의 ETF·TDF·커버드콜 투자와 리밸런싱 — 14건

| 주장ID·cue | 시작시각 | 판정 | 주장 의역 | 근거 대조·활용 제한 | 근거 URL |
|---|---|---|---|---|---|
| `7JqAdMGokqk-01` / 9 | 00:00:16.799 | QUALIFIED | 퇴직금을 일시금 고위험 주식에 집중 투자하면 노후에 큰 손실 가능 | 퇴직금의 유동성·인출시점 위험과 자산분산 필요 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-02` / 101 | 00:03:17.840 | HYPOTHETICAL | 고객이 시장 하락시 나눠 산 개인 거래사례 | 개인 거래실적 원장 미확보, 재현 가능한 수익률 증거로 사용불가 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-03` / 149 | 00:04:49.199 | PRIMARY_CONFIRMED | 상대적으로 비중이 낮아진 자산을 사는 리밸런싱 | 목표 비중 회복을 위해 언더웨이트 자산에 납입하거나 매도·매수 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-04` / 186 | 00:05:59.199 | QUALIFIED | 시장상황에 흔들리지 않는 정기 적립 | 매매규율에는 도움되지만 시장손실을 막는 보장은 아님 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-05` / 297 | 00:09:31.760 | QUALIFIED | 계좌증가액으로 연간 투자성과 평가 | 납입/인출/분배금과 실현손익을 반영해야 실제 수익률 산출 가능 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-06` / 407 | 00:12:58.000 | PRIMARY_CONFIRMED | 주식급등 때 목표 주식비중을 초과하는 포트 리밸런싱 | 목표비중에서 벗어난 자산을 매도/추가납입으로 조정 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-07` / 452 | 00:14:21.680 | QUALIFIED | 리밸런싱은 비용·세금과 무관하게 반드시 빈번하게 실시 | 리밸런싱 효익과 거래비용·과세를 고려한 주기/밴드 선택 필요 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-08` / 502 | 00:15:54.240 | PRIMARY_CONFIRMED | TDF는 은퇴목표연도에 따라 위험자산 비중 조절 | 글라이드패스 상품별 상이, 2030 등 목표연도만으로 성과보장 불가 | [공식자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/target-date-funds-investor-bulletin) |
| `7JqAdMGokqk-09` / 552 | 00:17:40.919 | QUALIFIED | TDF ETF가 모든 TDF보다 더 저렴하다는 설명 | 총보수·기타비용·스프레드 및 하위펀드 보수를 합산 확인 | [공식자료](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/target-date-funds-investor-bulletin) |
| `7JqAdMGokqk-10` / 593 | 00:19:02.240 | QUALIFIED | 커버드콜 ETF 분배금이 높으면 총수익률도 높은 것으로 평가 | 분배금+가격변화(세금/재투자)와 콜매도 상방제약 구별 | [공식자료](https://www.optionseducation.org/strategies/all-strategies/covered-call-buy-write) |
| `7JqAdMGokqk-11` / 651 | 00:21:07.880 | QUALIFIED | 유사한 기초지수 ETF 다중보유로 투자위험 완전 분산 | 상관관계가 높은 지수의 중복노출은 실질 분산에 한계 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-12` / 751 | 00:24:19.960 | QUALIFIED | 퇴직 IRP에 목돈이 들어오면 즉시 전액 주식에 투자 | 현금흐름 필요시점·적격 상품·손실감내도 확인 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `7JqAdMGokqk-13` / 803 | 00:25:57.720 | QUALIFIED | 은퇴 후 몇 년 남았으면 단기 급락이 위험하지 않다 | 연금 인출순서·생활비 지출시점에 따라 위험이 커질 수 있음 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |
| `7JqAdMGokqk-14` / 889 | 00:28:46.519 | QUALIFIED | 예금투자자가 늦게 시작한 소액 위험자산 분산 | 비상자금·학습과 위험허용도를 먼저 점검 | [공식자료](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset) |

### #220 국민연금 추납·실업크레딧·개인보험 노후 자금 사례 — 18건

| 주장ID·cue | 시작시각 | 판정 | 주장 의역 | 근거 대조·활용 제한 | 근거 URL |
|---|---|---|---|---|---|
| `IK_VUi3PUIU-01` / 201 | 00:06:47.560 | QUALIFIED | 소액으로 ETF를 여러 차례 사 보며 투자 위험을 학습했다는 개인 경험 | 자산시장 입문·학습에는 도움될 수 있지만 소액매수 자체로 수익·원금안전이 보장되지 않음 | [공식자료](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `IK_VUi3PUIU-02` / 353 | 00:11:52.600 | QUALIFIED | ISA·연금저축·IRP 여러 계좌를 나누면 무조건 유동성이 좋아진다 | 계좌별 세액공제/의무기간·인출제약·거래비용을 고려해야 유동성이 달라짐 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `IK_VUi3PUIU-03` / 401 | 00:13:25.959 | QUALIFIED | 전체 자산 규모를 표·그래프로 관리하면 포트폴리오 파악에 도움 | 순납입·평가손익과 외부입출금 분리해야 수익률이 정확하며 표만으로 수익성 보장 불가 | [공식자료](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `IK_VUi3PUIU-04` / 485 | 00:16:08.040 | PRIMARY_CONFIRMED | 국민연금 납부 공백기간을 나중에 추후납부로 살릴 수 있다 | 공단 추납 대상기간·가입자 자격 충족시 최대119개월까지 가입기간 증가 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do) |
| `IK_VUi3PUIU-05` / 529 | 00:17:30.200 | HYPOTHETICAL | 국민연금을 과거 4~5년 냈다는 가족 이력 | 개인 가입기간 원장 미확인, 공단 예상연금액과 추납 적격 개월수 직접 조회 필요 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0097M0.do) |
| `IK_VUi3PUIU-06` / 551 | 00:18:19.360 | PRIMARY_CONFIRMED | 추납한 기간을 통해 국민연금 가입기간을 늘릴 수 있다 | 법정 적격 과거 납부예외·적용제외·일부 군복무만 추납 가능, 단순 미납 체납금과 다름 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do) |
| `IK_VUi3PUIU-07` / 573 | 00:19:01.840 | QUALIFIED | 최대 20년 이상 공백도 전부 추납할 수 있다는 인상 | 법정 최대119개월(10년 미만)이며 단순 장기 공백 전액을 제한없이 복원할 수 없음 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0097M0.do) |
| `IK_VUi3PUIU-08` / 601 | 00:19:57.600 | QUALIFIED | 연금 추납이 고소득 가구에 무조건 높은 투자수익을 제공 | 연금액 증가효과는 납부 개월·수령나이·소득·생존기간과 보험료에 좌우, 고정 IRR 보장 아님 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do) |
| `IK_VUi3PUIU-09` / 651 | 00:21:26.440 | PRIMARY_CONFIRMED | 실업크레딧은 구직급여 수급 중 연금보험료 일부를 국가가 지원 | 적격 실직자가 연금보험료 본인25% 부담하면 정부75%, 생애최대12개월 지원 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0048M0.do) |
| `IK_VUi3PUIU-10` / 701 | 00:23:06.039 | QUALIFIED | 추납은 퇴직 후 소득이 낮을 때 신청하면 납입료도 언제나 그 수준으로 고정 | 2026법은 신청월 기준소득월액과 **납부기한이 속하는 달의 보험료율**을 결합하며 가입자격·임의가입 상한·보험료율 변화 고려 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do) |
| `IK_VUi3PUIU-11` / 749 | 00:24:35.240 | QUALIFIED | 추납 비용에는 신청시점만 중요하고 납부월은 무관하다는 발언 | 2025 구제도는 신청월 보험료율 참고; 2026-01 법개정 후 보험료율은 납부기한 월 기준으로 변경, 2025 동영상 설명의 현행 재사용 금지 | [공식자료](https://m.nps.or.kr/pnsgdnc/nscvrgdata/getOHAE0002M1.do?menuId=MN24000898&pstId=ZZ202500000000001465) |
| `IK_VUi3PUIU-12` / 793 | 00:25:58.399 | PRIMARY_CONFIRMED | 추납은 국민연금공단에 신청하여 대상기간 확정 | 현재 소득신고 가입 또는 임의(계속)가입 상태인지와 납부예외 이력 및 대상기간을 확인 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do) |
| `IK_VUi3PUIU-13` / 801 | 00:26:14.559 | QUALIFIED | 추납 수천만원을 납부하면 누구나 노령연금 월액이 큰 폭으로 늘고 높은 수익 보장 | 가입기간 증가효과 있으나 개인 소득재산·기초연금 감액·수령연령·총수령기간 등에 따라 실제효과 상이 | [공식자료](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0097M0.do) |
| `IK_VUi3PUIU-14` / 925 | 00:30:14.240 | QUALIFIED | 개인연금 보험의 종신 수령 조건과 해약환급금을 비교 | 기존 상품 계약 최저보증·중도해약 수수료·계약자/수익자 및 세제 적격성을 확인 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `IK_VUi3PUIU-15` / 969 | 00:31:34.840 | HYPOTHETICAL | 보험 원금·연금개시 후 연140만원씩 지속 수령 사례 | 실제 보험약관/해약환급금/종신연금 확정·예상표 미확보, 사례의 연금수령액 일반화 금지 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `IK_VUi3PUIU-16` / 1002 | 00:32:39.120 | QUALIFIED | 개인보험 원금은 그대로 있으면서 연금이 계속 생긴다는 설명 | 연금소득은 보험/투자형 계약구조별로 원금차감 또는 준비금 감소 가능, '원금 불변+종신 수익'은 보장 아님 | [공식자료](https://www.samsungpop.com/ux/kor/pension/introduce/taxation/tab_irp.pop) |
| `IK_VUi3PUIU-17` / 1053 | 00:34:10.760 | HYPOTHETICAL | 토지 매각시 40%의 세금이 언제나 발생 | 토지 취득/양도가·보유기간·사업용 여부·세율·지방세 등 따라 과세 달라져 개인사례 40% 일괄적용 금지 | [공식자료](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |
| `IK_VUi3PUIU-18` / 1101 | 00:35:57.680 | QUALIFIED | 개인연금·예적금 만기 자금을 함께 노후 현금흐름으로 계획 | 각 계좌 만기·대출·보험적격성과 인출세금·물가를 합산하여 계획 | [공식자료](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) |

## 5. 연구 한계 및 종합 원장

- #216~218·220의 타임코드 주요 금융 주장 **65건**만 승인함. 원본 음성·영상/공개 한국어 전문 일치 검사를 실시했다고 주장하지 않는다.
- #216 실제 IRP 인출/퇴직소득세 감면연차 미확정; #217 노후 자산 시뮬레이션의 개인 납입·환급내역 미확정; #218 개인 포트 수익률 원장 미확정; #220 가족 국민연금 납부 공백/추납확인서·개인보험 원표 미확정.
- #219는 원본 **1,036 cues/79,451 bytes**를 검증했으나 투자교육이 아닌 이동통신 소비자 정보이므로 V3 과제 제외. 다른 4편 SRT **3,205 cues/249,161 bytes**.
- 누적 이전 **212편·3,495건** + 신규 **4편·65건** = **216편·3,560건**. 잔여 791편 중 **575편 미승인**(기존 사용자 승인 #204 원본부재와 #219 비투자 분야 제외 포함). 이 수치는 GitHub Push·PR 둘 다 성공해야 최종 V3 완료.
- 기존 OPEN 24건 유지. 비공개 자료 Google Drive 미저장, 원본 SRT·ZIP GitHub 미게시, `main` 변경 금지.
