# V182 — cross-chat owner checkpoint, source-only OPEN review, E2 native semantic loss

Date: 2026-11-20 KST. Research status: **SOURCE_FIRST_HOLD / V123-E4=0 / E5=0**.

## Live V181 private restart evidence
- Independently restored private V181 ZIP SHA-256 `318eb1a3c8716473f7241e2034dd68a1e6dcfe14866b4252f1a71fd141326b3f`.
- Verified 10/10 archive members against the embedded manifest, SQLite `integrity_check=ok`, and owner SRT exact byte pin `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- Recovered V176 checkpoint head `15133c381b9e3ad3989340b932d5e87862bcd3c4e75d5374b164f52f55a021e5`, existing 20 events, 250/250 source cues, 69 provisional claims and 25 OPEN using the new conversation's independent process. CLI `--resume-head` and `--resume-reviewed` match. The previous owner journal was not reset.
- Original ZIP and all private scripts/SQLite stay outside GitHub.

## Eight contextual OPEN dispositions (not audio correction)
- The active ChatGPT reader rechecked original text and adjacent cues and appended three source-grounded V176 context-revision events for 8 initially OPEN cues:
  `124,125,199,200,201,202,203,248` → **NON_RESEARCH**.
- These were transition text, clauses of an existing opinion, a rhetorical analogy and a closing greeting, **not stand-alone financial facts**. No audio-only transcription error, percentage or money unit was silently corrected; the 197 financial comparison opinion remains provisional.
- Original OPEN records remain immutable in `cue_reviews`; effective revisions are appended to `cue_revisions` and `events`.
- New private journal head: `ccd789a0fc6259e600d434381f8b5064a1e6b137256968d7b061192896a9b138`.
- Effective OPEN 25→17; 69 provisional V6 atoms unchanged; native `suspicious_no_atom_cues` 52→53 because revised nonresearch classifications remain open to lexical omission inspection. Total events 23; revision rows 14; V123 E4 approval remains 0.

## Critical E2 defect: frozen-stage qualifier text loss
- V176 private claim records contain **69 conditions and 69 exceptions across the 69 staged candidates**.
- Before V182: all frozen V6 candidates exported with `condition_cue_indices=[]` and `exception_cue_indices=[]`, plus `stance=UNRESOLVED`, `speaker=UNKNOWN`. A successful V6 structural audit therefore **does not mean context/qualifier preservation**.
- V182 adds a native-stage `semantic_projection_gate` with a hash-only, per-claim repair manifest and counts of unprojected qualifiers and unresolved semantic role labels. The new field **fails closed**: `full_semantic_projection_verified=false` and `v123_e4_approval_permitted=false`. It does not invent source cue anchors or alter the frozen V6 schema. Free-text conditions/exceptions remain recoverable from the private original journal.
- This is a **diagnostic and admission-blocking improvement**, not a full semantic-mapping solution. Future reviewers must add verified source cue anchors and a separate mapped speaker/stance review before any E4 submission.

## Remaining 17 OPEN by owner-SRT evidence type
- Audio/ASR unresolved: 19,23,52,133,149,150,153,160,171 (9).
- Video graphics/screen missing: 163,166,230,232,233 (5).
- Historical ETF-count evidence/as-of missing: 8 (1).
- Factual overgeneralization and source scope: 123,126 (2).
- Do not fill audio/screen-specific gaps using the surrounding SRT or a general KRX explainer.

## Test/approval status
- Synthetic fixture tests verify semantic loss detection, private restart consistency, and no-approval property. They do not constitute a ChatGPT-independent gold set or financial approval.
- `main` and user data remain untouched; PR remains draft. E5 publication remains 0.
