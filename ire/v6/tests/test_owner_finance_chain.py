"""V6-3/4 trust-root and structural finance candidate transaction boundaries.

Only fabricated subtitle/document/knowledge fixtures. No actual financial
rules, 116 approved master entries, or private owner SRT is included.
"""
from __future__ import annotations

import copy
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import (InvalidInput, DomainConflict, LedgerCorrupted,
                           ConcurrentHeadChanged, IdempotencyConflict, QualityNotProven)
from ire.v6.finance import audit_official_candidate, audit_prior_relation
from ire.v6.trust import verify_owner_inventory
from ire.v6.store import TransactionStore
from ire.v6.tests.test_source_and_proof import (VIDEO, make_srt, make_manifest,
                                                 make_model, make_review)


def fixture_baseline(size=3):
    return {"schema":"IRE_V6_LEGACY_BASELINE_V1", "entries":[
        {"id":f"LEGACY-{i:03d}","content_sha256":sha256(f"legacy-{i}".encode())}
        for i in range(size)]}


class OwnerAndFinanceChainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / "private" / "v6.db"
        self.store = TransactionStore(self.db)
        self.source = make_srt()
        self.manifest = make_manifest(self.source)
        from ire.v6.source import verify_source
        self.verified = verify_source(self.source, self.manifest,
                                     expected_source_sha256=sha256(self.source),
                                     expected_manifest_sha256=json_digest(self.manifest))
        self.inventory = {"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id": VIDEO,
            "source_sha256":sha256(self.source),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":self.verified.cue_census_sha256
        }]}
        self.inventory_bytes=canonical(self.inventory)
        self.owner_pin_sha=sha256(self.inventory_bytes)
        self.created=self.store.create_scope(scope_id="v6_test_scope",video_id=VIDEO,
                         source_sha256=sha256(self.source),
                         manifest_sha256=json_digest(self.manifest),command_id="scope_genesis")
        self.official_bytes=("Illustrative example only: a fictional condition has "
                             "an exception described in this sample. This is not law.").encode()
        self.proposal={
            "schema":"IRE_V6_OFFICIAL_CANDIDATE_V1",
            "claim_id":"C00001", "issuer":"Synthetic Test Office",
            "url":"https://example.org/synthetic-test-only", "quote":"a fictional condition has an exception",
            "published_on":"2025-01-05","effective_from":"2025-02-01",
            "effective_until":None,"retrieved_on":"2026-01-10",
            "jurisdiction":"FICTIONAL_TEST_ONLY", "scope_note":"not financial law",
            "claim_support_verdict":"UNREVIEWED",
        }
        self.baseline=fixture_baseline()
        self.relation={"schema":"IRE_V6_PRIOR_RELATION_CANDIDATE_V1",
                       "claim_id":"C00001","prior_id":"LEGACY-000",
                       "relationship":"OPEN", "rationale":"synthetic relation pending",
                       "semantic_relation_verified":False}

    def head(self):
        return self.store.snapshot("v6_test_scope")["ledger_head_sha256"]

    def attest(self):
        return self.store.attest_source(scope_id="v6_test_scope",command_id="source_attest",
                   expected_head=self.head(),raw=self.source,manifest=self.manifest)

    def pin(self, **overrides):
        args=dict(scope_id="v6_test_scope", command_id="pin_source",
                  expected_head=self.head(),raw=self.source,manifest=self.manifest,
                  inventory_bytes=self.inventory_bytes,
                  expected_inventory_sha256=self.owner_pin_sha)
        args.update(overrides)
        return self.store.attest_owner_inventory(**args)

    def model(self, key="model_A", kind="A"):
        m=make_model()
        if kind != "A":
            m["claims"][0]["proposition"] = f"Revision {kind} of original interpretation"
        return self.store.submit(scope_id="v6_test_scope",command_id=key,
               expected_head=self.head(),kind="MODEL_RECORDED",
               payload={"window_id":"W00001", "model":m})

    def proof(self, key="structural_A"):
        return self.store.submit_structural_proof(scope_id="v6_test_scope",
                  command_id=key,expected_head=self.head(),window_id="W00001",
                  raw=self.source,manifest=self.manifest,review=make_review())

    def finance(self, **overrides):
        args=dict(scope_id="v6_test_scope",command_id="finance_candidate_A",
                  expected_head=self.head(),window_id="W00001",raw=self.source,
                  manifest=self.manifest,inventory_bytes=self.inventory_bytes,
                  expected_inventory_sha256=self.owner_pin_sha,
                  official_document_raw=self.official_bytes,
                  official_proposal=self.proposal,
                  expected_official_sha256=sha256(self.official_bytes),
                  as_of="2026-02-01",prior_baseline=self.baseline,
                  prior_relation=self.relation,
                  expected_baseline_sha256=json_digest(self.baseline))
        args.update(overrides)
        return self.store.submit_finance_candidate(**args)

    def ready(self):
        self.attest();self.pin();self.model();self.proof()

    def test_external_inventory_is_pinned_to_bytes_and_cue_census(self):
        anchor=verify_owner_inventory(self.source,self.manifest,self.inventory_bytes,
                                      expected_inventory_sha256=self.owner_pin_sha)
        self.assertEqual(anchor.inventory_count,1)
        self.assertFalse(anchor.attestation()["owner_identity_verified"])
        with self.assertRaisesRegex(InvalidInput,"PIN_MISMATCH"):
            verify_owner_inventory(self.source,self.manifest,self.inventory_bytes,
                                   expected_inventory_sha256=sha256(b"wrong"))
        with self.assertRaisesRegex(InvalidInput,"SOURCE_OR_PLAN_BYTES_MISMATCH"):
            verify_owner_inventory(self.source+b"\n\n",self.manifest,self.inventory_bytes,
                                   expected_inventory_sha256=self.owner_pin_sha)

    def test_duplicate_video_and_copied_content_across_cohorts_rejected_by_inventory(self):
        for field in ("video_id", "source_sha256"):
            evil=copy.deepcopy(self.inventory)
            extra=copy.deepcopy(evil["entries"][0]);extra["video_id"]="12345678901"
            if field=="video_id":extra["video_id"]=VIDEO
            evil["entries"].append(extra)
            encoded=canonical(evil)
            with self.subTest(field=field), self.assertRaisesRegex(InvalidInput,"DUPLICATE_VIDEO_OR_SOURCE"):
                verify_owner_inventory(self.source,self.manifest,encoded,
                                       expected_inventory_sha256=sha256(encoded))

    def test_coordinated_untrusted_source_and_self_digest_not_owner_authentication(self):
        # Recomputed fake registry/source digests can pass structural checks.
        # An owner-held digest pinned BEFORE the adversary's revision rejects it.
        altered=self.source.replace(b"A statement",b"An invented claim")
        new_manifest=make_manifest(altered)
        from ire.v6.source import verify_source
        derived=verify_source(altered,new_manifest,
                        expected_source_sha256=sha256(altered),
                        expected_manifest_sha256=json_digest(new_manifest))
        fake=copy.deepcopy(self.inventory)
        fake["entries"][0].update(source_sha256=sha256(altered),
                                 manifest_sha256=json_digest(new_manifest),
                                 cue_census_sha256=derived.cue_census_sha256)
        fake_raw=canonical(fake)
        with self.assertRaisesRegex(InvalidInput,"PIN_MISMATCH"):
            verify_owner_inventory(altered,new_manifest,fake_raw,
                                   expected_inventory_sha256=self.owner_pin_sha)
        # This cannot be used as evidence of actual owner authentication.
        same_attacker_pin=verify_owner_inventory(altered,new_manifest,fake_raw,
                                  expected_inventory_sha256=sha256(fake_raw))
        self.assertFalse(same_attacker_pin.attestation()["owner_identity_verified"])

    def test_owner_pin_requires_byte_attestation_and_rejects_generic_submit(self):
        with self.assertRaises(DomainConflict):self.pin()
        self.attest()
        with self.assertRaises(DomainConflict):self.store.submit(
            scope_id="v6_test_scope",command_id="generic_forgery",expected_head=self.head(),
            kind="OWNER_PIN_RECORDED",payload={"operator_held_inventory_digest_matched":True})
        self.assertEqual(self.pin()["sequence"],3)
        self.assertTrue(self.store.snapshot("v6_test_scope")["progress"]["owner_inventory_pin_recorded"])
        self.assertFalse(self.store.snapshot("v6_test_scope")["progress"]["source_original_bytes_verified"])

    def test_exact_owner_pin_retry_historical_and_modified_payload_rejected(self):
        self.attest(); initial=self.head()
        a=self.pin(expected_head=initial)
        b=self.pin(expected_head=initial)
        self.assertTrue(b["idempotent_replay"])
        self.assertEqual(a["event_sha256"], b["event_sha256"])
        with self.assertRaisesRegex(InvalidInput,"PIN_MISMATCH"):
            self.pin(expected_head=initial,expected_inventory_sha256=sha256(b"fake"))
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],3)

    def test_official_evidence_bytes_dates_and_quote_fail_closed(self):
        audit=audit_official_candidate(self.official_bytes,self.proposal,
              expected_document_sha256=sha256(self.official_bytes),as_of="2026-02-01")
        self.assertEqual(audit["status"],"SOURCE_CANDIDATE_REVIEW_PENDING")
        self.assertFalse(audit["finance_fact_approved"])
        for change,kw in [({"quote":"invented missing text"},"QUOTE_NOT_IN"),
                          ({"retrieved_on":"2027-01-01"},"DATE_CHRONOLOGY"),
                          ({"claim_support_verdict":"ACCEPTED"},"CANNOT_SELF_APPROVE"),
                          ({"url":"http://example.org/test"},"NOT_SAFE_HTTPS"),
                          ({"effective_from":"2026-02-30"},"EFFECTIVE_DATE_INVALID")]:
            with self.subTest(change=change),self.assertRaisesRegex(InvalidInput,kw):
                audit_official_candidate(self.official_bytes,{**self.proposal,**change},
                    expected_document_sha256=sha256(self.official_bytes),as_of="2026-02-01")
        future={**self.proposal,"effective_from":"2027-01-01"}
        audit=audit_official_candidate(self.official_bytes,future,
                         expected_document_sha256=sha256(self.official_bytes),as_of="2026-02-01")
        self.assertEqual(audit["status"],"DATE_NOT_APPLICABLE")
        self.assertFalse(audit["effective_at_as_of"])

    def test_official_quote_presence_not_entailment_or_issuer_authenticity(self):
        data=b"A reported rumor states the amount is 100. The source denies it."
        proposal={**self.proposal,"quote":"the amount is 100"}
        result=audit_official_candidate(data,proposal,
                     expected_document_sha256=sha256(data),as_of="2026-02-01")
        self.assertTrue(result["quoted_text_present"])
        self.assertFalse(result["claim_semantically_supported"])
        self.assertFalse(result["issuer_authenticity_independently_verified"])

    def test_prior_baseline_snapshot_membership_not_semantics(self):
        out=audit_prior_relation(self.baseline,self.relation,
                     expected_baseline_sha256=json_digest(self.baseline))
        self.assertEqual(out["legacy_records_in_pinned_snapshot"],3)
        self.assertFalse(out["prior_fact_contents_replayed"])
        self.assertFalse(out["semantic_relation_verified"])
        with self.assertRaisesRegex(InvalidInput,"TARGET_UNKNOWN"):
            audit_prior_relation(self.baseline,{**self.relation,"prior_id":"MISSING"},
                                 expected_baseline_sha256=json_digest(self.baseline))
        with self.assertRaisesRegex(InvalidInput,"PIN_MISMATCH"):
            audit_prior_relation(self.baseline,self.relation,
                                 expected_baseline_sha256=sha256(b"outdated"))

    def test_malformed_relation_enum_is_typed_fail_closed(self):
        for value in ([], {}, ["OPEN"], {"OPEN": 1}):
            with self.subTest(value=value), self.assertRaisesRegex(
                    InvalidInput,"PRIOR_RELATION_SELF_APPROVAL_OR_REASON_INVALID"):
                audit_prior_relation(self.baseline,
                    {**self.relation,"relationship":value},
                    expected_baseline_sha256=json_digest(self.baseline))

    def test_finance_candidate_requires_source_pin_and_proof(self):
        self.attest();self.model();self.proof()
        with self.assertRaisesRegex(DomainConflict,"REQUIRES_OWNER_PIN"):
            self.finance()
        self.pin()
        result=self.finance()
        self.assertEqual(result["sequence"],6)
        snap=self.store.snapshot("v6_test_scope")
        self.assertEqual(snap["progress"]["current_revision_finance_candidate_reviews"],1)
        self.assertFalse(snap["progress"]["financial_facts_approved"])
        self.assertFalse(snap["progress"]["p0_go"])
        with self.assertRaises(QualityNotProven):self.store.issue_terminal_receipt("v6_test_scope")

    def test_finance_candidate_idempotent_and_only_one_record(self):
        self.ready();old=self.head()
        a=self.finance(expected_head=old)
        b=self.finance(expected_head=old)
        self.assertTrue(b["idempotent_replay"])
        self.assertEqual(a["event_sha256"],b["event_sha256"])
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],6)
        with self.assertRaises(IdempotencyConflict):
            self.finance(expected_head=old,as_of="2026-02-02")

    def test_finance_candidate_source_tamper_fails_without_event(self):
        self.ready();seq=self.store.snapshot("v6_test_scope")["sequence"]
        changed=self.source.replace(b"A statement",b"An invented")
        with self.assertRaises(InvalidInput):self.finance(raw=changed)
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],seq)

    def test_finance_candidate_document_tamper_fails_without_event(self):
        self.ready();seq=self.store.snapshot("v6_test_scope")["sequence"]
        with self.assertRaises(InvalidInput):
            self.finance(official_document_raw=self.official_bytes+b"changed")
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],seq)

    def test_finance_candidate_prior_tamper_fails_without_event(self):
        self.ready();seq=self.store.snapshot("v6_test_scope")["sequence"]
        fake=copy.deepcopy(self.baseline)
        fake["entries"][0]["content_sha256"]=sha256(b"rewritten")
        with self.assertRaisesRegex(InvalidInput,"PRIOR_BASELINE_PIN_MISMATCH"):
            self.finance(prior_baseline=fake)
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],seq)

    def test_revision_change_invalidates_structural_finance_candidate(self):
        self.ready();self.finance()
        self.assertEqual(self.store.snapshot("v6_test_scope")["progress"]["current_revision_finance_candidate_reviews"],1)
        self.model(key="revision_B",kind="B")
        self.model(key="revision_A_again",kind="A")
        snap=self.store.snapshot("v6_test_scope")
        self.assertEqual(snap["progress"]["current_revision_finance_candidate_reviews"],0)
        with self.assertRaisesRegex(DomainConflict,"CURRENT_PROOF"):
            self.finance(command_id="stale_finance_attempt")
        self.proof(key="proof_again")
        result=self.finance(command_id="new_finance_again")
        self.assertFalse(result["research_complete"])
        self.assertEqual(self.store.snapshot("v6_test_scope")["progress"]["current_revision_finance_candidate_reviews"],1)

    def test_owner_pin_rollback_after_head_update_and_clean_retry(self):
        self.attest()
        original=self.head()
        def abort(stage):
            if stage == "after_head_update":
                raise RuntimeError("ABORT_AFTER_HEAD_ADVANCE")
        with patch.object(self.store,"_before_commit",side_effect=abort):
            with self.assertRaisesRegex(RuntimeError,"ABORT_AFTER_HEAD_ADVANCE"):
                self.pin()
        reopened=TransactionStore(self.db)
        self.assertEqual(reopened.snapshot("v6_test_scope")["ledger_head_sha256"],original)
        self.assertFalse(reopened.snapshot("v6_test_scope")["progress"]["owner_inventory_pin_recorded"])
        self.assertEqual(self.pin()["sequence"],3)

    def test_competing_finance_writers_are_serialized(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        self.ready()
        starting_head=self.head()
        ready=Barrier(2)
        def submit(key):
            ready.wait(timeout=8)
            try:
                return ("PASS",self.finance(command_id=key,expected_head=starting_head))
            except ConcurrentHeadChanged as exc:
                return ("CONFLICT",str(exc))
        with ThreadPoolExecutor(max_workers=2) as pool:
            tasks=[pool.submit(submit,"finance_writer_"+str(i)) for i in (1,2)]
            results=[t.result(timeout=15) for t in tasks]
        self.assertEqual(sorted(x[0] for x in results),["CONFLICT","PASS"])
        self.assertEqual(TransactionStore(self.db).snapshot("v6_test_scope")["sequence"],6)

    def test_finance_rollback_after_event_insert(self):
        self.ready();original=self.head()
        with patch.object(self.store,"_before_commit",side_effect=RuntimeError("INJECTED_ABORT")):
            with self.assertRaisesRegex(RuntimeError,"INJECTED_ABORT"):
                self.finance()
        self.assertEqual(self.head(),original)
        self.assertEqual(TransactionStore(self.db).snapshot("v6_test_scope")["sequence"],5)
        self.finance()
        self.assertEqual(self.store.snapshot("v6_test_scope")["sequence"],6)

    def replay_finance(self, **overrides):
        args=dict(scope_id="v6_test_scope",window_id="W00001",claim_id="C00001",
                  raw=self.source,manifest=self.manifest,
                  inventory_bytes=self.inventory_bytes,
                  expected_inventory_sha256=self.owner_pin_sha,
                  official_document_raw=self.official_bytes,
                  official_proposal=self.proposal,
                  expected_official_sha256=sha256(self.official_bytes),
                  as_of="2026-02-01",prior_baseline=self.baseline,
                  prior_relation=self.relation,
                  expected_baseline_sha256=json_digest(self.baseline))
        args.update(overrides)
        return self.store.snapshot_with_finance_candidate(**args)

    def test_finance_read_replay_verifies_same_snapshot_and_no_approval(self):
        self.ready();self.finance()
        a=self.replay_finance()
        self.assertEqual(a["sequence"],6)
        self.assertTrue(a["source_original_bytes_replayed_this_call"])
        self.assertTrue(a["official_document_bytes_replayed_this_call"])
        self.assertTrue(a["legacy_baseline_membership_replayed_this_call"])
        self.assertFalse(a["financial_claim_semantically_verified"])
        self.assertFalse(a["p0_go"])
        b=TransactionStore(self.db).snapshot_with_finance_candidate(
            scope_id="v6_test_scope",window_id="W00001",claim_id="C00001",
            raw=self.source,manifest=self.manifest,
            inventory_bytes=self.inventory_bytes,
            expected_inventory_sha256=self.owner_pin_sha,
            official_document_raw=self.official_bytes,official_proposal=self.proposal,
            expected_official_sha256=sha256(self.official_bytes),as_of="2026-02-01",
            prior_baseline=self.baseline,prior_relation=self.relation,
            expected_baseline_sha256=json_digest(self.baseline))
        self.assertEqual(a,b)

    def test_finance_read_replay_rejects_edited_inputs_and_owner_drift(self):
        self.ready();self.finance()
        with self.assertRaises(InvalidInput):
            self.replay_finance(official_document_raw=self.official_bytes+b"modified")
        with self.assertRaises(LedgerCorrupted):
            self.replay_finance(official_proposal={**self.proposal,
                                                  "scope_note":"new scope cannot reuse old proof"})
        with self.assertRaises(InvalidInput):
            self.replay_finance(expected_inventory_sha256=sha256(b"wrong"))
        with self.assertRaises(LedgerCorrupted):
            altered={**self.relation,"rationale":"changed rationale"}
            self.replay_finance(prior_relation=altered)

    def test_finance_read_replay_refuses_historical_revision(self):
        self.ready();self.finance()
        self.model(key="rev_B_for_replay",kind="B")
        self.model(key="rev_A_again_for_replay",kind="A")
        with self.assertRaisesRegex(DomainConflict,"CURRENT_CANDIDATE_NOT_AVAILABLE"):
            self.replay_finance()

    def test_unverified_finance_preview_never_issues_terminal(self):
        self.ready();self.finance();self.replay_finance()
        with self.assertRaises(QualityNotProven):
            self.store.issue_terminal_receipt("v6_test_scope")
        self.assertFalse(self.store.progress_receipt("v6_test_scope")["engine_quality_certified"])

    def test_ledger_tamper_blocks_snapshot_and_finance(self):
        self.ready();self.finance()
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE events SET event_json='{}' WHERE scope_id='v6_test_scope' AND sequence=6")
            con.commit()
        with self.assertRaises(LedgerCorrupted):self.store.snapshot("v6_test_scope")
        with self.assertRaises(LedgerCorrupted):self.finance(command_id="retry_tampered")

    def test_public_event_json_does_not_contain_document_or_srt_body(self):
        self.ready();self.finance()
        with closing(sqlite3.connect(self.db)) as con:
            blobs="\n".join(row[0] for row in con.execute("SELECT event_json FROM events"))
        self.assertNotIn("a fictional condition has an exception",blobs)
        self.assertNotIn("the original condition must still",blobs)
        self.assertIn("SOURCE_CANDIDATE_REVIEW_PENDING",blobs)


if __name__ == "__main__":
    unittest.main()
