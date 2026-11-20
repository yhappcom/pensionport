"""V206 E2: source-first full-cue semantic challenge and fail-closed audit.

E1's native route is frozen. E2 requires independently authored ChatGPT
semantic *responses* for EVERY original cue, including QUESTION/QUOTE/NO_ATOM.
This validator cannot infer speech acts or approve financial facts. The hash
is custody, not an independent gold label or model signature. No model API.
"""
from __future__ import annotations

from collections import Counter
from ire.v6.atomic_exchange import NUMBER
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession

PLAN="IRE_V206_E2_FULL_CUE_MEANING_CHALLENGE_V1"
ANSWER="IRE_V206_E2_FULL_CUE_MEANING_RESPONSE_V1"
RESULT="IRE_V206_E2_FULL_CUE_MEANING_AUDIT_V1"
SPEECH_ACTS={
    "QUESTION_ONLY","QUESTION_WITH_EMBEDDED_ASSERTION",
    "QUOTE_ONLY","QUOTE_WITH_FACT_DEPENDENCY","NON_RESEARCH_ONLY",
    "FINANCIAL_FACT_ASSERTION","OTHER_FACT_ASSERTION",
    "OPINION_ASSERTION","HYPOTHESIS_ASSERTION","RECOMMENDATION_ASSERTION",
    "MIXED_ASSERTION","UNRESOLVED_MEANING",
}
CUE_NUMBER_ROLES={"QUANTITY_SPOKEN_UNVERIFIED","ASR_NUMERIC_AMBIGUITY",
                  "NONFINANCIAL_CONTEXT_NUMBER"}
