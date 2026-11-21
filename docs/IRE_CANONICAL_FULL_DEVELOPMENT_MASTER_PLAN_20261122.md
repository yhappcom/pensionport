# IRE 투자 연구·지식통합·자문 시스템 — 전수 재감사 및 단일 개발 마스터 계획

- 작성 기준: 2026-11-22 KST.
- 저장소: `yhappcom/pensionport`.
- 코드·자료 전수 비교 기준 HEAD: `a9448166c84185f3e55f8e72d376594e533b27e8`. 뒤따른 `docs/IRE_FULL_CURRENT_TRACKED_TREE_MANIFEST_20261122.json` 추가는 문서 전용이다.
- 개발 작업 기준: `audit/full-repository-snapshot-20261122` 단일 통합 브랜치. `main` HEAD `d613fd201f4bb077f1ccc74d28dee937b11bfcb2` 보존, 병합/수정 금지, 신규 실험 브랜치 금지.
- 독립 분기 이력 통합 커밋: `3d1beba08ea3037df3c6c46f21cff9a5bb0374db`.
- 판정 원칙: 소프트웨어 구조·실제 원본 의미·2턴 ChatGPT 결정·공식 금융근거·승인 권한·영구 발행·개인 자문 적격성은 서로 다른 상태다. PASS를 다른 단계로 승격하지 않는다.

## A. 개발 목표와 사용자 경계

**최종 목표:** 박곰희TV 791개 영상(롱폼 703·Shorts 88)과 관련 공식 금융·시장 원문을 대상으로, ChatGPT가 원본의 실제 의미를 판단하고 독립 V6 엔진이 출처·원자·검토·승인·저장 전 과정을 일관되게 검문하며, 신규 영상의 지식을 기존 검증 지식과 중복·보완·상충·시점 관계로 통합하여 답변·투자 판단·최종 개인 포트폴리오 자문에 재사용하는 시스템을 완성한다.

조건:
1. 단순 자막 요약, 후보 원자 증가, GitHub CI 성공, 예전 V3/V5 등록 편수는 최종 승인 지식이 아니다.
2. 사용자와 ChatGPT의 **실제 별도 메시지 2턴**을 요구한다. TURN1 원본 연구·비공개 동결 → 다음 사용자 명령 TURN2 ChatGPT source-first 독립적 의미 재판정·근거 검문. 동일 턴의 두 프로세스/함수, 수동 발급 임의 ID는 대체 불가. 암호학적 호스트 서명이 없으면 `host_two_turns_verified=false`로 표시한다.
3. 모델 API를 별도로 호출하지 않는다. 엔진의 결정론적 단계는 사용자 요청 후 가급적 연속 완료하지만 ChatGPT 모델의 TURN2 최종 검증은 실제 **두 번째 사용자 요청**까지 대기해야 한다. 따라서 사용자에게 반복적인 “진행해 주세요”를 요구하지 않되, 필수 두 사용자 메시지를 없앴다고 주장하지 않는다.
4. 최신 금융법령·공식 원문·시점·관할·상품 유형·조건을 영상 제작 시점과 답변 시점별로 구별한다. 적법성/최신성·적합성이 보장되지 않은 자료는 HOLD/QUARANTINE이며 금융 자문 GO로 승격하지 않는다.
5. Google Drive 개인 포트폴리오·종목/계좌 연결은 **연구 엔진과 검증 지식 자문이 합격한 이후**의 독립 단계다.

## B. 전수 검사 결과와 범위의 정확한 한계

### B1. 현재 HEAD 파일 인벤토리
GitHub 재귀 트리 결과 **2,364개 blob / 22,343,449바이트 / tree truncated=false**. 17개 최상위 그룹: `.github` 27, 루트 5, `data` 303, `docs` 12, `ire` 654, `knowledge` 31, `pending` 9, `research` 1, `sources` 5, `state` 46, `synthesis` 23, `validation` 1,007, `videos` 241. 전체 경로·Git blob SHA·바이트 크기는 [동결 전체 트리 인벤토리](IRE_FULL_CURRENT_TRACKED_TREE_MANIFEST_20261122.json)에 모두 기록했다.

이전 전체 추적 백업 `3fd99c8d47af1163c5a788bf9630658ccf2eda43`에서 **2,360/2,360개를 모두 읽고 SHA-256·바이트 길이를 대조**, 누락/손상/읽기 오류 0. 그 후 위 기준 HEAD까지 **변경/신규 10개 파일**을 GitHub에서 별도 재조회했다. 구성: Python 825개 AST 구문 PASS, JSON 759개 파싱 PASS, JSONL 6개 유효, Markdown 697개 UTF-8 판독, YAML 27개, HTML 2개, 텍스트 1개, 36개 암호화/바이너리 아카이브 바이트 확인, 6개 `.b64` 압축 JSON은 디코딩 가능한 구조임을 확인(민감 내용 공개 금지).

