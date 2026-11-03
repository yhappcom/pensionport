# IRE V5 sequential P0C → P0D → P0E execution report (2026-11-03)

## Decision
**P0C: PARTIAL REAL SOURCE PROOF. P0D: LOCAL ENCRYPTED RESTORE PASS / CLOUD NOT PROVEN. P0E: NO-GO.**

Unlike V4 proxy tests, V5 now **enforces a source capture checksum, exact quotation, issuer domain, date/scope review and prior Git source pin at acceptance** for opt-in new runs with `p0c_policy=STRICT_P0C_V1`. Legacy pilot event chains remain backward compatible. A search result is still not a separately attested official fact.

## Implementation (this branch)
- `ire/v5/p0c.py` validates captured UTF-8 markdown/HTML/text bytes supplied by the current ChatGPT host, exact quote containment, SHA-256, official HTTPS issuer-domain allowlist, retrieval timestamp, effective date and applicability notes. It never independently certifies that the host actually fetched a URL, and it rejects `financial_fact_approved=true`.
- `ire/v5/engine.py` invokes strict P0C validators for new evidence and relation events only when the locked source manifest opts into the new contract. Historical 3-window / 26-event pilot receipts are not rewritten.
- `ire/v5/tests/test_p0c.py` adds nine synthetic strict-contract defensive tests. Existing V5 core and encrypted transport tests remain included.
- GitHub Action **41611048166 PASS**, including existing clean-room rules and V5 tests. Secret real-source fixtures are absent from public CI, so the original-source test below was run locally and is not a CI semantic accuracy certification.

## Actual original-source P0C pilot
- Original #1 `sz5N9WJS310` original SRT SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`.
- Source 1,195 cues, V3 adaptive planner 81 windows, **new strict V5 scope W00018**, primary cues 256–262.
- ChatGPT independently interpreted two provisional propositions: (1) 5y pension deferral is described as 36% increase, and (2) a KRW300k/month to about KRW400k/month illustrative comparison, which must not be conflated with a certified personal pension amount.
- The host retrieved the NPS FAQ at `https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0100M0.do`. A **bounded, tool-returned text extract** was recorded with exact excerpt and SHA-256, **not the raw HTTP response**. Effective date, eligibility, survivorship and taxpayer scope remain OPEN.
- Existing old #1 claim `sz5N9WJS310-07` from Git blob SHA `5bd8c20cff81446fb5fe058f92953f6ce4457962` linked as candidate; not copied into new V5 truth.
- V5 accepted **1/81** planned source windows, **2** model-authored claims, **2** evidence dispositions, **2** legacy-relation dispositions, plus 1 closure = **6 immutable receipts**.
- Reopened an AES-256-GCM encrypted archive in a separate local store: exact source, manifest and event head matched. All approvals remain false.
- `scope_kind=PILOT_WINDOW_SCOPE`, `full_video_source_scope_sealed=false`, `p0_one_command_full_research_go=false`.
- Private source original, model answers, encrypted sealed archive and passphrase are NOT committed to Git.

## Tests and blockers
- **Local**: 35 tests executed, **32 PASS**, 3 prior private-pilot-fixture tests SKIP. The three skipped tests are not described as passed.
- **P0D** local store export/import PASS; **Google Drive encrypted upload + re-download + totally independent new-chat recovery not proven**. A portable backup alone does not establish durable cloud retention; a user-owned recovery secret/key policy is required.
- **P0E** full original #1 one-command 81-window research NOT PERFORMED: 80 remaining windows in this *new strict pilot*, no independent fact approvals, no exhaustive official scope or old-video relation review. Prior V4 81-window statement is not a V5 complete run.
- **Current host constraints**: Python cannot itself invoke an additional ChatGPT inference or tool search without a model API. ChatGPT controls the research loop in a single user command only as execution limits permit. No claim of unbounded host execution.
- **Future seal**: complete source analysis and every claim-specific source search + OPEN reason + legacy revision + cross-video relation; require immutable readback from persistent storage; keep fact verification and advisory-release grades distinct.

