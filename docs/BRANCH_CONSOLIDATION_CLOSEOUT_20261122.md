# IRE 브랜치 98→2 통합·연구 보존 최종 정리 보고서 (2026-11-22)

## 1. 최종 사실 판정

| 구분 | 통합 전 | 통합 후 |
|---|---:|---:|
| Git 브랜치 | 98 | **2** |
| 기존 열림 PR | 42 | **0** |
| 안전 삭제한 불필요 브랜치 | 0 | **96** |
| 삭제 실패·SHA 변동으로 보류 | — | **0** |
| 원래 98개 HEAD가 통합 Git 이력에 포함 | 일부 상속 | **98/98** |
| 변경된 `main` | — | **0** |
| 미승인 E3/E4/E5 연구 결과의 승인 승격 | — | **0** |

- **영구 보존:** 모든 원래 HEAD 및 원래 커밋·Git blob은 단일 Git 이력 병합 `3d1beba08ea3037df3c6c46f21cff9a5bb0374db`의 조상으로 포함됐다.
- **보호된 브랜치:** `main` (`d613fd201f4bb077f1ccc74d28dee937b11bfcb2`)과 `audit/full-repository-snapshot-20261122` (한시적으로 단일 통합 개발 브랜치).
- **이력 통합과 활성 코드 통합은 다름:** 11개의 별도 분기 이력을 추가 부모로 기록하되 그 통합 커밋의 작업 트리는 첫 부모와 동일했다. 따라서 과거 V3/V4/V5/V6의 충돌 가능 코드를 루트 실행 경로에 무검토로 섞지 않았다. 옛 분기에만 존재하는 파일은 `git show <old_sha>:<path>`로 복원 가능하며 자동 활성화한 것으로 보지 않는다.

## 2. 보존 영수증

