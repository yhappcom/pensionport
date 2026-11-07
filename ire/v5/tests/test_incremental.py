"""Synthetic reproducible tests for an append-only incremental research audit."""
from __future__ import annotations
import copy, json, tempfile, unittest
from pathlib import Path
from ire.v5.engine import ResearchRun, RunError, sha256, canonical
from ire.v5.planner import prepare_full_video_manifest
from ire.v5.incremental import IncrementalAudit, make_document, REVIEW_SCHEMA

ORIGINAL=(
    b"1\n00:00:00,000 --> 00:00:01,000\nToday we compare returns\n\n"
    b"2\n00:00:01,100 --> 00:00:02,000\n7 years 5000 is\n\n"
    b"3\n00:00:02,100 --> 00:00:03,000\nnot necessarily accurate\n\n"
    b"4\n00:00:03,100 --> 00:00:04,000\ntax treatment differs\n\n"
    b"5\n00:00:04,100 --> 00:00:05,000\n1500 thresholds might change.\n\n"
    b"6\n00:00:05,100 --> 00:00:06,000\nEnd of example.\n")
NOW="2026-11-04T01:00:00+09:00"
TEXT="Official guidance explains pension withdrawal eligibility and annual tax thresholds. " * 3

def model(r, wid, linked):
    p=r.packet(wid)
    ids=r.windows[wid]["primary_cue_ids"]
    cid="V5C0001" if wid=="W00001" else "V5C0002"
    linked=set(linked)
    return {"schema":"IRE_V5_MODEL_WINDOW_V1","window_id":wid,
        "packet_sha256":p["packet_sha256"],"claimed_author":"CURRENT_CHATGPT_CONVERSATION",
        "independent_human_verified":False,
        "claims":[{"claim_id":cid,"kind":"RULE","proposition":"Pension withdrawals vary by effective tax regime.",
                   "requires_external_verification":True,"fact_verified":False,
                   "advisory_approved":False,"source_refs":[{"cue_index":i,"quote":r.cues[i].text} for i in linked]}],
        "cue_dispositions":[{"cue_index":i,"status":"LINKED" if i in linked else "NONCLAIM",
                             "claim_ids":[cid] if i in linked else [],
                             "reason":None if i in linked else "Dialogue fragment, needs review."} for i in ids]}


def evidence(cid):
    return {"schema":"IRE_V5_EVIDENCE_CASE_V1","claim_id":cid,"status":"OFFICIAL_CANDIDATE_APPLICABILITY_OPEN",
            "investigation_summary":"General law applicability requires effective date review.",
            "open_reason":"No independent fact review has taken place.","financial_truth_approved":False,
            "search_query":"national tax service pension account eligibility"}


