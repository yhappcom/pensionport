#!/usr/bin/env python3
"""P0-0-06 public-safe byte audit: integrity is not confidentiality or recovery."""
from __future__ import annotations
import argparse, base64, hashlib, json, re, subprocess, sys, zlib
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = Path("docs/IRE_P0_0_06_42_FILE_SECURITY_INVENTORY_20261122.json")
V3_MANIFEST = Path("ire/v3/private_migration/manifest.json")
V5_README = Path("ire/v5/encrypted_archives/README.md")
B64_DIR = Path("ire/v5/validation/private_source_derived_20261107")
V3_DIR = Path("ire/v3/private_migration")
V5_DIR = Path("ire/v5/encrypted_archives")
V5_EXT = {".v5archive",".v5enc",".v5inc",".v5bundle",".v5pack"}
V3 = "V3_V4_PPC1_AEAD_ENCRYPTED"
V5 = "V5_LEGACY_ENCRYPTED_UNPROVEN_RECOVERY"
B64 = "V5_PUBLIC_REVERSIBLE_B64_ZLIB"
EXPECTED = {V3:25,V5:11,B64:6}
RISK = {V3:"HOLD_BACKUP_DECRYPTION_AND_KEY_CUSTODY_UNVERIFIED",
        V5:"HOLD_BACKUP_DECRYPTION_AND_KEY_CUSTODY_UNVERIFIED",
        B64:"HOLD_UNENCRYPTED_RESEARCH_DERIVATIVE"}
BLOB = re.compile(r"^[0-9a-f]{40}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
V5_ROW = re.compile(r"^\|\s*\x60([^\x60]+)\x60\s*\|[^|]*\|\s*(\d+)\s*\|\s*\x60([0-9a-f]{64})\x60\s*\|",re.M)
SENSITIVE_KEY = re.compile(r"(?:text|quote|excerpt|transcript|subtitle|original|analysis|reason|semantic|note|claim|utterance|cue)",re.I)
COMPRESS_LIMIT = 2_000_000
JSON_LIMIT = 8_000_000

class AuditError(ValueError):
    def __init__(self,code):
        super().__init__(code)
        self.code=code

def need(ok,code):
    if not ok:
        raise AuditError(code)

def blob_sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode("ascii")+b"\x00"+b).hexdigest()

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def parse_v5_readme(text):
    found={}
    for name,size,hash_value in V5_ROW.findall(text):
        need(name not in found,"V5_DUPLICATE_README_NAME")
        found[name]=(int(size),hash_value)
    need(len(found)==11,"V5_README_EXPECTED_11")
    return found

