"""Private V3 journal synthetic regression, not semantic or financial truth."""
import copy,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_source_graph import compile_graph,compare_graphs,score_graphs
from ire.v6.semantic_graph_journal import GraphJournal,plan_for,revision,adjudicate_disputes
from ire.v6.tests.test_semantic_source_graph import SourceGraphTests

class GraphJournalTests(unittest.TestCase):
    def setUp(self):
        self.f=SourceGraphTests();self.f.setUp()
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"private.db"
        self.args={"source_sha":sha256(self.f.raw),"manifest_sha":json_digest(self.f.m)}
        self.j=GraphJournal(self.path,self.f.raw,self.f.m,create=True,**self.args)
        self.plan=plan_for(self.f.s,campaign_id="synthetic_graph",engine_commit="a"*40",
             registered_at="2026-01-01T00:00:00+00:00",purpose="DEVELOPMENT")
        self.first={"user_ref":"actual-label-first","observed_at":"2026-01-01T00:01:00+00:00","packet":self.f.first}
        self.second={"user_ref":"actual-label-second","observed_at":"2026-01-01T00:02:00+00:00","packet":self.f.second}
    def freeze(self):
        self.j.append("REGISTER",self.plan);self.j.append("FIRST",self.first);self.j.append("SECOND",self.second)
    def complete(self):
        self.freeze()
        a=compile_graph(self.f.s,self.f.first);b=compile_graph(self.f.s,self.f.second)
        al=self.f.alignment();r=score_graphs(self.f.s,self.f.first,self.f.second,al)
        self.j.append("SCORE",{"alignment":al,"result":r})
        comps=compare_graphs(a,b)["components"]
        self.j.append("DISPUTES",[{"component_sha256":json_digest(c),"verdict":"EQUIVALENT",
            "reason":"Explicit synthetic reviewer decision.","evidence":[self.f.full(1)]} for c in comps])
        l=[{"old_ids":["A00001"],"new_ids":["A00001"],"operation":"KEEP","reason":"Same frozen first claim.","losses":[]}]
        m=[{**l[0],"operation":"REVISE","reason":"Reconciled textual speaker hypothesis."}]
        rev=revision(self.f.s,a,b,self.f.first,l,m)
        val={"packet":self.f.first,"first_lineage":l,"second_lineage":m,"receipt":rev}
        self.j.append("REVISION",val);return val
    def test_complete_reopen_and_exact_retry(self):
        val=self.complete();snap=self.j.snapshot()
        self.assertEqual(snap["event_count"],6)
        self.assertEqual(self.j.append("REVISION",val),snap["head_sha256"])
        other=GraphJournal(self.path,self.f.raw,self.f.m,expected_head=self.j.head,**self.args)
        self.assertEqual(other.snapshot(),snap);self.assertFalse(snap["publication_authorized"])
    def test_same_turn_or_copied_packet_rejected(self):
        self.j.append("REGISTER",self.plan);self.j.append("FIRST",self.first)
        head=self.j.head
        with self.assertRaisesRegex(InvalidInput,"SAME_USER_REF"):self.j.append("SECOND",{**self.second,"user_ref":self.first["user_ref"]})
        with self.assertRaisesRegex(InvalidInput,"COPIED_PACKET"):self.j.append("SECOND",{**self.second,"packet":self.f.first})
        self.assertEqual(self.j.snapshot()["head_sha256"],head)
    def test_wrong_external_head_and_sql_mutation(self):
        self.freeze()
        with self.assertRaises(InvalidInput):GraphJournal(self.path,self.f.raw,self.f.m,expected_head="f"*64,**self.args)
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE events SET kind='FIRST' WHERE seq=1")
    def test_forged_score_and_out_of_order(self):
        self.freeze()
        with self.assertRaisesRegex(InvalidInput,"SCORE_DRIFT"):self.j.append("SCORE",{"alignment":self.f.alignment(),"result":{"tp":99}})
        with self.assertRaisesRegex(InvalidInput,"EVENT_ORDER"):self.j.append("REVISION",{})
        self.assertEqual(self.j.snapshot()["event_count"],3)
    def test_missing_dispute(self):
        a=compile_graph(self.f.s,self.f.first);b=compile_graph(self.f.s,self.f.second)
        with self.assertRaisesRegex(InvalidInput,"DISPUTE_CENSUS"):adjudicate_disputes(self.f.s,a,b,[])
    def test_missing_numeric_disposition_and_false_keep(self):
        a=compile_graph(self.f.s,self.f.first);b=compile_graph(self.f.s,self.f.second)
        p=copy.deepcopy(self.f.first);p["nodes"][0]["numbers"]=[]
        l=[{"old_ids":["A00001"],"new_ids":["A00001"],"operation":"REVISE","reason":"Number removed without grounds.","losses":[]}]
        with self.assertRaisesRegex(InvalidInput,"UNACCOUNTED_NUMERIC_OR_QUALIFIER_LOSS"):revision(self.f.s,a,b,p,l,l)
        l[0]["operation"]="KEEP"
        with self.assertRaisesRegex(InvalidInput,"LINEAGE_KEEP_FALSE"):revision(self.f.s,a,b,p,l,l)
    def test_missing_lineage(self):
        a=compile_graph(self.f.s,self.f.first);b=compile_graph(self.f.s,self.f.second)
        with self.assertRaisesRegex(InvalidInput,"LINEAGE_ROWS"):revision(self.f.s,a,b,self.f.first,[],[])
