"""V105 blind independent gold protocol and strict NO-SCORE fallback.

Cryptographic source control and role segregation do not create independent
human reviewers. No gold is accepted absent externally verified reviewers.
Public repository ships NO original SRT or private reviewer annotation.
"""
from __future__ import annotations
import hashlib, json, re
from collections import defaultdict
from datetime import datetime,timezone

SCHEMA='V105_EXTERNAL_BLIND_GOLD_NOT_CREATED_V1'
ALLOWED_STANCES={'FACT_CANDIDATE','QUESTION','OPINION','HYPOTHESIS','CONDITION','EXCEPTION','REBUTTAL','UNCERTAIN'}
ALLOWED_RISK={'HIGH','MEDIUM','LOW','NONE'}

# V107: NO independently authenticated identity-authority roots are yet registered.
# An arbitrarily supplied 'verified_by_external_identity_authority=True' boolean
# and self-generated Ed25519 keys MUST NOT create alleged independent human gold.
# A verified authority root must be reviewed and pinned out-of-band before
# accepting real reviewer signatures (the empty set is a deliberate fail-close).
TRUSTED_IDENTITY_AUTHORITY_ROOT_PINS_SHA256=frozenset()

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def digest(x):return sha(canon(x))
def require(a,c):
 if not a:raise ValueError('V105_'+c)


def verify_externally_pinned_signature(payload, *, key_field='identity_authority_root_public_key_hex', signature_field='identity_authority_registry_signature_hex'):
 """Require a root whose SHA was approved out-of-band, then verify its signature.

 Never infer real-world human independence from self-issued flags. There are
 currently zero approved roots: all incoming alleged real gold fails closed.
 """
 require(type(payload) is dict,'EXTERNAL_ATTESTATION_TYPE')
 root=payload.get(key_field)
 require(type(root) is str and re.fullmatch('[0-9a-f]{64}',root) is not None,'NO_TRUSTED_AUTHORITY_ROOT')
 require(sha(bytes.fromhex(root)) in TRUSTED_IDENTITY_AUTHORITY_ROOT_PINS_SHA256,'SELF_ASSERTED_IDENTITY_AUTHORITY_BLOCKED')
 signature=payload.get(signature_field)
 require(type(signature) is str and re.fullmatch('[0-9a-f]{128}',signature) is not None,'UNSIGNED_EXTERNAL_ATTESTATION')
 try:
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
 except ImportError as exc:
  raise ValueError('V105_CRYPTO_SIGNATURE_VERIFIER_NOT_INSTALLED') from exc
 signed={k:v for k,v in payload.items() if k!=signature_field}
 try:
  Ed25519PublicKey.from_public_bytes(bytes.fromhex(root)).verify(bytes.fromhex(signature),canon(signed).encode('utf-8'))
 except Exception as exc:
  raise ValueError('V105_INVALID_ROOT_SIGNED_ATTESTATION') from exc
 return True

def lock_blind_cohort(lock,cues,*,source_archive_sha256, prior_windows):
 """Private source packet with all cues, including no-alert source, no predictions."""
 require(type(lock)==dict and lock.get('schema')=='V105_UNSEEN_OWNER_SOURCE_PRE_REVIEW_LOCK_V1','LOCK_SCHEMA')
 require(lock.get('source_zip_sha256')==source_archive_sha256 and re.fullmatch('[0-9a-f]{64}',source_archive_sha256),'ARCHIVE_PIN')
 require(type(prior_windows)==set,'PRIOR_SET')
 selections=lock.get('selected');require(type(selections)==list and len(selections)==4,'FOUR_WINDOWS')
 selection_keys={(w['video_id'],w['window_id']) for w in selections};require(len(selection_keys)==4 and not (selection_keys&prior_windows),'REVIEW_LEAK')
 require(lock.get('cue_count')==160 and lock.get('independent_gold') is False,'NO_FAKE_GOLD')
 seen=set();packet=[]
 for w in selections:
  v,win=w['video_id'],w['window_id'];rows=cues.get(v)
  require(type(rows)==list,'MISSING_SOURCE')
  fi,la=w['first_cue'],w['last_cue'];require(la-fi+1==40 and fi>=1,'SCOPE_40')
  source=rows[fi-1:la];require(len(source)==40,'SOURCE_40')
  require([x.index for x in source]==list(range(fi,la+1)),'SOURCE_SEQUENCE')
  require(sha(' '.join(x.text for x in source))==w['source_window_sha256'],'SOURCE_WINDOW_SHA')
  for x in source:
   key=(v,x.index);require(key not in seen,'CUE_REPEAT');seen.add(key)
   packet.append({'video_id':v,'window_id':win,'cue_index':x.index,'start_ms':x.start_ms,'end_ms':x.end_ms,'text_private':x.text,'cue_sha256':sha(x.text)})
 require(len(packet)==160,'SOURCE_TOTAL_160')
 # Returned packet is never public. Produce a source-only review question pack.
 return {'schema':SCHEMA,'owner_private_cues':packet,'blind_view':True,'prediction_disclosed':False,
         'independent_gold':False,'packet_sha256':digest([[r['video_id'],r['cue_index'],r['cue_sha256']] for r in packet]),
         'source_archive_sha256':source_archive_sha256,'p0_go':False}

