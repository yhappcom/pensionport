"""V149 actual V128 synthetic multi-child DB evidence and adversarial read tests."""
from __future__ import annotations
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.codec import json_digest,sha256,ZERO_SHA
from v149_owner_approved_evidence import prepare_verified_owner_question, OwnerEvidenceHold
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from ire.v6.errors import QualityNotProven

class V149ParentOnlyEvidenceTests(unittest.TestCase):
    def setUp(self):
        # Test host, original V6 child replay, V123/V126 and actual V128 ACID code.
        # The data and ChatGPT judgments in this fixture are *synthetic*.
        from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests
        fx=V128HostRunAndAtomicParentTests('test_01_two_native_v6_children_seam_and_atomic_private_parent_publication')
        fx.setUp();self.addCleanup(fx.doCleanups);self.fx=fx

    def published_pin(self):
        result=self.fx.run_engine()
        with sqlite3.connect(self.fx.knowledge.path) as con:
            proof=json.loads(con.execute('SELECT proof_json FROM parent_publications').fetchone()[0])
            ids=sorted(row[0] for row in con.execute('SELECT knowledge_id FROM knowledge'))
        checkpoint=self.fx.checkpoint
        return result,ids,{'schema':'IRE_V149_EXTERNALLY_FROZEN_PARENT_READ_PIN_V1',
            'identity':{'video_id':checkpoint.parent.video_id,
                        'source_sha256':checkpoint.parent.source_sha256,
                        'manifest_sha256':checkpoint.parent.manifest_sha256,
                        'owner_inventory_pin':checkpoint.owner_pin},
            'parent_publication_proof_sha256':json_digest(proof),
            'parent_chat_release_sha256':proof['chat_release_sha256'],
            'child_batches_sha256':proof['request']['child_batches_sha256'],
            'expected_knowledge_head_sha256':result['knowledge_head_sha256'],
            'expected_segment_count':2}

    def query(self,pin,ids,*,count=2,source=None):
        return prepare_verified_owner_question(self.fx.knowledge,'연금저축 교육 설명',owner_checkpoint=pin,
            selected_knowledge_ids=ids,expected_segment_count=count,
            as_of='2026-11-16',required_source_sha256=source or pin['identity']['source_sha256'])

    def test_01_only_real_synthetic_parent_published_evidence_is_readable(self):
        r,ids,pin=self.published_pin()
        ans=self.query(pin,ids[:1])
        self.assertEqual(ans['child_segment_count'],2)
        self.assertEqual(ans['evidence']['count'],1)
        self.assertFalse(ans['p0_e_go'])
        self.assertTrue(ans['answer_must_be_checked_by_V126_chat_research_answer_bridge'])
        self.assertTrue(ans['separate_external_checkpoint_authenticity_not_proven_by_same_DB'])

    def test_02_zero_knowledge_actual_owner_like_hold_cannot_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty=PrivateKnowledgeStore(Path(tmp)/'unapproved.db')
            fake={'schema':'IRE_V149_EXTERNALLY_FROZEN_PARENT_READ_PIN_V1',
                'identity':{'video_id':'TEST_OWNER','source_sha256':'a'*64,'manifest_sha256':'b'*64,'owner_inventory_pin':'c'*64},
                'parent_publication_proof_sha256':'d'*64,'parent_chat_release_sha256':'e'*64,
                'child_batches_sha256':'f'*64,'expected_knowledge_head_sha256':ZERO_SHA,
                'expected_segment_count':13}
            with self.assertRaisesRegex(OwnerEvidenceHold,'NO_RELEASED_RESEARCH_KNOWLEDGE'):
                prepare_verified_owner_question(empty,'ISA 적용 범위',owner_checkpoint=fake,
                    selected_knowledge_ids=['1'*64],as_of='2026-11-16')

    def test_03_forged_or_stale_parent_proof_fails_closed(self):
        r,ids,pin=self.published_pin()
        forged=copy.deepcopy(pin);forged['parent_publication_proof_sha256']='f'*64
        with self.assertRaisesRegex(OwnerEvidenceHold,'PARENT_PROOF_NOT_FROZEN'):
            self.query(forged,ids[:1])
        forged=copy.deepcopy(pin);forged['expected_knowledge_head_sha256']='f'*64
        with self.assertRaises(QualityNotProven):self.query(forged,ids[:1])

    def test_04_owner_video_source_or_parent_id_mismatch(self):
        r,ids,pin=self.published_pin()
        with self.assertRaisesRegex(OwnerEvidenceHold,'WRONG_OWNER_SOURCE'):
            self.query(pin,ids[:1],source='f'*64)
        forged=copy.deepcopy(pin);forged['identity']['manifest_sha256']='f'*64
        with self.assertRaisesRegex(OwnerEvidenceHold,'REQUIRED_PARENT_NOT_PUBLISHED'):
            self.query(forged,ids[:1])

    def test_05_unpublished_or_foreign_id_never_retrieved(self):
        r,ids,pin=self.published_pin()
        with self.assertRaisesRegex(OwnerEvidenceHold,'UNPUBLISHED_OR_FOREIGN_KNOWLEDGE_SELECTED'):
            self.query(pin,['f'*64])
        with self.assertRaisesRegex(OwnerEvidenceHold,'UNPUBLISHED_OR_FOREIGN_KNOWLEDGE_SELECTED'):
            self.query(pin,[])

    def test_06_owner_prod_13_not_satisfied_by_synthetic_two_child(self):
        r,ids,pin=self.published_pin()
        with self.assertRaisesRegex(OwnerEvidenceHold,'CHECKPOINT_CENSUS'):
            self.query(pin,ids[:1],count=13)

    def test_07_tampered_parent_proof_cannot_be_read(self):
        r,ids,pin=self.published_pin()
        with sqlite3.connect(self.fx.knowledge.path) as con:
            con.execute('UPDATE parent_publications SET proof_sha256=?',('1'*64,))
        with self.assertRaises(QualityNotProven):self.query(pin,ids[:1])

if __name__=='__main__':unittest.main()
