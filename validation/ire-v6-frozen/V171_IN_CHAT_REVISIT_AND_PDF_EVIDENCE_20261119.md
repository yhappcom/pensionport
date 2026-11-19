# V171 — current-chat re-review of a previously KEEP_OPEN atom and publisher PDF evidence derivation

Date: 2026-11-19 (KST)  
Scope: V167–V170 draft code only; no frozen/native approval code modified.  
Target parent: `verify/ire-v6-v170-chat-boundary-revisit-20261119`.

## Problem 1 — no direct in-chat call for second-pass evidence revisit

V170 added `EvidenceRevisitJournal.run_revisit(...)`, but it still required an opaque `chat_reviewer` callback. Without an LLM API, a real ChatGPT reviewer must author a response **in this conversation**, and Python cannot itself be the reviewer. The new `v171_in_chat_revisit_bridge.py` implements `prepare_revisit_chat_turn` / `commit_revisit_chat_turn`: (a) full original claim/context/condition and past evidence hashes, (b) truly new evidence excerpt and request hash, (c) explicit current-chat verdict, (d) exact source, prior proposal, revisit chain and new evidence byte verification, (e) V170 append-only atomic commit. Missing answers and forged model/E4 claims cannot advance progress. The adapter *does not* call the model or create ChatGPT judgments on its own.

## Problem 2 — compressed PDF original bytes are incompatible with V167's excerpt substring rule

The legacy V167 `_evidence_summary` demands `excerpt.encode('utf-8') in body`. In legitimate publisher PDFs, visible text frequently resides in compressed PDF streams and is not a byte-for-byte UTF-8 substring of the original PDF. Submitting the raw PDF with a correct visible excerpt is therefore rejected. **Do not bypass this check or replace the original PDF digest with a transcript digest.**

`v171_pdf_research_evidence.py` deliberately separates (1) publisher **raw PDF SHA-256 and size**, (2) explicitly derived text SHA-256, (3) excerpt SHA-256, (4) V167-compatible research-only `body` holding the **derived transcript bytes** with an unmistakable `DERIVED_PDF_TEXT_NOT_ISSUER_RAW_BYTES` label, and (5) a private sidecar digest to detect substitutions. It independently verifies neither retrieval origin nor PDF-to-text fidelity. E4 must re-fetch authentic original PDF bytes, test source and applicability, and independently compare the extraction. This is **not** an original-byte E4 verifier.

## Private owner SRT and historical publisher-original audit performed in current chat

- V162 original source: video ID `5NvtBlmt93Y`, 1,481 cues; SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`.
- V162/V164 original B0002: C00017/C00018/C00019/C00021 source-ref exact cue quotes, atom SHA, old V123 review SHA and OPEN status rechecked **4/4**. C00018 remains subjective FACT misclassification needing reatomization.
- V164 archived Wiley Chapter 1 publisher PDF: raw-body SHA-256 `870be11899036a19351d1ce8644f833748e9b9618d67233d6a0c162144397024`; matches original TLS capture receipt. Page 1 contains the historical book attributions for **C00019 and C00021**. Those 2 publisher-derived evidence sidecars were generated and verified against locally preserved PDF and `pdftotext` output. Text-extraction *independence* is NOT certified, and a historical source's statements cannot prove current demographics or investment performance.
- Private-only output (not committed to repository): `V171_REAL_B0002_OWNER_PUBLISHER_SOURCE_PINNED_NOT_APPROVED.json`. Owner SRT, excerpts in review notes and PDF body are **not uploaded**.
- These are **historical V162 + V164 inputs, not a current V166 source snapshot**. Native V166 counted 193 OPEN and 13/13 HOLD; NO V166 OPEN count reduction is claimed. The audit has not yet replayed V169 private journal or native V123 for these four claims.

## Test boundaries and next gating actions

- New synthetic regression tests exercise no-response, stale original/revisit heads, same-evidence replay, raw-evidence swaps, fake approval, missing PDF excerpts, raw PDF substitution and source-versus-derived digests. Existing V167–V170 and native V166 tests also run.
- Native E4 still **FAIL** on the complete video; E5/E6/E7 **NOT_RUN**. A real 13/13 positive V123/E4 cannot be inferred from synthetic tests or 4/4 semantic note pinning.
- Highest priority: load the exact current V166 full typed original docket; execute current-chat decisions through the actual V169/V170 private SQLite and V171 adapter; independently re-check current authoritative primary financial/legal evidence; run real native V123 + E4 across 13 segments; release E5 only if all pass. This draft PR does none of those automatically.