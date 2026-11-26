import copy
import unittest
from unittest.mock import patch
from ire.v6.atomic_exchange import _digest_rows
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.knowledge_change import audit_knowledge_change, prepare_host_knowledge_change_review


class Store:
    def snapshot(self, scope_id):
        return {'ledger_head_sha256':'b'*64}


class KnowledgeReviewTests(unittest.TestCase):
    def setUp(self):
        self.atom={'claim_id':'C00001','proposition':'Original speaker text.',
                   'context_cue_indices':[1,2],'condition_cue_indices':[1],
                   'exception_cue_indices':[],'numeric_references':[],'as_of':None}
        typed={'relations':[{'type':'CONDITION','premise':[[1,0,3]]}]}
        self.native=[{'claim_id':'C00001','relationship':'OPEN','target_id':'old',
                      'target_content_sha256':'c'*64}]
        key=json_digest(self.native[0]); url='https://example.org/evidence'
        self.record={'exchange':{'atoms':[self.atom]},'ledger':{'quarantine_atoms':[],
                       'projection_rows':[{'claim_id':'C00001','typed_id':'A00001'}],
                       'authored':{'atoms':[typed]}}}
        self.plan={'schema':'IRE_V6_KNOWLEDGE_CHANGE_PLAN_V1',
                   'predecessor_event_sha256':'a'*64,'rows':[{'prior_row_sha256':key,
                   'native_atom_sha256':json_digest(self.atom),'operation':'CORRECT_SOURCE_CANDIDATE',
                   'reason':'Correct interpretation only.','evidence_urls':[url]}]}
        pin=audit_knowledge_change(self.record,self.record,'a'*64,_digest_rows(self.native),self.native,self.plan)
        self.staged={'event_sha256':'b'*64,'record':self.record,'knowledge_change_pin':pin,
                     'knowledge_change_plan':self.plan,'knowledge_change_rows':self.native,
                     'receipt':{'quarantined_claim_ids':[],'quarantined_cue_indices':[],
                                'open_numeric_occurrences':0,'reviewed_support_cue_indices':[1]}}
        self.review={'schema':'IRE_V6_KNOWLEDGE_CHANGE_REVIEW_DRAFT_V1',
                     'host_event_sha256':'b'*64,'plan_sha256':pin['plan_sha256'],
                     'as_of':'2026-11-26','rows':[{'prior_row_sha256':key,
                     'operation':'CORRECT_SOURCE_CANDIDATE','proposed_proposition':'Corrected financial interpretation.',
                     'scope_note':'Historical scope, not legal generalization.','evidence_refs':['r1']}]}
        body=b'Official illustrative source, not real evidence.'
        self.evidence={'r1':{'document_raw':body,'document_sha256':sha256(body),
                       'capture_kind':'DECODED_HTML_CAPTURE','evidence_role':'COUNTEREXAMPLE',
                       'proposal':{'schema':'IRE_V6_OFFICIAL_CANDIDATE_V1','claim_id':'C00001',
                       'issuer':'Example official source','url':url,'quote':'illustrative source',
                       'published_on':'2026-01-01','effective_from':'2026-01-01','effective_until':None,
                       'retrieved_on':'2026-11-26','jurisdiction':'KR','scope_note':'Example only.',
                       'claim_support_verdict':'UNREVIEWED'}}}

    def run_review(self,store=None):
        with patch('ire.v6.host_batch.read_host_typed_staging',return_value=self.staged):
            return prepare_host_knowledge_change_review(store or Store(),scope_id='scope',run_id='run',
                raw=b'',manifest={},inventory_bytes=b'',expected_inventory_sha256='a'*64,
                review=self.review,evidence_inputs=self.evidence)

    def test_draft_preserves_conditions_and_target(self):
        result=self.run_review(); row=result['rows'][0]
        self.assertEqual(row['condition_cue_indices'],[1]); self.assertEqual(row['prior_target_id'],'old')
        self.assertEqual(len(row['typed_relation_sha256s']),1)
        self.assertEqual(result['captured_evidence_audits'],1)
        self.assertIs(row['prior_target_mutation_authorized'],False)
        self.assertIs(result['formal_v123_input_authorized'],False)
        self.assertIs(result['finance_evidence_authenticated'],False)

    def test_missing_capture_is_reported_not_approved(self):
        self.review['rows'][0]['evidence_refs']=[]; self.evidence={}
        r=self.run_review(); self.assertEqual(r['change_rows_without_capture'],1)
        self.assertEqual(r['unreplayed_planned_url_links'],1)
        self.assertFalse(r['active_knowledge_changed'])

    def test_wrong_source(self):
        self.evidence['r1']['proposal']['claim_id']='C00002'
        with self.assertRaisesRegex(InvalidInput,'EVIDENCE_WRONG_CLAIM_OR_URL'): self.run_review()

    def test_expired(self):
        self.evidence['r1']['proposal']['effective_until']='2026-01-02'
        with self.assertRaisesRegex(InvalidInput,'EVIDENCE_DATE_NOT_APPLICABLE'): self.run_review()

    def test_change_operation(self):
        self.review['rows'][0]['operation']='RETIRE'
        with self.assertRaisesRegex(InvalidInput,'OPERATION_DRIFT'): self.run_review()

    def test_unbound_evidence(self):
        self.review['rows'][0]['evidence_refs']=[]
        with self.assertRaisesRegex(InvalidInput,'CENSUS_OR_UNUSED_EVIDENCE'): self.run_review()

    def test_fake_approval(self):
        self.review['rows'][0]['approved']=True
        with self.assertRaisesRegex(InvalidInput,'ROW_SCHEMA'): self.run_review()

    def test_stale_head(self):
        stale=Store(); stale.snapshot=lambda scope_id:{'ledger_head_sha256':'0'*64}
        with self.assertRaisesRegex(InvalidInput,'STALE_HEAD'): self.run_review(stale)
