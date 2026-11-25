"""R3-04 private two-turn research journal and revision custody.

This verifies supplied semantic decisions, not their truth. The journal's
observed timestamps/user labels are operator records, not authenticated host
events. It can detect modification relative to an externally retained head;
it cannot prevent an owner from rewriting a database and its external pins.
No E3/E4/E5 approval or operational release is produced.
"""
from __future__ import annotations
import json, os, re, sqlite3
from copy import deepcopy
from contextlib import closing
from pathlib import Path
from .codec import canonical,sha256,json_digest,require_hash
from .errors import InvalidInput
from .assessment_plan import timestamp,THRESHOLDS
from .semantic_source_graph import (compile_graph,source_grid,RUBRIC_SHA256,
    compare_graphs,score_graphs,_rows_digest,_span,_note)
from .source import verify_source

GENESIS="0"*64
KINDS=("REGISTER","FIRST","SECOND","SCORE","DISPUTES","REVISION","RECONCILIATION","SUCCESSOR")
LEGACY_KIND="LEGACY_RECONCILIATION"

def _allowed(previous_kind,kind):
    if previous_kind is None:return kind=="REGISTER"
    if previous_kind=="FIRST" and kind=="SOURCE_AUDIT_LEDGER":return True
    if previous_kind=="SOURCE_AUDIT_LEDGER" and kind=="SOURCE_AUDIT_SCORE":return True
    if previous_kind=="SOURCE_AUDIT_SCORE" and kind=="SOURCE_AUDIT_CANDIDATE":return True
    if previous_kind=="REGISTER" and kind==LEGACY_KIND:return True
    if previous_kind==LEGACY_KIND and kind=="SUCCESSOR":return True
    if previous_kind in ("SUCCESSOR","SUCCESSOR_AMENDMENT","PENDING_REVIEW") and kind=="SUCCESSOR_AMENDMENT":return True
    if previous_kind in ("SUCCESSOR","SUCCESSOR_AMENDMENT","PENDING_REVIEW") and kind=="PENDING_REVIEW":return True
    return previous_kind in KINDS[:-1] and kind==KINDS[KINDS.index(previous_kind)+1]
EXPOSED_IDS={"LVE7XN_esTc","BXjda2v6e-Q","Yd5qnDtW2TM"}
EXPOSED_SHAS={"e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b",
 "a2c3017542b2670a39d7fcd796f706e583006a4d0a043d26854f27fc6a1f50e1",
 "e67be6da14dc6eae2fe8172add56f2c98efb1e6e232587aaa591d8752b043792"}

def need(ok,why):
    if not ok:raise InvalidInput("V3_LINEAGE_"+why)

def _payload(value):
    # Large private packets must not be forced into the 1 MiB event codec.
    # Every top-level list row is independently canonicalized/size checked.
    def check(v,depth=0):
        need(depth<=32,"PAYLOAD_DEPTH")
        if type(v) is dict:
            for k,item in v.items():
                need(type(k) is str,"PAYLOAD_KEY");canonical(k);check(item,depth+1)
        elif type(v) is list:
            for item in v:check(item,depth+1)
        else:canonical(v)
    check(value)
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),
                   allow_nan=False).encode("utf8")
    need(len(raw)<=64*1024*1024,"PAYLOAD_LIMIT")
    return raw

# Prospective diagnostic only, never a legacy HOLDOUT or release.
PROSPECTIVE_PURPOSE="PROSPECTIVE_AUDIT_DIAGNOSTIC"
PROSPECTIVE_SPEC={"id":"IRE_PROSPECTIVE_AUDIT_DIAGNOSTIC_V1",
    "initial_metrics":"elementary source obligations and first propositions, separate from historical scores",
    "thresholds":{"precision_bp":9500,"recall_bp":9800,"high_risk_unresolved_max":0},
    "repeat_review_required":True,"high_risk_source_obligation_required":True,
    "screening_receipt_required":True,"release_authorized":False}
PROSPECTIVE_SHA256=json_digest(PROSPECTIVE_SPEC)
PROSPECTIVE_EXPOSED_IDS=EXPOSED_IDS|{"-lX8iJd-xDM","w8nnPJe8lmo"}
PROSPECTIVE_EXPOSED_SHAS=EXPOSED_SHAS|{
    "059484995ba7a84dd5ec21ed682a526b95832f65b56cea1cf48745548c2d8335",
    "08da1e9cd5f2ebba39e03844dd4b93e30185124feb4ffa9ef13ea5a283eb2924"}

