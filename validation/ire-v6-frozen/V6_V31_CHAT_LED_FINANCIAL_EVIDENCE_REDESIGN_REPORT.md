# V31 — ChatGPT-led finance evidence judgment, deterministic audit and bounded operational reuse

**Scope:** additive validation-only implementation on Draft PR #53. V22–V30, protected original V5, 116 knowledge items, P4 29, original SRT and historical frozen manifests are untouched. This is an architecture / software contract release, **not** independent semantic certification or all-791 production deployment.

## 1. Reassigned authority

| Task | Authority / execution | Machine-verifiable boundary |
|---|---|---|
| Read original SRT, source windows and candidate atoms | Existing V6 source, V28–V30 | SHA-256, cue ownership, exact quote, conditions/exceptions, literal numeric references |
| Judge what speaker actually claims, asks, quotes, rejects, qualifies | **ChatGPT host in this chat** | V31 typed meaning review for each atom with atom-frame SHA, original cue SHA list, speaker, stance, condition/exception fields |
| Retrieve the **currently applicable** official Korean rules | **ChatGPT host web-search / reasoning** | Existing V22 source allowlist, dates, excerpt digests, rule IDs and scope; publisher authentication is not inferred from URLs |
| Judge current rule **as of the present response**, not filming date | **ChatGPT host** | V22 claims vs dated rule IDs, missing conditions and classification |
| Compare prior knowledge for same / refines / conflict | **ChatGPT host** | V31 per-atom relation review plus optional master claim-ID / SHA digest; topical similarity alone never auto-merges approved master116 |
| Relevance and adversarial omission detection | Host plus existing V26/V27/V29 | Full candidate census, relevant facet, split-ASR context, zero unresolved semantic-review risk |
| Generate contextual general financial education reply | Existing actual V27→V5 P3 + ChatGPT | V31 opt-in question route *only after* chat evidence gates; hash-only result and explicit educational scope |
| Independently certify semantic precision/recall or approve a personal order/tax outcome | **Separate source-first blind expert protocol**; not current-chat self-review | Explicitly **false** in all V31 receipts. Frozen 9-video / 6,829-cue prospective gold protocol unchanged, gold absent. |

No external ChatGPT/model API. Execution is orchestrated by an active ChatGPT user turn; no autonomous background execution claimed.

## 2. New additive contract: `ire/v6/chat_led_evidence_v31.py`

**Private input stage** — `prepare_private_chat_packet_v31(source,exchange,current_as_of,primary_evidence,start_index,max_claims)` emits a private-only, paginated claim list (up to 25 atoms) with original quotes, asserted speaker/stance, exception/condition cues, literal number tokens, original frame hashes and current official excerpts. Allows empty official evidence specifically to prompt ChatGPT to search official issuers. The packet and full answers **must never be uploaded to public GitHub**. The packet has an explicit `next_start_index` to cover large videos without conflating an entire film with a single window.

**Host decision stage** — ChatGPT returns (a) a source-bound `meaning_reviews` row for each claim; (b) V22 `regulatory_decisions` bound to original proposition and real current-law evidence; and (c) `prior_knowledge_reviews` with `UNREVIEWED`, `NO_MATCH_FOUND_CHAT_ONLY`, `POSSIBLE_RELATION_PENDING` or a specific SHA-pinned master-knowledge candidate. It may mark `UNRESOLVED`; it **cannot** establish itself as an external reviewer. All judgments require an exact atom SHA, full original quote-cue SHA list, claim role, speaker and relevant condition/exception indices, contemporaneous reviewer/as-of, checked numeral scope and text rationale.

