# pensionport

An evidence-based investment research project that builds a knowledge base from educational video content and authoritative primary sources.

## Core Resources

- [Verified Video Inventory](VIDEO_INVENTORY_2026-10-07.md): 791 videos in the roster, including 703 long-form videos in the primary research scope.
- [V3 Single-Record Research Workflow](WORKFLOW.md): prioritize source-based analysis and write one final analysis record per newly reviewed video.
- [Research Completion and Investment Decision-Use Standard](docs/RESEARCH_DECISION_USE_STANDARD_20261029.md): one canonical rule set for study closure, reusing existing knowledge, and evaluating decision readiness.
- `data/videos.jsonl` and `data/canonical_events/`: preserved legacy registry records (read-only during routine research).
- `data/analysis_events/<video_id>.json`: the final V3 research record for each newly reviewed video, including sources, claims, risks, and independent verification.
- `knowledge/` and `synthesis/`: consolidated investment knowledge organized by topic.

## V6 E3 현행 필수 규칙 — 실제 사용자 메시지 두 번

최신 V6 E3는 **사용자의 연구 명령 1턴 → 별도 사용자 메시지로 시작하는 ChatGPT 최종 의미 검증 1턴**을 필수로 합니다. 같은 턴에서 두 배치/두 프로세스/두 번째 의미 분석을 수행해도 두 개의 사용자 턴이 아닙니다. 연구 결과를 턴 1에서 동결하고 턴 2에서 원본·근거·동결 결과를 검증해야 합니다. 확인 전에는 **E3 HOLD / E4 NOT RUN / E5=0**입니다.

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
