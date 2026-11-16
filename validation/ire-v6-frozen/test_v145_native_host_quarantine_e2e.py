"""V145 real V6 host mechanics with SYNTHETIC four-cue quarantine fixture.
This does NOT certify owner video, semantic recall, issuer law or financial advice.
"""
from __future__ import annotations
import copy
import json
import unittest
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.tests.test_host_batch import HostBatchTests
from test_v123_chat_final_gate import ChatFinalGateTests
from v123_chat_final_gate import assess_chat_final_gate


def sh(t):return sha256(t.encode('utf8'))

class V145NativePendingSourceHostTests(unittest.TestCase):
    def setUp(self):
        base=HostBatchTests('test_one_command_commits_all_models_and_proofs_atomically');base.setUp();self.addCleanup(base.doCleanups)
        self.base=base
        self.ex=copy.deepcopy(base.fx.exchange)
        self.ex['cue_dispositions'][3].update(disposition='UNRESOLVED',claim_ids=[],note='원음 미확인으로 연구 제외 후보')
        self.idx=4
        self.pending={
            'schema':'IRE_V6_HOST_SOURCE_PREQUARANTINE_V145',
            'source_sha256':base.fx.source.source_sha256,
            'manifest_sha256':base.fx.source.manifest_sha256,
            'review_executor':'CHATGPT_IN_CHAT',
            'private_review_sha256':sh('synthetic four-cue preflight'),
            'cue_rows':[{'cue_index':self.idx,
                          'cue_text_sha256':sh(base.fx.source.cues[self.idx-1].text),
                          'reason_code':'ASR_ORIGINAL_UNVERIFIED',
                          'private_chat_cue_review_sha256':sh('synthetic cue four note'),
                          'source_first_context_reviewed':True}],
            'audio_authenticity_verified':False,
            'semantic_claims_independently_verified':False,
            'p0_go':False
        }
    def kwargs(self,**extras):
        args=self.base.args(exchange=self.ex,quarantine_preflight=self.pending)
        args.update(extras);return args
    def test_01_unresolved_without_explicit_pending_is_rejected_with_zero_model_events(self):
        with self.assertRaisesRegex(QualityNotProven,'HOST_BATCH_UNRESOLVED_SOURCE_RESIDUALS'):
            self.base.fx.store.submit_host_atomic_batch(**self.base.args(exchange=self.ex))
        snap=self.base.fx.store.snapshot('host_scope')
        self.assertEqual(snap['ledger_head_sha256'],self.base.base['ledger_head_sha256'])
        self.assertEqual(snap['progress']['model_windows_recorded'],0)
    def test_02_pinned_pending_allows_structural_host_but_not_quality(self):
        first=self.base.fx.store.submit_host_atomic_batch(**self.kwargs())
        second=self.base.fx.store.submit_host_atomic_batch(**self.kwargs())
        self.assertEqual(first['event_sha256'],second['event_sha256'])
        self.assertFalse(first['idempotent_replay'])
        self.assertTrue(second['idempotent_replay'])
        self.assertEqual(first['host_source_prequarantine_pin']['unresolved_original_cue_indices'],[4])
        self.assertFalse(first['research_complete'])
        self.assertFalse(first['p0_go'])
        self.assertEqual(self.base.fx.store.snapshot('host_scope')['progress']['model_windows_recorded'],2)
    def test_03_missing_or_forged_cue_hash_reason_schema_source_rejected(self):
        variants=[('hash',lambda a:a['cue_rows'][0].update(cue_text_sha256='0'*64)),
                  ('reason',lambda a:a['cue_rows'][0].update(reason_code='AUTO_APPROVED')),
                  ('reviewer',lambda a:a.update(review_executor='NOT_CHATGPT')),
                  ('source',lambda a:a.update(source_sha256='0'*64)),
                  ('census',lambda a:a.update(cue_rows=[])),
                  ('false_auth',lambda a:a.update(audio_authenticity_verified=True))]
        for k,fn in variants:
            p=copy.deepcopy(self.pending);fn(p)
            with self.subTest(k=k),self.assertRaises((InvalidInput,QualityNotProven)):
                self.base.fx.store.submit_host_atomic_batch(**self.kwargs(quarantine_preflight=p))
        self.assertEqual(self.base.fx.store.snapshot('host_scope')['progress']['model_windows_recorded'],0)
    def test_04_preflight_changed_after_commit_must_not_replay(self):
        first=self.base.fx.store.submit_host_atomic_batch(**self.kwargs())
        p=copy.deepcopy(self.pending)
        p['private_review_sha256']=sh('different synthetic private note')
        with self.assertRaises(Exception):
            self.base.fx.store.submit_host_atomic_batch(**self.kwargs(quarantine_preflight=p))
        self.assertEqual(self.base.fx.store.snapshot('host_scope')['ledger_head_sha256'],first['event_sha256'])
    def test_05_v123_owner_pending_receipt_requires_actual_source_exclusion(self):
        host=self.base.fx.store.submit_host_atomic_batch(**self.kwargs())
        approval=ChatFinalGateTests('test_01_real_native_v6_batch_then_synthetic_chat_final_pass')
        approval.setUp();self.addCleanup(approval.doCleanups)
        # The separate synthetic approval fixture shares exact source and claim
        # bytes but has a different *host* scope proof. Bind to actual host.
        audit=audit_host_atomic_exchange(self.base.fx.source,self.ex)
        reviewed=copy.deepcopy(approval.review)
        reviewed.update(host_event_sha256=host['event_sha256'],
                        host_bundle_sha256=host['bundle_sha256'],
                        atom_candidate_digest=audit['atom_candidate_digest'],
                        cue_disposition_digest=audit['cue_disposition_digest'],
                        unresolved_audio_visual=1)
        reviewed['source_cues'][-1]['status']='EXCLUDED_FROM_RESEARCH'
        reviewed['quarantine']={
            'schema':'IRE_V123_SOURCE_PINNED_QUARANTINE_V1',
            'source_sha256':self.base.fx.source.source_sha256,
            'manifest_sha256':self.base.fx.source.manifest_sha256,
            'review_executor':'CHATGPT_IN_CHAT',
            'cue_rows':[{'cue_index':4,
                         'cue_text_sha256':sh(self.base.fx.source.cues[3].text),
                         'reason_code':'AUDIO_UNVERIFIED',
                         'private_review_note_sha256':sh('synthetic V123 cue four note'),
                         'source_first_context_checked':True}],
            'atom_rows':[],
            'audio_unverified_cue_indices':[4],
            'private_chat_quarantine_review_sha256':sh('synthetic downstream ChatGPT review')}
        def gate(review,host_receipt=host):
            return assess_chat_final_gate(self.base.fx.source,self.ex,
                     host_receipt=host_receipt,chat_review=review,
                     store=self.base.fx.store,
                     official_evidence_bodies=approval.evidence_bodies)
        got=gate(reviewed)
        self.assertEqual(got['status'],'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY')
        self.assertEqual(got['cues_excluded'],1)
        self.assertFalse(got['audio_authenticity_verified'])
        self.assertFalse(got['p0_go'])
        partial=copy.deepcopy(reviewed);partial.pop('quarantine')
        with self.assertRaises((InvalidInput,QualityNotProven)):
            gate(partial)
        forged=copy.deepcopy(host);forged['host_source_prequarantine_pin']['preflight_ledger_sha256']='0'*64
        with self.assertRaises((InvalidInput,QualityNotProven)):
            gate(reviewed,host_receipt=forged)

