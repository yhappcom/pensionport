"""V5 transaction core synthetic tests. Not an independent semantic evaluation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from ire.v5.engine import ResearchRun,RunError,sha256

SRT=b"""1
00:00:00,000 --> 00:00:01,000
Questioner has an estimated pension.

2
00:00:01,100 --> 00:00:02,000
Monthly income is uncertain.

3
00:00:02,100 --> 00:00:03,000
There is a possible withdrawal limit.

4
00:00:03,100 --> 00:00:04,000
The account outcome varies by rule.

5
00:00:04,100 --> 00:00:05,000
A second scenario compares taxation.

6
00:00:05,100 --> 00:00:06,000
Individual tax information is missing.
"""
TEXT={1:"Questioner has an estimated pension.",2:"Monthly income is uncertain.",
      3:"There is a possible withdrawal limit.",4:"The account outcome varies by rule.",
      5:"A second scenario compares taxation.",6:"Individual tax information is missing."}
WINS=[]
for j,(start,end) in enumerate([(1,2),(3,4),(5,6)],1):
    WINS.append({"window_id":f"W{j:05d}","primary_cue_ids":list(range(start,end+1)),
                 "primary_text_sha256":sha256(" ".join(TEXT[i] for i in range(start,end+1)).encode())})
MAN={"schema":"IRE_V5_SOURCE_PLAN_V1","video_id":"sz5N9WJS310",
     "source_sha256":sha256(SRT),"source_cues":6,"planner_version":"TEST_STATIC_SOURCE_PLAN",
     "prior_baseline_git_blob_sha":"a"*40,
     "active_window_ids":[w["window_id"] for w in WINS],"windows":WINS}

class V5ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Path(self.temp.name)/"private"
        self.r=ResearchRun(SRT,MAN,self.store)
    def model(self,n):
        wid=f"W{n:05d}";p=self.r.packet(wid)
        ids=WINS[n-1]["primary_cue_ids"]
        cid=f"V5C{n:04d}"
        return {"schema":"IRE_V5_MODEL_WINDOW_V1","window_id":wid,
                "claimed_author":"CURRENT_CHATGPT_CONVERSATION",
                "independent_human_verified":False,"packet_sha256":p["packet_sha256"],
                "claims":[{"claim_id":cid,"proposition":"The hypothetical case is contingent on personal conditions.",
                           "kind":"HYPOTHETICAL","requires_external_verification":True,
                           "fact_verified":False,"advisory_approved":False,
                           "source_refs":[{"cue_index":i,"quote":TEXT[i]} for i in ids]}],
                "cue_dispositions":[{"cue_index":i,"status":"LINKED","claim_ids":[cid],"reason":None} for i in ids]}
    def evidence(self,n):
        return {"schema":"IRE_V5_EVIDENCE_CASE_V1","claim_id":f"V5C{n:04d}",
                "status":"OPEN_PERSONAL_DATA","search_query":"official pension personalized eligibility",
                "financial_truth_approved":False,"open_reason":"Individual records are missing.",
                "investigation_summary":"Looked for the official rules; person-specific records missing."}
    def relation(self,n):
        return {"schema":"IRE_V5_PRIOR_RELATION_V1","claim_id":f"V5C{n:04d}",
                "prior_baseline_git_blob_sha":"a"*40,"prior_claim_ids":[],
                "status":"NO_RELEVANT_PRIOR_WITH_SEARCH","search_terms":["pension","tax"],
                "review_notes":"Prior study was searched and no exact same-scope claim was found.",
                "automerge":False,"financial_truth_approved":False}
    def accept_all(self):
        for n in (1,2,3):self.r.append('MODEL_ANALYSIS',self.model(n))
        for n in (1,2,3):self.r.append('EVIDENCE_REVIEW',self.evidence(n))
        for n in (1,2,3):self.r.append('PRIOR_RELATION_REVIEW',self.relation(n))
    def test_host_next_task_routes_all_stages_without_continue(self):
        # A deterministic synthetic host supplies prepared answers. Real model
        # interpretation still belongs to ChatGPT, not the Python program.
        trace=[]
        while True:
            task=self.r.next_task()
            self.assertFalse(task["user_continue_requested"])
            phase=task["phase"];trace.append(phase)
            if phase=="MODEL_ANALYSIS_REQUIRED":
                self.r.append("MODEL_ANALYSIS",self.model(int(task["window_id"][-5:])))
            elif phase=="OFFICIAL_EVIDENCE_REVIEW_REQUIRED":
                self.r.append("EVIDENCE_REVIEW",self.evidence(int(task["claim_id"][-4:])))
            elif phase=="PRIOR_KNOWLEDGE_REVIEW_REQUIRED":
                self.r.append("PRIOR_RELATION_REVIEW",self.relation(int(task["claim_id"][-4:])))
            elif phase=="SEAL_RESEARCH_REPORT_REQUIRED":
                self.r.close()
            elif phase=="DONE":
                break
            else:
                self.fail("Unexpected task: "+str(task))
        self.assertEqual(len(trace),11)  # 3 x (model,evidence,relation) + seal + done
        self.assertTrue(self.r.status()["sealed"])

    def test_happy_path_reports_open_no_approval_and_reopens(self):
        self.accept_all();out=self.r.close()
        self.assertEqual(out['submitted_windows'],3)
        self.assertEqual(out['claims'],3)
        self.assertEqual(out['receipt_count'],10)
        self.assertEqual(out['research_status'],'RESEARCH_REPORT_COMPLETE_WITH_OPEN_ITEMS')
        self.assertEqual(out['approved_financial_facts'],0)
        other=ResearchRun(SRT,MAN,self.store)
        self.assertEqual(other.status()['event_chain_head_sha256'],out['event_chain_head_sha256'])
        self.assertTrue(other.status()['sealed'])
    def test_no_close_missing_windows(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        with self.assertRaisesRegex(RunError,'MODEL_WINDOWS_NOT_COMPLETE'):self.r.close()
    def test_source_sha_rejected(self):
        m=copy.deepcopy(MAN);m['source_sha256']='0'*64
        with self.assertRaisesRegex(RunError,'MANIFEST_SOURCE_MISMATCH'):
            ResearchRun(SRT,m,Path(self.temp.name)/"other")
    def test_window_cue_loss_rejected(self):
        m=copy.deepcopy(MAN);m['windows'][2]['primary_cue_ids']=[5]
        with self.assertRaises(RunError):ResearchRun(SRT,m,Path(self.temp.name)/"other")
    def test_model_fabricated_quote_rejected(self):
        a=self.model(1);a['claims'][0]['source_refs'][0]['quote']='Invented claim'
        with self.assertRaisesRegex(RunError,'MODEL_HALO_OR_FABRICATED_QUOTE'):
            self.r.append('MODEL_ANALYSIS',a)
        self.assertEqual(self.r.status()['receipt_count'],0)
    def test_wrong_reverse_link_rejected(self):
        a=self.model(1);a['cue_dispositions'][0]['claim_ids']=[]
        with self.assertRaisesRegex(RunError,'MODEL_CUE_REVERSE_LINK_INVALID'):
            self.r.append('MODEL_ANALYSIS',a)
    def test_missing_evidence_blocks_report(self):
        for n in (1,2,3):self.r.append('MODEL_ANALYSIS',self.model(n))
        for n in (1,2,3):self.r.append('PRIOR_RELATION_REVIEW',self.relation(n))
        with self.assertRaisesRegex(RunError,'CLAIM_EVIDENCE_NOT_INVESTIGATED'):
            self.r.close()
    def test_non_verified_cannot_approve(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        x=self.evidence(1);x['financial_truth_approved']=True
        with self.assertRaisesRegex(RunError,'EVIDENCE_OPEN_REASON_REQUIRED'):
            self.r.append('EVIDENCE_REVIEW',x)
    def test_self_certified_facts_refused(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        x=self.evidence(1);x['status']='FACT_VERIFIED_IN_SCOPE';x['independent_external_confirmation']=True
        with self.assertRaisesRegex(RunError,'INDEPENDENT_VERIFIER'):
            self.r.append('EVIDENCE_REVIEW',x)
    def test_bad_relation_version_refused(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        x=self.relation(1);x['prior_baseline_git_blob_sha']='b'*40
        with self.assertRaisesRegex(RunError,'RELATION_PRIOR_BASELINE_DRIFT'):
            self.r.append('PRIOR_RELATION_REVIEW',x)
    def test_unreviewed_relation_blocks_report(self):
        for n in (1,2,3):self.r.append('MODEL_ANALYSIS',self.model(n))
        for n in (1,2,3):self.r.append('EVIDENCE_REVIEW',self.evidence(n))
        with self.assertRaisesRegex(RunError,'PRIOR_RELATIONS_NOT_REVIEWED'):
            self.r.close()
    def test_tampered_receipt_refused_after_restart(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        f=next((self.store/'events').glob('*.json'))
        s=f.read_text();f.write_text(s.replace('hypothetical','fabricated'),encoding='utf8')
        with self.assertRaisesRegex(RunError,'EVENT_CONTENT_OR_FILENAME_TAMPERED'):
            ResearchRun(SRT,MAN,self.store)
    def test_duplicate_model_receipt_refused(self):
        self.r.append('MODEL_ANALYSIS',self.model(1))
        with self.assertRaisesRegex(RunError,'MODEL_WINDOW_ALREADY_ACCEPTED'):
            self.r.append('MODEL_ANALYSIS',self.model(1))
    def test_closed_run_no_new_claims(self):
        self.accept_all();self.r.close()
        with self.assertRaisesRegex(RunError,'RUN_ALREADY_CLOSED'):
            self.r.append('EVIDENCE_REVIEW',self.evidence(1))
    def test_manifest_rebind_refused(self):
        m=copy.deepcopy(MAN);m['active_window_ids']=['W00001']
        with self.assertRaisesRegex(RunError,'RUN_SOURCE_OR_SCOPE_CHANGED'):
            ResearchRun(SRT,m,self.store)

if __name__=='__main__':unittest.main()