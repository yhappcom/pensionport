"""Original synthetic cases: no historical research conclusions are test fixtures."""
from __future__ import annotations
import copy
import hashlib
import json
import stat
import tempfile
import unittest
from pathlib import Path

from ire.source import parse_srt,source_record,discourse_windows,sha256
from ire.claims import validate_annotations,obligations
from ire.retrieval import related_proposals
from ire.research import inspect_document_bytes,compound_lump_sum
from ire.cli import run,write_new_private_report,REPOSITORY

VID="AaBbCcDdE12"
def synthetic_srt():
    texts=[
        "상품 비용은",
        "계약 조건에 따라 달라질 수 있습니다.",
        "연간 수수료 0.3%는 예시입니다.",
        "자세한 사항은 약관을 직접 확인해야 합니다."
    ]
    blocks=[]
    for n,t in enumerate(texts,1):
        blocks.append(f"{n}\n00:00:{(n-1)*2:02d},000 --> 00:00:{(n-1)*2+1:02d},500\n{t}")
    raw=("\n\n".join(blocks)+"\n").encode("utf-8")
    return raw,sha256(raw)

def empty_frame(**changes):
    model={
        "subject":None,"product":None,"financial_event":None,
        "action":None,"object":None,"jurisdiction":None,
        "effective_date":None,"conditions":[],"exceptions":[],
        "measurements":[],"modality":"UNRESOLVED"
    }
    model.update(changes)
    return model

def annotations(digest):
    return {
        "schema":"IRE_PROPOSALS_V1",
        "video_id":VID,
        "source_sha256":digest,
        "generator":{
            "origin":"EXTERNAL_UNVERIFIED",
            "model_sha256":sha256(b"synthetic-model-v0"),
            "prompt_sha256":sha256(b"synthetic-prompt-v0")},
        "claims":[
            {"claim_id":"C00001",
             "proposition":"해당 상품의 비용이 계약 조건에 따라 달라질 수 있다.",
             "claim_types":["PRODUCT","MECHANISM"],
             "frame":empty_frame(product="가상의 상품 A",
                 financial_event="계약 비용",action="조건부 변경",
                 conditions=["계약 조건"],modality="CONDITIONAL"),
             "source_refs":[{"cue_index":1,"quote":"상품 비용은"},
                            {"cue_index":2,"quote":"계약 조건에 따라 달라질 수 있습니다."}],
             "annotation_status":"UNREVIEWED"},
            {"claim_id":"C00002",
             "proposition":"연간 0.3% 수수료는 확정치가 아니라 예시다.",
             "claim_types":["NUMERIC"],
             "frame":empty_frame(product="가상의 상품 A",
                 financial_event="계약 비용",action="예시 제시",
                 modality="HYPOTHESIS",
                 measurements=[{"value_text":"0.3%","unit":"%",
                     "measure_kind":"연간 수수료율","reference_cue":3}]),
             "source_refs":[{"cue_index":3,"quote":"연간 수수료 0.3%는 예시입니다."}],
             "annotation_status":"UNREVIEWED"}
        ],
        "cue_dispositions":[
            {"cue_index":1,"status":"LINKED","claim_ids":["C00001"],"reason":None},
            {"cue_index":2,"status":"LINKED","claim_ids":["C00001"],"reason":None},
            {"cue_index":3,"status":"LINKED","claim_ids":["C00002"],"reason":None},
            {"cue_index":4,"status":"NONCLAIM_CANDIDATE",
             "claim_ids":[],"reason":"일반적인 자료 확인 권유 표현으로 판단한 미확정 분류"}
        ]
    }


class IndependentEngineTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.digest=synthetic_srt()
        self.a=annotations(self.digest)

    def assertRejected(self,fn,code=None):
        with self.assertRaises(ValueError) as cx:fn()
        if code:self.assertIn(code,str(cx.exception))

    def test_input_hash_and_cue_integrity(self):
        cues=parse_srt(self.raw,self.digest)
        self.assertEqual(len(cues),4)
        self.assertEqual([c.index for c in cues],[1,2,3,4])
        self.assertRejected(lambda:parse_srt(self.raw,sha256(b"wrong")),
                            "SOURCE_SHA256_MISMATCH")
        self.assertRejected(lambda:parse_srt(self.raw.replace(b"4\n00",b"3\n00"),sha256(self.raw.replace(b"4\n00",b"3\n00"))),
                            "CUE_NUMBER_GAP_OR_DUPLICATE")

    def test_discourse_context_is_not_atomic(self):
        cues=parse_srt(self.raw,self.digest)
        groups=discourse_windows(cues,max_cues=2,pause_ms=3000)
        self.assertEqual([x["source_cue_ids"] for x in groups],[[1,2],[3,4]])
        self.assertEqual(groups[0]["right_context_cue_ids"],[3,4])
        self.assertEqual(groups[1]["left_context_cue_ids"],[1,2])
        self.assertTrue(all(x["semantic_interpretation"]=="NOT_PERFORMED"
                            for x in groups))
        self.assertFalse(source_record(self.raw,VID,self.digest)["claims_extracted"])

    def test_cross_cue_semantic_claim_is_traceable_but_unreviewed(self):
        report=validate_annotations(self.raw,self.digest,VID,self.a)
        self.assertEqual(report["proposed_atomic_claims"],2)
        self.assertEqual(report["linked_cues"],3)
        self.assertEqual(report["unresolved_cues"],0)
        self.assertFalse(report["semantic_accuracy_certified"])
        self.assertFalse(report["research_complete"])
        self.assertIn("INDEPENDENT_DECIMAL_FORMULA_INPUT_AND_UNITS",
                      obligations(self.a["claims"][1]))
        self.assertIn("UNRESOLVED_EFFECTIVE_DATE",
                      obligations(self.a["claims"][0]))

    def test_source_fabrication_rejected(self):
        a=copy.deepcopy(self.a)
        a["claims"][0]["source_refs"][0]["quote"]="상품 비용이 무조건 0원입니다"
        self.assertRejected(lambda:validate_annotations(self.raw,self.digest,VID,a),
                            "UNTRACEABLE_QUOTED_SOURCE")
        a=copy.deepcopy(self.a)
        a["claims"][1]["frame"]["measurements"][0]["value_text"]="9%"
        self.assertRejected(lambda:validate_annotations(self.raw,self.digest,VID,a),
                            "NUMERIC_LITERAL_NOT_FOUND_IN_SOURCE")

    def test_omission_coverage_and_forged_approval(self):
        a=copy.deepcopy(self.a)
        a["cue_dispositions"].pop()
        self.assertRejected(lambda:validate_annotations(self.raw,self.digest,VID,a),
                            "CLAIM_OR_CUE_CENSUS_INVALID")
        a=copy.deepcopy(self.a)
        a["cue_dispositions"][1]["claim_ids"]=[]
        self.assertRejected(lambda:validate_annotations(self.raw,self.digest,VID,a),
                            "SOURCE_CUE_REVERSE_CLAIM_LINK_MISMATCH")
        a=copy.deepcopy(self.a)
        a["claims"][0]["annotation_status"]="APPROVED"
        self.assertRejected(lambda:validate_annotations(self.raw,self.digest,VID,a),
                            "ANNOTATOR_MAY_NOT_APPROVE")

    def test_cue_unresolved_preserved(self):
        a=copy.deepcopy(self.a)
        a["cue_dispositions"][3]={
            "cue_index":4,"status":"UNRESOLVED","claim_ids":[],
            "reason":"Meaning unclear without speech"}
        r=validate_annotations(self.raw,self.digest,VID,a)
        self.assertEqual(r["unresolved_cue_ids"],[4])
        self.assertFalse(r["research_complete"])

    def test_new_corpus_only_candidate_search(self):
        r=related_proposals(self.a,top_k=2,audit_count=1)
        self.assertFalse(r["external_legacy_corpus_loaded"])
        self.assertEqual(r["claim_count"],2)
        self.assertEqual(r["queries"][0]["hits"][0]["claim_id"],"C00002")
        self.assertFalse(r["queries"][0]["hits"][0]["relation_verified"])
        self.assertIsNone(r["recall_at_k"])

    def test_offline_document_is_not_official_certification(self):
        data="가상 금융상품 A 약관 설명: 조건부 수수료가 적용될 수 있습니다.".encode()
        digest=sha256(data)
        e=inspect_document_bytes(data,digest,
              "https://example.org/mock-document",
              "조건부 수수료가 적용될 수 있습니다.")
        self.assertTrue(e["source_bytes_match"])
        self.assertFalse(e["publisher_identity_verified"])
        self.assertFalse(e["claim_truth_approved"])
        self.assertRejected(lambda:inspect_document_bytes(data,digest,
              "http://example.org/mock","조건부 수수료가 적용될 수 있습니다."),
              "EVIDENCE_CANONICAL_HTTPS_LOCATOR_REQUIRED")

    def test_exact_financial_arithmetic_not_fact(self):
        a=compound_lump_sum("100","0.05",2)
        self.assertEqual(a["gross_future_value"],"110.2500")
        self.assertFalse(a["financial_fact_verified"])
        self.assertRejected(lambda:compound_lump_sum("100", "NaN",2),
                            "NONFINITE_CALCULATION")

    def test_integrated_source_only_and_private_io(self):
        draft=run(self.raw,self.digest,VID)
        self.assertTrue(draft["source_only_analysis"])
        self.assertEqual(draft["source"]["cue_count"],4)
        self.assertEqual(draft["approved_claims"],0)
        interpreted=run(self.raw,self.digest,VID,self.a)
        self.assertEqual(interpreted["annotation_result"]["proposed_atomic_claims"],2)
        self.assertEqual(len(interpreted["research_worklist"]["claims"]),2)
        self.assertFalse(interpreted["previous_research_cited"])
        self.assertTrue(interpreted["production_release"].startswith("BLOCKED_"))
        with tempfile.TemporaryDirectory() as home:
            path=str(Path(home)/"private.json")
            write_new_private_report(path,interpreted)
            self.assertEqual(stat.S_IMODE(Path(path).stat().st_mode),0o600)
            self.assertRejected(lambda:write_new_private_report(path,interpreted),
                                "PRIVATE_REPORT_OVERWRITE_FORBIDDEN")
            self.assertRejected(lambda:write_new_private_report(
                str(REPOSITORY/"prohibited.json"),interpreted),
                "PRIVATE_FILE_MUST_NOT_BE_STORED_INSIDE_GIT_REPOSITORY")

if __name__=="__main__":
    unittest.main()
