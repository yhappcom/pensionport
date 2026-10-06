# Run Events

Append-only execution ledger for **every scheduled or manual writer run**.

- Each writer run creates one unique `state/run_events/<timestamp>_<run_id>.json`.
- Successful runs are recorded too; this directory is not failure-only.
- `state/progress.json` is the latest canonical snapshot/summary, not the execution-history ledger.
- `state/run-heartbeat.json` is legacy fallback only and must not be used to decide the latest state.
- Canonical video state is derived from `data/videos.jsonl` base plus non-duplicated `data/canonical_events/` overlay.
- Before writing, a run must acquire `state/execution_lock.json`; only the active unexpired lease holder may write canonical state.
