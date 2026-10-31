#!/usr/bin/env python3
"""V3.4 source-attested interfaces for separately executed language models.

This module validates pinned external *proposals*. It cannot prove model
identity, model quality, semantic completeness, human review or blindness.
Every word of each atom must be traceable to original SRT cue text. Optional
proposals never mutate frozen V3.3 annotation or gold data.
"""
from __future__ import annotations
import copy
from collections import Counter
from v30_verified_core import parse_srt, sha256, canonical, guard, HASH_RE, VID_RE
from v30_v34_atomic_semantics import (
    SCHEMA, normalize, make_draft, validate_draft, ENTITY_ALIASES,
    EVENT_RULES, ACTION_RULES
)

ATOM_SCHEMA="V34_PINNED_EXTERNAL_ATOM_PROPOSALS_V1"
SEMANTIC_SCHEMA="V34_PINNED_EXTERNAL_SEMANTIC_PROPOSALS_V1"
MODALITIES={"ASSERTED_PROVISIONAL","CONDITIONAL","NEGATED","HYPOTHETICAL",
            "OPINION","UNRESOLVED"}

def check_model_envelope(packet, schema, raw_sha, model_sha, prompt_sha, video_id):
    guard(type(packet) is dict and packet.get("schema")==schema
          and packet.get("source_srt_sha256")==raw_sha
          and packet.get("video_id")==video_id
          and type(model_sha) is str and HASH_RE.fullmatch(model_sha)
          and type(prompt_sha) is str and HASH_RE.fullmatch(prompt_sha)
          and packet.get("model_sha256")==model_sha
          and packet.get("prompt_sha256")==prompt_sha,
          "V34_EXTERNAL_MODEL_PACKET_IDENTITY_OR_SOURCE_CHANGED")

def _coverage(cue_text,quotes):
    """Reject unaccounted material characters; spaces/punctuation are ignored.

    Span location is deterministic. Repeated substrings require an explicit
    occurrence, and cannot be inferred to cover all repeating source speech.
    """
    text=normalize(cue_text)
    occupied=set()
    for quote in quotes:
        q=normalize(quote)
        guard(q and q in text, "V34_MODEL_ATOM_QUOTE_NOT_IN_SOURCE_CUE")
        positions=[i for i in range(len(text)-len(q)+1) if text.startswith(q,i)]
        available=[i for i in positions if not any(j in occupied for j in range(i,i+len(q)))]
        guard(available, "V34_MODEL_ATOM_QUOTE_OVERLAP_OR_REPETITION")
        start=available[0]
        occupied.update(range(start,start+len(q)))
    remaining="".join(ch for i,ch in enumerate(text) if i not in occupied and ch.isalnum())
    guard(not remaining, "V34_MODEL_OMITTED_ORIGINAL_MATERIAL_CHARACTERS")
    return True

def apply_model_atomization(raw,source_sha,video_id,packet,model_sha,prompt_sha):
    check_model_envelope(packet,ATOM_SCHEMA,source_sha,model_sha,prompt_sha,video_id)
    guard(type(video_id) is str and VID_RE.fullmatch(video_id),"V34_BAD_MODEL_VIDEO_ID")
    cues=parse_srt(raw,source_sha)
    atoms=packet.get("atoms")
    guard(type(atoms) is list and len(cues)<=len(atoms)<=25000
          and len(cues)<=25000 and
          type(packet.get("source_cue_count")) is int and
          packet["source_cue_count"]==len(cues),
          "V34_MODEL_CUE_COUNT_OR_ATOM_COUNT_INVALID")
    by_cue={cue.index:[] for cue in cues}
    previous=0
    for row in atoms:
        guard(type(row) is dict and set(row)=={"cue_index","source_quote"}
              and type(row["cue_index"]) is int
              and previous<=row["cue_index"]<=len(cues)
              and type(row["source_quote"]) is str,
              "V34_MODEL_ATOM_ORDER_OR_SCHEMA_INVALID")
        previous=row["cue_index"]
        by_cue[previous].append(row["source_quote"])
    guard(all(by_cue[i] for i in by_cue),"V34_MODEL_OMITTED_CUE")
    for cue in cues:_coverage(cue.text,by_cue[cue.index])
    draft=make_draft(raw,source_sha,video_id)
    claims=[];links=[]
    for cue in cues:
        ids=[]
        for q in by_cue[cue.index]:
            quote=normalize(q)
            cid=video_id+"-A"+str(len(claims)+1).zfill(5)
            prior=normalize(cues[cue.index-2].text) if cue.index>1 else ""
            claims.append({
                "claim_id":cid,"video_id":video_id,
                "source_srt_sha256":source_sha,
                "cue_indices":[cue.index],
                "source_quote":quote,
                "quote_sha256":sha256(quote.encode("utf-8")),
                "context_previous_sha256":sha256(prior.encode("utf-8")),
                "claim_status":"PROPOSED_UNREVIEWED",
                "materiality":"UNCLASSIFIED_REVIEW_REQUIRED",
                "atomization_confidence":"EXTERNAL_MODEL_PROPOSAL_NOT_REVIEWED",
                "source_exposure":"NOT_ATTESTED",
                "external_model_sha256":model_sha,
                "prompt_sha256":prompt_sha,
            })
            ids.append(cid)
        links.append({"cue_index":cue.index,"claim_ids":ids,
                      "classification":"REVIEW_REQUIRED",
                      "human_exclusion_authorized":False})
    draft["claims"]=claims
    draft["cues"]=links
    draft["proposed_claim_count"]=len(claims)
    draft["atomization_origin"]="PINNED_EXTERNAL_MODEL_UNREVIEWED"
    draft["atomization_model_sha256"]=model_sha
    draft["atomization_prompt_sha256"]=prompt_sha
    validate_draft(draft,raw,source_sha)
    return draft

