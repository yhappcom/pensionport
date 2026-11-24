"""V3 source-coordinate semantic graph, not a semantic classifier.

Source-only grid is frozen before either review. Nodes and adjudications are
ChatGPT-authored, separately frozen. A coordinate overlap is a diagnostic,
never a match or proof of completeness. No finance/knowledge release here.
"""
from __future__ import annotations
from collections import defaultdict
import re
from .atomic_exchange import COMPLETE_NUMBER
from .codec import canonical,json_digest,sha256
from .errors import InvalidInput
from .gold_eval import MATCH_FIELDS

RUBRIC={
 "id":"IRE_SOURCE_COORDINATE_GRAPH_V3",
 "coordinate":"Exact parsed SRT cue index and half-open Unicode codepoint interval; preserve original raw SHA.",
 "unit":"One independently assessable predicate, with direct source spans; shared anchors are allowed but not automatic equivalence.",
 "speaker":"Textual participant ID separate from utterance act; unknown stays unknown, no audio authentication.",
 "scope":"Qualifier edges attach to their own predicate, not surrounding window.",
 "number":"Literal original spans in source order; adjacent cue continuation can join only boundary fragments forming a complete numeric token.",
 "residual":"Every nonspace source character is direct, support, explicitly nonclaim or open; no silent gap.",
 "evaluation":"Overlap components are diagnostics. Exact one-to-one nine-axis judgment and existing thresholds unchanged; no score from overlap.",
}
RUBRIC_SHA256=json_digest(RUBRIC)
ACTS={"ASSERTION","QUESTION","RECOMMENDATION","EVALUATION","CALCULATION","OTHER"}
KINDS={"FACT","OPINION","QUESTION","RECOMMENDATION","HYPOTHETICAL","MATH"}
MODES={"ASSERTED","CONDITIONAL","HYPOTHETICAL","QUESTION","UNRESOLVED"}
ATTR={"DIRECT","REPORTED","UNRESOLVED"}
POL={"AFFIRMED","NEGATED","UNRESOLVED"}

def _need(ok,label):
    if not ok:raise InvalidInput("SOURCE_GRAPH_"+label)

def _note(x):
    return type(x) is str and 4<=len(x.strip())<=2000

def _rows_digest(rows):
    # Bounded individual canonical records rather than a monolithic event.
    return sha256("".join(json_digest(x)+"\n" for x in rows).encode("ascii"))

def source_grid(source):
    _need(source.scope_first_cue==1 and source.scope_last_cue==len(source.cues),"FULL_SOURCE")
    rows=[{"cue_index":i,"length":len(c.text),"text_sha256":sha256(c.text.encode("utf8"))}
          for i,c in enumerate(source.cues,1)]
    return {"schema":"IRE_V3_SOURCE_COORDINATE_GRID_V1","rubric_sha256":RUBRIC_SHA256,
            "video_id":source.video_id,"source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,"cue_count":len(rows),
            "coordinate_census_sha256":_rows_digest(rows)}

def _span(source,raw):
    _need(type(raw) is list and len(raw)==3 and all(type(v) is int for v in raw),"SPAN_SHAPE")
    i,a,b=raw
    _need(1<=i<=len(source.cues) and 0<=a<b<=len(source.cues[i-1].text),"SPAN_RANGE")
    return (i,a,b)

def _text(source,span):
    i,a,b=span
    return source.cues[i-1].text[a:b]

def _spans(source,values,*,nonempty=False):
    _need(type(values) is list and (bool(values) or not nonempty),"SPAN_LIST")
    result=[_span(source,r) for r in values]
    _need(result==sorted(set(result)),"SPAN_ORDER_OR_DUPLICATE")
    for a,b in zip(result,result[1:]):
        _need(a[0]!=b[0] or a[2]<=b[1],"SPAN_SELF_OVERLAP")
    return result

def _contained(span,others):
    i,a,b=span
    return any(j==i and x<=a and b<=y for j,x,y in others)

def _intersection(a,b):
    return a[0]==b[0] and max(a[1],b[1])<min(a[2],b[2])

