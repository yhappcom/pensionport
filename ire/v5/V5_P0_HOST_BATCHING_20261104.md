# V5 one-request host batching (2026-11-04)

The authenticated private V5 loopback application now offers
`GET /v1/next-bundle`: up to eight unprocessed source-locked windows from
the current run, with its immutable head, current task hash and a declaration
that actual ChatGPT interpretation is still required.

`POST /v1/receipt` additionally accepts `BATCH_ACCEPT` when there is an
active model/evidence/relation/correction task, with the same optimistic head
and task hash conditions used by single events. `ResearchRun.append`
validates every nested model/review/correction action before committing
one event. Replaying the event always uses the normal validation rules.

This reduces application request/response overhead, and enables several
real user-authored ChatGPT analyses to be submitted in a single receipt.
It does not synthesize model output or claim that 8 packets were processed
merely because they were served. Official verification and prior research
relations remain required before closing any research scope.

The no-external-model-API restriction remains. This is a concrete throughput
improvement, not proof of unattended ChatGPT operation, all-video closure,
semantic recall or approved investment advice. Keep source packets and
credentials off public GitHub.
