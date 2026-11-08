"""V6-2/3 byte replay, protected proofs and adversarial transaction tests.

Only invented synthetic financial-free subtitles are used. Real private
sources, author identity, semantic precision and official rules remain OPEN.
"""
from __future__ import annotations

import copy
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6 import (ConcurrentHeadChanged, DomainConflict, IdempotencyConflict,
                    InvalidInput, LedgerCorrupted, QualityNotProven,
                    TransactionStore, UnsupportedSchema)
from ire.v6.codec import json_digest, sha256
from ire.v6.source import parse_srt, verify_source
from ire.v6.proof import audit_model_anchors

VIDEO="AbCdEf12345"
TEXTS=["A statement about a hypothetical rule",
       "if an exception exists it must be evaluated",
       "however a second narrator rejects that interpretation",
       "the original condition must still be considered"]


def make_srt(texts=TEXTS,*,timestamps=None):
    timestamps=timestamps or [1000,2000,3000,4000]
    return ("\n\n".join(f"{i}\n00:00:{int(t//1000):02d},{t%1000:03d} --> "
                         f"00:00:{int(t//1000):02d},{(t%1000)+700:03d}\n{text}"
                         for i,(text,t) in enumerate(zip(texts,timestamps),1))).encode("utf-8")


def make_manifest(raw,*,scope_first=1,scope_last=None,start_window=1,cut=2,mode="FULL_VIDEO"):
    cues=parse_srt(raw)
    scope_last=scope_last or len(cues)
    windows=[]
    for ix, begin in enumerate(range(scope_first,scope_last+1,cut)):
        end=min(begin+cut-1,scope_last)
        windows.append({"window_id":f"W{start_window+ix:05d}",
                        "first_cue":begin,"last_cue":end,
                        "text_sha256":sha256(" ".join(cues[j-1].text for j in range(begin,end+1)).encode("utf-8"))})
    return {"schema":"IRE_V6_SOURCE_PLAN_V1","video_id":VIDEO,
            "source_sha256":sha256(raw),"cue_count":len(cues),
            "scope":{"mode":mode,"first_cue":scope_first,"last_cue":scope_last},
            "windows":windows}


def make_model(*, owner="W00001",first=2,last=3,quote1=None,quote2=None):
    refs=[{"cue_index":first,"quote":quote1 or TEXTS[first-1]}]
    if first!=last:
        refs.append({"cue_index":last,"quote":quote2 or TEXTS[last-1]})
    return {"schema":"IRE_V6_ATOMIC_MODEL_V1","claims":[{
        "claim_id":"C00001","proposition":"A linked conditional statement",
        "kind":"HYPOTHETICAL","owner_window_id":owner,"source_refs":refs,
        "context_first_cue":first,"context_last_cue":last}]}


def make_review(*,independent=False):
    return {"schema":"IRE_V6_STRUCTURAL_REVIEW_V1",
            "review_scope":"SOURCE_ANCHORS_ONLY",
            "reviewed_claim_ids":["C00001"],
            "independent_gold_verified":independent}


class SourceAndProofTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/"private"/"v6.db"
        self.raw=make_srt()
        self.manifest=make_manifest(self.raw)
        self.store=TransactionStore(self.db)
        self.genesis=self.store.create_scope(scope_id="research_scope",video_id=VIDEO,
                     source_sha256=sha256(self.raw),manifest_sha256=json_digest(self.manifest),
                     command_id="genesis_record")

    def head(self):
        return self.store.snapshot("research_scope")["ledger_head_sha256"]

    def attest(self,key="private_source_attested",*,raw=None,manifest=None,expected=None):
        return self.store.attest_source(scope_id="research_scope",command_id=key,
                    expected_head=expected or self.head(),
                    raw=self.raw if raw is None else raw,
                    manifest=self.manifest if manifest is None else manifest)

    def model(self,*,kind="A",key="submit_model_A"):
        return self.store.submit(scope_id="research_scope",command_id=key,
                  expected_head=self.head(),kind="MODEL_RECORDED",
                  payload={"window_id":"W00001", "model":make_model() if kind=="A" else
                           {**make_model(),"claims":[{**make_model()["claims"][0],
                                                      "proposition":kind+" revised content"}]}})

    def proof(self,*,key="proof_A",review=None,raw=None,manifest=None,expected=None):
        return self.store.submit_structural_proof(
            scope_id="research_scope",command_id=key,expected_head=expected or self.head(),
            window_id="W00001",raw=self.raw if raw is None else raw,
            manifest=self.manifest if manifest is None else manifest,
            review=make_review() if review is None else review)

    def test_source_exact_bytes_replay_and_no_false_approval(self):
        result=self.attest()
        self.assertEqual(result["sequence"],2)
        snap=self.store.snapshot("research_scope")
        self.assertTrue(snap["progress"]["source_attestation_recorded"])
        self.assertFalse(snap["progress"]["source_original_bytes_verified"])
        live=self.store.snapshot_with_source(scope_id="research_scope",raw=self.raw,manifest=self.manifest)
        self.assertTrue(live["source_original_bytes_verified_this_call"])
        self.assertFalse(live["engine_quality_certified"])
        self.assertEqual(live["current_structural_proofs_reverified"],0)
        with self.assertRaises(QualityNotProven):self.store.issue_terminal_receipt("research_scope")
        with closing(sqlite3.connect(self.db)) as con:
            stored=b"".join(bytes(row[0],"utf8") for row in con.execute("SELECT event_json FROM events"))
        self.assertNotIn(TEXTS[0].encode("utf-8"),stored)

    def test_real_bytes_change_and_updated_but_unpinned_manifest_refused(self):
        altered=self.raw.replace(TEXTS[2].encode(),b"the attacker substituted text without changing timing")
        with self.assertRaisesRegex(InvalidInput,"PINNED_SOURCE_OR_PLAN_BYTES_MISMATCH"):
            self.attest(raw=altered)
        with self.assertRaisesRegex(InvalidInput,"PINNED_SOURCE_OR_PLAN_BYTES_MISMATCH"):
            self.attest(raw=altered,manifest=make_manifest(altered))
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],1)

    def test_time_only_change_fails_even_when_cue_text_same(self):
        altered=self.raw.replace(b"00:00:03,000",b"00:00:03,001")
        with self.assertRaises(InvalidInput):self.attest(raw=altered)

    def test_nonmonotonic_start_fails_with_even_recomputed_hashes(self):
        altered=make_srt(timestamps=[1000,3000,2000,4000])
        with self.assertRaisesRegex(InvalidInput,"SRT_NON_MONOTONIC_START"):
            verify_source(altered,make_manifest_for_negative(altered),
                expected_source_sha256=sha256(altered),
                expected_manifest_sha256=json_digest(make_manifest_for_negative(altered)))

    def test_window_order_and_contiguous_primary_owner(self):
        for mutation in (lambda m:m["windows"][1].update(window_id="W00004"),
                         lambda m:m["windows"][1].update(first_cue=4),
                         lambda m:m["windows"][1].update(first_cue=2)):
            copied=copy.deepcopy(self.manifest)
            mutation(copied)
            with self.subTest(copied=copied),self.assertRaises(InvalidInput):
                verify_source(self.raw,copied,
                              expected_source_sha256=sha256(self.raw),
                              expected_manifest_sha256=json_digest(copied))

    def test_source_plan_detached_from_mutating_caller(self):
        mutable=copy.deepcopy(self.manifest)
        verified=verify_source(self.raw,mutable,
            expected_source_sha256=sha256(self.raw),
            expected_manifest_sha256=json_digest(self.manifest))
        mutable["scope"]["first_cue"]=4
        mutable["windows"][0]["first_cue"]=4
        self.assertEqual(verified.attestation()["scope_first_cue"],1)
        self.assertEqual(verified.owner(2),"W00001")

    def test_partial_window_offset_and_explicit_scope(self):
        m=make_manifest(self.raw,scope_first=3,scope_last=4,start_window=25,mode="PARTIAL")
        out=verify_source(self.raw,m,expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(m))
        self.assertEqual(out.owner(4),"W00025")
        self.assertIsNone(out.owner(2))
        m["scope"]["mode"]="FULL_VIDEO"
        with self.assertRaises(InvalidInput):verify_source(self.raw,m,
                    expected_source_sha256=sha256(self.raw),expected_manifest_sha256=json_digest(m))

    def test_source_attestation_retry_and_conflicting_replay(self):
        first=self.attest()
        same=self.attest(expected=self.genesis["event_sha256"])
        self.assertTrue(same["idempotent_replay"])
        self.assertEqual(first["event_sha256"],same["event_sha256"])
        with self.assertRaises(ConcurrentHeadChanged):self.attest(key="another_attestation",expected=self.genesis["event_sha256"])
        with self.assertRaises(DomainConflict):self.attest(key="another_attestation")

    def test_pilot_cross_window_anchor_requires_original_cue(self):
        self.attest()
        self.model()
        result=self.proof()
        self.assertEqual(result["sequence"],4)
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],1)
        live=self.store.snapshot_with_source(scope_id="research_scope",raw=self.raw,manifest=self.manifest)
        self.assertEqual(live["current_structural_proofs_reverified"],1)
        self.assertFalse(live["semantic_recall_verified"])
        self.assertFalse(live["p0_go"])
        self.assertFalse(self.store.progress_receipt("research_scope")["terminal"])

    def test_proof_wont_accept_false_independence_or_impossible_quote(self):
        self.attest()
        self.model()
        with self.assertRaises(InvalidInput):self.proof(key="false_blind",review=make_review(independent=True))
        with self.assertRaises(InvalidInput):self.proof(key="wrong_review",review={**make_review(),"reviewed_claim_ids":[]})
        with self.assertRaises(InvalidInput):audit_model_anchors(
            verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                expected_manifest_sha256=json_digest(self.manifest)),
            "W00001",make_model(quote1="not spoken in any original cue"),make_review())
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],3)

    def test_structural_anchor_cannot_steal_neighbor_owner(self):
        src=verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                         expected_manifest_sha256=json_digest(self.manifest))
        with self.assertRaisesRegex(InvalidInput,"PRIMARY_OWNER_INVALID"):
            audit_model_anchors(src,"W00001",make_model(first=3,last=4),make_review())
        with self.assertRaisesRegex(InvalidInput,"CONTEXT_SPAN_INCOMPLETE"):
            model=make_model()
            model["claims"][0]["context_last_cue"]=2
            audit_model_anchors(src,"W00001",model,make_review())

    def test_attestation_and_proof_cannot_be_forged_through_generic_submit(self):
        for name in ("SOURCE_ATTESTED","STRUCTURAL_PROOF_RECORDED", "RESEARCH_CLOSURE", "ENGINE_QUALITY_GO"):
            with self.subTest(name=name),self.assertRaises(DomainConflict):
                self.store.submit(scope_id="research_scope",command_id="forged",
                    expected_head=self.head(),kind=name,payload={"approved":True})
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],1)

    def test_exact_proof_retry_is_idempotent_and_historical(self):
        self.attest();self.model()
        at=self.head()
        first=self.proof(expected=at)
        replay=self.proof(expected=at)
        self.assertEqual(replay["event_sha256"],first["event_sha256"])
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],4)
        with self.assertRaises(IdempotencyConflict):
            self.proof(expected=at,review={**make_review(),"reviewed_claim_ids":[]})
        self.model(kind="B",key="rev_B")
        historical=self.proof(expected=at)
        self.assertTrue(historical["idempotent_replay"])
        self.assertFalse(historical["research_complete"])
        self.assertEqual(self.store.snapshot("research_scope")["progress"]
                         ["current_revision_structural_proof_records"],0)

    def test_unhashable_kind_is_typed_invalid_input(self):
        src=verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(self.manifest))
        model=make_model();model["claims"][0]["kind"]=["FACT"]
        with self.assertRaises(InvalidInput):
            audit_model_anchors(src,"W00001",model,make_review())

    def test_revision_aba_hides_old_proof_and_rejects_reuse(self):
        self.attest()
        first=self.model()
        self.proof()
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],1)
        self.model(kind="B",key="model_B")
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],0)
        self.model(key="model_A_again")
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],0)
        live=self.store.snapshot_with_source(scope_id="research_scope",raw=self.raw,manifest=self.manifest)
        self.assertEqual(live["current_structural_proofs_reverified"],0)
        self.proof(key="proof_A_again")
        self.assertEqual(self.store.snapshot_with_source(scope_id="research_scope",raw=self.raw,
                         manifest=self.manifest)["current_structural_proofs_reverified"],1)
        self.assertNotEqual(first["event_sha256"],
            self.store.snapshot("research_scope")["state"]["models"]["W00001"]["revision_event_sha256"])

    def test_source_drift_after_proof_blocks_fresh_replay(self):
        self.attest();self.model();self.proof()
        altered=self.raw.replace(TEXTS[0].encode(),b"different not source pinned")
        with self.assertRaises(InvalidInput):self.store.snapshot_with_source(
            scope_id="research_scope",raw=altered,manifest=self.manifest)
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],1)

    def test_source_attestation_mid_commit_crash_simulation_rolls_back(self):
        original=self.head()
        def crash(stage):
            if stage=="after_head_update":
                raise RuntimeError("INJECTED_CRASH_BEFORE_SOURCE_ATTESTATION_COMMIT")
        self.store._before_commit=crash
        with self.assertRaisesRegex(RuntimeError,"INJECTED_CRASH"):
            self.attest()
        self.store=TransactionStore(self.db)
        self.assertEqual(self.head(),original)
        self.assertFalse(self.store.snapshot("research_scope")["progress"]["source_attestation_recorded"])
        self.attest()
        self.assertTrue(self.store.snapshot("research_scope")["progress"]["source_attestation_recorded"])

    def test_proof_mid_commit_crash_simulation_rolls_back(self):
        self.attest();self.model()
        original=self.head()
        def crash(stage):
            if stage=="after_event_insert":
                raise RuntimeError("INJECTED_CRASH_BEFORE_PROOF_COMMIT")
        self.store._before_commit=crash
        with self.assertRaisesRegex(RuntimeError,"INJECTED_CRASH"):
            self.proof()
        self.store=TransactionStore(self.db)
        self.assertEqual(self.head(),original)
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],0)
        self.assertEqual(self.store.snapshot_with_source(scope_id="research_scope",
                         raw=self.raw,manifest=self.manifest)["current_structural_proofs_reverified"],0)
        self.proof()
        reopened=TransactionStore(self.db)
        self.assertEqual(reopened.snapshot_with_source(scope_id="research_scope",
                         raw=self.raw,manifest=self.manifest)["current_structural_proofs_reverified"],1)

    def test_event_chain_corruption_fails_even_with_available_original(self):
        self.attest();self.model();self.proof()
        con=sqlite3.connect(self.db)
        con.execute("UPDATE events SET event_json=? WHERE scope_id=? AND sequence=4",
                    ('{"fake":true}',"research_scope"))
        con.commit();con.close()
        with self.assertRaises(LedgerCorrupted):self.store.snapshot_with_source(
             scope_id="research_scope",raw=self.raw,manifest=self.manifest)
        with self.assertRaises(LedgerCorrupted):self.store.progress_receipt("research_scope")

    def test_v6_1_db_requires_explicit_migration_no_silent_upgrade(self):
        con=sqlite3.connect(self.db)
        con.execute("PRAGMA user_version=1");con.commit();con.close()
        with self.assertRaisesRegex(UnsupportedSchema,"MIGRATION_REQUIRED"):
            TransactionStore(self.db)
        con=sqlite3.connect(self.db)
        try:self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0],1)
        finally:con.close()

    def test_proof_error_and_concurrent_stale_head_leave_no_partial_event(self):
        self.attest();self.model()
        old_head=self.head()
        # A second handle commits a new model before the first proof submission.
        TransactionStore(self.db).submit(scope_id="research_scope",command_id="racer",
            expected_head=old_head,kind="MODEL_RECORDED",payload={"window_id":"W00002",
                                                                 "model":{"draft":"unverified"}})
        with self.assertRaises(ConcurrentHeadChanged):self.proof(expected=old_head)
        self.assertEqual(self.store.snapshot("research_scope")["sequence"],4)
        self.assertEqual(self.store.snapshot("research_scope")["progress"]["current_revision_structural_proof_records"],0)


def make_manifest_for_negative(raw):
    # Source manifest made directly from deliberately out-of-order timestamps;
    # string hashes can all match but temporal truth still fails.
    blocks=raw.decode().split("\n\n")
    texts=[x.splitlines()[2].strip() for x in blocks]
    return {"schema":"IRE_V6_SOURCE_PLAN_V1","video_id":VIDEO,"source_sha256":sha256(raw),
            "cue_count":len(texts),"scope":{"mode":"FULL_VIDEO","first_cue":1,"last_cue":len(texts)},
            "windows":[{"window_id":"W00001","first_cue":1,"last_cue":len(texts),
                        "text_sha256":sha256(" ".join(texts).encode())}]}


if __name__=='__main__':unittest.main()