def numeric_binding(source,parts):
    """Reconstruct only actual source literal, never corrected ASR/derived value."""
    p=_spans(source,parts,nonempty=True)
    _need(len(p)<=8,"NUMBER_TOO_MANY_PARTS")
    if len(p)>1:
        for a,b in zip(p,p[1:]):
            _need(b[0]==a[0]+1 and
                  not source.cues[a[0]-1].text[a[2]:].strip() and
                  not source.cues[b[0]-1].text[:b[1]].strip(),"NUMBER_NONCONTIGUOUS")
    literal=" ".join(_text(source,x).strip() for x in p)
    _need(bool(COMPLETE_NUMBER.fullmatch(literal)),"NUMBER_NOT_COMPLETE_LITERAL")
    # Reject truncation of a recognized complete token in the joined context.
    first,last=p[0],p[-1]
    # A standalone magnitude at the end of one cue may be truncated by
    # the currency/unit at the start of the next. Include adjacent cues
    # when checking lexical boundaries, never silently accept a fragment.
    # This is a conservative source warning, not automatic numerical truth.
    left=max(1,first[0]-1);right=min(len(source.cues),last[0]+1)
    texts=[source.cues[i-1].text for i in range(left,right+1)]
    combined=" ".join(texts)
    start=sum(len(t)+1 for t in texts[:first[0]-left])+first[1]
    end=sum(len(t)+1 for t in texts[:last[0]-left])+last[2]
    _need(any(m.start()==start and m.end()==end for m in COMPLETE_NUMBER.finditer(combined)),
          "NUMBER_BOUNDARY")
    return {"parts":[list(x) for x in p],"literal":literal,
            "literal_sha256":sha256(literal.encode("utf8")),"cross_cue":len(p)>1}

def _speaker(source,value,scope):
    _need(type(value) is dict and set(value)=={"participant_id","status","evidence","reason"} and
          _note(value["reason"]),"SPEAKER_SCHEMA")
    s=value["participant_id"];status=value["status"]
    evidence=_spans(source,value["evidence"])
    _need(type(s) is str and status in ("TEXT_INFERRED","UNRESOLVED") and
          all(_contained(x,scope) for x in evidence),"SPEAKER_EVIDENCE")
    _need((status=="UNRESOLVED" and s=="UNKNOWN") or
          (status=="TEXT_INFERRED" and re.fullmatch(r"S[0-9]{5}",s) and bool(evidence)),
          "SPEAKER_IDENTITY_NOT_PROVEN")
    return {"participant_id":s,"status":status,"evidence":[list(x) for x in evidence],"reason":value["reason"]}

