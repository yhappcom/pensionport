#!/usr/bin/env python3
"""V3.4: broad-recall multi-lane retrieval, conservative financial relation triage.

Uses independently sourced claim metadata. Lexical/character/event/entity/graph
retrieval are separate lanes and fused by reciprocal rank. Optional external
embeddings need model digests and identical dimensions. No hit implies truth.
"""
from __future__ import annotations
import math
import re
from collections import Counter, defaultdict
from v30_verified_core import guard, sha256, canonical, HASH_RE, CLAIM_RE
from v30_v34_atomic_semantics import infer_frame

TOKEN = re.compile(r"[0-9a-z가-힣]+",re.I)
PARTICLES = re.compile(r"(?:으로|에서|에게|까지|부터|처럼|을|를|은|는|이|가|의|도|와|과)$")
RELATION_SCHEMA = "V34_REVIEW_ONLY_RELATION_RETRIEVAL_V1"

def features(text):
    guard(type(text) is str and 0<len(text)<=16000,"V34_SEARCH_TEXT_INVALID")
    words=[w.lower() for w in TOKEN.findall(text)]
    stems=[PARTICLES.sub("",w) if len(w)>=3 else w for w in words]
    word_features=Counter(w for w in words+stems if w)
    char_features=Counter()
    for word in words:
        for length in (2,3,4):
            char_features.update(word[i:i+length] for i in range(max(0,len(word)-length+1)))
    return word_features,char_features

def _vector(vector,model_sha):
    guard(type(model_sha) is str and HASH_RE.fullmatch(model_sha),
          "V34_UNPINNED_EXTERNAL_EMBEDDING_MODEL")
    guard(type(vector) is list and 2<=len(vector)<=4096 and
          all(type(v) in (float,int) and math.isfinite(v) for v in vector),
          "V34_INVALID_DENSE_VECTOR")
    sq=sum(float(v)*float(v) for v in vector)
    guard(sq>0 and math.isfinite(sq),"V34_ZERO_OR_OVERFLOW_DENSE_VECTOR")
    return tuple(float(v)/math.sqrt(sq) for v in vector)

def make_record(claim_id,text,video_number,source_sha256,verdict="UNREVIEWED",
                frame=None,embedding=None,embedding_model_sha256=None,
                provenance_state="ORIGINAL_SHA_VERIFIED",source_record_digest=None):
    legacy_71 = (video_number==71 and re.fullmatch(r"71-PUBLIC-(?:0[1-9]|1[0-3])",str(claim_id)) is not None)
    guard(type(claim_id) is str and (CLAIM_RE.fullmatch(claim_id) or legacy_71)
          and type(video_number) is int and 1<=video_number<=791
          and type(text) is str and text.strip() and len(text)<=16000,
          "V34_SEARCH_RECORD_MUST_HAVE_TRACEABLE_SOURCE")
    if source_sha256 is None:
        guard(provenance_state=="HISTORIC_ORIGINAL_SHA_MISSING"
              and type(source_record_digest) is str and HASH_RE.fullmatch(source_record_digest),
              "V34_HISTORICAL_MISSING_ORIGINAL_MUST_REMAIN_UNVERIFIED")
    else:
        guard(type(source_sha256) is str and HASH_RE.fullmatch(source_sha256)
              and provenance_state=="ORIGINAL_SHA_VERIFIED",
              "V34_ORIGINAL_HASH_OR_STATE_INVALID")
    # A historical claim's annotation is a proposal, not an independently
    # verified statement. Preserve original verdict even when vocab differs.
    if frame is None:
        atom={"claim_id":claim_id,"source_quote":text,
              "quote_sha256":sha256(text.encode("utf-8")),
              "source_srt_sha256":source_sha256,
              "claim_status":"PROPOSED_UNREVIEWED"}
        frame=infer_frame(atom)
    guard(type(frame) is dict and frame.get("claim_id")==claim_id
          and frame.get("source_srt_sha256")==source_sha256
          and frame.get("quote_sha256")==sha256(text.encode("utf-8"))
          and frame.get("annotation_status")=="PROPOSED_UNREVIEWED"
          and frame.get("financial_fact_verified") is False,
          "V34_SEARCH_INDEX_REJECTS_UNPROVEN_OR_SPOOFED_FRAME")
    vector=None
    if embedding is not None:
        vector=_vector(embedding,embedding_model_sha256)
    else:
        guard(embedding_model_sha256 is None,
              "V34_ORPHAN_EMBEDDING_VERSION")
    words,chars=features(text)
    return {"claim_id":claim_id, "text":text, "video_number":video_number,
            "source_srt_sha256":source_sha256, "source_record_digest":source_record_digest,
            "provenance_state":provenance_state, "original_verdict":verdict,
            "frame":frame, "words":words, "chars":chars,
            "embedding":vector, "embedding_model_sha256":embedding_model_sha256}

