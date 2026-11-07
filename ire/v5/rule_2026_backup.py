"""Fifth-chain encrypted portability of focused V5 financial rule recheck.

The archive intentionally contains an encrypted *inner* four-chain archive;
no original SRT or private model claim is committed to GitHub.
"""
from __future__ import annotations
import os,json,zlib,base64,secrets,shutil
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from .engine import sha256,canonical,require,RunError,ResearchRun,_exclusive_json,_private_dir
from .portable import _key,_inflate,_private_write_bytes,SALT_BYTES,NONCE_BYTES,MAX_ARCHIVE,MAX_DECOMPRESSED
from .third_pass_backup import restore as restore_four
from .incremental import IncrementalAudit
from .second_pass import RelationSecondPass
from .third_pass import FocusedReview64
from .rule_2026_audit import RuleRecheck29
SCHEMA='IRE_V5_FIVE_CHAIN_2026_RULE_AUDIT_ARCHIVE_V1'
MAGIC=(SCHEMA+'\n').encode()

def export(*,old_four_chain_archive:Path,rule_run:RuleRecheck29,passphrase:str,destination:Path):
 rule_run.replay();archive=Path(old_four_chain_archive).read_bytes()
 require(0<len(archive)<=MAX_ARCHIVE,'RULE_FIFTH_BAD_PRIOR_ARCHIVE')
 data={'schema':SCHEMA,'four_chain_archive_base64':base64.b64encode(archive).decode(),
 'four_chain_archive_sha256':sha256(archive),'rule_lock':rule_run.lock,
 'rule_events':[{'name':p.name,'content':json.loads(p.read_text('utf-8'))} for p in sorted(rule_run.events.glob('*.json'))],
 'fifth_head':rule_run.head,'fifth_status_sha256':sha256(canonical(rule_run.status()))}
 raw=canonical(data);require(len(raw)<=MAX_DECOMPRESSED,'RULE_FIFTH_OVERSIZED')
 salt=secrets.token_bytes(SALT_BYTES);nonce=secrets.token_bytes(NONCE_BYTES)
 encrypted=MAGIC+salt+nonce+AESGCM(_key(passphrase,salt)).encrypt(nonce,zlib.compress(raw,9),MAGIC)
 require(len(encrypted)<=MAX_ARCHIVE,'RULE_FIFTH_TOO_BIG')
 p=Path(destination);require(p.parent.is_dir() and not p.exists(),'RULE_FIFTH_NO_OVERWRITE')
 _private_write_bytes(p,encrypted)
 return {'schema':SCHEMA,'archive_sha256':sha256(encrypted),'archive_bytes':len(encrypted),
 'rule_reviewed':rule_run.status()['cases_reviewed'],'official_cases':21,'asr_cases':8,
 'independently_approved_financial_facts':0,'recovery_key_in_archive':False}

def restore(*,archive:Path,passphrase:str,destination:Path):
 blob=Path(archive).read_bytes()
 require(blob.startswith(MAGIC) and len(blob)<=MAX_ARCHIVE and len(blob)>len(MAGIC)+SALT_BYTES+NONCE_BYTES+16,'RULE_FIFTH_INVALID_HEADER')
 off=len(MAGIC);salt=blob[off:off+SALT_BYTES];nonce=blob[off+SALT_BYTES:off+SALT_BYTES+NONCE_BYTES]
 try:compressed=AESGCM(_key(passphrase,salt)).decrypt(nonce,blob[off+SALT_BYTES+NONCE_BYTES:],MAGIC)
 except InvalidTag as e:raise RunError('RULE_FIFTH_WRONG_KEY_OR_TAMPER') from e
 data=json.loads(_inflate(compressed));require(data.get('schema')==SCHEMA,'RULE_FIFTH_SCHEMA_INVALID')
 inner=base64.b64decode(data['four_chain_archive_base64'],validate=True)
 require(sha256(inner)==data['four_chain_archive_sha256'],'RULE_FIFTH_INNER_CHANGED')
 dst=Path(destination);require(dst.parent.is_dir() and not dst.exists(),'RULE_FIFTH_OVERWRITE_DENIED')
 stage=dst.with_name(dst.name+'.stage-'+secrets.token_hex(5))
 try:
  stage.mkdir(mode=0o700)
  _private_write_bytes(stage/'four_chain.v5archive',inner)
  restore_four(archive=stage/'four_chain.v5archive',passphrase=passphrase,destination=stage/'four')
  old=stage/'four'
  base=old/'previous'/'previous'/'base'
  aud=old/'previous'/'previous'/'review'
  prior_dir=old/'previous'/'second_pass'
  source=(base/'private_source.srt').read_bytes()
  run=ResearchRun(source,json.loads((base/'source_manifest.json').read_text('utf-8')),base)
  audit=IncrementalAudit(run,aud)
  lock=json.loads((prior_dir/'second_pass_lock.json').read_text('utf-8'))
  # The prior claims are encrypted in the original triple-chain archive.
  triple=(old/'previous.v5bundle').read_bytes()
  triple_magic=b'IRE_V5_SECOND_PASS_COMBINED_ARCHIVE_V1\n'
  require(triple.startswith(triple_magic),'RULE_FIFTH_PRIOR_MAGIC')
  s=len(triple_magic);k_salt=triple[s:s+SALT_BYTES];k_nonce=triple[s+SALT_BYTES:s+SALT_BYTES+NONCE_BYTES]
  pbytes=AESGCM(_key(passphrase,k_salt)).decrypt(k_nonce,triple[s+SALT_BYTES+NONCE_BYTES:],triple_magic)
  prior_blob=json.loads(_inflate(pbytes))
  rel=RelationSecondPass(audit,prior_dir,prior_blob['second_pass_prior_claims'],prior_blob_sha=lock['prior_blob_sha256'])
  third=FocusedReview64(audit,rel,old/'third_pass')
  fld=_private_dir(stage/'rule');_private_dir(fld/'events')
  _exclusive_json(fld/'lock.json',data['rule_lock'])
  for n,item in enumerate(data['rule_events'],1):
   require(item['name'].startswith(f'{n:06d}_') and item['name'].endswith('.json'),'RULE_FIFTH_BAD_EVENT_NAME')
   _exclusive_json(fld/'events'/item['name'],item['content'])
  fifth=RuleRecheck29(third,fld)
  require(fifth.head==data['fifth_head'] and sha256(canonical(fifth.status()))==data['fifth_status_sha256'] and fifth.status()['cases_reviewed']==29,'RULE_FIFTH_STATUS_INVALID')
  result=fifth.status();os.rename(stage,dst)
 except Exception:
  if stage.exists():shutil.rmtree(stage)
  raise
 return {'archive_sha256':sha256(blob),'five_ledger_chains_replayed':True,
 'previous_four_chain_head':result['previous_four_chain_head'],
 'fifth_chain_head':result['current_fifth_chain_head'],
 'official_risks_rechecked':result['official_cases_reviewed'],
 'asr_cues_rechecked':result['asr_cases_reviewed'],
 'remaining_open':92,'independent_financial_facts_approved':0,'advice_approved':False}
