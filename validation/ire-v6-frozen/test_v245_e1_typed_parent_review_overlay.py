"""V245 PRIVATE overlay; fixtures are invented, never actual ETF approval."""
import copy, json, unittest
from hashlib import sha256 as H
from ire.v6.errors import InvalidInput
from test_v227_e2_source_semantic_reconciliation import synthetic
from v244_e1_private_parent_child_source_graph import (
    audit_parent_child_lineage, source_child_plan)
from v245_e1_typed_parent_review_overlay import (
    typed_parent_atom_review, build_typed_parent_review_overlay,
    verify_typed_parent_review_overlay, _extract_foreign_edges)

def hh(b):return H(b).hexdigest()


class TypedParentReviewTests(unittest.TestCase):
    def setUp(self):
        self.docs,*_=synthetic()
        self.args=dict(source_raw=self.docs["srt"],
            native_raw=self.docs["native"],cue_raw=self.docs["source_triage"],
            e3_raw=self.docs["canonical_e3"],pairs_raw=self.docs["all_pairs"],
            expected_source_sha256=hh(self.docs["srt"]),
            expected_native_sha256=hh(self.docs["native"]),
            expected_cue_count=8,expected_child_count=1,
            expected_atom_count=3,expected_cross_atom_count=0,
            expected_cross_edge_count=0)
        g=audit_parent_child_lineage(
            self.docs["srt"],self.docs["native"],
            self.docs["source_triage"],self.docs["canonical_e3"],
            self.docs["all_pairs"],expected_source_sha256=self.args["expected_source_sha256"],
            expected_native_sha256=self.args["expected_native_sha256"],
            expected_cue_count=8,expected_child_count=1)
        self.args["expected_graph_sha256"]=g["source_graph_sha256"]

    def build(self,**updates):
        return build_typed_parent_review_overlay(**dict(self.args,**updates))

    def test_01_source_full_v6_atoms_preserved(self):
        result=self.build()
        self.assertEqual((result["cue_count"],result["child_count"],
                          result["atom_count"]),(8,1,3))
        atoms=result["child_review_inputs"][0]["parent_atom_review_tasks"]
        self.assertEqual(len(atoms),3)
        native=json.loads(self.docs["native"])
        self.assertEqual([a["full_original_parent_atom"] for a in atoms],
                         native["atoms"])
        self.assertFalse(result["e3_final_approved"])
        self.assertFalse(result["e5_published"])

    def test_02_private_source_replay_and_owner_digest_pass(self):
        r=self.build()
        out=verify_typed_parent_review_overlay(
            r,expected_overlay_sha256=r["typed_overlay_sha256"],
            **self.args)
        self.assertEqual(out["child_count"],1)
        self.assertFalse(out["e3_approved"])

    def test_03_source_quote_tamper_rejected(self):
        r=self.build()
        r["child_review_inputs"][0]["source_first_cues_exact"][0]["quote"]="변조"
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_CUE"):
            verify_typed_parent_review_overlay(
                r,expected_overlay_sha256=r["typed_overlay_sha256"],**self.args)

    def test_04_full_atom_condition_tamper_rejected(self):
        r=self.build()
        r["child_review_inputs"][0]["parent_atom_review_tasks"][0][
            "full_original_parent_atom"]["context_cue_indices"]=[]
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_CUE"):
            verify_typed_parent_review_overlay(
                r,expected_overlay_sha256=r["typed_overlay_sha256"],**self.args)

    def test_05_explicit_outdated_parent_graph_pin_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"PARENT_SOURCE_GRAPH_PIN_DRIFT"):
            self.build(expected_graph_sha256="0"*64)

    def test_06_expected_count_cannot_be_forged(self):
        with self.assertRaisesRegex(InvalidInput,"ATOM_OR_CROSS_EDGE_CENSUS_DRIFT"):
            self.build(expected_cross_edge_count=49)

    def test_07_cross_b0013_inherited_conditions_text_and_roles(self):
        # 250 original *invented* cue texts; no financial fact asserted.
        rows=[]
        for i in range(1,251):
            t=f"00:{i//60:02d}:{i%60:02d},000"
            e=f"00:{i//60:02d}:{i%60:02d},800"
            rows.append(f"{i}\n{t} --> {e}\n합성 ETF 조건 {i}.")
        raw="\n\n".join(rows).encode("utf8")
        source=source_child_plan(raw,"SYNTHET0001",
                    expected_source_sha256=hh(raw))["source"]
        a={"claim_id":"C00057","owner_window_id":"W00013",
           "source_refs":[{"cue_index":246,"quote":"합성 ETF"}],
           "context_cue_indices":[45,46,47,244,245,246,247],
           "condition_cue_indices":[45,46,47,244,245],
           "exception_cue_indices":[],"numeric_references":[
               {"cue_index":45,"token":"45"}],
           "proposition":"합성 ETF 비교 권고","kind":"RECOMMENDATION",
           "stance":"UNRESOLVED","speaker":"UNKNOWN","as_of":None}
        task=typed_parent_atom_review(a,source,"B0013")
        foreign=[x for x in task["typed_source_references"]
                 if x["external_to_owner_child"]]
        self.assertEqual([x["cue_index"] for x in foreign],[45,46,47])
        self.assertTrue(all(x["source_child_id"]=="B0003" and
                            "CONDITION" in x["reference_roles"] for x in foreign))
        self.assertEqual([x["numeric_tokens_exact"] for x in foreign][0],["45"])
        self.assertEqual(task["full_original_parent_atom"],a)
        self.assertEqual(_extract_foreign_edges([{"parent_atom_review_tasks":[task]}])
            [0]["foreign_reference_roles"],
            ["condition_cue_indices","context_cue_indices","numeric_references"])

    def test_08_required_c00057_mismatch_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,"REQUIRED_CROSS_CLAIM_NOT_FOUND"):
            self.build(required_cross_scope_claim={
                "claim_id":"C00057","owner_child_id":"B0013",
                "primary_cue_index":246,
                "inherited_condition_cue_indices":[45,46,47]})

    def test_09_original_source_changed_with_unmodified_pin_rejected(self):
        with self.assertRaises(InvalidInput):
            self.build(source_raw=self.docs["srt"]+b"\n")

if __name__=="__main__":
    unittest.main()
