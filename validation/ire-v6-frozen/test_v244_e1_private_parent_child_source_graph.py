"""V244 synthetic source graph regressions; NEVER an ETF actual gold."""
import copy,json,unittest
from hashlib import sha256 as hash256
from ire.v6.errors import InvalidInput
from test_v227_e2_source_semantic_reconciliation import synthetic
from v244_e1_private_parent_child_source_graph import (
    source_child_plan,audit_parent_child_lineage,foreign_context_links)

def h(b):return hash256(b).hexdigest()

class V244SourceGraphTests(unittest.TestCase):
    def setUp(self):
        self.doc,*_=synthetic()
        self.args=dict(source_raw=self.doc["srt"],
                       native_raw=self.doc["native"],
                       cue_raw=self.doc["source_triage"],
                       e3_raw=self.doc["canonical_e3"],
                       pairs_raw=self.doc["all_pairs"],
                       expected_source_sha256=h(self.doc["srt"]),
                       expected_native_sha256=h(self.doc["native"]),
                       expected_cue_count=8,expected_child_count=1)
    def runcheck(self,**kw):
        return audit_parent_child_lineage(**dict(self.args,**kw))
    def test_01_full_eight_original_cues_and_three_atoms(self):
        r=self.runcheck()
        self.assertEqual((r["original_cue_count"],r["child_count"],
                          r["atomic_candidate_count"]),(8,1,3))
        self.assertEqual(r["children"][0]["first_cue"],1)
        self.assertEqual(r["children"][0]["last_cue"],8)
        self.assertEqual(len(r["source_cue_hashes"]),8)
        self.assertEqual(r["parent_to_child_lineage_loss_count"],0)
        self.assertFalse(r["e3_final_approved"])
        self.assertFalse(r["e5_knowledge_published"])
    def test_02_original_sha_tamper_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,"OWNER_SOURCE_OR_NATIVE_PIN_DRIFT"):
            self.runcheck(source_raw=self.doc["srt"]+b"X")
    def test_03_native_sha_tamper_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,"OWNER_SOURCE_OR_NATIVE_PIN_DRIFT"):
            self.runcheck(expected_native_sha256="0"*64)
    def test_04_wrong_child_count_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,"THIRTEEN_CHILD_PLAN_CENSUS_DRIFT"):
            self.runcheck(expected_child_count=2)
    def test_05_cue_source_quote_mutation_fails_closed(self):
        d=json.loads(self.doc["source_triage"])
        d["rows"][1]["source_quote"]="위조 원문"
        with self.assertRaises(InvalidInput):
            self.runcheck(cue_raw=json.dumps(d,ensure_ascii=False).encode())
    def test_06_250_cue_source_to_13_child_segmenter_exact_range(self):
        rows=[]
        for i in range(1,251):
            minute=i//60;second=i%60
            time=f"00:{minute:02d}:{second:02d},000"
            end=f"00:{minute:02d}:{second:02d},900"
            rows.append(f"{i}\\n{time} --> {end}\\n가상으로 제공한 자막 문장입니다.")
        raw="\\n\\n".join(rows).encode("utf8")
        plan=source_child_plan(raw,"SYNTHET0001",
                               expected_source_sha256=h(raw),window_size=20)
        self.assertEqual(len(plan["cue_rows"]),250)
        self.assertEqual(len(plan["children"]),13)
        self.assertEqual((plan["children"][-1]["first_cue"],
                          plan["children"][-1]["last_cue"]),(241,250))
        self.assertEqual(plan["children"][0]["child_id"],"B0001")
        self.assertEqual(plan["children"][-1]["child_id"],"B0013")
    def test_07_foreign_context_and_condition_preserved_with_roles(self):
        raw=[]
        for i in range(1,251):
            raw.append(f"{i}\\n00:{i//60:02d}:{i%60:02d},000 --> "
                       f"00:{i//60:02d}:{i%60:02d},900\\n가상 문장입니다.")
        source=source_child_plan("\\n\\n".join(raw).encode(),"SYNTHET0001",
                                 expected_source_sha256=h("\\n\\n".join(raw).encode()))["source"]
        atom={"claim_id":"C00001","owner_window_id":"W00013",
              "source_refs":[{"cue_index":246,"quote":"가상 문장입니다."}],
              "context_cue_indices":[45,246],
              "condition_cue_indices":[45],
              "exception_cue_indices":[],
              "numeric_references":[]}
        links=foreign_context_links(source,[atom])
        self.assertEqual(len(links),1)
        self.assertEqual(links[0]["referenced_cue_index"],45)
        self.assertEqual(links[0]["referenced_child_id"],"B0003")
        self.assertEqual(links[0]["owner_child_id"],"B0013")
        self.assertEqual(links[0]["foreign_reference_roles"],
                         ["condition_cue_indices","context_cue_indices"])
    def test_08_out_of_scope_context_is_rejected(self):
        from v176_chat_engine_loop import make_original_plan
        source,_=make_original_plan(self.doc["srt"],"SYNTHET0001",
            expected_source_sha256=h(self.doc["srt"]),window_size=20)
        x={"claim_id":"C00001","owner_window_id":"W00001",
            "source_refs":[],"context_cue_indices":[9],
            "condition_cue_indices":[],"exception_cue_indices":[],
            "numeric_references":[]}
        with self.assertRaisesRegex(InvalidInput,"CROSS_CONTEXT_SOURCE_OUTSIDE_PARENT"):
            foreign_context_links(source,[x])

if __name__=="__main__":
    unittest.main()