**Deterministic audit stage** — `audit_chat_evidence_v31` calls existing actual V6 source audit, V14 semantic-risk audit, V30 original numeric-token census and V22 dated-official-rule reassessment. Fails closed on unknown source/cue, tampered original, wrong rule hash, future/expired rule as current, false master knowledge claim or claim/source attribution drift. Missing host decisions remain `PENDING_CHAT_EVIDENCE_OR_SOURCE_REPAIR`; a whole-video research pass is `CHAT_EVIDENCE_REVIEWED_EDUCATIONAL_ONLY` only when each supplied atom has a completed host meaning, dated regulatory disposition, documented prior-relation review, zero raw semantic-risk alerts and no unanchored literal numbers.

**Question/answer stage** — `evaluate_chat_question_v31` requires every *selected* claim to be `CHAT_REVIEWED_GENERAL_EDUCATION` or `CHAT_REVIEWED_CORRECTION_ONLY`. It then reruns original V26 candidate census, V27 source-facet omitted-claim audit, V29 split-ASR pension context audit and the actual V27→V26→V25→V22→V5 P3 answer generator. Questions asking the engine to directly send an order, move money, sell or execute an investment transaction fail before V5. A legally disproven historical claim is usable only as an explicitly corrective explanation, not promoted to true current law. Source `QUESTION` / `QUOTED` speech cannot be relabeled a proven fact by host approval.

**Output custody** — Public-safe receipt includes source/claim/review/official input and answer digests, per-claim status, counts, open-issue IDs and explicit FALSE flags for all independent-gold, individual advice, knowledge auto-merge and P0 GO. No transcript, official excerpt body, personal question body or complete answer is included. The actual private original archive still must be replay-attested by existing V28/V29 local trusted entrypoints; a source object alone does not prove local ZIP bytes were reread in the final call.

## 3. Trust / policy separation

`CHAT_REVIEWED_GENERAL_EDUCATION`: same-chat interpretation supported by stated current general-rule excerpt, not publisher/expert certified.

`CHAT_REVIEWED_CORRECTION_ONLY`: host judges old/source blanket claim wrong or under-qualified vs currently applicable rule; **original claim is not reused as true**.

`QUESTION_OR_QUOTE_NOT_VERIFIED_FACT`: speaker asking or quoting is not equivalent to a true narrator fact.

`CHAT_REVIEW_REQUIRED` or `SOURCE_RISK_OR_NUMERIC_LINK_PENDING`: remain open, never silently approved.

All same-chat classes are provisional for wider 791-video knowledge integration. Specific master116/P4 relationships require actual master record review; no auto-merge of `NO_MATCH_FOUND_CHAT_ONLY` into new facts.

**Operating benefit:** Independent blind gold absence no longer forces every *general educational* answer path to stop. This is **not** a relaxation of independent engine quality certification, personalized suitability review or financial law scope requirements. The blinded 9-video preregistration, gold precommitment requirement and all original P0 checks remain unchanged.

## 4. Limits, verification, and rollout

- New **28 synthetic tests** exercise chat omission, false current law, invalid official excerpts, tampered atom/cue/speaker/number, false prior-knowledge assertion, question-as-fact laundering, quote handling, private packet pagination, V5 route, and refusal of trade actions.
- Previous V6 **417** unique tests; expected V31 total **445**. Final full V6/IRE/V5/app/preflight/one-turn CI and cleanroom must be verified at the exact pushed commit before software PASS.
- No new private owner SRT replay through the **new V31 host decision contract** in this code-authoring session, and no real external model API. Previously V30 source/3-question E2E tests do not imply an unseen end-to-end V31 original replay.
- Semantically complete atom extraction, host judgment correctness, official document body publisher authentication and final answer decision utility **cannot** be proved by deterministic receipts. Independent gold precision/recall remains **UNMEASURED**; P0 research-quality **NO-GO** and Draft PR remain.
- To extend to the 791-video workflow: stream 25-atom private chat packets per source, collect all signed SHA-bound same-chat review decisions in the same turn, fail closed on unresolved high-risk claims, then persist hash-only operational evidence. Follow-up independent blinded sample separately.

**Decision: V31 shifts judgment authority to ChatGPT, deterministic engine enforces custody and safety; permits evidence-scoped operational financial education only, never independent gold GO.**