def index_records(records,development=True,maximum=100000):
    guard(type(records) is list and len(records)<=maximum
          and 1<=maximum<=100000, "V34_INDEX_SIZE_INVALID")
    built=[];known=set()
    for record in records:
        guard(type(record) is dict,"V34_INDEX_RECORD_MALFORMED")
        number=record.get("video_number")
        # In development, all actual #261+ and evaluation data are embargoed.
        guard(not development or (type(number) is int and number<=260),
              "V34_REAL_UNSEEN_HOLDOUT_EMBARGO")
        row=make_record(**record)
        guard(row["claim_id"] not in known,"V34_DUPLICATE_CLAIM_ID")
        known.add(row["claim_id"]);built.append(row)
    return tuple(sorted(built,key=lambda x:x["claim_id"]))

def _bm25(query,candidates,field):
    n=len(candidates)
    if not n:return {}
    df=Counter()
    lengths=[]
    for item in candidates:
        df.update(item[field].keys())
        lengths.append(sum(item[field].values()))
    avgdl=max(1,sum(lengths)/n)
    scores={}
    for item,length in zip(candidates,lengths):
        score=0.0
        for term,qtf in query[field].items():
            tf=item[field].get(term,0)
            if not tf:continue
            idf=math.log(1+(n-df[term]+0.5)/(df[term]+0.5))
            score+=idf*tf*2.2/(tf+1.2*(0.25+0.75*length/avgdl))*min(2,qtf)
        scores[item["claim_id"]]=score
    return scores

def _semantic_score(a,b):
    x=a["frame"]; y=b["frame"]
    xe=set(x["event_candidates"]); ye=set(y["event_candidates"])
    ea={e["id"] for e in x["entities"]}
    eb={e["id"] for e in y["entities"]}
    matches=xe & ye
    entity_intersection=ea & eb
    # Exact event is a stronger retrieval signal than broad product identity,
    # but both remain only provisional.
    return (7.0*len(matches)+2.0*len(entity_intersection)
            +0.9*len(set(x["action_candidates"]) & set(y["action_candidates"])))

def _risk(verdict):
    if verdict in ("CONTRADICTED","CORRECTED_AFTER_PRIMARY_CONTRADICTION"):
        return "CORRECTION_ONLY"
    if verdict=="HYPOTHETICAL":return "HYPOTHETICAL_UNVERIFIED"
    return "HUMAN_REVIEW_ONLY"

def relation_triage(query, candidate):
    a=query["frame"]; b=candidate["frame"]
    events=set(a["event_candidates"])&set(b["event_candidates"])
    entities={x["id"] for x in a["entities"]}&{x["id"] for x in b["entities"]}
    if not a["event_candidates"] or not b["event_candidates"]:
        kind="UNRESOLVED_EVENT_REVIEW"
    elif events:
        if a["modality"]=="NEGATED" or b["modality"]=="NEGATED":
            kind="POSSIBLE_NEGATION_CONFLICT_REVIEW"
        elif a["conditions"]["has_condition"]!=b["conditions"]["has_condition"]:
            kind="CONDITIONAL_SCOPE_REVIEW"
        else:kind="SHARED_EVENT_SCOPE_REVIEW"
    elif entities:
        kind="SHARED_PRODUCT_DIFFERENT_EVENT_REVIEW"
    else:
        kind="LEXICAL_OR_SEMANTIC_BROAD_AUDIT_ONLY"
    return {
        "relation_type":kind,
        "shared_events":sorted(events), "shared_entities":sorted(entities),
        "source_risk":_risk(candidate["original_verdict"]),
        "numeric_values_must_be_scope_checked":True,
        "no_statement_truth_inference":True,
        "relation_review_status":"UNREVIEWED_CANDIDATE",
        "automatic_relation_approval":False,
        "automatic_knowledge_merge":False
    }

