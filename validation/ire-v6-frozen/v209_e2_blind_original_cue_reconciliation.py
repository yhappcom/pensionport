"""V209 E2 — blind-to-V176 original-cue interpretation then disagreement audit.

The source-only challenge intentionally NEVER shows V176 labels, original atoms,
or prior knowledge to the reviewing ChatGPT. The returned ChatGPT response is
not an independent human gold set; all financial truth remains unapproved.
A second, deterministic pass compares that *already authored* response against
the pinned private V176 owner journal and returns HOLD for disagreements.
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing

from ire.v6.atomic_exchange import NUMBER
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession

PLAN="IRE_V209_E2_BLIND_ORIGINAL_SOURCE_TASK_V1"
ANSWER="IRE_V209_E2_BLIND_CHAT_MEANING_RESPONSE_V1"
RESULT="IRE_V209_E2_BLIND_V176_DISAGREEMENT_AUDIT_V1"
ACTS={
    "QUESTION_ONLY","QUESTION_WITH_EMBEDDED_ASSERTION",
    "QUOTE_ONLY","QUOTE_WITH_FACT_DEPENDENCY",
    "NON_RESEARCH_ONLY","FACT_ASSERTION","OPINION_ASSERTION",
    "HYPOTHESIS_ASSERTION","RECOMMENDATION_ASSERTION",
    "MIXED_ASSERTION","UNRESOLVED_MEANING",
}
NO_ATOMS={"QUESTION_ONLY","QUOTE_ONLY","NON_RESEARCH_ONLY"}
MUST_ATOMS={
    "QUESTION_WITH_EMBEDDED_ASSERTION","QUOTE_WITH_FACT_DEPENDENCY",
    "FACT_ASSERTION","OPINION_ASSERTION","HYPOTHESIS_ASSERTION",
    "RECOMMENDATION_ASSERTION","MIXED_ASSERTION",
}
KINDS={"FACT","OPINION","HYPOTHETICAL","RECOMMENDATION","QUESTION","MATH","ANECDOTE"}
ROLE={
    "QUESTION_ONLY":"QUESTIONED_NOT_ASSERTED",
    "QUOTE_ONLY":"QUOTED_NOT_ENDORSED",
    "QUESTION_WITH_EMBEDDED_ASSERTION":"QUESTIONED_NOT_ASSERTED",
    "QUOTE_WITH_FACT_DEPENDENCY":"QUOTED_NOT_ENDORSED",
    "FACT_ASSERTION":"ASSERTED_UNVERIFIED",
    "OPINION_ASSERTION":"OPINION_ONLY",
    "HYPOTHESIS_ASSERTION":"HYPOTHETICAL_ONLY",
    "RECOMMENDATION_ASSERTION":"RECOMMENDATION_ONLY",
}
LINK_FIELDS={"cue_index","source_quote","source_text_sha256"}
ATOM_FIELDS={
    "kind","proposition","source_quote","epistemic_role",
    "context_cue_indices","condition_links","exception_links",
    "rebuttal_links","numeric_references",
}
ROW_FIELDS={
    "cue_index","source_text_sha256","speech_act","original_quote",
    "analysis","analysis_sha256","atoms","cue_numeric_tokens",
    "audio_speaker_verified","financial_fact_approved",
}


def need(ok,reason):
    if not ok:
        raise InvalidInput("V209_E2_"+reason)


def blind_challenge(owner,*,expected_owner_head,start_cue=1,limit=20,context_radius=6):
    need(type(owner) is EngineChatSession,"V176_OWNER_REQUIRED")
    need(type(start_cue) is int and type(limit) is int and
         type(context_radius) is int and 1<=limit<=30 and
         0<=context_radius<=12 and 1<=start_cue<=len(owner.source.cues),
         "BLIND_RANGE")
    progress=owner.progress()
    need(progress["checkpoint_head_sha256"]==expected_owner_head,
         "OWNER_CHECKPOINT_CHANGED")
    last=min(start_cue+limit-1,len(owner.source.cues))
    cues=owner.source.cues
    context=range(max(1,start_cue-context_radius),
                  min(len(cues),last+context_radius)+1)
    task={
        "schema":PLAN,
        "source_sha256":owner.source.source_sha256,
        "manifest_sha256":owner.source.manifest_sha256,
        "owner_head_sha256":expected_owner_head,
        "start_cue":start_cue,"end_cue":last,
        "context_radius":context_radius,
        "target_cues":[{
            "cue_index":i,"original_text":cues[i-1].text,
            "source_text_sha256":sha256(cues[i-1].text.encode("utf-8")),
            "original_numeric_tokens":NUMBER.findall(cues[i-1].text),
        } for i in range(start_cue,last+1)],
        "surrounding_cues":[{
            "cue_index":i,"original_text":cues[i-1].text,
            "source_text_sha256":sha256(cues[i-1].text.encode("utf-8")),
        } for i in context],
        "v176_labels_present":False,
        "preexisting_candidate_claims_present":False,
        "blind_to_existing_financial_knowledge":True,
        "independent_external_reviewer_certified":False,
        "financial_facts_approved":False,
    }
    return {**task,"challenge_sha256":json_digest(task)}


def _source_link(link,cues):
    need(type(link) is dict and set(link)==LINK_FIELDS,
         "SOURCE_LINK_SCHEMA")
    i=link["cue_index"]
    need(type(i) is int and i in cues and
         link["source_text_sha256"]==cues[i]["source_text_sha256"] and
         type(link["source_quote"]) is str and
         len(link["source_quote"].strip())>=3 and
         link["source_quote"] in cues[i]["original_text"],
         "SOURCE_LINK_NOT_IN_CONTEXT")
    return i


def review_blind_and_reconcile(owner,challenge,answer,*,expected_owner_head):
    """Return mechanically certified differences, not an E2 quality PASS."""
    need(type(challenge) is dict and
         challenge.get("schema")==PLAN and
         challenge.get("challenge_sha256")==json_digest({
             k:v for k,v in challenge.items() if k!="challenge_sha256"}),
         "BLIND_CHALLENGE_HASH_OR_SCHEMA")
    expected=blind_challenge(
        owner,expected_owner_head=expected_owner_head,
        start_cue=challenge.get("start_cue"),
        limit=challenge.get("end_cue",0)-challenge.get("start_cue",0)+1
              if type(challenge.get("end_cue")) is int and
                 type(challenge.get("start_cue")) is int else 0,
        context_radius=challenge.get("context_radius"))
    need(challenge==expected,"BLIND_CHALLENGE_NOT_ORIGINAL")
    need(type(answer) is dict and set(answer)=={
        "schema","challenge_sha256","review_executor","responses",
        "independent_external_gold_certified",
        "financial_fact_truth_certified","e2_final_pass",
    } and answer["schema"]==ANSWER and
         answer["challenge_sha256"]==challenge["challenge_sha256"] and
         answer["review_executor"]=="CHATGPT_IN_CHAT" and
         answer["independent_external_gold_certified"] is False and
         answer["financial_fact_truth_certified"] is False and
         answer["e2_final_pass"] is False and
         type(answer["responses"]) is list and
         len(answer["responses"])==len(challenge["target_cues"]),
         "BLIND_ANSWER_SCHEMA_OR_CUE_CENSUS")
    cue_context={i["cue_index"]:i for i in challenge["surrounding_cues"]}
    counter=Counter()
    for original,row in zip(challenge["target_cues"],answer["responses"]):
        need(type(row) is dict and set(row)==ROW_FIELDS,
             "BLIND_REVIEW_ROW_FIELDS")
        i=original["cue_index"]
        need(row["cue_index"]==i and
             row["source_text_sha256"]==original["source_text_sha256"] and
             type(row["speech_act"]) is str and
             row["speech_act"] in ACTS and
             type(row["original_quote"]) is str and
             len(row["original_quote"].strip())>=3 and
             row["original_quote"] in original["original_text"] and
             type(row["analysis"]) is str and
             len(row["analysis"].strip())>=20 and
             row["analysis_sha256"]==sha256(row["analysis"].encode("utf-8")) and
             type(row["atoms"]) is list and
             type(row["cue_numeric_tokens"]) is list and
             row["cue_numeric_tokens"]==original["original_numeric_tokens"] and
             row["audio_speaker_verified"] is False and
             row["financial_fact_approved"] is False,
             "BLIND_ORIGINAL_QUOTE_NUMERIC_OR_REVIEWER_DRIFT")
        need((not row["atoms"] if row["speech_act"] in NO_ATOMS else
              bool(row["atoms"]) if row["speech_act"] in MUST_ATOMS else
              True),
             "BLIND_SPEECH_ACT_ATOM_CONSISTENCY")
        for atom in row["atoms"]:
            need(type(atom) is dict and set(atom)==ATOM_FIELDS,
                 "BLIND_ATOM_FRAME_SCHEMA")
            need(type(atom["kind"]) is str and
                 atom["kind"] in KINDS and
                 type(atom["proposition"]) is str and
                 len(atom["proposition"].strip())>=8 and
                 type(atom["source_quote"]) is str and
                 len(atom["source_quote"].strip())>=3 and
                 atom["source_quote"] in original["original_text"] and
                 type(atom["context_cue_indices"]) is list and
                 atom["context_cue_indices"]==
                    sorted(set(atom["context_cue_indices"])) and
                 i in atom["context_cue_indices"] and
                 all(type(k) is int and k in cue_context
                     for k in atom["context_cue_indices"]) and
                 type(atom["epistemic_role"]) is str,
                 "BLIND_ATOM_SOURCE_CONTEXT")
            required_role=ROLE.get(row["speech_act"])
            if required_role is not None and row["speech_act"] in MUST_ATOMS:
                need(atom["epistemic_role"]==required_role,
                     "BLIND_REPORTED_CLAIM_PROMOTED_TO_DIRECT_FACT")
            else:
                need(atom["epistemic_role"] in {
                    "QUESTIONED_NOT_ASSERTED","QUOTED_NOT_ENDORSED",
                    "ASSERTED_UNVERIFIED","OPINION_ONLY",
                    "HYPOTHETICAL_ONLY","RECOMMENDATION_ONLY",
                    "UNRESOLVED_MEANING",
                },"BLIND_EPISTEMIC_ROLE_INVALID")
            for key in ("condition_links","exception_links","rebuttal_links"):
                need(type(atom[key]) is list,
                     "BLIND_QUALIFIER_OR_REBUTTAL_LIST_MISSING")
                for link in atom[key]:
                    li=_source_link(link,cue_context)
                    need(li in atom["context_cue_indices"],
                         "BLIND_QUALIFIER_OUTSIDE_CONTEXT")
            refs=atom["numeric_references"]
            need(type(refs) is list and
                 all(type(r) is dict and set(r)=={"cue_index","token"}
                     for r in refs),"BLIND_NUMERIC_REFERENCE_SCHEMA")
            available=Counter()
            seen=Counter()
            for k in atom["context_cue_indices"]:
                available.update(NUMBER.findall(cue_context[k]["original_text"]))
            for r in refs:
                need(type(r["cue_index"]) is int and
                     r["cue_index"] in atom["context_cue_indices"] and
                     type(r["token"]) is str and
                     r["token"] in NUMBER.findall(
                         cue_context[r["cue_index"]]["original_text"]),
                     "BLIND_NUMERIC_NOT_FROM_ORIGINAL")
                seen[r["token"]]+=1
            need(all(seen[n]<=available[n] for n in seen) and
                 all(seen[n]>=count
                     for n,count in Counter(NUMBER.findall(
                         atom["proposition"])).items()),
                 "BLIND_NUMERIC_OMITTED_OR_INVENTED")
            counter["blind_atom_count"]+=1
            counter["blind_"+atom["kind"]]+=1
        counter["original_cues_checked"]+=1
        counter["blind_"+row["speech_act"]]+=1
    # Only after source-only review is fully validated can the historical
    # V176 ledger be revealed for disagreement detection.
    with closing(owner._connect()) as db:
        current,old=owner._audit(db)
    need(current==expected_owner_head,
         "OWNER_CHANGED_BEFORE_RECONCILIATION")
    discrepancies=[]
    def mark(cue,reason,details=None):
        discrepancies.append({"cue_index":cue,"reason":reason,
                              "details":details})
    for row in answer["responses"]:
        i=row["cue_index"]
        orig=old.get(i)
        if orig is None or orig[1]["disposition"]=="OPEN":
            mark(i,"UNREVIEWED_OR_OPEN_V176_CUE")
            continue
        decision=orig[1]
        prior=decision["claims"]
        blind=row["atoms"]
        kind=decision["disposition"]
        if row["speech_act"]=="UNRESOLVED_MEANING":
            mark(i,"BLIND_SOURCE_MEANING_STILL_UNRESOLVED")
        if (kind=="QUESTION" and
            row["speech_act"] not in {
                "QUESTION_ONLY","QUESTION_WITH_EMBEDDED_ASSERTION",
                "UNRESOLVED_MEANING"} or
            kind=="QUOTE" and
            row["speech_act"] not in {
                "QUOTE_ONLY","QUOTE_WITH_FACT_DEPENDENCY",
                "UNRESOLVED_MEANING"} or
            kind=="NON_RESEARCH" and
            row["speech_act"] not in {
                "NON_RESEARCH_ONLY","UNRESOLVED_MEANING"} or
            kind=="ASSERTION" and
            row["speech_act"] in NO_ATOMS):
            mark(i,"SOURCE_SPEECH_ACT_DISAGREEMENT",
                 {"original_v176_disposition":kind,
                  "blind_speech_act":row["speech_act"]})
        if kind in {"QUESTION","QUOTE","NON_RESEARCH"} and blind:
            mark(i,"ATOM_HIDDEN_BY_V176_NONASSERTION",
                 {"v176_disposition":kind,"blind_count":len(blind)})
        if kind=="ASSERTION" and not blind:
            mark(i,"BLIND_DID_NOT_CONFIRM_V176_ASSERTION",
                 {"prior_claims":len(prior)})
        if kind=="ASSERTION" and blind and len(prior)!=len(blind):
            mark(i,"ATOMIC_CLAIM_COUNT_DISAGREEMENT",
                 {"prior_claims":len(prior),"blind_claims":len(blind)})
        for j,(before,after) in enumerate(zip(prior,blind),1):
            if before["kind"]!=after["kind"]:
                mark(i,"CLAIM_KIND_DISAGREEMENT",
                     {"ordinal":j,"previous_kind":before["kind"],
                      "blind_kind":after["kind"]})
            for native,blind_field in (
                    ("conditions","condition_links"),
                    ("exceptions","exception_links")):
                source_terms=before[native]
                independently_cited=[
                    l["source_quote"] for l in after[blind_field]]
                if (len(source_terms)!=len(independently_cited) or
                    any(not any(s in q or q in s
                                for q in independently_cited)
                        for s in source_terms)):
                    mark(i,"CONDITION_EXCEPTION_SOURCE_DISAGREEMENT",
                         {"ordinal":j,"qualifier_type":native,
                          "v176_terms":len(source_terms),
                          "blind_source_links":len(independently_cited)})
            if after["rebuttal_links"]:
                mark(i,"SOURCE_REBUTTAL_LINK_REQUIRES_EXPLICIT_RECONCILIATION",
                     {"ordinal":j,
                      "link_count":len(after["rebuttal_links"])})
        if kind=="ASSERTION" and any(p["kind"]=="ANECDOTE" for p in prior):
            mark(i,"ANECDOTE_NOT_PROJECTABLE_IN_V6")
        # Even if V176 had no atoms, new E2-only rebuttal links need
        # explicit resolution. Do not let the zip(prior,blind) suppress them.
        for ordinal,blind_atom in enumerate(blind[len(prior):],len(prior)+1):
            if blind_atom["rebuttal_links"]:
                mark(i,"NEW_BLIND_DISCOURSE_NEEDS_V176_RECHECK",
                     {"ordinal":ordinal,
                      "link_count":len(blind_atom["rebuttal_links"])})
    need(owner.progress()["checkpoint_head_sha256"]==expected_owner_head,
         "OWNER_CHANGED_AFTER_RECONCILIATION")
    return {
        "schema":RESULT,"source_sha256":owner.source.source_sha256,
        "owner_head_sha256":expected_owner_head,
        "blind_challenge_sha256":challenge["challenge_sha256"],
        "blind_response_sha256":json_digest(answer),
        "blind_original_cues_checked":counter["original_cues_checked"],
        "blind_original_claims_proposed":counter["blind_atom_count"],
        "counts":dict(counter),
        "disagreements":discrepancies,
        "disagreement_count":len(discrepancies),
        "status":("HOLD_FOR_CHAT_DISAGREEMENT_ADJUDICATION"
                  if discrepancies else
                  "BLIND_V176_CONCORDANT_UNCERTIFIED_SEMANTIC_GOLD"),
        "independent_external_gold_certified":False,
        "automated_precision_recall_certified":False,
        "e2_final_pass":False,"e3_e4_e5_authorized":False,
        "original_v176_mutated":False,"financial_knowledge_published":False,
    }


def reconcile_full_blind_video(owner, reviewed_batches, *, expected_owner_head):
    """Require 1:1 coverage of EVERY source cue by independently authored batches."""
    need(type(reviewed_batches) is list and bool(reviewed_batches),
         "FULL_BLIND_BATCHES_REQUIRED")
    observed=set()
    receipts=[]
    for batch in reviewed_batches:
        need(type(batch) is dict and set(batch)=={"challenge","answer"},
             "FULL_BLIND_BATCH_SCHEMA")
        c=batch["challenge"]
        r=review_blind_and_reconcile(
            owner,c,batch["answer"],
            expected_owner_head=expected_owner_head)
        ids=set(range(c["start_cue"],c["end_cue"]+1))
        need(not (observed & ids),"FULL_BLIND_CUE_DOUBLE_COUNT")
        observed.update(ids)
        receipts.append(r)
    need(observed==set(range(1,len(owner.source.cues)+1)),
         "FULL_BLIND_SOURCE_CUE_MISSING")
    all_gaps=[item for receipt in receipts
              for item in receipt["disagreements"]]
    return {
        "schema":"IRE_V209_E2_FULL_BLIND_SOURCE_RECONCILIATION_V1",
        "source_sha256":owner.source.source_sha256,
        "owner_head_sha256":expected_owner_head,
        "original_cues_covered":len(observed),
        "source_batches":len(receipts),
        "blind_claims_proposed":sum(r["blind_original_claims_proposed"]
                                     for r in receipts),
        "semantic_disagreements":len(all_gaps),
        "disagreements":all_gaps,
        "status":("HOLD_BLIND_SOURCE_DISAGREEMENT_AND_GOLD"
                  if all_gaps else "HOLD_INDEPENDENT_GOLD_STILL_REQUIRED"),
        "actual_independent_human_gold_available":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
    }
