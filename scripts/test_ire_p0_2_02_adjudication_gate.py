"""P0-2-02 negative tests for SHA-only public receipt (not independent financial gold)."""
import copy,unittest
from scripts.ire_p0_2_02_adjudication_gate import ROOT,RECEIPT,STATE,LEDGER,load,verify
class P202SourceCrossAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(load(ROOT,RECEIPT),load(ROOT,STATE),load(ROOT,LEDGER))
    def setUp(self):
        self.r,self.s,self.l=copy.deepcopy(self.base)
    def problems(self):
        return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l)
    def expect(self,s):
        p=self.problems()
        self.assertTrue(any(s in e for e in p),p)
    def test_01_valid_sha_only_record(self):
        self.assertEqual([],self.problems())
    def test_02_one_atom_lost(self):
        self.r["dispositions"]["KEEP"]["ids"].pop()
        self.expect("DISPOSITION_IDS")
    def test_03_one_atom_duplicated(self):
        self.r["dispositions"]["OPEN"]["ids"][0]=self.r["dispositions"]["KEEP"]["ids"][0]
        self.expect("DISPOSITION_DUPLICATE")
    def test_04_source_sha_changed(self):
        self.r["original_srt_sha256"]="0"*64
        self.expect("EVIDENCE_SHA")
    def test_05_private_package_changed(self):
        self.r["private_decision_package_zip_sha256"]="0"*64
        self.expect("EVIDENCE_SHA")
    def test_06_condition_47_discarded(self):
        self.r["b0013_c00057"]["foreign_condition_cues"]=[45,46]
        self.expect("FOREIGN_INDEX_CONDITION")
    def test_07_numeric_references_dropped(self):
        self.r["cross_reference_roles"]["numeric"]=2
        self.expect("SOURCE_AND_CROSS_EDGE_CENSUS")
    def test_08_unverified_cue_count_clipped(self):
        self.r["original_source_cues_verified"]=249
        self.expect("SOURCE_AND_CROSS_EDGE_CENSUS")
    def test_09_fake_financial_gold(self):
        self.r["independent_precision"]=0.99
        self.expect("FALSE_GOLD_AUDIO_OR_APPROVAL")
    def test_10_fake_e3_release(self):
        self.r["e3_children_approved"]=13
        self.expect("FALSE_GOLD_AUDIO_OR_APPROVAL")
    def test_11_false_source_video_certainty(self):
        self.r["real_video_frame_verified"]=True
        self.expect("FALSE_GOLD_AUDIO_OR_APPROVAL")
    def test_12_wrong_next_cursor(self):
        self.l["development_gate"]["pending_next_item"]="P0-2-04"
        self.expect("LIVE_CURSOR_MISMATCH")
    def test_13_two_next_items_not_allowed(self):
        self.s["items"][15]["status"]="READY"
        self.expect("CHECKLIST_INVALID")
    def test_14_forget_original_exception_lineage(self):
        self.r["zero_conditions_exceptions_numeric_dropped"]=False
        self.expect("LOSSLESS")
    def test_15_forged_library_custody(self):
        self.r["private_library_upload_succeeded"]=False
        self.expect("PRIVATE_LIBRARY_CUSTODY")
if __name__=="__main__":unittest.main()
