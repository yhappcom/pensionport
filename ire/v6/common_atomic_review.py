"""Common prospective source-first atomic review contract for both chat turns.

No automatic meaning inference. One reviewer-authored decision predicate per
atom; all source references/qualifiers/roles are explicit. Both passes compile
through the same path; a reference cannot be constructed from a candidate
projection or a different ad hoc atom schema. Structural checks do not prove
semantic correctness or independence.
"""
from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from .atomic_exchange import NUMBER, COMPLETE_NUMBER, audit_host_atomic_exchange
from .chat_revision import _project, _FRAME_KEYS
from .codec import json_digest, sha256
from .errors import InvalidInput
from .numeric_provenance import audit_numeric_reference_boundaries

RUBRIC={
    "id":"IRE_COMMON_ATOMIC_RUBRIC_V2",
    "unit":"One independently falsifiable assertion, recommendation, calculation or question per atom; split if either can be true or applicable without the other.",
    "repeat":"Repeated same meaning and same scope share one atom; separate distinct times, conditions, speakers or propositions.",
    "question":"Question and answer are separate units; reported speech is not endorsement.",
    "qualifiers":"Conditions and exceptions belong to their governing predicate; do not split into standalone claims unless independently asserted.",
    "numbers":"Exact numeric spans with units must be within direct or explicit qualifier quotes; literal ASR is not corrected without evidence.",
    "roles":"Role, attribution, polarity, modality and correction are separate dimensions; unknown identity is not a verified speaker.",
    "cue_census":"Review every cue, distinguish direct proposition, supporting context, nonclaim and unresolved; never silently suppress.",
    "scope":"Source assertions are not current financial truth; high risk review is separate."
}
RUBRIC_SHA256=json_digest(RUBRIC)


def _need(ok,label):
    if not ok:raise InvalidInput("COMMON_ATOM_"+label)


def _reason(x):
    return type(x) is str and 5<=len(x.strip())<=1000


