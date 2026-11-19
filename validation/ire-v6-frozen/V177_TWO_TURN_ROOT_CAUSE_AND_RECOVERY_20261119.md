# V177 — Two-turn test diagnosis: preserve actual V176 720-cue research before continuing

Date: 2026-11-19. Target `verify/ire-v6-v176-engine-driven-chat-e4-20261119` draft branch. No change to `main`, frozen V6/V123/V126/V128 or E4 approval code.

## Confirmed root cause

V170/V171's `PreparedChatTurn` objects are in-memory and cannot independently survive an ordinary two-turn conversation. But the **current and more advanced** V176 engine already stores actual ChatGPT cue decisions in a SQLite private journal. Its GitHub PR #65 reports 720/1,481 real SRT cues (41 events, head `2e881a6a5d5b0c851fa198ae7b880665a0ed1d7c93166e3c7873c9c75f3dc494`), remaining 761, next challenge 721–740. 129 atom candidates, 99 questions, 407 context/no-atom, 85 OPEN. No V123/E4 approval. These cannot be regenerated from GitHub's source-safe hash-only progress file.

The actual **cross-turn failure** is that the next turn needs (a) the same owner-original SRT bytes, (b) the exact prior SQLite journal and its chain, (c) the original source/manifest and checkpoint head, (d) the engine-issued next challenge, and (e) a *new current-chat authored answer*. GitHub only stores public code/hash-only counts. A new container/session cannot assume its private workspace preserves the prior 720 decisions. V176 `EngineChatSession` **auto-creates a new empty journal if path is absent**; blindly restarting risks reporting a new zero-progress session as the old one. The v176 CLI supports external challenge JSON, but does not enforce a portable, independently checked checkpoint.

## V177 change

`v177_private_turn_checkpoint.py`: source-verified SQLite backup into a PRIVATE *unencrypted* ZIP (original SRT, SQLite snapshot, next challenge, SHA-pinned manifest). Every export/restore requires the **externally recorded** source SHA, old journal head, and previously reviewed count. Existing SQLite must exist and have mode 0600; no auto-create or overwrite. Restore into a new 0700 directory; audit original native V176 chain, source-cue census, cue count and next challenge by deterministic reissue. Archive is not uploaded to GitHub. No actual model inference is performed by Python and no final approval is claimed.

User-private checkpoint commands for the **existing 720-cue owner journal only if the actual private state is available**:

```bash
python validation/ire-v6-frozen/v177_private_turn_checkpoint.py export \
  --srt /private/original.srt --db /private/owner.sqlite \
  --sha 638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d \
  --video-id 5NvtBlmt93Y \
  --head 2e881a6a5d5b0c851fa198ae7b880665a0ed1d7c93166e3c7873c9c75f3dc494 \
  --reviewed 720 --zip /private/next_turn_v176_720_PRIVATE.zip
python validation/ire-v6-frozen/v177_private_turn_checkpoint.py restore \
  --zip /private/next_turn_v176_720_PRIVATE.zip --out-dir /private/restored_v176 \
  --sha 638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d \
  --video-id 5NvtBlmt93Y \
  --head 2e881a6a5d5b0c851fa198ae7b880665a0ed1d7c93166e3c7873c9c75f3dc494 \
  --reviewed 720
```

Then ChatGPT reads the restored **private** `next_challenge.json` and authors an answer; native `v176_chat_engine_cli.py ... commit` writes that exact answer to the restored SQLite journal. **Nothing can auto-generate or approve an answer.** In a new engine process, `progress` must show 740/1,481 and a new journal head only *after* a real ChatGPT verdict. If the original 720-review ZIP is missing, fail closed and preserve the GitHub 720-count historical report; do not fabricate the old 41 events.

## Verification scope

New tests use **synthetic captions only**, including a truly separate Python interpreter process: first-pass 3 reviewed → export private checkpoint → new process restore → explicit synthetic answer → 5 reviewed; missing DB, wrong head, wrong count, forged source, corrupted SQLite, unsafe file mode, archive member tamper/traversal, no overwrite, and e4/e5 fail-closed. Existing V176 tests are also run. This is a **transport/persistence proof**, not two separate real ChatGPT model turns, and not a new measurement of 720 owner cues.

Remaining: actual V176 private 720-cue journal inaccessible in current working container; cannot certify a real 720 → 740 continuation until it is supplied or recovered. Latest real meaning-first progress remains 720; V123/E4 0/13 certified, E5 0. No external LLM API used.