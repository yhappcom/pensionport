# Inventory event ledger

This directory stores append-only baseline inventory discoveries for the fixed 2026-10-06 channel snapshot.

Rules:
- One immutable event per exact YouTube Video ID: `<video_id>.json`.
- Event creation does not require the mutable single-writer lease because each Video ID has its own deterministic path.
- Before create, check both the compacted snapshot and this directory for the same Video ID.
- If the file already exists, treat the desired state as already applied.
- Mutable aggregate compaction into `data/channel_snapshot_2026-10-06.jsonl`, queue/meta/progress files still follows the single-writer lease.
- Effective baseline inventory = compacted snapshot + unique inventory events not already present in the snapshot.
- A failed aggregate compaction must not discard or repeat a successfully created inventory event.