def plan_for(source,*,campaign_id,engine_commit,registered_at,purpose,protocol_sha256=None,audit_sha256=None,screening_sha256=None):
    need(type(campaign_id) is str and bool(re.fullmatch(r"[A-Za-z0-9_-]{3,80}",campaign_id)),"CAMPAIGN")
    need(type(engine_commit) is str and bool(re.fullmatch(r"[0-9a-f]{40}",engine_commit)),"ENGINE")
    timestamp(registered_at)
    need(purpose in ("DEVELOPMENT","HOLDOUT",PROSPECTIVE_PURPOSE),"PURPOSE")
    prospective=purpose==PROSPECTIVE_PURPOSE
    if prospective:
        need(protocol_sha256 is not None and audit_sha256 is not None,"PROSPECTIVE_AUDIT_REQUIRED")
        need(source.video_id not in PROSPECTIVE_EXPOSED_IDS and source.source_sha256 not in PROSPECTIVE_EXPOSED_SHAS,"PROSPECTIVE_EXPOSED_SOURCE")
        need(type(screening_sha256) is str and bool(re.fullmatch(r"[0-9a-f]{64}",screening_sha256)) and screening_sha256!="0"*64,"PROSPECTIVE_SCREENING_PIN")
    else:need(screening_sha256 is None,"UNEXPECTED_SCREENING_PIN")
    need(purpose!="HOLDOUT" or (source.video_id not in EXPOSED_IDS and
        source.source_sha256 not in EXPOSED_SHAS),"EXPOSED_SOURCE")
    if protocol_sha256 is not None:
        from .semantic_authoring_protocol import PROTOCOL_SHA256
        need(protocol_sha256==PROTOCOL_SHA256,"AUTHORING_PROTOCOL")
        need(purpose!="HOLDOUT" or (source.video_id!="-lX8iJd-xDM" and source.source_sha256!="059484995ba7a84dd5ec21ed682a526b95832f65b56cea1cf48745548c2d8335"),"AUTHORING_EXPOSED_288")
    if audit_sha256 is not None:
        from .source_first_audit import AUDIT_SHA256
        need(protocol_sha256 is not None and audit_sha256==AUDIT_SHA256,"SOURCE_AUDIT_PLAN")
        need(purpose=="DEVELOPMENT" or prospective,"SOURCE_AUDIT_PROSPECTIVE_NOT_AUTHORIZED")
    return {"schema":"IRE_V3_GRAPH_RESEARCH_PLAN_V1"
      ,**({"prospective_policy_sha256":PROSPECTIVE_SHA256,"screening_sha256":screening_sha256} if prospective else {})
      ,**({"audit_sha256":audit_sha256} if audit_sha256 is not None else {}),"campaign_id":campaign_id,
      **({"protocol_sha256":protocol_sha256} if protocol_sha256 is not None else {}),
      "engine_commit_sha":engine_commit,"registered_at":registered_at,"purpose":purpose,
      "source_sha256":source.source_sha256,"video_id":source.video_id,
      "manifest_sha256":source.manifest_sha256,"grid_sha256":json_digest(source_grid(source)),
      "rubric_sha256":RUBRIC_SHA256,"thresholds":dict(THRESHOLDS)}

def prospective_diagnostic(source,plan,ledger,score,repeat_reviews):
    """Internal first-packet diagnostic; no promotion from corrected candidates."""
    from .source_audit_completion import review_repeats
    need(plan.get("purpose")==PROSPECTIVE_PURPOSE and plan.get("prospective_policy_sha256")==PROSPECTIVE_SHA256,"PROSPECTIVE_POLICY")
    repeat=review_repeats(source,ledger,repeat_reviews)
    need(repeat["ledger_sha256"]==score["ledger_sha256"],"PROSPECTIVE_LEDGER_DRIFT")
    high=sum(o["risk"]=="HIGH" for o in ledger["obligations"])
    met=bool(score["internal_thresholds_met"] and high and not repeat["open_segments"] and not repeat["open_numeric_occurrences"])
    return {"schema":"IRE_PROSPECTIVE_AUDIT_DIAGNOSTIC_RESULT_V1",
      "policy_sha256":PROSPECTIVE_SHA256,"plan_sha256":json_digest(plan),
      "initial_score_sha256":json_digest(score),"high_risk_source_obligations":high,
      "repeat_review":repeat,"diagnostic_thresholds_met":met,
      "independent_gold_verified":False,"operational_release_authorized":False,"publication_authorized":False}

def _atom_map(g):
    return g["nodes"]

def _edges(node):
    # Exact source-coordinate obligations; semantic equivalence is never
    # inferred from coordinate equality. Explicit disposal for each loss.
    out={}
    for n in node["numbers"]:
        item={"type":"NUMBER","parts":n["parts"],"function":n["function"],"literal":n["literal"]}
        out[json_digest(item)]=item
    for q in node["qualifiers"]:
        item={"type":q["type"],"span":q["span"]}
        out[json_digest(item)]=item
    return out

