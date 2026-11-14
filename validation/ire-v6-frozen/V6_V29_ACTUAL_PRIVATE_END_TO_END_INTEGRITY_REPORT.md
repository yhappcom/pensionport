# V29 — Actual owner-original pinned replay through real V5 P3 (3 questions), source-ellipsis fix and hash-only chain

**Date:** 2026-11-10 Asia/Seoul. **Scope:** Draft PR #53 / validation branch, no merge, no edits to original V5/V6 historical modules, protected 116 or P4 29. This is NOT independent gold or investment approval.

## Concrete primary-source evidence and implementation

* Original owner Library ZIP `1-70.zip`, bytes SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`. Exact private member `1-70/youtube-transcript-8Zh1q4Ziv4c.srt`, **2,643 bytes**, raw SHA-256 `cbb57d372bc0fb5965052a776b5b945a5b82df3178d5c40dcd30cdcc8b0d8239`, exactly **34 cues**. Pre-pinned expected values verified with actual `ire.v6.private_original_pin_v28.verify_private_original_archive`.
* Full-video source-plan SHA-256 `b9eaf0c528f159ec62159fa6e509f27628bfc4f3dc4c194ef639f22d7ae74aaf`; actual V6 `source_cue_census_sha256` `b43fe8ef0c82cac7c608aa58a6740466e9b0ca097ff72b063ccbb6b64b941ea2`; 16 **same-chat candidate** claims audited by *actual imported* V6 source and atomic-exchange code. No unresolved or flagged financial NO_ATOM cues; one intro-only cue, 33 linked.
* Recovered source tree via read-only short-lived GitHub Actions code-only artifact from intermediate HEAD `21b421d2229d73414b44d992159b47109957f7bf`, code archive ZIP SHA-256 `7bff54a451af61dff05a35478bdd2b5631b579e88c49d23cf1e4b11d23ddf66f`. There were no tracked owner SRT/ZIP files in this artifact, and **no owner original was sent to GitHub**. The temporary artifact workflow is deleted in the final V29 tree because its presence changes the historical canonical file count. Core 11 Python module file **git blob hashes** were matched against GitHub including original V5 P3, V22..V28 and new V29 code. The complete dependency tree was not independently signed.

## Actual non-mocked end-to-end results — THREE real source-bound question paths

Execute `evaluate_private_original_v29` from the actual local source, with original ZIP in private local storage and exact 11 code-blob pins. It calls V28 original verification, V29 source-ellipsis guard, V27/V26/V25/V24/V23/V22 and the **real V5 `advisory_answer_pipeline.answer`**, not a mocked P3. For each answer record source, question, candidate census, regulatory evidence and same-chat review hashes; never store the original SRT or answer text publicly.

| Source question facet | Selected claims | V5 P3 executed | V29 receipt SHA256 | Final answer SHA256 |
|---|---|---|---|---|
| IRP statutory early withdrawal | C00012, C00013 | true | `ce7bcf01cabfb5c8fcd4e6c8b8da19da5f75c5a7a6d6deb45e1d7f18b6825c7a` | `1bf3bc09d3207be7a36b060a7a5db0d8688468fe43149a3c79b58bf5b47e9364` |
| Ordinary-account ETF capital gain taxation | C00005 | true | `5572c4c9ba410b5cc57d32d9955f03051be0e861383ef461b12bbf5a35f562f9` | `9e75bc50440ea99d8e4ae25bea8927aba6bffbd6d360351c471715910bacfece` |
| Pension savings non-credit basis withdrawals | C00009, C00015 | true | `1dc49fd0636efefac93603b8b7662bc4a931c319da898029a7708b717c4834b3` | `e29aacc237212b9ee452f75c996944fd1e82c95a57311f442f34ff3325bdd0db` |

Private local full hash-only 3-case bundle SHA-256 `b6278a8859df9a3e5049a21df644af646411ba8100e45bf86f327d36ef3c3f94`. Public GitHub hash-only index `validation/ire-v6-frozen/V6_V29_REAL_PRIVATE_REPLAY_HASH_ONLY_RECEIPTS.json` contains no SRT, excerpts, questions or answer bodies. The pension-basis case required correcting *the private same-chat candidate frame* (C00015 account-name ellipsis and context cues); unchanged actual source quotes remained byte-bound. The independent correctness of this contextual interpretation is **not proven**.

## Discovered and closed omission path

The previous V27 `_facet` considers literal subject names in the atom proposition. Original subtitle ASR fragments split a pension account name across successive cues and the later claim elides that account name. Old V27 accepted the relevant C00015 as `REVIEWED_OFF_TOPIC` when C00009 alone was selected in a pension-excluded-basis question. This is a genuine **false negative in the prior guard**.

New additive `ire/v6/private_replay_receipt_v29.py` blocks unselected excluded-basis withdrawal candidates whose nearby original cue string (whitespace-normalized, bounded predecessor context) establishes pension-savings context. It does not silently rewrite text or automatically approve; the host must explicitly repair candidate scope and selection. Also matches Git blob source bytes for configured V5/V6 core files and emits a hash-only chain receipt.

**Five actual local negative controls rejected:** (1) omitted same-question-context pension claim, (2) wrong SRT SHA, (3) wrong ZIP SHA, (4) missing candidate census row, (5) altered V5 source Git blob pin. Thirteen additional synthetic V29 unit cases cover the same omission and pinning invariants.

## Current official-rule references / limitations

* IRP: [Enforcement Decree of the Employee Retirement Benefit Security Act, Art. 18](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1032589237), in force 2026-03-24, provides statutory conditional early-withdrawal exceptions.
* ETF: [KRX ETF tax scheme](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp) distinguishes Korean equity ETF gains from other ETF types.
* Pension non-credit basis: [Enforcement Decree of Income Tax Act, Art. 40-3](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1029964673), in force 2026-10-01, specifies exclusion and withdrawal order.

These official pages were checked through the **current ChatGPT web tool**, and rule excerpt strings and applicability classifications passed into the deterministic engine in this chat. **Publisher-signed raw legal document bodies were NOT verified**, and the host judgments were not adjudicated by independent experts. None of the three runs proved all original atomic propositions captured, individual tax eligibility, or advice usefulness.

## P0 integrity resolution verdict

* **P0-1** original ZIP and SRT bytes: actual PASS.
* **P0-2** all 34 original cues assigned: actual structural PASS.
* **P0-3** 16 original-linked candidate frame/quotes/number tokens: actual structural PASS, **semantic precision/recall NOT certified**.
* **P0-4** original -> V28 -> V29 -> V27 -> V26 -> V25 -> V24 -> real V5 P3: **three real question paths PASS**, no mocked P3. This is not universal scenario coverage.
* **P0-5** three official public references plus current-effectivity checks: **same-chat official context PASS**, independent publisher legal body authentication / individualized applicability OPEN.
* **P0-6** hash chain receipt: **three actual receipt hashes generated**, complete-repository attestation / external independent signing OPEN.

**Software CI** is a distinct synthetic/legacy gate; verify FINAL exact commit SHA, unique V6 test count **404** (previous 391 plus 13), original IRE 310/V5 855/V5 application 59, SHA manifests, and cleanroom before claiming PASS. PR remains Draft, P0 researcher-quality **NO-GO**, original 791-run blocked pending independent gold precision/recall and generalization.
