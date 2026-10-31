#!/usr/bin/env python3
"""V3.0 end-to-end development regression and red-team, no unseen #21+ read.

Every source, "official" page and observed price in this test is an invented
unit-test fixture. A passing test never certifies a real public financial fact.
"""
import copy
import hashlib
import hmac
import json
import shutil
import tempfile
from datetime import date,timedelta
from pathlib import Path

from v30_verified_core import (
    TRUST_PINS,policy_gate,parse_srt,verify_ledger,frame_check,
    evidence_requirements,sha256,canonical,check_privacy,
    bind_reviewed_claim,verify_bound_claim,typed_relation,decimal,
    verify_attestation,guard,
)
from v30_evidence_services import (
    review_primary_evidence,math_reproduce,empirical_reproduce,
    safe_public_url,
)
from v30_hybrid_search import make_index,search,build_development_history
from v30_claim_extraction import propose_atomic_draft
from v30_state_machine import ResearchState
from v30_independent_evaluator import evaluate,wilson
from v30_research_pipeline import (
    scan_source_state,research_run,authority_registry_from_environment,
    v5_append_only_preview,complete_with_preexisting_v5_certificate,
)

from v30_v5_bridge import blocked_v5_package,pending_knowledge_proposal
import os

ROOT=Path(__file__).resolve().parents[1]

def fail(fn,label):
    try:fn()
    except (ValueError,TypeError,KeyError,IndexError,OSError):
        return
    raise ValueError("FAILED_TO_REJECT_"+label)

def mac(authority,role,payload):
    a=authority[role]
    return {"role":role,"reviewer_id":a["reviewer_id"],
            "mac":hmac.new(a["secret"],canonical(payload),hashlib.sha256).hexdigest()}

def frame(role,action,value,period="ANNUAL"):
    return {
        "subject_type":"EDUCATIONAL_FINANCIAL_EXAMPLE",
        "subject_id":"PUBLIC_SYNTHETIC_EXAMPLE",
        "action":action,
        "object_type":"CLAIMED_VALUE",
        "object_id":"AMOUNT",
        "financial_role":role,
        "jurisdiction":"KR",
        "effective_date":"2026-01-01",
        "conditions":{"hypothetical_or_explanation":"EDUCATIONAL_ONLY"},
        "units":"KRW","value":value,"period":period,
    }

def synthetic():
    video="DEMO0000001"
    data=("1\n00:00:00,000 --> 00:00:03,000\n"
          "ISA 만기 연금계좌 이전 시 추가 공제상한은 300만원입니다.\n\n"
          "2\n00:00:03,100 --> 00:00:05,200\n"
          "안녕하세요 여러분.\n\n"
          "3\n00:00:05,300 --> 00:00:11,300\n"
          "월 60만원을 연 4%로 25년 적립하면 약 3억원이 됩니다.\n").encode()
    tax={
      "claim_id":video+"-01","cue_indices":[1],
      "quote":"ISA 만기 연금계좌 이전 시 추가 공제상한은 300만원입니다.",
      "legacy_verdict":"QUALIFIED","material":True,
      "claim_types":["LEGAL_OR_PRODUCT","NUMERIC"],
      "frame":frame("ISA_TRANSFER_TAX_CREDIT","TAX","3000000","ANNUAL"),
      "topic_families":["ISA_PENSION_TRANSFER"]
    }
    future={
      "claim_id":video+"-02","cue_indices":[3],
      "quote":"월 60만원을 연 4%로 25년 적립하면 약 3억원이 됩니다.",
      "legacy_verdict":"HYPOTHETICAL","material":True,
      "claim_types":["NUMERIC"],
      "frame":frame("MATHEMATICAL_COMPOUND_GROWTH","COMPUTE",
                    "308477728","25_YEARS"),
      "topic_families":["RETIREMENT_PORTFOLIO"]
    }
    ledger={
      "schema":"V30_ATOMIC_LEDGER_V2",
      "cues":[
        {"cue_index":1,"classification":"MATERIAL",
         "claim_ids":[tax["claim_id"]]},
        {"cue_index":2,"classification":"NON_MATERIAL",
         "claim_ids":[],"nonmaterial_reason":"Intro and greetings only"},
        {"cue_index":3,"classification":"MATERIAL",
         "claim_ids":[future["claim_id"]]}
      ],
      "claims":[tax,future]
    }
    binding={
        "video_id":video,"video_number":19,
        "srt_sha256":sha256(data),"cue_count":3,
        "ledger_sha256":sha256(canonical(ledger)),
        "claim_digests":{x["claim_id"]:sha256(canonical(x)) for x in ledger["claims"]}
    }
    manifest={
      "schema":"V30_FULL_SOURCE_MANIFEST_V1",
      "test_fixture":True,
      "video_id":video,"video_number":19,
      "srt_sha256":binding["srt_sha256"],
      "original_cue_count":3,
      "legacy_verdicts":{x["claim_id"]:x["legacy_verdict"] for x in ledger["claims"]}
    }
    authorities={
      "source_reviewer":{"reviewer_id":"SYNTHETIC_REVIEWER_ONE",
                         "secret":b"s"*32,"test_fixture":False},
      "independent_reviewer":{"reviewer_id":"SYNTHETIC_REVIEWER_TWO",
                              "secret":b"i"*32,"test_fixture":False},
      "numeric_auditor":{"reviewer_id":"SYNTHETIC_NUMERIC",
                         "secret":b"m"*32,"test_fixture":False},
      "primary_auditor":{"reviewer_id":"SYNTHETIC_PRIMARY",
                         "secret":b"p"*32,"test_fixture":False},
      "empirical_auditor":{"reviewer_id":"SYNTHETIC_DATA",
                           "secret":b"d"*32,"test_fixture":False},
    }
    manifest["source_review_attestation"]=mac(authorities,"source_reviewer",binding)
    return data,ledger,binding,manifest,authorities

