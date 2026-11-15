# V128 — Synchronous ChatGPT-hosted full-video review and atomic knowledge publication

**Date: 2026-11-16 KST** · Validation branch only, Phase E engine development. The user mandated *finish engine before researching another video or connecting Google Drive portfolio*. This implementation honors that phase order.

## Implemented (not merely proposed)

- **Single host invocation / deterministic continuous loop:** \`v128_host_continuous_video.run_all_video_scopes_in_chat\` loops over **every** parent-plan child manifest in order. For each segment, the current ChatGPT host supplies a *synchronous* callback returning actual V6 host event and source atom exchange, V123 ChatGPT final review, original government-body input, prior knowledge relationships and exact original host replay parameters. The coordinator validates and checkpoints every supplied child before advancing.
- **Resume with original private evidence:** when a child already has a PASS checkpoint, the host callback is required to **LOAD_EXISTING_PINNED_PASS**, retrieving the original private proof; its replay is checked rather than treating a SHA alone as proof. HOLD/rejected child causes immediate whole-parent HOLD and zero cumulative knowledge insertion; an existing HOLD requires explicit ChatGPT-review revision before it can change to PASS.
- **Mandatory cross-child and whole-parent ChatGPT verdict:** after the full child census, a separate synchronous ChatGPT callback supplies conditions/exceptions/rebuttals and cross-scope seam disposition. The exact V1271/V127 parent assembly gate runs; a **separate parent ChatGPT review** must pin parent source SHA, exact parent assembly digest, checkpoint HEAD, each child host receipt+review, seam results and per-child semantic prior relations. A missing/false verdict or changed digest rejects publication. The optional parent-review template deliberately defaults to **false flags and -1 unresolved counts**; code NEVER self-marks final acceptance.
- **Atomic whole-parent candidate storage:** \`v128_atomic_parent_knowledge.publish_parent_once\` takes *all child cases together*, first obtains actual V1271 parent PASS, then clones the owner-private V126 SQLite knowledge DB into a disposable private temporary file. It replays each child's original V6 immutable host event **exactly**, the actual V123 ChatGPT final research gate and prior relation adjudication through the original \`PrivateKnowledgeStore.add_chat_final_batch\`. A child failure, unresolved parent \`CONFLICT\` or newly quarantined/duplicated knowledge aborts the whole operation. The real knowledge DB is touched **only after the entire multi-child staging passes**.
- A **single SQLite \`BEGIN IMMEDIATE\` transaction** then inserts all new \`knowledge\` rows, append-only \`events\` and one \`parent_publications\` SHA-bound record. All SQL event rows and source/parent evidence are verified under the lock before commit; an error at the **last parent-publication INSERT** rolls back all child rows. The immutable parent receipt is idempotent for exact replays, rejects substituted ChatGPT approval, concurrent/stale heads and revised parent proof, and can be re-audited against the original SHA event-chain boundaries.
- The feature accepts **research candidates only** after ChatGPT source-first review; it does not legally certify a source document, approve tax facts, grant personal advisory action, touch protected Master116/P4, submit orders or read portfolios.

## Honest execution boundary

**Python cannot invoke the ChatGPT model on its own without a supported model API.** No external model API is used or introduced. The synchronous host API is a working integration contract, but the *in-chat* ChatGPT host must actually supply the \`review_or_load_child\`, \`review_seams\`, \`review_parent\` callbacks. Installing this code does **not** create an always-running model worker, scheduled task or background execution. The end-to-end **chat host binding and real 1,481-cue / 13-segment semantic review are not certified**. Owner-independent inventory signatures and live official issuer-response provenance are still missing.

## Synthetic end-to-end regressions

The dedicated \`test_v128_continuous_chat_atomic_parent.py\` uses the real V6 \`TransactionStore\` for **two child original-source scopes**, real V123 ChatGPT final gate logic (with *synthetic* approvals and fake government body HTML), V1271 private checkpoint, actual V126 staged cumulative ledger, actual graph audit, and actual SQLite all-child transaction. Negative cases exercise OPEN child, explicit HOLD revision, missing parent ChatGPT review, forged parent verdict, missing seam, forged prior relation/host input, wrong knowledge head, duplicate parent request, changed final review, and final-SQL-insert failure rollback. This is **software proof**, NOT independent semantic truth, official issuer authenticity, owner-production DB P0 GO or a 791-video automated throughput benchmark.

## Release decision

Prior V127.3 1,481-cue real-source test proved **13-segment structural partitioning only**. This V128 implements host-callback continuous review and all-or-nothing parent publication; an in-chat host adapter still must be exercised with full real video semantics. Existing V122 historical 47-cue/18-atom financing review still has **12 finance OPEN** and \`CHAT_FINAL_HOLD_OPEN\`. **No new real video research performed, no new real cumulative knowledge released, P0 NO-GO, no Google Drive portfolio integration**. E1/E5/E6/E7/E9 remain OPEN pending real acceptance.

### Next objective

Run V128 on previously acquired long private original with actual ChatGPT reviewing each segment in one user turn (with external source capture and owner inventory reconciliation), validate 13/13 semantic windows and a real all-or-nothing current-db checkpoint/release; then verify current-law, cumulative retrieval and user-question advisory end-to-end without model API or false approvals.


## V128.1 — unittest naming collision correction

The first V128 CI run failed before executing its new tests because the helper \`V128HostRunAndAtomicParentTests.run(self, **kw)\` accidentally shadowed Python \`unittest.TestCase.run(result)\`. The helper is renamed \`run_engine\` throughout the dedicated test module and re-queued in CI. This is a test-harness invocation correction, not a semantic research approval.


## V128.2 — Actual new full-path CI exceptions corrected

The second V128 CI successfully entered all 15 tests and exposed (1) a Python \`staging_head\` variable typo in the full-knowledge-DB staging audit, (2) negative regression assertions that treated creation of an **empty** \`parent_publications\` metadata table as a publication, and (3) native V6 concurrency error \`ConcurrentHeadChanged\` being rightly rejected but not listed in the forged-replay test's expected exceptions. Corrected all three. The core safety invariant is **zero entries and zero events**, even when empty schema metadata exists.


## V128.3 — close the old per-child direct-write bypass

The V126 **public/private production** \`PrivateKnowledgeStore.add_chat_final_batch\` path now rejects **partial source scopes** by default, even if a child V123 review PASS exists. Only the disposable \`v128_staging_*/staging.db\` instance used by the V128 atomic parent publisher may temporarily assemble partial children; such staging instances cannot answer questions or revoke knowledge. Thus older clients cannot accidentally store a long-video child before other children and the parent ChatGPT final review pass. Two additional negative tests verify direct partial publication and temporary DB Q&A/revocation are blocked. This flag is an in-process programming boundary, not a tamper-proof identity attestation against arbitrary malicious Python execution.


## V128.4 — Public source-byte SHA receipt alignment

The files connector's extracted text dropped the final LF during Git tree construction. Restored the canonical POSIX newline on V126/V128 Python source and test files without changing program semantics. The public V128 SHA receipt's three content hashes are now intended to match the actual Git blob UTF-8 bytes, not only the local pre-upload files; validated by direct GitHub content readback. Original owner-private data remain absent.