def prepare_external_review_forms(lock, packet):
 """Distinct anonymous packets; neither includes model predictions or model annotations."""
 require(packet.get('schema')==SCHEMA and packet.get('prediction_disclosed') is False,'BLIND_PACK')
 cuekeys=[(r['video_id'],r['cue_index']) for r in packet['owner_private_cues']]
 require(len(cuekeys)==160 and len(set(cuekeys))==160,'SOURCE_COMPLETE')
 scope=digest(lock['selected']);frames=[]
 for slot in ('REVIEWER_A','REVIEWER_B'):
  frames.append({'review_slot':slot,'locked_scope_sha256':scope,'source_receipt_sha256':packet['packet_sha256'],
    'instructions':'Independently read all 160 cues, note every atomic financial claim and no-claim cue, stance/amount/period/condition/exception; no other review or prediction output.',
    'unreviewed_cues':160,'cue_verdict_template':[{'video_id':v,'cue_index':i,'status':'UNREVIEWED','atomic_ids':[]} for v,i in cuekeys],
    'claims_private':[],'reviewer_identity_not_attested':True,'predictions_disclosed':False,'independent_gold':False})
 return frames

def external_gold_gate(lock, packet, reviewer_a=None, reviewer_b=None, adjudication=None, *, trusted_registry=None):
 """Never score unless actual externally verified independent people and gold.

    trusted_registry is supplied by a separately authenticated process, not a
    self-asserted ChatGPT field; this module cannot verify human independence.
 """
 fields={'schema':SCHEMA,'independent_gold':False,'gold_locked':False,'precision':None,'recall':None,
         'high_risk_recall':None,'reason':'AWAIT_EXTERNAL_INDEPENDENT_REVIEWERS','p0_go':False}
 if any(x is None for x in (reviewer_a,reviewer_b,adjudication,trusted_registry)):
  return fields
 require(type(trusted_registry)==dict and trusted_registry.get('verified_by_external_identity_authority') is True,'UNVERIFIED_IDENTITY_REGISTRY')
 verify_externally_pinned_signature(trusted_registry)
 reviewer_ids=(reviewer_a.get('reviewer_id'),reviewer_b.get('reviewer_id'),adjudication.get('adjudicator_id'))
 require(all(type(r) is str and r in trusted_registry.get('verified_unique_people',[]) for r in reviewer_ids),'REVIEWER_NOT_EXTERNAL_VERIFIED')
 require(len(set(reviewer_ids))==3,'REVIEWER_COLLUSION_OR_DUP')
 require(all(r.get('prediction_disclosed') is False for r in (reviewer_a,reviewer_b,adjudication)),'PREDICTION_LEAK')
 require(all(r.get('source_receipt_sha256')==packet['packet_sha256'] for r in (reviewer_a,reviewer_b,adjudication)),'SOURCE_DRIFT')
 # Cryptographic verification is mandatory: unverified boolean attestations
 # never count as signatures. Human identity still requires external attestation.
 try:
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
 except ImportError:
  raise ValueError('V105_CRYPTO_SIGNATURE_VERIFIER_NOT_INSTALLED')
 verified_keys=trusted_registry.get('verified_public_key_hex_by_person',{})
 for rid,submission in zip(reviewer_ids,(reviewer_a,reviewer_b,adjudication)):
  pub=verified_keys.get(rid);sig=submission.get('signature_hex')
  require(type(pub) is str and len(pub)==64 and type(sig) is str and len(sig)==128,'UNVERIFIED_SIGNATURE')
  signed={k:v for k,v in submission.items() if k not in {'signature_hex','externally_authenticated_signature_verified'}}
  try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub)).verify(bytes.fromhex(sig),canon(signed).encode('utf-8'))
  except Exception as exc:
   raise ValueError('V105_INVALID_EXTERNAL_SIGNATURE') from exc

 source={(r['video_id'],r['cue_index']) for r in packet['owner_private_cues']}
 for r in (reviewer_a,reviewer_b):
  reviewed={(z['video_id'],z['cue_index']) for z in r.get('cue_verdicts',[])}
  require(len(r.get('cue_verdicts',[]))==len(source) and reviewed==source,'NOT_ALL_CUES_REVIEWED')
  require(all(z.get('status') in {'CLAIM','NO_FINANCIAL_CLAIM','OPEN_SOURCE_AUDIO'} for z in r['cue_verdicts']),'INVALID_CUE_STATUS')
  for claim in r.get('atomic_claims',[]):
   require(claim.get('stance') in ALLOWED_STANCES and claim.get('risk') in ALLOWED_RISK,'CLAIM_ROLE')
   require(set((r['video_id'],i) for i in claim.get('cue_indices',[]))<=source and len(claim.get('cue_indices',[]))>0,'CLAIM_SOURCE')
 require(adjudication.get('all_disagreements_resolved') is True and adjudication.get('gold_frozen_before_prediction_unseal') is True,'NOT_ADJUDICATED')
 require(type(adjudication.get('adjudicated_claims')) is list and adjudication.get('adjudicated_gold_sha256')==digest(adjudication['adjudicated_claims']),'GOLD_DIGEST')
 # Even with externally verified independent humans, confirm scoring protocol separately.
 return {'schema':SCHEMA,'independent_gold':True,'gold_locked':True,'gold_source_digest':digest(adjudication['adjudicated_claims']),
         'gold_count':len(adjudication['adjudicated_claims']),'precision':None,'recall':None,'high_risk_recall':None,
         'reason':'INDEPENDENT_GOLD_LOCKED_PREDICTION_COMPARISON_SEPARATE','p0_go':False}