def run(root=ROOT):
    root=Path(root)
    policy_gate(root)
    cases=0
    # P0: editing manifest or weakening an unrelated critical invariant must fail
    # even when the new hash list itself is removed.
    with tempfile.TemporaryDirectory(prefix="v30_gate_audit_") as d:
        tmp=Path(d)
        for relative in TRUST_PINS:
            source=root/relative;target=tmp/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        for relative in ("v30/contracts/integrated_engine_v1.json",
                         "v30/contracts/evaluation_protocol_v1.json"):
            source=root/relative;target=tmp/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        policy_gate(tmp)
        p=tmp/"v30/contracts/integrated_engine_v1.json"
        j=json.loads(p.read_text());j["frozen_existing_policy_files"]={}
        p.write_text(json.dumps(j))
        fail(lambda:policy_gate(tmp),"EDITABLE_SOURCE_HASH_MANIFEST")
        cases+=1
        j=json.loads((root/"v30/contracts/integrated_engine_v1.json").read_text())
        j["hard_safety"]["automatic_research_completion_certificate"]=True
        p.write_text(json.dumps(j))
        fail(lambda:policy_gate(tmp),"AUTO_RESEARCH_COMPLETE_UNBLOCKED")
        cases+=1
        j=json.loads((root/"v30/contracts/integrated_engine_v1.json").read_text())
        j["relation_output"]["claim_truth_inferred_from_similarity"]=True
        p.write_text(json.dumps(j))
        fail(lambda:policy_gate(tmp),"AUTO_SEMANTIC_TRUTH_FROM_SIMILARITY")
        cases+=1

    data,ledger,binding,manifest,authority=synthetic()
    cues=parse_srt(data,binding["srt_sha256"])
    guard(len(cues)==3,"FULL_SUBTITLE_PARSER_DID_NOT_CONSUME_ALL_CUES")
    c=verify_ledger(cues,ledger,manifest["video_id"],manifest["legacy_verdicts"])
    guard(c["missing_or_unmapped_cues"]==0 and
          c["mapped_material_cues"]==2 and
          c["justified_nonmaterial_cues"]==1 and
          c["source_material_statement_completeness_audited_by_human"] is False,
          "NONMATERIAL_AND_ATOMIC_CUE_ACCOUNTING")
    cases+=1
    draft=propose_atomic_draft(cues,manifest["video_id"])
    guard(draft["total_source_cues"]==3
          and draft["generated_atomic_proposals"]==3
          and draft["human_approved_claims"]==0
          and not draft["completed_full_statement_coverage"]
          and all(x["review_status"]=="UNREVIEWED" for x in draft["proposals"]),
          "FULL_SRT_ATOMIC_EXTRACTION_MUST_REQUIRE_INDEPENDENT_REVIEW")
    guard(draft["proposals"][0]["proposed_atomic_id"]==
          "DEMO0000001-A00001","LONG_ATOMIC_ID_NOT_SUPPORTED")
    cases+=1
    bad=copy.deepcopy(ledger);bad["cues"].pop()
    fail(lambda:verify_ledger(cues,bad,manifest["video_id"]),
         "DROPPED_LAST_SOURCE_CUE")
    bad=copy.deepcopy(ledger);bad["cues"][0]["claim_ids"]=[]
    fail(lambda:verify_ledger(cues,bad,manifest["video_id"]),
         "MATERIAL_CUE_WITHOUT_ATOMIC_LINK")
    bad=copy.deepcopy(ledger);bad["claims"][0]["quote"]="not original text"
    fail(lambda:verify_ledger(cues,bad,manifest["video_id"]),
         "FABRICATED_ATOMIC_ORIGINAL_QUOTE")
    bad=copy.deepcopy(ledger);bad["claims"][0]["legacy_verdict"]="CONTRADICTED"
    fail(lambda:verify_ledger(cues,bad,manifest["video_id"],
                              manifest["legacy_verdicts"]),
         "SOURCE_LEGACY_VERDICT_SPOOF")
    fail(lambda:parse_srt(data,binding["srt_sha256"].replace("0","1")),
         "BAD_SOURCE_FINGERPRINT")
    cases+=5

    old_guard=scan_source_state(root,manifest,data,ledger,authority)
    guard(old_guard["source_reviewer_authenticated"] and
          old_guard["binding"]==binding and
          old_guard["source_digest_checked_from_actual_bytes"],
          "SIGNED_FULL_SOURCE_REVIEW_NOT_BOUND")
    cases+=1
    untrusted_video=copy.deepcopy(manifest)
    untrusted_video["test_fixture"]=False
    fail(lambda:scan_source_state(root,untrusted_video,data,ledger,authority),
         "NONEXISTENT_VIDEO_WITH_FALSIFIED_REAL_SOURCE")
    cases+=1
    bad=copy.deepcopy(manifest)
    bad["source_review_attestation"]["mac"]="0"*64
    fail(lambda:scan_source_state(root,bad,data,ledger,authority),
         "INVALID_SOURCE_REVIEWER_SIGNATURE")
    cases+=1
    bound=bind_reviewed_claim(
        ledger["claims"][0],binding,manifest["source_review_attestation"],authority)
    verify_bound_claim(bound)
    claim2=bind_reviewed_claim(
        ledger["claims"][1],binding,manifest["source_review_attestation"],authority)
    r=typed_relation(bound,claim2)
    guard(r["relationship_candidate"]=="SCOPE_DIFFERENT" and
          r["source_risk"]=="UNREPLICATED_HYPOTHETICAL_SOURCE" and
          not r["automatic_merge_permitted"],
          "MIXED_HYPOTHETICAL_REVIEW_SCOPE")
    cases+=1
    forged=copy.deepcopy(ledger["claims"][0]);forged["claim_id"]="DEMO0000001-55"
    fail(lambda:bind_reviewed_claim(forged,binding,
                    manifest["source_review_attestation"],authority),
         "FORGED_CLAIM_SAME_VIDEO")
    fail(lambda:typed_relation(
         {"claim_id":"DEMO0000001-01","frame":ledger["claims"][0]["frame"],
          "legacy_verdict":"PRIMARY_CONFIRMED",
          "claim_types":["NUMERIC"],
          "source_bound":True,"review_binding_checked":True},bound),
         "BARE_DICT_RELATION_V2.3_PROVENANCE_BYPASS")
    cases+=2

    numeric=copy.deepcopy(ledger["claims"][0]["frame"])
    numeric["value"]="3000000.00"
    sim=copy.deepcopy(ledger["claims"][1])
    # Same legal role and economically equal numeric values must NOT be conflicts.
    sim["frame"]=numeric
    sim["claim_types"]=["LEGAL_OR_PRODUCT","NUMERIC"]
    edited=copy.deepcopy(ledger)
    edited["claims"][1]=sim
    newbind={**binding,"ledger_sha256":sha256(canonical(edited)),
             "claim_digests":{x["claim_id"]:sha256(canonical(x))
                              for x in edited["claims"]}}
    signed=mac(authority,"source_reviewer",newbind)
    eq=bind_reviewed_claim(edited["claims"][1],newbind,signed,authority)
    original=bind_reviewed_claim(edited["claims"][0],newbind,signed,authority)
    z=typed_relation(original,eq)
    guard(z["relationship_candidate"]=="SAME_PROPOSITION_CANDIDATE" and
          not z["approved_semantic_equivalence"],
          "EQUAL_NUMERICAL_VALUES_FALSELY_REFUTED")
    cases+=1
    missing=copy.deepcopy(numeric);missing.pop("value")
    fail(lambda:frame_check(missing,["NUMERIC"]),"MISSING_NUMERIC_PAYLOAD")
    wrong_date=copy.deepcopy(numeric);wrong_date["effective_date"]="2026-99-99"
    fail(lambda:frame_check(wrong_date,["LEGAL_OR_PRODUCT"]),
         "IMPOSSIBLE_LEGAL_EFFECTIVE_DATE")
    unknown=copy.deepcopy(numeric);unknown["financial_role"]="UNKNOWN_FAKE_ROLE"
    fail(lambda:frame_check(unknown,["NUMERIC"]),
         "UNREGISTERED_FINANCIAL_ROLE")
    cases+=3

    kinds=evidence_requirements(["LEGAL_OR_PRODUCT","NUMERIC"])
    guard("INDEPENDENT_PRIMARY_OR_DOMAIN_EVIDENCE" in kinds and
          "REPRODUCED_NUMERIC_METHOD" in kinds,
          "LEGAL_WITH_NUMERIC_MUST_HAVE_BOTH_EVIDENCE_OBLIGATIONS")
    cases+=1
    math={
      "model_id":"MATH-001","claim_ids":[ledger["claims"][1]["claim_id"]],
      "model_type":"MONTHLY_SAVINGS_FUTURE_VALUE",
      "principal_or_monthly_contribution":"600000",
      "nominal_annual_rate":"0.04","months":300,
      "cashflow_timing":"END_OF_MONTH",
      "monthly_rate_convention":"NOMINAL_ANNUAL_DIVIDED_BY_12",
      "includes_fees_taxes":False,"currency":"KRW",
      "asserted_value":"308477728","asserted_tolerance":"100"
    }
    model=math_reproduce(math)
    guard(model["independent_methods_agree"] and
          model["historical_asserted_value_matches_model"] is True and
          not model["real_product_contract_validated"],
          "DOUBLE_METHOD_ANNUITY_MATH_FAIL")
    cases+=1
    bad=copy.deepcopy(math);bad["asserted_value"]="2130000";bad["asserted_tolerance"]="1"
    guard(math_reproduce(bad)["historical_asserted_value_matches_model"] is False,
          "INCORRECT_NUMERIC_QUOTE_NOT_DETECTED")
    cases+=1

    text=("Fictional public regulator example. ISA 만기 연금계좌 이전 시 "
          "추가 공제상한은 300만원입니다. Hypothetical test section 8.")
    body=("<html><body>"+text+"</body></html>").encode()
    doc={
        "source_id":"FICTIONAL-PRIMARY-001",
        "claim_ids":[ledger["claims"][0]["claim_id"]],
        "source_url":"https://www.nts.go.kr/educational-unit-test",
        "document_sha256":sha256(body),
        "mime_type":"text/html",
        "verbatim_quote":"ISA 만기 연금계좌 이전 시 추가 공제상한은 300만원입니다.",
        "exact_location":"Hypothetical unit-test paragraph 8",
        "effective_from":"2026-01-01","effective_to":"2026-12-31",
        "jurisdiction":"KR",
        "exceptions_reviewed":"Fictional exceptions only for unit tests",
        "applicability_scope":"Fictional domestic pension-transfer rule",
    }
    ev=review_primary_evidence(
        {"claim_id":ledger["claims"][0]["claim_id"],
         "claim_types":ledger["claims"][0]["claim_types"],
         "frame":ledger["claims"][0]["frame"]},
        doc,body)
    guard(ev["exact_quote_present"] and
          not ev["legal_applicability_independently_audited"],
          "OFFICIAL_BYTES_ALONE_MUST_NOT_AUTO_PROVE_SOURCE_TRUTH")
    cases+=1
    bad=copy.deepcopy(doc);bad["document_sha256"]="0"*64
    fail(lambda:review_primary_evidence(
         {"claim_id":ledger["claims"][0]["claim_id"],
          "claim_types":ledger["claims"][0]["claim_types"],
          "frame":ledger["claims"][0]["frame"]},bad,body),
         "MISMATCHED_OFFICIAL_DOCUMENT_BYTES")
    bad=copy.deepcopy(doc);bad["effective_to"]="2025-12-31"
    fail(lambda:review_primary_evidence(
         {"claim_id":ledger["claims"][0]["claim_id"],
          "claim_types":ledger["claims"][0]["claim_types"],
          "frame":ledger["claims"][0]["frame"]},bad,body),
         "OUT_OF_DATE_LEGAL_SOURCE")
    fail(lambda:safe_public_url("https://127.0.0.1/internal"),
         "PRIVATE_NETWORK_SSRF")
    cases+=3

    csvdata="date,price,benchmark_price\n"
    for i in range(30):
        dt=date(2026,1,1)+timedelta(days=i)
        csvdata+=f"{dt.isoformat()},{100+i},{100+i/2}\n"
    sample=csvdata.encode()
    metadata={
        "study_id":"FICTIONAL-EMPIRICAL-001",
        "claim_ids":[ledger["claims"][1]["claim_id"]],
        "dataset_sha256":sha256(sample),
        "real_world_data":True,"synthetic_only":False,
        "provider":"FICTIONAL_UNIT_TEST_DO_NOT_TREAT_AS_MARKET_DATA",
        "source_url":"https://www.bok.or.kr/unit-test",
        "benchmark":"FIXTURE_BENCHMARK",
        "costs_and_taxes":"Fictional cost and tax parameters",
        "bias_assessment":"Fictional example; no investment conclusion",
        "out_of_sample_definition":"last 14 observations",
        "out_of_sample_start":"2026-01-17",
        "round_trip_cost_fraction":"0.001",
        "tax_rate_on_positive_gain":"0.12",
    }
    emp=empirical_reproduce(sample,metadata)
    guard(emp["sample_count"]==30 and
          not emp["dataset_issuer_independently_authenticated"] and
          not emp["historical_market_truth_verified_by_internal_math"] and
          emp["max_drawdown"]=="0",
          "EMPIRICAL_CALCULATOR_MUST_NOT_PROVE_SOURCE_AUTHENTICITY")
    cases+=1
    bad=copy.deepcopy(metadata);bad["synthetic_only"]=True
    fail(lambda:empirical_reproduce(sample,bad),
         "EMPIRICAL_SYNTHETIC_FLAG_REJECT")
    bad=copy.deepcopy(metadata);bad["dataset_sha256"]="0"*64
    fail(lambda:empirical_reproduce(sample,bad),
         "EMPIRICAL_DATA_TAMPERING")
    cases+=2

    bank=[
        {"claim_id":"DEMO0000002-01","video_number":18,
         "text":"ISA 연금저축 만기 세액공제 세법",
         "legacy_verdict":"QUALIFIED",
         "financial_role":"ISA_TRANSFER_TAX_CREDIT",
         "topic_families":["ISA_PENSION_TRANSFER"]},
        {"claim_id":"DEMO0000002-02","video_number":18,
         "text":"채권 원금보전 이율 위험",
         "legacy_verdict":"CONTRADICTED",
         "financial_role":"BOND_DIRECT_MATURITY",
         "topic_families":["BONDS"]}
    ]
    indexed=make_index(bank)
    lookup=search({"claim_id":ledger["claims"][0]["claim_id"],
                   "text":ledger["claims"][0]["quote"],
                   "financial_role":"ISA_TRANSFER_TAX_CREDIT",
                   "topic_families":["ISA_PENSION_TRANSFER"]},
                  indexed,limit=1,audit_non_candidates=1)
    guard(lookup["review_candidates"][0]["claim_id"]=="DEMO0000002-01"
          and lookup["noncandidate_audit_sample"]==["DEMO0000002-02"]
          and lookup["candidate_recall_claimed"] is None
          and not lookup["automatic_knowledge_merge"],
          "HYBRID_SEARCH_OR_NONCANDIDATE_AUDIT_BROKEN")
    cases+=1
    vector_bank=copy.deepcopy(bank)
    vector_bank[0].update(embedding=[1.0,0.0],
                          embedding_model_sha256="b"*64)
    vector_bank[1].update(embedding=[0.0,1.0],
                          embedding_model_sha256="b"*64)
    vector_index=make_index(vector_bank)
    vector_result=search({
         "claim_id":"DEMO0000001-01",
         "text":"ISA 이전 세액공제",
         "financial_role":"ISA_TRANSFER_TAX_CREDIT",
         "topic_families":["ISA_PENSION_TRANSFER"],
         "embedding":[1.0,0.0],"embedding_model_sha256":"b"*64
    },vector_index,limit=1)
    guard("PINNED_MODEL_VECTOR_COSINE" in vector_result["search_lanes"]
          and vector_result["review_candidates"][0]["claim_id"]==
               "DEMO0000002-01"
          and not vector_result["external_embedding_model_semantic_accuracy_proven"],
          "OPTIONAL_PINNED_VECTOR_SEARCH_LANE_FAILED")
    cases+=1
    fail(lambda:search({
         "text":"ISA 이전","financial_role":"ISA_TRANSFER_TAX_CREDIT",
         "embedding":[1.0,0.0,0.0],
         "embedding_model_sha256":"b"*64
    },vector_index,limit=1),"VECTOR_DIMENSION_MISMATCH")
    cases+=1
    bad=copy.deepcopy(bank);bad[0]["video_number"]=21
    fail(lambda:make_index(bad),"POST20_CORPUS_LEAK")
    cases+=1

    blocked=research_run(root,manifest,data,ledger,search_bank=bank)
    guard(blocked["research_status"]=="RESEARCH_BLOCKED"
          and blocked["claims_processed"]==2
          and blocked["claims_with_open_blockers"]==2
          and blocked["stages"]["SOURCE_PROVENANCE"]=="BLOCKED"
          and blocked["automatic_knowledge_approvals"]==0
          and blocked["automatic_research_completion_certificates"]==0
          and blocked["source_sealed_claim_count"]==0,
          "UNATTESTED_FULL_ORIGINAL_MUST_BE_BLOCKED")
    guard(blocked["stage_journal"]["status"]=="RESEARCH_BLOCKED"
          and blocked["stage_journal"]["completed_stages"]==0,
          "UNATTESTED_SOURCE_CANNOT_PASS_STAGE_JOURNAL")
    state=ResearchState(manifest["video_id"],binding["srt_sha256"])
    fail(lambda:state.append("ATOMIC_COVERAGE","PASSED",
             proof_ids=["forged_nonexistent_evidence"]),
         "SKIP_ORIGINAL_SOURCE_STAGE")
    first=state.append("SOURCE_PROVENANCE","PASSED",
                       proof_ids=["original_source_sha256_verified"])
    guard(first.previous_digest=="GENESIS" and len(first.digest)==64,
          "BAD_EVENT_HASH_CHAIN")
    fail(lambda:state.append("SOURCE_PROVENANCE","PASSED",
                             proof_ids=["malicious_duplicate"]),
         "DOUBLE_APPROVAL_OF_STAGE")
    state.append("ATOMIC_COVERAGE","BLOCKED",
                 reason="full independent claim review is missing")
    fail(lambda:state.append("CLAIM_FRAME_AND_OBLIGATIONS","PASSED",
                             proof_ids=["forged_frame_review"]),
         "ADVANCE_AFTER_BLOCKED_STAGE")
    guard(state.preview()["status"]=="RESEARCH_BLOCKED",
          "BLOCKED_STAGE_JOURNAL_WAS_IGNORED")
    cases+=1
    signed_source=research_run(
        root,manifest,data,ledger,search_bank=bank,authorities=authority)
    guard(signed_source["stage_journal"]["status"]=="RESEARCH_BLOCKED"
          and signed_source["stage_journal"]["completed_stages"]==3,
          "SIGNED_SOURCE_MUST_ADVANCE_ONLY_THROUGH_THREE_VERIFIED_STAGES")
    guard(signed_source["source_reviewer_authenticated"]
          and signed_source["source_sealed_claim_count"]==2
          and len(signed_source["intra_video_typed_relation_candidates"])==1
          and signed_source["research_status"]=="RESEARCH_BLOCKED"
          and not signed_source["typed_relation_accuracy_independently_verified"],
          "SOURCE_SIGNED_BUT_EVIDENCE_MISSING_MUST_BLOCK")
    cases+=1
    reviewed=research_run(
        root,manifest,data,ledger,search_bank=bank,authorities=authority,
        documents=[{"metadata":doc,"bytes":body}],
        models=[math],
        empirical=[{"metadata":metadata,"bytes":sample}])
    guard(reviewed["research_status"]=="RESEARCH_BLOCKED"
          and reviewed["claims_with_open_blockers"]==2
          and reviewed["automatic_knowledge_approvals"]==0,
          "UNSIGNED_EXTERNAL_DATA_CANNOT_CERTIFY")
    cases+=1

    # Genuine V5 append-only code is wired to a pending (NEVER approved)
    # historical event, with its exact source Git blob.
    from verify_v5_knowledge_integration import read
    seed=read(root/"data/synthesis/investment_knowledge_001_260/curated_recurring_concepts_16.json")
    ev={
      "event_id":"V5-COMP-999999",
      "source_path":"data/analysis_events/zi9x_q2fYoc.json",
      "source_blob_sha":"8fbb48dbff06389f69223fdcbdc94241b960d3e4",
      "source_claim_id":"zi9x_q2fYoc-02",
      "target_concept_id":seed["concepts"][0]["concept_id"],
      "relation":"TOPIC_ONLY",
      "review_state":"PENDING_REVIEW",
      "assessment":"Candidate only, needs authentic independent financial review",
      "evidence_refs":[],"evidence_blob_shas":{},
      "blocked_reason":"Original source not independently audited in V3.0",
      "reopen_trigger":"Human reviewed actual V5 completed evidence",
      "supersedes_claim_id":None,"certificate_path":None
    }
    v5=v5_append_only_preview(root,ev,ev["source_blob_sha"])
    guard(v5["statistics"]["topic_only"]==1
          and v5["approved_overlaid_relation_count"]==0
          and v5["original_claims_overwritten"]==0,
          "V5_REAL_INTEGRATION_GATE_MUST_STAY_UNMODIFIED_AND_PENDING")
    cases+=1
    pkg=blocked_v5_package(blocked,root)
    guard(pkg["verified_by_original_v5_gate"]
          and pkg["status"]=="RESEARCH_BLOCKED"
          and pkg["certificate"]["release"]["approved"] is False
          and pkg["certificate"]["preflight"]["expected_claim_count"]==2
          and all(x["claim_type"] in ("LEGAL_OR_PRODUCT","NUMERIC")
                  for x in pkg["certificate"]["obligations"]),
          "V30_TO_V5_BLOCKED_CERTIFICATE_BRIDGE_FAILURE")
    cases+=1
    proposal=pending_knowledge_proposal(
        root,"zi9x_q2fYoc","zi9x_q2fYoc-02",
        seed["concepts"][0]["concept_id"])
    guard(proposal["preview"]["statistics"]["topic_only"]==1
          and not proposal["automatic_merge"] and
          proposal["event"]["review_state"]=="PENDING_REVIEW",
          "PENDING_APPEND_ONLY_PROPOSAL_BUILDER_FAILED")
    cases+=1
    with tempfile.TemporaryDirectory(prefix="v30_credentials_") as td:
        credentials=Path(td)/"registry.json"
        credentials.write_text(json.dumps({
            "source_reviewer":{
                "credential_type":"HMAC_SHA256",
                "reviewer_id":"TEST_ONLY_RUNTIME_SOURCE",
                "secret_hex":(b"a"*32).hex(),
                "test_fixture":False
            },
            "independent_reviewer":{
                "credential_type":"HMAC_SHA256",
                "reviewer_id":"TEST_ONLY_RUNTIME_AUDITOR",
                "secret_hex":(b"b"*32).hex(),
                "test_fixture":False
            }
        }))
        credentials.chmod(0o600)
        old_env=os.environ.get("V30_REVIEWER_REGISTRY_PATH")
        try:
            os.environ["V30_REVIEWER_REGISTRY_PATH"]=str(credentials)
            out=authority_registry_from_environment(root)
            guard(set(out)=={"source_reviewer","independent_reviewer"}
                  and out["source_reviewer"]["reviewer_id"]!=
                      out["independent_reviewer"]["reviewer_id"],
                  "EXTERNAL_REVIEWER_CREDENTIAL_LOOKUP_FAILED")
            cases+=1
            credentials.chmod(0o644)
            fail(lambda:authority_registry_from_environment(root),
                 "INSECURE_WORLD_READABLE_REVIEWER_KEY_FILE")
            cases+=1
        finally:
            if old_env is None:
                os.environ.pop("V30_REVIEWER_REGISTRY_PATH",None)
            else:os.environ["V30_REVIEWER_REGISTRY_PATH"]=old_env
    bad=copy.deepcopy(ev);bad["review_state"]="APPROVED"
    fail(lambda:v5_append_only_preview(root,bad,ev["source_blob_sha"]),
         "UNAUTHORIZED_SEMANTIC_MERGE")
    fail(lambda:complete_with_preexisting_v5_certificate(
         root,"v5/completion/v5_019_zi9x_q2fYoc_certificate.json",
         "v5/videos/v5_019_zi9x_q2fYoc_advisory_review.json"),
         "UNISSUED_V5_CERTIFICATE")
    cases+=2

    # Diagnostic data are deliberately previously exposed and self-selected.
    # The quantitative evaluator must never report production release.
    benchmark={
        "schema":"V30_PREREGISTERED_RELATION_BENCHMARK_V1",
        "engine_blob_sha":"a"*40,"index_sha256":"b"*64,
        "independent_blinded_adjudication":False,
        "historical_index_exposure":"PREVIOUSLY_EXPOSED_HISTORICAL_INDEX",
        "committed_before_predictions":True,
        "sampling_method":"ANALYST_DIAGNOSTIC",
        "release_thresholds":{"recall_lower_bound":0.95,
                              "precision_lower_bound":0.85},
        "cases":[
            {"id":f"DIAG-{i}","related":i in (1,2),"stratum":"LEGAL",
             "relation_type":"CONDITIONAL","video_number":19,
             "independent_reviewer_reference":"FIXTURE_NOT_HUMAN"}
            for i in range(1,5)],
    }
    pred={
        "schema":"V30_FROZEN_RELATION_PREDICTIONS_V1",
        "engine_blob_sha":"a"*40,"index_sha256":"b"*64,
        "cases":[{"id":f"DIAG-{i}","candidate":i in (1,3)}
                 for i in range(1,5)],
    }
    diag=evaluate(benchmark,pred,require_independent=False)
    guard(diag["total"]["counts"]=={"TP":1,"FN":1,"FP":1,"TN":1}
          and diag["model_release_threshold_pass"] is False
          and not diag["independent_blinded"],
          "HISTORIC_ANALYST_LABELS_FALSELY_APPROVED_AS_UNSEEN_ACCURACY")
    cases+=1
    fail(lambda:evaluate(benchmark,pred,require_independent=True),
         "NONBLIND_HISTORICAL_SAMPLE_AS_INDEPENDENT_HOLDOUT")
    bad=copy.deepcopy(pred);bad["index_sha256"]="0"*64
    fail(lambda:evaluate(benchmark,bad,require_independent=False),
         "INDEX_CHANGED_AFTER_GOLD_REGISTRATION")
    cases+=2

    return {
        "schema":"V30_FULL_INTEGRATION_ADVERSARIAL_TEST_V1",
        "test_scenarios_passed":cases,
        "synthetic_source_cues":len(cues),
        "synthetic_atomic_claims":len(ledger["claims"]),
        "synthetic_external_evidence_used_for_fixtures_only":True,
        "crypto_attestation_test_keys_are_not_real_human_review":True,
        "production_certificates_issued":0,
        "real_financial_facts_independently_verified":0,
        "real_unseen_video_21_plus_opened":False,
        "existing_v5_pending_overlay_preview_validated":True,
        "original_v1_v2_v23_v5_files_modified":False,
        "production_ready":False,
    }

if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
    except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
