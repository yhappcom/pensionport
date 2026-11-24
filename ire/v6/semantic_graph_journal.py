"""R3-04 private two-turn research journal and revision custody.

This verifies supplied semantic decisions, not their truth. The journal's
observed timestamps/user labels are operator records, not authenticated host
events. It can detect modification relative to an externally retained head;
it cannot prevent an owner from rewriting a database and its external pins.
No E3/E4/E5 approval or operational release is produced.
"""
from __future__ import annotations
import json, os, re, sqlite3
from contextlib import closing
from pathlib import Path
from .codec import canonical,sha256,json_digest,require_hash
from .errors import InvalidInput
from .assessment_plan import timestamp,THRESHOLDS
from .semantic_source_graph import (compile_graph,source_grid,RUBRIC_SHA256,
    compare_graphs,score_graphs,_rows_digest,_span,_note)
from .source import verify_source

GENESIS="0"*64
KINDS=("REGISTER","FIRST","SECOND","SCORE","DISPUTES","REVISION")
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

def plan_for(source,*,campaign_id,engine_commit,registered_at,purpose):
    need(type(campaign_id) is str and bool(re.fullmatch(r"[A-Za-z0-9_-]{3,80}",campaign_id)),"CAMPAIGN")
    need(type(engine_commit) is str and bool(re.fullmatch(r"[0-9a-f]{40}",engine_commit)),"ENGINE")
    timestamp(registered_at)
    need(purpose in ("DEVELOPMENT","HOLDOUT"),"PURPOSE")
    need(purpose!="HOLDOUT" or (source.video_id not in EXPOSED_IDS and
        source.source_sha256 not in EXPOSED_SHAS),"EXPOSED_SOURCE")
    return {"schema":"IRE_V3_GRAPH_RESEARCH_PLAN_V1","campaign_id":campaign_id,
      "engine_commit_sha":engine_commit,"registered_at":registered_at,"purpose":purpose,
      "source_sha256":source.source_sha256,"video_id":source.video_id,
      "manifest_sha256":source.manifest_sha256,"grid_sha256":json_digest(source_grid(source)),
      "rubric_sha256":RUBRIC_SHA256,"thresholds":dict(THRESHOLDS)}

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
        need(type(row) is dict and set(row)=={"old_ids","new_ids","operation","reason","losses","carries"},"LINEAGE_ROW")
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
        carried=set()
        for carry in row["carries"]:
            need(type(carry) is dict and set(carry)=={"old_id","edge_sha256","new_id","reason"}
                 and _note(carry["reason"]),"CARRY_ROW")
            k=(carry["old_id"],carry["edge_sha256"]);target=carry["new_id"]
            need(k in obligations and k not in carried and target in destinations and
                 k[1] in destinations[target],"FALSE_CARRY")
            carried.add(k)
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

class GraphJournal:
    """Private SQLite journal, bounded records, transactionally appended.

    Every append validates all previous events by replay on original bytes.
    Reopen requires the externally retained head. SQLite triggers prevent
    ordinary row updates/deletes, not privileged filesystem replacement.
    """
    def __init__(self,path,raw,manifest,*,source_sha,manifest_sha,create=False,expected_head=None):
        self.source=verify_source(raw,manifest,expected_source_sha256=source_sha,
                                  expected_manifest_sha256=manifest_sha)
        self.path=Path(path)
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
        p={};previous=GENESIS
        rows=db.execute("SELECT seq,kind,previous,payload,payload_sha,head FROM events ORDER BY seq").fetchall()
        for i,(seq,kind,prev,raw,ph,head) in enumerate(rows,1):
            need(i<=len(KINDS) and seq==i and kind==KINDS[i-1] and prev==previous and sha256(raw)==ph,"CHAIN")
            need(head==json_digest({"seq":i,"kind":kind,"previous":prev,"payload_sha256":ph}),"HEAD")
            value=json.loads(raw)
            need(_payload(value)==raw,"CANONICAL")
            self._apply(p,kind,value);previous=head
        return p,previous
    def _apply(self,p,kind,v):
        source=self.source
        if kind=="REGISTER":
            need(type(v) is dict and v==plan_for(source,campaign_id=v["campaign_id"],
                engine_commit=v["engine_commit_sha"],registered_at=v["registered_at"],purpose=v["purpose"]),"PLAN")
            p["plan"]=v
        elif kind in ("FIRST","SECOND"):
            need(type(v) is dict and set(v)=={"user_ref","observed_at","packet"} and _note(v["user_ref"]),"TURN")
            prior=p["plan"]["registered_at"] if kind=="FIRST" else p["first_meta"]["observed_at"]
            need(timestamp(v["observed_at"])>timestamp(prior),"TURN_ORDER")
            g=compile_graph(source,v["packet"])
            if kind=="SECOND":
                need(v["user_ref"]!=p["first_meta"]["user_ref"],"SAME_USER_REF")
                need(g["packet_sha256"]!=p["first"]["packet_sha256"],"COPIED_PACKET")
            k=kind.lower();p[k]=g;p[k+"_packet"]=v["packet"]
            p[k+"_meta"]={x:v[x] for x in ("user_ref","observed_at")}
        elif kind=="SCORE":
            need(type(v) is dict and set(v)=={"alignment","result"},"SCORE_SHAPE")
            r=score_graphs(source,p["first_packet"],p["second_packet"],v["alignment"])
            need(r==v["result"],"SCORE_DRIFT");p["score"]=r
        elif kind=="DISPUTES":
            p["disputes"]=adjudicate_disputes(source,p["first"],p["second"],v)
        elif kind=="REVISION":
            need(type(v) is dict and set(v)=={"packet","first_lineage","second_lineage","receipt"},"REVISION_SHAPE")
            r=revision(source,p["first"],p["second"],v["packet"],v["first_lineage"],v["second_lineage"])
            need(r==v["receipt"],"REVISION_DRIFT");p["revision"]=r
    def append(self,kind,value):
        raw=_payload(value)
        with closing(sqlite3.connect(self.path,timeout=10,isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                p,head=self._replay(db);need(head==self.head,"EXTERNAL_HEAD_DRIFT")
                n=db.execute("SELECT count(*) FROM events").fetchone()[0]
                # Retry exact most recent event is idempotent; altered retry fails.
                if n and kind==KINDS[n-1]:
                    prev=db.execute("SELECT payload FROM events WHERE seq=?",(n,)).fetchone()[0]
                    need(prev==raw,"NONIDENTICAL_RETRY")
                    db.commit();return self.head
                need(n<len(KINDS) and KINDS[n]==kind,"EVENT_ORDER")
                self._apply(p,kind,value)
                ph=sha256(raw);new=json_digest({"seq":n+1,"kind":kind,"previous":head,"payload_sha256":ph})
                db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",(n+1,kind,head,raw,ph,new))
                db.commit();self.head=new;return new
            except BaseException:
                db.rollback();raise
    def snapshot(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN')
            p,head=self._replay(db)
            need(head==self.head,"EXTERNAL_HEAD_DRIFT")
            count=db.execute("SELECT count(*) FROM events").fetchone()[0]
        return {"head_sha256":head,"event_count":count,"phase":KINDS[count-1] if count else "EMPTY",
            "first_packet_sha256":p.get("first",{}).get("packet_sha256"),
            "second_packet_sha256":p.get("second",{}).get("packet_sha256"),
            "score":p.get("score"),"disputes":p.get("disputes"),"revision":p.get("revision"),
            "host_turn_authentication_verified":False,"independent_gold_verified":False,
            "operational_release_authorized":False,"publication_authorized":False}
