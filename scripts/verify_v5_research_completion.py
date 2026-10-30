#!/usr/bin/env python3
"""Fail-closed V5 research completeness gate. CI checks verifiable structure,
file hashes and provenance; source truth and scientific validity need human audit.
No private SRT, investor data or licensed datasets are read.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = "v5/policy/research_completion_gate_v1.json"
HISTORY = "v5/research_completion_001_010.json"
REVIEWS = "v5/videos"
CERTS = "v5/completion"
DOMAINS = {"SOURCE_AND_CLAIMS", "PRIMARY_EVIDENCE",
           "QUANT_AND_EMPIRICAL", "GENERAL_DECISION"}
KINDS = {"LEGAL_OR_PRODUCT", "NUMERIC", "STRATEGY_OR_PERFORMANCE", "QUALITATIVE"}
REVIEW_NAME = re.compile(r"v5_(\d{3})_([A-Za-z0-9_-]{11})_advisory_review\.json$")
CERT_NAME = re.compile(r"v5_(\d{3})_([A-Za-z0-9_-]{11})_certificate\.json$")
SHA = re.compile(r"^[a-f0-9]{64}$")
PRIVATE_KEYS = {"account_number", "owner_income", "owner_balance", "owner_portfolio",
                "personal_holdings", "kis_account", "tax_basis_amount", "real_portfolio"}
PRIVATE_PAT = re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text_field(obj, field):
    need(isinstance(obj.get(field), str) and bool(obj[field].strip()), "missing " + field)

def private_check(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            need(k.lower() not in PRIVATE_KEYS, "personal data field: " + k)
            private_check(v)
    elif isinstance(obj, list):
        for v in obj:
            private_check(v)
    elif isinstance(obj, str):
        need(PRIVATE_PAT.search(obj) is None, "possible personal identifier")

def verify(record, review, policy, review_digest, root=None):
    need(policy["schema"] == "RESEARCH_COMPLETENESS_V1", "policy version")
    need(set(policy["four_domains"]) == DOMAINS and
         policy["historical_001_010_certified"] is False and
         policy["private_data_allowed"] is False,
         "research policy was weakened")
    need(record["schema"] == "RESEARCH_CERTIFICATE_V1", "certificate version")
    need(record["video_number"] == review["video_number"] and
         record["video_id"] == review["video_id"], "video identity")
    need(SHA.fullmatch(record["review_sha256"]) is not None and
         record["review_sha256"] == review_digest, "review was changed after assessment")
    need(record["uses_personal_data"] is False and record["contains_private_srt"] is False,
         "research must be nonpersonal/public")
    claims = review["claims"]
    claim_by_id = {x["id"]: x for x in claims}
    need(len(claim_by_id) == len(claims) and len(claims) > 0, "claim ID inventory")
    need(record["preflight"]["expected_claim_count"] == len(claims), "claim denominator")
    need(record["preflight"]["classified_before_conclusions"] is True, "first-pass obligations missing")
    obligations = record["obligations"]
    need(isinstance(obligations, list) and
         len(obligations) == len(claims) and
         {x["claim_id"] for x in obligations} == set(claim_by_id),
         "all claim IDs must have a research obligation")
    primary = {x["id"]: x for x in review["primary_sources"]}
    source_audits = record.get("source_audits", {})
    need(isinstance(source_audits, dict), "independent primary source audits absent")
    for sid, audit in source_audits.items():
        need(sid in primary, "source audit without original reference")
        for name in ("location_in_original", "scope_and_exception_review",
                     "competing_evidence_or_limitation", "reviewed_on"):
            text_field(audit, name)
        need(audit["verdict"] in ("SUPPORTS", "REFUTES", "LIMITS"),
             "unsupported source audit disposition")
    models = {x["id"]: x for x in review["models"]}
    empirical = {x["id"]: x for x in record["empirical_evidence"]}
    need(len(empirical) == len(record["empirical_evidence"]), "duplicate empirical IDs")
    for e in empirical.values():
        need(e["real_world_data"] is True and e["synthetic_only"] is False,
             "synthetic experiments cannot establish historical strategy returns")
        for name in ("method", "benchmark", "period", "reproduction_command",
                     "costs_and_taxes", "drawdown_and_risk", "bias_assessment",
                     "out_of_sample_or_justification"):
            text_field(e, name)
        need(SHA.fullmatch(e["dataset_sha256"]) is not None, "empirical data digest absent")
        need(isinstance(e["claim_ids"], list) and bool(e["claim_ids"]) and
             set(e["claim_ids"]) <= set(claim_by_id), "empirical claim linkage")
        if e.get("public_dataset_path"):
            p = e["public_dataset_path"]
            need(isinstance(p, str) and p.startswith("v5/public_data/") and
                 ".." not in Path(p).parts and root is not None,
                 "unsafe public data path")
            file = root / p
            need(file.is_file() and digest(file) == e["dataset_sha256"],
                 "empirical data bytes missing or changed")
        else:
            # No auditable data in public CI: cannot certify complete here.
            need(e["external_audit_only"] is True,
                 "external dataset must be explicitly marked unverified by CI")
    for o in obligations:
        cid = o["claim_id"]
        c = claim_by_id[cid]
        kind = o["claim_type"]
        need(kind in KINDS, "unclassified claim: " + cid)
        need(type(o["material"]) is bool and o["material"] == c["material"],
             "inconsistent materiality " + cid)
        need(o["status"] in ("VERIFIED", "REFUTED", "BLOCKED"),
             "invalid obligation status " + cid)
        for k in ("applicability", "counterexample", "decision_impact"):
            text_field(o, k)
        ps, ms, es = (o["primary_source_ids"], o["model_ids"], o["empirical_ids"])
        need(isinstance(ps, list) and isinstance(ms, list) and isinstance(es, list),
             "evidence references not arrays")
        need(set(ps) <= set(primary) and set(ms) <= set(models) and
             set(es) <= set(empirical), "unresolved evidence reference " + cid)
        for id in ps:
            need(cid in primary[id]["claim_ids"] and
                 primary[id]["actual_text_checked"] is True,
                 "primary source not linked to exact claim " + cid)
        for id in ms:
            need(cid in models[id]["claim_ids"], "math model back-link " + cid)
        for id in es:
            need(cid in empirical[id]["claim_ids"], "empirical back-link " + cid)
        if kind == "STRATEGY_OR_PERFORMANCE":
            need(not o.get("empirical_not_applicable_reason"),
                 "strategy cannot waive empirical study " + cid)
        if c["legacy_verdict"] == "CONTRADICTED":
            need(o["status"] != "VERIFIED" and c["positive_principle_allowed"] is False,
                 "contradicted principle promoted " + cid)
        if o["status"] in ("VERIFIED", "REFUTED"):
            need(c["current_review"] == "CHECKED" and
                 c["independently_checked_this_turn"] is True,
                 "no independent review of resolved claim " + cid)
            if o["material"] and kind in ("LEGAL_OR_PRODUCT", "STRATEGY_OR_PERFORMANCE"):
                need(ps, "material fact has no official source " + cid)
            if o["material"] and kind in ("NUMERIC", "STRATEGY_OR_PERFORMANCE"):
                need(ms, "material numeric/strategy claim has no reproducible model " + cid)
            if o["material"] and kind == "STRATEGY_OR_PERFORMANCE":
                need(es, "material strategy lacks real empirical evidence " + cid)
            if o["material"] and kind == "QUALITATIVE":
                need(ps or es, "qualitative principle has no external evidence " + cid)
            if kind != "STRATEGY_OR_PERFORMANCE" and not es:
                text_field(o, "empirical_not_applicable_reason")
            if kind == "STRATEGY_OR_PERFORMANCE":
                need(not o.get("empirical_not_applicable_reason"),
                     "strategy cannot waive empirical study " + cid)
            if o["status"] == "REFUTED":
                text_field(o, "correction")
                need(ps or ms or es, "refutation lacks independently testable basis " + cid)
        if o["status"] == "BLOCKED":
            need(not c["positive_principle_allowed"], "blocked claim promoted " + cid)
    domains = record["domains"]
    need(set(domains) == DOMAINS, "four acceptance domains are mandatory")
    for d in domains.values():
        need(d["status"] in ("PASS", "BLOCKED"), "invalid domain result")
        text_field(d, "reason")
    blockers = record["blockers"]
    need(isinstance(blockers, list), "blockers")
    blocker_ids = set()
    for b in blockers:
        need(b["id"] not in blocker_ids, "duplicate blocker")
        blocker_ids.add(b["id"])
        need(set(b["claim_ids"]) <= set(claim_by_id) and b["claim_ids"],
             "blocker missing claim IDs")
        for k in ("missing_evidence", "decision_blocked", "reopen_when"):
            text_field(b, k)
    release = record["release"]
    need(release["status"] in ("RESEARCH_COMPLETE", "RESEARCH_BLOCKED"),
         "release status")
    need(release["personal_advice"] is False and release["trading"] is False,
         "cannot authorize personal investment advice or trading")
    if release["status"] == "RESEARCH_COMPLETE":
        atomic = record.get("atomic_coverage")
        need(isinstance(atomic, dict) and
             atomic.get("full_srt_material_claim_inventory_completed") is True,
             "atomic financial statements not fully inventoried")
        source_cue_count = review["source"].get("source_cue_count")
        need(type(source_cue_count) is int and source_cue_count > 0 and
             atomic.get("source_cue_count") == source_cue_count,
             "atomic claim inventory not tied to original source cues")
        units = atomic.get("statements")
        need(isinstance(units, list) and len(units) >= len(claims),
             "only a core claim subset was reviewed")
        unit_ids = [u["atomic_id"] for u in units]
        need(len(unit_ids) == len(set(unit_ids)), "duplicate atomic ID")
        mapped_core = set()
        for unit in units:
            refs = unit["linked_core_claim_ids"]
            need(isinstance(refs, list) and set(refs) <= set(claim_by_id),
                 "atomic claim links nonexistent core claim")
            if unit["material"]:
                need(refs and unit["evidence_refs"] and
                     unit["review_verdict"] in ("VERIFIED", "REFUTED"),
                     "unresolved material atomic statement")
                start, end = unit["source_cue_range"]
                need(type(start) is int and type(end) is int and
                     0 <= start <= end < source_cue_count,
                     "atomic source cue range invalid")
            mapped_core.update(refs)
        need(mapped_core == set(claim_by_id), "not all core claims traced to atomic statements")
        need(atomic.get("unmapped_material_statement_count") == 0,
             "remaining material statements outside core claim registry")
        need(all(d["status"] == "PASS" for d in domains.values()), "domain not passed")
        need(not blockers and not review["open_blockers"], "OPEN evidence cannot be concealed")
        need(all(o["status"] != "BLOCKED" for o in obligations),
             "unresolved claim cannot be certified")
        need(review["source"]["raw_srt_read_and_hash_verified_this_turn"] is True and
             review["source"]["full_cue_review_this_turn"] is True,
             "original source not fully reviewed")
        need(all(isinstance(d.get("proof_ids"), list) and d["proof_ids"]
                 for d in domains.values()),
             "four domains require concrete proof IDs")
        need(all(sid in source_audits for o in obligations
                 if o["status"] in ("VERIFIED", "REFUTED") and o["material"]
                 for sid in o["primary_source_ids"]),
             "material primary source lacks contextual audit")
        need(all(e["public_dataset_path"] for e in empirical.values()),
             "nonpublic empirical data cannot be independently replayed in CI")
        need(review["one_turn_closeout"]["result"] == "DECISION_MODULE_READY_L2",
             "legacy limited decision module cannot be research complete")
        need(review["decision_logic"]["baseline_is_same_horizon_and_currency"] is True,
             "alternatives not comparable")
        need(record["independent_audit"]["human_or_separately_appointed_reviewer"] is True and
             record["independent_audit"]["source_and_method_checked"] is True,
             "independent source/semantic audit absent")
        text_field(record["independent_audit"], "limitations")
        need(not any(e.get("external_audit_only") for e in empirical.values()),
             "external data not reproducible in public CI: cannot certify")
        need(release["approved"] is True, "completion not approved")
    else:
        need(release["approved"] is False, "blocked report cannot be approved")
        need(blockers and (any(o["status"] == "BLOCKED" for o in obligations) or
                           any(d["status"] == "BLOCKED" for d in domains.values())),
             "blocked status requires specific unresolved claims and evidence")
    private_check(record)
    return release["status"]

def check_repo(root):
    policy = read(root / POLICY)
    history = read(root / HISTORY)
    legacy = read(root / "v5/retrofit/summary_20261030.json")
    need(history["schema"] == "HISTORICAL_RESEARCH_COMPLETENESS_001_010_V1",
         "legacy research status version")
    need(history["video_count"] == legacy["video_count"] == 10 and
         history["claim_count"] == legacy["claim_ids"] == 122 and
         history["material_open"] == legacy["external_open_recorded_historically"] == 26,
         "legacy research denominator")
    need(history["certified_count"] == 0 and
         sorted(x["video_number"] for x in history["videos"]) == list(range(1, 11)) and
         all(x["status"] == "NOT_CERTIFIED" for x in history["videos"]),
         "historical research falsely promoted")
    reviews = sorted((root / REVIEWS).glob("*.json")) if (root / REVIEWS).is_dir() else []
    certs = sorted((root / CERTS).glob("*.json")) if (root / CERTS).is_dir() else []
    need(len(reviews) == len(certs), "every research review needs a completion certificate")
    expected = set()
    completed = 0
    blocked = 0
    for file in reviews:
        m = REVIEW_NAME.fullmatch(file.name)
        need(m is not None, "unknown research file")
        name = "v5_" + m.group(1) + "_" + m.group(2) + "_certificate.json"
        cert_file = root / CERTS / name
        need(cert_file.is_file(), "missing completion certificate " + name)
        doc = read(file)
        need(doc["synthetic_example"] is False, "synthetic fixture published as research")
        outcome = verify(read(cert_file), doc, policy, digest(file), root)
        completed += outcome == "RESEARCH_COMPLETE"
        blocked += outcome == "RESEARCH_BLOCKED"
        expected.add(name)
    need({f.name for f in certs} == expected and
         all(CERT_NAME.fullmatch(f.name) for f in certs),
         "orphan certificate or unexpected JSON")
    return {"structural_gate": "PASS", "historical_1_10_certified": 0,
            "new_completed": completed, "new_blocked": blocked,
            "real_primary_source_truth_automatically_proven": False}

def self_test(root):
    # All structural examples are fictional. Passing says nothing about real source truth.
    policy = read(root / POLICY)
    claim = {"id":"DEMO0000001-01","material":True,"legacy_verdict":"QUALIFIED",
             "positive_principle_allowed":False,"current_review":"BLOCKED",
             "independently_checked_this_turn":False}
    review = {"video_number":999,"video_id":"DEMO0000001",
              "source":{"raw_srt_read_and_hash_verified_this_turn":False,
                        "full_cue_review_this_turn":False},
              "claims":[claim], "primary_sources":[], "models":[], "open_blockers":[],
              "one_turn_closeout":{"result":"EVIDENCE_BLOCKED"},
              "decision_logic":{"baseline_is_same_horizon_and_currency":False}}
    sha = "a" * 64
    obligation = {"claim_id":claim["id"],"claim_type":"STRATEGY_OR_PERFORMANCE",
                  "material":True,"status":"BLOCKED","applicability":"Fictional strategy",
                  "counterexample":"Fictional reversal","decision_impact":"No decision permitted",
                  "primary_source_ids":[],"model_ids":[],"empirical_ids":[],
                  "empirical_not_applicable_reason":None}
    cert = {"schema":"RESEARCH_CERTIFICATE_V1","video_number":999,"video_id":"DEMO0000001",
            "review_sha256":sha,"uses_personal_data":False,"contains_private_srt":False,
            "preflight":{"expected_claim_count":1,"classified_before_conclusions":True},
            "obligations":[obligation],"empirical_evidence":[],
            "domains":{x:{"status":"BLOCKED","reason":"no verifiable source"} for x in DOMAINS},
            "blockers":[{"id":"D-1","claim_ids":[claim["id"]],
                         "missing_evidence":"original source and public benchmark",
                         "decision_blocked":"all strategy conclusions",
                         "reopen_when":"authentic sources become available"}],
            "release":{"status":"RESEARCH_BLOCKED","approved":False,
                       "personal_advice":False,"trading":False},
            "source_audits":{},
            "independent_audit":{"human_or_separately_appointed_reviewer":False,
                                 "source_and_method_checked":False,"limitations":"fictional"}}
    need(verify(cert,review,policy,sha,root) == "RESEARCH_BLOCKED",
         "valid blocked example rejected")
    # A fictional positive path exercises the *logic*, not independent truth.
    passed_review = copy.deepcopy(review)
    passed_review["source"].update(raw_srt_read_and_hash_verified_this_turn=True,
                                   full_cue_review_this_turn=True,
                                   source_cue_count=1)
    passed_review["claims"][0].update(current_review="CHECKED",
                                      independently_checked_this_turn=True,
                                      positive_principle_allowed=True)
    passed_review["primary_sources"] = [{
        "id":"MOCK_PRIMARY", "actual_text_checked":True,
        "claim_ids":[claim["id"]]}]
    passed_review["one_turn_closeout"]["result"] = "DECISION_MODULE_READY_L2"
    passed_review["decision_logic"]["baseline_is_same_horizon_and_currency"] = True
    good = copy.deepcopy(cert)
    good["obligations"][0].update(claim_type="LEGAL_OR_PRODUCT",
                                  status="VERIFIED",
                                  primary_source_ids=["MOCK_PRIMARY"],
                                  empirical_not_applicable_reason="A fictional legal-fact example")
    good["source_audits"] = {"MOCK_PRIMARY":{
        "location_in_original":"Synthetic clause 1",
        "scope_and_exception_review":"Synthetic fact, no real legal effect",
        "competing_evidence_or_limitation":"Never use as actual evidence",
        "reviewed_on":"2026-10-30","verdict":"SUPPORTS"}}
    good["blockers"] = []
    good["domains"] = {
        x:{"status":"PASS","reason":"Fictional structural test",
           "proof_ids":["MOCK_PRIMARY" if x == "PRIMARY_EVIDENCE" else "SYNTHETIC_ONLY"]}
        for x in DOMAINS}
    good["independent_audit"].update(human_or_separately_appointed_reviewer=True,
                                      source_and_method_checked=True)
    good["atomic_coverage"] = {
        "full_srt_material_claim_inventory_completed":True,
        "source_cue_count":1,
        "unmapped_material_statement_count":0,
        "statements":[{
            "atomic_id":"DEMO-A01","material":True,"source_cue_range":[0,0],
            "linked_core_claim_ids":[claim["id"]],
            "evidence_refs":["MOCK_PRIMARY"],"review_verdict":"VERIFIED"}]}
    good["release"].update(status="RESEARCH_COMPLETE",approved=True)
    need(verify(good,passed_review,policy,sha,root) == "RESEARCH_COMPLETE",
         "fictional valid completion structure rejected")
    for mutation in ("missing_atomic", "missing_unit", "unmapped", "cue_gap", "unreviewed"):
        x = copy.deepcopy(good)
        if mutation == "missing_atomic": x.pop("atomic_coverage")
        elif mutation == "missing_unit": x["atomic_coverage"]["statements"] = []
        elif mutation == "unmapped": x["atomic_coverage"]["unmapped_material_statement_count"] = 1
        elif mutation == "cue_gap": x["atomic_coverage"]["statements"][0]["source_cue_range"] = [0,1]
        else: x["atomic_coverage"]["statements"][0]["review_verdict"] = "BLOCKED"
        try:
            verify(x,passed_review,policy,sha,root)
        except (ValueError,TypeError,KeyError,IndexError):
            pass
        else:
            raise ValueError("atomic inventory mutation passed: "+mutation)
    trials = []
    x = copy.deepcopy(cert); x["release"].update(status="RESEARCH_COMPLETE",approved=True); trials.append(x)
    x = copy.deepcopy(cert); x["obligations"] = []; trials.append(x)
    x = copy.deepcopy(cert); x["review_sha256"] = "0"*64; trials.append(x)
    x = copy.deepcopy(cert); x["blockers"] = []; trials.append(x)
    x = copy.deepcopy(cert); x["domains"].pop("PRIMARY_EVIDENCE"); trials.append(x)
    x = copy.deepcopy(cert); x["obligations"][0]["status"] = "VERIFIED"; trials.append(x)
    x = copy.deepcopy(cert); x["obligations"][0]["empirical_not_applicable_reason"]="Skip empirical"; trials.append(x)
    x = copy.deepcopy(cert); x["uses_personal_data"] = True; trials.append(x)
    x = copy.deepcopy(cert); x["preflight"]["expected_claim_count"] = 2; trials.append(x)
    x = copy.deepcopy(cert); x["release"]["approved"] = True; trials.append(x)
    x = copy.deepcopy(cert); x["obligations"][0]["claim_type"]="INVALID"; trials.append(x)
    # The above successful structure must fail if source audit or method coverage disappears.
    for f in ("source_audits", "empirical_evidence"):
        x = copy.deepcopy(good)
        x.pop(f)
        try:
            verify(x, passed_review, policy, sha, root)
        except (ValueError, KeyError, TypeError):
            pass
        else:
            raise ValueError("fictional completion missing " + f + " passed")
    x = copy.deepcopy(good)
    x["domains"]["PRIMARY_EVIDENCE"]["proof_ids"] = []
    try:
        verify(x, passed_review, policy, sha, root)
    except (ValueError, TypeError, KeyError):
        pass
    else:
        raise ValueError("unproven primary evidence accepted")
    for i, x in enumerate(trials):
        try:
            verify(x,review,policy,sha,root)
        except (ValueError, TypeError, KeyError):
            pass
        else:
            raise ValueError("invalid research accepted in mutation " + str(i))
    return {"fictional_blocked_positive_test": 1, "fictional_complete_structure_test": 1,
            "additional_positive_mutations_rejected": 8,
            "negative_mutations_rejected": len(trials),
            "real_research_completed_by_test": 0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = check_repo(args.root.resolve())
    if args.self_test:
        result["tests"] = self_test(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(json.dumps({"structural_gate": "FAIL", "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