def adjudicate_disputes(source,first,second,rows):
    """One explicit verdict per overlap component, including one-to-one.

    A verdict is a research judgment. Even a verdict of equivalent does not
    change the strict score or prove that the two graphs are correct.
    """
    comps=compare_graphs(first,second)["components"]
    keys={json_digest(c):c for c in comps}
    need(type(rows) is list and len(rows)==len(keys),"DISPUTE_CENSUS")
    seen=set();open_count=0
    for row in rows:
        need(type(row) is dict and set(row)=={"component_sha256","verdict","reason","evidence"},"DISPUTE_ROW")
        key=row["component_sha256"]
        need(type(key) is str and key in keys and key not in seen,"DISPUTE_COMPONENT")
        seen.add(key);c=keys[key]
        need(row["verdict"] in ("EQUIVALENT","SPLIT_MERGE","PREDICTION_OMISSION",
            "REFERENCE_OMISSION","BOTH_NEED_CORRECTION","SEMANTIC_CONFLICT","OPEN"),"DISPUTE_VERDICT")
        need(_note(row["reason"]),"DISPUTE_REASON")
        need(type(row["evidence"]) is list and bool(row["evidence"]),"DISPUTE_EVIDENCE")
        anchors=[tuple(s) for g,ids in ((first,c["prediction_ids"]),(second,c["reference_ids"]))
                 for aid in ids for s in g["nodes"][aid]["direct"]]
        for sp in row["evidence"]:
            i,a,b=_span(source,sp)
            need(any(i==j and max(a,x)<min(b,y) for j,x,y in anchors),"DISPUTE_UNRELATED_EVIDENCE")
        if row["verdict"]=="EQUIVALENT":
            need(c["shape"]=="ONE_TO_ONE","MULTI_NOT_EXACT_EQUIVALENCE")
        if row["verdict"]=="SPLIT_MERGE":
            need(c["shape"] in ("SPLIT_CANDIDATE","MERGE_CANDIDATE","MANY_TO_MANY"),"SPLIT_MERGE_SHAPE")
        open_count+=row["verdict"]=="OPEN"
    return {"components":len(keys),"open_components":open_count,
            "dispute_sha256":_rows_digest(rows),"semantic_truth_certified":False}

def _lineage(source,old,new,rows):
    """Total, disjoint partition of old and new nodes for each parent graph.

    A lineage operation is not an accuracy credit. Loss of any original
    exact numeric/qualifier binding requires an explicit disposition linked
    to that original binding. Deletion of a high-risk node stays escrowed.
    """
    need(type(rows) is list and bool(rows),"LINEAGE_ROWS")
    before=old["nodes"];after=new["nodes"];seen_old=set();seen_new=set();escrow=[];counts={}
    for row in rows:
        need(type(row) is dict and set(row) in ({"old_ids","new_ids","operation","reason","losses","carries"},
             {"old_ids","new_ids","operation","reason","losses","carries","shared_qualifier_exclusions"}),"LINEAGE_ROW")
        a=row["old_ids"];b=row["new_ids"]
        need(type(a) is list and type(b) is list and all(type(x) is str for x in a+b) and
             (a or b) and len(set(a))==len(a) and len(set(b))==len(b) and
             set(a)<=set(before)-seen_old and set(b)<=set(after)-seen_new,"LINEAGE_PARTITION")
        seen_old.update(a);seen_new.update(b)
        op=row["operation"];need(type(op) is str,"OPERATION_TYPE");counts[op]=counts.get(op,0)+1
        need(_note(row["reason"]),"LINEAGE_REASON")
        if not a:need(op=="ADD","LINEAGE_SHAPE")
        elif not b:need(op=="RETIRE","LINEAGE_SHAPE")
        elif len(a)==len(b)==1:
            # Local IDs are not semantic fields.
            x={k:v for k,v in before[a[0]].items() if k!="atom_id"}
            y={k:v for k,v in after[b[0]].items() if k!="atom_id"}
            need(op==("KEEP" if x==y else "REVISE"),"LINEAGE_KEEP_FALSE")
        elif len(a)==1:need(op=="SPLIT","LINEAGE_SHAPE")
        elif len(b)==1:need(op=="MERGE","LINEAGE_SHAPE")
        else:need(op=="REPARTITION","LINEAGE_SHAPE")
        # Every old obligation must be preserved or explicitly disposed.
        # Distinct owners are retained even when their literal spans coincide.
        obligations={(x,d):v for x in a for d,v in _edges(before[x]).items()}
        destinations={x:_edges(after[x]) for x in b}
        # For split/merge the reviewer must specify which successor owns each
        # carried binding. Matching coordinates elsewhere cannot cover it.
        need(type(row["carries"]) is list,"CARRY_LIST")
        carried=set();carried_targets=set()
        for carry in row["carries"]:
            need(type(carry) is dict and set(carry)=={"old_id","edge_sha256","new_id","reason"}
                 and _note(carry["reason"]),"CARRY_ROW")
            k=(carry["old_id"],carry["edge_sha256"]);target=carry["new_id"]
            triple=(*k,target)
            need(k in obligations and triple not in carried_targets and target in destinations and
                 k[1] in destinations[target],"FALSE_CARRY")
            need(k not in carried or obligations[k]["type"] in ("CONDITION","EXCEPTION"),"MULTI_NUMBER_CARRY_REQUIRES_REVIEW")
            carried.add(k);carried_targets.add(triple)
        # Every exact qualifier candidate in a split/repartition must be
        # explicitly carried or excluded. An exclusion is not approval.
        required={(*k,target) for k in carried if obligations[k]["type"] in ("CONDITION","EXCEPTION")
                  for target,edges in destinations.items() if k[1] in edges} - carried_targets
        exclusions=row.get("shared_qualifier_exclusions",[])
        need(type(exclusions) is list,"SHARED_EXCLUSIONS_LIST")
        excluded=set()
        for e in exclusions:
            need(type(e) is dict and set(e)=={"old_id","edge_sha256","new_id","reason"} and _note(e["reason"]),"SHARED_EXCLUSION")
            triple=(e["old_id"],e["edge_sha256"],e["new_id"])
            need(triple in required and triple not in excluded,"SHARED_EXCLUSION_SCOPE")
            excluded.add(triple)
            escrow.append({"old_id":triple[0],"edge_sha256":triple[1],"new_id":triple[2],
                           "disposition":"SHARED_QUALIFIER_EXCLUSION_REQUIRES_E3"})
        need(excluded==required,"SHARED_QUALIFIER_TARGET_UNREVIEWED")
        missing={k:v for k,v in obligations.items() if k not in carried}
        need(type(row["losses"]) is list,"LOSS_LIST")
        seen=set()
        for loss in row["losses"]:
            need(type(loss) is dict and set(loss)=={"old_id","edge_sha256","disposition","reason","evidence"},"LOSS_ROW")
            k=(loss["old_id"],loss["edge_sha256"])
            need(k in missing and k not in seen and _note(loss["reason"]) and
                 loss["disposition"] in ("OPEN","RETIRED_UNSUPPORTED","REBOUND_REQUIRES_REVIEW"),"LOSS_DISPOSITION")
            seen.add(k);e=missing[k]
            anchors=e["parts"] if e["type"]=="NUMBER" else [e["span"]]
            need(type(loss["evidence"]) is list and bool(loss["evidence"]),"LOSS_EVIDENCE")
            for sp in loss["evidence"]:
                i,l,r=_span(source,sp)
                need(any(i==j and max(l,x)<min(r,y) for j,x,y in anchors),"LOSS_UNRELATED_EVIDENCE")
            escrow.append({"old_id":k[0],"edge_sha256":k[1],"disposition":loss["disposition"]})
        need(seen==set(missing),"UNACCOUNTED_NUMERIC_OR_QUALIFIER_LOSS")
        # Changed or retired high-risk meaning is never implicitly approved.
        if op!="KEEP":
            for x in a:
                if before[x]["risk"]=="HIGH":
                    escrow.append({"old_id":x,"disposition":"HIGH_RISK_CHANGE_REQUIRES_E3"})
    need(seen_old==set(before) and seen_new==set(after),"LINEAGE_INCOMPLETE")
    return {"operations":counts,"escrow":escrow,"lineage_sha256":_rows_digest(rows)}

