# IRE V5 application control plane — GitHub Actions + private research API

## What the user actually requested

GitHub is the **versioned application and public task-control plane**. It can execute event-triggered short jobs in **GitHub Actions**; it is not a 24/7 local server. ChatGPT in the current user conversation is the **research processor** responsible for reading exact private SRT cues, conducting live official web searches, interpreting financial scope, and authoring source-referenced conclusions. It can submit those outcomes to a **private local V5 app**; the Python code itself never calls a model or searches the web. Private encrypted checkpoints live outside the public Git repository, e.g. in private Google Drive.

## Two actual executable modes

**1. GitHub Actions application mode:** Push an allow-listed, privacy-safe numbered command to `ire/v5_app/requests/<job_id>/000001.json` (`OPEN`), then `000002.json` (`CHECKPOINT`). `.github/workflows/ire-v5-app-control.yml` runs the control worker, tests the app, and commits `ire/v5_app/states/<job_id>.json` back to the V5 development branch. ChatGPT reads this status via its GitHub connector. It **does not** mean GitHub produced the model response or verified the sealed private data.

```bash
python -m ire.v5_app.worker --requests ire/v5_app/requests --states ire/v5_app/states
cat ire/v5_app/states/v5-video-001-research.json
```

**2. Private local API mode:** Restore a user-authorized encrypted V5 archive to a mode-0700 private directory, supply an independent strong bearer token via env, and run:

```bash
export IRE_V5_APP_TOKEN='REPLACE_WITH_LONG_RANDOM_USER_HELD_TOKEN'
python -m ire.v5_app.server --store /private/verified_v5_run --port 8766
# GET /health (unauthenticated), GET /v1/state, GET /v1/next,
# POST /v1/receipt, POST /v1/seal (Bearer token required).
```

The server binds to `127.0.0.1` only. The ChatGPT host can use authorized local desktop/computer or Python tools to call it. The `/v1/next` request yields a source-locked cue packet; the host must perform genuine semantic analysis and official research. `/v1/receipt` accepts only the next event type with the exact expected task hash and event-chain head (optimistic concurrency). This is **not** a public webhook; never publish an auth token, original SRT, financial claims, encrypted archive recovery key or raw model answer to GitHub.

## The current #1 research job

- Video `sz5N9WJS310`, full manifest 1,195 original SRT cues / 81 windows.
- Prior 2026-11-03 private V5 checkpoint **reported** 3/81 analyzed, five provisional claims, 5 official research dispositions, five prior-claim relation reviews and 13 event receipts, next `W00004`. The public GitHub worker does **not** have the private archive so this status is an *unverified ChatGPT receipt digest*.
- Private archive: Google Drive is separately managed. The recorded archive digest does not let GitHub decrypt or validate original content; only the owner-held recovery secret and actual V5 replay can.
- `source_verified = false`, `facts_approved = false`, `advice_approved = false`, full-video P0 **NO-GO**.

## Critical limitations

GitHub Actions is not an always-on model runner. An Actions job cannot force a new ChatGPT response while the chat is inactive. A genuinely unattended 24/7 loop requires a deployed host or self-hosted runner **and** an authorized research invocation mechanism (contrary to the current prohibition on additional model APIs, arbitrary ChatGPT inference cannot be programmed inside Python). ChatGPT Work mode is suitable for cloud-browser research and multi-step UI handoffs, but does not itself guarantee 81 windows in a single turn. This architecture turns GitHub into an executable task manager with durable status, and keeps research correctness in the chat + authenticated private store.

### Acceptance evidence, not synthetic benchmarks

An app can only be called fully operational if: (1) a committed request actually triggers GitHub Actions, (2) status is committed and read back; (3) a current ChatGPT session can read `W00004`, verify official sources and submit source-locked private receipts; (4) encrypted private backup roundtrip succeeds; and (5) full 81-window independent research closes without hidden unprocessed windows. Until (5), **NO-GO**.