### B2. 모든 기존 분기
원래 98개 브랜치의 HEAD SHA를 **98/98 통합 커밋 조상**으로 로컬 Git bundle 재확인. 11개 최대 독립 분기의 현재 기준과 다른 **1,111개 고유 경로 / 1,117개 고유 텍스트 blob, 약 26.0MB를 읽고 유형·구문 확인**. 이 중 Python 경로 113개(현재 경로에 없는 것 96, 같은 경로의 다른 코드 17)가 **기능 채택 재심사 후보**다. 이력 포함과 실행 코드 승격은 구별한다. 정확한 전체 계보/변경 파일은 `BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json`와 `BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv`를 활용한다.

11개 독립 분기의 고유 변경 검토 원장:
| 분기 | 검토 방향 |
|---|---|
| `feat/ire-v4-execution-design-20261103` | V4 ChatGPT 검토 수용·기존 지식 조인 코드를 V6와 비교, 중복 기능은 승격 금지 |
| `feat/v34-001-005-sourceonly-research-replay-20261101` | 과거 원본 1~5편 재현·독립 평가·구 V3/V4/V5 검색·스크립트를 별도 역사/시험 후보로 분류 |
| `feat/v5-p0-cross-audit-ownership-20261107` | claim ownership 교차 검사/테스트 후보 비교 |
| `feat/v5-p0-p24-w25-w36-20261107` | 24구간 실물 검토와 대기열·범위 검사 보존 |
| `research/v5-p0-video24-w37-w44-quality-20261107` | 24번 영상의 남은 문맥 실증·OPEN 보존 |
| `v4/evidence-based-pilot-20261008` | 근거 기반 초기 연구 체계와 검증기, 역사 유지 또는 최신 근거 규격으로 전환 |
| `verify/ire-v6-e1-v202-source-to-frozen-parent-isolated-20261120` | E1 parent-source isolated 결함·반례 시험을 현행에 대조 |
| `verify/ire-v6-p0e-v155-host-integration-20261117` | `host_batch.py` / `proof.py`의 상이 버전, 원본→호스트 경계 재검토 |
| `verify/ire-v6-v170-live-chat-bridge-20261119` | 실제 ChatGPT 검토 연결과 신뢰 경계 비교 |
| `verify/ire-v6-v171-revisit-pdf-provenance-20261119` | PDF/금융 원문 출처·재검토 이력 실증·보안 재검토 |
| `verify/ire-v6-v180-source-gap-kind-semantic-20261119` | 미해결 위험 cue, 부정·인용·조건 처리 비교 |

각 후보의 정책: `ADOPT` (명시적 코드 diff·실제 개선 증명) / `TEST_ONLY` (회귀·반례로만 승계) / `ARCHIVE` (역사 보존) / `HOLD` (출처/개인정보/효과 불확정). **11개 분기를 통째로 실행 루트에 머지하는 작업은 금지**.

### B3. 실제 실행·시험 증거와 한계
- 본 재감사 오프라인 Python 3.13.5에서 기본 `ire/tests` **310 PASS**, `ire/v6/tests` **647 PASS**, 최신 V237~V242 대상 **58 PASS**, V123/V126/V127/V128/V166-E4/V172 검증 **215 PASS**. 총 **1,230개의 선별 단위·통합·합성 시험 PASS**. 이들은 서로 다른 시험 집합이며 비공개 원본 전체 의미 정확도는 측정하지 않는다.
- V5 앱 전체 테스트는 본 재감사에서 완주 성공을 입증하지 못했다. 전체 frozen CI·엄격 V5·V6·E1~E5를 **현재 통합 브랜치의 동일 SHA, Python 3.11.18**에서 한 번에 모두 성공시켰다는 증거는 없다.
- 11개 분기의 텍스트 blob을 읽고 구문 분류했으나 **모든 과거 커밋을 각각 사람처럼 의미 심사했다는 뜻은 아니다**. 36개 비공개 키 의존 바이너리 아카이브는 의미 복호화하지 못했다. GitHub에는 ETF 비공개 원본 ZIP·SQLite 정식 실물이 없으므로, 실제 ETF 전 구간 ChatGPT 의미 판정의 독립 재현은 비공개 보관본 접근을 필요로 한다.

## C. 현행 기능 판정 — 누락·과장 없는 기준

