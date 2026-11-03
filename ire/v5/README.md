# IRE V5 — one-command research transaction core (first executable vertical slice)

**Status (2026-11-03):** Three original #1 adaptive windows were actually reviewed by ChatGPT during one user request, official NPS sources were searched, prior-study relation candidates were considered, and 26 source-linked receipts were sealed and reopened using 26 deterministic `next_task()` host steps. **This does not prove an 81-window fully automatic run** and does not certify investor-specific financial facts or advice.

## Product architecture: one command, two roles

- **ChatGPT host / control plane:** Within the user's research request, reads SRT packets, interprets finance semantics, calls official-source search, judges conflicts and exceptions, and submits the resulting structured decisions. *It is not a Python API and cannot be invoked again by `engine.py`.*
- **V5 deterministic transaction kernel:** Validates the full-source cue ownership plan, the exact source hash and per-window direct citations; accepts actual host-authored semantic answers; checks that each claim has an evidence-disposition and prior-knowledge decision; stores an append-only chained receipt per step; and seals a bounded research report only when every selected window and claim has passed the mandatory steps.
- **Separate human/official verifier:** Outside this pilot. A current ChatGPT self-assertion cannot approve a financial fact or personalized advice. V5 intentionally refuses `FACT_VERIFIED_IN_SCOPE` until a separately verified provenance mechanism exists.

## Interface

`ResearchRun(original_srt_bytes, fixed_manifest_dict, private_store_dir)` loads the run and checks its source binding. Use `packet(window_id)` to present exact primary cues to ChatGPT. The *current chat* creates a `MODEL_ANALYSIS` response with every primary cue disposition and direct original quote; `append("MODEL_ANALYSIS", payload)` validates it. Next submit `EVIDENCE_REVIEW` and `PRIOR_RELATION_REVIEW` for each claim. `next_task()` returns the next required model/evidence/relation/closure step in the same chat request; it does not execute model inference. `close()` seals only after all selected windows, claim evidence obligations and relation reviews are represented; `replay()` verifies stored immutable SHA-256 event chains. Every run has a frozen source baseline and exact Git blob pin for prior research.

**No external LLM API calls, no automatic transcript summarization heuristic, no invented model answers.** The ChatGPT host is a real participant and may be constrained by model/tool execution limits. The project cannot claim that a Python loop provides unattended host inference.

## Original-source pilot record (not committed)

- Input: video #1 `sz5N9WJS310`, source SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f` (1,195 cues; V3 adaptive manifest 81 windows).
- Selected **W00003–W00005**, 45 original cues, 11 newly interpreted atomic statements across the personal NPS catch-up case and pension-savings comparison.
- Source verification: official National Pension Service FAQ (119-month ceiling and personal eligibility, not a guaranteed benefit projection); personalized KRW18m and KRW250k/month figures remain case-only OPEN.
- 11 claim evidence decisions (all OPEN/not fact-approved) and 11 prior-reference reviews (no automatic merge). 26 chained receipts, readback verified in a separate `ResearchRun` instance.
- Runtime outcome: `RESEARCH_REPORT_COMPLETE_WITH_OPEN_ITEMS` **for the three-window pilot scope only**. The other 78/81 windows were deliberately outside this pilot and are *not* completed.
- Run head for the verified local pilot: `e518a271b5e31a22a2878fa438f9ae22caeda5bef4e731ac7ddfb03fae390b9f`.

## Tests and safety constraints

`python -m unittest discover -s ire/v5/tests -v` — 16 synthetic regression/negative tests, distinct from the private real-source pilot. Detects source/plan drift, wrong source quote, missing cues, missing claim evidence, missing prior relation, duplicate checkpoint, forged fact approval, stale legacy revision, tampered receipt, and false closure. No synthetic success constitutes an independent semantic accuracy score.

### Next blockers

1. Establish durable private external storage for the full event chain (not just ephemeral runtime files) and cross-session readback. Do not publish private SRT/claim text to GitHub.
2. Extend current ChatGPT host research over all 81 source windows, with genuine source reading and official-source review in the same request; benchmark tool/time constraints rather than assume unlimited execution.
3. Integrate issuer-specific original-document byte capture, laws' effective dates and exceptions with an independent attestation; support per-claim verification with a cryptographically authentic external reviewer.
4. Execute full prior-knowledge relation diff, including previous video #1's 23 historical claims, then relevant external video corpus, without overwriting earlier approved studies.
5. Distinguish `RESEARCH_REPORT_COMPLETE_WITH_OPEN_ITEMS`, `FACT_VERIFIED_IN_SCOPE`, and question-scoped `ADVISORY_ELIGIBLE` as three independent release grades.

Legacy V3/V4 code and the `main` branch are not modified by the V5 vertical slice. Changes live under `ire/v5/` on an independent V5 development branch.