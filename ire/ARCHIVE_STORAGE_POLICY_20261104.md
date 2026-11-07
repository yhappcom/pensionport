# IRE research archive storage policy (2026-11-04)

## Authoritative Git branch and scope
- GitHub repository: `yhappcom/pensionport`.
- Archive migration was committed to `feat/ire-v5-vertical-slice-20261103`, not `main`; preserve the draft PR process. Existing V3/V4 approved research and older event records were not rewritten.
- Research plans, review code, public-safe test statuses, historical knowledge, and source-linked research reports remain in their current GitHub paths (`WORKFLOW.md`, `ire/`, `data/`, `knowledge/`, `synthesis/`).

## Google Drive migration
- 11 V5 encrypted archive files (stored under `ire/v5/encrypted_archives/`) migrated in commit `973ac54140538412b9c3a5b72f3d1217ffd942ed`; Git objects verified before deleting Drive copies.
- 25 historical V3/V4 research ZIP/JSON files (stored under `ire/v3/private_migration/`) migrated in commit `c86304d3431575b0e9a30357be1cd67926e4eb8e`. Files potentially containing private SRT excerpts, prior research, and test cases were encrypted under a **new** 256-bit owner-only key using ChaCha20-Poly1305; `manifest.json` records original and encrypted SHA-256. The key is **not in GitHub**. Restore is via `ire/v3/private_migration/restore.py`.
- Total 36 generated research artifacts transferred, and 36 original Drive copies deleted following transfer verification. Old Drive links in historical reports are therefore no longer live download locations; the immutable research report text was preserved for audit lineage.
- The Drive folder `박곰희TV_투자연구/원본자막` remains. This is original user source material, not an engine-generated archive; it was not moved into the public repository or deleted. Do not infer that raw SRT text is publicly stored in GitHub.

## Safety and recovery
- Public GitHub must **never** contain cleartext original SRTs, confidential full claim excerpts, user/investor private data, archive keys or passwords.
- Historic V5 encrypted archives use their original separately held secrets, which were **not** replaced or recovered in this migration. The new V3/V4 key does not decrypt V5.
- Encrypted Git snapshots prevent direct plaintext review; apply private-store restoration only with the correct owner-held key. Loss of a recovery key can make archived data unusable.
- Successful Git object hash checks verify file transfer, not independent financial truth or personal-investment-advice approval; all previous NO-GO limitations remain.
- Future analysis should avoid generating redundant Drive backups by default. Continue using GitHub for code/public-safe research and an appropriately access-controlled private store for sensitive working sources. A public encrypted Git archive is not a substitute for a complete managed key-recovery policy.
