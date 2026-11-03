"""Authenticated encrypted package of *both* V5 source and incremental audit chains.

No data leaves the local machine from this module. A cloud upload must occur via
an explicitly connected private store; the passphrase must be retained offline.
"""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import zlib
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .engine import ResearchRun, RunError, require, canonical,sha256,_private_dir,_exclusive_json
from .incremental import IncrementalAudit
from .portable import _key,_inflate,_private_write_bytes, SALT_BYTES,NONCE_BYTES,MAX_ARCHIVE,MAX_DECOMPRESSED

MAGIC=b"IRE_V5_INCREMENTAL_PRIVATE_ARCHIVE_V1\n"
SCHEMA="IRE_V5_INCREMENTAL_PRIVATE_ARCHIVE_V1"
_EVENT_NAME=re.compile(r"^\d{6}_[0-9a-f]{64}\.json$")


def _chain_entries(folder:Path)->list[dict]:
    out=[]
    for p in sorted(folder.glob('*.json')):
        require(_EVENT_NAME.fullmatch(p.name) is not None,"AUDIT_BACKUP_EVENT_BAD_NAME")
        out.append({"name":p.name,"value":json.loads(p.read_text('utf-8'))})
    return out


def backup(run:ResearchRun,audit:IncrementalAudit,passphrase:str,archive_path:str|Path)->dict:
    run.replay();audit.replay()
    require(audit.lock['base_chain_sha256']==run.head and
            audit.lock['source_sha256']==sha256(run.source),"AUDIT_BACKUP_BASE_DRIFT")
    data={"schema":SCHEMA,
        "source_srt_base64":base64.b64encode(run.source).decode('ascii'),
        "source_sha256":sha256(run.source),
        "manifest":run.manifest,
        "run_lock":run.lock,
        "base_events":_chain_entries(run.events),
        "base_event_head_sha256":run.head,
        "audit_lock":audit.lock,
        "audit_events":_chain_entries(audit.events_dir),
        "audit_event_head_sha256":audit.head,
        "audit_status_sha256":sha256(canonical(audit.status()))}
    encoded=canonical(data)
    require(len(encoded)<=MAX_DECOMPRESSED,'AUDIT_BACKUP_TOO_BIG')
    salt,nonce=secrets.token_bytes(SALT_BYTES),secrets.token_bytes(NONCE_BYTES)
    sealed=MAGIC+salt+nonce+AESGCM(_key(passphrase,salt)).encrypt(nonce,zlib.compress(encoded,9),MAGIC)
    require(len(sealed)<=MAX_ARCHIVE,'AUDIT_BACKUP_TOO_LARGE')
    dest=Path(archive_path).resolve()
    require(dest.parent.exists() and not dest.exists(),'AUDIT_BACKUP_WOULD_OVERWRITE')
    _private_write_bytes(dest,sealed)
    return {'schema':SCHEMA,'encrypted_archive_sha256':sha256(sealed),
            'source_sha256':sha256(run.source), 'source_event_count':len(data['base_events']),
            'audit_event_count':len(data['audit_events']),
            'audit_head_sha256':audit.head,
            'source_head_sha256':run.head,
            'no_secret_stored_in_archive':True}


def restore(archive_path:str|Path,passphrase:str,new_root:str|Path)->dict:
    blob=Path(archive_path).resolve().read_bytes()
    require(blob.startswith(MAGIC) and len(blob)<=MAX_ARCHIVE and
            len(blob)>len(MAGIC)+SALT_BYTES+NONCE_BYTES+16,"AUDIT_BACKUP_HEADER_INVALID")
    i=len(MAGIC);salt=blob[i:i+SALT_BYTES];nonce=blob[i+SALT_BYTES:i+SALT_BYTES+NONCE_BYTES]
    try:
        encoded=AESGCM(_key(passphrase,salt)).decrypt(nonce,blob[i+SALT_BYTES+NONCE_BYTES:],MAGIC)
    except InvalidTag as e:
        raise RunError('AUDIT_BACKUP_WRONG_SECRET_OR_TAMPERED') from e
    try:
        data=json.loads(_inflate(encoded))
    except (ValueError,UnicodeError) as e:
        raise RunError('AUDIT_BACKUP_BODY_INVALID') from e
    require(type(data) is dict and data.get('schema')==SCHEMA,'AUDIT_BACKUP_SCHEMA')
    try:source=base64.b64decode(data['source_srt_base64'],validate=True)
    except (KeyError,ValueError) as e:raise RunError('AUDIT_BACKUP_SOURCE_INVALID') from e
    require(sha256(source)==data.get('source_sha256'),'AUDIT_BACKUP_SOURCE_DRIFT')
    dest=Path(new_root).resolve()
    require(not dest.exists() and dest.parent.is_dir(),'AUDIT_BACKUP_RESTORE_DESTINATION_EXISTS')
    temp=dest.with_name(dest.name+'.stage-'+secrets.token_hex(8))
    try:
        temp.mkdir(mode=0o700)
        base=_private_dir(temp/'base');_private_dir(base/'events')
        ra=_private_dir(temp/'review');_private_dir(ra/'events')
        _private_write_bytes(base/'private_source.srt',source)
        for p,value in ((base/'source_manifest.json',data['manifest']),
                        (base/'run_lock.json',data['run_lock']),
                        (ra/'audit_lock.json',data['audit_lock'])):
            _exclusive_json(p,value)
        for typ,root in [('base_events',base/'events'),('audit_events',ra/'events')]:
            entries=data[typ]
            require(type(entries) is list and len(entries)<=250000,'AUDIT_BACKUP_EVENT_COUNT')
            for n,entry in enumerate(entries,1):
                require(type(entry) is dict and type(entry.get('name')) is str and
                        _EVENT_NAME.fullmatch(entry['name']) is not None and
                        entry['name'].startswith(f'{n:06d}_') and
                        type(entry.get('value')) is dict,'AUDIT_BACKUP_EVENT_NAME_INVALID')
                _exclusive_json(root/entry['name'],entry['value'])
        rec=ResearchRun(source,data['manifest'],base)
        audit=IncrementalAudit(rec,ra)
        require(rec.head==data['base_event_head_sha256'] and
                audit.head==data['audit_event_head_sha256'] and
                sha256(canonical(audit.status()))==data['audit_status_sha256'],
                'AUDIT_BACKUP_REPLAY_MISMATCH')
        os.rename(temp,dest)
    except Exception:
        if temp.exists():shutil.rmtree(temp)
        raise
    return {'schema':SCHEMA,'encrypted_archive_sha256':sha256(blob),
           'restored_source_head_sha256':rec.head,
           'restored_incremental_head_sha256':audit.head,
           'restored_risk_cases':audit.status()['issues_total'],
           'restored_review_count':audit.status()['issues_reviewed'],
           'validated_by_actual_replay':True,
           'investment_advice_approved':False,
           'restored_root':str(dest)}
