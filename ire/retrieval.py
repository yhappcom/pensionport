"""Source-isolated candidate relationship retrieval for independently extracted atoms.

No access to previous versions, historical labels, historical databases, or
precomputed embeddings. Search ranks candidates; it never verifies relations.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import re
from .source import require

WORD = re.compile(r"[0-9A-Za-z가-힣]+")
MAX_ATOMS = 250000


def _features(text: str) -> tuple[set[str], set[str]]:
    words=[x.lower() for x in WORD.findall(text) if len(x)>=2]
    lexical=set(words)
    pieces=set()
    for word in words:
        for n in (2,3):
            pieces.update(word[i:i+n] for i in range(max(0,len(word)-n+1)))
    return lexical, pieces


def _scope_relation(a: dict,b: dict) -> str:
    left=a["frame"];right=b["frame"]
    event_match=(left["financial_event"] is not None and
                 left["financial_event"]==right["financial_event"])
    product_match=(left["product"] is not None and
                   left["product"]==right["product"])
    if event_match and product_match:
        if "NEGATION" in (left["modality"],right["modality"]):
            return "POSSIBLE_POLARITY_CONFLICT_REVIEW"
        if (left["jurisdiction"]!=right["jurisdiction"] or
                left["effective_date"]!=right["effective_date"] or
                left["conditions"]!=right["conditions"]):
            return "POSSIBLE_SCOPE_VARIANCE_REVIEW"
        return "SAME_TOPIC_SCOPE_REVIEW"
    if product_match:
        return "PRODUCT_OVERLAP_EVENT_DIFFERENT_REVIEW"
    if event_match:
        return "FINANCIAL_EVENT_OVERLAP_REVIEW"
    return "LEXICAL_SIMILARITY_ONLY_REVIEW"


def related_proposals(proposed: dict, top_k: int = 10,
                      audit_count: int = 5) -> dict:
    require(type(proposed) is dict and proposed.get("schema")=="IRE_PROPOSALS_V1"
            and type(top_k) is int and 1<=top_k<=50 and
            type(audit_count) is int and 0<=audit_count<=200,
            "INVALID_INDEPENDENT_RETRIEVAL_INPUT")
    entries=proposed.get("claims")
    require(type(entries) is list and len(entries)<=MAX_ATOMS,
            "INVALID_INDEPENDENT_CLAIM_CORPUS")
    byid={}
    word_index=defaultdict(set)
    piece_index=defaultdict(set)
    context_index=defaultdict(set)
    for atom in entries:
        cid=atom["claim_id"]
        require(cid not in byid, "DUPLICATE_CANDIDATE_ID")
        byid[cid]=atom
        word,piece=_features(atom["proposition"])
        for key in word:word_index[key].add(cid)
        for key in piece:piece_index[key].add(cid)
        frame=atom["frame"]
        for k in ("product", "financial_event", "action"):
            if frame[k]:
                context_index[(k,frame[k].lower())].add(cid)
    results=[]
    for cid in sorted(byid):
        current=byid[cid]
        words,pieces=_features(current["proposition"])
        scores=defaultdict(float)
        lanes=defaultdict(set)
        # No content or scores are imported from other source runs.
        for token in words:
            for target in word_index[token] - {cid}:
                scores[target]+=2.0
                lanes[target].add("WORD")
        for token in pieces:
            for target in piece_index[token] - {cid}:
                scores[target]+=0.2
                lanes[target].add("CHAR")
        for name,weight in (("financial_event",5.0),("product",2.0),
                            ("action",0.7)):
            val=current["frame"][name]
            if val:
                for target in context_index[(name,val.lower())] - {cid}:
                    scores[target]+=weight
                    lanes[target].add("EXPLICIT_FRAME")
        # Every zero-signal pair remains unclassified, not disproved.
        ranked=sorted(scores,key=lambda target:(-scores[target],target))
        hits=[]
        for target in ranked[:top_k]:
            hits.append({
                "claim_id":target,
                "rank":len(hits)+1,
                "score":round(scores[target],5),
                "retrieval_lanes":sorted(lanes[target]),
                "relation_proposal":_scope_relation(current,byid[target]),
                "relation_verified":False,
                "requires_independent_reviewer":True
            })
        non_candidates=set(byid)-set(ranked[:top_k])-{cid}
        diagnostics=sorted(non_candidates,key=lambda target:
                           hashlib.sha256((cid+"|"+target).encode()).hexdigest())
        results.append({
            "claim_id":cid,
            "hits":hits,
            "noncandidate_audit_ids":diagnostics[:audit_count],
            "unseen_related_pairs_may_exist":True,
        })
    return {
        "schema":"IRE_WITHIN_SOURCE_RETRIEVAL_V1",
        "source_sha256":proposed["source_sha256"],
        "claim_count":len(entries),
        "top_k":top_k,
        "queries":results,
        "external_legacy_corpus_loaded":False,
        "relation_ground_truth_count":0,
        "precision_at_k":None,
        "recall_at_k":None,
        "all_relation_candidates_unapproved":True
    }
