# V126 — ChatGPT-final-gated private cumulative knowledge prototype

**Date:** 2026-11-15 KST · **Scope:** E6/E7/E8 partial engine development only, no new video research, no Google Drive portfolio access or integration.

## Actual implementation

- `v126_chat_approved_knowledge_store.py` implements `PrivateKnowledgeStore` using a private SQLite database and an append-only SHA-256 event chain. It must be placed in a nonpublic directory. The code itself is public; owner source quotes and accepted candidate text remain private.
- **Mandatory V123 gate:** `add_chat_final_batch` calls the existing `v123_chat_final_gate.require_chat_final_release` **before opening the accumulating database for writes**. `CHAT_FINAL_HOLD_OPEN`, missing real host DB, missing original official body, cue/atom gaps or absent ChatGPT review therefore reject the entire batch.
- **Prior protected knowledge:** calls the existing `ire.v6.prior_knowledge.audit_prior_candidates` against immutable Master116 + P4 29 read-only bytes. For each source atom, a separate ChatGPT semantic relationship verdict, claim-content hash, and private review digest are required. The prototype supports only **one pending prior relation per atom**; more complex cases remain explicitly blocked. Target options include the SHA-bound existing protected prior record and an already-accumulated active candidate.
- **Private ACID cumulative log:** deterministic SHA IDs, immutable evidence payload, single transaction per batch, expected head, idempotent same-input retry and fail-closed no-partial-write handling. The audit replays each event's full SHA chain against its stored immutable private record. An **independently held external head checkpoint is still needed** to detect complete database replacement.
- **Conflict / duplicate safeguards:** `CONFLICT` rows are kept in history but quarantined from Q&A retrieval; exact duplicate proposition text cannot become separate NEW/EXTENDS knowledge without explicit equivalence judgment; removal requires a reviewed SHA-backed tombstone event without erasing source history. **Semantic equivalence is supplied by ChatGPT, not proven by lexical matching.**
- **Read-only question evidence packet:** `evidence_for_question` returns citeable private owner-source claim frames, source/manifest hashes, concept IDs, review lineage and possible lexical relevance. It cannot autonomously author a personal investment or tax recommendation and flags all finance as requiring fresh official-body/current-law/ChatGPT rechecking. Retrieval's lexical ranking is **not independent relevance precision**.

## Test evidence

Actual local Python replay using the frozen public V6 synthetic host-batch fixtures plus the **real existing V123 final ChatGPT gate**: **9/9 dedicated V126 tests PASS**, including genuine V6 batch and synthetic PASS -> private insertion, no ChatGPT review -> no insertion, finance OPEN -> no insertion, forged/missing relationship -> rollback, same-input idempotence, changed head, SQL tamper detection, revocation and withdrawn-candidate search blocking. The V123 test suite also passed when included by the initial test collection. These tests use **synthetic government text and simulated ChatGPT verdicts**, so they prove software enforcement, not independent law authenticity or semantic recall.

## What has NOT been achieved

- The owner-private V122 47-cue 18-atom case is still **`CHAT_FINAL_HOLD_OPEN`**, finance OPEN **12**. **No real new video accepted into this ledger**, no currently approved personal finance fact, no new research knowledge released.
- No actual owner operational DB or owner-independent inventory was verified; the V123 historical staging run remains isolated.
- Multi-window one-request long-video orchestration, multi-relation conflict adjudication, shared ontology supersession, production external checkpoints, full-text retrieval, live current-law lookup to chat-authored answer, and real end-to-end acceptance are **still OPEN**.
- The two-way boundary is unchanged: user first requires finished research engine (Phase E); only then new video research (Phase R); **Google Drive portfolio integration remains Phase P after engine completion**.
- Frozen `ire/v6` implementation, V5, Master116, P4 and `main` remain untouched.

**Decision:** E6/E7/E8 **active prototypes under development, not PASS**; V125 machine-status becomes `OPEN` for three prototype items. All ten final-completion requirements remain unresolved, research rollout blocked, **P0 NO-GO**.
