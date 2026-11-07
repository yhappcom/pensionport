"""V5 five-video portable encrypted bundle using existing per-video AES-GCM seals.

No plaintext SRT or claim is written into the ZIP. Every video archive is AEAD
and replay-validated; the multi-video batch lock and receipt-chain digests are
rechecked after restoring all videos to a new private directory.
"""
from __future__ import annotations
import json
import os
import secrets
import shutil
import tempfile
import zipfile
from pathlib import Path
from .engine import canonical, sha256, require, _exclusive_json, _private_dir, RunError
from .batch import FiveVideoResearchBatch
from .portable import export_encrypted, import_encrypted, _private_write_bytes

SCHEMA="IRE_V5_FIVE_VIDEO_ENCRYPTED_PACKAGE_V1"
MAX_ENTRY=70_000_000
MAX_PACKAGE=250_000_000


def export_batch(batch: FiveVideoResearchBatch, secret: str,
                 destination: str | Path) -> dict:
    path=Path(destination).expanduser().resolve()
    require(not path.exists(),"FIVE_VIDEO_ARCHIVE_WOULD_OVERWRITE")
    require(path.parent.exists(),"FIVE_VIDEO_ARCHIVE_PARENT_MISSING")
    state=batch.status()
    with tempfile.TemporaryDirectory() as t:
        private=Path(t)
        entries=[]
        for vid in batch.video_order:
            p=private/(vid+".v5enc")
            one=export_encrypted(batch.runs[vid],secret,p)
            entries.append({"video_id":vid,"archive_sha256":one["archive_sha256"],
                            "source_sha256":one["source_sha256"],
                            "receipt_count":one["receipt_count"],
                            "receipt_head_sha256":one["event_chain_head_sha256"]})
        manifest={"schema":SCHEMA,"lock":batch.lock,
                  "entries":entries,"batch_status_sha256":sha256(canonical(state)),
                  "model_execution_independently_attested":False,
                  "financial_facts_approved":0}
        temporary=path.with_name(path.name+"."+secrets.token_hex(8)+".tmp")
        fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.close(fd)
        try:
            with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_STORED) as z:
                z.writestr("manifest.json",canonical(manifest))
                for row in entries:
                    z.write(private/(row["video_id"]+".v5enc"),
                            arcname="videos/"+row["video_id"]+".v5enc")
            require(temporary.stat().st_size <= MAX_PACKAGE,
                    "FIVE_VIDEO_ARCHIVE_TOO_LARGE")
            os.replace(temporary,path)
        finally:
            temporary.unlink(missing_ok=True)
    return {"schema":SCHEMA,"archive_sha256":sha256(path.read_bytes()),
            "video_count":len(entries),"event_receipts":sum(x["receipt_count"] for x in entries),
            "source_windows_processed":state["windows_processed"],
            "source_windows_remaining":state["windows_remaining"],
            "encrypted_video_payloads":True,"secret_saved_with_file":False,
            "independently_approved_financial_facts":0}


def restore_batch(archive: str | Path, secret: str, destination: str | Path) -> dict:
    path=Path(archive).expanduser().resolve()
    require(path.stat().st_size <= MAX_PACKAGE,"FIVE_VIDEO_ARCHIVE_TOO_LARGE")
    dest=Path(destination).expanduser().resolve()
    require(not dest.exists(),"FIVE_VIDEO_RESTORE_WOULD_OVERWRITE")
    require(dest.parent.exists(),"FIVE_VIDEO_RESTORE_PARENT_MISSING")
    staging=dest.with_name(dest.name+".stage-"+secrets.token_hex(8))
    try:
        _private_dir(staging)
        _private_dir(staging/"videos")
        with zipfile.ZipFile(path) as z:
            files=z.infolist()
            require(all(not f.is_dir() and 0<=f.file_size<=MAX_ENTRY for f in files),
                    "FIVE_VIDEO_ARCHIVE_ENTRY_SIZE_INVALID")
            require(len(files) in (5,6),"FIVE_VIDEO_ARCHIVE_ENTRY_COUNT_INVALID")
            require(sum(f.file_size for f in files)<=MAX_PACKAGE,
                    "FIVE_VIDEO_ARCHIVE_DECOMPRESSED_TOO_LARGE")
            require(files[0].filename=="manifest.json", "FIVE_VIDEO_ARCHIVE_MANIFEST_MISSING")
            manifest=json.loads(z.read("manifest.json"))
            require(type(manifest) is dict and manifest.get("schema")==SCHEMA and
                    manifest.get("financial_facts_approved")==0 and
                    manifest.get("model_execution_independently_attested") is False,
                    "FIVE_VIDEO_ARCHIVE_SCHEMA_OR_APPROVAL_INVALID")
            entries=manifest.get("entries")
            lock=manifest.get("lock")
            require(type(entries) is list and 4<=len(entries)<=5 and
                    type(lock) is dict and len(lock.get("videos",[]))==len(entries),
                    "FIVE_VIDEO_ARCHIVE_SOURCE_CENSUS_INVALID")
            paths=["manifest.json"]+["videos/"+e["video_id"]+".v5enc" for e in entries]
            require([f.filename for f in files]==paths,
                    "FIVE_VIDEO_ARCHIVE_UNEXPECTED_FILES")
            for entry in entries:
                vid=entry["video_id"]
                raw=z.read("videos/"+vid+".v5enc")
                require(sha256(raw)==entry["archive_sha256"],
                        "FIVE_VIDEO_ARCHIVE_ENCRYPTED_BLOB_CHANGED")
                encrypted=staging/(vid+".v5enc")
                _private_write_bytes(encrypted,raw)
                try:
                    result=import_encrypted(encrypted,secret,staging/"videos"/vid)
                finally:
                    encrypted.unlink(missing_ok=True)
                require(result["source_sha256"]==entry["source_sha256"] and
                        result["receipt_count"]==entry["receipt_count"] and
                        result["event_chain_head_sha256"]==entry["receipt_head_sha256"],
                        "FIVE_VIDEO_ARCHIVE_VIDEO_REPLAY_MISMATCH")
        _exclusive_json(staging/"batch_lock.json",lock)
        batch=FiveVideoResearchBatch.open_private(staging)
        status=batch.status()
        require(sha256(canonical(status))==manifest["batch_status_sha256"],
                "FIVE_VIDEO_ARCHIVE_AGGREGATE_STATE_CHANGED")
        os.rename(staging,dest)
    except Exception:
        if staging.exists():shutil.rmtree(staging)
        raise
    return {"schema":SCHEMA,"archive_sha256":sha256(path.read_bytes()),
            "video_count":status["video_count"],
            "source_windows_processed":status["windows_processed"],
            "source_windows_remaining":status["windows_remaining"],
            "event_receipts":sum(x["event_receipts"] for x in status["videos"]),
            "fresh_store_replay_verified":True,
            "one_chat_turn_full_research_proven":False}
