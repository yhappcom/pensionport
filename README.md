# pensionport

An evidence-based investment research project that builds a knowledge base from educational video content and authoritative primary sources.

## Core Resources

- [Verified Video Inventory](VIDEO_INVENTORY_2026-10-07.md): 791 videos in the roster, including 703 long-form videos in the primary research scope.
- [V3 Single-Record Research Workflow](WORKFLOW.md): prioritize source-based analysis and write one final analysis record per newly reviewed video.
- [Research Completion and Investment Decision-Use Standard](docs/RESEARCH_DECISION_USE_STANDARD_20261029.md): one canonical rule set for study closure, reusing existing knowledge, and evaluating decision readiness.
- `data/videos.jsonl` and `data/canonical_events/`: preserved legacy registry records (read-only during routine research).
- `data/analysis_events/<video_id>.json`: the final V3 research record for each newly reviewed video, including sources, claims, risks, and independent verification.
- `knowledge/` and `synthesis/`: consolidated investment knowledge organized by topic.

## E1→E5 순차 검증 — 2026-11-20 E1 재검문 실패 (현행 V176 경로)

사용자 동결 원칙: **E1→E2→E3→E4→E5 순차 진행. 이전 단계가 합격하지 못하면 다음 단계에 진입하지 않는다.** E1 완료 기준은 **입력·검토·승인·저장 경로가 하나로 연결**이다.

**최신 판정: 현행 V176→V202 E1 `FAIL`, E2 `BLOCKED_BY_E1`, E3~E5 `NOT_RUN`.** 기존 V166의 역사적 합성 구조 연결 E1 PASS는 보존하지만 V202로 옮겨온 승인·저장 입력에서 **화자·발언 입장·조건·시점이 원래 V176 원장과 달라도 합성 저장이 가능했던 오류**가 독립 재검문에서 입증됐다. [반례가 CI 실패를 유발함](https://github.com/yhappcom/pensionport/actions/runs/44705219505); 방어 패치 후 [398/398 회귀 PASS](https://github.com/yhappcom/pensionport/actions/runs/44706008466)는 **불합격 입력의 안전한 차단 증명**일 뿐 E1 정상 종단간 PASS가 아니다. E1 실제 동일 검토 레코드가 정식 V6 host→V123→V126로 전달되는 합성 양성 경로를 재구축하기 전 E2 금지.

- [현행 E1 독립 재검문 FAIL 및 후속 E1 수리 조건](validation/ire-v6-frozen/V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md)
- [동결된 E1~E5 최신 단계 판정 원장](validation/ire-v6-frozen/V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json)
- [V166 원래 순차 검증 운영 계약](validation/ire-v6-frozen/V166_E1_E7_SEQUENTIAL_ENGINE_VERIFICATION_PLAN.md)

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
