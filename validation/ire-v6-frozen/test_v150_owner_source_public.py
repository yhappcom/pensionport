import copy,json,unittest
from pathlib import Path
from v150_source_evidence_contract import audit_public_owner_progress,SourceContractError

ROOT=Path(__file__).resolve().parent

class V150OwnerSourcePublic(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'V150_PUBLIC_SOURCE_SHA_ONLY.json').read_text('utf-8'))
    def test_01_real_1481_source_census_and_17_reviewed_holds(self):
        x=audit_public_owner_progress(self.data)
        self.assertFalse(x['p0_e_go'])
        self.assertEqual(x['unreferenced_pending'],237)
    def test_02_made_up_accuracy_pass_rejected(self):
        for key in ('p0e_go','full_precision_recall_measured','b0012_full_precision_recall_measured'):
            a=copy.deepcopy(self.data);a[key]=True
            with self.subTest(key=key),self.assertRaises(SourceContractError):audit_public_owner_progress(a)
    def test_03_missing_source_cue_rejected(self):
        a=copy.deepcopy(self.data);a['unreferenced_queue_still_pending']=236
        with self.assertRaises(SourceContractError):audit_public_owner_progress(a)
    def test_04_v123_approval_forgery_rejected(self):
        a=copy.deepcopy(self.data);a['real_v123_approved_scopes']=13
        with self.assertRaises(SourceContractError):audit_public_owner_progress(a)
    def test_05_source_sha_change_rejected(self):
        a=copy.deepcopy(self.data);a['source_sha256']='0'*64
        with self.assertRaises(SourceContractError):audit_public_owner_progress(a)

if __name__=='__main__':unittest.main()
