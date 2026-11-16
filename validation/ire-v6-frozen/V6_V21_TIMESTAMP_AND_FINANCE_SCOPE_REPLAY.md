# IRE V6 V21 — 영상 게시시점·금융규정 소급적용 차단 및 미사용 원본 5편 교차검증

**실행일:** 2026-11-10 KST. **기준 V20 커밋:** `db74afdc24f11be50d6af5d1e503d89e4ec5f9c4` (Draft PR #53).
**원본 소유자 제공 1–70 ZIP SHA256:** `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`.
**비공개 선정 원장 SHA256:** `c0a71784c9bfea0090d31b9051871ef7489db45b9b38c27560a4d3285bfbdd19`. 해당 선정 목록은 원문 의미 열람 전에 파일/로스터 메타데이터로 12개 과거 보정 영상 제외 후 원본 SHA 기준 5편 고정. 기존 사전 등록 9편/6,829 cue 블라인드 cohort가 아니며 독립 골드가 아니다.
**공개 안전:** 원본 SRT 텍스트, 실제 원자 주장 전문, 사내 DB, 채팅 참조 대조표와 개인 금융정보는 공개 GitHub에 게시하지 않음.

## A. 실제 공개 YouTube 메타데이터로 확인한 영상 게시시점

사용자 Library **박곰희TV_전수영상_791편_최종.xlsx**와 공개 YouTube 비디오 페이지의 `datePublished`/`uploadDate` 및 `identifier`/채널명을 **각 ID별로 독립 조회**했다. 아래 날짜는 업로드 메타데이터이며 녹화일·발언이 이루어진 시점으로 인증하지 않는다. 출처 URL 형식: `https://www.youtube.com/watch?v=<video_id>`.

| ID | 수집 로스터 게시일 | YouTube 원본 ISO-8601 오프셋 기록 | 한국시간 날짜 | 2026-10-01 규칙 적용성 |
|---|---|---|---|---|
| `Bu36RrQMkVU` | 2026-09-01 | 2026-09-01T01:30:38-07:00 | 2026-09-01 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `nCXWFko0TaA` | 2026-09-09 | 2026-09-09T18:00:12-07:00 | 2026-09-10 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `HqLTZzXirkQ` | 2026-07-14 | 2026-07-14T02:00:38-07:00 | 2026-07-14 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `09ojTPmKlQg` | 2026-07-27 | 2026-07-27T02:00:37-07:00 | 2026-07-27 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `8Zh1q4Ziv4c` | 2026-07-21 | 2026-07-21T02:00:25-07:00 | 2026-07-21 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `yDt8Ki7d_Yk` | 2026-08-24 | 2026-08-24T19:06:07-07:00 | 2026-08-25 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `VKr060rIirM` | 2026-09-16 | 2026-09-16T18:00:26-07:00 | 2026-09-17 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `IMJfPgmnFwc` | 2026-09-13 | 2026-09-13T18:00:09-07:00 | 2026-09-14 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `33HPIrzl6xI` | 2026-08-27 | 2026-08-27T01:30:31-07:00 | 2026-08-27 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |
| `EYya0e4APBE` | 2026-09-07 | 2026-09-07T06:00:27-07:00 | 2026-09-07 | FUTURE_RULE_NOT_VALID_AT_PUBLICATION |

- 로스터의 날짜는 YouTube가 제공하는 **오프셋 지역 날짜**와 10/10 일치. 한국시간(KST)으로 변환 시 4건은 다음 날짜로 넘어간다(영상명/게시시점 혼동 방지).
- 10편 **모두 2026-10-01보다 먼저 게시**. 따라서 그날 시행한 연금계좌 관련 **소득세법 시행령 제40조의3 현행 문구로 과거 영상 발언을 소급 확정**해서는 안 된다.
- 법제처 2026-07-01 시행 전 법령 판본이 존재함은 확인: https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=02&joNo=0040&lsiSeq=286211&urlMode=lsScJoRltInfoR . 다만 **당시 제40조의3의 관련 조항 전문 바이트 SHA와 동일한 의미의 개정 전 문구를 현재 원본별로 고정·검토하지 않았다**. 시점상 후보라고 해서 승인 아님.
- 공개 페이지 메타데이터의 실제 바이트·신뢰 주체 서명, 사용자 로스터의 외부 소유자 신원 서명 및 **녹화일** 미확보. 검증 상태는 `PUBLISHED_DATE_OBSERVED_NOT_SIGNED`, `SPEECH_DATE_UNKNOWN`.

## B. 새 개발용 5편 전체 자막 구조 실증 (V20)

| 실제 영상 ID | 원본 cue | ChatGPT 원자 후보 | 최초 원시 의미 경고 | 전체 원문 frontier 검토 요청 |
|---|---:|---:|---:|---:|
| `Bu36RrQMkVU` | 39 | 10 | 0 | 14 |
| `nCXWFko0TaA` | 37 | 11 | 2 | 14 |
| `HqLTZzXirkQ` | 39 | 11 | 0 | 18 |
| `09ojTPmKlQg` | 35 | 9 | 0 | 14 |
| `8Zh1q4Ziv4c` | 34 | 11 | 2 | 17 |
| **합계** | **184** | **52** | **4** | **77** |

전수 184/184 cue 상태를 실제 SRT 원문 SHA에 연결, V20 `verify_source`/`audit_host_atomic_exchange`/`audit_semantic_risks`/`source_first_semantic_frontier` 실제 실행 **구조 통과**. 최초 원시 V14 위험 4건에서 **원문 조건·예외 연결 보완으로 1건 원시 위험 유지**, 나머지 1건은 질문과 조건부 답변이 같은 cue에 혼재해 별도 출처절 판정이 필요하다. 원래 원시 경고와 후속 영수증은 append-only 유지하며 지운 후 자동 승인하지 않는다. **52건은 ChatGPT가 제안한 후보이지 외부 참값/완전한 의미 재현율이 아니다.** 77건 frontier는 휴리스틱 위험 검토 요청이지 77개의 실제 오류 확정 아님.

## C. 실제 원본에 대한 금융 의미 문제와 공식 기관 비교

| 영상 | 원문에서 찾은 위험 | 대조 및 보류 판정 |
|---|---|---|
| `nCXWFko0TaA` | 예상 퇴직연금 2억4천만원 / 개인연금 2억원에서 **월 6%** 분배 표현을 사용하면서 월 120/100만원 예상 | 각각 `2.4억×6%÷12=120만원/월`, `2억×6%÷12=100만원/월`: **연 6%의 월 분할 지급 산술**에 해당. 6%/월이면 월 1,440만원/1,200만원으로 설명치와 12배 차이. 새 `RATE_PERIOD_CONTRADICTION_REVIEW`, 배당지급/원금·세금·수익보장 미확인 |
| `nCXWFko0TaA` | 연 5~7% 수익을 10년 누적하면 “두 배”라고 설명 | 복리 배율 5%는 1.6289배, 7%는 1.9672배. **7%일 때 약 2배**지만 5%에서는 아니다. 산술 시나리오와 수익 보장 분리 |
| `8Zh1q4Ziv4c` | 일반계좌 **ETF 매매차익 모두 15.4%**라는 설명 | 한국거래소·운용사/투자자교육 공식자료에 따른 국내주식형 ETF 매매차익 비과세 vs 국내상장 기타 ETF 배당소득 과세 vs 해외상장 자산 별도 분류 필요. [KRX](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp) / [삼성 KODEX](https://www.samsungfund.com/etf/insight/guide/view05.do). `ETF_GAINS_TAX_TYPE_SCOPE_MISSING` 미승인 |
| `8Zh1q4Ziv4c` | IRP **중도인출이 전혀 불가**라는 단정 | 법정 사유(무주택자 주택구입, 일정 요양, 파산 등)에 따른 개인형 IRP 중도인출 가능. [KB퇴직연금 제도 안내](https://okbfex.kbstar.com/quics?page=C019571). `IRP_MIDTERM_WITHDRAWAL_LEGAL_EXCEPTIONS_MISSING` 미승인 |
| `8Zh1q4Ziv4c` | 미공제 연금저축 원금은 언제든 자유 인출, 과세이연·연금 수령 세율 일반화 | 세액공제 여부·과세제외/과세소득·인출순서·해지와 연금외수령 차이·계좌종류·발언 당시 시행 규정 필요. 2026-10 시행 조항을 7월 게시 영상에 소급하지 않음. `AS_OF_LAW_BODY_UNPINNED`, `INDIVIDUAL_APPLICATION_OPEN` |
| `HqLTZzXirkQ` | 2026 국민연금 납부율 9.5%, 연금저축+IRP 납입 1,800만원 / 세액공제 대상 900만원, 55세 수령 | 9.5%는 [국민연금공단 2026 보험료율 안내](https://ma.nps.or.kr/pnsinfo/ntpsklg/getOHAF0016M0.do?menuId=MN24001108)로 확인. 그 외 납입/공제 구분과 55세 + 법정 추가 조건·개인 결정세액 별도 확인. `RULE_STRUCTURE_NOT_INDIVIDUAL_APPROVAL` |
| `Bu36RrQMkVU`, `09ojTPmKlQg` | 특정 미래산업 성장 보장·전설적 투자 법칙/주택 매수 절대 우위 | 교육적 의견·가치 판단이며 실증/투자수익 보장과 구분. ASR의 정밀 수치는 회수 불가 시 OPEN |

이상의 4가지 [연금 연수익 과대일반화, ETF과세, IRP 절대표현, 월6% 분배] 위험은 **모델 후보를 소스에서 뽑는 단계와 공식 규정·산술의 진실을 판정하는 단계를 분리**한다. 계산식이 맞아도 과거 2026년 영상의 실제 녹화일이나 개인 사정이 확보되었다는 뜻은 아니다.

## D. 신규 V21 방어 코드와 검증 계약

- **신규 모듈:** `ire/v6/temporal_finance_gate.py` — 오프셋 포함 native 공개 메타데이터·개별 SRT SHA·로스터 날짜·법령 시행 범위를 구별하고 **업로드 시점에 미래/이미 폐지된 법령**을 현재 적용 법령으로 승인하지 않는 `publication_temporal_rule_gate`; 정확한 Decimal 월/연 분배 산술 감시 `audit_rate_frequency`; ETF/IRP 전면 단정 원문 휴리스틱 위험 `flag_legal_scope_overgeneralization`.
- 모든 함수 반환값: `recording_time_independently_known=false`, `independent_gold=false` 취지의 비승인 상태; 법규 본문 원본 해시나 개인 적용성은 외부로부터 별도 신뢰된 경우에만 입력할 수 있으나 **그 경우에도 단독 법령 승인 불가**.
- **신규 15개 합성 단위·공격 시험:** KST 날짜 경계, 오프셋 누락·위조 ID·불가능한 날짜, 법령 미래 시행/종료/본문 해시, 월·연 금액 산술 12배 오해, 잘못된 ETF·IRP 일반화 탐지와 예외를 설명한 문장은 오경보 배제. 로컬 Python 3.13에서 15/15 PASS. 부분 추출본 전체 V6 discover는 오래된 메인 저장소의 `data/claims.jsonl` fixture가 없어 완료 불가 → GitHub full checkout CI가 공식 판정.
- **실제 바이트 연결:** 총 10개 YouTube ID의 실제 공개 `datePublished`/원본 SRT SHA/로스터 날짜를 함께 검증, ETF/IRP 위험 원문 구간에 대한 문자열 결박 SHA 및 2건 월분배 산술 반례 실행. 모두 본문 비공개, 해당 SHA와 날짜만 보고.
- **원본 소유자 핀·문맥 검토 제한:** 이 실행에서 zip 원본을 통해 자체 생성한 소유자 inventory는 외부 서명 아님. 실제 인간 독립 골드 및 정밀도·재현율 미측정. 사전 등록 9편/6,829 cue 원본 `201-300.zip` 미확보. 승인된 V5/116/P4 및 `main` 불변, PR #53 Draft.

## E. 품질 판정과 다음 작업

`S2/S5_SOURCE_STRUCTURALLY_AUDITED=true`, `CHAT_CANDIDATES=52`, `PUBLIC_UPLOAD_DATE_OBSERVED=10`, `REGULATORY_RETROACTIVITY_DETECTED=10`, `RATE_PERIOD_MISMATCH=2`, `LEGAL_SCOPE_HAZARD=2`, `RAW_LEXICAL_RISK_RETAINED=1`, `INDEPENDENT_GOLD_RECALL_UNMEASURED`, `FINANCIAL_FACTS_NOT_APPROVED`, `P0_NO_GO`, `S6/S7_BLOCKED`.

다음 실행은 (1) 2026-07-01 당시 제40조의3 적용 판본 원문을 별도 SHA 고정해 계좌 인출 규정의 시점 확인, (2) 새 5편 남은 질문·조건 원자 인용 분리와 전체 77 frontier 검토(독립 품질 아님), (3) 변조·월수익 오해·ETF/IRP 전면 단정의 신규 회귀군 확대, (4) 원래 9편 블라인드 아카이브 회수 여부 재검증. **현 V21은 실제 연구 전수 승인이나 791편 확장 허가가 아니다.**
