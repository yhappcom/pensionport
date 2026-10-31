#!/usr/bin/env python3
"""V3.4 synthetic adversarial integration tests + read-only 4,120 corpus census.

SYNTHETIC results MUST NOT be represented as unseen finance retrieval scores.
"""
from __future__ import annotations
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from v30_verified_core import sha256
from v30_v34_atomic_semantics import make_draft, attach_frames, validate_draft, infer_frame
from v30_v34_retrieval import make_record, index_records, retrieve, relation_triage, features
from v30_v34_pipeline import read_historical, historical_index, run_development, private_export

ROOT=Path(__file__).resolve().parents[1]
VIDEO="abcdefghijk"
H1="lmnopqrstuv"
H2="wxyzABCDEF0"
H3="QWERTYUIOPA"

def fixture(lines):
    blocks=[]
    for k,text in enumerate(lines,1):
        minute=(k-1)//60
        second=(k-1)%60
        blocks.append(f"{k}\n00:{minute:02d}:{second:02d},000 --> 00:{minute:02d}:{second:02d},900\n{text}")
    raw=("\n\n".join(blocks)+"\n").encode("utf-8")
    return raw,sha256(raw)

def expect_fail(label,fun):
    try:fun()
    except (ValueError,TypeError,KeyError):return label
    raise AssertionError("EXPECTED_FAIL_"+label)

def history(id,text,n=19):
    return {"claim_id":id,"roster_no":n,"video_id":id[:11],
            "source_srt_sha":sha256(id.encode()),
            "source_canonical_sha":"a"*40,"source_pilot_sha":"b"*40,
            "text":text,"original_verdict":"QUALIFIED"}

def sample_index():
    return index_records([
        {"claim_id":H1+"-01","text":"IRP 납입금은 세액공제 조건을 확인해야 합니다.","video_number":20,
         "source_sha256":sha256(b"h1")},
        {"claim_id":H1+"-02","text":"IRP 연금수령 때 적용되는 소득세를 확인합니다.","video_number":20,
         "source_sha256":sha256(b"h1")},
        {"claim_id":H2+"-01","text":"ETF 추적오차는 지수와의 차이를 의미합니다.","video_number":20,
         "source_sha256":sha256(b"h2")},
        {"claim_id":H2+"-02","text":"ETF의 NAV 괴리율은 시장가격과 다릅니다.","video_number":20,
         "source_sha256":sha256(b"h2")},
        {"claim_id":H3+"-01","text":"한국은행 기준금리는 3%라고 가정합니다.","video_number":20,
         "source_sha256":sha256(b"h3")},
        {"claim_id":H3+"-02","text":"예금금리 3%를 받는다는 가정입니다.","video_number":20,
         "source_sha256":sha256(b"h3")},
    ])

