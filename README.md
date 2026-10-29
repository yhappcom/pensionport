# pensionport

An evidence-based investment research project that builds a knowledge base from educational video content and authoritative primary sources.

## Core Resources

- [Verified Video Inventory](VIDEO_INVENTORY_2026-10-07.md): 791 videos in the roster, including 703 long-form videos in the primary research scope.
- [V3 Single-Record Research Workflow](WORKFLOW.md): prioritize source-based analysis and write one final analysis record per newly reviewed video.
- [Research Completion and Investment Decision-Use Standard](docs/RESEARCH_DECISION_USE_STANDARD_20261029.md): one canonical rule set for study closure, reusing existing knowledge, and evaluating decision readiness.
- `data/videos.jsonl` and `data/canonical_events/`: preserved legacy registry records (read-only during routine research).
- `data/analysis_events/<video_id>.json`: the final V3 research record for each newly reviewed video, including sources, claims, risks, and independent verification.
- `knowledge/` and `synthesis/`: consolidated investment knowledge organized by topic.

## Operations

Each research cycle follows **select an unfinished long-form video → obtain the correct source text → analyze and verify its content → save one JSON record → read it back and validate it**.

- A new analysis is counted as complete only after its saved file passes validation. Do **not** create or require a separate new `data/canonical_events/` entry.
- Completion counts use the union of unique video IDs in the legacy registry and valid new analysis records, intersected with the long-form roster. Count each video only once.
- A `PARTIAL` record without sufficient source content does not count as a newly completed review. Distinguish transcript-based research from review of audiovisual material.
- Never bypass GitHub safety checks. If a write is blocked, stop further writes for that run and report only verified saved results.
- Do not repeatedly recollect the inventory, refresh writer locks, or rebuild aggregates on every run. `state/progress.json` is a historical reference snapshot.
- For time-sensitive matters such as pensions, ISA accounts, and taxation, distinguish historical statements from current rules verified against official sources.

Preserve historical canonical events. An earlier analysis-only record for `09R29vsv6to` may count as a V3 completion if it satisfies the V3 data requirements. Do not recreate the previously blocked canonical event #232.