def apply_model_semantics(draft,semantic_census,packet,model_sha,prompt_sha):
    check_model_envelope(packet,SEMANTIC_SCHEMA,draft["source_srt_sha256"],
                         model_sha,prompt_sha,draft["video_id"])
    guard(type(semantic_census) is dict and
          semantic_census.get("draft_sha256")==sha256(canonical(draft))
          and semantic_census.get("total_proposals")==len(draft["claims"]),
          "V34_MODEL_SEMANTIC_CENSUS_WRONG_ATOM_VERSION")
    rows=packet.get("annotations")
    guard(type(rows) is list and len(rows)==len(draft["claims"]),
          "V34_EXTERNAL_MODEL_MUST_ANNOTATE_FULL_ATOM_CENSUS")
    mapping={}
    for row in rows:
        guard(type(row) is dict and set(row)=={
            "claim_id","quote_sha256","source_evidence_quote",
            "entity_ids","event_candidates","action_candidates",
            "modality","has_condition"
        } and type(row["claim_id"]) is str and
              row["claim_id"] not in mapping,
              "V34_EXTERNAL_SEMANTIC_DUPLICATE_OR_MALFORMED")
        for field,allowed in (("entity_ids",ENTITY_ALIASES),
                              ("event_candidates",EVENT_RULES),
                              ("action_candidates",ACTION_RULES)):
            values=row[field]
            guard(type(values) is list and len(values)==len(set(values))
                  and all(type(x) is str and x in allowed for x in values),
                  "V34_EXTERNAL_UNKNOWN_FINANCIAL_ROLE_OR_EVENT")
        guard(row["modality"] in MODALITIES
              and type(row["has_condition"]) is bool,
              "V34_EXTERNAL_MODALITY_OR_CONDITION_INVALID")
        mapping[row["claim_id"]]=row
    guard(set(mapping)=={a["claim_id"] for a in draft["claims"]},
          "V34_EXTERNAL_MODEL_DROPPED_OR_INVENTED_ATOM")
    output=copy.deepcopy(semantic_census)
    for atom,frame in zip(draft["claims"],output["frames"]):
        row=mapping[atom["claim_id"]]
        evidence=normalize(row["source_evidence_quote"])
        guard(type(row["source_evidence_quote"]) is str and len(evidence)>=3
              and evidence in normalize(atom["source_quote"])
              and row["quote_sha256"]==atom["quote_sha256"],
              "V34_EXTERNAL_SEMANTIC_EVIDENCE_NOT_IN_ORIGINAL_ATOM")
        frame["entities"]=[
            {"id":name,"kind":ENTITY_ALIASES[name][1]}
            for name in row["entity_ids"]
        ]
        frame["event_candidates"]=row["event_candidates"]
        frame["event_kind"]=(row["event_candidates"][0] if
                             len(row["event_candidates"])==1 else "UNRESOLVED")
        frame["action_candidates"]=row["action_candidates"]
        frame["action"]=(row["action_candidates"][0] if
                         len(row["action_candidates"])==1 else "UNRESOLVED")
        frame["modality"]=row["modality"]
        frame["conditions"]["has_condition"]=row["has_condition"]
        # Model output may propose labels but cannot create verified source,
        # numeric units, jurisdiction, effective dates or human signatures.
        flags=set(frame["ambiguity_flags"])
        flags.add("EXTERNAL_MODEL_SEMANTIC_INFERENCE_UNREVIEWED")
        if not row["event_candidates"]:flags.add("UNKNOWN_FINANCIAL_EVENT")
        if len(row["event_candidates"])>1:flags.add("MULTI_EVENT_OR_SCOPE_REVIEW")
        frame["ambiguity_flags"]=sorted(flags)
        frame["annotation_origin"]="PINNED_EXTERNAL_MODEL_PROPOSAL"
        frame["external_model_sha256"]=model_sha
        frame["external_prompt_sha256"]=prompt_sha
        frame["annotation_status"]="PROPOSED_UNREVIEWED"
        frame["financial_fact_verified"]=False
        frame["automatic_knowledge_merge"]=False
    output["unresolved_events"]=sum(x["event_kind"]=="UNRESOLVED" for x in output["frames"])
    output["model_annotation_origin"]="PINNED_EXTERNAL_MODEL_UNREVIEWED"
    output["model_sha256"]=model_sha
    output["prompt_sha256"]=prompt_sha
    output["human_semantic_accuracy_proven"]=False
    output["review_status"]="BLOCKED_PENDING_INDEPENDENT_REVIEW"
    return output