def compile_graph(source,packet):
    """Compile explicit graph and exact character disposition ledger.

    The graph stays private. A broad direct span is not proof that its words
    entail the proposition; reviewer reasoning and later challenge required.
    """
    grid=source_grid(source)
    _need(type(packet) is dict and set(packet)=={"schema","grid_sha256","nodes","residual"} and
          packet["schema"]=="IRE_V3_SEMANTIC_GRAPH_PACKET_V1" and
          packet["grid_sha256"]==json_digest(grid),"PACKET")
    rows=packet["nodes"];residual=packet["residual"]
    _need(type(rows) is list and 0<len(rows)<=10000 and type(residual) is list,"ROWS")
    events=defaultdict(list);nodes={};duplicate=set();unbound=[]
    for n,row in enumerate(rows,1):
        cid=f"A{n:05d}"
        _need(type(row) is dict and set(row)=={"predicate","atomicity_reason","kind","utterance_act",
              "speaker","attribution","attributed_participant","polarity","modality","correction","as_of",
              "direct","context","qualifiers","numbers","risk","risk_reason"},"NODE_SCHEMA")
        _need(_note(row["predicate"]) and _note(row["atomicity_reason"]) and _note(row["risk_reason"]) and
              row["kind"] in KINDS and row["utterance_act"] in ACTS and row["attribution"] in ATTR and
              row["polarity"] in POL and row["modality"] in MODES and type(row["correction"]) is bool and
              row["risk"] in ("HIGH","NORMAL") and (row["as_of"] is None or _note(row["as_of"])),"NODE_SEMANTICS")
        _need((row["kind"]=="QUESTION")== (row["utterance_act"]=="QUESTION") and
              (row["modality"]=="QUESTION")== (row["utterance_act"]=="QUESTION"),"QUESTION_ACT")
        target=row["attributed_participant"]
        _need((row["attribution"]=="DIRECT" and target is None) or
              (row["attribution"]=="REPORTED" and type(target) is str and
               (target=="UNKNOWN" or bool(re.fullmatch(r"S[0-9]{5}",target)))) or
              (row["attribution"]=="UNRESOLVED" and target=="UNKNOWN"),"ATTRIBUTION_TARGET")
        _need(not (row["correction"] and row["attribution"]=="REPORTED"),"CORRECTION_SCOPE")
        direct=_spans(source,row["direct"],nonempty=True)
        context=_spans(source,row["context"])
        _need(all(_text(source,x).strip() for x in direct),"EMPTY_DIRECT")
        q=row["qualifiers"];_need(type(q) is list,"QUALIFIERS")
        qs=[];qseen=set()
        for e in q:
            _need(type(e) is dict and set(e)=={"type","span","reason"} and
                  e["type"] in ("CONDITION","EXCEPTION") and _note(e["reason"]),"QUALIFIER_EDGE")
            sp=_span(source,e["span"]);_need(bool(_text(source,sp).strip()),"EMPTY_QUALIFIER")
            k=(e["type"],sp);_need(k not in qseen,"DUPLICATE_QUALIFIER");qseen.add(k);qs.append(sp)
        _need(row["modality"]!="CONDITIONAL" or any(e["type"]=="CONDITION" for e in q),"CONDITION_MISSING")
        speaker=_speaker(source,row["speaker"],direct+context+qs)
        numbers=[];parts=[];nseen=set()
        _need(type(row["numbers"]) is list,"NUMBERS")
        for b in row["numbers"]:
            _need(type(b) is dict and set(b)=={"parts","function","reason"} and
                  b["function"] in ("AMOUNT","RATE","DURATION","COUNT","DATE","RATIO","OTHER") and
                  _note(b["reason"]),"NUMBER_BINDING")
            value=numeric_binding(source,b["parts"])
            pp=[tuple(x) for x in value["parts"]]
            _need(all(_contained(x,direct+qs) for x in pp),"NUMBER_OUTSIDE_PREDICATE")
            key=tuple(pp);_need(key not in nseen,"DUPLICATE_NUMBER");nseen.add(key);parts+=pp
            numbers.append({**value,"function":b["function"],"reason":b["reason"]})
        # Every recognized numeric substring in the governing evidence must
        # be explicitly bound, otherwise remain a diagnostic blocker.
        for sp in sorted(set(direct+qs)):
            i,a,b=sp
            for m in COMPLETE_NUMBER.finditer(_text(source,sp)):
                z=(i,a+m.start(),a+m.end())
                if not _contained(z,parts):
                    unbound.append({"atom_id":cid,"span":list(z)})
        for kind,spans in (("DIRECT",direct),("SUPPORT",context+qs)):
            for i,a,b in spans:events[i].append((a,b,kind,cid))
        node={**row,"speaker":speaker,"numbers":numbers,"atom_id":cid}
        key=json_digest({k:v for k,v in node.items() if k not in ("atom_id","atomicity_reason","risk_reason")})
        _need(key not in duplicate,"DUPLICATE_NODE");duplicate.add(key);nodes[cid]=node
    for r in residual:
        _need(type(r) is dict and set(r)=={"span","status","reason"} and
              r["status"] in ("NONCLAIM","OPEN") and _note(r["reason"]),"RESIDUAL")
        i,a,b=_span(source,r["span"]);events[i].append((a,b,r["status"],None))
    census=[];counts=defaultdict(int)
    for i,c in enumerate(source.cues,1):
        text=c.text;edges=events[i]
        bounds=sorted({0,len(text)}|{p for a,b,_,_ in edges for p in (a,b)})
        for a,b in zip(bounds,bounds[1:]):
            if not text[a:b].strip():continue
            owners=[(k,x) for l,r,k,x in edges if l<=a and b<=r]
            primary=sorted({x for k,x in owners if k=="DIRECT"})
            supporting=sorted({x for k,x in owners if k=="SUPPORT"})
            rest=[k for k,x in owners if k in ("NONCLAIM","OPEN")]
            _need(not (rest and (primary or supporting)) and len(rest)<=1,"RESIDUAL_CONFLICT")
            status="DIRECT" if primary else "SUPPORT" if supporting else rest[0] if rest else None
            _need(status is not None,"SILENT_SOURCE_GAP")
            counts[status]+=b-a
            census.append({"span":[i,a,b],"status":status,"direct_ids":primary,"support_ids":supporting,
                           "text_sha256":sha256(text[a:b].encode("utf8"))})
    return {"schema":"IRE_V3_COMPILED_SOURCE_GRAPH_V1","grid":grid,
            "grid_sha256":json_digest(grid),"packet_sha256":_rows_digest([{"schema":packet["schema"],
              "grid_sha256":packet["grid_sha256"]}]+rows+residual),
            "nodes":nodes,"census":census,"census_sha256":_rows_digest(census),
            "character_dispositions":dict(counts),"unbound_numeric_spans":unbound,
            "source_cue_count":len(source.cues),"speaker_identity_authenticated":False,
            "semantic_truth_certified":False,"publication_authorized":False}