1. [98개 HEAD 정확한 SHA 등록부](BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json): 브랜치명/이전 HEAD SHA/조상 분류/고유 변경 규모.
2. [5,939개 분기별 파일 변경 후보와 Git blob SHA 목록](BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv): 중복된 파일 경로를 포함하며, 서로 다른 기능·근거의 정식 중복 제거 또는 승인 처리는 별도.
3. [구조 통합 전수 보고서](BRANCH_CONSOLIDATION_20261122.md): 77 조상 + 18 분기 + E1 현재 1 + `main` 1 + 감사 1의 98개 계보, 최대 독립 분기 끝점 11.
4. [PR 42개 연구 HOLD 이관 원장](BRANCH_LEGACY_PR_RESEARCH_TRANSFER_20261122.json): 기존 연구 완료·금융 적법 승인으로 오인하지 않고 원문 검문·미해결 상태를 후속 연구 대상으로 보존.
5. [브랜치 수명주기·연구 종료 정책](BRANCH_LIFECYCLE_AND_RESEARCH_CLOSEOUT_POLICY_20261122.md), [연구 종료 영수증 양식](RESEARCH_RUN_CLOSEOUT_RECEIPT_TEMPLATE_20261122.md).
6. [96개 안전 삭제 GitHub Actions 영수증](https://github.com/yhappcom/pensionport/actions/runs/44961824077): `original_count=98`, `deleted=96`, `skipped=0`, `failed=0`, 삭제 전 모든 역사적 PR 종료 확인. 개인 Git bundle을 별도로 백업했으며 GitHub 원본 전체 이력도 새 통합 커밋에서 접근 가능.

## 3. 반영한 영구 운영 통제

- **단일 브랜치 개발:** 사용자 별도 승인 없이 영상별/턴별/버전별 브랜치 신규 생성 금지; `main` + 단일 통합 브랜치 **2개 유지**.
- **읽기 전용 CI:** [브랜치 통제 GitHub Actions](https://github.com/yhappcom/pensionport/actions/runs/44962128892)가 매 통합 브랜치 push마다 브랜치명·개수 2개, `main` SHA, 98개 역사 HEAD 접근성, 다중 부모 이력 합병, 5,939 변경파일 목록의 보존, 연구 정책 문서 존재 여부를 확인한다.
- **일회성 삭제 권한 제거:** 정리 성공 후 삭제용 `contents: write` 워크플로를 저장소에서 제거했다. 일상 CI에는 `contents: read`만 허용한다.
- **연구 폐쇄 시 자료 정리:** 연구 원본·비공개 경로·SHA, 실제 별도 사용자 메시지 1/2턴, 원자·조건·예외·숫자 검증, ChatGPT 결정, OPEN·격리, 공식 근거, 지식 관계, V123/E4/E5 승인과 통합 head, CI/원본 재실행을 종료 영수증에 기록한다. 미완료는 새 통합 브랜치의 중앙 연구 큐로 이관하고 금융 사실 PASS로 표시하지 않는다.
- **기존 `main` 불변 및 역사적 연구 보존:** 당장 운영 코드 채택/개인 원본 공개/미승인 E5 발행 없음.

## 4. 아직 해야 할 일 — 브랜치 수가 아니라 연구 품질

- 이번에 통합한 11개 고유 분기의 실제 코드 중 현재 코드와 다른 부분은 위 경로·blob SHA 목록을 참고해 **의미 있는 수선만 선택적으로 채택**해야 한다. 삭제한 브랜치에서 연구자료의 원본 및 미승인 검문을 무조건 PASS로 간주할 수 없다.
- 투자 연구 엔진의 **E1 전체 종단간·E2 의미정확도·E3 2턴 정식 ChatGPT 검토·E4 공식 근거 봉인·E5 승인된 지식 원자적 저장**은 V242 당시 실제 ETF의 승인 결과로 아직 입증되지 않았으며 HOLD.
- `main` 승격이나 기능 개발은 **이 통합·연구 종료 정책을 준수하는 후속 별도 단계**에서 결정한다.
- 코드 호스트의 생성 권한을 사전 차단하는 GitHub 규칙집(admin-level branch ruleset)은 이 작업에서 변경하지 않았다. 현 정책은 **CI 위반 탐지 + 브랜치 생성 금지 문서 + 단일 통합 브랜치 유지**의 조합이며, 계정 차원의 브랜치 생성 자체를 사전 거부하는 권한 설정은 별도 관리자 조치가 필요하다.

## 5. 독립 재확인

- 정리 직후 실제 GitHub 브랜치 목록: `main` 및 `audit/full-repository-snapshot-20261122`만 존재.
- 기존 PR 42건은 모두 상태 `closed`; 본문에는 원래 SHA·연구 HOLD 이관·`main` 미병합 안내를 기록.
- 삭제용 workflow가 제거돼 이후 무단 삭제가 자동 재발하지 않음.
- 기계 검사: Git branch ancestry 98/98, 최초 octopus tree(first parent) 일치, 시점 고정 `main` HEAD 유지; 최신 읽기 전용 정책 CI.


## 6. 후속 감사: 삭제 영수증 원본 재조회·지속 관리 보강 (2026-11-22)

- GitHub Actions `44961824077`의 실제 아티팩트 `14730251026`(`ire-branch-retirement-evidence-20261122.zip`)를 다운로드해 ZIP 내 `branch-retirement-result.json`을 확인했다. `original_count=98`, `original_heads_reachable=98`, `deleted=96`, `skipped=0`, `failed=0`, `all_open_prs_closed_before_deletion=true`; `main` SHA는 `d613fd201f4bb077f1ccc74d28dee937b11bfcb2`.
- GitHub에 표시된 아티팩트 ZIP SHA-256과 다운로드 실물 해시가 `5828cea7a4bfd71ec6f10fc8b0839607fae92c115435c612eddc0f318c6ea98b`로 일치했다. 원본 아티팩트 만료 예정일은 2026-12-21 UTC이므로 [영구 요약·검증값](BRANCH_RETIREMENT_DURABLE_ATTESTATION_20261122.json)을 Git에 고정했다. **Git의 요약값은 원본 ZIP 자체를 대체하지 않으며, 그 이후에도 Git 조상/브랜치/PR 실물 검사가 필요하다.**
- 별도 브랜치를 만들지 않고 현행 `.github/workflows/full-all-branch-history-audit-20261122.yml`을 강화하여 42개 기존 PR 이관 자료의 동치/OPEN·E3/E4/E5 미승인 보존, 96개 삭제 영수증, 98개 HEAD/변경 목록과 `main` 불변을 같은 감사에서 검문하도록 했다.
- 2026-11-22 기준 Ruleset은 **0개**이며 현재 workflow는 통합 브랜치 push/수동 실행만 감지한다. **새 브랜치의 생성 자체를 사전 차단하거나 독립적인 실시간 감시를 제공하지 않는다.** GitHub 관리자 Ruleset 설정 또는 별도 외부 정기 점검이 필요하다. [운영 정책 E절](BRANCH_LIFECYCLE_AND_RESEARCH_CLOSEOUT_POLICY_20261122.md)에 관리자 설정 절차와 예외·정리 규칙을 기록했다.
- 42개 기존 PR의 종료 영수증은 **기술적 이력 정리**이며 원자 검증·금융 사실 승인·E1~E5 합격이 아니다. 자료가 없는 개별 연구의 승인 확정 금지; 먼저 OPEN을 중앙 연구 큐에서 소스 기준으로 재판정한다.