def test_atomic_source_and_semantics():
    lines=[
        "IRP의 납입금은 세액공제 대상입니다. 연금을 수령할 때에는 세금이 달라집니다.",
        "ETF 추적오차와 NAV 괴리율은 다른 개념입니다.",
        "월 30만원을 납입하면 10년 뒤 7% 수익률을 가정할 수 있습니다.",
        "매수하지 않는 경우에도 위험은 있습니다.",
        "[음악]",
    ]
    raw,hash_=fixture(lines)
    draft=make_draft(raw,hash_,VIDEO)
    assert draft["source_cue_count"]==5
    assert len(draft["claims"])>=6
    assert set(c["cue_index"] for c in draft["cues"])==set(range(1,6))
    assert draft["cues"][0]["claim_ids"] and draft["cues"][4]["claim_ids"]
    assert validate_draft(draft,raw,hash_) is True
    frames=attach_frames(draft)
    assert len(frames["frames"])==len(draft["claims"])
    assert frames["unreviewed_frames"]==len(draft["claims"])
    assert frames["human_semantic_accuracy_proven"] is False
    values=[v for f in frames["frames"] for v in f["measurements"]]
    assert any(x["normalized_value"]=="300000" and x["unit"]=="만원" for x in values)
    assert any(x["unit"]=="%" and x["rate_basis"]=="UNRESOLVED" for x in values)
    assert any(f["modality"]=="NEGATED" for f in frames["frames"])
    assert frames["frames"][-1]["event_kind"]=="UNRESOLVED"
    assert frames["frames"][-1]["ambiguity_flags"]
    expect_fail("BAD_SOURCE_HASH",lambda:make_draft(raw,"a"*64,VIDEO))
    expect_fail("BAD_VIDEO_ID",lambda:make_draft(raw,hash_,"x"))
    tampered=json.loads(json.dumps(draft,ensure_ascii=False))
    tampered["claims"][0]["source_quote"]="위조된 세액공제 발언"
    expect_fail("FORGED_QUOTE",lambda:validate_draft(tampered,raw,hash_))
    tampered=json.loads(json.dumps(draft,ensure_ascii=False))
    tampered["cues"][0]["claim_ids"]=[]
    expect_fail("CUE_OMISSION",lambda:validate_draft(tampered,raw,hash_))
    tampered=json.loads(json.dumps(draft,ensure_ascii=False))
    tampered["all_semantic_statements_independently_extracted"]=True
    expect_fail("FALSE_REVIEW_ASSERTION",lambda:validate_draft(tampered,raw,hash_))
    return raw,hash_,draft,frames

def test_relation_search():
    corpus=sample_index()
    a=make_record(VIDEO+"-A00001","IRP 납입한 금액의 세액공제를 확인합니다.",
                  19,sha256(b"a"))
    out=retrieve(a,corpus,top_k=4,audit_count=2)
    assert out["index_claim_count"]==6
    assert out["hits"][0]["claim_id"]==H1+"-01",out["hits"]
    assert out["blind_recall_at_k"] is None
    assert len(out["noncandidate_audit_ids"])==2
    assert not out["automatic_knowledge_merge"]
    b=next(r for r in corpus if r["claim_id"]==H1+"-02")
    triage=relation_triage(a,b)
    assert triage["relation_type"]=="SHARED_PRODUCT_DIFFERENT_EVENT_REVIEW"
    e=make_record(VIDEO+"-A00002","ETF의 추적오차를 확인합니다.",
                  19,sha256(b"a"))
    eo=retrieve(e,corpus,top_k=2)
    assert eo["hits"][0]["claim_id"]==H2+"-01",eo["hits"]
    neg=make_record(VIDEO+"-A00003","ETF 추적오차는 존재하지 않습니다.",
                    19,sha256(b"a"))
    tr=relation_triage(neg,next(r for r in corpus if r["claim_id"]==H2+"-01"))
    assert tr["relation_type"]=="POSSIBLE_NEGATION_CONFLICT_REVIEW"
    rev=retrieve(a,tuple(reversed(corpus)),top_k=4)
    assert [x["claim_id"] for x in out["hits"]]==[x["claim_id"] for x in rev["hits"]]
    expect_fail("HOLDOUT_DATA_LEAK",lambda:index_records([
        {"claim_id":VIDEO+"-01","text":"새로운 평가용 자료",
         "video_number":269,"source_sha256":sha256(b"secret")}]))
    expect_fail("EMBEDDING_WITHOUT_HASH",lambda:make_record(
        VIDEO+"-A00004","IRP 투자",19,sha256(b"a"),embedding=[0.1,0.9]))
    expect_fail("INVALID_GRAPH_ASSERTION",lambda:retrieve(
        a,corpus,reviewed_graph_edges=[
            {"left":H1+"-01","right":H1+"-02","review_status":"UNREVIEWED"}]))
    # A controlled, versioned embedding has to be identical on both sides.
    pinned=sha256(b"model-v1")
    v=make_record(VIDEO+"-A00005","연금저축",19,sha256(b"a"),
                  embedding=[1,0],embedding_model_sha256=pinned)
    expect_fail("EMBEDDING_DIMENSION_OR_COVERAGE",lambda:retrieve(v,corpus))
    return True

