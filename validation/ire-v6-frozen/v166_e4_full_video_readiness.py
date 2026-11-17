"""E4 full-video blocker census. Diagnostic, NEVER a V123 replacement.

Source and original revision inputs are supplied privately. Each original
claim/manifest/cue is re-hashed. OPEN atoms, legacy risk counters and actual
unadjudicated omissions are reported separately. No status gets changed.
"""
import hashlib
import json
import re
from collections import Counter

def digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,
        separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()

def h(b):
    return hashlib.sha256(b).hexdigest()

def need(ok,reason):
    if not ok:
        raise ValueError("E4_VIDEO_READINESS_"+reason)

def audit_video_readiness(raw, cues, segments, *, expected_source_sha256):
    """cues: owner-parsed {absolute cue index: text}; segments: plan, exchange,
    V123 review, host receipt, legacy risk provenance (metadata only).
    Host pins are checked here but actual durable host verification and
    native semantic adjudication remain separate required gates.
    """
    need(type(raw) is bytes and type(cues) is dict and bool(cues)
         and set(cues)==set(range(1,len(cues)+1))
         and all(type(t) is str for t in cues.values()),"SOURCE_CENSUS")
    need(type(segments) is list and bool(segments),"NO_SEGMENTS")
    source=h(raw)
    need(source==expected_source_sha256,"OWNER_SOURCE_PIN_MISMATCH")
    # Reparse the raw SRT text independently of the supplied cue mapping.
    # This is text-census verification, not the native V6 timing/host audit.
    parsed={}
    for block in re.split(r"\n\s*\n",raw.decode("utf-8-sig").replace(
            "\r\n","\n").replace("\r","\n").strip()):
        lines=block.split("\n")
        need(len(lines)>=3 and lines[0].strip().isdecimal()
             and int(lines[0].strip())==len(parsed)+1
             and "-->" in lines[1],"RAW_SRT_BLOCK_OR_ORDER")
        value=" ".join(t.strip() for t in lines[2:] if t.strip())
        need(bool(value),"RAW_SRT_EMPTY_TEXT")
        parsed[int(lines[0].strip())]=value
    need(parsed==cues,"CUE_MAP_NOT_RAW_SOURCE_TEXT")
    seen_claims=set()
    seen_segments=set()
    previous=0
    result=[]
    excluded_cues=set()
    accepted_dependencies={}
    for item in segments:
        sid=item["segment_id"]
        plan=item["plan"]
        exchange=item["exchange"]
        review=item["review"]
        host=item["host"]
        need(type(sid) is str and sid not in seen_segments,"DUPLICATE_SEGMENT")
        seen_segments.add(sid)
        first,last=plan["scope"]["first_cue"],plan["scope"]["last_cue"]
        mp=digest(plan)
        need(plan["cue_count"]==len(cues) and first==previous+1
             and first<=last<=len(cues),"GAP_OR_OVERLAP")
        previous=last
        need(plan["source_sha256"]==source
             and exchange["source_sha256"]==source
             and review["source_sha256"]==source
             and exchange["manifest_sha256"]==mp
             and review["manifest_sha256"]==mp
             and host["event_sha256"]==review["host_event_sha256"]
             and host["bundle_sha256"]==review["host_bundle_sha256"]
             and host["atomic_batch_committed"] is True,
             "FROZEN_SOURCE_MANIFEST_HOST_MISMATCH")
        rows=review["source_cues"]
        need([r["cue_index"] for r in rows]==list(range(first,last+1))
             and all(r["cue_text_sha256"]==h(cues[r["cue_index"]].encode("utf-8"))
                     and r["status"] in {"REVIEWED","OPEN","EXCLUDED_FROM_RESEARCH"}
                     for r in rows),"CUE_ORDER_HASH_OR_STATUS")
        excluded={r["cue_index"] for r in rows if r["status"]=="EXCLUDED_FROM_RESEARCH"}
        excluded_cues.update(excluded)
        a=exchange["atoms"]
        v=review["atom_verdicts"]
        atoms={r["claim_id"]:r for r in a}
        verdicts={r["claim_id"]:r for r in v}
        need(len(atoms)==len(a)==len(v)==len(verdicts)
             and set(atoms)==set(verdicts) and not seen_claims.intersection(atoms),
             "CLAIM_CENSUS_OR_DUPLICATE_CROSS_SEGMENT")
        seen_claims.update(atoms)
        counts=Counter()
        open_high=[]
        ref_count=0
        for cid,atom in atoms.items():
            row=verdicts[cid]
            need(row["atom_sha256"]==digest(atom),"ATOM_DIGEST_DRIFT")
            ctx=atom["context_cue_indices"]
            need(type(ctx) is list and bool(ctx) and all(
                type(i) is int and first<=i<=last for i in ctx),"CONTEXT_SCOPE")
            refs=atom["source_refs"]
            need(type(refs) is list and bool(refs) and all(
                 r["cue_index"] in ctx and r["cue_index"] in cues
                 and type(r["quote"]) is str and bool(r["quote"])
                 and r["quote"] in cues[r["cue_index"]] for r in refs),
                 "SOURCE_REF_DRIFT")
            ref_count+=len(refs)
            status=row["status"]
            need(status in {"OPEN","REJECT","EXCLUDE_FROM_RESEARCH",
                            "ACCEPT_FOR_RESEARCH"},"UNKNOWN_STATUS")
            counts[status]+=1
            if status=="OPEN" and row["high_risk"]:
                open_high.append(cid)
            if status=="ACCEPT_FOR_RESEARCH":
                accepted_dependencies[cid]=set(ctx)
        historical_count=review["unresolved_high_risk_omissions"]
        need(type(historical_count) is int and historical_count>=0,"LEGACY_RISK_COUNTER")
        result.append({
            "segment_id":sid,"first_cue":first,"last_cue":last,
            "original_review_sha256":digest(review),
            "original_exchange_sha256":digest(exchange),
            "source_ref_count":ref_count,
            "accepted_candidate_count":counts["ACCEPT_FOR_RESEARCH"],
            "open_atom_count":counts["OPEN"],
            "excluded_atom_count":counts["EXCLUDE_FROM_RESEARCH"],
            "rejected_atom_count":counts["REJECT"],
            "open_high_risk_atom_count":len(open_high),
            "open_high_risk_atom_ids":sorted(open_high),
            "legacy_unresolved_high_risk_omissions_field":historical_count,
            "legacy_field_equals_open_high_risk_count":historical_count==len(open_high),
            "independent_missing_high_risk_claim_count":None,
            "excluded_cue_count":len(excluded),
            "open_cue_count":sum(r["status"]=="OPEN" for r in rows),
            "disagreements_adjudicated":review["disagreements_adjudicated"],
            "native_final_pass_proven_by_this_audit":False,
        })
    need(previous==len(cues),"TRAILING_SOURCE_GAP")
    cross=sorted(cid for cid,ctx in accepted_dependencies.items()
                 if ctx&excluded_cues)
    totals={field:sum(r[field] for r in result) for field in (
        "source_ref_count","accepted_candidate_count","open_atom_count",
        "excluded_atom_count","rejected_atom_count","open_high_risk_atom_count",
        "legacy_unresolved_high_risk_omissions_field","excluded_cue_count",
        "open_cue_count")}
    return {
        "schema":"IRE_V166_E4_WHOLE_VIDEO_READINESS_DIAGNOSTIC_V1",
        "owner_source_sha256":source,"source_cue_count":len(cues),
        "segment_count":len(result),"distinct_claim_count":len(seen_claims),
        "segments":result,"totals":totals,
        "accepted_candidate_ids_touching_excluded_cue":cross,
        "legacy_risk_counter_not_independent_missing_claim_census":True,
        "actual_independent_high_risk_false_negative_count":None,
        "legacy_review_modified":False,
        "native_v123_approval_granted":False,
        "real_knowledge_publication_authorized":False,
        "e5_authorized":False,
    }
