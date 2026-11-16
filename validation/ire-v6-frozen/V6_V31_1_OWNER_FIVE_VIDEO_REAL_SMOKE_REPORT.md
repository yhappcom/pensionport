# V31.1 actual private owner-original five-video smoke, prior-knowledge release fix

**When:** 2026-11-10 KST. **Status:** source-scoped, same-chat actual V31 execution; historical V30/V31 code and synthetic CI do not substitute for real original full-video research or independent gold. Validation Draft PR #53 only; no main/master116/P4 modification.

## 1. Exact actual owner originals and sampling boundary

The original owner-provided `1-70.zip` ZIP was actually opened locally; SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`. The FIVE target originals were found, UTF-8 SRT parsed by the exact V6 parser and SHA verified:

| Video | Original YT ID | Total original cues | Tested cue range | Tested cues | Candidate atoms | Actual V31 evidence state |
|---|---|---:|---|---:|---:|---|
| #1 | `sz5N9WJS310` | 1,195 | 1123–1127 | 5 | 1 | correction/education available for scoped claim |
| #2 | `6VEfKF7BzZU` | 1,347 | 177–181 | 5 | 1 | **PENDING** source-unit ambiguity |
| #3 | `OiDTNstaSpM` | 785 | 143–150 | 8 | 1 | correction/education available; **actual unmocked V27→V5 P3 answer executed** |
| #4 | `aNfGrcO6WPI` | 758 | 273–278 | 6 | 1 | general investment principle education available |
| #5 | `qtluAViPpsQ` | 1,044 | 300–303 | 4 | 2 | question distinguished from unsupported factual assertion; general education available |
| **TOTAL** | 5 originals | **5,129** | **PARTIAL** | **28** | **6** | **4 eligible scoped studies, 1 PENDING** |

This is **28/5,129 original cue positions (~0.55%)**, not full five-video source atomic extraction; never report the 5 original videos as researched end-to-end. Each trial uses a real `IRE_V6_SOURCE_PLAN_V1` with scope `PARTIAL`, preexisting pinned ZIP bytes, source SHA, and exact window-text SHA. Actual `verify_source`, `audit_host_atomic_exchange`, `audit_semantic_risks`, `prepare_private_chat_packet_v31`, and `audit_chat_evidence_v31` were called for all five. All tested cue positions were original-bound; no source-risk heuristic alerts arose in the deliberately narrow windows. Original captions and ChatGPT host text not in GitHub.

## 2. ChatGPT supplied real current Korean law evidence and 116-claim knowledge

Original master ledger `data/claims.jsonl` opened locally, **116 records**, Git blob `ab5af7eea02e65d5e36174546a2a94f4cc642d92`, exact known baseline pin. Source-first ChatGPT reviewed current official public legal pages dated 2026-11-10:
- [근로자퇴직급여 보장법 §9, in force 2026-09-18](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1030452785): employer pays by transfer to worker-designated IRP/account with statutory exceptions; **not an unconditional legal mandate to open a separate new IRP**. #3 original overbroad speaker assertion corrected. Account institution requirements and individual facts OPEN.
- [조세특례제한법 §91조의18, in force 2026-09-18](https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1024359131): joining/extending ISA is legally contemplated, but renewal eligibility, maturity settlement and timing of tax benefits require separate analysis. #1 term-extension context is a scope warning rather than a categorical ban.

Host model meaning frames distinguish historical reported speech from current rule, numeric units, speaker uncertainty, conditions, and educational vs current fact. Actual prior116 claims compared at original ledger: #1 C32, #2 C40, #4 C63, #5 C09; #3 new-IRP-only assertion has no confirmed exact match. These are chat-reviewed relation candidates, **not auto-approved new knowledge merges**. Official web excerpt hashes are content integrity of CHAT-prepared summaries; `document_body_sha256=None` and publisher-authenticated full body remains false.

#2 partial source contains unit-elided ASR account allocation numbers; `numeric_scope_checked=false` expressly keeps this candidate PENDING. It would be misleading to infer numeric KRW unit from bare ASR tokens.

## 3. Actual non-mocked V31→V27→V5 P3 question-path

For #3, source-scoped input and current-law decision passed V31 source-first and existing V27/V26/V25/V22 guards, then **called the real installed `ire.v5.advisory_answer_pipeline.answer`**, not a test mock. Final answer SHA-256 `d0bd9261609b5d4afac6609de2c49f83c98a7487a7d08b15926bd2115a0b8c12`; hash-only V31 question receipt `cddfd204ddf3af1882f8fb80763f977f7ec5034f9e005eac7c8ad15d548fb09e`.

**First attempt demonstrated a real route-linguistic limit:** question paraphrase "퇴직금을 받을 때" triggered `V27_NO_SUPPORTED_FINANCE_FACET`; explicit phrase "퇴직금 수령" passed. No silent rewrite; original wording rejection is recorded. The V27 lexical facet router does not handle #4/#5 generic loss-behavior/diversification question types, even when their V31 source evidence passes. Those routes require additional safe ChatGPT final-answer output handoff; do not count them as V5 actual E2E passes.

The V31 final answer receipt itself marks `private_original_bytes_replayed_in_this_call=false` because its final method accepts an already verified source. The host script did open the owner private ZIP and pass its exact original bytes through `verify_source` immediately before invoking V31. **Do not claim fully integrated V28 archive attest-to-V31 V5 transaction proof** or universal one-turn orchestration.

## 4. Real old-V31 defect found and repaired

Real #4 owner-original source smoke with valid `prior_knowledge_reviews` rows changed to `UNREVIEWED` or `POSSIBLE_RELATION_PENDING` **previously returned `CHAT_EVIDENCE_REVIEWED_EDUCATIONAL_ONLY` and `operational_research_ready=true`**. This is an actual unsafe completion claim, not a hypothetical unit issue.

V31.1 **fail-closed fix** in `ire/v6/chat_led_evidence_v31.py`: a claim can enter the educational/correction-ready state only if `prior_review is not None` **AND** its relation is neither `UNREVIEWED` nor `POSSIBLE_RELATION_PENDING`. An explicit unresolved relation now stays pending, preserving source/usefulness gates. Two new negative regression tests in `ire/v6/tests/test_chat_led_evidence_v31.py` assert this behavior. Original V31 manifest retained as historic reference; a separately pinned V31.1 override records modified files. Local V6 full suite **447/447 PASS**. Exact final commit CI must be checked before any claim of GitHub PASS.

## 5. Remaining open quality gates

* Source-wide extraction and recall for five originals: **not performed**; 28 sampled cue positions only. Broader original 791 rollout **NOT APPROVED**.
* Full current official issuer-body authentication and personal applicability: **OPEN**.
* Human-independent blind gold recall/precision on frozen 9-video / 6,829-cue cohort: **not measured**, do not conflate model self-review or 447 unit tests with certified semantic accuracy.
* #2 numeric unit clarification: **OPEN**.
* #4/#5 general investing/behavior final-answer route and #3 paraphrase normalization: **OPEN**. Do not auto-fabricate a V5 P3 call.
* Code and private originals are stored separately; no private SRT, exchange, host review details or final user question/answer body is published to GitHub.

**Decision: V31.1 actual private 5-original PARTIAL-scope smoke PASS, one actual V31→V5 current-rule educational answer PASS, prior-knowledge false-ready defect fixed. Full original-video meaning research, independent engine semantic-certification P0 and global adviser release remain NO-GO.**
