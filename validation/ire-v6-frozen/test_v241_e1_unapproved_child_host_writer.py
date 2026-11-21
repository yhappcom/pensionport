"""V241 2-child synthetic fixture; V231 authenticity stubbed ONLY in this module.

Real V231 verify and real 12/13 ETF child host runs are separately executed.
No signed owner or authorized knowledge is synthesized by this test.
"""
from __future__ import annotations
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6 import TransactionStore
from ire.v6.codec import json_digest,sha256,ZERO_SHA
from ire.v6.errors import InvalidInput,QualityNotProven
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v237_e1_parent_child_review_contract import build_child_review_tasks
from v238_e1_child_native_scope_draft import build_partial_native_drafts
from v241_e1_unapproved_child_host_writer import build_unapproved_child_host_case,stage_child_host_only
import test_v234_e1_cross_child_context_custody as fixture

class TestV241UnapprovedRealNativeWriter(unittest.TestCase):
    def setUp(self):
        f=fixture.TestV234CrossChildCustody('test_01_two_scopes_three_local_atoms_no_cross')
        f.setUp();self.addCleanup(f.doCleanups)
        self.fx=f
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)/'private';self.folder.mkdir(mode=0o700)
        self._setup_origin(copy.deepcopy(f.origin))

    def _setup_origin(self,origin):
        self.origin=origin
        origin['cue_count']=len(origin['source'].cues)
        models={};reviews={}
        for wid,first,last in origin['source'].primary_windows:
            atoms=[a for a in origin['exchange']['atoms'] if a['owner_window_id']==wid]
            claims=[{'claim_id':a['claim_id'],'proposition':a['proposition'],
                     'kind':a['kind'],'owner_window_id':a['owner_window_id'],
                     'source_refs':a['source_refs'],
                     'context_first_cue':a['source_refs'][0]['cue_index'],
                     'context_last_cue':a['source_refs'][-1]['cue_index']} for a in atoms]
            models[wid]={'schema':'IRE_V6_ATOMIC_MODEL_V1','claims':claims}
            reviews[wid]={'schema':'IRE_V6_STRUCTURAL_REVIEW_V1',
                          'review_scope':'SOURCE_ANCHORS_ONLY',
                          'reviewed_claim_ids':sorted(a['claim_id'] for a in atoms),
                          'independent_gold_verified':False}
        origin['models']=models;origin['reviews']=reviews
        a=self.fx.args()
        a['origin']=origin;a['externally_pinned_exchange_digest']=json_digest(origin['exchange'])
        escrow=build_lossless_context_escrow(**a)
        tasks=build_child_review_tasks(**dict(a,cross_context_escrow=escrow,
                                 externally_pinned_escrow_sha256=json_digest(escrow)))
        self.tasks=tasks
        drafts=build_partial_native_drafts(origin=origin,checkpoint=self.fx.ck,
            review_tasks=tasks,externally_pinned_review_tasks_sha256=json_digest(tasks),
            **{k:v for k,v in dict(a,cross_context_escrow=escrow,
              externally_pinned_escrow_sha256=json_digest(escrow)).items()
              if k not in ('origin','checkpoint')})
        self.drafts=drafts
        source=origin['source']
        from ire.v6.codec import canonical
        self.fake_receipt={'turn2_review':{'source_only_review_rows':[{
            'cue_index':cue.index,'quote':cue.text,
            'quote_sha256':sha256(cue.text.encode('utf-8')),
            'review_reason':'Synthetic only pending review, not authentic'
            } for cue in source.cues]}}
        self.kw=dict(origin=origin,checkpoint=self.fx.ck,
            child_native_draft=drafts,review_tasks=tasks,cross_context_escrow=escrow,
            second_receipt=self.fake_receipt,private_source_note={},prequarantine={},
            externally_pinned_child_draft_sha256=json_digest(drafts),
            externally_pinned_review_tasks_sha256=json_digest(tasks),
            externally_pinned_receipt_sha256='b'*64,
            externally_pinned_source_note_sha256='c'*64,
            externally_pinned_prequarantine_sha256='d'*64,
            externally_pinned_escrow_sha256=json_digest(escrow),
            externally_pinned_parent_plan_sha256=self.fx.ck.plan_pin,
            externally_pinned_checkpoint_head_sha256=ZERO_SHA,
            externally_pinned_source_sha256=origin['source_sha256'],
            externally_pinned_exchange_digest=json_digest(origin['exchange']))
        repo=Path(__file__).resolve().parents[2]
        priorpath=repo/'ire/v5/advisory_knowledge'
        prior={'master116_bytes':(repo/'data/claims.jsonl').read_bytes(),
               'p4_22_bytes':(priorpath/'p4_integrated_scoped_education22_20261106.json').read_bytes(),
               'p4_7_bytes':(priorpath/'p4_p3_incremental_education29_20261106.json').read_bytes(),
               'relations':[{'claim_id':a['claim_id'],
                  'candidate_source_sha256':origin['source_sha256'],
                  'target_kind':'NONE','target_id':None,'target_content_sha256':None,
                  'relationship':'NOVEL_PENDING',
                  'rationale':'Synthetic testing, not independent novelty proof',
                  'independent_semantic_review_verified':False,
                  'personalized_action_approved':False}
                 for a in origin['exchange']['atoms']]}
        self.kw['prior_knowledge']=prior

    def prepare(self,child_id):
        with patch('v241_e1_unapproved_child_host_writer.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_AUTH_STUB_ONLY'}):
            return build_unapproved_child_host_case(child_id=child_id,**self.kw)

    def test_01_two_scopes_can_preflight_local_atoms_without_approval(self):
        for cid in ('B0001','B0002'):
            case=self.prepare(cid)
            self.assertFalse(case['e3_formal_approved'])
            self.assertEqual(case['original_cross_atoms_awaiting_meaning'],0)
            self.assertGreater(case['original_local_atoms_staged'],0)

    def test_02_real_v6_sqlite_commit_and_reopen_with_owner_only_flag_false(self):
        case=self.prepare('B0001');s=TransactionStore(self.folder/'success.db')
        r=stage_child_host_only(case=case,native_store=s,scope_id='v241_synthetic_child_B0001',
           run_id='v241_synthetic_child_host_01',
           externally_operator_pinned_inventory_sha256=case['operator_inventory_digest_sha256'],
           explicit_unapproved_host_stage=True)
        reopened=TransactionStore(self.folder/'success.db').snapshot('v241_synthetic_child_B0001')
        self.assertEqual(reopened['ledger_head_sha256'],r['host_event_sha256'])
        self.assertEqual(reopened['progress']['model_windows_recorded'],1)
        self.assertEqual(r['e5_published'],0)
        self.assertFalse(r['independent_owner_signature_proven'])

    def test_03_no_stage_permission_rejected_before_write(self):
        case=self.prepare('B0001');s=TransactionStore(self.folder/'denied.db')
        with self.assertRaisesRegex(InvalidInput,'EXPLICIT_OWNER_SCOPED'):
            stage_child_host_only(case=case,native_store=s,scope_id='v241_synthetic_deny',
             run_id='v241_synthetic_deny',externally_operator_pinned_inventory_sha256=case['operator_inventory_digest_sha256'])
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            s.snapshot('v241_synthetic_deny')

    def test_04_wrong_operator_pin_blocks_no_scope(self):
        case=self.prepare('B0001');s=TransactionStore(self.folder/'wrongpin.db')
        with self.assertRaisesRegex(InvalidInput,'OPERATOR_HELD_CHILD_INVENTORY_PIN_MISMATCH'):
            stage_child_host_only(case=case,native_store=s,scope_id='v241_synthetic_wrong',
             run_id='v241_synthetic_wrong',externally_operator_pinned_inventory_sha256='f'*64,
             explicit_unapproved_host_stage=True)
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            s.snapshot('v241_synthetic_wrong')

    def test_05_empty_local_child_preflight_blocks_before_sqlite_creation(self):
        src=copy.deepcopy(self.fx.origin)
        # Make C00003's owner B0002 dependent on cue 4 in B0001.
        atom=next(a for a in src['exchange']['atoms'] if a['claim_id']=='C00003')
        atom['context_cue_indices']=[4,5,6]
        src['native_exchange_digest']=json_digest(src['exchange'])
        self._setup_origin(src)
        with self.assertRaisesRegex(QualityNotProven,'EMPTY_CHILD_LOCAL_ATOMS_REQUIRE_SOURCE_MEANING_REPAIR'):
            self.prepare('B0002')
        self.assertFalse((self.folder/'B0002.db').exists())

    def test_06_child_provenance_without_source_quote_rejected(self):
        bad=copy.deepcopy(self.kw)
        bad['second_receipt']['turn2_review']['source_only_review_rows'][1]['quote']='FAKE'
        with self.assertRaisesRegex(InvalidInput,'CHILD_SOURCE_ONLY_REVIEW_QUOTE_DRIFT'):
            with patch('v241_e1_unapproved_child_host_writer.verify_real_turn2_private_custody',return_value={}):
                build_unapproved_child_host_case(child_id='B0001',**bad)

if __name__=='__main__':unittest.main()