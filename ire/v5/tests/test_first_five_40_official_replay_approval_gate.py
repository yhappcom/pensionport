"""Adversarial offline legal-extract replay and signed narrow-knowledge gate tests."""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from ire.v5 import first_five_40_official_replay_approval_gate as gate

BASE=Path(__file__).resolve().parents[1]

class First40ReproFactsTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=json.loads((BASE/'validation/first_five_40_official_replay_manifest_20261106.json').read_text('utf-8'))
  cls.scope=json.loads((BASE/'validation/first_five_40_scoped_fact_knowledge_review_20261106.json').read_text('utf-8'))
  cls.resolution=json.loads((BASE/'validation/first_five_40_open5_resolution_20261106.json').read_text('utf-8'))
  cls.b04=json.loads((BASE/'legacy_consolidation/B04_FIRST40_SCOPED_EDUCATION_EDGES_20261106.json').read_text('utf-8'))
 def setUp(self):
  self.m=copy.deepcopy(self.manifest);self.s=copy.deepcopy(self.scope)
  self.r=copy.deepcopy(self.resolution);self.b=copy.deepcopy(self.b04)
 def check(self):return gate.verify_source_claim_bundle(self.m,self.s,self.r,self.b)
 def test_20_regulatory_claims_97_claims_15_extract_pins(self):
  rule=self.check();self.assertEqual(len(rule),20)
  self.assertEqual(len(self.m['snapshots']),15)
  self.assertEqual(len({x['snapshot_sha256'] for x in self.m['snapshots']}),14)
  self.assertEqual(set(self.m['regulatory_claim_narrow_source_map']),set(rule))
 def test_source_packet_sha_is_stable(self):
  self.assertEqual(gate.source_packet_digest(self.m,self.check()),'4bf476073e339186bfe5ecaa0957da672999bcce043b84b9c64eb3cfcc4d08ee')
 def test_reject_new_unreviewed_rule_claim(self):
  self.m['regulatory_claim_narrow_source_map']['V5C9999']=['LAW_55']
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_RULE_MAP_CENSUS_CHANGED'):self.check()
 def test_reject_removing_rule_from_mapping(self):
  self.m['regulatory_claim_narrow_source_map'].pop('V5C0266')
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_RULE_MAP_CENSUS_CHANGED'):self.check()
 def test_reject_nonofficial_source(self):
  self.m['snapshots'][0]['official_url']='https://not-a-gov.example/statement'
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(gate.ApprovalGateError,'EXTRACT_SOURCE_NOT_OFFICIAL_DOMAIN'):
    gate._snapshot_bytes(Path(d),self.m['snapshots'][0])
 def test_reject_unsafe_snapshot_path(self):
  self.m['snapshots'][0]['snapshot_path']='../../etc/passwd'
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(gate.ApprovalGateError,'EXTRACT_PATH_NOT_APPROVED'):
    gate._snapshot_bytes(Path(d),self.m['snapshots'][0])
 def test_reject_fake_HTTP_authenticity_or_capture_kind(self):
  self.m['snapshots'][0]['capture_type']='GOVERNMENT_SIGNED_ORIGINAL'
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(gate.ApprovalGateError,'SOURCE_CAPTURE_PROVENANCE_MISSTATED'):
    gate._snapshot_bytes(Path(d),self.m['snapshots'][0])
 def test_reject_change_of_snapshot_pin(self):
  self.m['snapshots'][0]['snapshot_sha256']='0'*64
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(gate.ApprovalGateError,'EXTRACT_PIN_CHANGED_IN_MANIFEST'):
    gate._snapshot_bytes(Path(d),self.m['snapshots'][0])
 def test_reject_unauthorized_fact_flag(self):
  self.m['fact_approval_records_published']=1
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_UNAUTHORIZED_APPROVAL_FLAG'):self.check()
 def test_reject_unauthorized_master_merge(self):
  self.m['formal_b04_master_merges_published']=1
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_UNAUTHORIZED_APPROVAL_FLAG'):self.check()
 def test_reject_personal_advice(self):
  self.m['personal_investment_advice_approved']=True
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_UNAUTHORIZED_APPROVAL_FLAG'):self.check()
 def test_source_cue_fingerprint_not_approvable(self):
  c=next(x for x in self.s['claims'] if x['claim_id']=='V5C0266')
  c['entire_video_claim_approved']=True
  with self.assertRaisesRegex(gate.ApprovalGateError,'WHOLE_CLAIM_FACT_OR_PERSONAL_ADVICE_WRONGFULLY_APPROVED'):self.check()
 def test_reject_97_count_drift(self):
  self.s['claims'].pop()
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_CLAIM_CENSUS_CHANGED'):self.check()
 def test_reject_forged_prior_master(self):
  self.m['prior_master_git_blob_sha1']='9'*40
  with self.assertRaisesRegex(gate.ApprovalGateError,'FIRST40_SOURCE_OR_MASTER_ANCHOR_CHANGED'):self.check()
 def test_reject_b04_wrong_claim_merge(self):
  self.b['B04_formal_master_fact_merge_completed']=True
  with self.assertRaisesRegex(gate.ApprovalGateError,'B04_MASTER_OUT_OF_SCOPE_OR_UNAUTHORIZED_MERGE'):self.check()

class DualIndependentSignatureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=json.loads((BASE/'validation/first_five_40_scoped_fact_knowledge_review_20261106.json').read_text('utf-8'))
  cls.res=json.loads((BASE/'validation/first_five_40_open5_resolution_20261106.json').read_text('utf-8'))
  cls.manifest=json.loads((BASE/'validation/first_five_40_official_replay_manifest_20261106.json').read_text('utf-8'))
 def setUp(self):
  c=next(c for c in self.old['claims'] if c['claim_id']=='V5C0266')
  r=next(x for x in self.res['open_five_review_outcomes'] if x['claim_id']=='V5C0266')
  self.claim={**c,'legally_supported_narrow_scope':r['legally_supported_narrow_scope']}
  self.a={id:next(s for s in self.manifest['snapshots'] if s['authority_id']==id)['snapshot_sha256'] for id in r['official_authority_ids']}
  self.packet='4bf476073e339186bfe5ecaa0957da672999bcce043b84b9c64eb3cfcc4d08ee'
  self.k1=Ed25519PrivateKey.generate();self.k2=Ed25519PrivateKey.generate()
  def entry(id,role,key):
   pub=key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
   return {'id':id,'role':role,'out_of_band_identity_vetted':True,'ed25519_public_key_b64':base64.b64encode(pub).decode('ascii')}
  self.registry={'schema':gate.REGISTRY_SCHEMA,'reviewers':[entry('legal-checker','LEGAL_EVIDENCE_REVIEWER',self.k1),entry('knowledge-owner','KNOWLEDGE_INTEGRATION_STEWARD',self.k2)]}
  self.registry_digest=gate.sha256(gate.canonical(self.registry))
  self.body={'schema':gate.CERT_SCHEMA,'claim_id':'V5C0266',
       'video_cue_refs_sha256':self.claim['source_cue_refs_sha256'],
       'official_extract_sha256_by_id':self.a,'evidence_packet_sha256':self.packet,
       'prior_master_git_blob_sha1':gate.MASTER_SHA,
       'decision':'APPROVE_NARROW_GENERAL_EDUCATION_FACT_ONLY',
       'approved_narrow_fact':r['legally_supported_narrow_scope'],
       'whole_speaker_claim_approved':False,'individual_tax_calculation_approved':False,
       'personal_investment_advice_approved':False,'automatic_master_rewrite':False,
       'legacy_relation_targets':['GOMHEE-C21','GOMHEE-C42'],
       'issued_on':'2026-11-06','expires_on':'2027-01-01'}
  self.make_cert()
 def make_cert(self):
  payload=gate.canonical(self.body)
  self.cert={'body':copy.deepcopy(self.body),'signatures':[
       {'reviewer_id':'legal-checker','ed25519_signature_b64':base64.b64encode(self.k1.sign(payload)).decode()},
       {'reviewer_id':'knowledge-owner','ed25519_signature_b64':base64.b64encode(self.k2.sign(payload)).decode()}]}
 def check(self):
  return gate.verify_signed_certificate(self.cert,self.registry,self.registry_digest,claim=self.claim,
                                         authority_sha256_by_id=self.a,evidence_packet_sha256=self.packet,
                                         relation_prior_targets=['GOMHEE-C21','GOMHEE-C42'])
 def test_valid_two_independently_keyed_synthetic_signers_narrow_scope_only(self):
  x=self.check();self.assertTrue(x['authorized_for_scoped_educational_knowledge'])
  self.assertFalse(x['authorized_for_automatic_legacy_master_rewrite'])
  self.assertFalse(x['authorized_for_personal_financial_advice'])
 def test_unpinned_registry_never_authorizes(self):
  with self.assertRaisesRegex(gate.ApprovalGateError,'NO_EXTERNALLY_PINNED_TRUST_ROOT'):
   gate.verify_signed_certificate(self.cert,self.registry,None,claim=self.claim,
                                authority_sha256_by_id=self.a,evidence_packet_sha256=self.packet,
                                relation_prior_targets=['GOMHEE-C21','GOMHEE-C42'])
 def test_forged_or_changed_registry(self):
  self.registry['reviewers'][0]['role']='KNOWLEDGE_INTEGRATION_STEWARD'
  with self.assertRaisesRegex(gate.ApprovalGateError,'UNTRUSTED_OR_MUTATED_REVIEWER_REGISTRY'):self.check()
 def test_claim_change_breaks_certificate(self):
  self.cert['body']['approved_narrow_fact']='All pension returns are guaranteed'
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_NARROW_FACT_CHANGED'):self.check()
 def test_signature_change_breaks_certificate(self):
  self.cert['signatures'][0]['ed25519_signature_b64']=base64.b64encode(b'Z'*64).decode()
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_SIGNATURE_VERIFICATION_FAILED'):self.check()
 def test_missing_second_review(self):
  self.cert['signatures'].pop()
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_SIGNERS_NOT_INDEPENDENT'):self.check()
 def test_duplicate_signature_identity(self):
  self.cert['signatures'][1]['reviewer_id']='legal-checker'
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_SIGNERS_NOT_INDEPENDENT'):self.check()
 def test_change_legal_scope_cannot_reuse_signatures(self):
  self.cert['body']['personal_investment_advice_approved']=True
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_UNSAFE_APPROVAL_SCOPE'):self.check()
 def test_changed_source_extraction_sha(self):
  self.cert['body']['official_extract_sha256_by_id']['LAW_129']='0'*64
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_NOT_BOUND_TO_CURRENT_VIDEO_EVIDENCE_OR_MASTER'):self.check()
 def test_expired_signature(self):
  self.body['expires_on']='2026-01-01';self.make_cert()
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_EXPIRED_FUTURE_OR_EXCESSIVE_VALIDITY'):self.check()
 def test_excessive_validity(self):
  self.body['expires_on']='2030-01-01';self.make_cert()
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_EXPIRED_FUTURE_OR_EXCESSIVE_VALIDITY'):self.check()
 def test_wrong_prior_relation_not_approved(self):
  self.body['legacy_relation_targets']=['GOMHEE-C99'];self.make_cert()
  with self.assertRaisesRegex(gate.ApprovalGateError,'CERT_PRIOR_RELATION_NOT_ADJUDICATED'):self.check()

if __name__=='__main__':unittest.main()