def retrieve(query, corpus, top_k=10, audit_count=20, reviewed_graph_edges=None):
    guard(type(query) is dict and query.get("claim_id") is not None
          and isinstance(corpus,(tuple,list))
          and type(top_k) is int and 1<=top_k<=200
          and type(audit_count) is int and 0<=audit_count<=500,
          "V34_SEARCH_ARGUMENTS_INVALID")
    known={r["claim_id"]:r for r in corpus}
    guard(len(known)==len(corpus),"V34_DUPLICATED_INDEX_RECORDS")
    others=[r for r in corpus if r["claim_id"]!=query["claim_id"]]
    words=_bm25(query,others,"words")
    chars=_bm25(query,others,"chars")
    sem={r["claim_id"]:_semantic_score(query,r) for r in others}
    graph=defaultdict(float)
    for edge in reviewed_graph_edges or ():
        guard(type(edge) is dict and set(edge)=={"left","right","review_status"}
              and edge["review_status"]=="INDEPENDENTLY_REVIEWED"
              and edge["left"] in known and edge["right"] in known
              and edge["left"]!=edge["right"],"V34_UNVERIFIED_RELATION_EDGE")
        if edge["left"]==query["claim_id"]:graph[edge["right"]]+=1
        if edge["right"]==query["claim_id"]:graph[edge["left"]]+=1
    vector_scores={}
    if query.get("embedding") is not None:
        guard(all(r["embedding"] is not None and
                  r["embedding_model_sha256"]==query["embedding_model_sha256"]
                  and len(r["embedding"])==len(query["embedding"]) for r in others),
              "V34_EMBEDDING_MODEL_VERSION_OR_DIMENSION_DRIFT")
        vector_scores={r["claim_id"]:sum(x*y for x,y in zip(query["embedding"],r["embedding"]))
                       for r in others}
    lanes=[words,chars,sem]
    if graph:lanes.append(dict(graph))
    if vector_scores:lanes.append(vector_scores)
    fused=defaultdict(float);lane_ranks={}
    for j,lane in enumerate(lanes):
        ranked=sorted(((score,cid) for cid,score in lane.items() if score>0),
                      key=lambda v:(-v[0],v[1]))
        lane_ranks[str(j)]=len(ranked)
        for rank,(_,cid) in enumerate(ranked,1):
            fused[cid]+=1.0/(60.0+rank)
    # Always include zero-signal records at the tail, without falsely
    # treating missing events as irrelevant. The audit covers the complement.
    ranked_ids=sorted(others,key=lambda r:(-fused.get(r["claim_id"],0),
                                           r["claim_id"]))
    hits=[]
    for rank,r in enumerate(ranked_ids[:top_k],1):
        hits.append({
            "rank":rank, "claim_id":r["claim_id"],
            "score_rrf":round(fused.get(r["claim_id"],0.0),9),
            "video_number":r["video_number"],
            "source_srt_sha256":r["source_srt_sha256"],
            "source_record_digest":r["source_record_digest"],
            "provenance_state":r["provenance_state"],
            "relation":relation_triage(query,r),
            "review_required":True
        })
    remaining=ranked_ids[top_k:]
    # Deterministic audit sampling is diagnostic, NOT unbiased human gold.
    audit_ids=[r["claim_id"] for r in
       sorted(remaining,key=lambda r:sha256(canonical(
           [query["claim_id"],r["claim_id"])))[:audit_count]]
    return {
        "schema":RELATION_SCHEMA,
        "query_claim_id":query["claim_id"],
        "index_claim_count":len(corpus),
        "searchable_complement_count":len(remaining),
        "retrieval_lanes":lane_ranks,
        "hits":hits,"noncandidate_audit_ids":audit_ids,
        "blind_recall_at_k":None,
        "blind_precision_at_k":None,
        "human_labeled_gold_available":False,
        "all_hits_review_only":True,
        "automatic_knowledge_merge":False,
        "research_completion":False
    }

def history_record(x):
    """Read-only adapter for frozen 4,120-claim historical crosswalk."""
    guard(type(x) is dict and type(x.get("roster_no")) is int
          and 1<=x["roster_no"]<=260 and type(x.get("claim_id")) is str
          and (x.get("video_id")==x["claim_id"][:11] or
               (x["roster_no"]==71 and x["claim_id"].startswith("71-PUBLIC-"))),
          "V34_HISTORICAL_SOURCE_CROSSWALK_INVALID")
    return {
        "claim_id":x["claim_id"],"text":x["text"],
        "video_number":x["roster_no"],
        "source_sha256":x.get("source_srt_sha"),
        "source_record_digest":sha256(canonical({
            "claim_id":x["claim_id"],"text":x["text"],
            "source_canonical_sha":x.get("source_canonical_sha"),
            "source_pilot_sha":x.get("source_pilot_sha")})),
        "provenance_state":("ORIGINAL_SHA_VERIFIED" if x.get("source_srt_sha")
                            else "HISTORIC_ORIGINAL_SHA_MISSING"),
        "verdict":x.get("original_verdict","UNREVIEWED")
    }

def indexed_historical_claim(x):
    r=history_record(x)
    return make_record(r["claim_id"],r["text"],r["video_number"],
                       r["source_sha256"],r["verdict"],
                       provenance_state=r["provenance_state"],
                       source_record_digest=r["source_record_digest"])
