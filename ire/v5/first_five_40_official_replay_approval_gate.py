"""Offline replay of official-site *extractions* and fail-closed knowledge approval.

No ChatGPT or GitHub CI job can assert a government signature from a third-party
markdown extraction. The pinned official-site capture is reproducible as a Git
object; legal-currentness and independent professional review are distinct.

A cryptographic two-role approval certificate can pass only under a trusted,
externally verified reviewer registry fingerprint. This repository intentionally
contains neither reviewer private keys nor a pre-approved fingerprint.
"""
from __future__ import annotations

import argparse
import base64
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .first_five_40_formal_approval_b04_gate import verify as original_b04_verify

SCHEMA='IRE_V5_FIRST40_OFFICIAL_EXTRACT_REPLAY_MANIFEST_V1'
CERT_SCHEMA='IRE_V5_NARROW_EDUCATION_FACT_DUAL_SIGNATURE_V1'
REGISTRY_SCHEMA='IRE_V5_EXTERNAL_REVIEWER_TRUST_REGISTRY_V1'
MANIFEST='ire/v5/validation/first_five_40_official_replay_manifest_20261106.json'
SCOPE='ire/v5/validation/first_five_40_scoped_fact_knowledge_review_20261106.json'
RESOLVED='ire/v5/validation/first_five_40_open5_resolution_20261106.json'
B04='ire/v5/legacy_consolidation/B04_FIRST40_SCOPED_EDUCATION_EDGES_20261106.json'
MASTER='data/claims.jsonl'
MASTER_SHA='ab5af7eea02e65d5e36174546a2a94f4cc642d92'
EVENT_SHA='9f0685b2b1f8b95c2eefa7708e8ae1ad8d1bd567d40e84e1d6b2d04aed81874e'
SRT_SHA='2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f'
CUTOFF=date(2026,11,6)
# Immutable independently content-addressed Git source-objects and SHA256 values.
# Editing the manifest *and* a document still fails until this reviewed code
# contract is changed and the new manifest/substantive analysis is re-examined.
PINS={
 'NTS_RATE2026':('6682bd34bc3b19bc01987cd84ddc8370e944828c','b1d29ab375ed2d3d79d639a945c70c82a1a19fa3f8f044f581a20ca8c91f3145'),
 'LAW_129':('72b7f3371eb50b84fd40386356d2ec6c7d3122ff','6ff82892fcc7a0dd87a1aaa78717ee3881499478248b5f7aa62224f26cfe4c8d'),
 'LAW_14':('9ebc690cd8d74f94e9ec5b71f288880fec53c361','367c4bd67124340fbb60bcd444e89008b9348495d38353ca80fb7167379faac1'),
 'LAW_40':('6d34574d7f26fcfe0cd7ea4637244ee812dd3cf1','e7f5654d24aaa5672e87cdb128d82f7239cc8e5bc4241288faa4d78c0fcb8eaa'),
 'LAW_55':('d3d7a88072329d2d85bad0d49f5c54887151747a','cc12a28e03393d32b4e868b53b6ed32f4c1b5740e178b4329a5034071ca0e558'),
 'NPS_TAX_FAQ':('90e64ec704d7c724cab9d4048fa851a591468f35','8399d972dd15a1a77b62a50d571b0f33d3e557a86cc8d0a6fec4383f9a9de695'),
 'NTS_TAXBRACKET':('fbddaf1171ae4aa1afc9e86779061944f6feb08b','8deb5b313ff8e0710e38d949f4b1031b62ae00a25c9ce19dc3e05c659e716697'),
 'NPS_RETRO':('b220913d10001a1f9eb866c4206a2f6130248af9','f62edf1c8b0dde315a9a16bb4e51a35a60017ec49efab4e4499788940e4649dd'),
 'NPS_CPI':('8a80893644ff949c57298c336879ee2a3f10acbd','edef4cbb62799f30cbd3dc647f865874cd98d83d1623181cd6221dd629665f67'),
 'NPS_PAY':('34b350242fcd8cd3830d782ce30bdab029d6ba25','1bdd315628ea626625fbadab1f3144d4122efd353b81155746115628a69372cd'),
 'NPS_DELAY':('8a80893644ff949c57298c336879ee2a3f10acbd','edef4cbb62799f30cbd3dc647f865874cd98d83d1623181cd6221dd629665f67'),
 'LAW_WITHDRAW':('166bd16491c1ac7fd71d63b4a1ae604ca806577c','b3409924d32934e5d81b8514b978209c9c1fdaccf423a3ae6b56d6b349158e9d'),
 'LAW_CREDIT':('3e97ee4be42a3309954f08beda996feb733a99f6','9704c663839a20d30a0699bb5f1492dbb149d8f492459a1b23b542cb94a307e0'),
 'NTS_CREDIT':('c63449bc534f0aaeec7bec3b770fe5329b8fc826','3858ca70d034869fee1f7b405c448bcd2ff939ff8fa601753664b075a39f6807'),
 'LAW_FIN2000':('4e4cdb75f705877820e087b6bfbf70e96ef62d41','fe79302441a2b9d8f09b8af5948432bb02f86c45edbeb2a1b3012b0d8096ce88')}