def validate_manifest(root,inventory):
    need(inventory.get("schema")=="IRE_P0_0_06_PUBLIC_REPOSITORY_ARCHIVE_BINARY_INVENTORY_V1","BAD_SECURITY_INVENTORY_SCHEMA")
    need(inventory.get("source_snapshot_sha")=="0cd5f8d69ab41772bd9eab4dd006e7fcdd1e7ce5","INVENTORY_SOURCE_SHA")
    need(inventory.get("source_tree_truncated") is False,"INVENTORY_TREE_TRUNCATED")
    need(inventory.get("expected_counts")=={"v3_v4_ppc1_aead":25,"v5_encrypted_archives":11,"public_reversible_b64_zlib":6,"all":42},"EXPECTED_COUNTS_DRIFT")
    need(inventory.get("private_data_exposure_absence_certified") is False
         and inventory.get("actual_decryption_and_restore_proved") is False
         and inventory.get("decryption_key_available_in_public_repo") is False,"FALSE_CONFIDENTIALITY_OR_RECOVERY")
    v3raw=(root/V3_MANIFEST).read_bytes()
    v5raw=(root/V5_README).read_bytes()
    need(blob_sha(v3raw)==inventory.get("v3_manifest_git_blob_sha1"),"V3_MANIFEST_CHANGED")
    need(blob_sha(v5raw)==inventory.get("v5_readme_git_blob_sha1"),"V5_README_CHANGED")
    v3=json.loads(v3raw)
    need(v3.get("algorithm")=="ChaCha20-Poly1305" and v3.get("container")=="PPC1"
         and v3.get("recovery_key_committed") is False and len(v3.get("files",[]))==25,"V3_CRYPTO_OR_COUNT_DRIFT")
    v3rows={}
    for x in v3["files"]:
        k="ire/v3/private_migration/"+x["name"]+".ppc1"
        need(k not in v3rows and HASH.fullmatch(x["encrypted_sha256"])
             and BLOB.fullmatch(x["git_blob_sha1"]) and HASH.fullmatch(x["original_sha256"]),"V3_MANIFEST_ROW_INVALID")
        v3rows[k]=x
    v5rows={"ire/v5/encrypted_archives/"+k:v for k,v in parse_v5_readme(v5raw.decode("utf-8")).items()}
    rows=inventory.get("files")
    need(isinstance(rows,list) and len(rows)==42,"FILE_INVENTORY_NOT_42")
    paths=[x.get("path") for x in rows]
    need(len(set(paths))==42,"DUPLICATE_SECURITY_FILES")
    need(Counter(x.get("group") for x in rows)==EXPECTED,"SECURITY_GROUP_COUNT_DRIFT")
    path_set={V3:set(),V5:set(),B64:set()}
    for x in rows:
        path=x["path"]; group=x["group"]
        need(isinstance(path,str) and str(PurePosixPath(path))==path
             and not path.startswith("/") and ".." not in PurePosixPath(path).parts
             and "\\" not in path,"INVENTORY_TRAVERSAL")
        path_set[group].add(path)
        need(x.get("public_repo_access")=="PUBLIC_GIT_BLOB"
             and x.get("release_eligible") is False
             and x.get("cryptographic_recovery_tested") is False
             and x.get("current_risk")==RISK[group],"ARCHIVE_HOLD_OR_ACCESS_LAUNDERED")
        need(BLOB.fullmatch(str(x.get("git_blob_sha1","")))
             and isinstance(x.get("bytes"),int) and x["bytes"]>20,"INVALID_GIT_SHA_OR_BYTE_SIZE")
        if group==V3:
            expect=v3rows.get(path)
            need(expect and x.get("sha256")==expect["encrypted_sha256"]
                 and x.get("git_blob_sha1")==expect["git_blob_sha1"]
                 and x.get("raw_sha256")==expect["original_sha256"],"PPC1_SHA_MISMATCH")
        elif group==V5:
            expect=v5rows.get(path)
            need(expect and x.get("sha256")==expect[1] and x["bytes"]==expect[0],
                 "V5_ARCHIVE_SHA_MISMATCH")
        else:
            need(path.endswith(".json.zlib.b64") and x.get("sha256") is None,
                 "PUBLIC_REVERSIBLE_B64_NOT_MARKED")
    need(path_set[V3]==set(v3rows),"V3_CENSUS_INCOMPLETE")
    need(path_set[V5]==set(v5rows),"V5_CENSUS_INCOMPLETE")
    actual_b64={p.relative_to(root).as_posix() for p in (root/B64_DIR).glob("*.json.zlib.b64")}
    actual_v3={p.relative_to(root).as_posix() for p in (root/V3_DIR).glob("*.ppc1")}
    actual_v5={p.relative_to(root).as_posix() for p in (root/V5_DIR).iterdir() if p.is_file() and p.suffix in V5_EXT}
    need(path_set[B64]==actual_b64 and len(actual_b64)==6,"UNINDEXED_PUBLIC_B64")
    need(path_set[V3]==actual_v3,"UNINDEXED_V3_ARCHIVE")
    need(path_set[V5]==actual_v5,"UNINDEXED_V5_ARCHIVE")
    return rows

def parse_reversible_b64(encoded):
    """No original string or key ever escapes this function."""
    need(len(encoded)<=COMPRESS_LIMIT,"B64_TOO_LARGE")
    try:
        compressed=base64.b64decode(encoded.strip(),validate=True)
    except Exception:
        raise AuditError("INVALID_BASE64") from None
    need(2<len(compressed)<=COMPRESS_LIMIT,"B64_BAD_COMPRESSED_LENGTH")
    try:
        d=zlib.decompressobj()
        raw=d.decompress(compressed,JSON_LIMIT+1)
        need(len(raw)<=JSON_LIMIT and not d.unconsumed_tail,"B64_DECOMPRESSION_SIZE_LIMIT")
        raw+=d.flush(JSON_LIMIT+1-len(raw))
        need(d.eof and not d.unused_data and len(raw)<=JSON_LIMIT,"B64_TRAILING_OR_INCOMPLETE_ZLIB")
        data=json.loads(raw.decode("utf-8"))
    except AuditError:
        raise
    except (ValueError,UnicodeError,zlib.error,RecursionError):
        raise AuditError("B64_CORRUPT_JSON_OR_ZLIB") from None
    need(isinstance(data,(dict,list)),"B64_JSON_NOT_OBJECT_OR_ARRAY")
    tally={"obj":0,"arr":0,"str":0,"long_text":0,"semantic_text":0,"korean_text":0}
    stack=[(data,"")]
    while stack:
        item,key=stack.pop()
        need(sum(tally[k] for k in ("obj","arr","str"))<200_000,"B64_JSON_NODE_LIMIT")
        if isinstance(item,dict):
            tally["obj"]+=1
            need(len(item)<200_000,"B64_DICT_FANOUT")
            stack.extend((v,str(k)) for k,v in item.items())
        elif isinstance(item,list):
            tally["arr"]+=1
            need(len(item)<200_000,"B64_ARRAY_FANOUT")
            stack.extend((v,key) for v in item)
        elif isinstance(item,str):
            tally["str"]+=1
            tally["long_text"]+=int(len(item)>=80)
            tally["semantic_text"]+=int(len(item)>=32 and bool(SENSITIVE_KEY.search(key)))
            tally["korean_text"]+=int(any("\uac00"<=c<="\ud7a3" for c in item))
    return {"decoded_bytes":len(raw),"long_text":tally["long_text"],
            "semantic_text":tally["semantic_text"],"korean_text":tally["korean_text"]}

