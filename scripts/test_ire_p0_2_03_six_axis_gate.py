"""P203 SHA-only contract; real owner caption bytes validated privately, not CI."""
from __future__ import annotations
import copy,unittest
from scripts.ire_p0_2_03_six_axis_gate import ROOT,P203,STATE,LEDGER,P201,P202,P103,load,verify
class P203CuesAtomsSemanticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.baseline=(load(ROOT,p) for p in (P203,STATE,LEDGER,P201,P202,P103))
  cls.baseline=tuple(cls.baseline)
 def setUp(self):
  self.r,self.s,self.l,self.p201,self.p202,self.p103=copy.deepcopy(self.baseline)
 def errs(self):return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,p201=self.p201,p202=self.p202,p103=self.p103)
 def bad(self,name):self.assertTrue(any(name in x for x in self.errs()),self.errs())
 def test_01_actual_public_sha_only_contract(self):self.assertEqual([],self.errs())
 def test_02_original_250_cue_missing(self):
  self.r["source_cue_total"]=249;self.bad("250_CUE_68_ATOM")
 def test_03_wrong_private_digest(self):
  self.r["p203_private_source_semantic_json_sha256"]="0"*64;self.bad("SOURCE_HASH")
 def test_04_owner_package_sha_tampered(self):
  self.r["p203_private_package_sha256"]="0"*64;self.bad("SOURCE_HASH")
 def test_05_last_cue_removed(self):
  self.r["cue_coverage"]["unlinked_provisional_no_finance_absence_proof"]=13;self.bad("CUE_COVERAGE")
 def test_06_114_claim_omission_census_erased(self):
  self.r["source_first_fact_opinion_without_primary_refs_total"]=0;self.bad("HIDDEN_OMISSION")
 def test_07_seven_unreferenced_cues_silenced(self):
  self.r["individually_adjudicated_didactic_cues"].pop();self.bad("HIDDEN_OMISSION")
 def test_08_wrong_68_atom_count(self):
  self.r["existing_unapproved_atom_total"]=67;self.bad("250_CUE_68_ATOM")
 def test_09_rhetorical_question_promoted(self):
  self.r["rhetorical_questions"]=[16,53];self.bad("SPEAKER_NEGATION")
 def test_10_speaker_audio_falsely_verified(self):
  self.r["speaker_voice_audio_authenticated"]=True;self.bad("SPEAKER_NEGATION")
 def test_11_65_negation_cue_dropped(self):
  self.r["explicit_negation_and_caveat_anchor_cues"].remove(65);self.bad("SPEAKER_NEGATION")
 def test_12_index_condition_cue47_lost(self):
  self.r["index_etf_global_scope_condition_cues"]=[45,46];self.bad("INHERITED_INDEX")
 def test_13_cross_edges_cannot_disappear(self):
  self.r["cross_scope_edge_count"]=48;self.bad("21_ATOM_49_EDGE")
 def test_14_tracking_single_return_forgery(self):
  self.r["hypothetical_tracking_example"]["statistical_tracking_error_from_two_returns_certified"]=True;self.bad("TRACKING_DIFFERENCE")
 def test_15_nav_spread_not_percentage(self):
  self.r["hypothetical_premium_case"]["nav_based_premium_percent"]=-83;self.bad("FICTIONAL_NAV")
 def test_16_fictional_screen_real_price_forgery(self):
  self.r["hypothetical_premium_case"]["screen_actual_data_verified"]=True;self.bad("FICTIONAL_NAV")
 def test_17_semantic_pair_auto_merge_not_allowed(self):
  self.r["exact_duplicate_merges_authorized"]=1;self.bad("DEDUP_RISK")
 def test_18_36_unsafe_original_atoms_cannot_be_approved(self):
  self.r["unresolved_and_repair_blocked_original_atoms"]=0;self.bad("36_UNREPAIRED")
 def test_19_fake_independent_recall(self):
  self.r["independent_recall"]=0.99;self.bad("FALSE_FINANCE")
 def test_20_fake_e3_release(self):
  self.r["e3_v123_approved_children"]=13;self.bad("FALSE_FINANCE")
 def test_21_wrong_step_order(self):
  self.s["items"][16]["status"]="READY";self.bad("CHECKLIST_INVALID")
 def test_22_wrong_current_development_cursor(self):
  self.l["development_gate"]["this_item"]="P0-2-05";self.bad("LEDGER_LIVE_CURSOR")
 def test_23_source_quote_exposed_claim(self):
  self.r["public_original_source_text_included"]=True;self.bad("PUBLIC_EXPOSURE")
 def test_24_68_status_count_drift(self):
  self.r["source_first_68_statuses_preserved"]["KEEP"]=33;self.bad("36_UNREPAIRED")
 def test_25_10_priority_corrections_not_lost(self):
  self.r["correction_action_ids"].pop();self.bad("DEDUP_RISK")
if __name__=="__main__":unittest.main()