def revision(source,first,second,packet,first_lineage,second_lineage):
    final=compile_graph(source,packet)
    a=_lineage(source,first,final,first_lineage);b=_lineage(source,second,final,second_lineage)
    return {"final_packet_sha256":final["packet_sha256"],"first_lineage":a,"second_lineage":b,
       "final_open_characters":final["character_dispositions"].get("OPEN",0),
       "unbound_numeric_spans":len(final["unbound_numeric_spans"]),
       "original_score_changed":False,"requires_e3_review":True,
       "publication_authorized":False}

def successor_revision(source,parent,plan,packet,lineage,new_edges):
    """General successor with explicit old/new edge custody; never approval.

    Parent and plan must already have been replayed from reconciliation.
    Prior obligations remain pinned to the historical graph. Candidate
    projections are review tasks, not newly approved ownership mappings.
    """
    from .semantic_source_graph import BOUNDARY_PACKET
    need(plan["source_sha256"]==source.source_sha256 and
         plan["draft_packet_sha256"]==parent["packet_sha256"],"SUCCESSOR_PARENT")
    need(packet["schema"]==BOUNDARY_PACKET,"SUCCESSOR_V2_REQUIRED")
    final=compile_graph(source,packet)
    need(final["packet_sha256"]!=parent["packet_sha256"],"SUCCESSOR_UNCHANGED")
    audit=_lineage(source,parent,final,lineage)
    carried={(x["new_id"],x["edge_sha256"]) for row in lineage for x in row["carries"]}
    expected={(n,h) for n,node in final["nodes"].items() for h in _edges(node)}-carried
    need(type(new_edges) is list,"SUCCESSOR_NEW_EDGE_LIST")
    seen=set()
    for row in new_edges:
        need(type(row) is dict and set(row)=={"node_id","edge_sha256","reason"} and _note(row["reason"]),"SUCCESSOR_NEW_EDGE_ROW")
        key=(row["node_id"],row["edge_sha256"])
        need(key in expected and key not in seen,"SUCCESSOR_NEW_EDGE_SCOPE");seen.add(key)
    need(seen==expected,"SUCCESSOR_NEW_EDGE_CENSUS")
    forward={n:row["new_ids"] for row in lineage for n in row["old_ids"]}
    def project(ids):
        need(all(n in forward for n in ids),"SUCCESSOR_HISTORICAL_OWNER")
        return sorted({x for n in ids for x in forward[n]})
    tasks=[]
    for x in plan["open_items"]:
        tasks.append({"old_sha256":x["old_sha256"],"historical_nodes":x["candidate_nodes"],
            "candidate_successors":project(x["candidate_nodes"]),"status":"OPEN"})
    for x in plan["scope_items"]:
        for k in x["obligation_ids"]:
            tasks.append({"old_sha256":k,"historical_nodes":x.get("candidate_nodes",[x["node_id"]]),
                "candidate_successors":project(x.get("candidate_nodes",[x["node_id"]])),"status":"SCOPE_DRAFT"})
    need(len({x["old_sha256"] for x in tasks})==len(tasks),"SUCCESSOR_DUPLICATE_OBLIGATION")
    return {"schema":"IRE_V3_GENERAL_SUCCESSOR_V1","parent_packet_sha256":parent["packet_sha256"],
        "parent_plan_sha256":json_digest(plan),"successor_packet_sha256":final["packet_sha256"],
        "obligation_count":plan["obligation_count"],"lineage":audit,"new_edge_count":len(new_edges),
        "new_edges_sha256":_rows_digest(new_edges),"pending_projection_sha256":_rows_digest(tasks),
        "open_obligations":len(plan["open_items"]),"scope_drafts":sum(len(x["obligation_ids"]) for x in plan["scope_items"]),
        "before_character_dispositions":parent["character_dispositions"],"after_character_dispositions":final["character_dispositions"],
        "unbound_numeric_spans":len(final["unbound_numeric_spans"]),"boundary_warnings":len(final["numeric_boundary_warnings"]),
        "original_score_changed":False,"semantic_conservation_verified":False,"ready_for_e3":False,"publication_authorized":False}

