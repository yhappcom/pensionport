# V166 E4 — 원전 유형 분리 + 운영키·최신 소유자 PIN 안전조회 + B0001 실물 근거 재검증

**2026-11-18 KST · E4 개선 실행 결과. 공식 단계 판정은 E4 FAIL 유지, E5~E7 NOT_RUN, 전체 엔진 NO-GO.**

## 1. 발견한 E4 설계 원인: B0001은 법령 영상이 아니다

비공개 소유자 원본 영상 `5NvtBlmt93Y` 1,481cue 중 B0001 120cue·V6 16원자를 바이트-동일한 실제 `ire.v6.source.verify_source`로 재검증했다. 원본 SHA `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`. **16원자 전부의 원문 `source_refs`가 실제 cue에 존재하는지 다시 확인.**

별도의 ChatGPT 근거 유형 분류를 적용한 결과:

| 검증할 근거 종류 | 16원자 중 |
|---|---:|
| 현행·과거 법령 조문을 근거로 해야 하는 `STATUTORY_FINANCIAL_RULE` | **0** |
| 책 제목·저자 서지 `PUBLISHER_BOOK_BIBLIOGRAPHY` | 2 |
| 책 저자의 원전 투자 원칙 `BOOK_ORIGINAL_AUTHOR_PRINCIPLE` | 1 |
| 버핏 초기 파트너십 역사 `HISTORICAL_PARTNERSHIP_CLAIM` | 2 |
| 편집된 주주서한 선집 수록 범위 `THIRD_PARTY_LETTER_ANTHOLOGY_SCOPE` | 1 |
| 어원·언어 사실 `LINGUISTIC_ETYMOLOGY` | 1 |
| 투자 원칙에 대한 의견 `INVESTMENT_STRATEGY_OPINION` | 2 |
| 개인적 독서 의견 `PERSONAL_SUBJECTIVE_OPINION` | 4 |
| 질문·가정 `HYPOTHETICAL_OR_QUESTION` | 2 |
| 외부 근거 불충분 `UNRESOLVED_CONTEXT` | 1 |

**반면 기존 V123 행에는 16개 중 13개에 `financial_claim=True` 또는 `high_risk=True`가 붙어 있다.** 이 필드는 안전검문상 중요한 *위험 스크리닝*이지 "이 원자는 현행 법령 조문을 원전으로 확인해야 한다"는 주제 분류가 아니다. 예를 들어 **책 원제는 출판사, 파트너십 연혁은 실제 원문 기록, 질문·주관적 평가는 화자 자막**을 검증해야지 국세청 법령 문서를 끼워 맞춰서는 안 된다.

**개선:** `v166_e4_typed_authority.py` + `test_v166_e4_typed_authority.py` 11개 합성 정상·변조 시험 구현. 유형·권한 출처·원자 해시·최종 V123 기존 상태·직접 source_ref cue·검토 메모 SHA를 전수 대조하며, 위험표시만으로 법령 사실을 승인하지 못하고 OPEN도 승격하지 못한다.

**비공개 실제 16원자 분류 영수증 SHA-256:** `58fab2d319e11c32e5f0b481d656835ba948df06283b50086ef7131506412f17`. 이 분류는 **추가 증빙을 찾는 범위를 고정하기 위한 독립 점검 자료**이며, 자체로 승인/법적 근거 검증이 아니다. 원문과 사용자 비공개 리뷰 내용은 GitHub에 업로드하지 않았다.

## 2. 실물 B0001 native V123 직접 재실행 — PASS로 조작하지 않음

실제 2026-11-17 V164 보존본의 동결 `v123_chat_final_gate.py` (정확한 Git blob SHA `17da9fae7d4fcc48087c55ca0d2031ba72a0bb3c`)와 원본 SRT·원자 V6·원본 host 영수증·소유자 전용 원문 Wiley HTML/PDF를 연결해, 별도 chmod 0600 **SQLite 사본**으로 실제 네이티브 V123을 다시 실행했다.

- 동결 V164 **원시 ChatGPT 리뷰**: `ACCEPT_FOR_RESEARCH=7`, `OPEN=8`, `EXCLUDE_FROM_RESEARCH=1`; **`CHAT_FINAL_HOLD_OPEN`**, `finance_open=8`, 정식 발행 불가.
- 이는 이후 V143 source-only 분류에 따라 OPEN 5건을 격리 처리한 **운영상 정리본 `ACCEPT=7, OPEN=3, EXCLUDE=6`**과 *서로 다른 시점의 검토 표현*이다. 혼용하지 않는다. 두 표현 모두 **B0001 HOLD, 정식 발행 0건**이다.
- 실제 동결 V123 재실행 결과 개인 소유 DB 변경 없음. 복사본 `PRAGMA integrity_check=ok`.
- 비공개 재실행 receipt SHA-256 `13f88c8c581f34719fe12638107fc97f8fb300e81e26fd2d2cbc59b7af5a17e9`, 실제 V123 native gate result digest `5fc08dcfc2acd728987ad67ff555e02c71af16c71aa76041b9878773fd74c71d`.
- 원전 1차 서지 원자 **`C00006`**: 실제 source_ref 3개 cue 일치, `V123 ACCEPT_FOR_RESEARCH` 기존 상태 유지; Wiley 공식 원문 바이트 SHA `0b444a35f1f3d6a4355188c4dcfd0d7327c00ba73e75e4c6c0cccb1379525bd2`와 V123 source row의 원문 SHA **실제 동일**, 원서 제목·저자·ISBN 존재 확인. 원음 인증/과거 수익률 증명 아님. 비공개 상세 서지 실물 대조 SHA `3bfe86799d6d4480cea2dbe29991b774a1115124f52299dd62f018e9c62edf28`. **C00002 및 기타 미해결 C00009/C00010은 계속 OPEN.**

