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