TERM_STATUS={"SOURCE_EXPLICIT","UNMAPPED_KEEP_OPEN"}
KIND_TYPES={
    "FACT":{"FINANCIAL_FACT_ASSERTION","OTHER_FACT_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "OPINION":{"OPINION_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "HYPOTHETICAL":{"HYPOTHESIS_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "RECOMMENDATION":{"RECOMMENDATION_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "QUESTION":{"QUESTION_ONLY","QUESTION_WITH_EMBEDDED_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "MATH":{"OTHER_FACT_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
    "ANECDOTE":{"OPINION_ASSERTION","MIXED_ASSERTION","UNRESOLVED_MEANING"},
}
NONASSERTION={
    "QUESTION":{"QUESTION_ONLY","QUESTION_WITH_EMBEDDED_ASSERTION","UNRESOLVED_MEANING"},
    "QUOTE":{"QUOTE_ONLY","QUOTE_WITH_FACT_DEPENDENCY","UNRESOLVED_MEANING"},
    "NON_RESEARCH":{"NON_RESEARCH_ONLY","UNRESOLVED_MEANING"},
    "OPEN":{"UNRESOLVED_MEANING"},
}


def check(value,reason):
    if not value:
        raise InvalidInput("V206_E2_"+reason)


def _snapshot(owner, head):
    check(type(owner) is EngineChatSession,"PRIVATE_V176_OWNER_REQUIRED")
    prog=owner.progress()
    check(type(head) is str and len(head)==64 and
          prog["checkpoint_head_sha256"]==head,
          "EXTERNAL_OWNER_HEAD_STALE")
    with owner._connect() as con:
        reread,rows=owner._audit(con)
    check(reread==head,"OWNER_CHANGED_DURING_AUDIT")
    exchange,stage=owner.compile_native_v6_stage()
    check(stage["checkpoint_head_sha256"]==head and
          stage["source_sha256"]==prog["source_sha256"] and
          exchange["source_sha256"]==owner.source.source_sha256,
          "NATIVE_SOURCE_OR_OWNER_DRIFT")
    bycue={}
    for atom in exchange["atoms"]:
        i=atom["source_refs"][0]["cue_index"]
        bycue.setdefault(i,[]).append(atom)
    return prog,rows,bycue


def prepare_e2_cue_challenge(owner, *, expected_owner_head,
                             start_cue=1,limit=20,context_radius=8):
    check(type(start_cue) is int and type(limit) is int and
          type(context_radius) is int and 1<=limit<=40 and
          0<=context_radius<=12,"CHALLENGE_BOUNDS")
    prog,reviewed,atoms=_snapshot(owner,expected_owner_head)
    count=prog["cue_total"]
    check(1<=start_cue<=count,"CHALLENGE_START_NOT_IN_SOURCE")
    last=min(start_cue+limit-1,count)
    targets=[]
    for i in range(start_cue,last+1):
        cue=owner.source.cues[i-1]
        event,row=reviewed.get(i,(None,None))
        claims=[] if row is None else row["claims"]
        native=atoms.get(i,[])
        unsupported=(row is not None and
                     row["disposition"]=="ASSERTION" and
                     any(c["kind"]=="ANECDOTE" for c in claims))
        if unsupported:
            # V176 deliberately has NO V6 native atom for an anecdote.
            # E2 must still REVIEW this source speech rather than crash on
            # the zero-native-atom projection or silently omit the cue.
            check(len(claims)>0 and native==[],
                  "UNSUPPORTED_ANECDOTE_NATIVE_NOT_QUARANTINED")
        else:
            check(len(claims)==len(native),"NATIVE_ATOM_CENSUS_MISMATCH")
            if row is not None and row["disposition"]=="ASSERTION":
                check(all(native[j]["kind"]==claims[j]["kind"] and
                          native[j]["proposition"]==claims[j]["proposition"]
                          for j in range(len(claims))),
                      "V176_V6_ATOM_ORDER_OR_MEANING_DRIFT")
        targets.append({
            "cue_index":i,
            "original_text":cue.text,
            "source_text_sha256":sha256(cue.text.encode("utf-8")),
            "v176_event_sha256":event,
            "v176_disposition":None if row is None else row["disposition"],
            "v176_speaker_role":None if row is None else row["speaker_role"],
            "native_projection_status":("UNSUPPORTED_ANECDOTE"
               if unsupported else "PROJECTED" if native else "NO_NATIVE_ATOM"),
            "v176_claims":[{
                "claim_ordinal":j+1,
                "claim_sha256":json_digest(claim),
                "claim_id":None if unsupported else native[j]["claim_id"],
                "kind":claim["kind"],
                "verbatim_quote":claim["quote"],
                "conditions":claim["conditions"],
                "exceptions":claim["exceptions"],
                "context_cue_indices":claim["context_cue_indices"],
                "numeric_tokens":claim["numeric_tokens"],
            } for j,claim in enumerate(claims)],
            "original_numeric_tokens":NUMBER.findall(cue.text),
        })
    neighbours=list(range(max(1,start_cue-context_radius),
                          min(count,last+context_radius)+1))
    challenge={
        "schema":PLAN,"owner_head_sha256":expected_owner_head,
        "source_sha256":owner.source.source_sha256,
        "manifest_sha256":owner.source.manifest_sha256,
        "cue_count":count,"start_cue":start_cue,"end_cue":last,
        "context_radius":context_radius,
        "target_cues":targets,
        "surrounding_context":[{
            "cue_index":i,"text":owner.source.cues[i-1].text,
            "source_text_sha256":sha256(owner.source.cues[i-1].text.encode("utf-8"))
        } for i in neighbours],
        "independent_semantic_gold_available":False,
        "financial_facts_approved":False,
        "e3_e4_e5_authorized":False,
    }
    return {**challenge,"challenge_sha256":json_digest(challenge)}


def audit_e2_cue_answer(owner,packet,answer,*,expected_owner_head):
    check(type(packet) is dict and type(answer) is dict and
          packet.get("schema")==PLAN and
          packet.get("challenge_sha256")==json_digest({
              k:v for k,v in packet.items() if k!="challenge_sha256"}),
          "CHALLENGE_SCHEMA_OR_HASH")
    required=prepare_e2_cue_challenge(
        owner,expected_owner_head=expected_owner_head,
        start_cue=packet["start_cue"],
        limit=packet["end_cue"]-packet["start_cue"]+1,
        context_radius=packet["context_radius"])
    check(packet==required,"CHALLENGE_NOT_CURRENT_OWNER_ISSUED")
    check(set(answer)=={
        "schema","challenge_sha256","review_executor","rows",
        "independent_gold_certified","financial_fact_truth_certified",
        "e3_e4_e5_authorized"} and
        answer["schema"]==ANSWER and
        answer["challenge_sha256"]==packet["challenge_sha256"] and
        answer["review_executor"]=="CHATGPT_IN_CHAT" and
        answer["independent_gold_certified"] is False and
        answer["financial_fact_truth_certified"] is False and
        answer["e3_e4_e5_authorized"] is False and
        type(answer["rows"]) is list and
        len(answer["rows"])==len(packet["target_cues"]),
        "REVIEW_DOCUMENT_OR_CUE_CENSUS")
    context={r["cue_index"]:r for r in packet["surrounding_context"]}
    counts=Counter()
    holds=[]
    original_kinds=Counter()
    for target,row in zip(packet["target_cues"],answer["rows"]):
        required_keys={
            "cue_index","source_text_sha256","v176_event_sha256",
            "source_speaker_role","speech_act","source_quote",
            "source_meaning_note","source_meaning_note_sha256",
            "reviewer_caution","reviewer_caution_sha256",
            "claim_judgments","cue_numeric_roles",
            "embedded_assertion_quote","rebuttal_source_links",
            "not_original_speaker_quote","audio_speaker_verified",
            "context_and_counterexamples_checked","finance_approved",
        }
        check(type(row) is dict and set(row)==required_keys,
              "CUE_REVIEW_FIELDS")
        i=target["cue_index"]
        check(row["cue_index"]==i and
              row["source_text_sha256"]==target["source_text_sha256"] and
              row["v176_event_sha256"]==target["v176_event_sha256"] and
              row["source_speaker_role"]==target["v176_speaker_role"] and
              row["speech_act"] in SPEECH_ACTS and
              type(row["source_quote"]) is str and
              row["source_quote"] in target["original_text"] and
              len(row["source_quote"].strip())>=3 and
              type(row["source_meaning_note"]) is str and
              len(row["source_meaning_note"].strip())>=20 and
              row["source_meaning_note_sha256"]==
                  sha256(row["source_meaning_note"].encode("utf-8")) and
              type(row["reviewer_caution"]) is str and
              len(row["reviewer_caution"].strip())>=20 and
              row["reviewer_caution_sha256"]==
                  sha256(row["reviewer_caution"].encode("utf-8")) and
              row["not_original_speaker_quote"] is True and
              row["audio_speaker_verified"] is False and
              row["context_and_counterexamples_checked"] is True and
              row["finance_approved"] is False,
              "QUOTE_SPEAKER_OR_REVIEWER_BOUNDARY")
        check(type(row["claim_judgments"]) is list and
              len(row["claim_judgments"])==len(target["v176_claims"]),
              "CLAIM_REVIEW_CENSUS")
        a=target["v176_disposition"]
        if target["native_projection_status"]=="UNSUPPORTED_ANECDOTE":
            check(a=="ASSERTION" and row["claim_judgments"],
                  "UNSUPPORTED_ANECDOTE_NEEDS_EXPLICIT_REVIEW")
            holds.append((i,"UNSUPPORTED_SOURCE_ANECDOTE_NOT_IN_V6"))
        if a=="ASSERTION":
            check(row["speech_act"] not in {
                "QUESTION_ONLY","QUOTE_ONLY","NON_RESEARCH_ONLY"},
                "ASSERTION_REBRANDED_NONRESEARCH")
        else:
            allowed=NONASSERTION.get(a,{"UNRESOLVED_MEANING"})
            check(row["speech_act"] in allowed,
                  "NONASSERTION_MISLABELLED_AS_APPROVED_FACT")
        for claim,judgment in zip(target["v176_claims"],row["claim_judgments"]):
            check(type(judgment) is dict and set(judgment)=={
                "claim_id","claim_ordinal","original_claim_sha256",
                "source_kind","speech_act","condition_terms",
                "exception_terms","meaning_dependent_fact_open",
            },"CLAIM_JUDGMENT_SCHEMA")
            check(judgment["claim_id"]==claim["claim_id"] and
                  judgment["claim_ordinal"]==claim["claim_ordinal"] and
                  judgment["original_claim_sha256"]==claim["claim_sha256"] and
                  judgment["source_kind"]==claim["kind"] and
                  judgment["speech_act"] in KIND_TYPES[claim["kind"]] and
                  type(judgment["meaning_dependent_fact_open"]) is bool,
                  "CLAIM_KIND_OR_ORIGINAL_SHA_DRIFT")
            original_kinds[claim["kind"]]+=1
            for field,answer_key in (
                ("conditions","condition_terms"),
                ("exceptions","exception_terms")):
                terms=judgment[answer_key]
                check(type(terms) is list and len(terms)==len(claim[field]),
                      "SOURCE_QUALIFIER_CENSUS")
                for pos,(orig,link) in enumerate(zip(claim[field],terms),1):
                    check(type(link) is dict and set(link)=={
                        "term_ordinal","original_term","cue_index",
                        "source_quote","source_text_sha256","status",
                    } and link["term_ordinal"]==pos and
                        link["original_term"]==orig and
                        link["status"] in TERM_STATUS,
                        "QUALIFIER_ORIGINAL_TERMS_CHANGED")
                    ci=link["cue_index"]
                    if link["status"]=="SOURCE_EXPLICIT":
                        check(type(ci) is int and ci in context and
                              link["source_text_sha256"]==
                                context[ci]["source_text_sha256"] and
                              type(link["source_quote"]) is str and
                              link["source_quote"] in context[ci]["text"] and
                              orig in link["source_quote"],
                              "QUALIFIER_SOURCE_QUOTE_UNVERIFIED")
                    else:
                        check(ci is None and link["source_quote"] is None and
                              link["source_text_sha256"] is None,
                              "UNMAPPED_QUALIFIER_FAKES_SOURCE")
                        holds.append((i,"UNMAPPED_"+field.upper()))
            if judgment["speech_act"]=="UNRESOLVED_MEANING":
                holds.append((i,"UNRESOLVED_CLAIM"))
            if judgment["meaning_dependent_fact_open"]:
                counts["unverified_fact_dependencies"]+=1
        nums=row["cue_numeric_roles"]
        expected=target["original_numeric_tokens"]
        check(type(nums) is list and len(nums)==len(expected),
              "WHOLE_CUE_NUMBER_CENSUS")
        for pos,(original,entry) in enumerate(zip(expected,nums),1):
            check(type(entry) is dict and set(entry)=={
                "ordinal","token","role"} and
                entry["ordinal"]==pos and entry["token"]==original and
                entry["role"] in CUE_NUMBER_ROLES,
                "WHOLE_CUE_NUMERIC_TOKEN_LOST_OR_FORGED")
            counts["numerical_tokens"]+=1
        extra=row["embedded_assertion_quote"]
        check(extra is None or
              (type(extra) is str and len(extra)>=3 and
               extra in target["original_text"]),
              "EMBEDDED_FACT_NOT_FROM_ORIGINAL")
        if a!="ASSERTION" and extra is not None:
            holds.append((i,"EMBEDDED_ASSERTION_EXCLUDED_BY_V176"))
        if row["speech_act"] in {
            "QUESTION_WITH_EMBEDDED_ASSERTION","QUOTE_WITH_FACT_DEPENDENCY"
        }:
            check(extra is not None,"EMBEDDED_ASSERTION_QUOTE_REQUIRED")
        if row["speech_act"]=="UNRESOLVED_MEANING" or a in (None,"OPEN"):
            holds.append((i,"UNRESOLVED_SOURCE_MEANING"))
        check(type(row["rebuttal_source_links"]) is list,
              "REBUTTAL_LINKS_REQUIRED")
        for link in row["rebuttal_source_links"]:
            check(type(link) is dict and set(link)=={
                "cue_index","source_quote","source_text_sha256",
                "relation_type"} and
                link["relation_type"] in {
                    "REBUTTAL","EXCEPTION","CONTRAST","CONDITION"} and
                link["cue_index"] in context and
                type(link["source_quote"]) is str and
                len(link["source_quote"])>=3 and
                link["source_quote"] in context[link["cue_index"]]["text"] and
                link["source_text_sha256"]==
                    context[link["cue_index"]]["source_text_sha256"],
                "REBUTTAL_OR_CONTEXT_QUOTE_FORGED")
        counts["cues_checked"]+=1
        counts["original_claims_checked"]+=len(target["v176_claims"])
        counts["native_atom_reviews"]+=sum(
            c["claim_id"] is not None for c in target["v176_claims"])
        counts["source_"+str(a)]+=1
        counts["speech_"+row["speech_act"]]+=1
    check(owner.progress()["checkpoint_head_sha256"]==expected_owner_head,
          "SOURCE_OWNER_HEAD_CHANGED_DURING_REVIEW")
    return {
        "schema":RESULT,"source_sha256":packet["source_sha256"],
        "owner_head_sha256":expected_owner_head,
        "challenge_sha256":packet["challenge_sha256"],
        "response_sha256":json_digest(answer),
        "status":("HOLD_SEMANTIC_OR_EXTRACTION_LOSS" if holds
                  else "SOURCE_CENSUS_MECHANICALLY_ATTESTED_PENDING_INDEPENDENT_GOLD"),
        "counts":dict(counts),"source_claim_kind_counts":dict(original_kinds),
        "hold_reasons":[{"cue_index":i,"reason":reason} for i,reason in holds],
        "independent_semantic_gold_certified":False,
        "e2_real_video_quality_pass":False,
        "e3_e4_e5_authorized":False,
        "research_knowledge_published":False,
    }


def audit_full_e2_video(owner, reviewed_packets, *,
                        expected_owner_head):
    check(type(reviewed_packets) is list and reviewed_packets,
          "FULL_VIDEO_REVIEW_PACKETS_REQUIRED")
    seen=set()
    receipts=[]
    for entry in reviewed_packets:
        check(type(entry) is dict and set(entry)=={"challenge","answer"},
              "FULL_REVIEW_ENTRY_SCHEMA")
        challenge=entry["challenge"]
        receipt=audit_e2_cue_answer(
            owner,challenge,entry["answer"],
            expected_owner_head=expected_owner_head)
        first,last=challenge["start_cue"],challenge["end_cue"]
        cur=set(range(first,last+1))
        check(not (seen & cur),"FULL_VIDEO_CUE_DOUBLE_COUNT")
        seen.update(cur)
        receipts.append(receipt)
    total=len(owner.source.cues)
    check(seen==set(range(1,total+1)),"FULL_VIDEO_CUE_COVERAGE_MISSING")
    holds=sum(len(r["hold_reasons"]) for r in receipts)
    return {
        "schema":"IRE_V206_E2_FULL_VIDEO_CENSUS_RESULT_V1",
        "source_sha256":owner.source.source_sha256,
        "owner_head_sha256":expected_owner_head,
        "original_cues_checked":total,
        "batch_count":len(receipts),
        "native_atom_reviews":sum(r["counts"]["native_atom_reviews"] for r in receipts),
        "original_source_claims_checked":sum(
            r["counts"]["original_claims_checked"] for r in receipts),
        "semantic_holds":holds,
        "status":("HOLD_SOURCE_SEMANTIC_ERRORS" if holds else
                  "MECHANICAL_FULL_CUE_CENSUS_PASS_INDEPENDENT_GOLD_PENDING"),
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "private_source_text_written_to_public_files":False,
    }


def build_e2_source_repair_docket(owner,packet,answer,*,
                                 expected_owner_head):
    """Describe exactly what a future in-chat semantic repair must adjudicate.

    No native atom, V176 revision, V123 token or financial fact is created.
    Return a private in-memory work packet, not a public SRT data file.
    """
    audited=audit_e2_cue_answer(
        owner,packet,answer,expected_owner_head=expected_owner_head)
    bycue={t["cue_index"]:t for t in packet["target_cues"]}
    rows={r["cue_index"]:r for r in answer["rows"]}
    issues=[]
    for idx,r in enumerate(audited["hold_reasons"],1):
        cue=r["cue_index"]
        original=bycue[cue]
        adjudicated=rows[cue]
        reason=r["reason"]
        quote=(adjudicated["embedded_assertion_quote"]
               if reason=="EMBEDDED_ASSERTION_EXCLUDED_BY_V176" else
               adjudicated["source_quote"])
        check(type(quote) is str and quote in original["original_text"],
              "REPAIR_DOCKET_ORIGINAL_QUOTE_MISSING")
        issues.append({
            "issue_id":f"E2-{packet['start_cue']:05d}-{idx:04d}",
            "cue_index":cue,
            "source_cue_sha256":original["source_text_sha256"],
            "original_v176_event_sha256":original["v176_event_sha256"],
            "original_disposition":original["v176_disposition"],
            "original_native_projection":original["native_projection_status"],
            "reason":reason,
            "original_source_quote":quote,
            "source_quote_sha256":sha256(quote.encode("utf-8")),
            "chat_review_note_sha256":adjudicated["source_meaning_note_sha256"],
            "required_action":(
                "EXPLICIT_SOURCE_BOUND_CHAT_ADJUDICATION_AND_APPEND_ONLY_REPAIR"
                if reason in {
                    "EMBEDDED_ASSERTION_EXCLUDED_BY_V176",
                    "UNSUPPORTED_SOURCE_ANECDOTE_NOT_IN_V6",
                    "UNMAPPED_CONDITIONS","UNMAPPED_EXCEPTIONS",
                } else "INDEPENDENT_SOURCE_MEANING_RECHECK"),
            "native_claim_auto_created":False,
            "finance_approved":False,
        })
    check(owner.progress()["checkpoint_head_sha256"]==expected_owner_head,
          "REPAIR_DOCKET_OWNER_HEAD_CHANGED")
    return {
        "schema":"IRE_V206_E2_PRIVATE_UNRESOLVED_SOURCE_DOCKET_V1",
        "source_sha256":packet["source_sha256"],
        "owner_head_sha256":expected_owner_head,
        "e2_challenge_sha256":packet["challenge_sha256"],
        "e2_answer_sha256":audited["response_sha256"],
        "issue_count":len(issues),
        "issues":issues,
        "original_private_source_must_not_be_uploaded":True,
        "v176_native_atoms_mutated":False,
        "e2_pass":False,
        "e3_e4_e5_authorized":False,
    }
