"""V4 Chat-to-V3 checkpoint adapter tests: stdlib only, synthetic input only."""
from __future__ import annotations
import copy
import hashlib
import os
import tempfile
import unittest
from ire.v4_chat_accept import accept_private_draft
from ire.chat_bridge import ConversationResearchSession
from ire.v3_adaptive import PLANNER_VERSION

def fixture(tmp):
    rows=[]
    for n in range(1,11):
        a=n*2000
        rows.append(f"{n}\n00:00:{a//1000:02d},000 --> 00:00:{a//1000+1:02d},000\n연금저축은 자신의 재무상황에 따라 판단해야 한다고 말합니다.\n")
    raw="\n".join(rows).encode("utf-8")
    session=ConversationResearchSession(raw,"sz5N9WJS310",
        hashlib.sha256(raw).hexdigest(),tmp,window_strategy="V3_ADAPTIVE")
    w=session.windows[0];ids=w["source_cue_ids"]
    refs=[{"cue_index":i,"quote":session.cues[i-1].text} for i in ids]
    claim={"claim_id":"P0C0001",
        "proposition":"발언자는 연금저축 선택이 개인의 재무상황에 따라 달라질 수 있다고 반복적으로 말한다.",
        "claim_types":["OPINION"],
        "frame":{"subject":"영상 발언자","product":"연금저축",
            "financial_event":None,"action":None,"object":None,
            "jurisdiction":"KR","effective_date":None,
            "conditions":[],"exceptions":[],"measurements":[],
            "modality":"ASSERTION"},
        "source_refs":refs,"annotation_status":"UNREVIEWED"}
    row={"window_id":w["window_id"],"first_cue":ids[0],
        "last_cue":ids[-1],"primary_count":len(ids),
        "primary_source_hash":w["source_text_sha256"],
        "forced_continuation_review":w["continuation_boundary_review_required"],
        "claims":[claim],
        "cue_dispositions":[{"cue_index":i,"status":"LINKED",
            "claim_ids":["P0C0001"],"reason":None} for i in ids]}
    draft={"schema":"IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1",
        "original_sha256":hashlib.sha256(raw).hexdigest(),
        "cue_count":len(session.cues),"planner_version":PLANNER_VERSION,
        "windows":[row]}
    return raw,draft,session

class ChatToV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        os.chmod(self.temp.name,0o700)
        self.raw,self.draft,self.session=fixture(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def accept(self,draft=None,perform_accept=False):
        return accept_private_draft(self.raw,"sz5N9WJS310",
            self.draft if draft is None else draft,self.temp.name,
            perform_accept=perform_accept)
    def test_real_v3_accept_and_idempotent_replay(self):
        a=self.accept(perform_accept=True)
        self.assertEqual(a["v3_accepted_now"],1)
        self.assertEqual(a["remaining_v3_windows"],0)
        self.assertFalse(a["financial_truth_approved"])
        b=self.accept(perform_accept=True)
        self.assertEqual(b["v3_accepted_now"],0)
        self.assertEqual(b["idempotent_existing"],1)
    def test_provisional_preflight_does_not_accept(self):
        a=self.accept()
        self.assertEqual(a["v3_accepted_now"],0)
        self.assertEqual(a["total_v3_accepted"],0)
    def test_tampered_source_quote_rejected(self):
        d=copy.deepcopy(self.draft)
        d["windows"][0]["claims"][0]["source_refs"][0]["quote"]="만들어낸 원문"
        with self.assertRaises(ValueError):
            self.accept(d,perform_accept=True)
        self.assertEqual(self.session.status()["accepted_windows"],0)
    def test_wrong_planner_rejected(self):
        d=copy.deepcopy(self.draft)
        d["planner_version"]="V2_FIXED_WINDOWS"
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
    def test_wrong_cue_reverse_link_rejected(self):
        d=copy.deepcopy(self.draft)
        d["windows"][0]["cue_dispositions"][0]["claim_ids"]=[]
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
    def test_wrong_source_hash_rejected(self):
        d=copy.deepcopy(self.draft)
        d["original_sha256"]="0"*64
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
    def test_forged_financial_approval_rejected(self):
        d=copy.deepcopy(self.draft)
        d["windows"][0]["claims"][0]["annotation_status"]="APPROVED"
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
    def test_window_drift_rejected(self):
        d=copy.deepcopy(self.draft)
        d["windows"][0]["last_cue"]+=1
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
    def test_conflicting_replay_rejected_without_overwrite(self):
        self.accept(perform_accept=True)
        d=copy.deepcopy(self.draft)
        d["windows"][0]["claims"][0]["proposition"]="수정된 잠정 원자 주장"
        with self.assertRaises(ValueError):self.accept(d,perform_accept=True)
        self.assertEqual(self.session.status()["accepted_windows"],1)

if __name__=="__main__":unittest.main()
