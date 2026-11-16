# V114 — 5-stage ChatGPT-host integration + real private 160-cue pilot (NO GOLD)

**Scope/date:** 2026-11-14 KST. GitHub verification PR #53, isolated from `main`, V5, Master116 and P4. This is an implementation/pilot report, **not** a released or fully autonomous 791-video research engine.

## Implementation

- **P0-1 source → parent → semantic unit:** `ire/v6/research_pipeline_v114.py` adds `audit_source_unit_crosswalk()`. It replays actual private cue text SHA in memory, binds source cue to 52 draft parents and 85 semantic/discourse units, recomputes each unit digest from exact source cue hashes, checks full cue disposition including 2 unassigned gaps, and reconciles all 85 V112 shadow statuses. It cannot verify **meaning completeness** or produce new ChatGPT inferences. Original V39/V40/V41 host semantic authoring and V6 proof gates are unchanged.
- **P0-2 ACID checkpoint/restart:** `V114ResearchJournal` stores exactly five stage receipts (`SOURCE → SEMANTIC → FINANCE → METRICS → KNOWLEDGE`) in a SQLite chain with expected-head checks, deterministic idempotency, rollback on failed writes, stage order enforcement and read-time integrity replay. Checkpoints contain hashes/counts only, not original SRT or owner-private reasoning. **This is crash-resumable bookkeeping; it does not run the ChatGPT model without an explicit host invocation or jump across turns automatically.** The V40/V6 ledgers remain separately authorized; this pilot journal is not their formal commit.
- **P0-3 financial evidence:** `audit_official_fact_docket()` enforces one source-bound status per `FACT_CANDIDATE`, checks exact candidate ID coverage, official HTTPS issuer domains, same-date check flags, and blocks all invented financial/personal approvals. URL verification in code is **metadata only**: neither HTML contents nor legal entailment is cryptographically proven. For the actual 5 cases, 2 pension tax cases have 3 official-reference pointers and are still OPEN, and 3 personal/company-history cases remain `SOURCE_FACT_OPEN` without verified independent issuer proof. The official primary-body bytes are not pinned in this pilot.
- **P0-4 stage instrumentation:** the private replay records monotonic local nanosecond *structural* spans for ZIP load/parse, source/unit crosswalk, evidence-docket guard, and prior metadata preview. `model_semantic_wall_ns`, `official_search_wall_ns`, `open_resolution_wall_ns`, and `independent_adjudication_wall_ns` are **null** because no valid per-stage isolated measurement was obtained. Never substitute CPU structural runtime for the ChatGPT model semantic-review duration or 791-video forecast.
- **P1 historical/knowledge preview:** a V113 prior overlap count of 1 source position against V96 is carried as **existing metadata**, not re-derived from V75. The V75 404-record identity mapping remains unavailable, whole-history dedup is **NOT complete**, 0 knowledge relations were formally confirmed, and 0 actual knowledge/portfolio/advisory writes occurred.

## Real owner-private pilot, not synthetic source replay

The offline pilot read and verified original bytes of recovered owner-private `V110`, `V112`, and `V113` ZIP packages by SHA-256; it did **not** re-fetch/re-hash the original `1-70.zip` itself or play audio/inspect original video frames. It then validated the actual 160-cue packet text hashes, parent links, unit hashes and V112 statuses. Results:

| Unit of measure | Actual replay |
| --- | ---: |
| Original-source-derived cue positions | **160** across 4 windows |
| Cue positions attached to V110 parents | **158** |
| Unassigned, explicitly preserved positions | **2** |
| Draft parent spans | **52** |
| Source-bound semantic/discourse units | **85** |
| Previously V111 context-resolved units | **10** |
| V111 evidence OPEN units remaining | **12** |
| Unit status not from original V111 OPEN docket | **63** |
| First-pass financial fact candidates | **5** |
| Per-fact provisional finance dispositions | **5** (2 general-rule limitations; 3 source fact OPEN) |
| Official government URL pointers for the 2 pension tax cases | **3** (metadata only) |
| SQLite stage checkpoints / restart recovery | **5 / PASS** |
| New ChatGPT semantic inference; actual independent gold | **0 / none** |
| Formal new financial knowledge, personal tax/advice approvals | **0 / 0** |

The owner-private recovery package `V114_PRIVATE_5_STAGE_160_CUE_PILOT_NO_GOLD.zip` includes the exact source ZIP digests, 5-stage SQLite checkpoint, per-fact OPEN docket, pilot script and SHA-only public receipt. It does not publish private text or personally identifying account information. Public receipt is `validation/ire-v6-frozen/V114_ACTUAL_PRIVATE_PILOT_PUBLIC_SHA_ONLY.json`.

The P0 pilot **does not prove** that the V110 85 units are the complete and correct atomic-claim set, the current regulatory facts are legally sufficient for all time periods, or that the model can complete a video by itself. Evidence debt remains: `OPEN_AUDIO=7`, `OPEN_VISUAL/ACCOUNT_VISUAL=4`, `OPEN_ACCOUNT_SCOPE=1`. No OPEN unit was silently closed.

## Software regression and quality gates

`validation/ire-v6-frozen/test_research_pipeline_v114.py` contains **27 synthetic regression tests**: source SHA tamper, wrong parent/unit source identities, missing cue/OPEN, forged approvals, unsafe official URL, stale evidence date, per-fact completeness, journal idempotency/stale head/stage order, restart, SQL chain corruption, disallowed private text, and unsupported V75-dedup promotion. Local CPython suite: **27/27 PASS**. The V6 frozen CI workflow invokes this regression explicitly; exact-head CI success must be separately confirmed after push.

The driver implements deterministic policy and owner-private replay, **not** a hidden independent adjudicator. Formal precision, recall, high-risk recall and true complete-video elapsed time remain `NO-SCORE`. `p0_go=false`, `research_complete=false`, `independent_gold=false`, `financial_fact_approved=0`, `personal_advice_approved=false`. Do not promote any test or stage to Master116/P4/V5.

## Remaining blockers / proposed execution criteria

1. Make one video run through **actual new chat semantic authoring**, V39 → V40 → V41 → V6 model/proof gates, under an explicit host invocation. Existing 160-cue replay only validates *old* model-authored annotations; it does not generate new claims.
2. Resume after interruption **without mutating completed steps**; subsequently measure per-step times using actual model/official lookup/open resolution timestamps. Session persistence is currently a hash journal, not autonomous ChatGPT invocation.
3. Resolve real audio/screen evidence where available and avoid closing the personal-account case without actual account facts. Re-check the specific 2026 effective legal rule on each applicable financial claim and pin genuine official document bytes.
4. Restore V75 historical claim identity, source-key crosswalk and conflicts, then perform a **read-only** P1 comparison before any new knowledge approval.
5. Only with independently adjudicated blinded claims measure precision, recall, and high-risk FN; until then P0 quality approval remains NO-GO.

**Assessment: source/annotation integrity integration PASS, ACID stage restart PASS, 5-case finance evidence docket coverage PASS at metadata level; new autonomous model execution NOT IMPLEMENTED, full financial truth and 791-video throughput NOT PROVEN, P0 NO-GO.**