TRUSTED_HOSTS={'www.law.go.kr','law.go.kr','www.nts.go.kr','nts.go.kr','www.nps.or.kr','nps.or.kr','m.nps.or.kr'}
OPEN5={'V5C0266','V5C0267','V5C0287','V5C0405','V5C0430'}

class ApprovalGateError(ValueError):
 pass

def need(condition,code):
 if not condition:raise ApprovalGateError(code)

def canonical(obj):
 return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def sha256(raw):return hashlib.sha256(raw).hexdigest()

def git_blob_sha1(raw):
 return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def _json(path):
 with open(path,encoding='utf-8') as stream:return json.load(stream)

def _snapshot_bytes(root,entry):
 sid=entry.get('authority_id')
 need(sid in PINS,'UNREGISTERED_OFFICIAL_EXTRACT')
 expected_path=f'ire/v5/validation/official_extracts_20261106/{sid}.md'
 need(entry.get('snapshot_path')==expected_path,'EXTRACT_PATH_NOT_APPROVED')
 url=entry.get('official_url','')
 parsed=urlsplit(url)
 need(parsed.scheme=='https' and parsed.hostname in TRUSTED_HOSTS and not parsed.username and not parsed.password,
      'EXTRACT_SOURCE_NOT_OFFICIAL_DOMAIN')
 need(entry.get('source_status_reported')==200 and entry.get('capture_date')=='2026-11-06'
      and entry.get('capture_type')=='THIRD_PARTY_FIRECRAWL_OFFICIAL_URL_MARKDOWN_EXTRACTION_NOT_GOVERNMENT_SIGNED_OR_HTTP_RAW',
      'SOURCE_CAPTURE_PROVENANCE_MISSTATED')
 expected_git,expected_sha=PINS[sid]
 need(entry.get('snapshot_sha256')==expected_sha and entry.get('snapshot_git_blob_sha1')==expected_git,
      'EXTRACT_PIN_CHANGED_IN_MANIFEST')
 absolute=(root/expected_path)
 need(absolute.is_file() and not absolute.is_symlink(),'EXTRACT_MISSING_OR_SYMLINK')
 blob=absolute.read_bytes()
 need(git_blob_sha1(blob)==expected_git and sha256(blob)==expected_sha,
      'OFFICIAL_EXTRACT_CONTENT_TAMPERED')
 content=blob.decode('utf-8')
 anchors=entry.get('expected_literal_anchors')
 need(type(anchors) is list and len(anchors)>=2 and all(type(s) is str and len(s)>=2 and s in content for s in anchors),
      'OFFICIAL_EXTRACT_ANCHOR_MISSING')
 if sid.startswith('LAW_'):
  effect=entry.get('effective_date_or_guidance_observed')
  need(effect in {'2026-07-01','2026-10-01'},'LAW_EFFECTIVE_DATE_NOT_LOCKED')
  normalized=content.replace('\\','')
  expected='시행 2026. 10. 1.' if effect=='2026-10-01' else '시행 2026. 7. 1.'
  need(expected in normalized,'LAW_EXTRACT_EFFECTIVE_VERSION_MISMATCH')
 else:
  need(entry.get('effective_date_or_guidance_observed')=='GUIDANCE_CURRENT_2026-11-06',
       'INSTITUTIONAL_GUIDANCE_NOT_STATUTE_EFFECTIVE_DATE')
 return {'authority_id':sid,'sha256':expected_sha,'blob_sha1':expected_git,
         'bytes':len(blob),'offline_replay':'PASS',
         'capture_kind':'THIRD_PARTY_SITE_EXTRACT_NOT_RAW_OFFICIAL_BYTES'}

