# IRE Single-invocation orchestrator: execution verification

Date: 2026-11-01
Disposition: ENGINE_INTEGRATION_PASSED; FINANCIAL_RESEARCH_BLOCKED.

## Integration

One command runs original source validation, discourse context construction,
financial semantic model inference when configured, source-linked annotation
validation, independent official-domain URL discovery, quantitative worklist,
new-source relationship retrieval, independent review gate, and private final
audit report. Each unfulfilled step is explicitly marked BLOCKED or SKIPPED.

Successful model response windows are validated against exact original cue
quotes BEFORE private checkpoint storage. Transient failures may retry with
model/prompt/source-bound cached windows. Incorrect or absent original files
produce per-video failure reports while the remainder of the batch continues.

Official web results are candidate URLs only, not verified law or financial
facts. All proposed claims require evidence and separate review. Neither
historical research assertions nor historical conclusions are cited or loaded.

## Test results

- CI synthetic adversarial unit/integration suite: 38 passing.
- Independently executed same suite: 38 passing.
- Real original source batch (one command, source-only): 5 videos, 3,600 cues,
  364 discourse windows, 5/5 source provenance passing, 5/5 audit reports
  created under private storage with mode 0600.
- Development source counts:
  - #266: 771 cues, 78 context windows
  - #267: 522 cues, 54 context windows
  - #269: 988 cues, 99 context windows
  - #270: 1,036 cues, 104 context windows
  - #271: 283 cues, 29 context windows
- Missing model configuration: all 5 runs returned BLOCKED
  (SEMANTIC_MODEL_NOT_CONFIGURED), CLI exit code 2.
- Model name specified but without available API key: one additional
  real-source run produced BLOCKED (SEMANTIC_API_KEY_UNAVAILABLE),
  a private audit report, and CLI exit code 2.
- Initial private-file-in-code-root test was denied; placing private
  originals outside the repository boundary corrected it.

## Quality limitations

The current environment cannot perform a live language-model API invocation
because no OPENAI_API_KEY is configured. No source-derived financial atomic
claim recall/precision can be measured. Official facts are not independently
approved by domain-filtered URL candidates. No independent human-blind gold
judgments, official full-document effect-date verification, or verified claim
merges were completed.

Approved financial claims = 0. Auto knowledge merges = 0. Release BLOCKED.
