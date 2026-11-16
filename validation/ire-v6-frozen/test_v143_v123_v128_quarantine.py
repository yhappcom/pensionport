"""V143 synthetic quarantine/adversarial tests; never a real-owner V123 PASS."""
from __future__ import annotations
import copy
import sqlite3
import unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from test_v123_chat_final_gate import ChatFinalGateTests
from test_v126_chat_approved_knowledge_store import V126RealGatePrivateCumulativeKnowledgeTests
from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests


def hash_text(s):
    return sha256(s.encode("utf-8"))


def exclude_case(case, index, atom_id):
    """Source-bound exclusion of one cue and one dependent claim."""
    source, exchange = case["source"], case["exchange"]
    atom = next(a for a in exchange["atoms"] if a["claim_id"] == atom_id)
    assert index in atom["context_cue_indices"]
    r = copy.deepcopy(case["chat_review"])
    for verdict in r["atom_verdicts"]:
        if verdict["claim_id"] == atom_id:
            verdict.update(status="EXCLUDE_FROM_RESEARCH",
                           finance_evidence_status=("OPEN" if verdict["financial_claim"] else "NOT_APPLICABLE"),
                           official_body_sha256=None, official_effective_as_of=None,
                           financial_scope_checked=False)
    for row in r["source_cues"]:
        if row["cue_index"] == index:
            row["status"] = "EXCLUDED_FROM_RESEARCH"
    r["unresolved_audio_visual"] = 1
    r["quarantine"] = {
        "schema": "IRE_V123_SOURCE_PINNED_QUARANTINE_V1",
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "review_executor": "CHATGPT_IN_CHAT",
        "cue_rows": [{
            "cue_index": index,
            "cue_text_sha256": hash_text(source.cues[index-1].text),
            "reason_code": "AUDIO_UNVERIFIED",
            "private_review_note_sha256": hash_text("synthetic quarantined cue"),
            "source_first_context_checked": True,
        }],
        "atom_rows": [{
            "claim_id": atom_id, "atom_sha256": json_digest(atom),
            "reason_code": "AUDIO_UNVERIFIED",
            "private_review_note_sha256": hash_text("synthetic quarantined atom"),
            "context_dependencies_checked": True,
        }],
        "audio_unverified_cue_indices": [index],
        "private_chat_quarantine_review_sha256": hash_text("synthetic private chat exclusion"),
    }
    return r