def overlap_components(left,right):
    """Connected components of actual source-span intersections, no match claim."""
    _need(type(left) is dict and type(right) is dict,"OVERLAP_INPUT")
    by_cue=defaultdict(list)
    for cid,spans in right.items():
        for i,a,b in spans:by_cue[i].append((a,b,cid))
    adj=defaultdict(set)
    for cid,spans in left.items():
        for i,a,b in spans:
            for x,y,gid in by_cue[i]:
                if max(a,x)<min(b,y):
                    adj[("L",cid)].add(("R",gid));adj[("R",gid)].add(("L",cid))
    vertices={("L",x) for x in left}|{("R",x) for x in right}
    out=[]
    while vertices:
        stack=[min(vertices)];seen=set()
        while stack:
            v=stack.pop()
            if v in seen:continue
            seen.add(v);stack.extend(adj[v]-seen)
        vertices-=seen
        l=sorted(x for side,x in seen if side=="L");r=sorted(x for side,x in seen if side=="R")
        shape=("REFERENCE_ONLY" if not l else "PREDICTION_ONLY" if not r else
               "ONE_TO_ONE" if len(l)==len(r)==1 else "SPLIT_CANDIDATE" if len(l)==1 else
               "MERGE_CANDIDATE" if len(r)==1 else "MANY_TO_MANY")
        out.append({"prediction_ids":l,"reference_ids":r,"shape":shape})
    return out

def legacy_quote_spans(source,atoms,id_key):
    """Exact unique legacy quote offsets; ambiguous repeats remain unresolved."""
    result={};unresolved=[]
    for a in atoms:
        cid=a[id_key];result[cid]=[]
        for r in a["source_refs"]:
            i=r["cue_index"];quote=r["quote"];text=source.cues[i-1].text
            starts=[m.start() for m in re.finditer("(?="+re.escape(quote)+")",text)] if quote else []
            if len(starts)!=1:
                unresolved.append({"atom_id":cid,"cue_index":i,"occurrences":len(starts)})
                continue
            result[cid].append([i,starts[0],starts[0]+len(quote)])
    return result,unresolved

def compare_graphs(first,second):
    _need(first["grid_sha256"]==second["grid_sha256"],"GRID_DRIFT")
    return {"schema":"IRE_V3_SOURCE_OVERLAP_DIAGNOSTIC_V1",
      "components":overlap_components({k:v["direct"] for k,v in first["nodes"].items()},
                                     {k:v["direct"] for k,v in second["nodes"].items()}),
      "semantic_equivalence_proven":False,"tp":None,"fp":None,"fn":None,
      "publication_authorized":False}