def source_packet(source):
    return {"schema":"IRE_COMMON_ATOMIC_SOURCE_PACKET_V2","rubric_sha256":RUBRIC_SHA256,
            "video_id":source.video_id,"source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,"cue_count":len(source.cues)}


def compile_review(source, packet):
    """Return both native prediction and reference projections of one typed review.

    Call on independently authored first/second turn packets, not the same
    packet twice. IDs are local to each pass. The native projection can lose
    typed stance information; the typed frame is always retained for matching.
    """
    _need(type(packet) is dict and set(packet)=={"schema","source_packet_sha256","atoms","cue_reviews"} and
          packet["schema"]=="IRE_COMMON_ATOMIC_REVIEW_V2" and
          packet["source_packet_sha256"]==json_digest(source_packet(source)),"PACKET")
    allowed=set(range(1,len(source.cues)+1))
    _need(source.scope_first_cue==1 and source.scope_last_cue==len(source.cues),"FULL_SOURCE")
    records=packet["atoms"];reviews=packet["cue_reviews"]
    _need(type(records) is list and 0<len(records)<=10000 and
          type(reviews) is list and len(reviews)==len(allowed),"CENSUS")
    atoms=[];gold=[];typed={};by_cue=defaultdict(list);context=defaultdict(list);keys=set()
    for n,row in enumerate(records,1):
        cid=f"C{n:05d}";gid=f"G{n:05d}"
        _need(type(row) is dict and set(row)=={"frame","unit","qualifiers","risk","risk_reason"},"ROW")
        f=row["frame"];u=row["unit"];q=row["qualifiers"]
        _need(type(f) is dict and set(f)==_FRAME_KEYS,"FRAME")
        _need(type(u) is dict and set(u)=={"subject","predicate","object","atomicity_reason"} and
              all(_reason(x) for x in u.values()),"ATOMIC_UNIT")
        _need(row["risk"] in ("HIGH","NORMAL") and _reason(row["risk_reason"]),"RISK")
        atom,overlay=_project(source,f,cid)
        # Explicit quoted qualifier edges. A cue cannot silently be a
        # condition for one claim and an exception for another by default.
        _need(type(q) is list,"QUALIFIER_LIST")
        actual=set();quoted=defaultdict(list)
        for ref in atom["source_refs"]:quoted[ref["cue_index"]].append(ref["quote"])
        for edge in q:
            _need(type(edge) is dict and set(edge)=={"type","cue_index","quote","reason"} and
                  edge["type"] in ("CONDITION","EXCEPTION") and
                  type(edge["cue_index"]) is int and edge["cue_index"] in allowed and
                  type(edge["quote"]) is str and len(edge["quote"].strip())>=2 and
                  edge["quote"] in source.cues[edge["cue_index"]-1].text and _reason(edge["reason"]),
                  "QUALIFIER_EDGE")
            k=(edge["type"],edge["cue_index"])
            _need(k not in actual,"DUPLICATE_QUALIFIER")
            actual.add(k);quoted[k[1]].append(edge["quote"])
        expected={("CONDITION",i) for i in atom["condition_cue_indices"]}|{
                  ("EXCEPTION",i) for i in atom["exception_cue_indices"]}
        _need(actual==expected,"QUALIFIER_GRAPH")
        # A number appearing somewhere in the context does not establish
        # its link to this predicate. Explicit governing quote required.
        for nr in atom["numeric_references"]:
            _need(any(nr["token"] in COMPLETE_NUMBER.findall(quote)
                      for quote in quoted[nr["cue_index"]]),"NUMERIC_NOT_IN_GOVERNING_QUOTE")
        _need(not audit_numeric_reference_boundaries(source.cues,[atom]),"NUMERIC_BOUNDARY")
        k=json_digest({key:value for key,value in atom.items() if key!="claim_id"})
        _need(k not in keys,"DUPLICATE_NATIVE");keys.add(k)
        atoms.append(atom)
        typed[cid]={"gold_id":gid,"unit":deepcopy(u),"qualifiers":deepcopy(q),
                    "overlay":overlay,"risk":row["risk"],"risk_reason":row["risk_reason"]}
        gold.append({"gold_id":gid,"kind":atom["kind"],"risk":row["risk"],
                     "proposition":atom["proposition"],
                     "speaker_stance":"|".join(str(f[key]) for key in
                         ("role","attribution","polarity","modality","correction")),
                     "as_of":f["as_of"] or "UNSPECIFIED","high_risk_reason":row["risk_reason"],
                     "source_refs":deepcopy(atom["source_refs"]),
                     "conditions":[deepcopy(e) for e in q if e["type"]=="CONDITION"],
                     "exceptions":[deepcopy(e) for e in q if e["type"]=="EXCEPTION"],
                     "numeric_evidence":deepcopy(atom["numeric_references"])})
        for ref in atom["source_refs"]:by_cue[ref["cue_index"]].append(cid)
        for i in atom["context_cue_indices"]:context[i].append(cid)
    native_rows=[];gold_rows=[]
    for i,r in enumerate(reviews,1):
        cue=source.cues[i-1];digest=sha256(cue.text.encode("utf8"))
        _need(type(r) is dict and set(r)=={"cue_index","cue_text_sha256","status","reason"} and
              type(r["cue_index"]) is int and r["cue_index"]==i and
              r["cue_text_sha256"]==digest and _reason(r["reason"]),"CUE_REVIEW")
        status=r["status"];ids=sorted(by_cue[i])
        _need(status in ("DIRECT","CONTEXT","NONCLAIM","OPEN"),"CUE_STATUS")
        _need((bool(ids)==(status=="DIRECT")) and
              (status!="CONTEXT" or bool(context[i])) and
              (status!="NONCLAIM" or not context[i]),"CUE_LINK")
        # OPEN may retain contextual evidence but no unreviewed direct claim.
        native_rows.append({"cue_index":i,"cue_text_sha256":digest,"claim_ids":ids,
                            "disposition":"CANDIDATES" if ids else "UNRESOLVED" if status=="OPEN" else "NO_ATOM",
                            "numeric_tokens":NUMBER.findall(cue.text),"note":r["reason"][:256]})
        gold_rows.append({"cue_index":i,"source_quote_sha256":digest,
                          "status":"REVIEWED_ATOM" if ids else "OPEN_UNCERTAIN" if status=="OPEN" else "NO_ATOM",
                          "gold_atom_ids":[typed[c]["gold_id"] for c in ids],"reason":r["reason"]})
    exchange={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1","video_id":source.video_id,
              "source_sha256":source.source_sha256,"manifest_sha256":source.manifest_sha256,
              "cue_dispositions":native_rows,"atoms":atoms}
    reference={"schema":"IRE_P205_PRIVATE_GOLD_ATOMIC_REVIEW_V1","source_srt_sha256":source.source_sha256,
               "reviewed_cues":gold_rows,"atomic_gold_claims":gold}
    audit=audit_host_atomic_exchange(source,exchange)
    return {"exchange":exchange,"reference":reference,"typed":typed,"audit":audit,
            "rubric_sha256":RUBRIC_SHA256,"packet_sha256":json_digest(packet),
            "independent_gold_verified":False}


def check_exact_typed_axes(first,second,alignment):
    """Reject an asserted exact role match despite incompatible typed roles.

    Other semantic comparisons (e.g. equivalent differently worded
    conditions) remain explicit human/model adjudication, not automatic TP.
    """
    by_gold={row["gold_id"]:row for row in second["typed"].values()}
    for pair in alignment["pairs"]:
        a=first["typed"].get(pair["claim_id"]);b=by_gold.get(pair["gold_id"])
        _need(a is not None and b is not None,"FOREIGN_ALIGNMENT")
        dims=pair["match_dimensions"]
        if dims["speaker_and_stance"]:
            _need(all(a["overlay"][k]==b["overlay"][k] for k in
                  ("role","attribution","polarity","modality","correction")),"FALSE_TYPED_ROLE_MATCH")
