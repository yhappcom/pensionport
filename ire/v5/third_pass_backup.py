"""AES-GCM encrypted four-ledger backup (original + risk + historical + 64-case).

All four prior event chains are replayed on a fresh private directory. The
archive carries no passphrase; public GitHub carries no private underlying data.
"""
from __future__ import annotations
import os, json, base64, zlib, secrets, shutil
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from .engine import sha256, canonical, require, RunError, _private_dir, _exclusive_json, ResearchRun
from .incremental import IncrementalAudit
from .second_pass import RelationSecondPass
from .second_pass_backup import restore as restore_previous
from .third_pass import FocusedReview64
from .portable import _key, _inflate, _private_write_bytes, SALT_BYTES, NONCE_BYTES, MAX_ARCHIVE, MAX_DECOMPRESSED
SCHEMA='IRE_V5_FOUR_CHAIN_64_RISK_ARCHIVE_V1'
MAGIC=(SCHEMA+'\n').encode()

def export(*,old_three_chain_archive:Path,third:FocusedReview64,passphrase:str,destination:Path):
    third.replay();base=Path(old_three_chain_archive).read_bytes()
    require(0<len(base)<MAX_ARCHIVE,'FOUR_CHAIN_BAD_OLD_ARCHIVE')
    data={'schema':SCHEMA,'three_chain_archive_base64':base64.b64encode(base).decode(),
      'three_chain_archive_sha256':sha256(base),'third_lock':third.lock,
      'third_events':[{'name':p.name,'body':json.loads(p.read_text('utf-8'))} for p in sorted(third.events.glob('*.json'))],
      'third_head':third.head,'third_status_sha256':sha256(canonical(third.status()))}
    payload=canonical(data)
    require(len(payload)<=MAX_DECOMPRESSED,'FOUR_CHAIN_DECOMPRESSED_TOO_BIG')
    salt=secrets.token_bytes(SALT_BYTES);nonce=secrets.token_bytes(NONCE_BYTES)
    blob=MAGIC+salt+nonce+AESGCM(_key(passphrase,salt)).encrypt(nonce,zlib.compress(payload,9),MAGIC)
    require(len(blob)<=MAX_ARCHIVE,'FOUR_CHAIN_ARCHIVE_TOO_BIG')
    dest=Path(destination);require(dest.parent.is_dir() and not dest.exists(),'FOUR_CHAIN_WOULD_OVERWRITE')
    _private_write_bytes(dest,blob)
    return {'schema':SCHEMA,'encrypted_sha256':sha256(blob),'encrypted_bytes':len(blob),
      'third_head':third.head,'reviewed_risks':64,'no_secret_included':True}

def restore(*,archive:Path,passphrase:str,destination:Path):
    blob=Path(archive).read_bytes()
    require(blob.startswith(MAGIC) and len(blob)<=MAX_ARCHIVE and len(blob)>len(MAGIC)+SALT_BYTES+NONCE_BYTES+16,'FOUR_CHAIN_BAD_HEADER')
    x=len(MAGIC);salt=blob[x:x+SALT_BYTES];nonce=blob[x+SALT_BYTES:x+SALT_BYTES+NONCE_BYTES]
    try:packed=AESGCM(_key(passphrase,salt)).decrypt(nonce,blob[x+SALT_BYTES+NONCE_BYTES:],MAGIC)
    except InvalidTag as e:raise RunError('FOUR_CHAIN_WRONG_PASSWORD_OR_TAMPER') from e
    data=json.loads(_inflate(packed))
    require(isinstance(data,dict) and data.get('schema')==SCHEMA,'FOUR_CHAIN_WRONG_SCHEMA')
    try:old=base64.b64decode(data['three_chain_archive_base64'],validate=True)
    except (ValueError,KeyError) as e:raise RunError('FOUR_CHAIN_MISSING_OLD') from e
    require(sha256(old)==data.get('three_chain_archive_sha256'),'FOUR_CHAIN_OLD_HASH_CHANGED')
    dest=Path(destination);require(dest.parent.is_dir() and not dest.exists(),'FOUR_CHAIN_OVERWRITE_DENIED')
    stage=dest.with_name(dest.name+'.stage-'+secrets.token_hex(6))
    try:
        stage.mkdir(mode=0o700)
        _private_write_bytes(stage/'previous.v5bundle',old)
        previous=restore_previous(archive=stage/'previous.v5bundle',passphrase=passphrase,destination=stage/'previous')
        b=stage/'previous'/'previous'/'base';a=stage/'previous'/'previous'/'review';r=stage/'previous'/'second_pass'
        source=(b/'private_source.srt').read_bytes()
        run=ResearchRun(source,json.loads((b/'source_manifest.json').read_text('utf-8')),b)
        audit=IncrementalAudit(run,a)
        prior=json.loads((r/'second_pass_lock.json').read_text('utf-8'))
        # Three-chain archive does not publicly expose old knowledge text. It stays
        # inside the previous encrypted bundle; reload only from private encrypted copy.
        import zlib as _zlib
        three_magic=b'IRE_V5_SECOND_PASS_COMBINED_ARCHIVE_V1\n'
        oldx=len(three_magic);old_salt=old[oldx:oldx+SALT_BYTES]
        old_nonce=old[oldx+SALT_BYTES:oldx+SALT_BYTES+NONCE_BYTES]
        old_plain=AESGCM(_key(passphrase,old_salt)).decrypt(old_nonce,old[oldx+SALT_BYTES+NONCE_BYTES:],three_magic)
        old_data=json.loads(_inflate(old_plain))
        rel=RelationSecondPass(audit,r,old_data['second_pass_prior_claims'],prior_blob_sha=prior['prior_blob_sha256'])
        p=_private_dir(stage/'third_pass');_private_dir(p/'events')
        _exclusive_json(p/'lock.json',data['third_lock'])
        for n,item in enumerate(data['third_events'],1):
            require(item['name'].startswith(f'{n:06d}_') and item['name'].endswith('.json') and
                    isinstance(item['body'],dict),'FOUR_CHAIN_BAD_EVENT_ID')
            _exclusive_json(p/'events'/item['name'],item['body'])
        third=FocusedReview64(audit,rel,p)
        require(third.head==data['third_head'] and sha256(canonical(third.status()))==data['third_status_sha256']
               and third.status()['reviewed']==64,'FOUR_CHAIN_REPLAY_STATUS_MISMATCH')
        summary=third.status();os.rename(stage,dest)
    except Exception:
        if stage.exists():shutil.rmtree(stage)
        raise
    return {'schema':SCHEMA,'archive_sha256':sha256(blob),'restored_four_chains':True,
      'original_event_head':summary['source_chain_head'],'incremental_event_head':summary['audit_chain_head'],
      'historic_relation_head':summary['relation_chain_head'],'focused_64_head':summary['third_pass_head'],
      'reviewed':summary['reviewed'],'remaining_initial_112_risks':summary['remaining_initial_112_risks'],
      'independent_financial_facts_approved':0,'advisory_go':False}