def relation(cid):
    return {"schema":"IRE_V5_PRIOR_RELATION_V1","claim_id":cid,
         "prior_baseline_git_blob_sha":"f"*40,"status":"CONFLICT_CANDIDATE",
         "review_notes":"Historical description may apply to a different calendar year.",
         "automerge":False,"financial_truth_approved":False,"search_terms":["pension","tax"],
         "prior_claim_ids":["historic-tax-001"]}


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.base=Path(t.name)
        plan=prepare_full_video_manifest(ORIGINAL,"sz5N9WJS310","f"*40,
                                          min_cues=2,max_cues=3,max_chars=800)
        run=ResearchRun(ORIGINAL,plan,self.base/"source")
        for wid,linked in [("W00001",[1,3]),("W00002",[4,5])]:
            run.append("MODEL_ANALYSIS",model(run,wid,linked))
        for cid in ("V5C0001","V5C0002"):
            run.append("EVIDENCE_REVIEW",evidence(cid))
            run.append("PRIOR_RELATION_REVIEW",relation(cid))
        run.close()
        self.run=run
        self.audit=IncrementalAudit(run,self.base/"incremental")
        self.doc=make_document(issuer="National Tax Service",url="https://www.nts.go.kr/some/a",
                               captured_text=TEXT,observed_at=NOW,
                               retrieval_note="Bounded hosted text extract, origin is not independently signed.",
                               effective_date_note="Tax law effective date requires per-claim confirmation.")

    def review(self,issue_id,decision=None):
        issue=self.audit.issues[issue_id]
        kind=issue["kind"]
        decision=decision or {"B":"CONTINUITY_REVIEWED", "N":"NONFINANCIAL_NUMERIC",
                              "E":"OFFICIAL_CANDIDATE_SCOPE_OPEN", "R":"CONFLICT_OPEN"}[kind]
        rev={"schema":REVIEW_SCHEMA,"issue_id":issue_id,
             "issue_sha256":sha256(canonical(issue)),"decision":decision,
             "rationale":"Read the source and compared the substantive conditions in the adjacent context.",
             "reviewer":"CURRENT_CHATGPT_CONVERSATION","independent_approval":False,
             "financial_fact_approved":False,"related_claim_ids":[]}
        if kind=="B":rev.update(left_quote=issue["left_quote"],right_quote=issue["right_quote"])
        elif kind=="N":rev["exact_quote"]=issue["quote"]
        elif kind=="E":rev.update(official_doc_id=self.doc["doc_id"],
              exact_official_excerpt="pension withdrawal eligibility and annual tax thresholds",
              applicability_limitation="Individual application and tax residency not confirmed.",
              effective_date_check="Relevant calendar year has not been independently checked.")
        elif kind=="R":rev.update(prior_baseline_git_blob_sha="f"*40,
              compared_prior_claim_ids=issue["prior_claim_ids"],
              scope_difference_note="The prior statement may rely on another tax year.")
        return rev

    def test_collects_all_risk_types(self):
        counts=self.audit.status()["issue_counts"]
        self.assertEqual(counts,{"B":1,"E":2,"N":1,"R":2})
        self.assertEqual(self.audit.status()["issues_total"],6)

    def test_shared_doc_two_claims_one_registration(self):
        reviews=[self.review(i) for i in self.audit.issues]
        result=self.audit.submit(documents=[self.doc],reviews=reviews)
        self.assertTrue(result["research_audit_complete_with_declared_open"])
        self.assertEqual(result["official_document_reuse_links"],2)
        self.assertEqual(result["registered_official_document_candidates"],1)
        self.assertEqual(result["independently_approved_financial_facts"],0)
        self.assertFalse(result["one_turn_five_video_research_go"])
        reopened=IncrementalAudit(self.run,self.base/"incremental")
        self.assertEqual(reopened.head,self.audit.head)
        self.assertEqual(reopened.status()["issues_reviewed"],6)

    def test_staged_invalid_review_does_not_append_any_document(self):
        bad=self.review("E-V5C0002");bad["exact_official_excerpt"]="invented quote not in official text"
        with self.assertRaisesRegex(RunError,"AUDIT_OFFICIAL_EXCERPT_NOT_IN_SOURCE"):
            self.audit.submit(documents=[self.doc],reviews=[bad])
        self.assertEqual(self.audit.seq,0)
        self.assertEqual(self.audit.status()["registered_official_document_candidates"],0)

    def test_rejects_fake_official_domain(self):
        d=copy.deepcopy(self.doc);d["url"]="https://www.nts.go.kr.attacker.invalid/fake"
        with self.assertRaisesRegex(RunError,"AUDIT_OFFICIAL_DOCUMENT_IDENTITY_INVALID"):
            self.audit.submit(documents=[d])

    def test_rejects_document_modification(self):
        d=copy.deepcopy(self.doc);d["captured_text"]+=" change"
        with self.assertRaisesRegex(RunError,"AUDIT_OFFICIAL_CAPTURE_DIGEST_INVALID"):
            self.audit.submit(documents=[d])

    def test_rejects_fabricated_boundary_quote(self):
        b=self.review("B-W00001");b["left_quote"]="fake text"
        with self.assertRaisesRegex(RunError,"AUDIT_BOUNDARY_EXACT_CUES_MISSING"):
            self.audit.submit(reviews=[b])

    def test_rejects_numeric_fragment_without_nearby_existing_claim(self):
        r=self.review("N-00002","EXISTING_CLAIM_FRAGMENT")
        with self.assertRaisesRegex(RunError,"AUDIT_FRAGMENT_WITHOUT_CLAIM"):
            self.audit.submit(reviews=[r])

    def test_rejects_unsubstantiated_truth_approval(self):
        r=self.review("R-V5C0001");r["financial_fact_approved"]=True
        with self.assertRaisesRegex(RunError,"AUDIT_UNSUPPORTED_REVIEW_DECISION"):
            self.audit.submit(reviews=[r])

    def test_rejects_prior_baseline_drift(self):
        r=self.review("R-V5C0001");r["prior_baseline_git_blob_sha"]="0"*40
        with self.assertRaisesRegex(RunError,"AUDIT_PRIOR_COMPARISON_INCOMPLETE"):
            self.audit.submit(reviews=[r])

    def test_duplicate_risk_fails_without_new_event(self):
        r=self.review("B-W00001")
        self.audit.submit(reviews=[r]);n=self.audit.seq
        with self.assertRaisesRegex(RunError,"AUDIT_DUPLICATE_RISK_REVIEW"):
            self.audit.submit(reviews=[r])
        self.assertEqual(self.audit.seq,n)

    def test_event_tampering_fails(self):
        self.audit.submit(reviews=[self.review("B-W00001")])
        f=next((self.base/"incremental"/"events").glob("*.json"))
        raw=json.loads(f.read_text());raw["payload"]["reviews"][0]["rationale"]="tampered"
        f.write_text(json.dumps(raw))
        with self.assertRaisesRegex(RunError,"AUDIT_EVENT_TAMPERED"):
            self.audit.replay()

    def test_outstanding_packet_has_real_context_and_digest(self):
        task=self.audit.outstanding(limit=3)
        self.assertEqual(len(task["issues"]),3)
        self.assertTrue(all(len(x["issue_sha256"])==64 for x in task["issues"]))

    def test_source_drift_blocked(self):
        wrong=copy.deepcopy(self.run)
        wrong.head="a"*64
        with self.assertRaisesRegex(RunError,"AUDIT_LOCK_OR_SOURCE_DRIFT"):
            IncrementalAudit(wrong,self.base/"incremental")

    def test_refuses_to_audit_unsealed_source(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        r=ResearchRun(ORIGINAL,self.run.manifest,Path(t.name)/"source")
        with self.assertRaisesRegex(RunError,"AUDIT_REQUIRES_FULL_SOURCE_SEAL"):
            IncrementalAudit(r,Path(t.name)/"audit")

    def test_cannot_approve_personal_advice(self):
        result=self.audit.status()
        self.assertFalse(result["personal_investment_advice_approved"])
        self.assertEqual(result["release_verdict"],"NO_GO_INDEPENDENT_FACT_AND_SEMANTIC_AUDIT")

if __name__=='__main__':unittest.main()

class IncrementalBackupTests(IncrementalTests):
    def test_private_encrypted_archive_roundtrip(self):
        from ire.v5.incremental_backup import backup,restore
        self.audit.submit(documents=[self.doc],reviews=[self.review(i) for i in self.audit.issues])
        archive=self.base/'sealed.v5inc';secret='not-a-public-secret-16-chars'
        one=backup(self.run,self.audit,secret,archive)
        two=restore(archive,secret,self.base/'new_root')
        self.assertEqual(one['audit_head_sha256'],two['restored_incremental_head_sha256'])
        self.assertEqual(two['restored_review_count'],6)
        self.assertFalse(two['investment_advice_approved'])

    def test_private_wrong_password_rejected(self):
        from ire.v5.incremental_backup import backup,restore
        archive=self.base/'sealed.v5inc';backup(self.run,self.audit,'long-secret-abcdef',archive)
        with self.assertRaisesRegex(RunError,'AUDIT_BACKUP_WRONG_SECRET_OR_TAMPERED'):
            restore(archive,'wrong-secret-abcdef',self.base/'new_root')
        self.assertFalse((self.base/'new_root').exists())

    def test_private_tamper_rejected(self):
        from ire.v5.incremental_backup import backup,restore
        archive=self.base/'sealed.v5inc';backup(self.run,self.audit,'long-secret-abcdef',archive)
        raw=bytearray(archive.read_bytes());raw[-1]^=1;archive.write_bytes(raw)
        with self.assertRaisesRegex(RunError,'AUDIT_BACKUP_WRONG_SECRET_OR_TAMPERED'):
            restore(archive,'long-secret-abcdef',self.base/'new_root')
