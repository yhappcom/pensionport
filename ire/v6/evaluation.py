"""V6-6 source-grounded blind evaluation *arithmetic*, not human attestation.

The evaluator verifies exact source references and alignment accounting, never
infers semantic truth. Reviewers and blind identity must be verified outside
this module. No self-declared independent=True can produce engine quality GO.
"""
from __future__ import annotations

import re
from decimal import Decimal, localcontext, ROUND_HALF_UP
from .codec import json_digest, require_hash
from .errors import InvalidInput
from .source import verify_source

GOLD_ID = re.compile(r"G[0-9]{5,8}\Z")
PRED_ID = re.compile(r"C[0-9]{5,8}\Z")
PERSON_ID = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")
CATEGORIES = frozenset({"TAX", "PENSION", "LEVERAGE", "RETURN", "OTHER"})
HIGH_RISK = frozenset({"TAX", "PENSION", "LEVERAGE", "RETURN"})
FIELDS = frozenset({"modality", "conditions", "exceptions", "measurements", "speaker_attribution", "effective_date"})


def _ident(value, pattern, error):
    if type(value) is not str or not pattern.fullmatch(value):
        raise InvalidInput(error)
    return value


def _ratio(n, d):
    return {"numerator": n, "denominator": d, "parts_per_million":
            (n*1000000+d//2)//d if d else None}


def _wilson95(n, d):
    """Reproducible Wilson intervals, integers in ppm (no JSON floats)."""
    if not d:
        return None
    with localcontext() as ctx:
        ctx.prec=45
        z=Decimal("1.959963984540")
        z2=z*z
        p=Decimal(n)/Decimal(d)
        denom=Decimal(1)+z2/Decimal(d)
        center=(p+z2/(2*Decimal(d)))/denom
        radius=(z*((p*(1-p)+z2/(4*Decimal(d)))/Decimal(d)).sqrt())/denom
        lower=max(Decimal(0),center-radius)
        upper=min(Decimal(1),center+radius)
        return {"lower_ppm":int((lower*1000000).to_integral_value(rounding=ROUND_HALF_UP)),
                "upper_ppm":int((upper*1000000).to_integral_value(rounding=ROUND_HALF_UP))}


def _source_refs(src, refs, error):
    if type(refs) is not list or not 1 <= len(refs) <= 80:
        raise InvalidInput(error + "_COUNT")
    seen=[]
    for ref in refs:
        if type(ref) is not dict or set(ref) != {"cue_index", "quote"}:
            raise InvalidInput(error + "_SCHEMA")
        n, quote = ref["cue_index"], ref["quote"]
        if (type(n) is not int or not 1 <= n <= len(src.cues) or
            type(quote) is not str or len(quote.strip()) < 2 or
            " ".join(quote.casefold().split()) not in
              " ".join(src.cues[n-1].text.casefold().split())):
            raise InvalidInput(error + "_NOT_IN_SOURCE")
        seen.append(n)
    if seen != sorted(set(seen)):
        raise InvalidInput(error + "_NOT_SORTED_UNIQUE")
    return seen


def validate_plan(src, plan):
    if type(plan) is not dict or set(plan) != {
        "schema", "video_id", "source_sha256", "manifest_sha256", "window_ids",
        "sampling_protocol", "rubric_version", "gold_commitment_sha256",
        "reviewer_protocol_sha256", "precision_min_ppm",
        "recall_min_ppm", "high_risk_recall_min_ppm", "gold_sealed_before_predictions"
    } or plan["schema"] != "IRE_V6_BLIND_EVAL_PLAN_V1":
        raise InvalidInput("BLIND_PLAN_SCHEMA_INVALID")
    if any(plan[k] != getattr(src, v) for k,v in (
        ("video_id","video_id"),("source_sha256","source_sha256"),
        ("manifest_sha256","manifest_sha256"))):
        raise InvalidInput("BLIND_PLAN_SOURCE_DRIFT")
    wins=[w for w,_,_ in src.primary_windows]
    if (type(plan["window_ids"]) is not list or plan["window_ids"] != wins or
        type(plan["sampling_protocol"]) is not str or
        not 12 <= len(plan["sampling_protocol"]) <= 500 or
        type(plan["rubric_version"]) is not str or
        not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}",plan["rubric_version"]) or
        plan["gold_sealed_before_predictions"] is not True):
        raise InvalidInput("BLIND_PLAN_SCOPE_OR_PRECOMMITMENT_INVALID")
    require_hash(plan["gold_commitment_sha256"],"GOLD_PRECOMMITMENT")
    require_hash(plan["reviewer_protocol_sha256"],"REVIEWER_PROTOCOL_PIN")
    for name in ("precision_min_ppm", "recall_min_ppm", "high_risk_recall_min_ppm"):
        if type(plan[name]) is not int or not 0 <= plan[name] <= 1000000:
            raise InvalidInput("BLIND_PLAN_THRESHOLD_INVALID")
    return json_digest(plan)


def _atoms(src, doc, *, gold):
    schema="IRE_V6_BLIND_GOLD_V1" if gold else "IRE_V6_BLIND_PREDICTIONS_V1"
    keys={"schema", "video_id", "source_sha256", "claims"}
    if type(doc) is not dict or set(doc) != keys or doc["schema"] != schema or \
       doc["video_id"] != src.video_id or doc["source_sha256"] != src.source_sha256:
        raise InvalidInput("BLIND_ATOMS_SOURCE_OR_SCHEMA_INVALID")
    claims=doc["claims"]
    if type(claims) is not list or not 1 <= len(claims) <= 2000:
        raise InvalidInput("BLIND_ATOMS_SIZE_INVALID")
    ids=set(); byid={}
    for c in claims:
        id_field="gold_id" if gold else "claim_id"
        if type(c) is not dict or set(c)!={id_field,"category","proposition","source_refs","frame"}:
            raise InvalidInput("BLIND_ATOM_SHAPE_INVALID")
        cid=_ident(c[id_field], GOLD_ID if gold else PRED_ID,"BLIND_ATOM_ID_INVALID")
        if cid in ids:
            raise InvalidInput("BLIND_DUPLICATE_ATOM_ID")
        ids.add(cid)
        if type(c["category"]) is not str or c["category"] not in CATEGORIES or type(c["proposition"]) is not str or \
           len(c["proposition"].strip()) < 5:
            raise InvalidInput("BLIND_ATOM_CATEGORY_OR_PROPOSITION_INVALID")
        _source_refs(src,c["source_refs"],"BLIND_ATOM_CUE")
        if type(c["frame"]) is not dict or set(c["frame"])!=FIELDS or \
           not all(type(v) is str for v in c["frame"].values()):
            raise InvalidInput("BLIND_ATOM_FRAME_INVALID")
        byid[cid]=c
    return byid


def measure_blind(raw, manifest, plan, gold, predictions, matching):
    """Compute strict per-category confusion counts from a *supplied* adjudication.

    Arithmetic is checked; true independence and whether alignment verdicts
    are correct cannot be established by this module. This result is NOT GO.
    """
    if type(manifest) is not dict:
        raise InvalidInput("BLIND_MANIFEST_REQUIRED")
    src=verify_source(raw, manifest, expected_source_sha256=manifest.get("source_sha256"),
                      expected_manifest_sha256=json_digest(manifest))
    psha=validate_plan(src,plan)
    for doc in (gold, predictions, matching):
        if type(doc) is not dict:
            raise InvalidInput("BLIND_DOCUMENT_TYPE_INVALID")
    if json_digest(gold) != plan["gold_commitment_sha256"]:
        raise InvalidInput("BLIND_GOLD_POST_PREDICTION_SUBSTITUTION")
    gold_ids=_atoms(src,gold,gold=True)
    pred_ids=_atoms(src,predictions,gold=False)
    if set(matching)!={"schema","plan_sha256","gold_sha256","predictions_sha256",
                        "adjudicator_id","pairs","all_claims_compared"} or \
       matching["schema"]!="IRE_V6_BLIND_ALIGNMENT_V1" or \
       matching["plan_sha256"]!=psha or \
       matching["gold_sha256"]!=json_digest(gold) or \
       matching["predictions_sha256"]!=json_digest(predictions) or \
       matching["all_claims_compared"] is not True:
        raise InvalidInput("BLIND_ALIGNMENT_NOT_BOUND_TO_FROZEN_INPUTS")
    _ident(matching["adjudicator_id"],PERSON_ID,"BLIND_ADJUDICATOR_ID_INVALID")
    pairs=matching["pairs"]
    if type(pairs) is not list or len(pairs)>min(len(gold_ids),len(pred_ids)):
        raise InvalidInput("BLIND_ALIGNMENT_PAIRS_INVALID")
    used_g=set();used_p=set();exact=[];partial=0
    for row in pairs:
        if type(row) is not dict or set(row)!={"gold_id","predicted_id","verdict","field_verdicts"}:
            raise InvalidInput("BLIND_PAIR_SHAPE_INVALID")
        gid,pid=row["gold_id"],row["predicted_id"]
        if gid not in gold_ids or pid not in pred_ids or gid in used_g or pid in used_p:
            raise InvalidInput("BLIND_PAIR_MISSING_OR_DUPLICATED")
        used_g.add(gid);used_p.add(pid)
        if row["verdict"] not in ("EXACT","PARTIAL","INCORRECT") or \
           type(row["field_verdicts"]) is not dict or \
           set(row["field_verdicts"])!=FIELDS or \
           any(v not in ("CORRECT","INCORRECT","UNDETERMINED") for v in row["field_verdicts"].values()):
            raise InvalidInput("BLIND_PAIR_VERDICT_INVALID")
        if row["verdict"]=="EXACT":
            if (gold_ids[gid]["category"]!=pred_ids[pid]["category"] or
                any(v!="CORRECT" for v in row["field_verdicts"].values())):
                raise InvalidInput("BLIND_FALSE_EXACT_FRAME_OR_CATEGORY")
            exact.append((gid,pid))
        elif row["verdict"]=="PARTIAL":partial+=1
    tp=len(exact); pn=len(pred_ids); gn=len(gold_ids)
    counts={"tp":tp,"fp":pn-tp,"fn":gn-tp,"predictions":pn,"gold":gn}
    by_category={}
    for cat in sorted(CATEGORIES):
        pset={cid for cid,item in pred_ids.items() if item["category"]==cat}
        gset={cid for cid,item in gold_ids.items() if item["category"]==cat}
        t=sum(1 for g,p in exact if g in gset and p in pset)
        by_category[cat]={"tp":t,"fp":len(pset)-t,"fn":len(gset)-t,
                          "precision":_ratio(t,len(pset)),"recall":_ratio(t,len(gset))}
    gp=sum(len([g for g in gold_ids.values() if g["category"]==cat]) for cat in HIGH_RISK)
    hp=sum(by_category[cat]["tp"] for cat in HIGH_RISK)
    prec=_ratio(tp,pn); recall=_ratio(tp,gn); high=_ratio(hp,gp)
    thresholds=(prec["parts_per_million"]>=plan["precision_min_ppm"] and
                recall["parts_per_million"]>=plan["recall_min_ppm"] and
                high["parts_per_million"] is not None and
                high["parts_per_million"]>=plan["high_risk_recall_min_ppm"])
    return {"schema":"IRE_V6_BLIND_ARITHMETIC_V1","source_sha256":src.source_sha256,
            "plan_sha256":psha,"gold_sha256":json_digest(gold),
            "predictions_sha256":json_digest(predictions),
            "alignment_sha256":json_digest(matching),"counts":counts,
            "precision":prec,"recall":recall,"high_risk_recall":high,
            "by_category":by_category,"partial_pairs":partial,
            "precision_wilson_95":_wilson95(tp,pn),
            "recall_wilson_95":_wilson95(tp,gn),
            "high_risk_recall_wilson_95":_wilson95(hp,gp),
            "pre_registered_thresholds_met_arithmetically":thresholds,
            "actual_reviewer_identity_verified":False,
            "actual_blindness_independently_verified":False,
            "gold_completeness_independently_verified":False,
            "semantic_accuracy_certified":False,"engine_quality_certified":False,
            "p0_go":False,"status":"ADJUDICATION_INPUT_UNVERIFIED"}