if __name__=='__main__':unittest.main(verbosity=2)

class V145V128IdempotentHeldChildTests(unittest.TestCase):
    """A replayed HELD checkpoint must not be mistaken for a PASS/advance."""
    def setUp(self):
        from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests
        from ire.v6.codec import ZERO_SHA
        base=V128HostRunAndAtomicParentTests(
            'test_03_second_child_finance_open_holds_and_knowledge_never_partially_inserts')
        base.setUp();self.addCleanup(base.doCleanups)
        self.base=base
        self.zero=ZERO_SHA
        packet=copy.deepcopy(base.packets[0])
        heldcase=dict(packet['case']); heldcase['official_evidence_bodies']={}
        packet['case']=heldcase
        base.packets[0]=packet

    def test_06_exact_replayed_held_child_stops_at_same_segment_without_second_checkpoint(self):
        base=self.base
        first=base.run_engine()
        self.assertEqual(first['status'],'HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE')
        self.assertEqual(first['next_segment_id'],'B0001')
        head=base.checkpoint.progress()['checkpoint_head_sha256']
        second=base.run_engine()
        self.assertEqual(second['status'],'HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE')
        self.assertEqual(second['next_segment_id'],'B0001')
        self.assertEqual(base.checkpoint.progress()['checkpoint_head_sha256'],head)
        self.assertEqual(base.checkpoint.progress()['missing_child_scopes'],1)
        self.assertEqual(base.trace,[('B0001','REVIEW_REQUIRED'),('B0001','REVIEW_REQUIRED')])
        self.assertEqual(base.knowledge.audit()['head_sha256'],self.zero)
        self.assertEqual(base._counts().get('knowledge',0),0)

    def test_07_changed_held_child_without_explicit_revision_rejected(self):
        base=self.base
        first=base.run_engine()
        self.assertEqual(first['next_segment_id'],'B0001')
        previous_head=base.checkpoint.progress()['checkpoint_head_sha256']
        base.packets[0]={**base.packets[0], 'case':base.p.cases[0]}
        with self.assertRaises(QualityNotProven):
            base.run_engine()
        self.assertEqual(base.checkpoint.progress()['checkpoint_head_sha256'],previous_head)
        self.assertEqual(base.knowledge.audit()['head_sha256'],self.zero)
