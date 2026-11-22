# P0-0-05 — 독립 11분기·42 PR HOLD·Issue #48/#50 전수 이관 종료 보고 (2026-11-22)

**체크리스트 판정: PASS (등록·후속 인계 범위만).** 연구 엔진의 실제 E1~E5 최종 금융 승인과 개인 자문은 HOLD. `main` 수정·새 브랜치·과거 코드 무검토 채택은 없음.

**정확한 GitHub CI:** [Actions 44985673668](https://github.com/yhappcom/pensionport/actions/runs/44985673668), 검증 HEAD `7711fb3216bc5c91ea3c302fabc39a48eef86fdf`, Python 3.11.18, **6/6 작업 성공**, P0-0-05 새 24개 승인 위조·누락·원본 SHA 변조 차단 시험 PASS. 기존 strict V3/V5/V6, E1~E5 frozen regression, checklist/status/workflow 관리 검증도 같은 커밋에서 성공.

## 1. 동일 근거를 3개 계층으로 분리

- **98개 역사 HEAD·96개 폐기된 브랜치 계보 보존**은 P0-0-01 검증으로 이미 확인. 현재 `main` + `audit/full-repository-snapshot-20261122` 두 브랜치 유지. Octopus history merge는 코드 자동 채택이 아니다.
- **11개 최대 독립 분기**가 이번 P0-0-05의 코드/원본/연구 보완 후보. 기존 [5,939행 분기 전체 변경목록](BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv)에서 해당 11개 분기의 **1,103개 (branch,path) 원본 blob SHA**를 빠짐없이 [개별 판정 원장](IRE_P0_0_05_ALL_DIVERGENT_PATH_DECISIONS_20261122.json)에 이관. 동일 경로가 다른 분기에서 재출현할 수 있으므로 1,103은 *각 분기별 경로 행수*이다.
- **과거 열려 있던 PR 42개**는 정확한 HEAD SHA 42/42가 GitHub 현행 closed·unmerged HEAD와 일치. 전체 GitHub PR 74개가 closed 상태지만 나머지 32개는 원래 열려 있던 PR 이관 코호트가 아니므로 분리. Issue [#48](https://github.com/yhappcom/pensionport/issues/48), [#50](https://github.com/yhappcom/pensionport/issues/50)은 OPEN, 그 원래 해결 의무를 축소하거나 닫지 않는다.

## 2. 경로별 보수적 의사결정

| 분류 | 행수 | 실행/후속 정책 |
|---|---:|---|
| **ADOPT** | **0** | 현재 활성 코드와 동치·신규 red/green·호환성 검증 없이 채택 금지 |
| **TEST_ONLY** | **95** | 독립 회귀·계약 시험의 *재실행 후보* (현행 테스트 PASS 수로 계산 금지) |
| **ARCHIVE** | **95** | 과거 문서·기존 실행 워크플로 등 Git 이력 보존만 |
| **HOLD** | **913** | 실행 코드·미검증 연구자료·비공개 자막/압축 데이터 후보. 원본·보안·모델 재판정 전 금지 |
| **전체** | **1,103** | **원본 11개 분기 HEAD·경로별 blob SHA 고정** |

**각 분기·결함 ID:** 아래 파일 수는 11개 최대 독립 분기에 해당하며 전체 98개 브랜치의 파일수와 다르다.

| 결함 ID | 삭제한 역사적 분기 | 경로 | TEST_ONLY | ARCHIVE | HOLD | 코드 승계 |
|---|---|---:|---:|---:|---:|---|
| `P005-B01` | `feat/ire-v4-execution-design-20261103` | 28 | 6 | 19 | 3 | HOLD |
| `P005-B02` | `feat/v34-001-005-sourceonly-research-replay-20261101` | 1019 | 73 | 60 | 886 | HOLD |
| `P005-B03` | `feat/v5-p0-cross-audit-ownership-20261107` | 5 | 2 | 1 | 2 | HOLD |
| `P005-B04` | `feat/v5-p0-p24-w25-w36-20261107` | 4 | 1 | 1 | 2 | HOLD |
| `P005-B05` | `research/v5-p0-video24-w37-w44-quality-20261107` | 1 | 0 | 1 | 0 | HOLD |
| `P005-B06` | `v4/evidence-based-pilot-20261008` | 12 | 3 | 4 | 5 | HOLD |
| `P005-B07` | `verify/ire-v6-e1-v202-source-to-frozen-parent-isolated-20261120` | 5 | 2 | 2 | 1 | HOLD |
| `P005-B08` | `verify/ire-v6-p0e-v155-host-integration-20261117` | 6 | 1 | 2 | 3 | HOLD |
| `P005-B09` | `verify/ire-v6-v170-live-chat-bridge-20261119` | 5 | 2 | 1 | 2 | HOLD |
| `P005-B10` | `verify/ire-v6-v171-revisit-pdf-provenance-20261119` | 6 | 2 | 1 | 3 | HOLD |
| `P005-B11` | `verify/ire-v6-v180-source-gap-kind-semantic-20261119` | 12 | 3 | 3 | 6 | HOLD |

연구자료로 의미 있는 구간 #24 W25~W44, V3.4 #1~#5 등은 **과거 기록으로 존재**하지만 이곳의 분류만으로 원본 100% 복구·원자 완결·현행 금융법규 재검증 또는 E5 승인 지식이 되지 않는다.

## 3. 42개 PR의 원문 기반 후속 업무

42개 전부에 `P005-PR-001` 등 원래 PR 번호를 보존하는 고유 결함 ID, 제목/원래 head·base/HEAD SHA, closed·미병합 실물 확인, 후속 workstream, 연구 E3/E4/E5 FALSE, 마지막 출처 URL을 연결했다. 세부 42행은 [통합 인계 원장](IRE_P0_0_05_LEGACY_TRANSFER_REGISTER_20261122.json)의 `pull_requests`가 기계 판독 기준이다.

대상 PR #49/#51/#52/#53을 포함해 과거 기능에서 확인된 좁은 안전 방어는 **현행 코드와 대조**하되, PR을 main에 자동 병합하거나 기존 사용자 비공개 자료·SQLite를 공개하지 않는다. PR 42개 연구 상태는 일괄 **HOLD**로 명시했고 개별 증거·이슈 해결 전 `ADOPT` 금지.

## 4. Issue #48·#50: 코드 수정·실물 미해결 분리

| Issue | 현재 좁은 소프트웨어 방어 | 해소되지 않은 핵심 의무 |
|---|---|---|
| **#48** 모델 생성 원자만으로 연구 완료 선언 | 현행 `ire/v6/official_completion.py`는 독립 source-first 원자 완결성을 **false**, `research_complete=false`로 고정하고 V6 음성시험도 보유 | 전체 원본 누락 고위험 FACT/질문으로 오분류/조건·예외·여러 자막 연결에 대한 실제 별도 검토 및 독립 평가 |
| **#50** 부정인용·중복 검문·진척 상태·V2 재생 | 원문과 정확히 일치하는 좁은 규정 문장을 요구; 동일 모델 revision에 대한 rule receipt를 검사; 소프트웨어 progress receipt는 E3/E4/E5 GO가 아니다 | 더 복잡한 인용·화자·반박 의미, **과거 SQLite v4 V2 이벤트의 실제 무손실 재생/이관**, 공식 근거 시행일 갱신, MATH 분리, 전체 원본 gold |

세부 리스크 **9건**을 `P005-I048-A..C`, `P005-I050-A..F`로, 공통 미해결 사항 **6건**을 `P005-G01..G06`으로 등록했다. `SOFTWARE_MITIGATED_RESEARCH_HOLD`는 **Issue 전체 해결이 아닌 좁은 코드 방어**만 뜻한다. 두 Issue를 닫거나 금융 사실을 승인한 적 없다.

## 5. 검증·실행 관문 및 다음 단계

- [기계 검문 코드](../scripts/ire_legacy_transfer_gate.py)와 [24개 양·음성 시험](../scripts/test_ire_legacy_transfer_gate.py)을 현재 단일 `full-all-branch-history-audit-20261122.yml`에 포함. 기존 59건 관리 검증에 추가된 현재 관리 시험은 총 **86건**이며, 엄격 V3/V5/V6 및 frozen E1~E5와 동일 SHA에서 실행됐다.
- 검문이 막는 사례: 경로 1개 누락, 11개 분기 원래 SHA 변경, 42개 PR 한 건 누락·HEAD 교체, 역사 연구를 E3/E4/E5 승인으로 표시, Issue #48·#50을 임의 종료/삭제, TEST_ONLY를 ADOPT로 조기 승격, OPEN 6건 누락.
- **완료 수준:** 11개 코드 후보를 현재 실행 경로에 자동 편입하지 않은 상태에서 *고정·분류·이관·통제* 완료. 각 HOLD 원본의 보안 재검증은 아직 미수행이며 다음 단계를 통과해야 향후 실제 코드 채택을 검토할 수 있다.
- **다음 유일한 허용 항목:** `P0-0-06` 공개 `.b64` 압축 자료 6개 및 비공개/보안 아카이브 36개에 대한 공개 적합성·복구 가능성·보안 HOLD 심사. 원문 비공개 자막의 유출을 금지하고, 체크리스트상 실패 발생 시 P0-0-06을 PASS하기 전에는 P0-0-07로 진행하지 않는다.

**승인 경계 유지:** ETF 원본 250cue/후보 68/13구간 구조 기록과 실제 `V123 E3 0/13` / `E5 발행 0` 분리. 사용자 실제 별도 2턴, E4 금융 승인, 개인 포트폴리오 연결 모두 HOLD.
