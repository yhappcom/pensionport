"""V173 synthetic E4-only native V123/authority/V127 parent integration.

No test is a real financial source approval or current-chat model invocation.
"""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from test_v166_e4_primary_approval_gate import (
    BODY, V166E4E3V128RealSQLiteIntegration,
)
from v173_e4_only_parent import (
    run_e4_only_parent, seal_e4_only, verify_e4_only_seal,
)

TEST_SECRET=b'SYNTHETIC_E4_ONLY_LOCAL_UNIT_KEY_NOT_FOR_PRODUCTION_2026'

class E4OnlyNativeVideoTests(unittest.TestCase):
    def setUp(self):
        fx=V166E4E3V128RealSQLiteIntegration(
            'test_14_both_valid_synthetic_children_do_publish_research_only')
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.owner=fx
        self.fx=fx.fx
        self.called=[]

    def child(self,sid,manifest,stage,raw):
        self.called.append(sid)
        self.assertEqual(stage,'E4_VERIFY_ONLY')
        return self.fx.child(sid,manifest,stage,raw)

    def engine(self,**override):
        d=dict(checkpoint=self.fx.checkpoint,
            review_or_load_child=self.child,
            primary_manifest_for_child=lambda sid,case:self.owner.manifests.get(sid),
            typed_inventory_for_child=lambda sid,case:self.owner.typed_inventories.get(sid),
            typed_manifest_for_child=lambda sid,case:self.owner.typed_manifests.get(sid),
            review_seams=self.fx.seams,review_parent=self.fx.parent_review,
            now_as_of='2026-11-17',expected_scope_count=2,
            expected_owner_source_sha256=sha256(self.fx.checkpoint.raw))
        d.update(override)
        with patch('v166_e4_primary_approval_gate._fetch_approved_primary_https',return_value=BODY):
            return run_e4_only_parent(**d)

    def counts(self):
        return self.fx._counts()

    def test_01_all_e4_and_parent_verified_no_knowledge_then_owner_seal(self):
        r=self.engine()
        self.assertEqual(r['status'],'E4_ALL_CHILDREN_AND_PARENT_VERIFIED_AWAIT_OWNER_SEAL')
        self.assertEqual(self.called,list(self.fx.checkpoint.child_ids))
        self.assertEqual(r['children_examined'],2)
        self.assertEqual(self.counts().get('knowledge',0),0)
        self.assertEqual(self.counts().get('events',0),0)
        self.assertEqual(self.counts().get('parent_publications',0),0)
        self.assertTrue(r['parent_source_semantic_review_verified'])
        self.assertFalse(r['e4_externally_certified'])
        self.assertFalse(r['e5_publication_called'])
        p=seal_e4_only(r,owner_signing_key=TEST_SECRET,
                       independent_owner_source_sha256=r['owner_source_sha256'])
        status=verify_e4_only_seal(p['certificate'],owner_signing_key=TEST_SECRET,
                       externally_pinned_certificate_sha256=p['external_owner_pin_sha256'])
        self.assertEqual(status['status'],'E4_CERTIFIED_ONLY_NO_E5')
        self.assertFalse(status['e5_authorized'])
        self.assertEqual(self.counts().get('knowledge',0),0)

    def test_02_first_child_missing_primary_still_evaluates_second(self):
        del self.owner.manifests[self.fx.checkpoint.child_ids[0]]
        r=self.engine()
        self.assertEqual(self.called,list(self.fx.checkpoint.child_ids))
        self.assertEqual(r['status'],'E4_HOLD_ALL_SEGMENTS_EXAMINED')
        self.assertEqual(r['blocked_segment_ids'],[self.fx.checkpoint.child_ids[0]])
        self.assertEqual(self.fx.checkpoint.progress()['passed_child_scopes'],0)
        self.assertEqual(self.counts().get('knowledge',0),0)
        with self.assertRaises(InvalidInput):
            seal_e4_only(r,owner_signing_key=TEST_SECRET,
                independent_owner_source_sha256=r['owner_source_sha256'])

    def test_03_last_child_missing_primary_blocks_but_examines_both(self):
        del self.owner.manifests[self.fx.checkpoint.child_ids[-1]]
        r=self.engine()
        self.assertEqual(r['blocked_segment_ids'],[self.fx.checkpoint.child_ids[-1]])
        self.assertEqual(r['children_examined'],2)
        self.assertFalse(r['knowledge_published'])

    def test_04_all_holds_no_checkpoint_or_knowledge(self):
        self.owner.manifests.clear()
        r=self.engine()
        self.assertEqual(r['blocked_segment_ids'],list(self.fx.checkpoint.child_ids))
        self.assertEqual(self.fx.checkpoint.progress()['passed_child_scopes'],0)
        self.assertEqual(self.counts().get('knowledge',0),0)

    def test_05_v123_open_stops_certification_not_video_traversal(self):
        self.fx.packets[0]['case']['chat_review']['atom_verdicts'][0]['status']='OPEN'
        r=self.engine()
        self.assertEqual(r['status'],'E4_HOLD_ALL_SEGMENTS_EXAMINED')
        self.assertEqual(self.called,list(self.fx.checkpoint.child_ids))
        self.assertFalse(r['e4_ready_to_seal'])

    def test_06_invalid_parent_chat_review_blocks_e4_seal(self):
        r=self.engine(review_parent=lambda *args:None)
        self.assertEqual(r['status'],'E4_PARENT_SEMANTIC_HOLD_NO_PUBLICATION')
        self.assertFalse(r['e4_ready_to_seal'])
        self.assertEqual(self.counts().get('knowledge',0),0)

    def test_07_missing_cross_segment_review_blocks_e4_seal(self):
        r=self.engine(review_seams=lambda *args:[])
        self.assertEqual(r['status'],'E4_PARENT_SEMANTIC_HOLD_NO_PUBLICATION')
        self.assertEqual(self.counts().get('knowledge',0),0)

    def test_08_changed_or_unknown_owner_source_pin_fails(self):
        with self.assertRaisesRegex(InvalidInput,'EXTERNALLY_PINNED_OWNER_SOURCE_REQUIRED'):
            self.engine(expected_owner_source_sha256='0'*64)
        self.assertEqual(self.called,[])

    def test_09_no_real_chat_host_callbacks_fails(self):
        with self.assertRaisesRegex(InvalidInput,'CHAT_AND_AUTHORITY_HOST_REQUIRED'):
            self.engine(review_or_load_child=None)
        self.assertEqual(self.called,[])

    def test_10_approval_cannot_be_signed_with_tampered_result(self):
        r=self.engine()
        r['child_reviews'][0]['e4_status']='E4_HOLD_INELIGIBLE_APPROVAL'
        with self.assertRaisesRegex(InvalidInput,'ONLY_UNALTERED_PARENT_APPROVED_E4_ELIGIBLE'):
            seal_e4_only(r,owner_signing_key=TEST_SECRET,
                independent_owner_source_sha256=r['owner_source_sha256'])

    def test_11_wrong_key_pin_or_original_source_blocks_certificate(self):
        r=self.engine()
        with self.assertRaises(InvalidInput):
            seal_e4_only(r,owner_signing_key=b'short',
                independent_owner_source_sha256=r['owner_source_sha256'])
        with self.assertRaises(InvalidInput):
            seal_e4_only(r,owner_signing_key=TEST_SECRET,
                independent_owner_source_sha256='a'*64)
        p=seal_e4_only(r,owner_signing_key=TEST_SECRET,
                independent_owner_source_sha256=r['owner_source_sha256'])
        with self.assertRaises(InvalidInput):
            verify_e4_only_seal(p['certificate'],owner_signing_key=b'z'*32,
                externally_pinned_certificate_sha256=p['external_owner_pin_sha256'])
        with self.assertRaises(InvalidInput):
            verify_e4_only_seal(p['certificate'],owner_signing_key=TEST_SECRET,
                externally_pinned_certificate_sha256='a'*64)

    def test_12_thirteen_scope_control_plane_finishes_after_first_hold(self):
        # Control-plane isolation; the two-scope cases above exercise native E4.
        root=b'synthetic placeholder not actual owner original'
        ids=[f'B{i:04d}' for i in range(1,14)]
        parent=SimpleNamespace(child_ids=ids,
            child_manifests=[{'scope':i} for i in range(1,14)],raw=root,
            parent=SimpleNamespace(source_sha256=sha256(root),
                cues=['synthetic']*13, manifest_sha256='0'*64),
            progress=lambda:{'checkpoint_head_sha256':'0'*64})
        seen=[]
        def child(sid,manifest,stage,raw):
            seen.append(sid)
            return {'case':{'manifest':manifest,'source':SimpleNamespace(
                source_sha256=sha256(root))},
                'relation_decisions':[],
                'original_host_batch_replay_args':{},
                'explicit_hold_revision':False}
        def mock_e4(case,primary,**kw):
            index=case['manifest']['scope']
            if index in (1,7,13):
                return {'status':'E4_HOLD_INELIGIBLE_APPROVAL',
                    'reason_code':'SYNTHETIC_HOLD'}
            return {'status':'E4_PASS_RESEARCH_CANDIDATES_ONLY'}
        with patch('v173_e4_only_parent.assess_e4_primary_authority_gate',mock_e4):
            r=self.engine(checkpoint=parent,review_or_load_child=child,
                expected_scope_count=13,
                expected_owner_source_sha256=sha256(root))
        self.assertEqual(seen,ids)
        self.assertEqual(r['blocked_segment_ids'],['B0001','B0007','B0013'])
        self.assertFalse(r['knowledge_published'])
        self.assertFalse(r['e4_ready_to_seal'])

if __name__=='__main__': unittest.main()