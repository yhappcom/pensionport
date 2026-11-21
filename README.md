> **현재 통합 개발 마스터 계획 (2026-11-22):** [저장소 전수 재감사·E1~E5/자문 단일 개발 계획](docs/IRE_CANONICAL_FULL_DEVELOPMENT_MASTER_PLAN_20261122.md), [2,364개 추적 파일 동결 목록](docs/IRE_FULL_CURRENT_TRACKED_TREE_MANIFEST_20261122.json). E1 합성 구조 성공과 ETF 실물 13구간 미승인 구조 기록은 **실제 E3/E4/E5 승인 및 지식 발행 성공이 아닙니다**. 신규 브랜치 생성 없이 통합 브랜치에서 진행하고 `main`은 변경하지 않습니다. 기존 역사 개발 설명과 최신 계획/검증 상태를 구분합니다.

> **브랜치 통제 사후점검:** 98개 중 96개 브랜치의 삭제 영수증과 42개 PR HOLD 이관을 검증했습니다. [원본 아티팩트 해시·영구 영수증](docs/BRANCH_RETIREMENT_DURABLE_ATTESTATION_20261122.json) / [보강된 검증 보고서](docs/BRANCH_CONSOLIDATION_CLOSEOUT_20261122.md). 현재 2개 브랜치 유지 검사는 통합 브랜치 push에서 동작하며, GitHub Ruleset은 아직 미설정입니다. **새 브랜치 생성의 사전 차단이나 상시 감시가 구현됐다고 주장하지 않습니다.** 연구 시작·종료 시 브랜치·OPEN·연구 영수증을 확인하고, Ruleset 설정은 관리자 승인 후 별도 수행합니다.

> **현행 연구·개발 브랜치 운영 기준 (2026-11-22):** [브랜치·연구 종료 정책](docs/BRANCH_LIFECYCLE_AND_RESEARCH_CLOSEOUT_POLICY_20261122.md)과 [98개 브랜치 이력 통합 장부](docs/BRANCH_CONSOLIDATION_20261122.md)를 우선 적용합니다. `main`은 변경하지 않습니다. 신규 영상/검증 작업마다 브랜치를 만들지 않으며, 통합 실행 기준은 `audit/full-repository-snapshot-20261122` (일시적인 통합 브랜치)로 단일화합니다. 과거 E1 합성 PASS는 **실제 E1~E5 최종 승인 PASS가 아님**. E1 실물 종단간 HOLD. **별도 두 사용자 턴의 ChatGPT 의미 검토** 필수. 연구 브랜치 종료 전 원본/검토/OPEN/지식계보 영수증 정리 필수.

# pensionport

An evidence-based investment research project that builds a knowledge base from educational video content and authoritative primary sources.

## Core Resources

- [Verified Video Inventory](VIDEO_INVENTORY_2026-10-07.md): 791 videos in the roster, including 703 long-form videos in the primary research scope.
- [V3 Single-Record Research Workflow](WORKFLOW.md): prioritize source-based analysis and write one final analysis record per newly reviewed video.
- [Research Completion and Investment Decision-Use Standard](docs/RESEARCH_DECISION_USE_STANDARD_20261029.md): one canonical rule set for study closure, reusing existing knowledge, and evaluating decision readiness.
- `data/videos.jsonl` and `data/canonical_events/`: preserved legacy registry records (read-only during routine research).
- `data/analysis_events/<video_id>.json`: the final V3 research record for each newly reviewed video, including sources, claims, risks, and independent verification.
- `knowledge/` and `synthesis/`: consolidated investment knowledge organized by topic.

## E1→E5 순차 검증 — E1 구조 연결 최종 마감 PASS (2026-11-20)

사용자 동결 원칙: **E1→E2→E3→E4→E5**, 이전 단계 미합격 시 다음 단계 금지. E1 완료 문구 **"입력·검토·승인·저장 경로가 하나로 연결"**를 변경하지 않는다.

