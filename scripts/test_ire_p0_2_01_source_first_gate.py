"""P201 source-first 250/250 contract; genuine private source in Library, NOT CI."""
from __future__ import annotations
import copy,unittest
from scripts.ire_p0_2_01_source_first_gate import ROOT,RECEIPT,STATE,LEDGER,P102,P103,load,verify

class P201Cue250EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(load(ROOT,RECEIPT),load(ROOT,STATE),load(ROOT,LEDGER),
                      load(ROOT,P102),load(ROOT,P103))
    def setUp(self):
        self.r,self.s,self.l,self.p102,self.p103=copy.deepcopy(self.original)
    def issues(self):
        return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,
                      p102=self.p102,p103=self.p103)
    def bad(self,code):
        errors=self.issues()
        self.assertTrue(any(code in x for x in errors),errors)
    def test_01_contract_source_first_250_not_financial_approval(self):
        self.assertEqual([],self.issues())
    def test_02_one_cue_changed(self):
        self.r["disposition_vector"]="F"+self.r["disposition_vector"][1:]
        self.bad("LABEL_VECTOR")
    def test_03_last_cue_missing(self):
        self.r["disposition_vector"]=self.r["disposition_vector"][:-1]
        self.bad("LABEL_VECTOR")
    def test_04_duplicate_cue_appended(self):
        self.r["disposition_vector"]+="O"
        self.bad("LABEL_VECTOR")
    def test_05_original_source_sha_tamper(self):
        self.r["original_srt_sha256"]="0"*64
        self.bad("ORIGINAL_SOURCE")
    def test_06_historical_p102_original_graph_tamper(self):
        self.p102["source_graph_canonical_sha256"]="0"*64
        self.bad("ORIGINAL_SOURCE")
    def test_07_one_quote_drift_not_ignored(self):
        self.r["source_cue_quote_mismatch_count"]=1
        self.bad("SOURCE_CUE250")
    def test_08_one_missing_cue_not_ignored(self):
        self.r["source_cue_missing_count"]=1
        self.bad("SOURCE_CUE250")
    def test_09_fake_independent_gold(self):
        self.r["not_an_independent_gold_label_set"]=False
        self.bad("FALSE_GOLD")
    def test_10_forged_precision(self):
        self.r["formal_e2_precision"]=.99
        self.bad("FALSE_GOLD")
    def test_11_noatom_false_certainty(self):
        self.r["no_atom_does_not_certify_absence_of_all_hidden_claims"]=False
        self.bad("FALSE_GOLD")
    def test_12_unsupported_audio_truth(self):
        self.r["audio_source_confirmed"]=True
        self.bad("FALSE_GOLD")
    def test_13_12_issue_groups_unaltered(self):
        self.r["unresolved_issue_groups"].pop()
        self.bad("12_RISK_GROUPS")
    def test_14_cross_index_qualifier_47_missing(self):
        self.r["index_etf_only_scope_cues"]=[45,46]
        self.bad("12_RISK_GROUPS")
    def test_15_32_legacy_open_not_silently_approved(self):
        self.r["previous_native_primary_anchor_cues_now_OPEN_source_first"]=0
        self.bad("OLD_68_ATOMS")
    def test_16_e5_real_publication_forgery(self):
        self.r["actual_etf_e5_parent_publications"]=1
        self.bad("ETF_E3_E4_E5")
    def test_17_private_content_exposure_blocked(self):
        self.r["public_artifact_contains_original_caption_text"]=True
        self.bad("PUBLIC_PRIVACY")
    def test_18_next_item_wrong_cursor(self):
        self.l["development_gate"]["this_item"]="P0-2-06"
        self.bad("LEDGER_NEXT")
    def test_19_no_skip_to_next_p203(self):
        # First blocked successor beyond the live active cursor, not the
        # historical P201 successor: P203 can legitimately be READY later.
        pos=next(i for i,x in enumerate(self.s["items"]) if x["status"]!="PASS")
        self.s["items"][pos+1]["status"]="READY"
        self.bad("ONLY_P202_NEXT")
    def test_21_open_cue_without_risk_docket_rejected(self):
        group=next(x for x in self.r["unresolved_issue_groups"]
                   if x["id"]=="P201-R07")
        group["cue_indices"].remove(123)
        self.bad("OPEN_CUE_WITHOUT_ESCALATION_DOCKET")
    def test_20_private_zip_sha_pin_required(self):
        self.r["private_review_package_sha256"]="0"*64
        self.bad("PRIVATE_EVIDENCE_SHA")

if __name__=="__main__":
    unittest.main()
