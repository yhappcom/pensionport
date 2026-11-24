# V6 research and evaluation separation — P0-2-05 architecture revision 2026-11-24

Decision: preserve the two-user-turn research process and the frozen 95%/98%/0 independent threshold. Separate engine benchmarking from individual video approval. No external API, no new branch, no automatic approval or publication.

## Track A: engine performance

- Existing ETF250 and 68/70-atom revisions are exposed development samples only; previous failed trials and preregistration remain immutable. Future holdout campaigns use actual newly selected original bytes and a frozen engine commit/prediction before scoring.
- Generic V2 campaign plans bind engine commit, video ID, original SHA/cue count, prediction SHA/atom count, source-only packet SHA and fixed rubric. Append registration records without overwriting prior plans; known ETF video or prior registered source cannot be relabelled holdout.
- L1 = structural diagnostic; L2 = complete internal reference and alignment; L3 = recorded two manually reported source-only review exports with transcript hashes and consensus lineage, NOT proof of context isolation; L4 = trusted host/reviewer production verification via existing signature gate and independently pre-enrolled campaign plan/registry pins.
- No caller-controlled enrolment. PINNED_CAMPAIGNS is empty. A local hash, user claim, synthetic test or L3 result does not establish L4. The public CI cannot certify private source review. Same-model common errors remain even in distinct sessions.
- Generic assessment returns exact counts and separate diagnostic/independent flags. L4 holdout meeting thresholds yields assessment readiness only, not a checklist PASS, E3/E4/E5 release or personal advice.
- Historical receipt checks now have a separate historical-only mode, and the original six receipt/plan blobs are pinned. Their validation does not require the live cursor to remain HOLD. CI also runs the existing live guard independently, which continues to reject false advancement. The positive public checklist transition remains unenrolled until genuine L4 evidence can be reviewed; historical checks cannot authorize it.

## Track B: ordinary research

TURN1 user command: whole source, semantic interpretation, candidate atomization, current official financial evidence, prior relations, freeze. TURN2 separate actual user command: re-read source, adjudicate every cue/atom, repair, evaluate official evidence, hold or quarantine unresolved claims, final authorization and atomic publication only under existing E3/E4/E5. No per-video independent performance certification required merely to validate the research workflow; current overall engine release gates remain in force. Never represent internal review as L4.

## Current status

R01 design split, R03 generic schema/registration and production pin routing, R04 graded evaluator implemented; synthetic coverage added. R02 historical receipt validation separated and pinned; current public gate still fail-closed pending genuine positive evidence transition. The historical-only mode is never used as release authority. R05 real SQLite replay, R06 new unseen source registration, R07 actual metrics, R08 cross-domain generalization, R09 final pass not completed by this change. No real independently authenticated reviewer exists. Keep P0-2-05 HOLD, 16 PASS / 43 BLOCKED, and all historical receipts.

## Follow-up: positive checklist transition and owner-source reinspection

Private assessment_closeout.propose_closeout re-executes the actual production L4 checker. It never accepts a supplied grade, mutates a checklist, or publishes knowledge. The separate public live guard checks a reviewed exact receipt digest, existing pre-review campaign enrolment, exact TP/FP/FN counts and same-engine six-job CI record, the checklist evidence blob, and the existing live sequential/status validators. Public CI does not have private source or independent host authority: a future independently reviewed enrollment must verify the private L4 replay and actual GitHub run before the public pin is changed. Both real pin maps remain unenrolled. Old receipts remain checked as history, not current authorization. Synthetic tests simulate the positive route, not financial accuracy.

On the owner-private saved ETF development artifacts (not a new holdout), separate local inspection rehashed the trial ZIP and all eight members, verified original SRT250 and native68 SHA, 70 revised atoms, 58 unchanged surviving atoms, 78 direct source quotes (0 mismatch), 0 missing prior direct quote links and 0 exact duplicate native atoms. The canonical revision input/output record is 238002 bytes (below 1048576-byte canonical-object ceiling); this is a size check, not a SQLite commit. Latest repository checkout was unavailable in the local runtime, so no claim of real new native SQLite execution. Prior preserved real data: 171 unresolved cues, 58 unknown speaker labels, 61 unresolved native stances. Independent metrics remain null.

No current status change. R02 transition guard implemented and awaits real independently reviewed enrollment; R05 actual latest engine replay remains open; no R06-R09 claims.
