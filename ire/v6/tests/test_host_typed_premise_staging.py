"""Synthetic typed staging regression; no semantic or financial approval."""
import copy
import unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.host_quarantine_preflight import (audit_host_quarantine_preflight,
    TYPED_STAGING_SCHEMA, TYPED_STAGING_RECEIPT)
from ire.v6.semantic_authoring_protocol import compile_authoring
from ire.v6.tests.test_semantic_authoring_protocol import source, packet, full


def fixture():
    s = source('투자 대상이 동일하다면', '비용을 비교한다.')
    a = packet(s)
    t = a['atoms'][0]
    t['node']['predicate'] = '투자 대상이 동일하다면 비용을 비교한다.'
    t['node']['direct'] = [full(s, 2)]
    a['segments'][0]['status'] = 'SUPPORT'
    t['quantities'] = []
    t['relations'] = [dict(type='CONDITION', premise=[full(s, 1)],
                          consequent=[full(s, 2)], reason='Explicit premise.')]
    _, r = compile_authoring(s, a)
    n = dict(claim_id='C00001', owner_window_id='W00001', proposition=t['node']['predicate'],
             kind='FACT', stance='CONDITIONAL', speaker='NARRATOR',
             source_refs=[dict(cue_index=2, quote=s.cues[1].text)],
             context_cue_indices=[1,2], condition_cue_indices=[1], exception_cue_indices=[],
             numeric_references=[], as_of=None)
    e = dict(schema='IRE_V6_HOST_ATOMIC_EXCHANGE_V1', video_id=s.video_id,
             source_sha256=s.source_sha256, manifest_sha256=s.manifest_sha256, atoms=[n],
             cue_dispositions=[dict(cue_index=i, cue_text_sha256=sha256(c.text.encode()),
                  disposition='NO_ATOM' if i==1 else 'CANDIDATES',
                  claim_ids=[] if i==1 else ['C00001'], numeric_tokens=[],
                  note='Synthetic source disposition.') for i,c in enumerate(s.cues,1)])
    l = dict(schema=TYPED_STAGING_SCHEMA, source_sha256=s.source_sha256,
             manifest_sha256=s.manifest_sha256, review_executor='CHATGPT_IN_CHAT',
             authored=a, authoring_receipt=r, exchange_sha256=json_digest(e),
             projection_rows=[dict(typed_id='A00001', claim_id='C00001',
                  typed_sha256=json_digest(t), native_sha256=json_digest(n), note='Synthetic draft.')],
             support_rows=[dict(cue_index=1, cue_sha256=sha256(s.cues[0].text.encode()),
                  claim_ids=['C00001'], reason='Entire premise is explicitly retained.')],
             quarantine_cues=[], quarantine_atoms=[], p0_go=False)
    return s,e,l


class TypedPremiseStagingTests(unittest.TestCase):
    def setUp(self): self.s,self.e,self.l=fixture()

    def test_reviewed_premise_staging_not_release(self):
        r=audit_host_quarantine_preflight(self.s,self.e,self.l)
        self.assertEqual(r['schema'],TYPED_STAGING_RECEIPT)
        self.assertEqual(r['reviewed_support_cue_indices'],[1])
        self.assertFalse(r['formal_v123_input_authorized'])
        self.assertFalse(r['p0_go'])
        with self.assertRaisesRegex(QualityNotProven,'UNRESOLVED_SOURCE_RESIDUALS'):
            audit_host_quarantine_preflight(self.s,self.e,None)

    def test_condition_cannot_be_removed_by_rehashing(self):
        e,l=copy.deepcopy(self.e),copy.deepcopy(self.l)
        e['atoms'][0]['condition_cue_indices']=[];e['atoms'][0]['stance']='UNRESOLVED'
        l['exchange_sha256']=json_digest(e);l['projection_rows'][0]['native_sha256']=json_digest(e['atoms'][0])
        with self.assertRaisesRegex(InvalidInput,'PREMISE_DRIFT'):
            audit_host_quarantine_preflight(self.s,e,l)

    def test_support_partition_and_dependency(self):
        for value,code in (([],'MANDATORY_RESIDUAL_MISSING'),
            ([dict(self.l['support_rows'][0],claim_ids=[])],'SUPPORT_PREMISE_CENSUS')):
            l=copy.deepcopy(self.l);l['support_rows']=value
            with self.subTest(code=code),self.assertRaisesRegex(InvalidInput,code):
                audit_host_quarantine_preflight(self.s,self.e,l)

    def test_quarantine_cannot_hide_dependent_claim(self):
        l=copy.deepcopy(self.l);l['support_rows']=[]
        l['quarantine_cues']=[dict(cue_index=1,cue_sha256=sha256(self.s.cues[0].text.encode()),reason='Synthetic unresolved premise.')]
        with self.assertRaisesRegex(InvalidInput,'QUARANTINE_DEPENDENCY_MISSING'):
            audit_host_quarantine_preflight(self.s,self.e,l)
        l['quarantine_atoms']=[dict(claim_id='C00001',native_sha256=json_digest(self.e['atoms'][0]),reason='Dependent claim is withheld.')]
        self.assertEqual(audit_host_quarantine_preflight(self.s,self.e,l)['quarantined_claim_ids'],['C00001'])

    def test_no_invented_date_or_projection_loss(self):
        e,l=copy.deepcopy(self.e),copy.deepcopy(self.l)
        e['atoms'][0]['as_of']='2026-11-26';l['exchange_sha256']=json_digest(e)
        l['projection_rows'][0]['native_sha256']=json_digest(e['atoms'][0])
        with self.assertRaisesRegex(InvalidInput,'TEMPORAL_PROJECTION_DRIFT'):
            audit_host_quarantine_preflight(self.s,e,l)
        l=copy.deepcopy(self.l);l['projection_rows']=[]
        with self.assertRaisesRegex(InvalidInput,'PROJECTION_CENSUS'):
            audit_host_quarantine_preflight(self.s,self.e,l)
