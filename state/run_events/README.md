# Run Events

Append-only heartbeat/run ledger used when scheduled existing-file updates are blocked.

Each run creates a unique JSON file. The newest event is run-tracking evidence only; canonical video state is derived from base aggregates plus `data/canonical_events/`.
