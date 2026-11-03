"""Encrypted, portable three-chain V5 archive (source + incremental + relation audit).

Original and incremental evidence receipts retain their own independent hashes.
Only private passphrase holders can restore; no original/secret gets sent to GitHub.
"""
from __future__ import annotations
import base64,json,os,secrets,shutil,zlib
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ire.v5.engine import sha256,canonical,require,RunError,_private_dir,_exclusive_json
from ire.v5.portable import _key,_inflate,_private_write_bytes,SALT_BYTES,NONCE_BYTES,MAX_ARCHIVE,MAX_DECOMPRESSED
from ire.v5.incremental_backup import restore as restore_base
from ire.v5.second_pass import RelationSecondPass
from ire.v5.incremental import IncrementalAudit
from ire.v5.engine import ResearchRun

MAGIC=b'IRE_V5_SECOND_PASS_COMBINED_ARCHIVE_V1\n'
SCHEMA='IRE_V5_SECOND_PASS_COMBINED_ARCHIVE_V1'

def _entries(root):
    return [{'name':f.name,'body':json.loads(f.read_text('utf-8'))} for f in sorted(root.glob('*.json'))]

def backup(*,original_incremental_archive:Path,second_pass:RelationSecondPass,passphrase:str,destination:Path):
    second_pass.replay()
    old=Path(original_incremental_archive).read_bytes()
    require(20<=len(old)<=MAX_ARCHIVE,'SECOND_PASS_BASE_ARCHIVE_TOO_LARGE')
    second_pass.audit.replay();second_pass.run.replay()
    data={'schema':SCHEMA,'original_incremental_archive_base64':base64.b64encode(old).decode('ascii'),
        'original_incremental_archive_sha256':sha256(old),
        'second_pass_lock':second_pass.lock,
        'second_pass_prior_claims':second_pass.prior_claims,
        'second_pass_events':_entries(second_pass.events),
        'second_pass_event_head_sha256':second_pass.head,
        'second_pass_status_sha256':sha256(canonical(second_pass.status())),
        'no_plaintext_secret_in_archive':True}
    raw=canonical(data)
    require(len(raw)<=MAX_DECOMPRESSED,'SECOND_PASS_BACKUP_TOO_LARGE')
    salt,nonce=secrets.token_bytes(SALT_BYTES),secrets.token_bytes(NONCE_BYTES)
    encrypted=MAGIC+salt+nonce+AESGCM(_key(passphrase,salt)).encrypt(nonce,zlib.compress(raw,9),MAGIC)
    dest=Path(destination)
    require(dest.parent.is_dir() and not dest.exists(),'SECOND_PASS_ARCHIVE_ALREADY_EXISTS')
    _private_write_bytes(dest,encrypted)
    return {'encrypted_archive_sha256':sha256(encrypted),'encrypted_archive_bytes':len(encrypted),
       'second_pass_event_head_sha256':second_pass.head,
       'base_audit_event_head_sha256':second_pass.audit.head,'no_secret_included':True}

def restore(*,archive:Path,passphrase:str,destination:Path):
    blob=Path(archive).read_bytes()
    require(blob.startswith(MAGIC) and len(blob)<=MAX_ARCHIVE and
          len(blob)>len(MAGIC)+SALT_BYTES+NONCE_BYTES+16,'SECOND_PASS_BAD_HEADER')
    i=len(MAGIC);salt=blob[i:i+SALT_BYTES];nonce=blob[i+SALT_BYTES:i+SALT_BYTES+NONCE_BYTES]
    try:
        packed=AESGCM(_key(passphrase,salt)).decrypt(nonce,blob[i+SALT_BYTES+NONCE_BYTES:],MAGIC)
    except InvalidTag as e:raise RunError('SECOND_PASS_WRONG_KEY_OR_TAMPERED') from e
    try:data=json.loads(_inflate(packed))
    except (ValueError,UnicodeError) as e:raise RunError('SECOND_PASS_BODY_INVALID') from e
    require(isinstance(data,dict) and data.get('schema')==SCHEMA,'SECOND_PASS_BAD_SCHEMA')
    try:old=base64.b64decode(data['original_incremental_archive_base64'],validate=True)
    except (ValueError,KeyError) as e:raise RunError('SECOND_PASS_MISSING_BASE_ARCHIVE') from e
    require(sha256(old)==data.get('original_incremental_archive_sha256'),
            'SECOND_PASS_OLD_ARCHIVE_TAMPERED')
    dest=Path(destination)
    require(not dest.exists() and dest.parent.is_dir(),'SECOND_PASS_RESTORE_DEST_EXISTS')
    stage=dest.with_name(dest.name+'.stage-'+secrets.token_hex(8))
    try:
        stage.mkdir(mode=0o700)
        base_archive=stage/'base.v5inc'
        _private_write_bytes(base_archive,old)
        res=restore_base(base_archive,passphrase,stage/'previous')
        base=stage/'previous'/'base'
        source=(base/'private_source.srt').read_bytes()
        run=ResearchRun(source,json.loads((base/'source_manifest.json').read_text('utf-8')),base)
        audit=IncrementalAudit(run,stage/'previous'/'review')
        root=_private_dir(stage/'second_pass');_private_dir(root/'events')
        _exclusive_json(root/'second_pass_lock.json',data['second_pass_lock'])
        entries=data['second_pass_events']
        require(isinstance(entries,list) and len(entries)<=100000,'SECOND_PASS_BAD_EVENTS_COUNT')
        for n,entry in enumerate(entries,1):
            require(isinstance(entry,dict) and isinstance(entry.get('name'),str)
                and entry['name'].startswith(f'{n:06d}_')
                and entry['name'].endswith('.json') and isinstance(entry.get('body'),dict),
                'SECOND_PASS_BAD_EVENT_NAME')
            _exclusive_json(root/'events'/entry['name'],entry['body'])
        s=RelationSecondPass(audit,root,data['second_pass_prior_claims'],
             prior_blob_sha=data['second_pass_lock']['prior_blob_sha256'])
        require(s.head==data['second_pass_event_head_sha256'] and
             sha256(canonical(s.status()))==data['second_pass_status_sha256'],
             'SECOND_PASS_REPLAY_MISMATCH')
        summary=s.status()
        os.rename(stage,dest)
    except Exception:
        if stage.exists():shutil.rmtree(stage)
        raise
    return {'schema':SCHEMA,'archive_sha256':sha256(blob),
        'original_source_head_sha256':summary['original_event_head_sha256'],
        'incremental_event_head_sha256':summary['incremental_event_head_sha256'],
        'second_pass_event_head_sha256':summary['second_pass_head_sha256'],
        'remaining_initial_open_risks':summary['remaining_all_initial_open_risks'],
        'relationship_candidates_reclassified':summary['relationship_false_conflicts_reclassified'],
        'independent_financial_facts_approved':0,'validated_by_actual_replay':True}
