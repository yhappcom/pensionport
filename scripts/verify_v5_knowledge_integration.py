#!/usr/bin/env python3
"""Append-only, fail-closed comparison and knowledge integration for V5.

Reads immutable V3 and curated #1-260 seed. Generates candidate/impact decisions.
APPROVED overlays require a verified V5 RESEARCH_COMPLETE certificate AND distinct
semantic-review metadata. The public CI cannot establish semantic truth on its own.
No personal/private SRT content is read or written.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY="v5/integration/integration_policy_v1.json"
QUEUE="v5/integration/pilot_001_205_candidate_queue.json"
BASE="data/synthesis/investment_knowledge_001_260/curated_recurring_concepts_16.json"
FAMILIES="data/synthesis/investment_knowledge_001_260/concept_families.json"
SHA1=re.compile(r"^[0-9a-f]{40}$")
VID=re.compile(r"^[A-Za-z0-9_-]{11}$")
CLAIM=re.compile(r"^(.{11})-(\d{2,3})$")
RELS={"SUPPORTS_UNDER_CONDITIONS","QUALIFIES_SCOPE","CONTRADICTS",
      "CORRECTION_ONLY","SUPERSEDES","TOPIC_ONLY","NEW_CONCEPT"}
DANGEROUS={"CONTRADICTS","CORRECTION_ONLY","SUPERSEDES"}
POSITIVE={"SUPPORTS_UNDER_CONDITIONS","QUALIFIES_SCOPE"}
PRIVATE_FIELDS={"account_number","personal_holdings","owner_portfolio",
                "owner_income","owner_balance","personal_account","investment_account_number"}
SPOT_PRIVATE=re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")

def need(ok,msg):
    if not ok: raise ValueError(msg)

def read(path): return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(path):
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def privacy_guard(x):
    if isinstance(x,dict):
        for k,v in x.items():
            need(k.lower() not in PRIVATE_FIELDS,"private field: "+k)
            privacy_guard(v)
    elif isinstance(x,list):
        for v in x: privacy_guard(v)
    elif isinstance(x,str):
        need(not SPOT_PRIVATE.search(x),"personal id/private key in public event")

def check_path(relative,root):
    need(isinstance(relative,str) and ".." not in relative.split("/")
         and not relative.startswith("/") and "\\" not in relative,
         "unsafe reference path")
    p=(root/relative)
    need(p.is_file(),"missing provenance file: "+relative)
    return p

def source_claims(event,root):
    src=event["source_path"]
    need(isinstance(src,str) and
         (re.fullmatch(r"data/analysis_events/[A-Za-z0-9_-]{11}\.json",src)
          or re.fullmatch(r"v5/videos/v5_\d{3}_[A-Za-z0-9_-]{11}_advisory_review\.json",src)),
         "unsupported mutable/private source path")
    path=check_path(src,root)
    need(SHA1.fullmatch(event["source_blob_sha"]) is not None and
         git_blob_sha(path)==event["source_blob_sha"],
         "source V3/V5 bytes have changed; new revision must be separate")
    d=read(path)
    if src.startswith("data/analysis_events/"):
        need(path.stem==d["video_id"],"source video file identity")
        claims=d["core_claims"]
        ids=[x["claim_id"] for x in claims]
        return d["video_id"],{x["claim_id"]:x for x in claims},ids
    claims=d["claims"]
    ids=[x["id"] for x in claims]
    return d["video_id"],{x["id"]:x for x in claims},ids

def completed_claim_ids(root):
    """Actual real RESEARCH_COMPLETE gate determines integration eligibility."""
    from verify_v5_research_completion import verify, digest
    policy=read(root/"v5/policy/research_completion_gate_v1.json")
    cdir=root/"v5/completion"
    rdir=root/"v5/videos"
    approved=set()
    if not cdir.is_dir(): return approved
    for cp in sorted(cdir.glob("v5_*_certificate.json")):
        c=read(cp)
        expected="v5_{:03d}_{}_advisory_review.json".format(
            c["video_number"],c["video_id"])
        rp=rdir/expected
        need(rp.is_file(),"orphan research completion certificate")
        review=read(rp)
        status=verify(c,review,policy,digest(rp),root)
        if status=="RESEARCH_COMPLETE":
            approved.update(x["id"] for x in review["claims"]
                            if x["current_review"]=="CHECKED")
    return approved

def seed_state(seed, policy,root):
    need(seed["concept_count"]==16 and len(seed["concepts"])==16
         and seed["confirmed_semantic_equivalence_merges"]==0,
         "original curation history unexpectedly revised")
    need(policy["baseline"]==BASE and
         policy["baseline_git_blob_sha"]==git_blob_sha(root/BASE),
         "baseline hash mismatch; explicit new version needed")
    concepts={}
    seen= set()
    for item in seed["concepts"]:
        cid=item["concept_id"]
        need(cid not in concepts,"duplicate canonical concept ID")
        relation={}
        all_evidence=set()
        for rel,ids in item["relations"].items():
            need(len(ids)==len(set(ids)),"duplicates in baseline relation")
            for claim in ids:
                relation.setdefault(claim,set()).add(rel)
                all_evidence.add(claim)
                seen.add(claim)
        need({x["claim_id"] for x in item["evidence"]}==all_evidence,
             "baseline evidence crosslinks mismatch: "+cid)
        concepts[cid]={
            "topic_family":item["topic_family"],
            "original_relation_ids":relation,
            "overlay_relations":{},
            "evidence_refreshes":{},
            "safety_conflicts":set(),
            "impacted_original_claim_ids":set(all_evidence)
        }
    need(len(seen)==seed["distinct_evidence_claims"]==55,
         "historical 55 distinct claim denominator mismatch")
    return concepts,seen

def load_families(root):
    registry=read(root/FAMILIES)
    names={x["concept_id"] for x in registry["concept_families"]}
    need(len(names)==39,"historical 39 family taxonomy changed")
    return names

def event_check(event,concepts,policy,root,source_cache,known_families,synthetic=False):
    required={"event_id","source_path","source_blob_sha","source_claim_id",
              "target_concept_id","relation","review_state","assessment",
              "evidence_refs","evidence_blob_shas","blocked_reason","reopen_trigger",
              "supersedes_claim_id","certificate_path"}
    need(set(event)>=required and
         set(event)<=required|{"semantic_review","new_concept"},
         "unexpected or missing fields in integration event")
    for k in ("event_id","target_concept_id","assessment","blocked_reason",
              "reopen_trigger"):
        need(isinstance(event.get(k),str) and event[k].strip(),
             "missing event field: "+k)
    need(event["relation"] in RELS and
         event["review_state"] in ("PENDING_REVIEW","APPROVED"),
         "unknown semantic relation/state")
    need(re.fullmatch(r"V5-COMP-\d{3,6}",event["event_id"]) is not None,
         "non-versioned integration event ID")
    src=event["source_path"]
    key=(src,event["source_blob_sha"])
    if key not in source_cache:
        source_cache[key]=source_claims(event,root)
    vid,records,ids=source_cache[key]
    need(len(ids)==len(set(ids)),"source claim IDs duplicated")
    claimid=event["source_claim_id"]
    match=CLAIM.fullmatch(claimid)
    standard=match is not None and match.group(1)==vid
    public_71=(vid=="4vNF2fui5jc" and
               re.fullmatch(r"71-PUBLIC-(0[1-9]|1[0-3])",claimid) is not None)
    need((standard or public_71) and claimid in records,
         "new event cites nonexistent or mismatched original claim "+str(claimid))
    source=records[claimid]
    verdict=source.get("verification",source.get("legacy_verdict"))
    need(isinstance(verdict,str) and verdict,
         "missing original verdict in source claim")
    if verdict=="CONTRADICTED":
        need(event["relation"] not in POSITIVE,
             "historically contradicted text was promoted as positive knowledge")
    target=event["target_concept_id"]
    if event["relation"]!="NEW_CONCEPT":
        need(target in concepts,"new concept cannot be minted by ordinary relation")
        need("new_concept" not in event,"unexpected new concept payload")
    else:
        need(target not in concepts,"NEW_CONCEPT collides with historical concept")
        spec=event.get("new_concept",{})
        need(spec.get("concept_id")==target and
             spec.get("topic_family") in known_families and
             isinstance(spec.get("conditional_principle"),str) and
             len(spec["conditional_principle"])>=12,
             "NEW_CONCEPT requires scoped proposed concept and known topic family")
    need(isinstance(event["evidence_refs"],list) and
         len(set(event["evidence_refs"]))==len(event["evidence_refs"]),
         "duplicated evidence reference")
    pins=event["evidence_blob_shas"]
    need(isinstance(pins,dict) and
         set(pins)==set(event["evidence_refs"]),
         "all evidence references need immutable content SHA")
    for ref in event["evidence_refs"]:
        need(ref.startswith("v5/") and SHA1.fullmatch(pins[ref]) and
             git_blob_sha(check_path(ref,root))==pins[ref],
             "independent evidence artifact altered: "+ref)
    refid=event["supersedes_claim_id"]
    if event["relation"]=="SUPERSEDES":
        need(CLAIM.fullmatch(refid or "") is not None and
             refid!=claimid,
             "supersession requires another historical claim")
    else:
        need(refid is None,"supersession target used without SUPERSEDES")
    if event["review_state"]=="PENDING_REVIEW":
        need(event["certificate_path"] is None and
             "semantic_review" not in event,
             "PENDING entry must not contain fake approval")
    else:
        need(event["certificate_path"] and
             isinstance(event.get("semantic_review"),dict),
             "reviewed integration requires completed certificate and independent semantic review")
        reviewer=event["semantic_review"]
        for k in ("reviewer_reference","review_date","equivalence_reason",
                  "scope_conditions","counterevidence_checked"):
            need(type(reviewer.get(k)) is str and reviewer[k].strip(),
                 "semantic reviewer proof missing: "+k)
        need(reviewer["reviewer_reference"]!="CHATGPT_ONLY",
             "no self-attested semantic approval from AI alone")
        cp=event["certificate_path"]
        need(cp.startswith("v5/completion/") and
             (synthetic and cp=="v5/completion/SYNTHETIC_ONLY.json"
              or check_path(cp,root)),
             "trusted completion certificate path required")
        if not synthetic:
            cert=read(root/cp)
            need(cert["video_id"]==vid and
                 cert["release"]["status"]=="RESEARCH_COMPLETE" and
                 cert["release"]["approved"] is True and
                 claimid in {x["claim_id"] for x in cert["obligations"]},
                 "completed certificate does not certify this exact source claim")
        if synthetic:
            need(cp=="v5/completion/SYNTHETIC_ONLY.json",
                 "synthetic completion tests cannot use real file references")
    return source,verdict,vid

def compare_and_integrate(events,seed,policy,root,eligible=None,allow_synthetic=False):
    """Returns nonmutating indexed overlay preview; rejects all unsafe merges.

    eligible may be injected ONLY inside self-test in memory; never CLI or on-disk.
    """
    need(not allow_synthetic or eligible is not None,"synthetic only internal")
    concepts, original_ids=seed_state(seed,policy,root)
    known_families=load_families(root)
    completed=eligible if allow_synthetic else completed_claim_ids(root)
    known_events=set()
    seen_decisions={}
    outputs=[]
    stats={"already_indexed":0,"pending":0,"conflict_review":0,
           "topic_only":0,"approved_overlays":0,"evidence_refreshes":0,
           "new_concepts_created":0}
    source_cache={}
    legacy_claims,parts,irregular=load_legacy_claim_index(root)
    for ev in events:
        # Validate every event at the entry point, including programmatic callers.
        privacy_guard(ev)
        eid=ev["event_id"]
        need(eid not in known_events,"duplicate event_id")
        known_events.add(eid)
        source,verdict,vid=event_check(ev,concepts,policy,root,source_cache,known_families,allow_synthetic)
        claimid=ev["source_claim_id"];target=ev["target_concept_id"]
        row=legacy_claims.get(claimid)
        if row:
            need(row["original_verdict"]==verdict and
                 row["video_id"]==vid,
                 "new evidence falsifies original crosswalk verdict or provenance")
        rel=ev["relation"]; status=ev["review_state"]
        old=concepts[target]["original_relation_ids"].get(claimid,set()) if target in concepts else set()
        key=(claimid,target)
        previous=seen_decisions.setdefault(key,set())
        need(not previous or rel in previous,
             "two incompatible relations on the same claim/concept require a separate conflict review")
        previous.add(rel)
        if rel=="TOPIC_ONLY":
            need(status=="PENDING_REVIEW","topic-only keyword overlap must never integrate")
            result="TOPIC_ONLY"
        elif old and rel not in old and rel not in ("SUPERSEDES",):
            result="CONFLICT_REVIEW_REQUIRED"
            need(status=="PENDING_REVIEW","historical relation conflict cannot be auto-approved")
        elif old and rel in old and status=="PENDING_REVIEW":
            result="ALREADY_INDEXED"
        elif status=="PENDING_REVIEW":
            result=("CONFLICT_REVIEW_REQUIRED" if rel in DANGEROUS else "PENDING_REVIEW")
        else:
            need(claimid in completed,
                 "APPROVED event has no V5 RESEARCH_COMPLETE claim certificate")
            need(rel!="TOPIC_ONLY","semantic-only similarity cannot merge")
            if rel=="SUPERSEDES":
                # historical target must be a known claim cited in target concept
                need(ev["supersedes_claim_id"] in
                     concepts[target]["impacted_original_claim_ids"],
                     "supersession cannot rewrite an unrelated legacy claim")
            need(ev["evidence_refs"],
                 "approved knowledge requires nonempty reproducible proof reference")
            if rel=="NEW_CONCEPT":
                spec=ev["new_concept"]
                concepts[target]={"topic_family":spec["topic_family"],
                     "original_relation_ids":{},"overlay_relations":{},
                     "evidence_refreshes":{},"safety_conflicts":set(),
                     "impacted_original_claim_ids":set()}
                stats["new_concepts_created"]+=1
            if old and rel in old:
                concepts[target]["evidence_refreshes"].setdefault(claimid,[]).append(eid)
                stats["evidence_refreshes"]+=1
                result="EVIDENCE_REFRESH_ONLY"
            else:
                concepts[target]["overlay_relations"].setdefault(rel,set()).add(claimid)
                stats["approved_overlays"]+=1
                result="APPROVED_OVERLAY"
                if rel in ("CONTRADICTS","SUPERSEDES","CORRECTION_ONLY"):
                    concepts[target]["safety_conflicts"].add(eid)
            # Verified relation does not silently edit prior canonical content.
        if result=="ALREADY_INDEXED":stats["already_indexed"]+=1
        if result=="PENDING_REVIEW":stats["pending"]+=1
        if result=="CONFLICT_REVIEW_REQUIRED":stats["conflict_review"]+=1
        if result=="TOPIC_ONLY":stats["topic_only"]+=1
        impact=(sorted(concepts[target]["impacted_original_claim_ids"])
                if target in concepts else [])
        outputs.append({
            "event_id":eid,"claim_id":claimid,"concept_id":target,
            "proposed_relation":rel,"original_verdict":verdict,
            "state":result,"previous_relation":sorted(old),
            "affected_existing_claim_ids":impact,
            "review_trigger":ev["reopen_trigger"],
            "positive_knowledge_allowed":result in ("APPROVED_OVERLAY","EVIDENCE_REFRESH_ONLY")
                                         and rel in POSITIVE and verdict!="CONTRADICTED"
        })
    need(all(x["state"]!="APPROVED_OVERLAY" for x in outputs
             if x["original_verdict"]=="CONTRADICTED"
             and x["proposed_relation"] in POSITIVE),
         "positive contradicted source leakage")
    # Stable distinct-claim tally; integration is overlays, never deletion or rekeying.
    added=set()
    for c in concepts.values():
        for claims in c["overlay_relations"].values():added.update(claims)
    view={
        "schema":"V5_KNOWLEDGE_INTEGRATION_PREVIEW_V1",
        "baseline_concepts":16,
        "baseline_distinct_evidence_claims":len(original_ids),
        "historical_crosswalk_claims":len(legacy_claims),
        "historical_crosswalk_video_count":253,
        "historical_crosswalk_partitions":parts,
        "historical_irregular_id_examples":irregular[:12],
        "historical_irregular_id_count":len(irregular),
        "baseline_original_events_preserved":True,
        "approved_new_distinct_evidence_claim_ids":sorted(added-original_ids),
        "approved_overlaid_relation_count":stats["approved_overlays"],
        "original_claims_overwritten":0,
        "canonical_baseline_mutated":False,
        "new_concepts_in_overlay":stats["new_concepts_created"],
        "statistics":stats,
        "decisions":outputs,
        "active_unreviewed_conflicts":[x["event_id"] for x in outputs
               if x["state"]=="CONFLICT_REVIEW_REQUIRED"],
        "concept_impact_flags":{key:sorted(v["safety_conflicts"])
                        for key,v in concepts.items() if v["safety_conflicts"]},
        "automatic_semantic_merge_claimed":False,
        "actual_research_completed_by_this_tool":False
    }
    privacy_guard(view)
    return view

def load_legacy_claim_index(root):
    """Read all 4,120 original claim records; no change to original crosswalk files."""
    known=load_families(root)
    all_rows={}
    irregular=[]
    parts=[]
    for name,expected in (
            ("claims_crosswalk_001_130.json",2127),
            ("claims_crosswalk_131_260.json",1993)):
        path=root/"data/synthesis/investment_knowledge_001_260"/name
        data=read(path)
        need(data["schema_version"]==1,"crosswalk schema version")
        rows=data["records"]
        need(len(rows)==expected,"historical claims deleted or added without migration")
        for row in rows:
            cid=row["claim_id"]
            m=CLAIM.fullmatch(cid)
            need(row["primary_concept_id"] in known and
                 cid not in all_rows,"unknown topic or duplicate historical claim: "+cid)
            if not m or m.group(1)!=row["video_id"]:
                irregular.append({"claim_id":cid,"video_id":row["video_id"],
                                  "roster_no":row["roster_no"]})
            all_rows[cid]=row
        parts.append({"part":name,"verified_claims":len(rows)})
    need(len(all_rows)==4120 and
         len({row["video_id"] for row in all_rows.values()})==253,
         "253 video/4,120 claim historical baseline mismatch")
    need(len(irregular)==13 and
         {x["claim_id"] for x in irregular}==
         {f"71-PUBLIC-{i:02d}" for i in range(1,14)}
         and all(x["roster_no"]==71 and
                 x["video_id"]=="4vNF2fui5jc" for x in irregular),
         "nonstandard historical claim IDs differ from documented #71 public proxy")
    # This is an original-v3 crosswalk. The curated 16 are only a sampled,
    # high-stakes synthesis of some of these immutable source events.
    return all_rows,parts,irregular

def validate_repository(root):
    p=read(root/POLICY)
    q=read(root/QUEUE)
    seed=read(root/BASE)
    need(p["schema"]=="V5_INCREMENTAL_KNOWLEDGE_INTEGRATION_V1"
         and p["immutable_v3_v4_v5"] is True
         and p["no_automatic_semantic_equivalence"] is True
         and p["approval_requires_research_complete"] is True
         and p["public_nonpersonal_only"] is True,
         "integration contract weakened")
    need(q["schema"]=="V5_INCREMENTAL_KNOWLEDGE_QUEUE_V1" and
         q["baseline_blob_sha"]==p["baseline_git_blob_sha"] and
         q["final_knowledge_approval_count"]==0 and
         q["all_entries_research_complete"] is False and
         q["no_personal_data"] is True,
         "real pilot falsely marked integrated")
    privacy_guard(q)
    v=compare_and_integrate(q["events"],seed,p,root)
    need(v["baseline_concepts"]==16 and
         v["historical_crosswalk_claims"]==4120 and
         v["baseline_distinct_evidence_claims"]==55 and
         v["statistics"]["already_indexed"]==4 and
         v["statistics"]["conflict_review"]==2 and
         v["statistics"]["topic_only"]==1 and
         v["statistics"]["pending"]==1 and
         v["statistics"]["approved_overlays"]==0,
         "real historical comparison no longer has expected conservative outcome")
    need(v["active_unreviewed_conflicts"]==["V5-COMP-005","V5-COMP-006"],
         "real contradictions disappeared from review queue")
    need(v["approved_new_distinct_evidence_claim_ids"]==[],
         "unverified knowledge integrated into canonical view")
    # Future user-command-driven research must arrive WITH an explicit comparison
    # package. CI never accepts a newly created review without its claim intake.
    inbox=root/"v5/integration/incoming"
    incoming=[]
    if inbox.is_dir():
        files=sorted(x for x in inbox.iterdir() if x.is_file())
        need(all(x.suffix==".json" for x in files),
             "unreviewed integration files in incoming queue")
        for file in files:
            data=read(file)
            need(data["schema"]=="V5_INCREMENTAL_KNOWLEDGE_QUEUE_V1"
                 and data["baseline_blob_sha"]==p["baseline_git_blob_sha"]
                 and data["no_personal_data"] is True,
                 "integration import is not based on immutable canonical schema")
            need(len(data["events"])>0,"no empty integration event packages")
            need(data["final_knowledge_approval_count"]==
                 sum(x["review_state"]=="APPROVED" for x in data["events"]),
                 "integration approvals count mismatches actual reviewed events")
            privacy_guard(data)
            incoming.extend(data["events"])
    all_events=q["events"]+incoming
    combined=compare_and_integrate(all_events,seed,p,root)
    reviews_dir=root/"v5/videos"
    reviews=sorted(reviews_dir.glob("v5_*_advisory_review.json")) if reviews_dir.is_dir() else []
    if reviews:
        seen={x["source_claim_id"] for x in all_events}
        for path in reviews:
            data=read(path)
            expected={x["id"] for x in data["claims"]}
            need(expected<=seen,
                 "new research lacks historical integration proposal for claims: "+
                 ",".join(sorted(expected-seen)[:8]))
    combined["incoming_event_count"]=len(incoming)
    combined["new_review_claims_covered"]=sum(len(read(p)["claims"]) for p in reviews)
    return combined

def synthetic_tests(root):
    """All simulated APPROVED items below have NO real completion certificate."""
    seed=read(root/BASE);policy=read(root/POLICY);q=read(root/QUEUE)
    events=q["events"]
    baseline=compare_and_integrate(events,seed,policy,root)
    rejects=0
    def no(cases, trusted=None):
        nonlocal rejects
        try:compare_and_integrate(cases,seed,policy,root,
               eligible=trusted if trusted is not None else set(),allow_synthetic=True)
        except (ValueError,TypeError,KeyError):
            rejects+=1
        else:
            raise ValueError("unsafe integration event was accepted")
    # Independent mutations: loss of actual source identity, predicate, privacy,
    # fake approval, wrong concept, a second relation, and suppressed conflicts.
    changes=[]
    x=copy.deepcopy(events);x[0]["source_claim_id"]="sz5N9WJS310-99";changes.append(x)
    x=copy.deepcopy(events);x[0]["source_blob_sha"]="0"*40;changes.append(x)
    x=copy.deepcopy(events);x[0]["relation"]="CORRECTION_ONLY";x[0]["review_state"]="APPROVED";changes.append(x)
    x=copy.deepcopy(events);x[4]["relation"]="SUPPORTS_UNDER_CONDITIONS";changes.append(x)
    x=copy.deepcopy(events);x[5]["relation"]="SUPPORTS_UNDER_CONDITIONS";changes.append(x)
    x=copy.deepcopy(events);x[6]["review_state"]="APPROVED";changes.append(x)
    x=copy.deepcopy(events);x[7]["target_concept_id"]="FAKE_CONCEPT";changes.append(x)
    x=copy.deepcopy(events);x[1]["source_path"]="../secret.json";changes.append(x)
    x=copy.deepcopy(events);x[3]["event_id"]=x[0]["event_id"];changes.append(x)
    x=copy.deepcopy(events);x[0]["assessment"]="Account 123456-1234567";changes.append(x)
    x=copy.deepcopy(events);x[4]["relation"]="SUPERSEDES";changes.append(x)
    x=copy.deepcopy(events);x[7]["relation"]="NEW_CONCEPT";changes.append(x)
    x=copy.deepcopy(events);x.append(copy.deepcopy(events[0]));x[-1]["event_id"]="V5-COMP-200";x[-1]["relation"]="QUALIFIES_SCOPE";changes.append(x)
    x=copy.deepcopy(events);x[1]["evidence_refs"]=["v5/nonexistent_proof.json"];changes.append(x)
    x=copy.deepcopy(events);x[4]["evidence_blob_shas"]["v5/research_progress/v5_001_models_20261030.json"]="0"*40;changes.append(x)
    x=copy.deepcopy(events);x[4]["evidence_blob_shas"]={};changes.append(x)
    for x in changes:no(x)
    need(rejects==16,"negative mutations incomplete")
    # Fictional user-accepted review/synthetic certificate authorization ONLY in memory.
    x=copy.deepcopy(events)
    approved=x[7]
    approved["review_state"]="APPROVED"
    approved["certificate_path"]="v5/completion/SYNTHETIC_ONLY.json"
    approved["semantic_review"]={
        "reviewer_reference":"SYNTHETIC_INDEPENDENT_REVIEW_TEST",
        "review_date":"2026-10-30",
        "equivalence_reason":"Synthetic exercise of scoped tax-basis qualifier",
        "scope_conditions":"No claim about an actual legal interpretation",
        "counterevidence_checked":"This is never a legal approval"}
    # The production path must reject an invented certificate even if a tester
    # supplies an otherwise plausible human-review assertion.
    try:
        compare_and_integrate(x,seed,policy,root)
    except (ValueError,KeyError,TypeError):
        rejects+=1
    else:
        raise ValueError("nonexistent real research completion certificate accepted")
    # To exercise the approved merge algorithm without an on-disk certificate,
    # inject a test-only read shim by creating fake in-memory approval path?
    # Do not bypass the file verifier for production. Instead build a
    # controlled view with the actual registered path once a real certificate exists.
    need(baseline["statistics"]["approved_overlays"]==0,
         "synthetic test accidentally published knowledge")
    successful=compare_and_integrate(x,seed,policy,root,
        eligible={"sz5N9WJS310-13"},allow_synthetic=True)
    need(successful["statistics"]["approved_overlays"]==1
         and successful["approved_new_distinct_evidence_claim_ids"]==
             ["sz5N9WJS310-13"]
         and successful["original_claims_overwritten"]==0
         and successful["canonical_baseline_mutated"] is False,
         "synthetic approved overlay did not safely accumulate knowledge")
    # Reviewed correction for known contradicted statement may be added ONLY
    # as correction-only link, never as positive financial advice.
    corrected=copy.deepcopy(events)
    ce=corrected[4]
    ce["review_state"]="APPROVED"
    ce["certificate_path"]="v5/completion/SYNTHETIC_ONLY.json"
    ce["semantic_review"]={
        "reviewer_reference":"SYNTHETIC_INDEPENDENT_REVIEW_TEST",
        "review_date":"2026-10-30",
        "equivalence_reason":"Simulation of correction-only, not actual academic validation",
        "scope_conditions":"No positive investment principle, synthetic test only",
        "counterevidence_checked":"Synthetic test fixture"}
    good=compare_and_integrate(corrected,seed,policy,root,
        eligible={"sz5N9WJS310-06"},allow_synthetic=True)
    row=next(v for v in good["decisions"] if v["event_id"]=="V5-COMP-005")
    need(row["state"]=="APPROVED_OVERLAY"
         and row["positive_knowledge_allowed"] is False
         and "V5-COMP-005" in good["concept_impact_flags"]["FORECAST_COMPOUND_RETURN"],
         "synthetic correction was promoted or lost impact dependency")
    # Existing claim replays remain idempotent.
    repeated=compare_and_integrate(events[:4],seed,policy,root)
    need(repeated["statistics"]["already_indexed"]==4 and
         repeated["approved_new_distinct_evidence_claim_ids"]==[],
         "idempotent historical replay failed")
    return {"negative_mutations_rejected":rejects+1,
            "real_historical_duplicate_replays":4,
            "real_pending_semantic_or_conflict_reviews":4,
            "synthetic_approval_without_real_completion_rejected":True,
            "synthetic_approved_overlay_and_correction_tested":2,
            "real_approved_knowledge_added":0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--preview",action="store_true")
    args=ap.parse_args()
    root=args.root.resolve()
    view=validate_repository(root)
    result={"gate":"PASS_STRUCTURAL_ONLY","historical_crosswalk_claims":view["historical_crosswalk_claims"],
            "historical_crosswalk_video_count":view["historical_crosswalk_video_count"],
            "historical_crosswalk_partitions":view["historical_crosswalk_partitions"],
            "historical_irregular_id_count":view["historical_irregular_id_count"],
            "historical_irregular_id_examples":view["historical_irregular_id_examples"],
            "baseline_concepts":view["baseline_concepts"],
            "baseline_distinct_claims":view["baseline_distinct_evidence_claims"],
            "incoming_event_count":view["incoming_event_count"],
            "new_review_claims_covered":view["new_review_claims_covered"],
            "statistics":view["statistics"],
            "unresolved_conflicts":view["active_unreviewed_conflicts"],
            "real_research_approvals":0}
    if args.self_test: result["selftest"]=synthetic_tests(root)
    if args.preview:result["decisions"]=view["decisions"]
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,OSError,IndexError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
