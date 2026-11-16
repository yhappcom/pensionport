# V28 — Correct private-original SRT provenance and add executable pinned ZIP replay gate

As-of: 2026-11-10 KST. Branch: `verify/ire-v6-p1-atomic-host-batch-20261109`. Draft PR #53, no merge or modifications to protected main/V5/116/P4.

## Critical finding from re-opening original owner Library archive

The private source archive `1-70.zip` SHA256 is `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`, and its ZIP member `1-70/youtube-transcript-8Zh1q4Ziv4c.srt` consists of exactly **34 cues**, 2,643 original bytes. Direct SHA-256 computation on the **actual SRT bytes** yields:

`cbb57d372bc0fb5965052a776b5b945a5b82df3178d5c40dcd30cdcc8b0d8239` (64 hex digits)

The V27 report and V27 manifest instead recorded
`cbb57d372bc0fb5965052a776b5b945a5b82df3178d5c40dcdcc8b0d8239` (**60 digits**). Existing V27 CI only compared that erroneous literal with itself; it did not run a private-original byte replay. This invalidates the V27 **raw-SRT provenance claim**, NOT the previously observed 376 synthetic/unit tests passing. The V27 historical manifest is preserved unchanged for traceability; this V28 override pins the corrected source digest and names the defective historical field.

## Additive correction

- New `ire/v6/private_original_pin_v28.py` verifies an exact **precommitted**, 64-digit ZIP SHA and SRT SHA against actual local bytes, ensures the uncompressed SRT member is unique and safe, rejects AppleDouble/traversal/symlinks/duplicates and wrong video ID, invokes the real V6 SRT parser and asserts the expected cue count.
- Optionally accepts a full-video source plan with an **independently pinned** plan digest, then calls the real V6 `verify_source` and `audit_host_atomic_exchange` on the same real original to validate cue/claim structure. No private subtitle text is returned.
- `evaluate_private_original_v27` is a **fully wired opt-in integration adapter**: if the local original, complete exchange, current official evidence, and all exact-hash chat-review receipts are present, it calls the actual V27/V26/V25/V5 P3 path. No fabricated defaults, no automatic P0 release and no personalized tax refund/order authorization.
- The private-only repository-independent analysis of this source previously mapped 16 developmental atom candidates across 33/34 original cues (one intro/no financial atom); these are NOT independent human gold and NOT a successful execution of the repository's full V27/V5 path.

## Reproduction status in the current chat

- **PRIVATE BYTE-LEVEL VERIFICATION PERFORMED** on the owner ZIP and 34-cue SRT in ChatGPT's local sandbox, with corrected SHA above. Raw content remains private.
- Synthetic V28 tests cover invalid 60-digit hash, archive/SRT tampering, repacking, cue-count mismatch, member traversal/AppleDouble, duplicate member, plan pin, actual V6 parser+atomic-exchange structure (synthetic), quote forgery, and no false release flags.
- The new private full end-to-end runner is CODED but a real original **V27/V5 full Python execution with 16 actual source claims and official current-law decisions has NOT been proven** in the current environment. Connecting production code to private raw source requires a full local repository runtime and independently reviewed exchange/legal evidence. Do not substitute the synthetic GitHub CI for this missing execution.
- No uploaded private archive, private raw subtitle or verbatim cue quote is placed in public GitHub.
- No independent semantic precision, recall or suitability evidence; **P0 NO-GO** and 791-video rollout blocked.

## Test and governance

New 15 synthetic tests; expected unique V6 test count **391** (prior V27 376 +15). Final exact commit GitHub Actions and separate cleanroom status must be checked before reporting PASS. Historical V27 source hash field is retained as an explicit documented error; V28 SHA must be checked as a 64-hex **actual-source pin** rather than trusting a string comparison of the old field.

**Next substantive requirement:** execute the new private adapter against the actual original with a fully reviewed 34-cue/16-candidate source exchange, current rule excerpts and a complete V5 installation. Track any source risk/facet failures; only separate blinded external labels can establish true semantic precision/recall.
