"""V6 official-primary-source terminal V2 RED/GREEN on genuine 2026 raw law.

All subtitles in this test are synthetic; original private user SRT stays off
GitHub. Unlike the legacy blind arithmetic path, this official-source rule
needs NO independent human judges, but cannot issue engine-wide P0 GO.
"""
from __future__ import annotations
import copy
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import (
    ConcurrentHeadChanged, DomainConflict, IdempotencyConflict,
    InvalidInput, LedgerCorrupted, QualityNotProven,
)
from ire.v6.official_completion import (
    LAW_RULE_ID, LAW_SOURCE_SHA256, LAW_ORIGINAL_URL,
    CANONICAL_PROPOSITION, verify_pinned_law,
)
from ire.v6.source import verify_source
from ire.v6.store import TransactionStore
from ire.v6.tests.test_source_and_proof import (
    VIDEO, make_manifest, make_model, make_review, make_srt,
)

SCOPE = "official_v2_scope"
ROOT = Path(__file__).resolve().parents[3]
LAW_PATH = ROOT / "validation/ire-v6-frozen/public_official_raw_20261108/decree_40_3.html"


class OfficialTerminalV2Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store=TransactionStore(Path(tmp.name)/"private"/"official.db")
        self.raw=make_srt([CANONICAL_PROPOSITION,
                           "연금계좌에서 일부 인출하면 모두 비과세된다.",
                           "A synthetic cue for the conditional case.",
                           "Nothing here is an investment recommendation."])
        self.manifest=make_manifest(self.raw, cut=4)
        src=verify_source(self.raw,self.manifest,
                          expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(self.manifest))
        inv={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":src.cue_census_sha256}]}
        self.inv_bytes=canonical(inv)
        self.inv_sha=sha256(self.inv_bytes)
        self.official=LAW_PATH.read_bytes()
        self.assertEqual(sha256(self.official),LAW_SOURCE_SHA256)
        self.baseline={"schema":"IRE_V6_LEGACY_BASELINE_V1","entries":[{
            "id":"LEGACY-000","content_sha256":sha256(b"synthetic knowledge")}]}
        self.relation={"schema":"IRE_V6_PRIOR_RELATION_CANDIDATE_V1",
                       "claim_id":"C00001","prior_id":"LEGACY-000",
                       "relationship":"OPEN","rationale":"No semantic merge",
                       "semantic_relation_verified":False}
        self.proposal={
            "schema":"IRE_V6_OFFICIAL_CANDIDATE_V1","claim_id":"C00001",
            "issuer":"국가법령정보센터","url":LAW_ORIGINAL_URL,
            "quote":"연금계좌에서 일부 금액이 인출되는 경우에는 다음 각 호의 금액이 순서에 따라 인출되는 것으로 본다.",
            "published_on":"2026-09-30","effective_from":"2026-10-01",
            "effective_until":None,"retrieved_on":"2026-11-08",
            "jurisdiction":"Republic of Korea","scope_note":"Only the registered statutory deemed order",
            "claim_support_verdict":"UNREVIEWED",
        }
        self.finance_input={
            "official_document_raw":self.official,
            "official_proposal":self.proposal,
            "expected_official_sha256":LAW_SOURCE_SHA256,
            "as_of":"2026-11-08","prior_baseline":self.baseline,
            "prior_relation":self.relation,
            "expected_baseline_sha256":json_digest(self.baseline),
        }
        self.store.create_scope(scope_id=SCOPE,video_id=VIDEO,
            source_sha256=sha256(self.raw),
            manifest_sha256=json_digest(self.manifest),command_id="genesis")

    def head(self):
        return self.store.snapshot(SCOPE)["ledger_head_sha256"]

    def setup_recorded(self, *, proposition=None, kind="FACT", include_finance=True):
        self.store.attest_source(scope_id=SCOPE,command_id="attest",expected_head=self.head(),
                                 raw=self.raw,manifest=self.manifest)
        self.store.attest_owner_inventory(scope_id=SCOPE,command_id="owner",expected_head=self.head(),
            raw=self.raw,manifest=self.manifest,inventory_bytes=self.inv_bytes,
            expected_inventory_sha256=self.inv_sha)
        m=make_model(first=1,last=1,quote1=CANONICAL_PROPOSITION)
        m["claims"][0]["kind"]=kind
        m["claims"][0]["proposition"]=CANONICAL_PROPOSITION if proposition is None else proposition
        self.store.submit(scope_id=SCOPE,command_id="model",expected_head=self.head(),
                          kind="MODEL_RECORDED",payload={"window_id":"W00001","model":m})
        self.store.submit_structural_proof(
            scope_id=SCOPE,command_id="proof",expected_head=self.head(),window_id="W00001",
            raw=self.raw,manifest=self.manifest,review=make_review())
        if include_finance:
            self.store.submit_finance_candidate(
                scope_id=SCOPE,command_id="finance",expected_head=self.head(),
                window_id="W00001",raw=self.raw,manifest=self.manifest,
                inventory_bytes=self.inv_bytes,expected_inventory_sha256=self.inv_sha,
                **self.finance_input)

    def decision(self,*,verdict="VERIFIED"):
        model=self.store.snapshot(SCOPE)["state"]["models"]["W00001"]
        return [{"window_id":"W00001","claim_id":"C00001",
                 "model_revision_event_sha256":model["revision_event_sha256"],
                 "verdict":verdict,"rule_id":LAW_RULE_ID,
                 "conditions_acknowledged":["SECTION_201_10_CONFIRMATION_WHEN_APPLICABLE"]}]

    def args(self, *, command_id="official_close",expected_head=None,
             finance_inputs=None,determinations=None,official_document_raw=None,as_of="2026-11-08"):
        return dict(scope_id=SCOPE,command_id=command_id,
                    expected_head=expected_head or self.head(),
                    raw=self.raw,manifest=self.manifest,
                    inventory_bytes=self.inv_bytes,expected_inventory_sha256=self.inv_sha,
                    finance_inputs=finance_inputs if finance_inputs is not None
                       else {"W00001:C00001":self.finance_input},
                    determinations=determinations if determinations is not None
                       else self.decision(),
                    official_document_raw=official_document_raw if official_document_raw is not None
                       else self.official,as_of=as_of)

    def test_true_official_scoped_complete_and_reopened_sqlite(self):
        self.setup_recorded()
        old=self.head()
        terminal=self.store.issue_terminal_receipt(**self.args(expected_head=old))
        self.assertFalse(terminal["research_complete"])
        self.assertTrue(terminal["scoped_official_rule_verified"])
        self.assertFalse(terminal["engine_quality_certified"])
        self.assertFalse(terminal["p0_go"])
        reopened=TransactionStore(self.store.path)
        read=reopened.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=terminal["event_sha256"])
        self.assertFalse(read["research_complete"])
        self.assertTrue(read["is_current"])
        self.assertEqual(read["report"]["officially_verified_fact_count"],1)
        self.assertFalse(reopened.progress_receipt(SCOPE)["research_complete"])
        self.assertFalse(reopened.progress_receipt(SCOPE)["p0_go"])
        with closing(sqlite3.connect(self.store.path)) as con:
            joined="\n".join(r[0] for r in con.execute("SELECT event_json FROM events"))
        self.assertNotIn("00:00:01,000 -->",joined)
        self.assertNotIn("<html",joined.lower())

    def test_idempotency_exact_retry_and_changed_rejection(self):
        self.setup_recorded()
        old=self.head()
        args=self.args(expected_head=old)
        one=self.store.issue_terminal_receipt(**args)
        two=self.store.issue_terminal_receipt(**args)
        self.assertEqual(one["event_sha256"],two["event_sha256"])
        self.assertTrue(two["idempotent_replay"])
        with self.assertRaisesRegex(IdempotencyConflict,"RETRY_CHANGED"):
            self.store.issue_terminal_receipt(**dict(args,determinations=[]))

    def test_unregistered_fact_is_rejected_without_head_mutation(self):
        self.setup_recorded(proposition="연금계좌의 모든 인출액은 세금이 없다")
        head=self.head()
        with self.assertRaisesRegex(QualityNotProven,"NOT_EXACT_REGISTERED"):
            self.store.issue_terminal_receipt(**self.args())
        self.assertEqual(self.head(),head)

    def test_missing_finance_and_proof_never_complete(self):
        self.setup_recorded(include_finance=False)
        head=self.head()
        with self.assertRaises(QualityNotProven):
            self.store.issue_terminal_receipt(**self.args(finance_inputs={}))
        self.assertEqual(self.head(),head)

    def test_fake_official_source_and_time_rejected(self):
        self.setup_recorded()
        head=self.head()
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_BYTES_NOT_PINNED"):
            self.store.issue_terminal_receipt(**self.args(official_document_raw=self.official+b"x"))
        with self.assertRaisesRegex(QualityNotProven,"SOURCE_VERSION_NOT_ESTABLISHED"):
            self.store.issue_terminal_receipt(**self.args(as_of="2026-11-09"))
        self.assertEqual(self.head(),head)

    def test_unsupported_verdict_and_missing_conditions_block(self):
        self.setup_recorded()
        bad=self.decision(verdict="UNVERIFIED")
        with self.assertRaisesRegex(QualityNotProven,"NOT_FIRST_PARTY_VERIFIED"):
            self.store.issue_terminal_receipt(**self.args(determinations=bad))
        bad=self.decision()
        bad[0]["conditions_acknowledged"]=[]
        with self.assertRaisesRegex(QualityNotProven,"MATERIAL_CONDITION_MISSING"):
            self.store.issue_terminal_receipt(**self.args(determinations=bad))

    def test_old_unqualified_api_still_fails(self):
        self.setup_recorded()
        with self.assertRaises(QualityNotProven):
            self.store.issue_terminal_receipt(SCOPE)

    def test_stale_revision_and_concurrent_head_rejected(self):
        self.setup_recorded()
        stale=self.decision()
        old=self.head()
        m=make_model(first=1,last=1,quote1=CANONICAL_PROPOSITION)
        m["claims"][0]["kind"]="FACT"
        m["claims"][0]["proposition"]=CANONICAL_PROPOSITION
        self.store.submit(scope_id=SCOPE,command_id="new_model",expected_head=old,
            kind="MODEL_RECORDED",payload={"window_id":"W00001","model":m})
        with self.assertRaises(ConcurrentHeadChanged):
            self.store.issue_terminal_receipt(**self.args(
                expected_head=old,determinations=stale))
        with self.assertRaises(QualityNotProven):
            self.store.issue_terminal_receipt(**self.args())

    def test_signature_and_text_tamper_fail_closed(self):
        self.setup_recorded()
        with self.assertRaisesRegex(InvalidInput,"OFFICIAL_ORIGINAL_BYTES_NOT_PINNED"):
            verify_pinned_law(b"fake",as_of="2026-11-08")
        with self.assertRaisesRegex(QualityNotProven,"SOURCE_VERSION_NOT_ESTABLISHED"):
            verify_pinned_law(self.official,as_of="2026-09-30")


    def test_revised_model_revokes_current_completion_and_old_retry_is_historical(self):
        self.setup_recorded()
        args=self.args()
        finished=self.store.issue_terminal_receipt(**args)
        self.assertFalse(self.store.progress_receipt(SCOPE)["research_complete"])
        revised=make_model(first=1,last=1,quote1=CANONICAL_PROPOSITION)
        revised["claims"][0]["kind"]="FACT"
        revised["claims"][0]["proposition"]=CANONICAL_PROPOSITION
        self.store.submit(scope_id=SCOPE,command_id="model_revised_after_completion",
            expected_head=self.head(),kind="MODEL_RECORDED",
            payload={"window_id":"W00001","model":revised})
        reopened=TransactionStore(self.store.path)
        historical=reopened.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=finished["event_sha256"])
        self.assertFalse(historical["historical_scope_completed"])
        self.assertFalse(historical["is_current"])
        self.assertFalse(historical["research_complete"])
        self.assertFalse(reopened.progress_receipt(SCOPE)["research_complete"])
        exact_retry=reopened.issue_terminal_receipt(**args)
        self.assertTrue(exact_retry["idempotent_replay"])
        self.assertFalse(exact_retry["historical_scope_completed"])
        self.assertFalse(exact_retry["research_complete"])
        self.assertFalse(exact_retry["is_current"])
        with self.assertRaises(QualityNotProven):
            reopened.issue_terminal_receipt(**self.args(command_id="new_completion"))

    def test_cannot_forge_terminal_through_generic_submit(self):
        self.setup_recorded()
        with self.assertRaisesRegex(DomainConflict,"COMMAND_KIND_NOT_ENABLED"):
            self.store.submit(scope_id=SCOPE,command_id="forged",expected_head=self.head(),
                kind="TERMINAL_OFFICIAL_COMPLETION_RECORDED",payload={})


    def test_omitted_second_high_risk_fact_cannot_close_research(self):
        # A valid official legal statement is in cue 1, but cue 2 asserts a
        # contradictory tax rule. The model submits only cue 1.
        self.setup_recorded()
        receipt=self.store.issue_terminal_receipt(**self.args())
        self.assertTrue(receipt["scoped_official_rule_verified"])
        self.assertFalse(receipt["research_complete"])
        report=self.store.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=receipt["event_sha256"])["report"]
        self.assertFalse(report["source_claim_census_independently_verified"])
        self.assertFalse(report["nonfact_roles_independently_verified"])
        self.assertFalse(report["research_complete"])
        self.assertFalse(self.store.progress_receipt(SCOPE)["research_complete"])

    def test_false_tax_fact_self_labelled_question_never_closes_research(self):
        self.setup_recorded()
        m=make_model(first=1,last=1,quote1=CANONICAL_PROPOSITION)
        m["claims"][0]["kind"]="FACT"
        m["claims"][0]["proposition"]=CANONICAL_PROPOSITION
        second=copy.deepcopy(m["claims"][0])
        second.update({"claim_id":"C00002","kind":"QUESTION",
                       "proposition":"연금계좌에서 일부 인출하면 모두 비과세된다.",
                       "source_refs":[{"cue_index":2,
                           "quote":"연금계좌에서 일부 인출하면 모두 비과세된다."}],
                       "context_first_cue":2,"context_last_cue":2})
        m["claims"].append(second)
        self.store.submit(scope_id=SCOPE,command_id="two_model_claims",
            expected_head=self.head(),kind="MODEL_RECORDED",
            payload={"window_id":"W00001","model":m})
        review=make_review()
        review["reviewed_claim_ids"].append("C00002")
        self.store.submit_structural_proof(
            scope_id=SCOPE,command_id="two_model_proof",expected_head=self.head(),
            window_id="W00001",raw=self.raw,manifest=self.manifest,review=review)
        self.store.submit_finance_candidate(
            scope_id=SCOPE,command_id="two_model_finance",expected_head=self.head(),
            window_id="W00001",raw=self.raw,manifest=self.manifest,
            inventory_bytes=self.inv_bytes,
            expected_inventory_sha256=self.inv_sha,**self.finance_input)
        reviews=self.decision()
        reviews.append({"window_id":"W00001","claim_id":"C00002",
                        "model_revision_event_sha256":reviews[0]["model_revision_event_sha256"],
                        "verdict":"NOT_FACT_CLAIM","rule_id":None,
                        "conditions_acknowledged":[]})
        receipt=self.store.issue_terminal_receipt(
            **self.args(command_id="mislabelled_nonfact",determinations=reviews))
        report=self.store.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=receipt["event_sha256"])["report"]
        self.assertEqual(report["model_labelled_nonfact_count"],1)
        self.assertFalse(report["nonfact_roles_independently_verified"])
        self.assertFalse(receipt["research_complete"])

    def test_second_rule_receipt_same_revision_rejected(self):
        self.setup_recorded()
        one=self.store.issue_terminal_receipt(**self.args())
        self.assertTrue(self.store.progress_receipt(SCOPE)["scoped_official_rule_verified"])
        with self.assertRaisesRegex(DomainConflict,"OFFICIAL_RULE_ALREADY_VERIFIED_CURRENT"):
            self.store.issue_terminal_receipt(**self.args(command_id="second_rule"))
        self.assertFalse(self.store.progress_receipt(SCOPE)["research_complete"])
        self.assertEqual(self.head(),one["event_sha256"])


    def test_interleaved_unrelated_review_does_not_expire_narrow_rule(self):
        self.setup_recorded()
        terminal=self.store.issue_terminal_receipt(**self.args())
        model=self.store.snapshot(SCOPE)["state"]["models"]["W00001"]
        self.store.submit(scope_id=SCOPE,command_id="unrelated_review",
            expected_head=self.head(),kind="REVIEW_PROPOSED",
            payload={"window_id":"W00001",
                     "model_revision_event_sha256":model["revision_event_sha256"],
                     "review":{"note":"unverified commentary"}})
        progress=self.store.progress_receipt(SCOPE)
        self.assertTrue(progress["scoped_official_rule_verified"])
        self.assertEqual(progress["terminal_outcome"],"OFFICIAL_RULE_VERIFIED_RESEARCH_OPEN")
        self.assertFalse(progress["research_complete"])
        historical=self.store.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=terminal["event_sha256"])
        self.assertTrue(historical["is_current"])
        self.assertFalse(historical["source_speaker_meaning_verified"])
        with self.assertRaisesRegex(DomainConflict,"OFFICIAL_RULE_ALREADY_VERIFIED_CURRENT"):
            self.store.issue_terminal_receipt(**self.args(command_id="interleaved_duplicate"))

    def test_post_verification_model_revision_invalidates_rule(self):
        self.setup_recorded()
        self.store.issue_terminal_receipt(**self.args())
        new_model=make_model(first=1,last=1,quote1=CANONICAL_PROPOSITION)
        new_model["claims"][0]["proposition"]=CANONICAL_PROPOSITION
        self.store.submit(scope_id=SCOPE,command_id="new_revision_for_coverage",
            expected_head=self.head(),kind="MODEL_RECORDED",
            payload={"window_id":"W00001","model":new_model})
        progress=self.store.progress_receipt(SCOPE)
        self.assertFalse(progress["scoped_official_rule_verified"])
        self.assertEqual(progress["terminal_outcome"],"V6_KERNEL_ONLY_VALIDATION_OPEN")
        self.assertFalse(progress["research_complete"])

    def test_negated_quote_in_same_cue_rejected_not_published(self):
        # The registered statutory sentence is *quoted and denied* in the cue.
        self.raw=make_srt([CANONICAL_PROPOSITION+" 그러나 이것은 틀린 주장입니다.",
            "A neutral cue.", "An independent synthetic cue.", "Further neutral text."])
        self.manifest=make_manifest(self.raw,cut=4)
        src=verify_source(self.raw,self.manifest,
            expected_source_sha256=sha256(self.raw),
            expected_manifest_sha256=json_digest(self.manifest))
        inv={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":src.cue_census_sha256}]}
        self.inv_bytes=canonical(inv)
        self.inv_sha=sha256(self.inv_bytes)
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store=TransactionStore(Path(tmp.name)/"private"/"negation.db")
        self.store.create_scope(scope_id=SCOPE,video_id=VIDEO,
            source_sha256=sha256(self.raw),manifest_sha256=json_digest(self.manifest),
            command_id="negation_genesis")
        self.setup_recorded()
        before=self.head()
        with self.assertRaisesRegex(QualityNotProven,"OFFICIAL_ORIGINAL_SOURCE_DOES_NOT_ASSERT_RULE"):
            self.store.issue_terminal_receipt(**self.args())
        self.assertEqual(self.head(),before)
        self.assertFalse(self.store.progress_receipt(SCOPE)["scoped_official_rule_verified"])

if __name__=="__main__":
    unittest.main()
