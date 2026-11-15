# V123.6 — Actual V122 47-cue V6 host_batch in isolated private staging, ChatGPT final HOLD (NOT OWNER PRODUCTION GO)

**2026-11-15 KST** · Protected `main`, Master116, P4, V5 unchanged · No non-public original text, private reviews, original government response bytes or personal data in this report.

## Executed, not inferred
1. GitHub [public-only offline V6 source bundle](https://github.com/yhappcom/pensionport/actions/runs/43677931512) was constructed from the exact public engine commit `7793abaf37ad07e47b1052661dfa69b353d2b166`, with the 116+29 immutable prior data, and its internal tar SHA-256 validated locally. No owner SRT/ZIP was uploaded to GitHub or GitHub Actions.
2. Owner's previously retained private V122 ZIP (original SRT SHA `189c99885ebb87988781d5eb8e608ece0f2ae2ac57199155ddb498e2c15bf8cb`) was independently parsed and SHA verified against previously public-committed V122; 47 cues, W00001 cues 1–47. Private inputs were prepared as 17 source-grounded **provisional** atomic candidate proposals, including prior unmatched R003/R017, with full cue dispositions and numeric-token coverage. Existing R016 duplicate is not separately asserted. The 17 references are the already-exposed same-chat A/B guide, **not independent gold or assured exhaustiveness**.
3. A separately committed [operator-derived inventory hash](V123_6_OPERATOR_SOURCE_ANCHOR_SHA_ONLY.json), not a pre-existing independently signed owner inventory, was checked by native `verify_owner_inventory`. Native `audit_host_atomic_exchange`, `audit_model_anchors`, and `audit_prior_candidates` ran with the actual raw SRT/116+29 prior records and succeeded structurally.
4. Native `TransactionStore` in a new **local private staging database**, not any prior owner operational DB, executed `create_scope` → `attest_source` → `attest_owner_inventory` → `submit_host_atomic_batch`. The actual non-synthetic one-window model and structural proof **committed atomically**: event HEAD `d6b1d86ffa776709c4b0100facdcd8275b60352285cbdc57cbda6cfa40296091`, sequence 6, model/proof 1/1, `atomic_batch_committed=true`, `is_current=true`. Re-open/read-back and exact same-input replay confirmed HEAD equality and idempotency. SQLite backup `PRAGMA integrity_check=ok`. Source bytes were never public.
5. Native V123 `assess_chat_final_gate` ran against this actual staged store with a private ChatGPT review tied to all 47 cues and 17 atoms. Result: **`CHAT_FINAL_HOLD_OPEN`**, accepted 0/open 17, finance-sensitive OPEN 17 under the conservative V123 classifier, high-risk OPEN 9, no evidence bodies, unresolved original audio/video. Previous narrower financial docket **OPEN 12 remains** (not changed/closed). Both `require_chat_final_release` and the supported `preview_chat_validated_candidates` raise `QualityNotProven`.
6. Original private store snapshot + full private review, candidate inputs, and member hashes are preserved **only in user's private Library** in `V123_6_V122_REAL_NATIVE_V6_SQLITE_AND_CHAT_HOLD_PRIVATE.zip`. Public [SHA-only receipt](V123_6_V122_REAL_NATIVE_V6_SHA_ONLY_RESULT.json) pins its SHA; the archive is not uploaded to GitHub.

## New source-first review debt
- `source_first_semantic_frontier` emitted **31 review cases**, including 17 stance/speaker uncertainty markers, 13 financial law effective-date/scope unknown cases, and one multi-number cue; these are review queue flags, not proven errors.
- `audit_semantic_risks` flagged condition cue **32** in provisional atom `C00011` as `UNMAPPED_CONDITION_IN_MODEL_CONTEXT`. This is a real mapping improvement item; the currently stored provisional candidate is not represented as final semantic completeness. Cue **14** contains more than one number but is linked to one provisional claim, requiring a conscious range-vs-independent-atom assessment.
- Original audio/video pronunciation and account/product eligibility are unconfirmed. No conservative OPEN or rejection was silently closed.

## Financial source checks (readable official webpages only; NOT primary HTTP bytes)
- ISA statutory exemptions and separated taxation: [Tax Incentives Restriction Act art. 91-18 (effective 2026-09-18)](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1033258307).
- Additional pension account credit base and limits: [NTS pension income](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6449).
- ISA-to-pension actual payment within **60 days** rather than mere application: [NTS pension income, contributions](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6605).
- Tax-excluded funds source order: [Income Tax Act Enforcement Decree art. 40-3 (effective 2026-10-01)](https://law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1016308725).

**Evidence limit:** The official pages were searched/parsed as rendered text, not replayed from independently retained first-party original HTTP response bytes with capture provenance and effective-date/product-scope adjudication. No primary-body SHA or final financial fact approvals are claimed. Unverified securities promotions remain OPEN.

## Release and authority boundaries

| Question | Observed result |
| --- | --- |
| Did actual original SRT pass native V6 source/model/proof and local isolated ACID host_batch? | **YES (staging only)** |
| Was operator inventory derived from owner-held SRT rather than independently owner-signed? | **YES (independence limitation)** |
| Does this prove pre-existing owner production DB HEAD or replace it? | **NO** |
| Did native V123 ChatGPT final gate actually execute on staged store? | **YES: CHAT_FINAL_HOLD_OPEN** |
| Is the owner-production final approval therefore PASS? | **NO, original signed inventory / production store not independently verified** |
| New knowledge preview, finance fact approval, Master116/P4/V5 advice, P0 GO? | **0 / NO / NO-GO** |

The old `HOLD_MISSING_V6_HOST_BATCH_OR_STORE` *readiness inference* still applies to an **existing owner operational DB**, but is no longer an accurate description of what was exercised in isolated staging. This new concrete staging gate returned `CHAT_FINAL_HOLD_OPEN`. Do not conflate their provenance.

The next high-value work is: privately correct cue-32 conditional mapping and check cue-14 number context; securely retain original official response bytes, effective-date and issuer/product scope for 12 priority cases; rerun a new-version staged batch and ChatGPT final review; maintain hold until all required OPENs are resolved.

## CI boundary repair in V123.6

A temporary public-only GitHub Actions source-export workflow was used to transfer the **public** frozen V6 engine into the private local runtime without uploading the private SRT. That added workflow path violated the existing canonical/clean-room allowed-diff policy; those intermediate GitHub CI runs failed **on repository scope enforcement**, not on the actual original-source host_batch. The temporary workflow was removed in commit `43129c4ebec6627f4c9943d6b836903a49bad1c0`, restoring a HEAD diff limited to V6 validation metadata and the already-approved V6 CI workflow. Keep the scope guard unchanged. Final CI is verified separately on the repaired HEAD, not by inheriting a previous green run.
