"""V149 accountable source-cue/atomic semantic scoring; no manufactured P0 GO.

Reviewers may submit a fully enumerated SAME-GRANULARITY blind gold and a
one-to-one adjudication. This checker measures decisions, never invents them.
A selected segment from the same ChatGPT receives an INTERNAL label, not an
independent accuracy certificate or full owner-video release.
"""
from __future__ import annotations
import hashlib, json, re
from collections import Counter

SHA = re.compile(r"[0-9a-f]{64}\Z")
ROLES = {"ASSERTION", "QUESTION", "CONTEXT", "EXCEPTION", "REBUTTAL", "CONDITION", "QUOTE", "NON_SPEECH", "OPEN"}

class GoldEvidenceError(ValueError):
    pass

def _assert(ok, reason):
    if not ok: raise GoldEvidenceError("V149_GOLD_"+reason)

def score(gold:dict, prediction:dict, adjudication:dict, *, original_cues:list,
          expected_scope:tuple[int,int], original_source_sha256:str,
          whole_video_cue_count:int=1481)->dict:
    """Exact atomic matching; composite/merged units count FP and independent FNs.

    The source-cue audit is required for *all* cues of the declared scope.
    Gold truth depends on ChatGPT/human review; the code cannot certify it.
    """
    first,last=expected_scope
    _assert(type(first) is int and type(last) is int and 1<=first<=last<=whole_video_cue_count,"SCOPE_INVALID")
    _assert(type(gold) is dict and type(prediction) is dict and type(adjudication) is dict,"REQUIRED_PACKETS_MISSING")
    _assert(gold.get("schema")=="IRE_V149_SOURCE_FIRST_GOLD_V1" and prediction.get("schema")=="IRE_V149_PRIOR_V6_PREDICTION_V1" and adjudication.get("schema")=="IRE_V149_EXACT_ATOMIC_ADJUDICATION_V1","SCHEMA_DRIFT")
    _assert(gold.get("source_sha256")==original_source_sha256 and prediction.get("source_sha256")==original_source_sha256 and adjudication.get("source_sha256")==original_source_sha256,"SOURCE_DRIFT")
    _assert(gold.get("scope")==[first,last] and prediction.get("scope")==[first,last] and adjudication.get("scope")==[first,last],"SCOPE_DRIFT")
    _assert(type(original_cues) is list and len(original_cues)==last-first+1,"OWNER_CUES_MISSING")
    _assert([r.get("cue_index") for r in original_cues]==list(range(first,last+1)),"OWNER_CUE_DISCONTIGUOUS")
    _assert(all(type(r.get("text")) is str and r.get("sha256")==hashlib.sha256(r["text"].encode()).hexdigest() for r in original_cues),"OWNER_CUE_TAMPERED")
    gold_rows=gold.get("cue_dispositions")
    _assert(type(gold_rows) is list and len(gold_rows)==len(original_cues),"GOLD_NOT_FULL_CUE_CENSUS")
    for row,orig in zip(gold_rows,original_cues):
        _assert(type(row) is dict and row.get("cue_index")==orig["cue_index"] and row.get("cue_text_sha256")==orig["sha256"] and row.get("role") in ROLES and isinstance(row.get("review_note"),str) and row["review_note"],"GOLD_CUE_ROLE_UNPINNED")
    gold_units=gold.get("atoms"); pred_units=prediction.get("atoms")
    _assert(type(gold_units) is list and type(pred_units) is list,"ATOM_LISTS_MISSING")
    def check_atoms(items,k):
        checked={}
        for a in items:
            _assert(type(a) is dict and type(a.get(k)) is str and a[k] not in checked,"DUPLICATE_ATOM_ID")
            _assert(type(a.get("proposition")) is str and len(a["proposition"].strip())>=8,"PROPOSITION_MISSING")
            cues=a.get("cue_indices")
            _assert(type(cues) is list and cues==sorted(set(cues)) and all(type(x) is int and first<=x<=last for x in cues) and cues,"ATOM_CUE_OUTSIDE_SCOPE")
            _assert(type(a.get("high_risk")) is bool,"HIGH_RISK_CLASSIFICATION_MISSING")
            checked[a[k]]=a
        return checked
    g=check_atoms(gold_units,"gold_id");p=check_atoms(pred_units,"predicted_id")
    matching=adjudication.get("exact_matches")
    _assert(type(matching) is list,"MATCHES_MISSING")
    used_g=set();used_p=set()
    for m in matching:
        _assert(type(m) is dict and set(m)=={"gold_id","predicted_id","proposition_and_conditions_equivalent","chat_decision_sha256"},"MATCH_SCHEMA")
        gid=m["gold_id"];pid=m["predicted_id"]
        _assert(gid in g and pid in p and gid not in used_g and pid not in used_p,"MATCH_NOT_ONE_TO_ONE")
        _assert(m["proposition_and_conditions_equivalent"] is True,"PARTIAL_CANNOT_BE_TP")
        _assert(isinstance(m["chat_decision_sha256"],str) and SHA.fullmatch(m["chat_decision_sha256"]),"MATCH_NOT_CHAT_REVIEWED")
        used_g.add(gid);used_p.add(pid)
    _assert(adjudication.get("unmatched_gold_ids")==sorted(set(g)-used_g) and adjudication.get("unmatched_prediction_ids")==sorted(set(p)-used_p),"UNMATCHED_CENSUS_NOT_COMPLETE")
    _assert(adjudication.get("review_executor")=="CHATGPT_IN_CHAT" and adjudication.get("reviewer_fully_checked_scope") is True,"ADJUDICATOR_NOT_ATTESTED")
    tp=len(matching);fp=len(p)-tp;fn=len(g)-tp
    high_fn=sum(g[k]["high_risk"] for k in set(g)-used_g)
    internal=gold.get("review_independence")=="SAME_CHAT_SOURCE_FIRST_NOT_EXTERNAL"
    return {"schema":"IRE_V149_ATOMIC_SCORE_V1","source_scope":[first,last],"source_cues_audited":len(original_cues),
            "tp_exact":tp,"fp_unmatched":fp,"fn_unmatched":fn,"high_risk_fn_unmatched":high_fn,
            "precision":round(tp/(tp+fp),6) if tp+fp else None,
            "recall":round(tp/(tp+fn),6) if tp+fn else None,
            "evaluation_type":"INTERNAL_SAME_CHAT_ATOMIC_SLICE" if internal else "REVIEW_SOURCE_EXTERNAL_STATUS_UNVERIFIED",
            "full_video_complete":first==1 and last==whole_video_cue_count,
            "independently_certified":False,
            "claim_granularity_checked_by_human_or_chat_not_by_code":True,
            "p0_e_pass":False,"p0_go":False,
            "status":"EXACT_ATOMIC_SCOPE_MEASURED_NOT_FULL_VIDEO_P0_CERTIFIED"}
