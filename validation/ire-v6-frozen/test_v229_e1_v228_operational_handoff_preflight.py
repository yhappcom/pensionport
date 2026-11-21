"""E1 V229 audit: distinguish V203 synthetic architecture from V228 live-owner handoff."""
import copy
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from ire.v6.errors import InvalidInput
from test_v227_e2_source_semantic_reconciliation import synthetic
from test_v228_v193_actual_two_turn_runtime_gate import make_input, pins
from v228_v193_actual_two_turn_runtime_gate import freeze_turn1_private
from v229_e1_v228_operational_handoff_preflight import check_v228_e1_owner_handoff


class TestV229E1HandoffReaudit(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.d=Path(t.name)
        docs,*_=synthetic()
        self.frozen=freeze_turn1_private(**make_input(docs,self.d))
        self.args=pins(self.frozen,self.d/'first.zip')

    def run_preflight(self,**changed):
        return check_v228_e1_owner_handoff(**dict(self.args,**changed))

    def test_01_v228_first_turn_is_not_operational_e1_end_to_end(self):
        out=self.run_preflight()
        self.assertEqual(out['status'],'HOLD_NO_GENUINE_V176_JOURNAL_OR_PARENT_CHECKPOINT')
        self.assertTrue(out['existing_v203_synthetic_architecture_pass_is_distinct'])
        self.assertFalse(out['e1_real_owner_full_approval_store_path_proven'])
        self.assertFalse(out['native_owner_chain_verified'])
        self.assertEqual(out['video_knowledge_written'],0)

    def test_02_actual_first_zip_may_not_be_accepted_as_v176_owner(self):
        with self.assertRaisesRegex(InvalidInput,'REAL_V176_OWNER_REQUIRED'):
            self.run_preflight(v176_owner=self.d/'first.zip',parent_checkpoint=object(),
                               externally_pinned_v176_owner_head_sha256='a'*64)

    def test_03_fake_second_turn_receipt_without_native_owner_refused(self):
        with self.assertRaisesRegex(InvalidInput,'TURN2_RECEIPT_WITHOUT_NATIVE_OWNER'):
            self.run_preflight(v193_second_turn_review_receipt={'source_sha256':self.frozen['source_sha256']})

    def test_04_orphan_v176_owner_head_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'ORPHAN_OWNER_HEAD'):
            self.run_preflight(externally_pinned_v176_owner_head_sha256='0'*64)

    def test_05_incomplete_parent_checkpoint_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'INCOMPLETE_OWNER_AND_PARENT_PAIR'):
            self.run_preflight(v176_owner=object())

    def test_06_wrong_owner_source_pin_rejected_before_decision(self):
        with self.assertRaises(InvalidInput):
            self.run_preflight(externally_pinned_source_sha256='f'*64)

    def test_07_wrong_first_head_rejected_before_decision(self):
        with self.assertRaises(InvalidInput):
            self.run_preflight(externally_pinned_first_head_sha256='f'*64)

    def test_08_no_private_v176_db_in_actual_frozen_zip_shape(self):
        with zipfile.ZipFile(self.d/'first.zip') as z:
            names=z.namelist()
        self.assertEqual(set(names),set(['source.srt','native.json','cue250.json',
          'e3_tasks.json','atom_pairs.json','first_turn_research.json',
          'turn1_manual_receipt.json','freeze_manifest.json']))
        self.assertFalse(any(n.endswith(('.db','.sqlite')) for n in names))

    def test_09_no_runtime_store_or_pub_even_for_valid_turn1(self):
        out=self.run_preflight()
        for key in ('e3_final_approved','e4_authorized','e2_independent_gold_certified',
                    'e1_real_owner_full_approval_store_path_proven'):
            self.assertIs(out[key],False)
        self.assertEqual(out['e5_published'],0)

    def test_10_full_frozen_source_and_lexical_counts_rechecked(self):
        out=self.run_preflight()
        self.assertEqual(out['v228_original_cues_rechecked'],8)
        self.assertEqual(out['v228_unapproved_atoms_rechecked'],3)
        self.assertEqual(out['v228_lexical_pairs_rechecked'],3)

    def test_11_bad_json_zip_member_cannot_fake_handoff(self):
        p=self.d/'first.zip'
        with zipfile.ZipFile(p,'r') as z:
            source={n:z.read(n) for n in z.namelist()}
        source['native.json']=b'{}'
        altered=self.d/'altered.zip'
        with zipfile.ZipFile(altered,'w') as z:
            for n,v in source.items():z.writestr(n,v)
        os.chmod(altered,0o600)
        with self.assertRaises(InvalidInput):
            self.run_preflight(private_zip=altered)

    def test_12_second_turn_not_satisfied_by_same_python_call(self):
        # A second Python call with the same PIN is still only one USER turn.
        one=self.run_preflight();two=self.run_preflight()
        self.assertEqual(one['status'],two['status'])
        self.assertFalse(two['v193_real_turn2_host_verified'])

if __name__=='__main__':unittest.main()