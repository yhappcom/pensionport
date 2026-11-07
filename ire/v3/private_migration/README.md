# V3 / V4 private Drive migration (2026-11-04)

The 25 files here were copied from the ChatGPT-created research artifacts in Google Drive, **encrypted before being committed to this public repository**, and verified by Git object SHA-1 against independently encrypted local reference bytes. No original source text or recovery key is in Git.

- Cipher: RFC 8439 ChaCha20-Poly1305, fresh cryptographic 256-bit key and unique 96-bit nonce per file, no associated data.
- Container: `PPC1` (4 bytes) + nonce (12 bytes) + ciphertext + authentication tag (16 bytes).
- `manifest.json` lists the original and encrypted SHA-256, file names, and original Drive IDs. The encrypted files are lossless backups, **not approved financial facts** and not executable investment research.
- **The recovery key is not recoverable from this repository.** It was provided separately to the owner in the migration conversation. If the key is lost, these archives are not recoverable.
- For recovery, install `cryptography==46.0.4` and use `python ire/v3/private_migration/restore.py --key-file /secure/IRE_GITHUB_MIGRATION_RECOVERY_KEY_20261104.txt --output-dir /private/restored_v3`. Do not commit decrypted output or the key.
- Prior V5 encrypted historical snapshots are separate under `ire/v5/encrypted_archives/` and require their **original** V5 archive secrets, not this new V3/V4 key.
- User-supplied source SRT folder `원본자막` is not part of this migration and must remain untouched.
