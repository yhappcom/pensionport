"""Native clean typed-to-V123 end-to-end synthetic tests; no actual approval."""
import copy
import tempfile
import unittest
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.tests.test_formal_typed_transition import build_fixture
from v123_chat_final_gate import SCHEMA, _is_finance, assess_chat_final_gate, require_chat_final_release

def review_for(s,e,formal):
    a=audit_host_atomic_exchange(s,e); n=e['atoms'][0]; assert not _is_finance(n,s)
    return dict(schema=SCHEMA,review_executor='CHATGPT_IN_CHAT',as_of='2026-11-26',source_sha256=s.source_sha256,manifest_sha256=s.manifest_sha256,host_event_sha256=formal['event_sha256'],host_bundle_sha256=formal['bundle_sha256'],atom_candidate_digest=a['atom_candidate_digest'],cue_disposition_digest=a['cue_disposition_digest'],blindness='PRIOR_EXPOSED',source_first_pass_completed=True,counterexample_pass_completed=True,disagreements_adjudicated=True,source_cues=[dict(cue_index=c.index,cue_text_sha256=sha256(c.text.encode()),status='REVIEWED',review_note_sha256=sha256(b'synthetic cue note')) for c in s.cues],atom_verdicts=[dict(claim_id=n['claim_id'],atom_sha256=json_digest(n),status='ACCEPT_FOR_RESEARCH',speaker_stance_checked=True,conditions_exceptions_checked=True,numeric_period_checked=True,counterexample_checked=True,high_risk=True,financial_claim=False,finance_evidence_status='NOT_APPLICABLE',official_body_sha256=None,official_effective_as_of=None,financial_scope_checked=False,private_review_note_sha256=sha256(b'synthetic atom note'))],unresolved_high_risk_omissions=0,unresolved_audio_visual=0,external_independent_certified=False,personalized_advice_approved=False,p0_go=False,review_private_evidence_sha256=sha256(b'synthetic review body'))

class FormalV123Tests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.store,self.s,self.e,self.l,self.kw,self.h=build_fixture(d.name)
        self.formal=self.store.submit_host_atomic_batch(**self.kw,run_id='formal',expected_head=self.h['event_sha256'],typed_predecessor=self.h['event_sha256'],formal_typed_transition=True)
        self.review=review_for(self.s,self.e,self.formal)
    def assess(self,host=None,review=None,exchange=None):
        return assess_chat_final_gate(self.s, self.e if exchange is None else exchange,host_receipt=self.formal if host is None else host,chat_review=self.review if review is None else review,store=self.store,official_evidence_bodies={})
    def test_formal_transition_reaches_existing_release(self):
        got=require_chat_final_release(self.s,self.e,host_receipt=self.formal,chat_review=self.review,store=self.store,official_evidence_bodies={})
        self.assertEqual(got['status'],'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY');self.assertEqual(got['atoms_accepted'],1);self.assertFalse(got['master_p4_knowledge_auto_merged']);self.assertFalse(got['p0_go'])
    def test_still_requires_final_review(self):
        self.assertFalse(assess_chat_final_gate(self.s,self.e,host_receipt=self.formal,chat_review=None,store=self.store)['research_candidate_export_allowed'])
    def test_open_verdict_blocks(self):
        r=copy.deepcopy(self.review);r['atom_verdicts'][0]['status']='OPEN';self.assertFalse(self.assess(review=r)['research_candidate_export_allowed'])
    def test_caller_strips_formal_pin(self):
        h=copy.deepcopy(self.formal);h.pop('formal_typed_transition_pin')
        with self.assertRaisesRegex(InvalidInput,'TYPED_HISTORY_REQUIRES_FORMAL_TRANSITION'):self.assess(host=h)
    def test_formal_pin_requires_native_store(self):
        class FakeStore:
            def snapshot(self, scope_id):
                return {}
        with self.assertRaisesRegex(InvalidInput, "FORMAL_TRANSITION_NATIVE_STORE_REQUIRED"):
            assess_chat_final_gate(self.s,self.e,host_receipt=self.formal,chat_review=self.review,store=FakeStore(),official_evidence_bodies={})
    def test_exchange_substitution(self):
        e=copy.deepcopy(self.e);e['atoms'][0]['proposition']='전혀 다른 계획을 세운다.'
        with self.assertRaisesRegex(InvalidInput,'HOST_FORMAL_EXCHANGE_CHANGED'):self.assess(exchange=e)
    def test_later_generic_marker_cannot_erase_typed_history(self):
        sid=self.kw['scope_id'];snap=self.store.snapshot(sid);revision=snap['state']['models']['W00001']['revision_event_sha256']
        h=self.store.submit(scope_id=sid,command_id='generic',expected_head=self.formal['event_sha256'],kind='REVIEW_PROPOSED',payload={'window_id':'W00001','model_revision_event_sha256':revision,'review':{'schema':'ORDINARY_UNAPPROVED_REVIEW'}})
        forged={**self.formal,'event_sha256':h['event_sha256']};forged.pop('formal_typed_transition_pin')
        with self.assertRaisesRegex(InvalidInput,'TYPED_HISTORY_REQUIRES_FORMAL_TRANSITION'):self.assess(host=forged)

class FormalSupportTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.store,self.s,self.e,self.l,self.kw,self.h=build_fixture(d.name,support=True)
        self.formal=self.store.submit_host_atomic_batch(**self.kw,run_id='formal',expected_head=self.h['event_sha256'],typed_predecessor=self.h['event_sha256'],formal_typed_transition=True)
        self.review=review_for(self.s,self.e,self.formal)
    def test_full_premise_remains_in_formal_exchange_and_is_reviewed(self):
        self.assertEqual(self.formal['formal_typed_transition_pin']['reviewed_support_cue_indices'],[1])
        self.assertEqual(self.e['atoms'][0]['condition_cue_indices'],[1])
        self.assertEqual(self.e['cue_dispositions'][0]['disposition'],'NO_ATOM')
        r=require_chat_final_release(self.s,self.e,host_receipt=self.formal,chat_review=self.review,store=self.store,official_evidence_bodies={})
        self.assertEqual(r['cues_reviewed'],2);self.assertTrue(r['research_candidate_export_allowed'])
    def test_open_support_blocks_release(self):
        self.review['source_cues'][0]['status']='OPEN'
        r=assess_chat_final_gate(self.s,self.e,host_receipt=self.formal,chat_review=self.review,store=self.store,official_evidence_bodies={})
        self.assertFalse(r['research_candidate_export_allowed'])
    def test_support_pin_cannot_be_stripped(self):
        self.formal['formal_typed_transition_pin']['reviewed_support_cue_indices']=[]
        with self.assertRaisesRegex(InvalidInput,'TYPED_HISTORY_REQUIRES_FORMAL_TRANSITION'):
            assess_chat_final_gate(self.s,self.e,host_receipt=self.formal,chat_review=self.review,store=self.store,official_evidence_bodies={})

class FormalV126Tests(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        from ire.v6.codec import ZERO_SHA
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.store,self.s,self.e,self.l,self.kw,self.h=build_fixture(d.name,support=True)
        replay={**self.kw,'run_id':'formal','expected_head':self.h['event_sha256'],'typed_predecessor':self.h['event_sha256'],'formal_typed_transition':True}
        self.formal=self.store.submit_host_atomic_batch(**replay)
        self.review=review_for(self.s,self.e,self.formal)
        self.k=PrivateKnowledgeStore(Path(d.name)/'knowledge.db')
        self.args=dict(host_receipt=self.formal,chat_review=self.review,source_store=self.store,official_evidence_bodies={},relation_decisions=[dict(claim_id='C00001',atom_sha256=json_digest(self.e['atoms'][0]),relation='NEW',target_kind='NONE',target_id=None,private_chat_relation_review_sha256=sha256(b'synthetic relation review'))],expected_knowledge_head=ZERO_SHA,original_host_batch_replay_args=replay)
    def add(self,**kw):
        return self.k.add_chat_final_batch(self.s,self.e,self.kw['knowledge'],**{**self.args,**kw})
    def test_approved_candidate_saved_reopened_and_idempotent(self):
        import sqlite3,json
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        r=self.add();self.assertEqual(r['entries'],1);self.assertTrue(r['master116_p4_untouched']);self.assertEqual(r['financial_fact_formal_approval'],0)
        again=PrivateKnowledgeStore(self.k.path).audit(externally_pinned_head=r['knowledge_head_sha256']);self.assertEqual(again['active_claims'],1)
        from contextlib import closing
        with closing(sqlite3.connect(self.k.path)) as c:
            rows=c.execute('select entry_json from knowledge').fetchall()
        self.assertEqual(len(rows),1);entry=json.loads(rows[0][0]);self.assertEqual(entry['atom'],self.e['atoms'][0]);self.assertEqual(entry['host_event_sha256'],self.formal['event_sha256'])
        self.assertTrue(self.add()['idempotent_replay'])
    def test_missing_formal_flag_blocks_storage(self):
        replay=dict(self.args['original_host_batch_replay_args']);replay.pop('formal_typed_transition')
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT'):self.add(original_host_batch_replay_args=replay)
        self.assertEqual(self.k.audit()['active_claims'],0)
    def test_open_review_blocks_storage(self):
        self.review['atom_verdicts'][0]['status']='OPEN'
        with self.assertRaises(QualityNotProven):self.add()
        self.assertEqual(self.k.audit()['active_claims'],0)
