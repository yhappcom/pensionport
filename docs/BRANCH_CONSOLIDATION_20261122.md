# IRE 전 브랜치 계보 전수 조사·이력 통합 계획 (2026-11-22)

**동결 기준:** GitHub PUBLIC `yhappcom/pensionport`, 2026-11-22, 브랜치 HEAD 98개. `main`은 수정하지 않는다.

## 1. 전수 검사 결과

| 상태 | 브랜치 수 | 의미 |
|---|---:|---|
| 현재 E1 최신 검증 HEAD와 **이미 동일 또는 조상** | 78 (현재 E1 1 + 조상 77) | 추가 이력 머지 필요 없음 |
| HEAD가 현재 E1과 **분기** | 18 | 독립 HEAD SHA/고유 커밋·파일 충돌 존재 |
| `main` | 1 | E1의 조상. **수정·병합 대상 아님** |
| 별도 감사 브랜치 | 1 | E1에서 분기된 본 정리 실행·보고서 보관 브랜치 |
| **전체** | **98** | 모든 브랜치 SHA 보존 |

분기 18개 중 서로 조상인 브랜치를 제거하면 **최대 독립 분기 HEAD 11개**이다. 기존 E1 브랜치를 병합 기반으로 삼는 대신, **현재 감사 브랜치에 이 11개를 추가 부모로 기록하는 Git *이력 병합*을 수행**하면 전체 98개 HEAD가 통합 HEAD의 조상이 된다. 이는 실제 코드의 미검토 파일 변경을 루트에 활성화하지 않으면서, 어떤 브랜치를 폐기해도 `git show <HEAD>:<PATH>`로 원본을 복구할 수 있게 한다.

## 2. 11개 분기 HEAD와 정리 원칙

| 독립 분기 HEAD | HEAD SHA-256/Git SHA-1 | 고유 변경 처리 원칙 |
|---|---|---|
| `feat/ire-v4-execution-design-20261103` | `8d8a76ecd5c0072036bba2276ee7e54089c6263c` | 독립 커밋 48건, 기존 E1에 없는 새 파일 후보 28개, 기존 경로와 다름 0개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `feat/v34-001-005-sourceonly-research-replay-20261101` | `6632efafad16a9f352a652131387469f130a01a2` | 독립 커밋 1601건, 기존 E1에 없는 새 파일 후보 1014개, 기존 경로와 다름 5개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `feat/v5-p0-cross-audit-ownership-20261107` | `735fa1336738b3c4c6c833ef90e8dbb096d057e2` | 독립 커밋 7건, 기존 E1에 없는 새 파일 후보 2개, 기존 경로와 다름 3개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `feat/v5-p0-p24-w25-w36-20261107` | `148d00abc2c4bdc12ff372f3dc616c98f881995a` | 독립 커밋 4건, 기존 E1에 없는 새 파일 후보 4개, 기존 경로와 다름 0개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `research/v5-p0-video24-w37-w44-quality-20261107` | `a08d7256eff6ce0e93763471af6887fbda6f0448` | 독립 커밋 1건, 기존 E1에 없는 새 파일 후보 1개, 기존 경로와 다름 0개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `v4/evidence-based-pilot-20261008` | `08fa35761fd53520ed9d3b4d2b088d23b4c8201f` | 독립 커밋 8건, 기존 E1에 없는 새 파일 후보 11개, 기존 경로와 다름 1개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `verify/ire-v6-e1-v202-source-to-frozen-parent-isolated-20261120` | `2829a109c458e346789dce4b39bc75547f3d0b2a` | 독립 커밋 5건, 기존 E1에 없는 새 파일 후보 2개, 기존 경로와 다름 3개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `verify/ire-v6-p0e-v155-host-integration-20261117` | `6e05c4cf9b2ed0a9e1f79beca09c252008649712` | 독립 커밋 7건, 기존 E1에 없는 새 파일 후보 5개, 기존 경로와 다름 1개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `verify/ire-v6-v170-live-chat-bridge-20261119` | `5aa8eaf017f7d5e62fd3467cf4be45a35f40c949` | 독립 커밋 9건, 기존 E1에 없는 새 파일 후보 3개, 기존 경로와 다름 2개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `verify/ire-v6-v171-revisit-pdf-provenance-20261119` | `a62ba0b29cb9ce7293620051844e59033e0d0100` | 독립 커밋 7건, 기존 E1에 없는 새 파일 후보 6개, 기존 경로와 다름 0개; 전체 이력 보존 후 별도 기능 채택 심사 |
| `verify/ire-v6-v180-source-gap-kind-semantic-20261119` | `6c4ba8350eeffdb99b8ad106aa3c3f0f78acfca0` | 독립 커밋 15건, 기존 E1에 없는 새 파일 후보 6개, 기존 경로와 다름 6개; 전체 이력 보존 후 별도 기능 채택 심사 |