PUBLIC_SENSITIVE_SUFFIXES = (
    ".json.zlib.b64",".ppc1",".v5archive",".v5enc",".v5inc",".v5bundle",
    ".v5pack",".srt",".sqlite",".sqlite3",".db",".p12",".pfx",".pem",".key",
    ".env",".zip",".tar",".tar.gz",".tgz",".gpg",".7z",".rar"
)

def unregistered_public_sensitive_paths(tracked_paths, inventory):
    """Fail closed on newly tracked private data/keys/archives anywhere in Git."""
    authorized = {item["path"] for item in inventory.get("files",[])}
    return sorted(path for path in tracked_paths
                  if path.lower().endswith(PUBLIC_SENSITIVE_SUFFIXES)
                  and path not in authorized)

def check_public_track_paths(root,inventory):
    try:
        result=subprocess.run(["git","ls-files","-z"],cwd=root,
                              stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                              check=True)
    except (OSError,subprocess.CalledProcessError):
        raise AuditError("GIT_TRACKED_TREE_NOT_AVAILABLE") from None
    paths=[p.decode("utf-8","surrogateescape")
           for p in result.stdout.split(b"\x00") if p]
    extra=unregistered_public_sensitive_paths(paths,inventory)
    need(not extra,"UNREGISTERED_PUBLIC_PRIVATE_ARCHIVE_OR_SECRET_FILE")
    return len(paths)

def inspect(root,inventory):
    rows=validate_manifest(root,inventory)
    check_public_track_paths(root,inventory)
    counts=Counter();nonces=set();sample=[]
    for row in rows:
        path=row["path"]
        file=root/path
        need(file.is_file() and not file.is_symlink(),"ARCHIVE_NOT_REGULAR_FILE")
        raw=file.read_bytes()
        need(len(raw)==row["bytes"] and blob_sha(raw)==row["git_blob_sha1"],
             "ARCHIVE_GIT_BLOB_OR_BYTE_DRIFT")
        group=row["group"]
        if group==V3:
            need(sha256(raw)==row["sha256"] and raw[:4]==b"PPC1"
                 and len(raw)>32,"PPC1_AEAD_HEADER_OR_HASH_INVALID")
            nonce=raw[4:16]
            need(nonce not in nonces,"PPC1_NONCE_REUSE")
            nonces.add(nonce)
        elif group==V5:
            need(sha256(raw)==row["sha256"],"V5_HASH_DRIFT")
            if raw[:4]==b"PK\x03\x04" or raw[:2]==b"\x1f\x8b" or raw.lstrip()[:1] in (b"{",b"["):
                counts["v5_plaintext_or_archive_header_risk"]+=1
        else:
            metrics=parse_reversible_b64(raw)
            counts["reversible_decoded_bytes"]+=metrics["decoded_bytes"]
            counts["source_semantic_text_fields"]+=metrics["semantic_text"]
            counts["long_text_strings"]+=metrics["long_text"]
            counts["korean_text_strings"]+=metrics["korean_text"]
        counts[group]+=1
        sample.append(row["git_blob_sha1"])
    need(all(counts[g]==n for g,n in EXPECTED.items()),"SECURITY_COUNTS_CHANGED")
    return {
        "schema":"IRE_P0_0_06_READ_ONLY_BYTES_AUDIT_V1",
        "integrity_verdict":"PASS_42_HASHED_ARCHIVES_AND_REVERSED_B64",
        "security_release":"HOLD",
        "actual_v3_v5_decryption":"NOT_VERIFIED_NO_KEY",
        "public_b64_reversible":True,
        "private_source_exposure_absence_certified":False,
        "no_original_or_decoded_content_written_to_public_logs":True,
        "totals":dict(counts),
        "exact_input_blob_set_sha256":sha256("".join(sample).encode("ascii"))
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",nargs="?",choices=("verify","release"),default="verify")
    ap.add_argument("--root",type=Path,default=ROOT)
    args=ap.parse_args()
    try:
        root=args.root.resolve()
        inventory=json.loads((root/INVENTORY).read_text("utf-8"))
        r=inspect(root,inventory)
        c=r["totals"]
        print("P006_42_ARCHIVE_INTEGRITY_PASS",
              "v3_ppc1",c[V3],"v5",c[V5],"public_reversible_b64",c[B64])
        print("P006_PUBLIC_B64_RISK",
              "reversible_decoded_bytes",c.get("reversible_decoded_bytes",0),
              "semantic_fields",c.get("source_semantic_text_fields",0),
              "long_text_strings",c.get("long_text_strings",0),
              "korean_strings",c.get("korean_text_strings",0))
        if args.action=="release":
            print("P006_RELEASE_BLOCKED_PUBLIC_REVERSIBLE_DATA_AND_UNVERIFIED_PRIVATE_RECOVERY",file=sys.stderr)
            return 2
        print("P006_AUDIT_PASS_SECURITY_RELEASE_HOLD owner_private_exposure_absence=UNVERIFIED")
        return 0
    except (AuditError,OSError,KeyError,TypeError,ValueError) as err:
        print("P006_AUDIT_FAIL",err.code if isinstance(err,AuditError) else type(err).__name__,file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
