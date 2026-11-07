# IRE V5 — #1 Incremental Research Audit (2026-11-04)

**Verdict:** original 67/67 source windows remain sealed; first-pass risk screening 182/182 performed; financial verification **125 OPEN**; independent financial truth approval **0**; advisory release **NO-GO**.

## Original source preservation
Video sz5N9WJS310, 1195 cues SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`, 81 existing provisional claims, original 11 chain receipts unchanged (head `d05ef6c38c9bda57e00bf10997cbb8c1cc93b0cf3f5f50fa75d0f825b8a80660`).

## New incremental risk audit
48 forced *end-of-window* boundary flags; 100 numeric nonclaim cues; 21 official applicability reviews; 13 prior-knowledge conflict candidates = **182 risk cases**. 3 new independent hash-chained incremental receipts head `c26adc8bb1c362d647f5d654973a3a17c6eb8b58934bddff03983c8439c9c4d9`.

First-pass source-anchored review dispositions:
- Potential fragment of existing claim: 43
- Boundary continuity preliminarily reviewed: 13
- Nonfinancial numeric index: 1
- **Still OPEN:** cross-boundary conditions 35; personal scenarios 48; ambiguous numeric ASR 8; official claim-specific scope 19; unmatched official candidates 2; prior conflicts 13. **Total OPEN: 125**.

Seven tool-returned official *candidate* snippets registered, 19 claim-specific reuse links. Several snapshots contain assistant-composed explanation mixed with excerpts. They are **not** authenticated full HTTP bodies, not legal effective-date judgments, and not independently approved facts. Reusing one document never carries the legal/fiscal claim's applicability verdict across people or dates.

## Implementation and recovery
`ire/v5/incremental.py` preserves sealed original and appends case-level risk-review receipts. `ire/v5/incremental_backup.py` combines private original source, original event receipts, and incremental receipts into encrypted AES-256-GCM archive. Cloud upload to private Google Drive, authenticated download, byte SHA256 equality, separate-directory decryption and replay **passed** for 11 original + 3 incremental receipts with 182 cases and 125 unresolved. Private backup SHA256 `38de5e09546ba849a2fd84c6dc97b061339f76cf963063799599db234bf9848b`, stored at https://drive.google.com/file/d/1e5UyCUqTfMhOhCOokDkKmgdmUjh84Bbr/view?usp=drivesdk . Offline recovery secret remains private, never committed.

Local tests: 86 tests = 83 pass, 3 skip private fixture; app tests 32 pass. GitHub cleanroom initially failed from a mismatched imported issuer-domain validator name; fixed in commit `d638b64c5e713c4296444739e2d99f1b4f218eb9`, CI run **41687992225 SUCCESS**.

GitHub control state `ire/v5_app/audit_states/v5-video-001-full67-20261104.json` reports risk screening counts and explicit NO_GO only when public request has been processed; public metadata must not imply independent source/financial attestation. Private SRT and source text stay outside GitHub. Existing main and V3/V4 remain unchanged.

## Required next step
Do **not** repeat original 67-window semantic pass. Investigate 125 substantive OPEN risks by issue class, with independent source check, effective date and individual applicability; measure blind semantic recall. Only after these close (or have properly evidence-backed bounded OPEN dispositions) can one-video research completion be considered. Never count OPEN as financial truth approval. Four-to-five full video one-user-turn goal remains **NOT DEMONSTRATED**.
