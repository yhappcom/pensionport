"""E2-only explicit ChatGPT corrections for statements lost in source-first NO_ATOM.

Derives unapproved, source-quoted *working drafts*; cannot mutate the frozen
V176 owner journal, issue a V6 C-atom ID, attest financial fact accuracy,
or send anything to V123/V128/V126. Uses actual V206 E2 cue and repair
docket attestations. All review decisions are supplied by active ChatGPT.
"""
from __future__ import annotations

from collections import Counter

from ire.v6.atomic_exchange import NUMBER
from ire.v6.codec import HEX64, json_digest, sha256
from ire.v6.errors import InvalidInput
from v206_e2_full_cue_semantic_census import (
    audit_e2_cue_answer, build_e2_source_repair_docket,
    DISCOURSE_LINK_FIELDS,
)

SCHEMA="IRE_V207_E2_CHAT_SOURCE_REPAIR_PLAN_V1"
STATUS="IRE_V207_E2_UNRELEASED_REPAIR_PROJECTION_V1"
ACTIONS={
    "KEEP_OPEN","DRAFT_UNVERIFIED_EMBEDDED_CLAIM",
    "SOURCE_ONLY_QUARANTINE",
}
KINDS={"FACT","OPINION","HYPOTHETICAL","RECOMMENDATION","MATH"}
EPISTEMIC={
    "REPORTED_CLAIM_IN_QUESTION","QUOTED_UNVERIFIED_SPEECH",
}
NOFACT={"financial_fact_approved":False,
        "native_v6_released":False,
        "knowledge_publication_authorized":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False}


def require(ok,what):
    if not ok:
        raise InvalidInput("V207_E2_"+what)


