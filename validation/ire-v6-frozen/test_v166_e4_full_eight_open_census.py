"""E4 B0001 8/8 OPEN reconciliation: original V164 five + E4 three.

All the source text here is SYNTHETIC. The original private user video is
checked separately in a local restricted no-uploads replay. No CI test
publishes genuine investment claims or self-approves V123 OPEN.
"""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_manifest
from test_v164_typed_v123 import TypedReviewSyntheticTests
from v164_typed_v123 import _cue_pin
from test_v166_e4_owner_open_partial_source import (
    TEXTS,BODY,NOTE)
from v166_e4_owner_open_partial_source import (
    OPEN_CLAIMS,assess_open_partial_claim)
from v166_e4_full_eight_open_census import (
    audit_b0001_eight_open,EXPECTED_OPEN,TYPED_IDS,DOCUMENT_IDS)


def synthetic_full_owner_case():
    pilot=TypedReviewSyntheticTests("test_01_all_five_synthetic_source_speech_rows_attested")
    pilot.setUp()
    special={
      3:"가상으로 들어가서 손해를 보면 어떻게 해야 하는 질문입니다.",
      5:"확신하고 매수했다는 말은 무슨 질문인가요?",
      42:"낯선 사례를 읽으니 꽤 어렵다고 느낀 주관적 감상입니다.",
      69:"사업 방법을 자산 투자에 적용해 보는 것은 어떨까요?",
      95:"저가에 매입하면 손실이 적을 것이라고 가정하는 조건부 설명입니다.",
    }
    pos={"C00002":30,"C00009":98,"C00010":107}
    for cid,first in pos.items():
        for n,quote in enumerate(TEXTS[cid]):
            special[first+n]=quote
    chunks=[]
    for i in range(1,121):
        t=i*2000;mm,ss=divmod(t//1000,60)
        ts=f"00:{mm:02d}:{ss:02d},000"
        te=f"00:{mm:02d}:{ss:02d},700"
        chunks.append(f"{i}\n{ts} --> {te}\n"+
            special.get(i,"검증을 위한 완전히 합성된 일반 대화 내용입니다."))
    raw="\n\n".join(chunks).encode("utf-8")
    manifest=make_manifest(raw,cut=120)
    source=verify_source(raw,manifest,
        expected_source_sha256=sha256(raw),
        expected_manifest_sha256=json_digest(manifest))
    atoms=copy.deepcopy(pilot.atoms)
    verdicts=copy.deepcopy(pilot.legacy)
    for cid,a in atoms.items():
        if cid in pos:
            i=pos[cid]; texts=TEXTS[cid]
            a.update(kind=OPEN_CLAIMS[cid]["kind"],
                     stance=OPEN_CLAIMS[cid]["stance"],
                     context_cue_indices=list(range(i,i+len(texts))),
                     source_refs=[
                         {"cue_index":j,"quote":quote}
                         for j,quote in zip(range(i,i+len(texts)),texts)],
                     speaker="UNKNOWN")
        else:
            ids=a["context_cue_indices"]
            a["source_refs"]=[
                {"cue_index":i,"quote":source.cues[i-1].text} for i in ids]
        verdicts[cid]["atom_sha256"]=json_digest(a)
    rows=copy.deepcopy(pilot.rows)
    for row in rows:
        cid=row["claim_id"]
        row["source_sha256"]=source.source_sha256
        row["atom_sha256"]=json_digest(atoms[cid])
        row["source_context_sha256"]=_cue_pin(source,row["source_cue_indices"])
    exchange={"source_sha256":source.source_sha256,
              "manifest_sha256":source.manifest_sha256,
              "atoms":list(atoms.values())}
    review={
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "atom_verdicts":list(verdicts.values()),
        "source_cues":[{
            "cue_index":i,
            "cue_text_sha256":sha256(source.cues[i-1].text.encode("utf-8")),
            "status":"REVIEWED"} for i in range(1,121)],
    }
    docs=[]
    for cid in sorted(DOCUMENT_IDS):
        docs.append(assess_open_partial_claim(
            source,atoms[cid],verdicts[cid],
            original_body=BODY[cid],
            review_note=NOTE,
            review_note_sha256=sha256(NOTE.encode("utf-8")),
            evidence_source_role=OPEN_CLAIMS[cid]["role"],
            body_origin_verified=True))
    return source,exchange,review,rows,docs


class V166E4AllEightNativeOpenReconciledTests(unittest.TestCase):
    def setUp(self):
        self.source,self.exchange,self.review,self.typed,self.docs=(
            synthetic_full_owner_case())

    def check(self):
        return audit_b0001_eight_open(
            self.source,self.exchange,self.review,self.typed,self.docs)

    def test_01_five_v164_and_three_e4_same_video_explicit_eight_hold(self):
        r=self.check()
        self.assertEqual(r["native_open_claims"],8)
        self.assertEqual(r["b0001_atom_census"],16)
        self.assertEqual(r["b0001_cues_reviewed"],120)
        self.assertEqual(set(r["source_only_v164_previously_reviewed_claim_ids"]),TYPED_IDS)
        self.assertEqual(set(r["documentary_partial_e4_claim_ids"]),DOCUMENT_IDS)
        self.assertEqual(set(r["all_open_claim_ids"]),EXPECTED_OPEN)
        self.assertEqual(r["native_accepted_claims"],7)
        self.assertEqual(r["native_excluded_claims"],1)
        self.assertEqual(r["approved_open_claims_newly_added"],0)
        self.assertFalse(r["full_v123_video_pass"])
        self.assertEqual(r["v128_real_owner_approved_knowledge_published"],0)

    def test_02_missing_source_only_prior_v164_row_blocked(self):
        self.typed.pop()
        with self.assertRaisesRegex(InvalidInput,"V164_FIVE_SOURCE_ONLY_CENSUS"):
            self.check()

    def test_03_missing_documentary_claim_or_duplicate_receipt_blocked(self):
        self.docs.pop()
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            self.check()
        self.setUp()
        self.docs[0]=copy.deepcopy(self.docs[1])
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            self.check()

    def test_04_changed_native_v123_open_to_accept_refused(self):
        x=next(r for r in self.review["atom_verdicts"]
               if r["claim_id"]=="C00277")
        x["status"]="ACCEPT_FOR_RESEARCH"
        with self.assertRaisesRegex(InvalidInput,"FROZEN_V123_7_ACCEPT_8_OPEN"):
            self.check()

    def test_05_pretend_only_three_are_open_is_wrong_census(self):
        for r in self.review["atom_verdicts"]:
            if r["claim_id"] in TYPED_IDS:
                r["status"]="EXCLUDE_FROM_RESEARCH"
        with self.assertRaisesRegex(InvalidInput,"FROZEN_V123_7_ACCEPT_8_OPEN"):
            self.check()

    def test_06_any_source_original_cue_review_hash_drift_blocks(self):
        self.review["source_cues"][89]["cue_text_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"REVIEWED_CUE_NOT_SOURCE_BYTE"):
            self.check()

    def test_07_existing_v164_five_source_note_pin_drift_blocks(self):
        self.typed[0]["chat_meaning_analysis_sha256"]="f"*64
        with self.assertRaises(InvalidInput):
            self.check()

    def test_08_documentary_partial_unsupported_component_flag_refused(self):
        self.docs[0]["whole_original_claim_supported"]=True
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            self.check()

    def test_09_cross_atom_book_speech_anchor_replayed_as_other_cue(self):
        self.typed[0]["verbatim_anchor_cue_index"]=30
        self.typed[0]["verbatim_anchor"]=TEXTS["C00002"][0]
        with self.assertRaisesRegex(InvalidInput,"SOURCE_ONLY_ANCHOR_BORROWED"):
            self.check()

    def test_10_wrong_native_v123_atom_digest_cannot_relabel(self):
        self.review["atom_verdicts"][0]["atom_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"ANY_ATOM_V123_DIGEST_MISMATCH"):
            self.check()

    def test_11_unreviewed_cue_cannot_pass_full_census(self):
        self.review["source_cues"][0]["status"]="OPEN"
        with self.assertRaisesRegex(InvalidInput,"REVIEWED_CUE_NOT_SOURCE_BYTE"):
            self.check()

    def test_12_passing_partial_three_cannot_be_a_full_gate(self):
        receipt=self.check()
        self.assertEqual(receipt["e4_status"],
                         "HOLD_ALL_EIGHT_NATIVE_OPEN_RECONCILED")
        self.assertFalse(receipt["e5_authorized"])
        self.assertFalse(receipt["personal_advice_approved"])
        self.assertFalse(receipt["speaker_original_audio_authenticated"])


if __name__=="__main__":
    unittest.main()