## 3. 외부 키·PIN 운영 경로 실제 구현, 별도 비공개 테스트

새 파일 `v166_e4_operator_trust.py`:

- E4 운영용 signing key와 최신 소유자 pin을 **SQLite/봉인 파일과 분리된 절대경로의 비공개 디렉터리**에서만 읽는다. POSIX 소유자 일치·디렉터리 0700·키/PIN 0600·심볼릭 링크·같은 DB 디렉터리 배치 거부.
- 유효한 서명 봉인과 **DB 외부 최신 PIN을 둘 다** 확인한 경우에만, 기존 V126 원자 raw 문자열이 아닌 **E4 서명검증→E2 화자 원문과 리뷰어 의견 분리된 읽기**를 제공.
- 새 부모 승인 PIN은 격리된 운영 PIN 파일에 `flock` 직렬화 + 현재 PIN compare-and-swap + 실제 DB·E4 서명 검문 + fsync/atomic replace로 기록. 충돌/롤백/변조 시 거부. SQLite 부모 커밋 이후 PIN 기록 전에 장애가 발생하면 **자동 인증하지 않고 복구 심사를 요구**.
- GitHub repo에는 **실제 운영키가 없고, 만들어 넣지도 않았음**. CI는 `os.urandom(48)`으로 만든 **격리된 테스트용 키**만 사용.
- `test_v166_e4_operator_trust.py`에서 12개 파일·키·PIN·CAS/무단 DB 수정 시험 + 3개 **실제 합성 V128 SQLite→E4 운영 PIN→E2 안전조회** 시험을 수행.
- 실제 운영 환경의 키 관리 시스템·사용자 계정별 PIN 장기 보관·모든 자문 호출의 해당 경로 고정은 미실증. 로컬 키와 PIN을 보유한 운영자 침해, 동일 사용자 프로세스 내 코드를 우회한 직접 레거시 V126 조회를 불가능하게 한다는 주장도 하지 않는다.

## 4. GitHub 자동 검증과 합격 기준

- [최신 종합 CI](https://github.com/yhappcom/pensionport/actions/runs/44161615816) **9/9 jobs success** — 동결 E1~E3 및 신규 E4 운영 PIN/분류/실물 SQLite 합성 경로 검증.
- E4 대표 보안시험: 부적합 원전·출처 변조·E3/123 보류 부정·운영 파일 권한 0600 미충족·비밀키 교체·잘못된 최신 owner PIN·PIN 롤백/중복 제출·비인증 V126 물리적 SQL 변조·E2 리뷰어 note SHA 위조·다른 영상 자막의 근거 오인.
- 실제 금융의 법적 원문 증명은 별도 재검증해야 하므로, **E4 소프트웨어 CI 성공은 E4 공식 단계 PASS가 아니다**.

## 5. 여전히 E4=FAIL인 이유, 다음 정확한 단계

1. **결정적 설계 미연결:** 기존 `assess_e4_primary_authority_gate`는 `financial_claim/high_risk` 표시가 달린 사실 원자를 금융 법령 출처로 강제 검문한다. 이번에는 **실제 B0001 전체 16원자의 근거 유형을 먼저 식별하는 개선**까지만 했으며, 새 유형별 출처 라우터를 정식 E4 parent-gate의 **필수 입력으로 연결**하는 부분은 아직 안 됐다. 이 부분을 E4 내부에서 계속 개발해야 한다. 단순히 법령 링크를 부착해 서지·역사·의견을 승인하면 안 된다.
2. **실물 E4 종단간 양성 미완료:** 실제 B0001 V123이 HOLD이므로 전체 parent E4 PASS→V128 발행은 불가. C00002 저자 음역/원음, C00009 선집 수록 범위/자본 규모, C00010 초기 파트너십 원문·화자 분해 등 3개 사실 주장 미해결. 한두 서지 사실 교차확인만으로 부모 승인 금지.
3. **운영 배포 실물 미완료:** 새 외부 PIN·비밀키·안전 조회 경로는 합성 사용자 환경에서 검증했지만 실제 운영 비밀키 공급, 키 회전, 장기 PIN 저장소, 투자자문 경로 강제는 배포하지 못했다. 다음 단계에서도 비공개 사용자 자산 원장·API·포트폴리오에 접근하지 않는다.

**순차 상태 E1 PASS, E2 PASS, E3 PASS, E4 FAIL, E5/E6/E7 NOT_RUN, 엔진 NO-GO.**  
기존 `main` 및 동결 V123·기존 V126/V127/V128·개인 원본 SRT/포트폴리오 변경 없음. GitHub 검증 브랜치/draft PR만 수정.