def score_predictions(gold, predictions, *, independent_gate_receipt, equivalence_receipt, synthetic_arithmetic_only=False):
 """Score *only* externally adjudicated one-to-one semantic equivalences.

 Gold IDs and prediction IDs are from disjoint namespaces, so raw ID equality
 cannot be used as a TP; scope, stance and conditions require adjudication.
 """
 require(type(synthetic_arithmetic_only) is bool,'SYNTHETIC_FLAG_TYPE')
 if not synthetic_arithmetic_only:
  # Caller-supplied 'independent_gold=True' is NEVER sufficient proof.
  # The real-world authority MUST sign BOTH the gold gate and equivalence receipt.
  verify_externally_pinned_signature(independent_gate_receipt,
     signature_field='identity_authority_gold_gate_signature_hex')
  verify_externally_pinned_signature(equivalence_receipt,
     signature_field='identity_authority_equivalence_signature_hex')
 require(independent_gate_receipt.get('independent_gold') is True and independent_gate_receipt.get('gold_locked') is True,'GOLD_NOT_READY')
 require(independent_gate_receipt.get('gold_source_digest')==digest(gold),'GOLD_NOT_SAME')
 require(type(gold)==list and type(predictions)==list,'PRED_TYPE')
 def keys(seq):
  result={}
  for z in seq:
   k=z['atomic_id'];require(type(k) is str and k not in result,'DUP_ID')
   result[k]=z
  return result
 g=keys(gold);p=keys(predictions)
 require(type(equivalence_receipt)==dict and equivalence_receipt.get('external_adjudication_verified') is True,'EQUIVALENCE_NOT_ATTESTED')
 require(equivalence_receipt.get('gold_sha256')==digest(gold) and equivalence_receipt.get('prediction_sha256')==digest(predictions),'EQUIVALENCE_SOURCE_DRIFT')
 eq=equivalence_receipt.get('pairs');require(type(eq)==list,'EQUIVALENCE_NOT_LIST')
 seen_gold=set();seen_prediction=set()
 for row in eq:
  gi,pi=row.get('gold_atomic_id'),row.get('predicted_atomic_id')
  require(gi in g and pi in p and gi not in seen_gold and pi not in seen_prediction,'EQUIVALENCE_DUPLICATE_OR_OUT_OF_SCOPE')
  require(all(row.get(x) is True for x in ('semantically_equivalent','source_span_verified','stance_preserved','condition_exception_preserved','adjudicator_attested')),'EQUIVALENCE_NOT_SEMANTICALLY_APPROVED')
  seen_gold.add(gi);seen_prediction.add(pi)
 tp=len(seen_gold);fp=len(p)-len(seen_prediction);fn=len(g)-len(seen_gold)
 high_gold={k for k,z in g.items() if z.get('risk')=='HIGH'};h_fn=len(high_gold-seen_gold)
 # Test-only arithmetic is deliberately kept apart from real-world accuracy.
 scores={'precision':tp/(tp+fp) if tp+fp else None,
         'recall':tp/(tp+fn) if tp+fn else None,
         'high_risk_recall':(len(high_gold)-h_fn)/len(high_gold) if high_gold else None}
 if synthetic_arithmetic_only:
  return {'tp':tp,'fp':fp,'fn':fn,'high_risk_fn':h_fn,
          'synthetic_precision':scores['precision'],
          'synthetic_recall':scores['recall'],
          'synthetic_high_risk_recall':scores['high_risk_recall'],
          'precision':None,'recall':None,'high_risk_recall':None,
          'independent_gold_certified':False,'synthetic_arithmetic_only':True,
          'p0_go':False,'automatic_personal_advice_approved':False}
 return {'tp':tp,'fp':fp,'fn':fn,'high_risk_fn':h_fn,
         **scores,'independent_gold_certified':True,'synthetic_arithmetic_only':False,
         'p0_go':False,'automatic_personal_advice_approved':False}