## 3. 이력과 실제 파일 통합의 분리

**이력 통합(PASS 가능):** 98개 브랜치 HEAD가 1개 통합 HEAD 조상인지 확인, 원래 SHA와 Git blob 접근성 유지, 기존 코드 루트/`main` 변경 0.
**코드/연구 기능 채택(미완료):** 다른 분기에서만 존재하는 5,939개(브랜치별 중복 포함)의 변경 파일 후보와 동일 경로 상이 버전 53개(브랜치별 중복 포함)를 의미·충돌 분석 후 선택. 단순 `git merge -s ours`를 기능 통합 성공으로 표현 금지. 파일·근거 단위로 승계 시 원래 SHA + 재검증 + 원본 보호 필요.
**연구자료:** 개인 원본·암호화 자료는 브랜치/커밋 개수로 승인되지 않는다. 각 브랜치의 연구/검토/보류 파일과 출처 SHA를 종료 영수증에 연결하고, 필요한 private 원본은 비공개에서 유지.

## 4. 병합/폐기 전 엄격 검사

1. 본 조사 때의 브랜치별 98개 SHA를 `docs/BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json`에 기록한다. **HEAD가 바뀐 브랜치는 자동 폐기 대상에서 제외**한다.
2. `main` SHA가 `d613fd201f4bb077f1ccc74d28dee937b11bfcb2`인지 재확인. 달라졌으면 즉시 중단.
3. 감사 브랜치 현재 HEAD를 먼저 확인하고, 기존 HEAD를 첫 부모로 두고 11개 최대 분기 SHA를 추가 부모로 만드는 **12-parent non-production Git 이력 합병**만 수행한다.
4. 합병 후 `git merge-base --is-ancestor BRANCH_HEAD CONSOLIDATED_HEAD`가 **98/98 참인지** 재검증. 참이 아니면 기존 브랜치를 삭제/닫지 않는다.
5. 모든 연구용 브랜치는 소스 SHA, 의미 검토 상태, OPEN, 공식 근거 및 지식 저장 결과에 대한 종료 영수증을 확인. 과거 미완료 자료를 승인 상태로 승격시키지 않는다.
6. PR 전체 74개 중 열린 42개(대부분 Draft)는 병합된 HEAD 및 자료 이력에 대응되도록 분류한 후 `SUPERSEDED_WITH_HISTORY_ARCHIVED` / `CLOSED_WITH_HOLD_TRANSFER`로 닫고, 브랜치는 HEAD 검사 후 단계적으로 폐기한다.
7. 최종 2개 이하 브랜치(`main`·통합), 이력 보존 98/98, 현재 코드 불변, 미승인 지식 발행 증가 0, 신규 브랜치 자동 생성 금지를 목표로 한다.

## 5. 브랜치별 98개 전수 목록

