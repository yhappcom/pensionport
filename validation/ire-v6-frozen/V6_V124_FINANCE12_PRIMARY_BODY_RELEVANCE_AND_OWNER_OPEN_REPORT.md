# V124 — Twelve finance OPEN cases: archived original-source scope reconciliation

**Date:** 2026-11-15 KST · Verification branch only. No private original SRT, claimant paragraphs, private review notes, production database, or financial account content is published.

## Actual private-source and primary government body checks

- The original V123.7 owner-held 47-cue SRT bytes were read and independently SHA-256 checked against the pinned public source SHA; the unchanged 12-case finance docket was replayed. A new [private exact 12-row evidence matrix](V124_REAL_FINANCE12_PRIMARY_BYTE_RELEVANCE_SHA_ONLY.json) is SHA-committed, but its text and case review remain only in user's private Library in \`V124_PRIVATE_FINANCE12_PRIMARY_SOURCE_SCOPE_OPEN.zip\`.
- The **original first-party HTML response bytes** retained in the 2026-11-08 GitHub snapshot were rehashed: the 78,056-byte 2026-10-01 statute implementation decree §40-3 body (SHA \`5540ac2a9ecfad76382580cf7f46c947e2e0f11469ac700f4855b3a16f9115c2\`) and the 200,399-byte generic NTS pension-income page (SHA \`9cd242c9778c6248dba8c01e6bfa35e7fcc649347714ab57a348f6881dbb107d\`).
- **R011** source-ordering sub-rule: a real primary legal clause exists in the stored decree. This proves source text provenance/wording, **not** whether the specific ISA-to-pension contribution is confirmed non-tax-credited for a given taxpayer. R011 remains OPEN.
- **R004 and R010**: stored decree relevant as **context only**, not direct support for blanket pension-return deferral rights, tax penalty exemptions, or unrestricted early withdrawals; both remain OPEN.
- **R001 R005 R007 R008 R009 R012 R014 R015 R018**: no matching older original-body bytes captured specifically for those claims. In particular, the saved NTS general pension page is **not ISA maturity-to-pension 60-day transfer proof** (R014); an issuer promotion requires the dated issuer notice/eligibility conditions (R015). All remain OPEN.
- Current 2026 live **rendered** law text was researched for law context, including [art. 118-2(3), ISA payment within 60 days](https://law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=153535) and [art. 40-3, withdrawal source order](https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1001061005); rendered retrieval is **not** a replacement for exact first-party original-response bytes, applicable-date range, issuer digital signature or a claim-specific ChatGPT final verdict.

## Actual code/quality upgrade

Added \`v124_finance12_primary_provenance_guard.py\` as an **additive offline negative-control gate**. It rehashes both original HTML files using the previously pinned government-source verifier; checks that a §40-3 clause is really present; insists on an exact twelve-case inventory; and rejects a generic pension page being attributed to 60-day ISA conversion, §40-3 being attributed to unconditional penalty exemptions, or a law body being substituted for an issuer's promotion. It prohibits self-certification by unverified boolean flags; no accepting path exists in this preflight. Public unit tests use synthetic case rows, not owner-private claims.

The code does **not** independently certify full semantic entailment, issuer identity signing, legal effective period, account eligibility, product list, original speech audio, or complete recall. **No modification** of frozen \`ire/v6\` source or V123 final ChatGPT gate is implied; this is an earlier source-evidence relevance check. Future releases still require the actual V123 ChatGPT final gate and original evidence scoped case by case.

## Release and privacy result

| Field | Verified / decision |
| --- | --- |
| Archived original government body files reverified | 2 |
| Finance OPEN source docket checked | 12 / 12 |
| Cases with old government original context linked | 3 |
| Cases with exact statutory sub-rule present | 1 (R011; still OPEN) |
| Cases without matching old captured original bytes | 9 |
| Original audio and owner signed inventory | OPEN |
| Existing owner operational DB latest HEAD | NOT VERIFIED |
| Formal financial approvals / new read-only releases | **0 / 0** |
| P0 GO | **NO-GO** |

**Next blocking items:** obtain fresh official source body bytes and legal effective/scope proofs for each individual finance claim; obtain issuer-promotion original notice or reject unverifiable promotion; reconcile original audio and real owner production DB independently anchored inventory. Merely repeating hashes without such evidence cannot close any item.