2026-11-20의 [V202 E1 독립 재검문 FAIL](validation/ire-v6-frozen/V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md)과 옛 V202 PASS 철회 기록은 그대로 보존한다. 새 **V203**은 V176 원본 검토 원장에서 각 V6 native 자식의 **실제 `submit_host_atomic_batch`**를 먼저 생성하고, 별도 채팅 승인 입력·V123·V127·V128을 거쳐 V126 SQLite에 **동일 합성 입력**의 연구 후보 2건과 부모 발행 1건을 원자적으로 저장했다. 두 번째 동일 실행은 중복 저장 0이고, 공식 근거 누락·원본 해시/조건 앵커 변경·구간 경계 의미 누락은 차단. [GitHub Actions 413/413 PASS](https://github.com/yhappcom/pensionport/actions/runs/44716365269). **이 합격은 합성 E1 구조 연결만 증명**한다.

- [E1 최종 구조적 마감·엄격 8관문·클린룸·재현 증빙](validation/ire-v6-frozen/E1_FINAL_STRUCTURAL_CLOSEOUT_AND_STRICT_GATE_20261120.md)
- [V203 E1 최종 합격 증빙](validation/ire-v6-frozen/V203_E1_REAL_V176_ORIGIN_TO_NATIVE_V128_STRUCTURAL_PASS_20261120.md)
- [E1~E5 최신 단일 순서 판정](validation/ire-v6-frozen/V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json)
- [V166 불변 사용자 순차 검증 계약](validation/ire-v6-frozen/V166_E1_E7_SEQUENTIAL_ENGINE_VERIFICATION_PLAN.md)

**현행 단계:** E1 PASS (합성 구조; V6 strict 8/8, E1 435/435, cleanroom 1,224/1,224), E2 READY/NOT_RUN, E3·E4·E5 NOT_RUN. 실제 원본 13구간 지식 승인, 금융 법률 의미 정확성, 실전 E3 ChatGPT 2턴은 여기에 포함되지 않으며 E2 PASS 전 E3 진행 금지.

## V6 E3 현행 필수 규칙 — 실제 사용자 메시지 두 번

최신 V6 E3는 **별개의 사용자 메시지 2턴** — **사용자의 연구 명령 1턴 → 별도 사용자 메시지로 시작하는 ChatGPT 최종 의미 검증 1턴** — 을 필수로 합니다. 같은 턴에서 두 배치/두 프로세스/두 번째 의미 분석을 수행해도 두 개의 사용자 턴이 아닙니다. 연구 결과를 턴 1에서 동결하고 턴 2에서 원본·근거·동결 결과를 검증해야 합니다. 확인 전에는 **E3 HOLD / E4 NOT RUN / E5=0**입니다.

[현행 V193 실제 사용자 2턴 운영 계약](validation/ire-v6-frozen/V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md)을 우선 적용합니다. 과거 V3 한 턴 연구와 V183~V192의 2차 분석 기록은 역사적 개발 자료입니다.

## Operations

Each research cycle follows **select an unfinished long-form video → obtain the correct source text → analyze and verify its content → save one JSON record → read it back and validate it**.

- A new analysis is counted as complete only after its saved file passes validation. Do **not** create or require a separate new `data/canonical_events/` entry.
- Completion counts use the union of unique video IDs in the legacy registry and valid new analysis records, intersected with the long-form roster. Count each video only once.
- A `PARTIAL` record without sufficient source content does not count as a newly completed review. Distinguish transcript-based research from review of audiovisual material.
- Never bypass GitHub safety checks. If a write is blocked, stop further writes for that run and report only verified saved results.
- Do not repeatedly recollect the inventory, refresh writer locks, or rebuild aggregates on every run. `state/progress.json` is a historical reference snapshot.
- For time-sensitive matters such as pensions, ISA accounts, and taxation, distinguish historical statements from current rules verified against official sources.

Preserve historical canonical events. An earlier analysis-only record for `09R29vsv6to` may count as a V3 completion if it satisfies the V3 data requirements. Do not recreate the previously blocked canonical event #232.



**브랜치 정리 완료 (2026-11-22):** 역사적 브랜치 98개를 단일 Git 이력으로 보존한 후 안전하게 96개를 종료하여 `main` + `audit/full-repository-snapshot-20261122` **2개만 유지**한다. 이전 열린 PR 42개는 `main` 병합 없이 연구 HOLD를 중앙으로 이관하고 종료했다. [최종 정리 보고서](docs/BRANCH_CONSOLIDATION_CLOSEOUT_20261122.md) · [연구 종료 영수증 양식](docs/RESEARCH_RUN_CLOSEOUT_RECEIPT_TEMPLATE_20261122.md). 기존 실제 E1/E2/E3/E4/E5 최종 연구 승인은 계속 HOLD다.
