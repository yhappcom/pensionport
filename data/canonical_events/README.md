# Canonical Events

This directory is an append-only canonical ledger for scheduled runs.

Rules:
- Each canonicalized video gets one immutable file: `NNN_<video_id>.json`.
- A canonical event is written with `create_file` before aggregate compaction.
- Effective canonical state = compacted base files + event files whose `video_id` is not yet present in the base aggregate.
- If aggregate `update_file` calls are blocked, the event remains canonical and later runs continue from the overlay state.
- Duplicate sequence/video_id events are prohibited.
- When base aggregates are later compacted, the immutable event remains as audit evidence and is ignored for double-counting because the base already contains the same video_id.
- Heartbeats use unique files under `state/run_events/` when existing-file heartbeat updates are blocked.