class V143SourceBoundV123Tests(unittest.TestCase):
    def setUp(self):
        fx=ChatFinalGateTests("test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.case={"source":fx.source,"exchange":fx.exchange,"chat_review":fx.review}
        self.review=exclude_case(self.case,3,"C00003")

    def run_gate(self,review=None):
        from v123_chat_final_gate import assess_chat_final_gate
        fx=self.fx
        return assess_chat_final_gate(fx.source,fx.exchange,host_receipt=fx.host,
                 chat_review=self.review if review is None else review,
                 store=fx.parent.fx.store,official_evidence_bodies=fx.evidence_bodies)

    def test_01_quarantine_audio_retained_two_research_claims_only(self):
        got=self.run_gate()
        self.assertEqual(got["status"],"CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertEqual((got["atoms_accepted"],got["atoms_excluded"]), (2,1))
        self.assertEqual((got["cues_excluded"],got["audio_unverified_quarantined"]), (1,1))
        self.assertEqual(got["quarantined_claim_ids"],["C00003"])
        self.assertFalse(got["audio_authenticity_verified"])
        self.assertFalse(got["p0_go"])

    def test_02_cannot_exclude_without_ledger(self):
        review=copy.deepcopy(self.review)
        del review["quarantine"]
        with self.assertRaisesRegex(InvalidInput,"QUARANTINE_LEDGER_REQUIRED"):
            self.run_gate(review)

    def test_03_cannot_forge_cue_or_atom_source_sha(self):
        for group,key in (("cue_rows","cue_text_sha256"),("atom_rows","atom_sha256")):
            review=copy.deepcopy(self.review)
            review["quarantine"][group][0][key]="0"*64
            with self.subTest(group=group),self.assertRaises(InvalidInput):
                self.run_gate(review)

    def test_04_cannot_underreport_unheard_audio(self):
        review=copy.deepcopy(self.review)
        review["quarantine"]["audio_unverified_cue_indices"]=[]
        with self.assertRaisesRegex(InvalidInput,"QUARANTINE_AUDIO_CASE_NOT_QUARANTINED"):
            self.run_gate(review)

    def test_05_cannot_approve_atom_depending_on_excluded_source(self):
        review=exclude_case(self.case,1,"C00001")
        with self.assertRaisesRegex(InvalidInput,"QUARANTINE_ACCEPTED_CLAIM_DEPENDS_ON_EXCLUDED_CUE"):
            self.run_gate(review)

    def test_06_open_items_are_not_silently_excluded(self):
        review=copy.deepcopy(self.review)
        review["source_cues"][0]["status"]="OPEN"
        self.assertEqual(self.run_gate(review)["status"],"CHAT_FINAL_HOLD_OPEN")
        review=copy.deepcopy(self.review)
        review["atom_verdicts"][0]["status"]="OPEN"
        self.assertEqual(self.run_gate(review)["status"],"CHAT_FINAL_HOLD_OPEN")

    def test_07_exclusion_reason_context_and_note_cannot_be_removed(self):
        for key,val in (("reason_code","UNSAFE_IMPLICIT_APPROVAL"),
                        ("source_first_context_checked",False),
                        ("private_review_note_sha256","BAD")):
            review=copy.deepcopy(self.review)
            review["quarantine"]["cue_rows"][0][key]=val
            with self.subTest(key=key),self.assertRaises(InvalidInput):
                self.run_gate(review)


class V143V126StoreTests(unittest.TestCase):
    def setUp(self):
        fx=V126RealGatePrivateCumulativeKnowledgeTests(
            "test_real_chat_gate_synthetic_source_then_immutable_cumulative_store")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx

    def test_08_only_accepted_original_claims_are_stored_and_retrievable(self):
        fx=self.fx
        case={"source":fx.p.source,"exchange":fx.p.exchange,"chat_review":fx.p.review}
        review=exclude_case(case,3,"C00003")
        result=fx.push(chat_review=review)
        self.assertEqual(result["entries"],2)
        with sqlite3.connect(fx.db.path) as con:
            content=[x[0] for x in con.execute("SELECT entry_json FROM knowledge")]
        self.assertEqual(len(content),2)
        self.assertTrue(all("C00003" not in x for x in content))
        evidence=fx.db.evidence_for_question("일반 연금 수익")
        self.assertTrue(all(x.get("claim_id")!="C00003" for x in evidence["claims"]))

    def test_09_unadjudicated_open_claim_still_causes_no_store(self):
        fx=self.fx
        review=exclude_case({"source":fx.p.source,"exchange":fx.p.exchange,
                             "chat_review":fx.p.review},3,"C00003")
        review["atom_verdicts"][0]["status"]="OPEN"
        with self.assertRaises(QualityNotProven):
            fx.push(chat_review=review)
        self.assertEqual(fx.db.audit()["active_claims"],0)


class V143V128AtomicParentTests(unittest.TestCase):
    def setUp(self):
        fx=V128HostRunAndAtomicParentTests(
            "test_01_two_native_v6_children_seam_and_atomic_private_parent_publication")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        case=fx.packets[1]["case"]
        atom=case["exchange"]["atoms"][0]
        index=atom["source_refs"][0]["cue_index"]
        case["chat_review"]=exclude_case(case,index,atom["claim_id"])
        self.excluded=atom["claim_id"]
        self.default_parent=fx.parent_review
        def reviewed_parent(checkpoint,assembly,seams,packets):
            r=self.default_parent(checkpoint,assembly,seams,packets)
            r["quarantine_dispositions_reviewed"]=True
            r["quarantine_cross_segment_dependencies_resolved"]=True
            return r
        fx.parent_review=reviewed_parent

    def test_10_all_excluded_child_stages_zero_then_one_parent_commit(self):
        got=self.fx.run_engine()
        self.assertTrue(got["all_video_knowledge_published"])
        self.assertEqual(got["publication_receipt"]["entry_count"],2)
        with sqlite3.connect(self.fx.knowledge.path) as con:
            entries=[x[0] for x in con.execute("SELECT entry_json FROM knowledge")]
            publications=con.execute("SELECT COUNT(*) FROM parent_publications").fetchone()[0]
        self.assertEqual(len(entries),2)
        self.assertEqual(publications,1)
        self.assertTrue(all(self.excluded not in x for x in entries))
        self.assertFalse(got["p0_go"])

    def test_11_unapproved_parent_quarantine_fails_and_rolls_back(self):
        with self.assertRaisesRegex(QualityNotProven,"PARENT_CHAT_RELEASE_NOT_SOURCE_BOUND"):
            self.fx.run_engine(review_parent=self.default_parent)
        self.assertEqual(self.fx._counts().get("events",0),0)
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_12_changed_parent_quarantine_digest_fails_and_rolls_back(self):
        def forged(checkpoint,assembly,seams,packets):
            r=self.fx.parent_review(checkpoint,assembly,seams,packets)
            r["quarantine_manifest_sha256"]="0"*64
            return r
        with self.assertRaisesRegex(QualityNotProven,"PARENT_CHAT_RELEASE_NOT_SOURCE_BOUND"):
            self.fx.run_engine(review_parent=forged)
        self.assertEqual(self.fx._counts().get("events",0),0)

    def test_13_repeating_identical_parent_does_not_duplicate(self):
        first=self.fx.run_engine()
        second=self.fx.run_engine()
        self.assertEqual(second["publication_receipt"]["status"],"IDEMPOTENT_PARENT_KNOWLEDGE_COMMIT")
        self.assertEqual(first["knowledge_head_sha256"],second["knowledge_head_sha256"])


if __name__=="__main__":
    unittest.main(verbosity=2)