def test_integrated_and_scale():
    corpus=[history(H1+"-01","IRP 납입금 세액공제"),
            history(H2+"-01","ETF 추적오차")]
    raw,digest=fixture(["IRP 납입금 세액공제를 검토합니다.",
                        "ETF 추적오차가 커질 수 있습니다. 분배금은 별도입니다."])
    output=run_development(raw,digest,VIDEO,19,corpus,synthetic_fixture=True)
    assert output["index"]["all_atomic_queries_processed"] is True
    assert output["index"]["historical_claims"]==2
    assert len(output["relations"])==output["atomic"]["proposed_claim_count"]
    assert output["metrics"]["independent_blind_recall"] is None
    with tempfile.TemporaryDirectory() as folder:
        dest=Path(folder)/"v34_test_private.json"
        summary=private_export(dest,ROOT,output)
        assert summary["private_output_created"] and dest.exists()
        assert stat.S_IMODE(dest.stat().st_mode)==0o600
        expect_fail("PRIVATE_FILE_OVERWRITE",lambda:private_export(dest,ROOT,output))
        expect_fail("PUBLIC_REPO_WRITE",lambda:private_export(ROOT/"forbidden.json",ROOT,output))
    partial=run_development(raw,digest,VIDEO,19,corpus,query_limit=1,
                            synthetic_fixture=True)
    assert partial["index"]["all_atomic_queries_processed"] is False
    expect_fail("FUTURE_HOLDOUT_DEVELOPMENT",lambda:run_development(
        raw,digest,VIDEO,269,corpus,synthetic_fixture=True))
    # V3.3's 80-atom census restriction is not inherited by V3.4 pipelines.
    large,d=fixture(["연금저축 납입 금액이 증가할 수 있습니다."]*121)
    big=run_development(large,d,VIDEO,19,corpus,query_limit=1,
                        synthetic_fixture=True)
    assert big["atomic"]["proposed_claim_count"]==121
    assert big["semantics"]["total_proposals"]==121
    assert big["index"]["all_atomic_queries_processed"] is False

def test_history_census():
    rows=read_historical(ROOT)
    idx=historical_index(rows)
    assert len(idx)==4120
    assert sum(x["source_srt_sha256"] is None for x in idx)==55
    assert len([x for x in idx if x["claim_id"].startswith("71-PUBLIC-")])==13
    assert sum(x["provenance_state"]=="HISTORIC_ORIGINAL_SHA_MISSING"
               for x in idx)==38
    assert sum(x["provenance_state"]=="HISTORIC_ORIGINAL_SHA_MALFORMED"
               for x in idx)==17
    assert all(x["provenance_state"]!="ORIGINAL_SHA_VERIFIED"
               for x in idx if x["source_srt_sha256"] is None)
    # Unknown original SHA is never replaced by a synthetic "verified" SHA.
    sampled=next(x for x in idx if x["claim_id"]=="71-PUBLIC-01")
    assert sampled["source_srt_sha256"] is None
    assert sampled["source_record_digest"]!=sampled["source_srt_sha256"]
    assert len(retrieve(idx[0],idx,top_k=3)["hits"])==3

if __name__=="__main__":
    test_atomic_source_and_semantics()
    test_relation_search()
    test_integrated_and_scale()
    test_history_census()
    print(json.dumps({
        "schema":"V34_SYNTHETIC_ADVERSARIAL_AND_HISTORY_CENSUS_TEST_V1",
        "tests":"PASS", "historical_claim_count":4120,
        "legacy_unusable_original_sha_count":55,
        "legacy_absent_original_sha_count":38,
        "legacy_malformed_original_sha_count":17,
        "legacy_noncanonical_public_71_ids":13,
        "large_synthetic_cue_census":121,
        "source_reviewer_human_confirmed":False,
        "actual_unseen_recall":None,"actual_unseen_precision":None,
        "release":"BLOCKED"
    },sort_keys=True))
