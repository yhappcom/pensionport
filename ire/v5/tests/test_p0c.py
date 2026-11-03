"""V5 P0C strict-contract synthetic tests; no private originals or gold labels."""
from __future__ import annotations
import base64,copy,unittest,tempfile
from pathlib import Path
from ire.v5.engine import ResearchRun,RunError,sha256
from ire.v5.p0c import validate_official_capture

NOW="2026-11-03T09:00:00+00:00"
SRT=(b"1\n00:00:00,000 --> 00:00:01,000\nPension conditions differ.\n\n"
     b"2\n00:00:01,100 --> 00:00:02,000\nPersonal record needs confirmation.\n")
RAW=("National Pension Service information on deferral and retirement eligibility. " * 4).encode()
SHA="a"*40
def cap():
    return {"schema":"IRE_V5_P0C_OFFICIAL_CAPTURE_V1",
     "official_url":"https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0100M0.do",
     "issuer":"National Pension Service","source_type":"HOST_RETRIEVED_TEXT",
     "observed_at":NOW,"capture_base64":base64.b64encode(RAW).decode(),
     "capture_sha256":sha256(RAW),"exact_excerpt":"deferral and retirement eligibility",
     "finding":"PERSONAL_APPLICABILITY_OPEN",
     "scope_limitation":"Personal eligibility cannot be established from public rules.",
     "effective_date_review":"Effective date needs review for individual use.",
     "financial_fact_approved":False,"independently_attested":False}

class P0CContractTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        man={"schema":"IRE_V5_SOURCE_PLAN_V1","video_id":"sz5N9WJS310",
             "source_sha256":sha256(SRT),"source_cues":2,
             "planner_version":"V5_TEST","prior_baseline_git_blob_sha":SHA,
             "p0c_policy":"STRICT_P0C_V1","active_window_ids":["W00001"],
             "windows":[{"window_id":"W00001","primary_cue_ids":[1,2],
                         "primary_text_sha256":sha256(b"Pension conditions differ. Personal record needs confirmation.")}]}
        self.r=ResearchRun(SRT,man,Path(tmp.name)/"private")
        pkt=self.r.packet("W00001")
        model={"schema":"IRE_V5_MODEL_WINDOW_V1","window_id":"W00001",
           "packet_sha256":pkt["packet_sha256"],
           "claimed_author":"CURRENT_CHATGPT_CONVERSATION",
           "independent_human_verified":False,
           "claims":[{"claim_id":"V5C0001","kind":"RULE",
             "proposition":"Pension conditions differ for each individual.",
             "requires_external_verification":True,"fact_verified":False,
             "advisory_approved":False,
             "source_refs":[{"cue_index":1,"quote":"Pension conditions differ."},
                            {"cue_index":2,"quote":"Personal record needs confirmation."}]}],
           "cue_dispositions":[{"cue_index":i,"status":"LINKED",
                                "claim_ids":["V5C0001"],"reason":None} for i in (1,2)]}
        self.r.append("MODEL_ANALYSIS",model)
        self.e={"schema":"IRE_V5_EVIDENCE_CASE_V1","claim_id":"V5C0001",
           "status":"OFFICIAL_CANDIDATE_APPLICABILITY_OPEN",
           "search_query":"national pension official eligibility",
           "investigation_summary":"Source captured and exact scope limitations retained.",
           "open_reason":"Personal circumstances and effective date still unverified.",
           "financial_truth_approved":False,
           "search_attempts":[{"query":"national pension eligibility requirements",
                                "outcome":"Official source text candidate returned.",
                                "observed_at":NOW}],
           "official_capture":cap()}
        self.rel={"schema":"IRE_V5_PRIOR_RELATION_V1","claim_id":"V5C0001",
            "prior_baseline_git_blob_sha":SHA,"prior_claim_ids":["historical-07"],
            "status":"SAME_SCOPE_PENDING",
            "review_notes":"Prior study has a similar topic but applicability differs.",
            "search_terms":["pension","eligibility"],
            "automerge":False,"financial_truth_approved":False,
            "prior_lookup":{"schema":"IRE_V5_P0C_PRIOR_LOOKUP_V1",
              "prior_git_blob_sha":SHA,
              "source_path":"data/analysis_events/sz5N9WJS310.json",
              "review_excerpt":"Historical source discussed retirement eligibility.",
              "relationship_reason":"Conditions may differ across historical periods.",
              "old_claims_autopromoted":False,"financial_fact_approved":False}}
    def test_real_kernel_open_closure(self):
        self.r.append("EVIDENCE_REVIEW",self.e)
        self.r.append("PRIOR_RELATION_REVIEW",self.rel)
        x=self.r.close()
        self.assertEqual(x["approved_financial_facts"],0)
        self.assertFalse(x["p0_one_command_full_research_go"])
        self.assertEqual(x["receipt_count"],4)
    def test_wrong_doc_sha(self):
        e=copy.deepcopy(self.e);e["official_capture"]["capture_sha256"]="0"*64
        with self.assertRaisesRegex(RunError,"P0C_CAPTURE_SHA_MISMATCH"):
            self.r.append("EVIDENCE_REVIEW",e)
    def test_wrong_quote(self):
        e=copy.deepcopy(self.e);e["official_capture"]["exact_excerpt"]="fabricated quote"
        with self.assertRaisesRegex(RunError,"P0C_EXCERPT_NOT_IN_CAPTURED_BYTES"):
            self.r.append("EVIDENCE_REVIEW",e)
    def test_fake_official_host(self):
        e=copy.deepcopy(self.e);e["official_capture"]["official_url"]="https://nps.or.kr.attack.invalid/doc"
        with self.assertRaisesRegex(RunError,"P0C_OFFICIAL_DOMAIN_NOT_ALLOWED"):
            self.r.append("EVIDENCE_REVIEW",e)
    def test_without_search_receipt(self):
        e=copy.deepcopy(self.e);e["search_attempts"]=[]
        with self.assertRaisesRegex(RunError,"P0C_MANDATORY_SEARCH_ATTEMPT_RECEIPT"):
            self.r.append("EVIDENCE_REVIEW",e)
    def test_prior_blob_drift(self):
        r=copy.deepcopy(self.rel);r["prior_lookup"]["prior_git_blob_sha"]="b"*40
        with self.assertRaisesRegex(RunError,"P0C_PRIOR_LOOKUP_BLOB_MISMATCH"):
            self.r.append("PRIOR_RELATION_REVIEW",r)
    def test_prior_promote_denied(self):
        r=copy.deepcopy(self.rel);r["prior_lookup"]["old_claims_autopromoted"]=True
        with self.assertRaisesRegex(RunError,"P0C_PRIOR_AUTOMERGE_DENIED"):
            self.r.append("PRIOR_RELATION_REVIEW",r)
    def test_not_close_without_evidence(self):
        with self.assertRaisesRegex(RunError,"CLAIM_EVIDENCE_NOT_INVESTIGATED"):
            self.r.close()
    def test_open_source_requires_reason(self):
        e=copy.deepcopy(self.e);e["status"]="OPEN_SOURCE";e["official_capture"]=None
        e["not_verified_explanation"]="Official page was unavailable after searching."
        self.r.append("EVIDENCE_REVIEW",e)
        self.assertEqual(self.r.status()["evidence_cases_reviewed"],1)

if __name__=="__main__": unittest.main()