def _project_plan(plan, lineage, packet_sha):
    """Internal projection only; preserve every historical pending obligation."""
    forward={n:row["new_ids"] for row in lineage for n in row["old_ids"]}
    def project(ids):
        need(all(n in forward for n in ids),"SUCCESSOR_HISTORICAL_OWNER")
        return sorted({x for n in ids for x in forward[n]})
    # Scope drafts may acquire several candidate owners. Preserve their status
    # and membership as groups instead of asserting one successor owns them.
    q=deepcopy(plan);q["draft_packet_sha256"]=packet_sha
    for x in q["open_items"]:x["candidate_nodes"]=project(x["candidate_nodes"])
    for x in q["scope_items"]:
        x["candidate_nodes"]=project(x.get("candidate_nodes",[x["node_id"]]))
    return q


def successor_amendment(source,parent,projected_plan,prior_receipt,packet,lineage,new_edges):
    need(prior_receipt["successor_packet_sha256"]==parent["packet_sha256"],"AMENDMENT_PARENT")
    result=successor_revision(source,parent,projected_plan,packet,lineage,new_edges)
    return {**result,"schema":"IRE_V3_GENERAL_SUCCESSOR_AMENDMENT_V1",
            "prior_receipt_sha256":json_digest(prior_receipt)}