| 계층 | 실제 확인 | 판정 |
|---|---|---|
| 소스/원장/SQLite 커널 | V6 결정론적 source, SHA, HEAD, ACID, replay, idempotency 존재; 기본 시험 PASS | 기반 재사용, 운영 안정성 별도 |
| E1 구조 경로 | V203 합성 긍정 E1, V241 12개 실제 로컬 child + V242 B0013 미승인 잠정 구조 호스트 1개, 총 13 child·78 구조 이벤트 이력 | 제한적 구조 PASS / 실제 승인까지 완결 HOLD |
| E2 금융 의미 | ETF 원본 250 cue, 후보 68 원자, cross-parent 21 원자·49 외부 edge; B0013 cue 45~47 제한 보존 | source/structure PASS, 68원자 최종 의미·독립 정확도 HOLD |
| E3 ChatGPT 최종 검토 | 별도 실제 2턴 계약 및 미승인 검토 입력·V123 코드 구현 | **실제 ETF V123 최종 0/13** |
| E4 공식 근거/권한 | 원문 해시·유효시점·출처 타입·sealed store의 여러 구현/음성 시험 | 실제 ETF 공식 금융근거 및 owner 승인 HOLD |
| E5 발행 | V126/V127/V128 및 합성 원자적 부모 커밋·재실행 시험 존재 | 실제 ETF 승인 지식 0 |
| 지식·자문 | 레거시 116·P4 29, V5 P3/P4 교육 자문 및 V6 제한적 조회 구현 | 검증된 E5 지식 기반 투자·개인 자문 GO 아님 |
| 전체 자동화 | 엔진이 ChatGPT 현재 모델을 API 없이 자체 반복 호출할 수는 없음 | 장편·2턴 오케스트레이션 실사용 UX 미완성 |

현행 791 로스터(703+88), 레거시 `data/videos.jsonl` 157, `claims.jsonl` 116, 학습 큐 211, 미해결 큐 19, 영상 기록 `videos/` 241, `data/analysis_events` 및 `canonical_events`를 서로 다른 분모로 유지한다. 과거 등록·요약은 E5 승인 지식과 합산 금지.

## D. 확인된 근본 원인 / 관리 결함

**R01 계약 파편화:** 정식 실행 기능이 `ire/v6` 외에 `validation/ire-v6-frozen`의 다수 버전 별 브리지에 흩어짐. `V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json` 등 일부 상태 기록은 이전 브랜치·시점 기준이며 단일 최신 사실 원장이 아님.

**R02 자막-원자 문맥 단절:** 68원자 중 부모 외부 문맥 원자 21개, 조건/숫자/예외 간 49 edge; B0013 `C00057`에는 인덱스 ETF로 대상을 제한하는 원본 cue 45~47이 필요. V242는 미승인 구조 표현을 보존했지만 정식 의미 원자와 V123 승인 packet은 미작성.

**R03 정정/승인 상태전이 부재:** `v238`의 원래 `cross_atoms_waiting_for_semantics`를 `v240`이 조건 없이 HOLD하는 경로는 실제 TURN2 정정 결과를 최신 canonical revision으로 편입하지 못함. 원본 sidecar를 버리고 count를 0으로 맞추는 수선은 금지.

**R04 2턴 실행 경계:** 모델 의견 메모/수동 turn ID는 정식 E3 V123 검토 영수증·호스트 신원 검증이 아니다. 두 번째 실제 사용자 요청 및 source-first 리뷰가 필요하다.

**R05 E4/E5 우회·등급 혼동:** 구 V235 일반 V126 경로와 V240 E4 sealed 경로가 병존. 정식 외부 발행 API는 E4 권한 받은 경로 **하나**만 허용해야 한다. 공식 법령 문구 일치, 화자 발언 참/거짓, 금융 사실 적합성, 투자자문 GO는 별도.

