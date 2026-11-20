# V185 — E3 source-first semantic error analysis and parent/qualifier safeguards

**2026-11-20 KST. Status: E3 NOT CERTIFIED / V123-E4 NOT RUN / E5=0 / NO INDEPENDENT GOLD.**

## Input provenance and previous actual proof
- Original owner video `LVE7XN_esTc`: source-only SRT 250 cues, immutable SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- V184 owner-only ZIP SHA-256 `c8ae3c764909b4b3456b7af5116b87ac069aa2ec9b1eb904896088abc2272d95`. Verified all 24/24 archived private file sizes and hashes and all three source/e3/adjudication SQLite `PRAGMA integrity_check=ok`, then reopened V176/V183/V184 audit state in a fresh process.
- V176 master source journal pinned head `ccd789a0fc6259e600d434381f8b5064a1e6b137256968d7b061192896a9b138`; V183 second review head `94d2e504e0622950d944ba79d37207c615d2d30351dc4c0012e953e5dd469038`, 92/250 2nd-reviewed, 158 pending; original 69 preliminary atoms and 17 effective OPEN. No master atom corrections were applied just to improve metrics.

## Actual source-informed adjudication: 42 remaining V184 cue-level cases
- ChatGPT reviewed original private SRT, adjacent cues and original/second decisions; authored 42 individual Korean explanations and source-quoted verdicts using the V184 explicit `prepare → submit` append-only path, in **three 14-cue batches**. All validations passed and the previous 12 adjudications remained unchanged.
- **Prior 12 + newly adjudicated 42 = 54 internally adjudicated review triggers**, classified as:

| Root-cause class | All 54 | Newly reviewed 42 |
|---|---:|---:|
| Claim boundary / cross-cue attachment mismatch | 24 | 22 |
| First-pass potential omission | 4 | 3 |
| Second-pass potential omission | 4 | 3 |
| Reviewer-added condition/exception not attributable as spoken | 6 | 4 |
| Equivalent wording or QUESTION/NON_RESEARCH transition | 5 | 4 |
| Missing original audio/video needed | 6 | 4 |
| Financial fact/date/scope OPEN | 3 | 1 |
| Other semantic OPEN | 2 | 1 |
| **Total** | **54** | **42** |

- The category prefixes `CONFIRMED_` are **the ChatGPT in-chat adjudicator's internal source-text reading**, not a certified independent gold determination. No financial rule or missing audio/screen was automatically resolved. 11 among 54 adjudications still carry explicit evidence/scope/open follow-up.
- V185 private adjudication journal appended 3 immutable events and reached head `35a056a7f47f08bc605f6c8efe13c8f3c6c5de41e82f9c537e24977b547aa584`. The prior 12 events and master/second journal heads remain intact.

## Reproduced E3 engine design defect
1. **Wrong evaluation unit:** A source assertion often crosses consecutive subtitles. First pass anchored it to the sentence beginning and the second pass to its conclusion, yielding different `ASSERTION` vs `NON_RESEARCH` labels per cue even for a common higher-level parent claim. 24 of 54 disagreement triggers were adjudicated as claim-boundary cases; a cue-level mismatch is not necessarily an omitted atomic fact.
2. **Mixed voices:** The original 69 candidate atoms each have free-text `conditions`/`exceptions` (138 terms total), but the engine does not distinguish the speaker's original qualifications from ChatGPT reviewer-added suitability/financial caveats. On a conservative **verbatim substring** scan of the cited original cues, **0/138 terms** matched directly; this finding does **not** prove that every qualifier is reviewer-invented, because source meaning can be paraphrased. However the source-spoken provenance for **all 138 remains unverified**. The second-pass subset has 11 qualifier terms, also 0 direct verbatim matches.
3. **No gold denominator:** 92/250 second-reviewed is not the full atom census; accuracy targets precision >=95%, recall >=98%, high-risk misses 0 remain **not measurable**. A second ChatGPT reading is not an independent human gold standard.

## V185 software fix: fail-closed source-alignment and provenance audit
- `v185_e3_parent_qualifier_audit.py`: read-only independent analysis of actual three pinned journal heads and original owner cues. Detects **possible** cross-cue parent overlap using context indices, limited cue shift, compatible claim kinds and exact numeric token equality. Never asserts semantic equivalence or auto-merges claims; multiple candidates remain ambiguous for explicit adjudication. O(cues × local span) source-scoped processing, rather than global all-to-all claim matching.
- Real native result among 92 previously reviewed cues: 35 literal `CLAIM_PRESENT` disagreements, **28 cue cases / 36 candidate cross-cue parent alignments** (8 cues have multiple possible alignments). These are **possible** links only, not 28 confirmed equivalences or a 28-error reduction.
- Qualifier diagnostics separately report source-verbatim matched terms vs source-unanchored or paraphrased terms; reviewer-authored notes are **not** converted into speaker utterance or native V6 source anchors. All outputs are JSON-safe hashes/cue indices/counts without private original wording, with `e3_quality_certified=false`, `v123_approved=false`, `e4_approved=false`, `e5_published=false`.
- `v185_e3_parent_qualifier_cli.py`: reproducible on the owner-private original/three SQLite journals, strict SHA and master head checks, output is new 0600 private file; never overwrites or changes original master or E3 journals.
- `test_v185_e3_parent_qualifier_audit.py`: synthetic adversarial cases for displaced parent links, numeric mismatch refusal, non-source qualifier false attribution, incompatible claim kinds, owner census omission, missing hash pins and **no automatic approval**.

## Result and restricted future plan
- This version **improves E3 error localization and avoids classifying cross-cue shifts as proven omissions**, but does NOT implement lossless V6 source-qualifier projection or prove automated semantic accuracy.
- Next: 158 remaining source-only second reviews, externally verifiable original audio/screen for specific OPENs, *typed source-spoken versus reviewer-added* qualifier annotation with exact cue indices and source quote, canonical semantic parent links validated by ChatGPT, then preregister and measure a true accuracy test set before E3 acceptance.
- E4/V123 final approval and E5 publishing are not attempted. `main` and private original assets untouched; GitHub PR remains draft. All private source, verdict payloads and SQLite stay outside public GitHub/Actions.