def verify_source_claim_bundle(manifest,scope,resolution,b04):
 need(manifest.get('schema')==SCHEMA and manifest.get('observed_as_of')=='2026-11-06'
      and manifest.get('source_window_scope')==40 and manifest.get('source_claims_scope')==97
      and manifest.get('regulatory_claims_scope')==20,'FIRST40_MANIFEST_SCOPE_DRIFT')
 need(manifest.get('source_event_head_sha256')==EVENT_SHA
      and manifest.get('source_srt_sha256')==SRT_SHA
      and manifest.get('prior_master_git_blob_sha1')==MASTER_SHA,
      'FIRST40_SOURCE_OR_MASTER_ANCHOR_CHANGED')
 need(manifest.get('formal_knowledge_release_policy')=='TWO_INDEPENDENT_ED25519_SIGNERS_WITH_OUT_OF_BAND_TRUST_REGISTRY_ONLY'
      and manifest.get('formal_b04_master_merges_published')==0
      and manifest.get('fact_approval_records_published')==0
      and manifest.get('full_speaker_claims_automatically_approved')==0
      and manifest.get('personal_investment_advice_approved') is False,
      'FIRST40_UNAUTHORIZED_APPROVAL_FLAG')
 snaps=manifest.get('snapshots');mp=manifest.get('regulatory_claim_narrow_source_map')
 need(type(snaps) is list and len(snaps)==15 and {s.get('authority_id') for s in snaps}==set(PINS),
      'FIRST40_AUTHORITY_CENSUS_CHANGED')
 claims=scope.get('claims')
 need(type(claims) is list and len(claims)==97 and len({x.get('claim_id') for x in claims})==97,
      'FIRST40_CLAIM_CENSUS_CHANGED')
 rule={x['claim_id']:x for x in claims if x.get('kind')=='RULE'}
 need(len(rule)==20 and type(mp) is dict and set(mp)==set(rule),
      'FIRST40_RULE_MAP_CENSUS_CHANGED')
 for cid,claim in rule.items():
  ids=mp[cid]
  need(type(ids) is list and bool(ids) and len(set(ids))==len(ids) and set(ids)<=set(PINS),
       'RULE_NOT_ANCHORED_TO_PINNED_OFFICIAL_EXTRACT')
  need(re.fullmatch('V5C[0-9]{4}',cid) and re.fullmatch('[a-f0-9]{64}',claim['claim_payload_sha256']) is not None
       and claim.get('entire_video_claim_approved') is False
       and claim.get('personal_application_approved') is False,
       'WHOLE_CLAIM_FACT_OR_PERSONAL_ADVICE_WRONGFULLY_APPROVED')
  if cid in OPEN5:
   need(claim.get('review_status')=='REGULATORY_COMPOSITE_OPEN',
        'OPEN_COMPOSITE_HISTORICAL_STATE_REWRITTEN')
  else:
   need(claim.get('review_status')=='OFFICIAL_NARROW_SUBFACT_VERIFIED'
        and type(claim.get('narrow_approved_subfact')) is str and len(claim['narrow_approved_subfact'])>=12,
        'PRIOR_NARROW_CANDIDATE_REWRITTEN')
 need(resolution.get('unresolved_5_review_dispositions_remaining')==0
      and {x['claim_id'] for x in resolution.get('open_five_review_outcomes',[])}==OPEN5,
      'FIVE_REVIEW_DISPOSITION_OR_SCOPE_CHANGED')
 need(scope.get('reviewed_claims_count')==97 and scope.get('reviewed_rule_claims_count')==20
      and scope.get('video1_20to40_event_head_sha256')==EVENT_SHA,
      'FIRST40_SCOPE_EVENT_ANCHOR_DRIFT')
 need(b04.get('B04_authorized_scoped_education_edges_count')==6
      and len(b04.get('B04_scoped_education_edges',[]))==6
      and len(b04.get('cross_batch_edges_not_promoted_here',[]))==9
      and b04.get('B04_formal_master_fact_merge_completed') is False,
      'B04_MASTER_OUT_OF_SCOPE_OR_UNAUTHORIZED_MERGE')
 return rule