| 브랜치 | HEAD SHA | 분류 | 통합 전 독립 커밋 |
|---|---|---|---:|
| `audit/full-repository-snapshot-20261122` | `e91f457817bf9d74` | AUDIT | 3 |
| `feat/ire-chat-assisted-noapi-20261101` | `dcdcca9337b75e43` | ANCESTOR | 0 |
| `feat/ire-cleanroom-engine-20261101` | `1a3d4a729229feab` | ANCESTOR | 0 |
| `feat/ire-incremental-advisory-20261101` | `4f20f2aa230b8c1c` | ANCESTOR | 0 |
| `feat/ire-live-evidence-verification-20261101` | `98bcfb236c4e074e` | ANCESTOR | 0 |
| `feat/ire-v2-advisory-system-redesign-20261101` | `6ac3d65333c77588` | ANCESTOR | 0 |
| `feat/ire-v3-chat-orchestration-20261102` | `be4cc19a692a670e` | ANCESTOR | 0 |
| `feat/ire-v4-execution-design-20261103` | `8d8a76ecd5c00720` | DIVERGED | 48 |
| `feat/ire-v5-vertical-slice-20261103` | `f753ba57a1afabaa` | ANCESTOR | 0 |
| `feat/subtitles-incremental-registry-20261009` | `5c5266e78425acbc` | DIVERGED | 1240 |
| `feat/v30-integrated-research-engine-20261031` | `692c61334f1b410e` | DIVERGED | 1568 |
| `feat/v33-holdout-overlap-preflight-20261031` | `dd458b2eec39391b` | DIVERGED | 1579 |
| `feat/v34-001-005-sourceonly-research-replay-20261101` | `6632efafad16a9f3` | DIVERGED | 1601 |
| `feat/v34-integrated-atomic-semantic-retrieval-20261101` | `4e31b0b9f2d07ce3` | DIVERGED | 1599 |
| `feat/v5-all5129-risk-cue-22-claims-audit-20261106` | `ca252229d3405fdb` | ANCESTOR | 0 |
| `feat/v5-extra369-65low-signal-semantic-review-20261107` | `3f421095dcb9862b` | ANCESTOR | 0 |
| `feat/v5-extra369-linked97-partial-cue-audit-20261107` | `cf4f207d665e398f` | ANCESTOR | 0 |
| `feat/v5-extra369-unanchored-13-review-20261107` | `25f185931dea39ce` | ANCESTOR | 0 |
| `feat/v5-first-five-atomic-residual-audit-20261106` | `58011f369935a201` | ANCESTOR | 0 |
| `feat/v5-gap13-master116-crosswalk-20261107` | `aff3f7867017f9b8` | ANCESTOR | 0 |
| `feat/v5-internal-source-verification-policy-20261106` | `14daff5f4d048e38` | ANCESTOR | 0 |
| `feat/v5-p0-claim-ownership-reconcile-20261107` | `37d2fed9c2763ada` | ANCESTOR | 0 |
| `feat/v5-p0-cross-audit-ownership-20261107` | `735fa1336738b3c4` | DIVERGED | 7 |
| `feat/v5-p0-hard-closure-recall-gate-20261107` | `22479963d404a7b4` | ANCESTOR | 0 |
| `feat/v5-p0-hourly-first12-semantic-20261107` | `c8e9cbe98170ab16` | ANCESTOR | 0 |
| `feat/v5-p0-hourly22-final8-20261107` | `0d5aab46a8ad2286` | ANCESTOR | 0 |
| `feat/v5-p0-hourly22-w13-w24-20261107` | `49eea9caf798dd54` | ANCESTOR | 0 |
| `feat/v5-p0-hourly22-w25-w36-attribution-20261107` | `27000d9270cf2d56` | ANCESTOR | 0 |
| `feat/v5-p0-multicue-span-contract-20261107` | `13028d83abad3ef0` | ANCESTOR | 0 |
| `feat/v5-p0-p24-w25-w36-20261107` | `148d00abc2c4bdc1` | DIVERGED | 4 |
| `feat/v5-p0-private-cue-replay-gate-20261107` | `be99d8c43fdf72eb` | ANCESTOR | 0 |
| `feat/v5-p0-quality-path-gate-20261107` | `0cc28f5e3f282aa2` | ANCESTOR | 0 |
| `feat/v5-p0-real10-adaptive-audit-20261107` | `cf94b7934ebb7fc3` | ANCESTOR | 0 |
| `feat/v5-p0-real10-claims-evidence-20261107` | `887e3a7110845507` | ANCESTOR | 0 |
| `feat/v5-p0-replay-count-reconciliation-20261108` | `4bbf013d5bc37976` | ANCESTOR | 0 |
| `feat/v5-p0-run3-w37-w50-source-review-20261107` | `2bb182cb73d159d7` | ANCESTOR | 0 |
| `feat/v5-p0-semantic-context-completeness-20261107` | `ff496b41fccc8484` | ANCESTOR | 0 |
| `feat/v5-p0-video24-w01-w24-20261107` | `84ad25356f8c0053` | ANCESTOR | 0 |
| `feat/v5-p3-original-p4-live-20261106` | `ebbd43be0d49939b` | ANCESTOR | 0 |
| `feat/v5-personal-investment-advisor-20261030` | `f978f5e70b166d4d` | DIVERGED | 1433 |
| `feat/v5-receipt-scope-no-false-completion-20261107` | `72e0d7295397776f` | ANCESTOR | 0 |
| `feat/v5-six-stage-source-crossvalidation-20261106` | `2cea941c0dd89045` | ANCESTOR | 0 |
| `feat/v5-video10-full34-cue-atomic-scope-20261106` | `91570d5402069191` | ANCESTOR | 0 |
| `feat/v5-video6-8-9-source-scope-20261107` | `c4f326ce0a6b77b8` | ANCESTOR | 0 |
| `feat/v5-video7-compilation-dedup-20261107` | `f76c2e03991a9656` | ANCESTOR | 0 |
| `fix/v5-receipt-blind-review-required-20261107` | `dd00356a25b51fe4` | ANCESTOR | 0 |
| `fix/v5-receipt-nested-p0-claims-20261108` | `6d75db205e7d938f` | ANCESTOR | 0 |
| `fix/v5-receipt-quality-claims-20261107` | `38a38688de09cd13` | ANCESTOR | 0 |
| `main` | `d613fd201f4bb077` | MAIN | 0 |
| `research/v5-p0-video24-w37-w44-quality-20261107` | `a08d7256eff6ce0e` | DIVERGED | 1 |
| `v4/evidence-based-pilot-20261008` | `08fa35761fd53520` | DIVERGED | 8 |
| `verify/ire-v6-e1-v202-source-to-frozen-parent-isolated-20261120` | `2829a109c458e346` | DIVERGED | 5 |
| `verify/ire-v6-e1-v230-v228-source-native-handoff-20261121` | `b6aae4a75832d2c4` | IDENTICAL | 0 |
| `verify/ire-v6-e2-source-census-adversarial-20261120` | `c9d2a676d3e3002e` | ANCESTOR | 0 |
| `verify/ire-v6-frozen-ci-20261108` | `b5e32f238c0897b8` | ANCESTOR | 0 |
| `verify/ire-v6-p0-atomic-exchange-20261109` | `dd88dd57df223197` | ANCESTOR | 0 |
| `verify/ire-v6-p0-false-completion-20261109` | `81fdcb88a37ecb9c` | ANCESTOR | 0 |
| `verify/ire-v6-p0-integrity-hardening-20261109` | `c42dcce3c450f75d` | ANCESTOR | 0 |
| `verify/ire-v6-p0-sourcefrontier-20261109` | `ccac3a3ef9a7b91e` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v151-remediation-20261116` | `40308b956fcba766` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v152-source-seam-20261116` | `b9c6f85934c832b4` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v153-semantic-202-20261116` | `cf0df1edc12d5806` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v154-integration-20261117` | `212c558203d84024` | DIVERGED | 6 |
| `verify/ire-v6-p0e-v154-real-integration-20261116` | `4a9ecb3e7bd69f5a` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v155-75-cue-adjudication-20261117` | `9be53a9f443c42e4` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v155-host-integration-20261117` | `6e05c4cf9b2ed0a9` | DIVERGED | 7 |
| `verify/ire-v6-p0e-v157-actual-284-host-semantic-fields-20261117` | `4de4edb8a9017a2b` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v158-129-source-stances-20261117` | `a8c72beb95fa23b4` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v159-v123-source-first-20261117` | `0cd6473e1abd03fa` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v160-one-video-full-source-e2e-20261117` | `804b55a037fe5227` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v161-source-evidence-recovery-20261117` | `7f9b54869ff32ca6` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v162-one-video-repeat-proof-20261117` | `101cc59563912606` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v163-b0001-final-meaning-audit-20261117` | `f3b93c2059cef6da` | ANCESTOR | 0 |
| `verify/ire-v6-p0e-v164-b0001-typed-final-20261117` | `552d0a812201b9fd` | ANCESTOR | 0 |
| `verify/ire-v6-p1-atomic-host-batch-20261109` | `30c5b9e2b0753a59` | ANCESTOR | 0 |
| `verify/ire-v6-p1-legacy-readonly-20261109` | `76584d60718e3597` | ANCESTOR | 0 |
| `verify/ire-v6-p1-prior-relation-20261109` | `a988bdc5209ce7de` | ANCESTOR | 0 |
| `verify/ire-v6-v165-one-video-feasibility-20261117` | `8048816962887cfd` | ANCESTOR | 0 |
| `verify/ire-v6-v166-e1-e7-sequential-gates-20261117` | `4398e171daece83c` | ANCESTOR | 0 |
| `verify/ire-v6-v167-chat-research-loop-20261118` | `bcfa6619cda7623b` | ANCESTOR | 0 |
| `verify/ire-v6-v168-chat-native-replay-20261118` | `5f11ad07c5c99cca` | ANCESTOR | 0 |
| `verify/ire-v6-v169-chat-resumable-20261118` | `9a15d893888fe857` | ANCESTOR | 0 |
| `verify/ire-v6-v170-chat-boundary-revisit-20261119` | `48e891272816b3e2` | ANCESTOR | 0 |
| `verify/ire-v6-v170-live-chat-bridge-20261119` | `5aa8eaf017f7d5e6` | DIVERGED | 9 |
| `verify/ire-v6-v171-revisit-pdf-provenance-20261119` | `a62ba0b29cb9ce72` | DIVERGED | 7 |
| `verify/ire-v6-v171-source-semantic-split-20261119` | `907364e1e5d769fc` | ANCESTOR | 0 |
| `verify/ire-v6-v172-exhaustive-video-engine-20261119` | `65fc5a1cdfedbe84` | ANCESTOR | 0 |
| `verify/ire-v6-v173-e4-only-final-gate-20261119` | `b68d5683e6bb1ea9` | ANCESTOR | 0 |
| `verify/ire-v6-v174-fresh-source-native-e4-20261119` | `75ba49d780c0e6f2` | ANCESTOR | 0 |
| `verify/ire-v6-v175-fresh-native-host-batch-20261119` | `83a3a877419c5d8d` | ANCESTOR | 0 |
| `verify/ire-v6-v176-engine-driven-chat-e4-20261119` | `92859fb704ae02ac` | ANCESTOR | 0 |
| `verify/ire-v6-v177-private-two-turn-checkpoint-20261119` | `c28ba0772c6c4d1b` | ANCESTOR | 0 |
| `verify/ire-v6-v178-source-only-coldstart-20261119` | `1437cb79e6de82d5` | ANCESTOR | 0 |
| `verify/ire-v6-v179-owner-two-turn-native-replay-20261119` | `14ed2451f4febd5d` | DIVERGED | 9 |
| `verify/ire-v6-v179-real-two-turn-source-firstpass-20261119` | `cef91f97882b328f` | ANCESTOR | 0 |
| `verify/ire-v6-v180-source-gap-kind-semantic-20261119` | `6c4ba8350eeffdb9` | DIVERGED | 15 |
| `verify/ire-v6-v200-e1-e5-live-gate-20261120` | `07eb944eaa59a700` | ANCESTOR | 0 |
| `verify/ire-v6-v201-e1-native-source-bridge-20261120` | `0232419c224e55bd` | ANCESTOR | 0 |

## 6. 변경 없는 지식 합격 판정

- V242 실물 ETF: 13개 구조적 미승인 V6 호스트 기록 및 출처/해시 시험 통과, **E2/E3/E4/E5 실제 승인=0, E1 전체 HOLD**.
- 본 통합은 기존 기능을 `main`으로 반영하지 않는다. 이전 문서에 기록된 E1/E2 PASS는 합성/실물 구분과 해당 브랜치 SHA 기준으로만 해석한다.
- `[Git 전체 브랜치 bundle]` 보관본은 이력 감사/복구용이며 브랜치 종료 전에 통합 Git ancestry로 추가된 이후 참조 유지 여부를 재확인한다.