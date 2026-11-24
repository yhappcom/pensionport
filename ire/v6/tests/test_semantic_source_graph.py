"""V3 synthetic semantic-coordinate contract, never actual financial gold."""
import copy,unittest
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.semantic_source_graph import (source_grid,compile_graph,numeric_binding,
    compare_graphs,score_graphs,overlap_components,legacy_quote_spans)

class SourceGraphTests(unittest.TestCase):
    def setUp(self):
        self.raw=make_srt(["인출액은 2억","3천만 원입니다.","자격을 갖춘 경우입니다.","종료합니다."])
        self.m=make_manifest(self.raw)
        self.s=verify_source(self.raw,self.m,expected_source_sha256=sha256(self.raw),
                             expected_manifest_sha256=json_digest(self.m))
        self.full=lambda i:[i,0,len(self.s.cues[i-1].text)]
        self.num=[[1,5,7],[2,0,5]]
        # Compute literal boundaries from the original fixture, not a derived amount.
        self.num=[[1,self.s.cues[0].text.index("2억"),len(self.s.cues[0].text)],
                  [2,0,self.s.cues[1].text.index("입니다")]]
        node={"predicate":"인출액을 제시합니다.","atomicity_reason":"One conditional amount assertion.",
              "kind":"FACT","utterance_act":"ASSERTION",
              "speaker":{"participant_id":"S00001","status":"TEXT_INFERRED","evidence":[self.full(1)],
                         "reason":"Textual participant hypothesis only."},
              "attribution":"DIRECT","attributed_participant":None,"polarity":"AFFIRMED",
              "modality":"CONDITIONAL","correction":False,"as_of":None,
              "direct":[self.full(1),self.full(2)],"context":[],
              "qualifiers":[{"type":"CONDITION","span":self.full(3),"reason":"Governs the amount assertion."}],
              "numbers":[{"parts":self.num,"function":"AMOUNT","reason":"Adjacent amount continuation."}],
              "risk":"HIGH","risk_reason":"Amount and eligibility are material."}
        self.first={"schema":"IRE_V3_SEMANTIC_GRAPH_PACKET_V1","grid_sha256":json_digest(source_grid(self.s)),
                    "nodes":[node],"residual":[{"span":self.full(4),"status":"NONCLAIM","reason":"Closing phrase."}]}
        self.second=copy.deepcopy(self.first)
        self.second["nodes"][0]["speaker"]["participant_id"]="S00002"
        self.second["nodes"][0]["atomicity_reason"]="Separate second-turn judgment."

    def test_cross_cue_literal_and_census(self):
        a=compile_graph(self.s,self.first)
        self.assertEqual(a["nodes"]["A00001"]["numbers"][0]["literal"],"2억 3천만 원")
        self.assertTrue(a["nodes"]["A00001"]["numbers"][0]["cross_cue"])
        self.assertEqual([],a["unbound_numeric_spans"])
        self.assertFalse(a["speaker_identity_authenticated"])
        self.assertEqual(a,compile_graph(self.s,self.first))

    def test_no_silent_gap(self):
        self.first["residual"]=[]
        with self.assertRaisesRegex(InvalidInput,"SILENT_SOURCE_GAP"):compile_graph(self.s,self.first)

    def test_residual_must_not_hide_direct(self):
        self.first["residual"].append({"span":self.full(1),"status":"NONCLAIM","reason":"Incorrect hidden source."})
        with self.assertRaisesRegex(InvalidInput,"RESIDUAL_CONFLICT"):compile_graph(self.s,self.first)

    def test_number_nonconsecutive(self):
        with self.assertRaisesRegex(InvalidInput,"NUMBER_NONCONTIGUOUS"):
            numeric_binding(self.s,[self.num[0],self.full(3)])

    def test_truncated_cross_cue_number_blocked(self):
        for part in self.num:
            with self.assertRaisesRegex(InvalidInput,"NUMBER_BOUNDARY"):
                numeric_binding(self.s,[part])

    def test_missing_numeric_binding_visible(self):
        self.first["nodes"][0]["numbers"]=[]
        self.assertTrue(compile_graph(self.s,self.first)["unbound_numeric_spans"])

    def test_context_number_not_predicate_number(self):
        node=self.first["nodes"][0];node["context"]=[self.full(2)]
        node["direct"]=[self.full(1)]
        with self.assertRaisesRegex(InvalidInput,"NUMBER_OUTSIDE_PREDICATE"):compile_graph(self.s,self.first)

    def test_missing_condition(self):
        self.first["nodes"][0]["qualifiers"]=[]
        with self.assertRaisesRegex(InvalidInput,"CONDITION_MISSING"):compile_graph(self.s,self.first)

    def test_span_overlap_is_not_equivalence(self):
        a=compile_graph(self.s,self.first);b=compile_graph(self.s,self.second)
        diag=compare_graphs(a,b)
        self.assertEqual(diag["components"][0]["shape"],"ONE_TO_ONE")
        self.assertIsNone(diag["tp"])
        self.assertFalse(diag["semantic_equivalence_proven"])
        comps=overlap_components({"A":[[1,0,5]]},{"B":[[1,0,2]],"C":[[1,2,5]]})
        self.assertEqual(comps[0]["shape"],"SPLIT_CANDIDATE")

    def alignment(self):
        a=compile_graph(self.s,self.first);b=compile_graph(self.s,self.second)
        return {"first_packet_sha256":a["packet_sha256"],"second_packet_sha256":b["packet_sha256"],
                "speaker_aliases":[{"first":"S00001","second":"S00002","reason":"Textual source mapping.",
                                    "evidence":[self.full(1)]}],
                "pairs":[{"prediction_id":"A00001","reference_id":"A00001",
                          "axes":{k:True for k in MATCH_FIELDS},
                          "reasons":{k:"Synthetic explicit adjudication." for k in MATCH_FIELDS}}],
                "unmatched_prediction_ids":[],"unmatched_reference_ids":[],"unmatched_reasons":{}}

    def test_explicit_nine_axis_score_not_release(self):
        r=score_graphs(self.s,self.first,self.second,self.alignment())
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(1,0,0))
        self.assertTrue(r["thresholds_met_on_supplied_internal_graphs"])
        self.assertFalse(r["operational_release_authorized"])
        self.assertFalse(r["independent_gold_verified"])

    def test_unknown_alias_not_automatically_same(self):
        al=self.alignment();al["speaker_aliases"]=[]
        with self.assertRaisesRegex(InvalidInput,"FALSE_SPEAKER_MATCH"):
            score_graphs(self.s,self.first,self.second,al)

    def test_numeric_omission_cannot_be_exact(self):
        self.second["nodes"][0]["numbers"]=[]
        al=self.alignment()
        with self.assertRaisesRegex(InvalidInput,"FALSE_NUMERIC_MATCH"):
            score_graphs(self.s,self.first,self.second,al)

    def test_open_source_is_not_pass(self):
        self.second["residual"][0]["status"]="OPEN"
        r=score_graphs(self.s,self.first,self.second,self.alignment())
        self.assertFalse(r["thresholds_met_on_supplied_internal_graphs"])
        self.assertGreater(r["open_source_characters"],0)