def source_packet_digest(manifest,rule):
 return sha256(canonical({'schema':'IRE_V5_FIRST40_EXTRACT_PACKET_V1',
                         'snapshots':{x['authority_id']:x['snapshot_sha256'] for x in manifest['snapshots']},
                         'claim_sources':manifest['regulatory_claim_narrow_source_map'],
                         'claim_refs':{x['claim_id']:x['source_cue_refs_sha256'] for x in rule.values()},
                         'legacy_master':MASTER_SHA,'event':EVENT_SHA}))

def verify_signed_certificate(certificate,trust_registry,expected_registry_sha256,
                              *,claim,authority_sha256_by_id,evidence_packet_sha256,
                              relation_prior_targets,as_of=CUTOFF):
 """Verify a *potential* formal narrow knowledge decision from two enrolled roles.

 It only validates cryptographic chain and narrowed scope; it cannot establish
 that the real-world signer is independent or that legal interpretation is true.
 The expected registry digest must be pre-approved OUT OF BAND by the operator.
 """
 from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
 need(type(expected_registry_sha256) is str and re.fullmatch('[a-f0-9]{64}',expected_registry_sha256),
      'NO_EXTERNALLY_PINNED_TRUST_ROOT')
 need(type(trust_registry) is dict and sha256(canonical(trust_registry))==expected_registry_sha256,
      'UNTRUSTED_OR_MUTATED_REVIEWER_REGISTRY')
 need(trust_registry.get('schema')==REGISTRY_SCHEMA,'UNTRUSTED_REGISTRY_SCHEMA')
 keys=trust_registry.get('reviewers')
 need(type(keys) is list and len(keys)>=2 and len({k.get('id') for k in keys})==len(keys),
      'TRUSTED_REVIEWERS_NOT_DISTINCT')
 trusted={x['id']:x for x in keys}
 need(type(certificate) is dict and set(certificate)=={'body','signatures'},'CERT_STRUCTURE_INVALID')
 body=certificate['body']
 need(type(body) is dict and body.get('schema')==CERT_SCHEMA
      and body.get('claim_id')==claim['claim_id']
      and body.get('video_cue_refs_sha256')==claim['source_cue_refs_sha256']
      and body.get('evidence_packet_sha256')==evidence_packet_sha256
      and body.get('official_extract_sha256_by_id')==authority_sha256_by_id
      and body.get('prior_master_git_blob_sha1')==MASTER_SHA,
      'CERT_NOT_BOUND_TO_CURRENT_VIDEO_EVIDENCE_OR_MASTER')
 need(body.get('decision')=='APPROVE_NARROW_GENERAL_EDUCATION_FACT_ONLY'
      and body.get('whole_speaker_claim_approved') is False
      and body.get('individual_tax_calculation_approved') is False
      and body.get('personal_investment_advice_approved') is False
      and body.get('automatic_master_rewrite') is False,
      'CERT_UNSAFE_APPROVAL_SCOPE')
 if claim['claim_id'] in OPEN5:
  need(body.get('approved_narrow_fact')==claim['legally_supported_narrow_scope'],
       'CERT_NARROW_FACT_CHANGED')
 else:
  need(body.get('approved_narrow_fact')==claim['narrow_approved_subfact'],
       'CERT_NARROW_FACT_CHANGED')
 need(body.get('legacy_relation_targets')==relation_prior_targets,
      'CERT_PRIOR_RELATION_NOT_ADJUDICATED')
 issued=body.get('issued_on');expires=body.get('expires_on')
 try:issued_date=date.fromisoformat(issued);expire_date=date.fromisoformat(expires)
 except (TypeError,ValueError):raise ApprovalGateError('CERT_DATE_INVALID')
 need(issued_date<=as_of<=expire_date and expire_date<=date(2027,11,6),
      'CERT_EXPIRED_FUTURE_OR_EXCESSIVE_VALIDITY')
 signatures=certificate['signatures']
 need(type(signatures) is list and len(signatures)==2
      and len({s.get('reviewer_id') for s in signatures})==2,'CERT_SIGNERS_NOT_INDEPENDENT')
 signed=canonical(body);roles=[]
 for sig in signatures:
  reviewer=trusted.get(sig.get('reviewer_id'))
  need(reviewer is not None and reviewer.get('out_of_band_identity_vetted') is True
       and reviewer.get('role') in {'LEGAL_EVIDENCE_REVIEWER','KNOWLEDGE_INTEGRATION_STEWARD'},
       'CERT_REVIEWER_NOT_VETTED_OR_ROLE_INVALID')
  try:
   public=base64.b64decode(reviewer['ed25519_public_key_b64'],validate=True)
   signature=base64.b64decode(sig['ed25519_signature_b64'],validate=True)
   need(len(public)==32 and len(signature)==64,'CERT_KEY_OR_SIGNATURE_LENGTH')
   Ed25519PublicKey.from_public_bytes(public).verify(signature,signed)
  except (ValueError,KeyError,TypeError) as exc:
   raise ApprovalGateError('CERT_PUBLIC_KEY_OR_SIGNATURE_INVALID') from exc
  except Exception as exc:
   raise ApprovalGateError('CERT_SIGNATURE_VERIFICATION_FAILED') from exc
  roles.append(reviewer['role'])
 need(set(roles)=={'LEGAL_EVIDENCE_REVIEWER','KNOWLEDGE_INTEGRATION_STEWARD'},
      'CERT_MISSING_DISTINCT_INDEPENDENT_ROLES')
 return {'authorized_for_scoped_educational_knowledge':True,
         'authorized_for_whole_original_claim':False,
         'authorized_for_personal_financial_advice':False,
         'authorized_for_automatic_legacy_master_rewrite':False,
         'claim_id':claim['claim_id'],'signatures_verified':2}