class GraphJournal:
    """Private SQLite journal, bounded records, transactionally appended.

    Every operation checks the complete byte/hash chain. Semantic replay of
    an already verified prefix may be reused within this instance only.
    Reopen always performs full semantic replay with the externally retained
    head. SQLite triggers prevent
    ordinary row updates/deletes, not privileged filesystem replacement.
    """
    def __init__(self,path,raw,manifest,*,source_sha,manifest_sha,create=False,expected_head=None):
        self.source=verify_source(raw,manifest,expected_source_sha256=source_sha,
                                  expected_manifest_sha256=manifest_sha)
        self.path=Path(path)
        self._verified=None
        if create:
            need(expected_head is None,"CREATE_PIN")
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
            with closing(sqlite3.connect(self.path)) as db, db:
                db.executescript("""CREATE TABLE events(seq INTEGER PRIMARY KEY,kind TEXT NOT NULL,
                    previous TEXT NOT NULL,payload BLOB NOT NULL,payload_sha TEXT NOT NULL,head TEXT NOT NULL UNIQUE);
                    CREATE TRIGGER immutable_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'immutable'); END;
                    CREATE TRIGGER immutable_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'immutable'); END;""")
            self.head=GENESIS
        else:
            need(self.path.is_file() and not self.path.is_symlink(),"MISSING_JOURNAL")
            require_hash(expected_head,"EXTERNAL_HEAD")
            self.head=expected_head
            self.snapshot()
    def _replay(self,db):
        p={};previous=GENESIS;previous_kind=None
        rows=db.execute("SELECT seq,kind,previous,payload,payload_sha,head FROM events ORDER BY seq").fetchall()
        cached=self._verified
        use_cache=cached is not None and cached[0]<=len(rows) and self.source is cached[3]
        for i,(seq,kind,prev,raw,ph,head) in enumerate(rows,1):
            need(seq==i and _allowed(previous_kind,kind) and prev==previous and sha256(raw)==ph,"CHAIN")
            need(head==json_digest({"seq":i,"kind":kind,"previous":prev,"payload_sha256":ph}),"HEAD")
            if use_cache and i==cached[0]:need(head==cached[1],"VERIFIED_PREFIX_DRIFT")
            previous=head;previous_kind=kind
        start=cached[0] if use_cache else 0
        if use_cache:p=deepcopy(cached[2])
        for seq,kind,prev,raw,ph,head in rows[start:]:
            value=json.loads(raw)
            need(_payload(value)==raw,"CANONICAL")
            self._apply(p,kind,value)
        return p,previous
    def _apply(self,p,kind,v):
        source=self.source
        if "audit_sha256" in p.get("plan",{}):
            need(kind in ("FIRST","SOURCE_AUDIT_LEDGER","SOURCE_AUDIT_SCORE","SOURCE_AUDIT_CANDIDATE"),"SOURCE_AUDIT_DIAGNOSTIC_ONLY")
        elif "protocol_sha256" in p.get("plan",{}):
            need(kind in ("FIRST","SECOND","SCORE"),"AUTHORING_DIAGNOSTIC_ONLY")
        elif kind in ("SOURCE_AUDIT_LEDGER","SOURCE_AUDIT_SCORE","SOURCE_AUDIT_CANDIDATE"):
            need(False,"SOURCE_AUDIT_PLAN_REQUIRED")
        if kind=="REGISTER":
            need(type(v) is dict and v==plan_for(source,campaign_id=v["campaign_id"],
                engine_commit=v["engine_commit_sha"],registered_at=v["registered_at"],purpose=v["purpose"],protocol_sha256=v.get("protocol_sha256"),audit_sha256=v.get("audit_sha256"),screening_sha256=v.get("screening_sha256")),"PLAN")
            p["plan"]=v
        elif kind in ("FIRST","SECOND"):
            protocol="protocol_sha256" in p["plan"]
            fields={"user_ref","observed_at","authored","receipt"} if protocol else {"user_ref","observed_at","packet"}
            need(type(v) is dict and set(v)==fields and _note(v["user_ref"]),"TURN")
            prior=p["plan"]["registered_at"] if kind=="FIRST" else p["first_meta"]["observed_at"]
            need(timestamp(v["observed_at"])>timestamp(prior),"TURN_ORDER")
            if protocol:
                from .semantic_authoring_protocol import compile_authoring
                packet,receipt=compile_authoring(source,v["authored"])
                need(receipt==v["receipt"],"AUTHORING_RECEIPT_DRIFT")
                p[kind.lower()+"_authoring"]=v["authored"]
                p[kind.lower()+"_authoring_receipt"]=receipt
            else:packet=v["packet"]
            g=compile_graph(source,packet)
            if kind=="SECOND":
                need(v["user_ref"]!=p["first_meta"]["user_ref"],"SAME_USER_REF")
                need(g["packet_sha256"]!=p["first"]["packet_sha256"],"COPIED_PACKET")
            k=kind.lower();p[k]=g;p[k+"_packet"]=packet
            p[k+"_meta"]={x:v[x] for x in ("user_ref","observed_at")}
        elif kind=="SOURCE_AUDIT_LEDGER":
            from .source_first_audit import freeze_source_ledger
            need(type(v) is dict and set(v)=={"user_ref","observed_at","ledger","receipt"} and _note(v["user_ref"]),"SOURCE_AUDIT_LEDGER_SHAPE")
            need(v["user_ref"]!=p["first_meta"]["user_ref"] and timestamp(v["observed_at"])>timestamp(p["first_meta"]["observed_at"]),"SOURCE_AUDIT_TURN_ORDER")
            r=freeze_source_ledger(source,v["ledger"])
            need(r==v["receipt"],"SOURCE_AUDIT_LEDGER_DRIFT")
            p["source_audit_ledger"]=v["ledger"];p["source_audit_ledger_receipt"]=r
            p["source_audit_meta"]={x:v[x] for x in ("user_ref","observed_at")}
        elif kind=="SOURCE_AUDIT_SCORE":
            from .source_first_audit import audit_bidirectional
            prospective=p["plan"]["purpose"]==PROSPECTIVE_PURPOSE
            fields={"user_ref","observed_at","assessment","result"}
            if prospective:fields|={"repeat_reviews","diagnostic"}
            need(type(v) is dict and set(v)==fields,"SOURCE_AUDIT_SCORE_SHAPE")
            need(v["user_ref"]==p["source_audit_meta"]["user_ref"] and timestamp(v["observed_at"])>=timestamp(p["source_audit_meta"]["observed_at"]),"SOURCE_AUDIT_SAME_SECOND_TURN")
            r=audit_bidirectional(source,p["first"],p["first_authoring"],p["first_authoring_receipt"],p["source_audit_ledger"],p["source_audit_ledger_receipt"],v["assessment"])
            need(r==v["result"],"SOURCE_AUDIT_SCORE_DRIFT");p["source_audit_score"]=r
            if prospective:
                d=prospective_diagnostic(source,p["plan"],p["source_audit_ledger"],r,v["repeat_reviews"])
                need(d==v["diagnostic"],"PROSPECTIVE_DIAGNOSTIC_DRIFT")
                p["prospective_diagnostic"]=d
            p["source_audit_score_meta"]={x:v[x] for x in ("user_ref","observed_at")}
        elif kind=="SOURCE_AUDIT_CANDIDATE":
            from .source_audit_completion import correction_candidate
            need(type(v) is dict and set(v)=={"user_ref","observed_at","candidate","result"},"SOURCE_AUDIT_CANDIDATE_SHAPE")
            m=p["source_audit_score_meta"]
            need(v["user_ref"]==m["user_ref"] and timestamp(v["observed_at"])>=timestamp(m["observed_at"]),"SOURCE_AUDIT_CANDIDATE_SAME_SECOND_TURN")
            r=correction_candidate(source,p["first"],p["first_authoring"],p["first_authoring_receipt"],p["source_audit_ledger"],p["source_audit_ledger_receipt"],p["source_audit_score"],v["candidate"])
            need(r==v["result"],"SOURCE_AUDIT_CANDIDATE_DRIFT");p["source_audit_candidate"]=r
        elif kind=="SCORE":
            need(type(v) is dict and set(v)=={"alignment","result"},"SCORE_SHAPE")
            r=score_graphs(source,p["first_packet"],p["second_packet"],v["alignment"])
            need(r==v["result"],"SCORE_DRIFT");p["score"]=r
            if "protocol_sha256" in p["plan"]:
                from .semantic_authoring_protocol import comparison_diagnostic
                d=comparison_diagnostic(source,p["first_authoring"],p["second_authoring"],v["alignment"],p["first_authoring_receipt"],p["second_authoring_receipt"])
                d["protocol_thresholds_met"]=bool(r["thresholds_met_on_supplied_internal_graphs"] and not d["open_numeric_occurrences"] and not d["uncertain_atoms"])
                p["authoring_comparison"]=d
        elif kind=="DISPUTES":
            p["disputes"]=adjudicate_disputes(source,p["first"],p["second"],v)
        elif kind=="REVISION":
            need(type(v) is dict and set(v)=={"packet","first_lineage","second_lineage","receipt"},"REVISION_SHAPE")
            r=revision(source,p["first"],p["second"],v["packet"],v["first_lineage"],v["second_lineage"])
            need(r==v["receipt"],"REVISION_DRIFT");p["revision"]=r
        elif kind in ("RECONCILIATION",LEGACY_KIND):
            from .semantic_reconciliation import verify_reconciliation_plan
            fields={"packet","old","candidates","events","rows","scopes","pins","plan","plan_sha256"}
            need(type(v) is dict and set(v)==fields,"RECONCILIATION_SHAPE")
            need(type(v["pins"]) is dict and set(v["pins"])=={
                "expected_head","expected_gap_receipt_sha256","expected_old_digest",
                "expected_candidate_digest","expected_packet_sha"},"RECONCILIATION_PINS")
            if kind==LEGACY_KIND:
                need(p["plan"]["purpose"]=="DEVELOPMENT","LEGACY_DEVELOPMENT_ONLY")
            else:
                need(v["pins"]["expected_packet_sha"]==p["revision"]["final_packet_sha256"],"RECONCILIATION_REVISION_DRIFT")
            h=verify_reconciliation_plan(v["plan"],source,v["packet"],v["old"],v["candidates"],
                v["events"],v["rows"],v["scopes"],expected_plan_sha256=v["plan_sha256"],**v["pins"])
            q=v["plan"]
            from .qualifier_gap_review import draft_qualifier_gaps
            draft,_=draft_qualifier_gaps(source,v["packet"],v["old"],v["candidates"],v["events"],v["rows"],v["scopes"],
                **{k:x for k,x in v["pins"].items() if k!="expected_gap_receipt_sha256"})
            p["reconciliation_parent"]=compile_graph(source,draft);p["reconciliation_plan"]=q
            p["historical_obligations"]=v["old"]
            p["reconciliation"]={"plan_sha256":h,"obligations":q["obligation_count"],
                "open_obligations":len(q["open_items"]),"scope_drafts":sum(len(x["obligation_ids"]) for x in q["scope_items"]),
                "scope_bundles":len(q["scope_items"]),"evidence_tasks":len(q["evidence_tasks"]),
                "open_characters":sum(x["span"][2]-x["span"][1] for x in q["residual_open"]),
                "unbound_numeric_spans":len(q["unbound_numeric"]),"legacy_development":kind==LEGACY_KIND,
                "semantic_conservation_verified":False,"ready_for_e3":False,"publication_authorized":False}
        elif kind=="SUCCESSOR":
            need(type(v) is dict and set(v)=={"packet","lineage","new_edges","receipt"},"SUCCESSOR_SHAPE")
            r=successor_revision(source,p["reconciliation_parent"],p["reconciliation_plan"],v["packet"],v["lineage"],v["new_edges"])
            need(r==v["receipt"],"SUCCESSOR_DRIFT");p["successor"]=r
            p["successor_parent"]=compile_graph(source,v["packet"])
            p["successor_plan"]=_project_plan(p["reconciliation_plan"],v["lineage"],r["successor_packet_sha256"])
        elif kind=="SUCCESSOR_AMENDMENT":
            fields={"packet","lineage","new_edges","receipt"}
            need("successor" in p,"AMENDMENT_BEFORE_SUCCESSOR")
            if "pending_review" in p:
                fields.add("invalidated_review_sha256")
                need(v.get("invalidated_review_sha256")==json_digest(p["pending_review"]),"AMENDMENT_REVIEW_INVALIDATION")
                p.setdefault("invalidated_reviews",[]).append(v["invalidated_review_sha256"])
                del p["pending_review"];del p["pending_review_rows"]
            need(type(v) is dict and set(v)==fields,"AMENDMENT_SHAPE")
            r=successor_amendment(source,p["successor_parent"],p["successor_plan"],p["successor"],v["packet"],v["lineage"],v["new_edges"])
            need(r==v["receipt"],"AMENDMENT_DRIFT");p["successor"]=r
            p["successor_parent"]=compile_graph(source,v["packet"])
            p["successor_plan"]=_project_plan(p["successor_plan"],v["lineage"],r["successor_packet_sha256"])
        elif kind=="PENDING_REVIEW":
            from .pending_semantic_review import pending_review
            need("successor" in p and type(v) is dict and set(v)=={"rows","receipt"},"PENDING_REVIEW_SHAPE")
            graph=p.get("successor_parent",p["reconciliation_parent"])
            plan=p.get("successor_plan",p["reconciliation_plan"])
            prior=p.get("pending_review_rows",[])
            r=pending_review(source,graph,plan,p["historical_obligations"],v["rows"],prior)
            need(r==v["receipt"],"PENDING_REVIEW_DRIFT")
            p["pending_review"]=r;p["pending_review_rows"]=prior+v["rows"]
    def append(self,kind,value):
        raw=_payload(value)
        with closing(sqlite3.connect(self.path,timeout=10,isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                p,head=self._replay(db);need(head==self.head,"EXTERNAL_HEAD_DRIFT")
                n=db.execute("SELECT count(*) FROM events").fetchone()[0]
                # Retry exact most recent event is idempotent; altered retry fails.
                last=db.execute("SELECT kind FROM events ORDER BY seq DESC LIMIT 1").fetchone()
                previous_kind=last[0] if last else None
                if n and kind==previous_kind:
                    prev=db.execute("SELECT payload FROM events WHERE seq=?",(n,)).fetchone()[0]
                    if prev==raw:
                        db.commit();self._verified=(n,head,p,self.source);return self.head
                    need(kind in ("SUCCESSOR_AMENDMENT","PENDING_REVIEW"),"NONIDENTICAL_RETRY")
                need(_allowed(previous_kind,kind),"EVENT_ORDER")
                self._apply(p,kind,json.loads(raw))
                ph=sha256(raw);new=json_digest({"seq":n+1,"kind":kind,"previous":head,"payload_sha256":ph})
                db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",(n+1,kind,head,raw,ph,new))
                db.commit();self.head=new;self._verified=(n+1,new,p,self.source);return new
            except BaseException:
                db.rollback();raise
    def amendment_context(self):
        """Return detached, currently verified inputs for the next amendment."""
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN')
            p,head=self._replay(db)
            need(head==self.head,"EXTERNAL_HEAD_DRIFT")
            need("successor" in p,"AMENDMENT_BEFORE_SUCCESSOR")
        return deepcopy({"head_sha256":head,"parent":p["successor_parent"],
            "projected_plan":p["successor_plan"],"prior_receipt":p["successor"],
            **({"pending_review_sha256":json_digest(p["pending_review"])} if "pending_review" in p else {})})
    def pending_review_context(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN')
            p,head=self._replay(db)
            need(head==self.head,"EXTERNAL_HEAD_DRIFT")
            need("reconciliation" in p,"PENDING_BEFORE_RECONCILIATION")
        return deepcopy({"head_sha256":head,"graph":p.get("successor_parent",p["reconciliation_parent"]),
            "plan":p.get("successor_plan",p["reconciliation_plan"]),"old":p["historical_obligations"],
            "prior_rows":p.get("pending_review_rows",[])})
    def source_audit_context(self):
        """Controlled first-body access after the source-ledger event only.

        Not a security boundary against direct file access or operator memory.
        """
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN');p,head=self._replay(db)
            need(head==self.head,"EXTERNAL_HEAD_DRIFT")
            need("source_audit_ledger_receipt" in p,"SOURCE_AUDIT_LEDGER_REQUIRED")
        return deepcopy({"head_sha256":head,"first":p["first"],"authored":p["first_authoring"],"first_receipt":p["first_authoring_receipt"],"ledger":p["source_audit_ledger"],"ledger_receipt":p["source_audit_ledger_receipt"]})
    def snapshot(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN')
            p,head=self._replay(db)
            need(head==self.head,"EXTERNAL_HEAD_DRIFT")
            count=db.execute("SELECT count(*) FROM events").fetchone()[0]
            last=db.execute("SELECT kind FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        self._verified=(count,head,p,self.source) if count else None
        # Do not expose the mutable cached projection to a caller.
        p=deepcopy(p)
        return {"head_sha256":head,"event_count":count,"phase":last[0] if last else "EMPTY",
            "first_packet_sha256":p.get("first",{}).get("packet_sha256"),
            "second_packet_sha256":p.get("second",{}).get("packet_sha256"),
            "score":p.get("score"),"disputes":p.get("disputes"),"revision":p.get("revision"),"reconciliation":p.get("reconciliation"),"successor":p.get("successor"),
            **({"authoring":{k:p[k] for k in ("first_authoring_receipt","second_authoring_receipt","authoring_comparison") if k in p}} if "first_authoring_receipt" in p else {}),
            **({"pending_review":p["pending_review"]} if "pending_review" in p else {}),
            **({"invalidated_reviews":p["invalidated_reviews"]} if "invalidated_reviews" in p else {}),
            **({"source_audit_ledger":p["source_audit_ledger_receipt"],"source_audit_score":p.get("source_audit_score")} if "source_audit_ledger_receipt" in p else {}),
            **({"source_audit_candidate":p["source_audit_candidate"]} if "source_audit_candidate" in p else {}),
            **({"prospective_diagnostic":p["prospective_diagnostic"]} if "prospective_diagnostic" in p else {}),
            "host_turn_authentication_verified":False,"independent_gold_verified":False,
            "operational_release_authorized":False,"publication_authorized":False}
