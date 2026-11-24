"""Current P205 transition guard, independent of historical HOLD receipts.

A public CI cannot replay private original bytes. It accepts a positive
transition only after a separately reviewed commit pins the actual private
L4 replay receipt and independently checked exact-engine CI evidence. This
trust enrollment is not derived from the submitted receipt or a runtime flag.
An empty enrollment is a real HOLD, not a simulated certificate.
"""
from __future__ import annotations
import ast,hashlib,json,re
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG,STATE,validate as validate_checklist
from scripts.ire_current_status_gate import LEDGER,validate as validate_status

ROOT=Path(__file__).resolve().parents[1]
CLOSEOUT_PATH="docs/IRE_P0_2_05_APPROVED_ASSESSMENT_CLOSEOUT.json"
# A reviewed future commit must pin the exact public receipt bytes only after
# private production replay AND checking the actual GitHub CI run. Never
# populate this in tests or from submitted files. No enrollment today.
APPROVED_CLOSEOUT_SHA256=None


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def _load(root,path):
    return json.loads((root/path).read_text(encoding="utf8"))


def _campaign_pins(root):
    tree=ast.parse((root/"ire/v6/assessment_plan.py").read_text(encoding="utf8"))
    nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=="PINNED_CAMPAIGNS" for t in n.targets)]
    if len(nodes)!=1:
        raise ValueError("CAMPAIGN_PIN_NOT_LITERAL")
    result=ast.literal_eval(nodes[0])
    if type(result) is not dict:
        raise ValueError("CAMPAIGN_PIN_MAP_INVALID")
    return result


def validate_closeout(receipt,pins):
    """Structural check of an already independently reviewed, pinned receipt."""
    errors=[]
    def need(x,name):
        if not x:errors.append("P205_LIVE_"+name)
    if type(receipt) is not dict or set(receipt)!={"schema","private_replay","ci"}:
        return ["P205_LIVE_CLOSEOUT_SCHEMA"]
    r=receipt["private_replay"];ci=receipt["ci"]
    keys={"schema","campaign_id","plan_sha256","registry_sha256","engine_commit_sha",
          "source_sha256","prediction_sha256","gold_sha256","alignment_sha256",
          "production_evidence_sha256","source_cues","prediction_atoms","gold_atoms",
          "tp","fp","fn","high_risk_fn","evidence_level","independent_gold_verified",
          "research_publication_authorized"}
    if type(r) is not dict or set(r)!=keys:
        return ["P205_LIVE_PRIVATE_REPLAY_SCHEMA"]
    need(r["schema"]=="IRE_P205_PRIVATE_ASSESSMENT_CLOSEOUT_V1" and
         r["evidence_level"]=="L4" and r["independent_gold_verified"] is True and
         r["research_publication_authorized"] is False,"L4_ONLY")
    need(all(type(r[k]) is str and re.fullmatch(r"[0-9a-f]{64}",r[k]) for k in
         ("plan_sha256","registry_sha256","source_sha256","prediction_sha256",
          "gold_sha256","alignment_sha256","production_evidence_sha256")),"REPLAY_SHA")
    need(type(r["engine_commit_sha"]) is str and
         bool(re.fullmatch(r"[0-9a-f]{40}",r["engine_commit_sha"])),"ENGINE_SHA")
    cid=r["campaign_id"]
    need(type(cid) is str and pins.get(cid)=={"plan_sha256":r["plan_sha256"],
              "registry_sha256":r["registry_sha256"]},"PREREVIEW_CAMPAIGN_NOT_ENROLLED")
    numbers=("source_cues","prediction_atoms","gold_atoms","tp","fp","fn","high_risk_fn")
    if not all(type(r[k]) is int and r[k]>=0 for k in numbers):
        errors.append("P205_LIVE_COUNTS_INVALID")
    else:
        tp,fp,fn=r["tp"],r["fp"],r["fn"]
        need(r["source_cues"]>0 and r["prediction_atoms"]==tp+fp>0 and
             r["gold_atoms"]==tp+fn>0 and tp*10000>=9500*(tp+fp) and
             tp*10000>=9800*(tp+fn) and r["high_risk_fn"]==0,"THRESHOLDS")
    need(type(ci) is dict and set(ci)=={"run_id","head_sha","successful_jobs","conclusion"}
         and type(ci.get("run_id")) is int and ci["run_id"]>0 and
         ci.get("head_sha")==r["engine_commit_sha"] and
         type(ci.get("successful_jobs")) is int and ci["successful_jobs"]==6 and
         ci.get("conclusion")=="success","SAME_ENGINE_CI")
    need(receipt["schema"]=="IRE_P205_REVIEWED_PUBLIC_CLOSEOUT_V1","SCHEMA")
    return errors


def verify_legacy_independent_transition(root=ROOT,*,state=None,ledger=None):
    """CI checks live status; old historical validators never grant release."""
    root=Path(root)
    s=_load(root,STATE) if state is None else state
    l=_load(root,LEDGER) if ledger is None else ledger
    rows=s.get("items",[])
    if len(rows)!=60 or rows[16].get("id")!="P0-2-05":
        return ["P205_LIVE_CHECKLIST_SHAPE"]
    if rows[16].get("status")!="PASS":
        from scripts.ire_p0_2_05_root_cause_gate import verify as hold
        from scripts.ire_p0_2_05_kind_triage_gate import verify as triage
        return hold(root,state=s,ledger=l)+triage(root,state=s,ledger=l)
    pin=APPROVED_CLOSEOUT_SHA256
    if type(pin) is not str or not re.fullmatch(r"[0-9a-f]{64}",pin):
        return ["P205_LIVE_NO_REVIEWED_CLOSEOUT_ENROLLMENT"]
    try:
        raw=(root/CLOSEOUT_PATH).read_bytes()
        if _sha(raw)!=pin:
            return ["P205_LIVE_CLOSEOUT_DIGEST_DRIFT"]
        receipt=json.loads(raw)
        errors=validate_closeout(receipt,_campaign_pins(root))
        if errors:return errors
        if not any(e.get("kind")=="assessment" and e.get("verdict")=="PASS"
                   and e.get("ref")==CLOSEOUT_PATH and e.get("sha")==_git_blob(raw)
                   for e in rows[16].get("evidence",[]) if type(e) is dict):
            return ["P205_LIVE_CHECKLIST_EVIDENCE_NOT_BOUND"]
        return (validate_checklist(_load(root,CATALOG),s,root=root)
                +validate_status(l,root=root))
    except (OSError,ValueError,KeyError,TypeError,SyntaxError):
        return ["P205_LIVE_CLOSEOUT_INVALID_OR_MISSING"]


def verify_current(root=ROOT,*,state=None,ledger=None):
    from scripts.ire_p205_operational_release import verify_current as operational
    return operational(root,state=state,ledger=ledger)