def review_private_signed_decisions(root:Path,registry_file:Path|None=None,
                                    registry_trust_anchor_sha256:str|None=None,
                                    decision_directory:Path|None=None):
 """Review an optional independent decision inbox, without rewriting old data.

 The trust-anchor fingerprint must be provided by a separately authorized
 operator, never read from the signed certificate or an untrusted repository
 manifest. No credentials or certificates are generated by this module.
 """
 if registry_file is None and registry_trust_anchor_sha256 is None and decision_directory is None:
  return {'eligible_scoped_facts_approved':0,'decision_status':'NO_EXTERNAL_TRUST_ANCHOR_OR_REVIEWER_SIGNATURES',
          'automatic_B04_master_merge':False}
 need(registry_file is not None and registry_trust_anchor_sha256 is not None
      and decision_directory is not None,'PARTIAL_EXTERNAL_APPROVAL_AUTHORITY_REJECTED')
 regfile=Path(registry_file);inbox=Path(decision_directory)
 need(regfile.is_file() and inbox.is_dir() and not regfile.is_symlink() and not inbox.is_symlink(),
      'EXTERNAL_APPROVAL_FILES_MISSING_OR_SYMLINKED')
 root=Path(root).resolve()
 m=_json(root/MANIFEST);scope=_json(root/SCOPE);resolution=_json(root/RESOLVED);b04=_json(root/B04)
 rules=verify_source_claim_bundle(m,scope,resolution,b04)
 trusted=_json(regfile)
 packet=source_packet_digest(m,rules)
 five={r['claim_id']:r for r in resolution['open_five_review_outcomes']}
 accepted=[]
 for certpath in sorted(inbox.glob('*.json')):
  need(not certpath.is_symlink(),'APPROVAL_CERT_SYMLINK')
  cert=_json(certpath);body=cert.get('body',{})
  cid=body.get('claim_id') if type(body) is dict else None
  need(cid in rules and cid not in accepted,'UNKNOWN_OR_DUPLICATED_APPROVAL_CLAIM')
  claim=rules[cid].copy()
  if cid in five:
   claim['legally_supported_narrow_scope']=five[cid]['legally_supported_narrow_scope']
   related=five[cid]['legacy_prior_ids']
  else:
   related=claim['existing_prior_candidates']
  sources={s:next(x for x in m['snapshots'] if x['authority_id']==s)['snapshot_sha256']
           for s in m['regulatory_claim_narrow_source_map'][cid]}
  verify_signed_certificate(cert,trusted,registry_trust_anchor_sha256,
                            claim=claim,authority_sha256_by_id=sources,
                            evidence_packet_sha256=packet,relation_prior_targets=related)
  accepted.append(cid)
 return {'eligible_scoped_facts_approved':len(accepted),'approved_claim_ids':accepted,
         'decision_status':'INDEPENDENT_TWO_ROLE_SIGNATURES_CRYPTOGRAPHICALLY_VERIFIED',
         'automatic_B04_master_merge':False,
         'personal_investment_advice_approved':False}