def audit_e2_chat_repairs(owner, challenge, answer, plan, *,
                          expected_owner_head):
    """Verify ChatGPT proposed meaning against exact E2 HOLD and actual source."""
    current=audit_e2_cue_answer(
        owner,challenge,answer,expected_owner_head=expected_owner_head)
    docket=build_e2_source_repair_docket(
        owner,challenge,answer,expected_owner_head=expected_owner_head)
    require(type(plan) is dict and set(plan)=={
        "schema","review_executor","source_sha256","owner_head_sha256",
        "e2_challenge_sha256","e2_answer_sha256","source_docket_sha256",
        "review_notes_sha256","decisions","financial_fact_approved",
        "native_v6_released","knowledge_publication_authorized",
        "e2_final_pass","e3_e4_e5_authorized",
    },"PLAN_SCHEMA")
    require(plan["schema"]==SCHEMA and
            plan["review_executor"]=="CHATGPT_IN_CHAT" and
            plan["source_sha256"]==owner.source.source_sha256 and
            plan["owner_head_sha256"]==expected_owner_head and
            plan["e2_challenge_sha256"]==challenge["challenge_sha256"] and
            plan["e2_answer_sha256"]==current["response_sha256"] and
            plan["source_docket_sha256"]==json_digest(docket) and
            type(plan["review_notes_sha256"]) is str and
            HEX64.fullmatch(plan["review_notes_sha256"]) and
            all(plan[k] is v for k,v in NOFACT.items()) and
            type(plan["decisions"]) is list and
            len(plan["decisions"])==docket["issue_count"],
            "PIN_OR_FALSE_RELEASE")
    # Retain ALL previously source-checked cross-cue rebuttals, exceptions
    # and conditions in the new unapproved draft, not just the main quote.
    e2_rows={r["cue_index"]:r for r in answer["rows"]}
    issues={row["issue_id"]:row for row in docket["issues"]}
    visited=set()
    projected=[]
    quarantined=0
    pending=0
    for decision in plan["decisions"]:
        required={
            "issue_id","cue_index","source_cue_sha256","issue_reason",
            "review_action","source_speech_act","quoted_source_excerpt",
            "review_note","review_note_sha256","draft_claims",
            "previous_v176_decision_unchanged",
        }
        require(type(decision) is dict and set(decision)==required,
                "ISSUE_REVIEW_SCHEMA")
        issue=issues.get(decision["issue_id"])
        require(issue is not None and issue["issue_id"] not in visited and
                decision["cue_index"]==issue["cue_index"] and
                decision["source_cue_sha256"]==issue["source_cue_sha256"] and
                decision["issue_reason"]==issue["reason"] and
                decision["quoted_source_excerpt"]==
                    issue["original_source_quote"] and
                decision["previous_v176_decision_unchanged"] is True and
                type(decision["review_note"]) is str and
                len(decision["review_note"].strip())>=30 and
                decision["review_note_sha256"]==
                    sha256(decision["review_note"].encode("utf-8")) and
                decision["review_action"] in ACTIONS and
                type(decision["draft_claims"]) is list,
                "SOURCE_ISSUE_OR_REVIEW_NOTE_DRIFT")
        visited.add(issue["issue_id"])
        embedded=issue["reason"]=="EMBEDDED_ASSERTION_EXCLUDED_BY_V176"
        if decision["review_action"]=="DRAFT_UNVERIFIED_EMBEDDED_CLAIM":
            require(embedded and 1<=len(decision["draft_claims"])<=6,
                    "DRAFT_MUST_BE_SOURCE_EMBEDDED")
        else:
            require(not decision["draft_claims"],
                    "QUARANTINE_OR_OPEN_CANNOT_ISSUE_ATOM")
            if decision["review_action"]=="SOURCE_ONLY_QUARANTINE":
                quarantined+=1
            else:
                pending+=1
        src=owner.source.cues[issue["cue_index"]-1].text
        if embedded:
            required_act={
                "QUESTION":"REPORTED_CLAIM_IN_QUESTION",
                "QUOTE":"QUOTED_UNVERIFIED_SPEECH",
            }.get(issue["original_disposition"])
            require(required_act is not None and
                    decision["source_speech_act"]==required_act,
                    "QUESTION_QUOTE_ATTRIBUTION_LOSS")
        else:
            require(decision["source_speech_act"]=="UNRESOLVED_SOURCE_SPEECH",
                    "NONEMBEDDED_SOURCE_ROLE")
        for ordinal,draft in enumerate(decision["draft_claims"],1):
            require(type(draft) is dict and set(draft)=={
                "draft_id","kind","proposition","source_cue_index",
                "verbatim_quote","context_cue_indices","conditions",
                "exceptions","source_discourse_links",
                "numeric_references","speaker",
                "stance","as_of","epistemic_status",
                "fact_dependency_open","not_native_v6_atom",
                "financial_fact_approved",
            },"DRAFT_FIELDS")
            index=issue["cue_index"]
            q=draft["verbatim_quote"]
            require(draft["draft_id"]==
                     f"E2DRAFT-{index:05d}-{ordinal:02d}" and
                    draft["source_cue_index"]==index and
                    draft["kind"] in KINDS and
                    type(draft["proposition"]) is str and
                    len(draft["proposition"].strip())>=12 and
                    type(q) is str and len(q.strip())>=3 and
                    q in src and
                    q in issue["original_source_quote"] and
                    type(draft["context_cue_indices"]) is list and
                    draft["context_cue_indices"]==
                        sorted(set(draft["context_cue_indices"])) and
                    index in draft["context_cue_indices"] and
                    all(type(x) is int and
                        1<=x<=len(owner.source.cues)
                        for x in draft["context_cue_indices"]) and
                    draft["speaker"]=="UNKNOWN" and
                    draft["stance"]=="UNRESOLVED" and
                    draft["as_of"] is None and
                    draft["epistemic_status"]==
                        decision["source_speech_act"] and
                    draft["fact_dependency_open"] is True and
                    draft["not_native_v6_atom"] is True and
                    draft["financial_fact_approved"] is False,
                    "DRAFT_MEANING_OR_SOURCE_DRIFT")
            # An explicit relation already reviewed at cue-census stage
            # may never vanish during E2 candidate construction. Across-child
            # context is preserved, never truncated to the owning cue.
            discourse=draft["source_discourse_links"]
            prior=e2_rows[index]["rebuttal_source_links"]
            # Schema validation precedes direct indexing, even for malicious
            # or outdated review packets. This prevents Python KeyError from
            # masking an ordinary, recoverable version-contract mismatch.
            require(type(discourse) is list and
                    type(prior) is list and
                    all(type(x) is dict and
                        set(x)==DISCOURSE_LINK_FIELDS
                        for x in discourse+prior),
                    "CROSS_CUE_LINK_SCHEMA_DRIFT")
            require(discourse==prior and
                    len({json_digest(x) for x in discourse})==len(discourse),
                    "CROSS_CUE_DISCOURSE_LOST_OR_DUPLICATED")
            for relation in discourse:
                ci=relation["cue_index"]
                require(ci in draft["context_cue_indices"] and
                        type(ci) is int and 1<=ci<=len(owner.source.cues) and
                        relation["source_text_sha256"]==
                            sha256(owner.source.cues[ci-1].text.encode("utf-8")) and
                        relation["source_quote"] in owner.source.cues[ci-1].text and
                        relation["relation_type"] in {
                            "REBUTTAL","EXCEPTION","CONTRAST","CONDITION"},
                        "CROSS_CUE_DISCOURSE_NOT_ORIGINAL")
            for key in ("conditions","exceptions"):
                terms=draft[key]
                require(type(terms) is list and
                        all(type(x) is dict and
                            set(x)=={"cue_index","verbatim_quote",
                                     "source_cue_sha256"}
                            for x in terms),
                        "QUALIFIER_ANCHOR_SCHEMA")
                for term in terms:
                    ci=term["cue_index"]
                    require(type(ci) is int and
                            ci in draft["context_cue_indices"] and
                            term["source_cue_sha256"]==
                                sha256(owner.source.cues[ci-1].text.encode()) and
                            type(term["verbatim_quote"]) is str and
                            len(term["verbatim_quote"])>=3 and
                            term["verbatim_quote"] in owner.source.cues[ci-1].text,
                            "QUALIFIER_SOURCE_NOT_ORIGINAL")
            nums=draft["numeric_references"]
            require(type(nums) is list and
                    all(type(x) is dict and
                        set(x)=={"cue_index","token"} for x in nums),
                    "DRAFT_NUMERIC_SCHEMA")
            actual=Counter()
            for num in nums:
                require(num["cue_index"]==index and
                        type(num["token"]) is str,
                        "NUMERIC_UNVERIFIED_CROSS_CUE")
                actual[num["token"]]+=1
            require(actual==Counter(NUMBER.findall(q)),
                    "REPORTED_NUMERIC_TOKEN_REMOVED_OR_INVENTED")
            projected.append({
                "draft_id":draft["draft_id"],
                "origin_issue_id":issue["issue_id"],
                "origin_cue_index":index,
                "source_cue_sha256":issue["source_cue_sha256"],
                "original_v176_disposition":issue["original_disposition"],
                "original_reported_quote":q,
                "source_speech_act":decision["source_speech_act"],
                "unverified_kind":draft["kind"],
                "candidate_sha256":json_digest(draft),
                "potential_conditions":draft["conditions"],
                "potential_exceptions":draft["exceptions"],
                "source_discourse_links":discourse,
                "numeric_references":draft["numeric_references"],
                "needs_explicit_native_owner_repair":True,
                "finance_verified":False,
                "native_v6_claim_id":None,
            })
    require(visited==set(issues),"INCOMPLETE_ISSUE_REVIEW")
    require(owner.progress()["checkpoint_head_sha256"]==expected_owner_head,
            "ORIGINAL_OWNER_HEAD_CHANGED")
    return {
        "schema":STATUS,
        "source_sha256":owner.source.source_sha256,
        "owner_head_sha256":expected_owner_head,
        "original_e2_docket_sha256":json_digest(docket),
        "authored_chat_plan_sha256":json_digest(plan),
        "issues_reviewed":len(visited),
        "unreleased_draft_claims":len(projected),
        "source_only_quarantined_issues":quarantined,
        "still_open_issues":pending,
        "unreleased_drafts":projected,
        "original_v176_changed":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "knowledge_written":False,
    }