**R06 원자 누락·거짓 완료:** GitHub open [#48](https://github.com/yhappcom/pensionport/issues/48) (모델만 만든 주장 census·NONFACT 자기라벨), [#50](https://github.com/yhappcom/pensionport/issues/50) (부정 인용·중복 영수증·진도 상태·구 V2 이벤트 replay). 현행 `ire/v6/official_completion.py`는 `research_complete=False` 등 보호를 추가했으나 **open issue를 자동 해결 처리하지 않는다**. 반례 재현/현행 회귀·마이그레이션 시험으로 각각 처분한다.

**R07 CI 실효성:** 27개의 기존 workflow 중 대다수 push 트리거가 삭제된 역사 브랜치에 묶임. 현재 통합 브랜치 push에 자동으로 도는 것은 주로 브랜치·파일 감사이며, 전체 E1~E5·V5/V6 품질 CI가 아님. V5 레거시 workflow에는 `contents: write` 권한도 남아 있어 least-privilege/작동범위 재검토 필요. GitHub Ruleset 0, `main` 보호 없음; 생성 사전 차단 미구현.

**R08 재현·보안:** 공개 저장소 `ire/v5/validation/private_source_derived_20261107/*.json.zlib.b64` 6개는 암호화가 아닌 압축 데이터. 공개 적합성·저작권·개인 식별·역사적 노출 재판정 필요. 36개 암호화·바이너리 아카이브는 복원키/원본 접근과 검증 가능한 재현 불확정. 사전 hash가 있어도 개인 SRT·영상 진위·법령 최신성 자동 보증 아님.

**R09 배포·운영 부재:** 표준 `pyproject.toml`/`setup.py`/배포 엔트리포인트 없이 여러 CLI·검증 스크립트에 의존. SQLite replay 성능, 장편·동시성·고장 복구·운영 지표와 개인 질문 적합성은 전체 검증 전.

## E. 목표 시스템의 단일 실행 계약

`TURN1(USER 연구 명령) → PRIVATE SOURCE (SRT/메타·SHA·cue) → SOURCE-FIRST 100% CUE DISPOSITION & PARENT ATOM GRAPH → QUALIFIER EDGE 보존 → 13 CHILD review packets → TURN1 append-only FREEZE → TURN2(별도 USER 명령) → ChatGPT 원문 우선 의미 재판정·정정 overlay → canonical V6 revision compiler → E2 품질/누락 검사 → E3 V123 원자·child·seam·parent 최종 판정 → E4 공식근거 원문·효력·권한 봉인 → E5 정확히 한 번 부모 단일 SQLite transaction → 기존 지식 관계 통합 → 최신 근거 조회 투자 답변`.

중요한 타입/상태 분리:
- `SOURCE_REGISTERED`, `SOURCE_FROZEN`, `MODEL_PROVISIONAL`, `PARENT_QUALIFIER_PENDING`, `CHAT_REVIEW_PROPOSED`, `E2_SEMANTIC_READY`, `E3_V123_REVIEWED`, `E3_HOLD`/`QUARANTINED`, `E4_AUTHORIZED`, `E5_ATOMIC_COMMITTED`, `ADVISORY_ELIGIBLE`.
- 모든 상태전이에 `parent/source/child/official/body_sha`, 검토 턴, 승인 주체·권한, as-of, 이전/새 HEAD, OPEN 목록, 사유와 idempotency key를 붙인다.
- 실제 원본·비공개 답변/포트폴리오는 접근통제된 private vault에만 두고 GitHub에는 영수증과 비민감 해시·상태만 둔다.
- 정정은 append-only. 이전 원자/원본 영수증을 덮어쓰지 않는다. 반드시 현재 revision을 대상으로 재평가하며 이전 HOLD를 묵시적으로 PASS로 치환하지 않는다.
- 13 child 중 미완료가 있으면 발행 0; 명시적 격리된 원자만 제외하고 13개 구간의 처분·검문이 완결된 경우에만 발행. 외부 조건 미반영 B0013 잠정 원자를 정식 승인으로 사용 금지.
- 처음부터 끝까지 **단일 public entrypoint**와 **단일 승인·저장 관문**을 사용한다. 실험용 CLI는 internal/test-only로 격리한다.

## F. 우선순위 및 명확한 완료 기준

### P0-0. 기준 정렬·원본 안전·통합 품질 CI (선행)
1. `docs`에 단 하나의 machine-readable 현재 상태 레지스트리를 생성한다. E1 구조/실물, E2 의미/정량, E3 TURN2/최종, E4 금융 근거/외부 승인, E5 발행, 자문, 791 로스터의 분모를 독립 필드로 고정.
2. 현재 통합 브랜치 push를 대상으로 **Python 3.11.18 고정**, V3/V5 core·V5 app·V6 frozen·E1~E5·보안·미리 등록한 긍정/부정 시험을 하나의 **필수 CI**로 연동. workflow 실패/타임아웃을 재현 가능하게 구별. 기존 루트/동결 V6 무의도 변경을 비교한다.
3. 27개 워크플로의 트리거·권한을 전수 분류(활성/역사/수동/폐기 권고), 쓰기 권한 축소 및 중복 관문 통일. `main`에 자동 PR/merge 금지; 신규 브랜치 없음. 관리자 Ruleset 사전 차단은 별도 인증 권한 작업으로 기록.
4. 공개 압축 JSON 6개 및 Git 히스토리의 source-derived 공개 적합성 검사, 암호화 archive 36개 private 복구 가능성/위치/키 소유자 검사. 개인 SRT를 공개 CI/Git에 업로드하지 않는다.
5. 기존 42개 닫힌 PR의 HOLD 이관·#48/#50 OPEN·11개 분기 코드 후보를 동일 작업 큐에 등록하고 소유자/채택·격리 기준을 고정.

**완료:** 최신 HEAD와 같은 SHA의 full CI 성공 영수증, 단계별 상태 1종, private 원본/OPEN 소실 0, 이전 연구 PASS 과장 0, 권한·브랜치 정책 위반 0. 보안 결함은 해결 완료 또는 명시적 보안 HOLD로 처리.

### P0-1. E1 운영 경로 단일화 및 실제 소스 계약
1. V6 `source.py`/`atomic_exchange.py`/`host_batch.py`/`store.py`를 재사용하고 V237~V242의 parent/child/source 운반을 단일 상태 기계의 타입으로 통합.
2. 21개 cross-parent 원자/49 edge를 지우지 않는 `source_anchor + parent qualifier` 계약, 외부 조건·예외·숫자·화자 조건을 검토 입력에서 완전 재구성하는 typed overlay compiler 구현.
3. B0013 `C00057`의 인덱스 ETF 제한을 parent→child→ChatGPT 입력→수정 revision→V6 native→E3까지 보존한다. 승인 전 미승인 staged 타입과 정식 V6 canonical atom은 코드 타입으로 분리.
4. 긍정 synthetic: 실제 커널·host→V123/E4/E5 관문까지 **법적 승인 조건을 충족한 합성 입력**의 기계적 통과. 부정: 진짜 2턴 없음·source 변조·qualifier 유실·빈 위험 child·실패 재개 등 차단. 금융 사실의 실제 참 인증과 구별.

**완료:** 사용자 동결 E1 정의 “입력·검토·승인·저장 경로가 하나로 연결”을 동일 입력·일련의 승인 API·실제 SQLite 영수증으로 합성 양성/음성 검증. ETF 실물은 13개 구조·누락 0, 미승인 발행 0, 의미 HOLD 유지.

### P0-2. E2 원자 정확도·빠짐없는 재판정
1. ETF 250 cue 전수 처분, 원자 후보 68개를 기준 후보로 사용하되 정답으로 가정하지 않는다. 21 cross 원자를 원문 기준 `KEEP/REATOMIZE/QUARANTINE/OPEN`으로 전수 판정하고 49 qualifier edge를 보존. B0013 독립적 현행 의미 판정.
2. 질문·인용·다른 화자 주장·반박·가설·광고·금융 사실·추천 분류, 하나 cue의 다중 주장, 여러 cue의 하나 주장, 숫자·세율·기간·예외·시점·적용대상을 모두 평가. `NO_ATOM`은 무주장이라는 적극적 원문 근거가 있을 때만 허용.
3. #48/#50 재현 시험: 숨은 두 번째 세금 주장, FACT를 QUESTION으로 모델 자가표기, 인용된 문장 뒤 “틀렸다”는 반박, 교차 자막 제한, 모순된 현행 법령, 중복 재전송, 과도·부족 분할.
4. 원본 우선 블라인드 검토 및 정답셋 사전 봉인. ChatGPT 자체 여러 차례 검토는 **내부 교차검토**일 뿐 외부 인간 독립 gold 인증이 아니다. TP/FP/FN, cue/atom precision/recall, 고위험 누락, 화자·조건·예외·숫자 정확도를 서로 다르게 계측.

**완료:** 250/250 cue 처분, 모든 확정된 원자/조건/예외/근거 역추적, 미해결 OPEN이 있다면 해당 범위 E2 HOLD. 외부 독립 정답 충족 시 precision ≥95%, recall ≥98%, high-risk FN=0; 그렇지 않으면 측정 범위를 명시하고 `INTERNAL_ONLY/UNMEASURABLE`를 보존.

### P0-3. E3 진짜 TURN2→정식 V123 결정·전달
1. TURN1 입력 원본 SHA·cue 수·원자·13개 child·이전 지식 HEAD·사전 OPEN을 0600 private vault에 불변 동결.
2. 다음 별도 사용자 TURN2에서 ChatGPT가 원본·공식근거를 **원문 우선**으로 재검토하고 각 원자/child/seam/parent의 승인·수정·격리·보류를 명시. 출처 불명/감독 권한 불명은 HOLD.
3. ChatGPT의 실제 결과를 `V123 atom_verdicts/source_cues/official evidence` typed case로 컴파일, 각 수정 revision과 기존 판정을 연결. `review_or_load_child` → `review_seams` → `review_parent` 검문. **TURN2를 Python이 만들어내지 않는다**.
4. E3가 승인한 자료만 E4 입력 가능; V123 유효 packet과 별도 금융근거/법률 판정까지 한 번에 합격한 것처럼 표시하지 않는다.

**완료:** 13/13 정식 V123 child case의 성공·HOLD 근거가 모두 영수증으로 재조회 가능. fake host signature, 수동 ID 위조, 다른 source SHA, stale turn, 누락 판정, 미승인 원자 통과 0.

### P0-4. E4 공식 금융근거/승인권한 하나로 통제
1. E3의 최종 승인 결과와 official HTTPS/PDF/HTML 실제 바이트 SHA-256, 기관·법령명·조문·시행일·조회일·관할·상품·수치·조건·적용 시점을 typed evidence로 연결.
2. 과거 영상 주장에 **현재 시행중인 규정**을 재조회하여 시점 변경을 별도 표시. 공식 자료와 화자 발언·인용·반박의 entailment를 혼동하지 않는다.
3. 구 V235/V126 직접 발행 경로는 외부 정식 출판 API에서 숨기고 V240 sealed/typed E4 결과 + 명시적 소유자 승인을 통해서만 E5로 간다. V173의 `e5_authorized=false`를 임의 변경하지 않는다.
4. 정상 합성 E4 긍정, 원문 변조·유효기간·대상·허위 승인자·인용만 맞는 부정 사례를 전부 별도 테스트한다. 실제 ETF 공식근거 실증은 그 뒤에만 판정.

**완료:** 적합한 실물/합성 근거는 정책대로 통과, 부적합·누락·시점 불일치는 결제·저장 이전 차단, owner seal 실제 확인 여부 표시, `FINANCIAL_FACT_VERIFIED`/`E4_RESEARCH_CERTIFIED`/`ADVISORY_ELIGIBLE` 독립 표시.

### P0-5. E5 승인된 13개 구간의 원자적 지식 저장
1. 13 child 전부 완료 판정·합법적인 격리·공식근거 승인 확인 후 한 부모 `SQLite transaction`으로만 저장. 12/13, OPEN 또는 E4 seal 누락 시 지식·이벤트·출판 delta=0.
2. 첫 승인 저장 시 parent publication=1, 정확한 승인 원자/이벤트 delta, 재실행/중복/중단/재개/동시 실행에서 정확히 한 번. WAL/HEAD/해시 체인, stale expected_head, 스키마 역사 V2 DB read-only replay/마이그레이션 모두 시험.
3. 기존 legacy116, P4 29는 조회 후보일 뿐 승인 신규 원자로 자동 합병하지 않는다. 수정/취소/겹침/충돌/시간 범위를 append-only 지식 관계와 이전 HEAD로 연결.

**완료:** 합성 전체 긍정 1건 + 모든 주요 부정·복구가 같은 frozen 커널에서 일관됨. 실제 ETF의 TURN2·E4 통과 전 E5 실물 발행 0 유지; 통과 후에만 재실행·DB 재개봉·원본 역추적으로 실제 한 편 지식 저장 승인.

### P0-6. 실물 ETF 한 편 최종 폐쇄 증명 (P0 완료 관문)
앞의 단계들을 **하나의 원본 영상/하나의 누적 지식 기준 HEAD**로 실행한다. 250cue/68 후보/13 child에서 원문·ChatGPT TURN2·공식 근거·원자 정정·승인·관계 통합·E5 실물 DB·추적 가능한 사용자 질의 답변을 한 장의 provenance graph와 closeout receipt로 재조회.

**완료:** E1~E5 각 단계의 입력/판정/오류/영수증·시간·OPEN 분모가 동일 커밋에 연결되고, 단계별 PASS/HOLD/FAIL이 부풀려지지 않음. 하나라도 미충족하면 개별 연구 CLOSE_WITH_HOLD이지 엔진 GO가 아니다.

### P1-1. 추가 미노출 5편 실증·다편 중복/충돌 검증
ETF와 다른 법령·시장·개인 투자 사례의 실제 새 SRT 5편을 사전 고정하여 같은 2턴 절차로 완주. 신규지식/동치/보완/상충/현행법 변경, 원문 무결성, 자료 출처, 1편별 E5 원자적 격리/발행, 재현성 비교. 실패는 새 브랜치를 만들지 않고 결함 ID·회귀 시험·정정 영수증으로 귀속.

**완료:** 추가 5편의 출처/검토/OPEN/승인·재실행 100% 추적, 고위험 누락·과잉 승인 0(평가 가능한 범위에서), 다른 영상의 기존 지식을 침묵 삭제하거나 중복 발행하지 않음.

### P1-2. 안정성·성능·대량 확장 판단
250cue → 1,000~1,500 cue 장편 → 5편 → 10편으로 단계별 시험. ChatGPT 분석/검토 시간, 공식근거 재조회 시간, Python/SQLite/해시 검문, 토큰·도구 호출·실패·재실행·보관 비용을 구분 측정. 장시간 실행 중 메모리·재연결·중복 작업·동시 writer·사이클/분기 폭증 시험.

**완료:** 실측 지표와 실패 복구 증거가 있을 때만 703 롱폼+88 Shorts 일괄 처리 운영 계획과 필요한 실행 예산을 확정. 임의 처리속도/완료일 예측 금지.

### P1-3. 검증 지식 검색·투자자문 평가
검증된 E5 승인 원자만 기본 신뢰로 사용하고, 현재 공식 1차자료를 답변 시점에 추가 조회. ISA·IRP·연금저축·ETF·세금·은퇴·리밸런싱 질문 1차 프리레지스터 평가셋으로 정확도·근거 링크·반례·조건·불확실·개인 적합성 검문. 금융교육/일반 정보와 개인화 권고 권한을 구별.

**완료:** 답변 문장 → 원자 ID → 원본 cue → 공식 근거 바이트 → 적용 조건·시점 역추적 가능, 보류/격리 지식 근거로 확정 조언하지 않음, 모델 환각 및 고위험 적용 누락 기준 충족.

### P2. 791편 확장 및 운영·유지보수
연구 ID·원본 비공개 위치·1턴 동결·2턴 검증·E1~E5·OPEN·E5 지식 HEAD·연구 종료 영수증을 **영상별 관리**하고 브랜치별로 관리하지 않는다. 검증된 연구만 증가, 중단·중복·갱신된 법령·사후 정정의 전 과정 재생. 매 주기 상태·OPEN 수·완료 편수의 진실값을 데이터 원장으로 산출.

**완료:** 연구 배치 전체가 개별 영상 closeout 수와 정확히 일치, fail-closed, 791 로스터 완료율과 실제 E5 승인율을 각각 보고.

### P3. 개인 포트폴리오/Google Drive 연계 (최종 단계)
검증 지식 자문이 합격한 후에만 개인 Drive 포트폴리오를 최소권한·동의 하에 읽고 계좌/종목/비중/현금흐름/세금·위험 및 적합성을 분석. 민감 자산정보의 공개 Git 저장 금지, 의사결정 지원과 거래 실행 분리. 가격·법령 최신성 검증·개인 조건 확인, 설명가능한 자문과 사후 검토 체계 수립.

**완료:** 데이터 접근통제·최신성·정확한 총액/비중·중복 계좌·세금 조건·위험 적합성, 근거 추적, 보안·재현성 검문을 통과하기 전 거래 유도/자동 집행 GO 금지.

## G. 단계별 정식 테스트 매트릭스

| 대상 | 반드시 포함할 긍정시험 | 반드시 포함할 부정/적대시험 |
|---|---|---|
| SOURCE | 전체 cue·SHA·신구 원본 스냅샷 재조회 | cue 누락·SRT 오염·인용 범위 위조·출처 분실 |
| E1 | 입력→검토→E4 조건부 승인→E5 합성 원자 저장 | 외부 조건 제거·위험 `NO_ATOM`·잘못된 scope·중단 복구 |
| E2 | 발화 역할·조건·숫자·충돌의 source-first 판정 | 자가 NONFACT 라벨·반어·부정 인용·법령 시점 바뀜·과도 원자 분할 |
| E3 | 13 child + seam + parent V123 실제 ChatGPT 검토 | 사용자 TURN2 미실시·수동 host 서명 위조·stale review·누락 |
| E4 | 현재 적법 공식원문·관할·효력일·owner 승인을 가진 입력 | URL/법령 원문 SHA 변조·폐지 조항·적용 범위 상실·무권한 출판 |
| E5 | 한 부모 커밋·재실행 exactly once | 12/13·부분 실패·동시성·이전 DB 스키마·E4 우회 |
| KB | SAME/SUPPORTS/EXTENDS/CONFLICTS/SUPERSEDED/DISTINCT/OPEN | 레거시 자동 승격·상충 삭제·시점 오염·인용 계보 단절 |
| ADVISORY | 승인 원자+최신 공식근거로 근거 설명 | 부적합 개인 권고·미승인 지식 사용·현행법 갱신 실패 |
| SECURITY/OPS | 비공개 vault pin·폐기 복구·single CI·2 branches | 공개 SRT/비밀 노출·권한 과다·새 브랜치·영수증 소실 |

## H. 출고/확장 승인 규칙

- `CODE_GREEN`: 지정 SHA의 CI 소프트웨어·정적/보안 시험 PASS.
- `E1_STRUCTURE_PASS`: 합법/불법 입력이 하나의 실제 실행 경로로 PASS/HOLD 분기됨.
- `E2_RESEARCH_REVIEWED`: 실제 원문 전수 처분·의미·조건·예외 증빙 재조회 가능. 독립 gold가 없으면 `INDEPENDENT_ACCURACY_UNCERTIFIED` 병기.
- `E3_FINAL_PASS`: 사용자 실제 TURN2 ChatGPT 판정의 V123 결과와 parent/child 범위 일치.
- `E4_FACT_GATE_PASS`: 공식 원문·법령 효력·owner 권한 실제 통과. 개인 자문 적격성과 구분.
- `E5_PUBLISHED`: 모든 child 처분·실물 단일 트랜잭션·재실행/재개봉 통과.
- `VIDEO_RESEARCH_CLOSED`: 이전 다섯 상태와 OPEN/격리 처리에 모순 없는 연구 종료 영수증.
- `ADVISORY_GO`: 지식 정확도·현재 법령·개인 적합성 평가 별도 충족. 포트폴리오 연계는 이 이후.
- 단계마다 `PASS/HOLD/FAIL/NOT_RUN/UNMEASURABLE`와 **실물/합성·source commit·owner 및 실제 사용자 턴·CI run ID**를 필수로 표시. 버전 번호나 PASS 1개로 모든 단계를 승격하지 않는다.

## I. 실행/관리 순서와 변경 통제

1. **다음 개발 작업 시작:** P0-0의 현재 STATUS·통합 CI·보안·OPEN 큐 정렬 → P0-1 단일 실행/원자 정정 계약 → P0-2 E2 실물 의미 → P0-3 실제 TURN2 E3 → P0-4 E4 → P0-5 E5 → P0-6 ETF 종단간 실증. 이후 P1-1/2/3 → P2 → P3.
2. 기존 R01~R09 결함마다 **원인·재현 입력(비공개인 경우 SHA만 공개)·최소 수정 계약·실패 전에 RED 시험·수정·그린 CI·실물 재생·영수증** 순서. 새 버전 wrapper만 만들어 “개선 완료” 금지.
3. 코드 수정 전에 이 문서 또는 결함 계약을 갱신한다. 한 번의 고정 기준 브랜치에서 변경, 필요한 과거 코드만 diff-review 후 반영, 기존 frozen/`main`/개인 원본 변조 금지.
4. 연구 종료 시 `RESEARCH_RUN_CLOSEOUT_RECEIPT_TEMPLATE_20261122.md` 필수 항목 채우기; APPROVED_AND_INTEGRATED / CLOSED_WITH_EXPLICIT_HOLD_TRANSFER / QUARANTINED / CANCELLED_WITH_ARCHIVE. 자료/OPEN 이관을 기록하기 전에는 임시 브랜치 폐기/완료 표시 불가.
5. 42개 닫힌 PR의 원래 지식·성능을 승인으로 오인하지 말고 중앙 HOLD 상태에서 재검토. GitHub Ruleset 관리자 설정 전까지 상시 선제 차단을 주장하지 않는다.
6. 현 master plan은 원본·legacy·승인 지식의 **진실값을 변경하지 않는 개발 계획**이다. 작업 후 상태 변경은 실제 테스트·원본·2턴·E4/E5 영수증과 정확히 같은 Git HEAD를 지정해 별도 machine-readable STATUS에서만 수행한다.

## J. 착수·완료에 필요한 핵심 원천 근거

- [전 저장소 동결 트리](IRE_FULL_CURRENT_TRACKED_TREE_MANIFEST_20261122.json)
- [기존 심층 감사 보고서](AUDIT_IRE_FULL_REPOSITORY_AND_DEVELOPMENT_ROADMAP_20261122.md)
- [98개 원래 브랜치 HEAD](BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json), [분기 변경 blob 목록](BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv)
- [브랜치 종료 정책](BRANCH_LIFECYCLE_AND_RESEARCH_CLOSEOUT_POLICY_20261122.md), [42개 PR HOLD 이관](BRANCH_LEGACY_PR_RESEARCH_TRANSFER_20261122.json)
- [현행 연구 종료 양식](RESEARCH_RUN_CLOSEOUT_RECEIPT_TEMPLATE_20261122.md)
- `validation/ire-v6-frozen/V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md`
- `validation/ire-v6-frozen/V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md`, `V203_E1_REAL_V176_ORIGIN_TO_NATIVE_V128_STRUCTURAL_PASS_20261120.md`
- `validation/ire-v6-frozen/V242_E1_REAL_ETF250_B0013_CONDITION_LINKED_NATIVE_HOST_PASS_E3_E5_HOLD_20261122.md`
- GitHub issues [#48](https://github.com/yhappcom/pensionport/issues/48), [#50](https://github.com/yhappcom/pensionport/issues/50)

**최종 GO 기준:** 엔진은 한 편을 실제 별도 사용자 2턴·정식 V123·공식 금융근거·E4·E5·기존 지식 통합까지 출처와 함께 재현 완료해야 한다. 그 증거가 없으면 구현·CI가 아무리 발전해도 791편 확대나 개인 포트폴리오 자문 출시 GO를 주지 않는다.