def verify(root:Path,*,read_snapshots=True,reviewer_registry:Path|None=None,
           reviewer_registry_sha256:str|None=None,decision_directory:Path|None=None):
 root=Path(root).resolve()
 master=root/MASTER
 need(master.is_file() and git_blob_sha1(master.read_bytes())==MASTER_SHA,
      'PRIOR_MASTER_116_CHANGED')
 # Inherit 17 tests of prior scope protection; no source rewrite is made.
 previous=original_b04_verify(root)
 manifest=_json(root/MANIFEST);old=_json(root/SCOPE)
 resolved=_json(root/RESOLVED);b04=_json(root/B04)
 rule=verify_source_claim_bundle(manifest,old,resolved,b04)
 independent=review_private_signed_decisions(root,reviewer_registry,reviewer_registry_sha256,decision_directory)
 extracts=[]
 if read_snapshots:
  for entry in manifest['snapshots']:
   extracts.append(_snapshot_bytes(root,entry))
 need(len(extracts)==15 if read_snapshots else True,'OFFICIAL_EXTRACT_COUNT_CHANGED')
 return {'schema':'IRE_V5_FIRST40_OFFICIAL_SOURCE_REPLAY_AND_DUAL_APPROVAL_POLICY_V1',
         'official_source_extraction_snapshots_replayed':len(extracts),
         'unique_snapshot_payloads':len({x['sha256'] for x in extracts}),
         'regulated_video_claims_with_source_scope_link':len(rule),
         'prior_narrow_rule_candidates_rechecked':15,
         'five_formerly_open_terminal_review_records_rechecked':5,
         'non_regulatory_97_claims_not_promoted':77,
         'scope40_source_immutable_event_head':EVENT_SHA,
         'evidence_packet_sha256':source_packet_digest(manifest,rule),
         'b04_education_only_edges_retained':previous['b04_scope_accepted_education_edges'],
         'outside_b04_edges_retained':previous['outside_b04_links_unmerged'],
         'verified_offline_proof_kind':'PINNED_THIRD_PARTY_OFFICIAL_SITE_MARKDOWN_EXTRACT_NOT_GOVERNMENT_SIGNED',
         'government_raw_signed_source_bytes_verified':False,
         'externally_vetted_approval_keys_registered_in_this_repository':False,
         'actual_dual_signed_legal_knowledge_approvals':independent['eligible_scoped_facts_approved'],
         'independent_approval_decision':independent['decision_status'],
         'formal_B04_master_merges':0,
         'entire_original_claims_approved':0,
         'personal_financial_advice_release':'NO_GO',
         'research_closure':'BLOCKED_40_OF_288_CUE_REVIEWED'}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,default=Path('.'))
 parser.add_argument('--reviewer-registry',type=Path)
 parser.add_argument('--reviewer-registry-sha256')
 parser.add_argument('--decision-directory',type=Path)
 args=parser.parse_args()
 print(json.dumps(verify(args.root,reviewer_registry=args.reviewer_registry,
                         reviewer_registry_sha256=args.reviewer_registry_sha256,
                         decision_directory=args.decision_directory),sort_keys=True,ensure_ascii=False))

if __name__=='__main__':main()