def score_graphs(source,first_packet,second_packet,alignment):
    """Internal strict nine-axis arithmetic; not an enrolled release evaluator.

    Both packets are recompiled. Source overlap never produces TP. Participant
    alias mapping is explicit reviewer evidence, not an authenticated identity.
    A separate preregistration/freeze/CI gate and E3-E5 bridge are still needed.
    """
    a=compile_graph(source,first_packet);b=compile_graph(source,second_packet)
    _need(a["packet_sha256"]!=b["packet_sha256"],"COPIED_PACKET")
    _need(type(alignment) is dict and set(alignment)=={"first_packet_sha256","second_packet_sha256",
          "speaker_aliases","pairs","unmatched_prediction_ids","unmatched_reference_ids","unmatched_reasons"} and
          alignment["first_packet_sha256"]==a["packet_sha256"] and
          alignment["second_packet_sha256"]==b["packet_sha256"],"ALIGNMENT_LOCK")
    l=a["nodes"];r=b["nodes"];aliases=set();la=set();ra=set()
    _need(type(alignment["speaker_aliases"]) is list and type(alignment["pairs"]) is list,"ALIGNMENT_ROWS")
    lp={n["speaker"]["participant_id"] for n in l.values()}|{n["attributed_participant"] for n in l.values()}
    rp={n["speaker"]["participant_id"] for n in r.values()}|{n["attributed_participant"] for n in r.values()}
    for m in alignment["speaker_aliases"]:
        _need(type(m) is dict and set(m)=={"first","second","reason","evidence"} and _note(m["reason"]) and
              type(m["first"]) is str and type(m["second"]) is str and
              m["first"] in lp and m["second"] in rp and m["first"]!="UNKNOWN" and m["second"]!="UNKNOWN" and
              m["first"] not in la and m["second"] not in ra and
              bool(_spans(source,m["evidence"],nonempty=True)),"SPEAKER_ALIAS")
        aliases.add((m["first"],m["second"]));la.add(m["first"]);ra.add(m["second"])
    seenl=set();seenr=set();tp=0;hit=set();critical=0;axis_mismatch=defaultdict(int)
    for pair in alignment["pairs"]:
        _need(type(pair) is dict and set(pair)=={"prediction_id","reference_id","axes","reasons"},"PAIR")
        x,y=pair["prediction_id"],pair["reference_id"]
        _need(type(x) is str and type(y) is str and x in l and y in r and x not in seenl and y not in seenr,"PAIR_ONE_TO_ONE")
        seenl.add(x);seenr.add(y);u,v=l[x],r[y];d=pair["axes"];why=pair["reasons"]
        _need(type(d) is dict and set(d)==set(MATCH_FIELDS) and all(type(z) is bool for z in d.values()) and
              type(why) is dict and set(why)==set(MATCH_FIELDS) and all(_note(z) for z in why.values()),"NINE_AXES")
        if d["speaker_and_stance"]:
            _need((u["speaker"]["participant_id"],v["speaker"]["participant_id"]) in aliases and
                  all(u[k]==v[k] for k in ("utterance_act","attribution","polarity","modality","correction")) and
                  (u["attribution"]=="DIRECT" or (u["attributed_participant"],v["attributed_participant"]) in aliases),
                  "FALSE_SPEAKER_MATCH")
        if d["claim_kind"]:_need(u["kind"]==v["kind"],"FALSE_KIND_MATCH")
        if d["negation_and_rebuttal"]:_need((u["polarity"],u["correction"])==(v["polarity"],v["correction"]),"FALSE_POLARITY_MATCH")
        if d["hypothetical_or_actual_scope"]:_need(u["modality"]==v["modality"],"FALSE_MODALITY_MATCH")
        if d["numeric_value_and_unit"]:
            signature=lambda z:sorted((re.sub(r"\s+","",n["literal"]),n["function"]) for n in z["numbers"])
            _need(signature(u)==signature(v),"FALSE_NUMERIC_MATCH")
        for typ,axis in (("CONDITION","conditions"),("EXCEPTION","exceptions")):
            if d[axis]:_need(bool([q for q in u["qualifiers"] if q["type"]==typ])==
                            bool([q for q in v["qualifiers"] if q["type"]==typ]),"FALSE_QUALIFIER_MATCH")
        for k,z in d.items():axis_mismatch[k]+=not z
        critical+=not all(d[k] for k in ("conditions","exceptions","numeric_value_and_unit"))
        if all(d.values()):tp+=1;hit.add(y)
    for side,seen,allnodes in (("prediction",seenl,l),("reference",seenr,r)):
        ids=alignment["unmatched_"+side+"_ids"]
        _need(type(ids) is list and all(type(x) is str for x in ids) and len(ids)==len(set(ids)) and
              set(ids)==set(allnodes)-seen,"UNMATCHED_CENSUS")
    expected={"prediction:"+x for x in set(l)-seenl}|{"reference:"+x for x in set(r)-seenr}
    reasons=alignment["unmatched_reasons"]
    _need(type(reasons) is dict and set(reasons)==expected and all(_note(x) for x in reasons.values()),"UNMATCHED_REASONS")
    high={k for k,v in r.items() if v["risk"]=="HIGH"}
    critical_unmatched=sum(bool(z["numbers"] or z["qualifiers"]) for k,z in l.items() if k not in seenl)+sum(
                           bool(z["numbers"] or z["qualifiers"]) for k,z in r.items() if k not in seenr)
    opened=a["character_dispositions"].get("OPEN",0)+b["character_dispositions"].get("OPEN",0)
    numeric_open=len(a["unbound_numeric_spans"])+len(b["unbound_numeric_spans"])
    met=bool(high and tp*10000>=9500*len(l) and tp*10000>=9800*len(r) and not(high-hit) and
             critical==critical_unmatched==opened==numeric_open==0)
    return {"schema":"IRE_V3_INTERNAL_GRAPH_SCORE_DIAGNOSTIC_V1","first_packet_sha256":a["packet_sha256"],
            "second_packet_sha256":b["packet_sha256"],"tp":tp,"fp":len(l)-tp,"fn":len(r)-tp,
            "precision_bp":tp*10000//len(l),"recall_bp":tp*10000//len(r),"high_risk_fn":len(high-hit),
            "critical_pair_mismatches":critical,"critical_unmatched_atoms":critical_unmatched,
            "open_source_characters":opened,"unbound_numeric_spans":numeric_open,
            "axis_mismatches":dict(axis_mismatch),"thresholds_met_on_supplied_internal_graphs":met,
            "independent_gold_verified":False,"operational_release_authorized":False,
            "research_publication_authorized":False}
