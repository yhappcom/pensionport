# 박곰희TV #231~235 — 원본 SRT·공식자료 V3 검증 종합보고서 (2026-10-28)

## 결과
**금융교육 선별 주장 78건 / 5편 V3 승인 범위**, `PRIMARY_CONFIRMED 14` / `QUALIFIED 51` / `HYPOTHETICAL 13` / `CONTRADICTED 0`.

승인은 검토 대상 교육원리와 정정·예외의 근거 기록에만 적용하며, 미확정 가정 13건 또는 개인 투자 수익을 사실로 인증하지 않는다. 원본 오디오·영상프레임·공개 한글 자막 독립 대조는 수행하지 않았다. 2025 정부안이나 2023 당시 시장 규정을 현재 적용 규칙으로 잘못 재사용하지 않도록 시행일을 별도 표시했다.

## 원본·불변 처리
- 개인 Google Drive 원본: https://drive.google.com/file/d/1CJvWcNyjcMM5xrjio_YFWSbr57-1J--1/view?usp=drivesdk
- ZIP SHA-256 `9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10`; 2,913,470바이트, 실제 원본 99개 SRT. 이번 5편 SRT 2,490cue·192,966바이트.
- `data/subtitles/registry_231_235_20261028.json`에 각 영상 ID, cue 수, 개별 SRT 원본 SHA·크기 등록. ZIP/SRT 본문은 공개 GitHub 저장 금지.
- 기존 #1~230 V3 기록, OPEN 24건, #204 원본 부재, #219 비투자 제외 유지. `main` 변경 금지.
- 기존 #216~220 연구 문서의 과거 ZIP 전체 해시와 2026-10-27 업로드 이후 저장본 해시는 불일치; 현재 구간은 사용한 저장본 SHA로 고정하며 과거 바이너리 동일성은 단정하지 않는다.

## 영상별 최종 검증
| 영상 | video_id | 원본 cue | 주장 | 1차 확인 | 조건부 | 미확정 | 정정 요지 |
|---|---|---:|---:|---:|---:|---:|---|
| #231 세법 정부안 | `C7KctGzg-K0` | 214 | 16 | 5 | 10 | 1 | 고배당 세율·대주주 기준은 확정법과 구분 |
| #232 공모주 상장일 | `WIXWPJjhF50` | 185 | 12 | 1 | 8 | 3 | 2023-06-26 이후 60~400% 상장일 제한 |
| #233 공모주 청약 | `BK4AlJFw9SM` | 504 | 15 | 4 | 10 | 1 | 균등배정·동일인 중복청약 제한 |
| #234 60세 연금전략 | `iP75FC0Gg0g` | 782 | 17 | 2 | 11 | 4 | 연기연금·ISA 만기전환 및 담보대출 약관 |
| #235 적립식 수익률 | `1Hzf1eiM-t8` | 805 | 18 | 2 | 12 | 4 | 수익금·납입금·기간조정 수익률 구별 |
| **합계** | | **2,490** | **78** | **14** | **51** | **13** | **0 직접 반증** |

## 주요 시행법·공식자료 반영
1. **#231 고배당 분리과세**: 당시 정부안 14%/20%/35%와 2026 법률 시행 세율 14%/20%/25%/30%를 분리. 개별 고배당기업 법정 요건도 개편안과 최종 시행규정으로 구분. [국세청 2026-03-09](https://www.nts.go.kr/nts/na/ntt/selectNttInfo.do?mi=2201&nttSn=1349597)
2. **#231 주식 양도세 대주주 기준**: 제안된 50억원 → 10억원 축소는 철회되었으며 2026 국세청 공식 안내에는 50억원 또는 지분율 요건(코스피 1%, 코스닥 2%, 코넥스 4%)이 적용. [국세청 2026-08-05](https://www.nts.go.kr/nts/na/ntt/selectNttInfo.do?nttSn=1353905)
3. **#231 법인세·거래세**: 법인세 과표 10/20/22/25%와 2026 코스피 거래세 0.05%+농특세0.15%, 코스닥 0.20%를 세목별로 구별. [국세청](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7746&mi=2220) / [증권사 법령시행 안내](https://p.tossinvest.com/ko/post?category=52&id=18410&type=notice)
4. **#232 공모주 상장일**: 2023-06-26 종전 90~200% 시초가+당일 ±30% 제도를 폐지, 공모가를 기준가격으로 60~400%를 신규상장일에 적용. [한국거래소](https://regulation.krx.co.kr/contents/RGL/03/03010100/RGL03010100T6.jsp)
5. **#233 청약배정**: 일반투자자 공모주 배정물량의 절반 이상 균등배정 및 동일인 여러 증권사 중복배정 제한. 청약증거금 50%는 상품별 투자설명서에서 검증해야 함. [금융위원회](https://www.fsc.go.kr/po010101/76078)
6. **#234 노령연금**: 출생연도별 개시연령과 최대 5년 연기, 연 7.2% 가산. ISA 의무가입 3년, 만기 이후 60일 이내 연금계좌 전환의 조건부 세액공제(전환액 10%, 최대 300만원의 공제 대상 납입액) 구분. [국민연금공단](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0100M0.do) / [금융기관 ISA 설명](https://www.samsungpop.com/ux/kor/finance/isa/isainfo/intro.do)
7. **#234 대출**: 인터뷰에 제시된 연금저축 담보대출 금리 3~5%, ETF 불가 및 TDF 교체 시 한도 증액 여부는 금융사 약정·상품 범위 미확보로 미확정 판정. 금융기관 전체에 일반화 금지.
8. **#235 성과 지표**: 적립식투자 정액매수 원리와 손실 가능성, 외부현금흐름을 제거하는 TWR과 시기·규모를 반영하는 MWR의 차이. 2025 개인 계좌 표·수익률은 거래원장 부재로 미인증. [미 SEC](https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging) / [CFA Institute](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/rates-and-returns)

## 원본 자막 주장별 전체 표 — 78건
아래 5개 문서에 **각각 주장 ID·SRT cue 번호·밀리초 시간코드·의역·판정·공식자료 URL·활용 제한**을 보존한다. 상세 `verification_evidence`는 `data/subtitles/pilots/<video_id>.json#claims`, 승인 교육 분석은 `data/analysis_events/<video_id>.json#core_claims`에 동기화한다.

- [#231 주장 16건](VIDEO231_V3_CLAIM_TABLE_20261028.md)
- [#232 주장 12건](VIDEO232_V3_CLAIM_TABLE_20261028.md)
- [#233 주장 15건](VIDEO233_V3_CLAIM_TABLE_20261028.md)
- [#234 주장 17건](VIDEO234_V3_CLAIM_TABLE_20261028.md)
- [#235 주장 18건](VIDEO235_V3_CLAIM_TABLE_20261028.md)

**2026년 실무 활용 원칙:** 공식 근거가 확인된 원리라도 개인별 세금·청약·퇴직계좌 처리·가정 수익률을 자동으로 보증하지 않는다. 숫자 검증 미완료 항목 13건은 미확정으로 추적한다.
