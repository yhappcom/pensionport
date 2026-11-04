"""Decrypt user-owned IRE V3/V4 legacy snapshots (RFC 8439 ChaCha20-Poly1305).

Requires pip install cryptography==46.0.4.
NEVER commit the key, decrypted outputs, or original private transcripts.
"""
import argparse
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    a = ap.parse_args()
    root = Path(__file__).resolve().parent
    key_text = a.key_file.read_text(encoding="utf-8")
    key_hex = next((x.partition("=")[2].strip() for x in key_text.splitlines() if x.startswith("key_hex=")), key_text.strip())
    key = bytes.fromhex(key_hex)
    if len(key) != 32:
        raise ValueError("Invalid 256-bit recovery key")
    entries = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["files"]
    if a.output_dir.exists() and list(a.output_dir.iterdir()):
        raise FileExistsError("Refusing overwrite of existing directory")
    results = []
    for ent in entries:
        blob = (root / (ent["name"] + ".ppc1")).read_bytes()
        if sha256(blob) != ent["encrypted_sha256"]:
            raise ValueError("Encrypted file SHA256 mismatch: " + ent["name"])
        if blob[:4] != b"PPC1":
            raise ValueError("Invalid archive header")
        plain = ChaCha20Poly1305(key).decrypt(blob[4:16], blob[16:], b"")
        if sha256(plain) != ent["original_sha256"]:
            raise ValueError("Decrypted file SHA256 mismatch")
        results.append((ent["name"], plain))
    a.output_dir.mkdir(parents=True, exist_ok=True)
    for name, plain in results:
        dst = a.output_dir / name
        dst.write_bytes(plain)
    print("Restored and verified:", len(results))

if __name__ == "__main__":
    main()
