# IRE V5 — 4~5 videos per user turn: performance contract and real source benchmark

**Baseline date:** 2026-11-04. **Implementation:** `ire/v5/batch.py`, `ire/v5/planner.py`, `ire/v5/batch_backup.py`, `ire/v5_app/batch_worker.py`.

## User acceptance contract

- One **user request** for 4 or 5 videos, independent exact-original SHA, complete cue census, frozen full-video plan, real ChatGPT-authored financial meanings, claim-level official primary-source investigation, relation decisions against a pinned prior knowledge revision, all-window research report, and recoverable encrypted evidence receipts.
- A source register, worklist, packet preparation, or automated lexical inference is **not** research completion. Any unprocessed source window blocks the requested 4/5-video goal. Explicit factual OPEN with recorded search history is distinct from UNPROCESSED; no unwarranted legal/fact/advisory approval is allowed.
- A *model turn* means one request from the user with internal host-controlled tools. GitHub Actions is a short-lived deterministic runner and has no ChatGPT model execution privileges or access to private source. **No external LLM API** is used. Neither GitHub nor Python alone guarantees that a user turn can produce 5 full research reports under host context/time limits.
- Throughput release criterion: **4/5 full-video** research snapshots complete and re-opened, 100% source cues dispositioned, claim-level official evidence search and applicability/OPEN, previous knowledge relation review, 0 undeclared unprocessed windows, 0 user `continue` turns, and an output report with scope limitations. Timing, host usage and verified user-turn span must be measured; tests cannot substitute for live model proof.

## Changes relative to the single-video bottleneck

- `FiveVideoResearchBatch`: accepts exactly **4 or 5** independently hashed full originals, pins Git blob revisions per video, and exposes **round-robin bounded source packets** across videos. No prior answer leaks into source-only packet.
- `ResearchRun.BATCH_ACCEPT`: up to 500 declared model/evidence/prior-review actions enter one validated, immutable hash-chained **per-video receipt file**. All subactions are validated before writing; an invalid quote or missing antecedent blocks the entire video bundle. Exact resubmissions are idempotent. Cross-video submission is separately preflighted then committed per video; this is **recoverable but not globally atomic** across a process/power interruption.
- `next_review_bundle` presents outstanding source-linked claims in batches. Sharing an official search URL between claims never proves equal applicability, exceptions, dates, limits or financial fact certification.
- `batch_backup` stores all sources, frozen plans, original/official/prior interpretations and event receipts as five **individually encrypted AES-256-GCM envelopes** in a single package. A new private directory must replay every video and the complete batch status hash before the restoration is accepted. Never upload raw ZIP or recovery key into a public GitHub repository.
- `v5_app.batch_worker` is a GitHub Actions event-driven **5-video status router**, not a model. The public state includes only counts, source SHA, Git prior blob SHA and event heads; it declares financial fact approvals false. It cannot attest private claims.

## Measured five real original sources (#1–#5)

Official historic roster `data/synthesis/investment_knowledge_v4/reviews/v4_002_005_incremental_decision_review_20261029.json`; source bytes were rechecked against `1-100.zip` and old SHA-256 hashes.

| # | Video id | Cues | V5 windows | Source SHA status |
| --- | --- | ---: | ---: | --- |
| 1 | `sz5N9WJS310` | 1195 | 67 | MATCH |
| 2 | `6VEfKF7BzZU` | 1347 | 76 | MATCH |
| 3 | `OiDTNstaSpM` | 785 | 44 | MATCH |
| 4 | `aNfGrcO6WPI` | 758 | 43 | MATCH |
| 5 | `qtluAViPpsQ` | 1044 | 58 | MATCH |
| **Sum** | **5 original sources** | **5129** | **288** | **5/5 MATCH** |

The prior V3 adaptive planner found **346 windows** for the same sources. The new V5 source-only planner uses different context boundaries (max 18 cues / 1600 characters by default) so windows are not numerically comparable as a claim-accuracy score. The 288-window planning result is a source census, not semantic extraction. 5 videos' raw SRT bytes total **394,221**.

- Current test turn: ChatGPT actually read and authored **first W00001 from each of five videos**, source-linked **5 provisional claims** (including 1 video introduction with zero financial claims), **5 evidence dispositions**, **5 prior-knowledge dispositions**. Per-video one-event batch receipts = **5 total**, committed and replayed unchanged; **5/288 windows provisionally processed, 283 unprocessed**.
- Example critical distinction: video #2's phrase `연금, 800` lacks a unit and date within that source window. National Tax Service's contemporary 600/900 tax-credit ceilings are official context only; the historical utterance and personal applicability are **OPEN**, never auto-corrected or approved.
- A first bounded source-only delivery of 25 windows had **36,510 serialized bytes** and included all 5 source videos. **These are packet-preparation metrics, not model reasoning throughput**.
- The 5-video run's encrypted backup and a separate fresh local restoration replayed each source and hash chain. Cloud readback and independent future-chat passphrase possession must be tested independently before treating cloud retention as proven.

**Observed full 4/5-video in one user turn:** **NOT PROVEN / NO-GO.** Estimated 288 source windows plus claim-specific official and prior-knowledge review cannot be certified by synthetic test passes. Increase batch size only with measured source omission/semantic recall checks, and never replace genuine model interpretation with regex-generated answers.