Status: **V5 P0C vertically demonstrated, V5 overall P0 NO-GO**. 


## 2026-11-03 follow-up — P0D actual cloud roundtrip and P0E full-scope progression

### P0D — CLOUD ROUNDTRIP VERIFIED FOR THE CURRENT HOST
The initial connector `upload_file` action rejected a plain local file pathname because it requires an authenticated connector file reference. We switched to **Files personal Library upload to its verified Google Drive folder**, and performed an actual upload → Google Drive API metadata readback → authenticated raw download → SHA-256 exact-byte comparison → **V5 `import_encrypted` → `reopen_private_store` replay**.

- Private research folder: `https://drive.google.com/drive/folders/18GCNmFIinrxInNvfFE9D6tHfggi2kYTh`.
- P0C W00018 encrypted archive Drive id `1A0tkRqnkM6MQpB6L2vz5xVaywahrsqHc`. Downloaded raw bytes SHA256 `42f104a10727441e83ac7d062b4f71ae44907939c081fecf49a74226a63f263a`, exactly matched upload. V5 decrypted/replayed **6 receipts**, source SHA `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`, event head `968a0746fe0cab589be0ec3ee49fb12dea298ea446d68c46e3b30a8bbd139d45`. P0C official text is **a manually transferred contiguous excerpt of a tool-returned NPS page's markdown**, not raw original HTTP bytes and not independently signed by the institution.
- Actual **P0E full-video-scope** frozen source ledger launched with **81/81 windows in the manifest**, original 1195 cues and exact SHA. ChatGPT read W00001–W00003 primary cues and authored actual source-linked dispositions and five provisional claims. W00002 was episode introduction and classified NONCLAIM; W00003 contained the unverified personal pension top-up scenario. No external LLM API used.
- Latest P0E V2 encrypted full-scope **IN-PROGRESS** archive Drive id `17of3h3oZ4Ihfme_zP23S_bbj38phOawp`. A second cloud upload→download→SHA match `9a5b4262740749118990a58fd049b0961eee79d5aee4b133a76b884b957183b8` and independent V5 process replay **passed**. It contains **3/81 analyzed source windows, 5 provisional claims, 5 evidence dispositions, 5 prior relation reviews, 13 immutable receipts; next task W00004**. Event head `37018c1d2358ee6c48aeb4d98b27053591b3b270b996f9c679bae424241bffa3`. The new V5 run is **NOT sealed**; 78 windows genuinely remain unprocessed, separate from OPEN factual obligations.
- No unencrypted originals, claim contents, archive secrets, or private raw data were uploaded to GitHub.
- The cloud archive is encrypted using a **random recovery secret present only in the current private runtime**. A user-held off-platform key escrow or user-chosen passphrase is necessary to guarantee recovery in a future entirely separate chat. **Never equate same-host independent-process readback with independently demonstrated future-chat recovery.**

### P0C factual caution
For W00003 the NPS public FAQ confirms a general maximum **119 months** and personal eligibility rules. The episode's user's **KRW18m hypothetical top-up and estimated +KRW250k/month** were kept `OPEN_PERSONAL_DATA`; no personal pension amount was verified. W00018's 5-year 36% rule is an official public general-rule candidate with individualized applicability left OPEN. Official network-origin provenance, effective-law authentication and independent financial factual approval remain unresolved.

### Cumulative gates after this execution
- **P0C:** strict code path and a real source window demonstrated; original official HTTP bytes / independent audit **not** complete.
- **P0D:** actual encrypted Google Drive **cloud roundtrip and separate local-process replay PASS** for 6-receipt pilot and 13-receipt full-scope checkpoint; cross-chat user-held-key recovery **not** demonstrated.
- **P0E:** original #1 **3/81**, 78 unprocessed, 13 event receipts, current next window W00004; final one-command full-video research `NO_GO`.
- **Release:** no independent facts approved, no personal financial advice authorized; P0 GO remains blocked.

**No additional follow-up or automation is scheduled by this report.**
