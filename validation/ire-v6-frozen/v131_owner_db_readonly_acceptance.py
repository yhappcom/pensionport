"""V131 no-write V6 operational DB snapshot and original SRT cross-replay.

Requires an externally supplied DB SHA and V6 head in addition to the raw
source/manifest pins. Caller-supplied pins are NOT authenticated signatures.
No method can upgrade a known isolated test fixture to owner operation.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import hashlib
import os
import sqlite3

from ire.v6.store import TransactionStore, SCHEMA_VERSION
from ire.v6.source import verify_source
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven


def _hold(code):
    raise QualityNotProven("V131_OWNER_DB_"+code)


def _file_hash(path):
    hasher=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            hasher.update(block)
    return hasher.hexdigest()


def audit_readonly_owner_v6_snapshot(path, *, owner_external_anchor, original_srt,
                                     source_manifest, independently_attested_owner_signature=False):
    """Return source/head consistency, NEVER a user-identity or P0 signature proof.

    WAL/SHM sidecars are forbidden: require an operator-exported closed SQLite
    snapshot and a separately held external SHA/head checkpoint.
    """
    if not isinstance(path,(str,Path)) or not str(path):
        _hold("OPERATIONAL_SNAPSHOT_MISSING")
    path=Path(path)
    if not path.is_file() or path.is_symlink() or path.suffix!=".db":
        _hold("OPERATIONAL_SNAPSHOT_MISSING_OR_UNSAFE")
    if (path.with_name(path.name+'-wal').exists() or
        path.with_name(path.name+'-shm').exists()):
        _hold("LIVE_WAL_SNAPSHOT_NOT_STABLE")
    if not 4096<=path.stat().st_size<=512*1024*1024:
        _hold("SNAPSHOT_SIZE_INVALID")
    required={"schema","source_kind","video_id","scope_id","db_sha256",
              "head_sha256","source_sha256","manifest_sha256"}
    a=owner_external_anchor
    if type(a) is not dict or set(a)!=required or a["schema"]!="IRE_V131_EXTERNAL_DB_SOURCE_ANCHOR_V1":
        _hold("INDEPENDENT_ANCHOR_REQUIRED")
    if a["source_kind"]!="OWNER_OPERATIONAL_CLOSED_SNAPSHOT":
        _hold("ISOLATED_STAGING_DB_NOT_OPERATIONAL")
    for k in ("db_sha256","head_sha256","source_sha256","manifest_sha256"):
        h=a[k]
        if type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
            _hold("EXTERNAL_ANCHOR_HASH_INVALID")
    if type(independently_attested_owner_signature) is not bool:
        _hold("OWNER_SIGNATURE_ATTESTATION_TYPE_INVALID")
    snapshot_digest=_file_hash(path)
    if a["db_sha256"]!=snapshot_digest:
        _hold("DB_BYTES_MISMATCH_EXTERNAL_ANCHOR")
    src=verify_source(original_srt,source_manifest,
                      expected_source_sha256=a["source_sha256"],
                      expected_manifest_sha256=a["manifest_sha256"])
    if src.video_id != a["video_id"]:
        _hold("OWNER_ORIGINAL_VIDEO_ID_MISMATCH")
    # immutable=1 means we explicitly require a completed closed snapshot,
    # not a live WAL database with uncheckpointed commits.
    uri='file:'+quote(str(path.resolve()),safe='/')+'?mode=ro&immutable=1'
    con=sqlite3.connect(uri,uri=True)
    con.row_factory=sqlite3.Row
    try:
        con.execute('PRAGMA query_only=ON')
        integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity!='ok' or con.execute('PRAGMA user_version').fetchone()[0]!=SCHEMA_VERSION:
            _hold("DB_INTEGRITY_OR_VERSION_FAILED")
        rows=con.execute('SELECT scope_id, video_id, source_sha256, manifest_sha256 FROM scopes').fetchall()
        if not rows:
            _hold("OPERATIONAL_DB_EMPTY_NO_RESEARCH")
        scope_map={r['scope_id']:dict(r) for r in rows}
        if a['scope_id'] not in scope_map:
            _hold("PINNED_SCOPE_NOT_PRESENT")
        target=scope_map[a['scope_id']]
        if target['video_id']!=a['video_id'] or target['source_sha256']!=src.source_sha256 or target['manifest_sha256']!=src.manifest_sha256:
            _hold("OPERATIONAL_SCOPE_SOURCE_DISAGREES")
        store=TransactionStore.__new__(TransactionStore)
        heads={}
        for sid in sorted(scope_map):
            _,seq,head=store._replay(con,sid)
            heads[sid]={"head":head,"events":seq}
        if heads[a['scope_id']]['head']!=a['head_sha256']:
            _hold("OWNER_EXPORTED_HEAD_MISMATCH")
        if (_file_hash(path)!=snapshot_digest or
                path.with_name(path.name+'-wal').exists() or
                path.with_name(path.name+'-shm').exists()):
            _hold("SNAPSHOT_CHANGED_DURING_READ")
        return {"schema":"IRE_V131_OWNER_DB_REPLAY_V1",
                "status":"DB_SOURCE_AND_EVENT_REPLAY_PASSED_OWNER_IDENTITY_UNATTESTED",
                "db_sha256":a['db_sha256'],"source_sha256":src.source_sha256,
                "scope_id":a['scope_id'],"head_sha256":a['head_sha256'],
                "scopes_replayed":len(heads),"events_replayed":sum(x['events'] for x in heads.values()),
                "operational_owner_identity_cryptographically_verified":False,
                "owner_signature_accepted_as_evidence":False,
                "external_pins_self_attested_not_certified":True,
                "independently_attested_owner_signature_supplied":independently_attested_owner_signature,
                "original_audio_semantics_verified":False,
                "chatgpt_final_research_approved":False,
                "p0_go":False}
    except sqlite3.DatabaseError as exc:
        raise QualityNotProven('V131_OWNER_DB_SQLITE_SCHEMA_OR_EVENTS_INVALID') from exc
    finally:
        con.close()
