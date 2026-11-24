"""Policy V1 operational closeout. Public CI checks pinned SHA-only records,
not private original bytes, truth or independent review. No external host pin
required. The two pins are separate project records, frozen at selection and
after actual private replay respectively; neither may be supplied by a caller.
"""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG,STATE,validate as validate_checklist
from scripts.ire_current_status_gate import LEDGER,validate as validate_status

ROOT=Path(__file__).resolve().parents[1]
POLICY_ID="IRE_P205_OPERATIONAL_V1_20261124"
POLICY_PATH="docs/IRE_P0_2_05_OPERATIONAL_EVALUATION_POLICY_20261124.json"
COHORT_PATH="docs/IRE_P0_2_05_OPERATIONAL_PREREGISTERED_COHORT.json"
CLOSEOUT_PATH="docs/IRE_P0_2_05_OPERATIONAL_CLOSEOUT.json"
PREREGISTERED_COHORT_SHA256="1792e30d8cae7e8a9455fe8fe2fa918b2d7c559de2c976906aa7ea156a6b534e"
REVIEWED_OPERATIONAL_CLOSEOUT_SHA256=None
DOMAINS={"ETF","PENSION","ASSET_ALLOCATION"}

def _sha(b):return hashlib.sha256(b).hexdigest()
def _blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def _hex(x,n=64):return type(x) is str and bool(re.fullmatch("[0-9a-f]{"+str(n)+"}",x))
def _load(root,path):return json.loads((root/path).read_text(encoding="utf8"))
def _time(x):
    try:
        t=datetime.fromisoformat(x.replace("Z","+00:00"))
        return t if t.tzinfo is not None else None
    except (AttributeError,ValueError,TypeError):return None

def validate_closeout(receipt,cohort,cohort_sha):
    errors=[]
    def need(flag,name):
        if not flag:errors.append("P205_OPERATIONAL_"+name)
    if type(cohort) is not dict or set(cohort)!={"schema","policy_id","engine_commit_sha","registered_at","sources"}:
        return ["P205_OPERATIONAL_COHORT_SCHEMA"]
    if (type(receipt) is not dict or set(receipt)!={"schema","policy_id","cohort_sha256","trials","ci"}):
        return ["P205_OPERATIONAL_CLOSEOUT_SCHEMA"]
    engine=cohort["engine_commit_sha"]
    need(cohort["schema"]=="IRE_P205_OPERATIONAL_COHORT_V1" and
         cohort["policy_id"]==receipt["policy_id"]==POLICY_ID and
         receipt["schema"]=="IRE_P205_OPERATIONAL_CLOSEOUT_V1" and
         receipt["cohort_sha256"]==cohort_sha and _hex(engine,40),"POLICY_COHORT_BINDING")
    sources=cohort["sources"];trials=receipt["trials"]
    if type(sources) is not list or len(sources)!=3 or type(trials) is not list or len(trials)!=3:
        return errors+["P205_OPERATIONAL_THREE_DOMAIN_TRIALS_REQUIRED"]
    registered=_time(cohort["registered_at"])
    if registered is None:return errors+["P205_OPERATIONAL_COHORT_REGISTRATION_TIME"]
    seen=set();vids=set();shas=set();campaigns=set();by_domain={}
    for row in sources:
        if type(row) is not dict or set(row)!={"domain","video_id","source_sha256","selection_sha256","exposure_screen_sha256"}:
            return errors+["P205_OPERATIONAL_SOURCE_ROW"]
        domain=row["domain"];vid=row["video_id"];sha=row["source_sha256"]
        if (type(domain) is not str or domain not in DOMAINS or domain in seen or
            type(vid) is not str or not re.fullmatch("[A-Za-z0-9_-]{11}",vid) or vid in vids or
            vid=="LVE7XN_esTc" or not _hex(sha) or sha in shas or
            sha=="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b" or
            not _hex(row["selection_sha256"]) or not _hex(row["exposure_screen_sha256"])):
            return errors+["P205_OPERATIONAL_SOURCE_REUSE_OR_DOMAIN"]
        seen.add(domain);vids.add(vid);shas.add(sha);by_domain[domain]=row
    seen=set()
    for r in trials:
        if type(r) is not dict:
            return errors+["P205_OPERATIONAL_TRIAL_SCHEMA"]
        domain=r.get("domain");src=by_domain.get(domain) if type(domain) is str else None
        if src is None or domain in seen:return errors+["P205_OPERATIONAL_TRIAL_DOMAIN"]
        seen.add(domain)
        cid=r.get("campaign_id")
        need(type(cid) is str and bool(cid) and cid not in campaigns,"CAMPAIGN_ID")
        if type(cid) is str:campaigns.add(cid)
        need(r.get("schema")=="IRE_P205_INTERNAL_OPERATIONAL_TRIAL_V1" and
             r.get("policy_id")==POLICY_ID and r.get("cohort_sha256")==cohort_sha and
             r.get("engine_commit_sha")==engine and
             all(r.get(k)==src[k] for k in ("video_id","source_sha256","selection_sha256")),
             "TRIAL_SOURCE_ENGINE_BINDING")
        need(all(_hex(r.get(k)) for k in ("plan_sha256","prediction_sha256","reference_sha256",
                                         "alignment_sha256","review_sha256","manifest_sha256","inventory_sha256")),"TRIAL_DIGESTS")
        frozen=_time(r.get("prediction_frozen_at"))
        need(frozen is not None and registered<frozen,"COHORT_BEFORE_PREDICTION")
        need(r.get("evidence_level")=="L2" and r.get("independent_gold_verified") is False and
             r.get("host_turn_authentication_verified") is False and
             all(k in r and r[k] is None for k in ("independent_precision","independent_recall","independent_high_risk_fn"))
             and r.get("research_publication_authorized") is False and
             r.get("personalized_advice_authorized") is False,"NO_INDEPENDENCE_OR_RELEASE_LAUNDERING")
        keys=("source_cues","reviewed_cues","prediction_atoms","reference_atoms","tp","fp","fn",
              "high_risk_reference_atoms","high_risk_fn","numeric_boundary_warnings","critical_pair_mismatches")
        if not all(type(r.get(k)) is int and r[k]>=0 for k in keys):
            errors.append("P205_OPERATIONAL_COUNTS");continue
        tp,fp,fn=r["tp"],r["fp"],r["fn"]
        need(r["source_cues"]==r["reviewed_cues"]>0 and r["prediction_atoms"]==tp+fp>0 and
             r["reference_atoms"]==tp+fn>0 and 0<r["high_risk_reference_atoms"]<=r["reference_atoms"]
             and tp*10000>=9500*(tp+fp) and tp*10000>=9800*(tp+fn)
             and r["high_risk_fn"]==r["numeric_boundary_warnings"]==r["critical_pair_mismatches"]==0
             and r.get("internal_thresholds_met") is True and r.get("status")=="INTERNAL_TRIAL_THRESHOLDS_MET",
             "PER_VIDEO_THRESHOLDS")
    ci=receipt["ci"]
    need(type(ci) is dict and set(ci)=={"run_id","head_sha","successful_jobs","conclusion"} and
         type(ci.get("run_id")) is int and ci["run_id"]>0 and ci.get("head_sha")==engine and
         ci.get("successful_jobs")==6 and ci.get("conclusion")=="success","ENGINE_CI")
    return errors

def verify_current(root=ROOT,*,state=None,ledger=None):
    root=Path(root)
    s=_load(root,STATE) if state is None else state
    l=_load(root,LEDGER) if ledger is None else ledger
    rows=s.get("items",[])
    if len(rows)!=60 or rows[16].get("id")!="P0-2-05":
        return ["P205_OPERATIONAL_CURSOR"]
    try:
        p=_load(root,POLICY_PATH)
        if (p.get("policy_id")!=POLICY_ID or p.get("independent_certification_required_for_operational_pass") is not False or
            p.get("thresholds")!={"precision_min_bp":9500,"recall_min_bp":9800,"high_risk_fn_max":0} or
            set(p.get("domains",[]))!=DOMAINS):
            return ["P205_OPERATIONAL_POLICY_DRIFT"]
        assessment=l.get("stages",{}).get("E2",{}).get("operational_assessment",{})
        if (assessment.get("policy_id")!=POLICY_ID or
            assessment.get("independent_certification_required") is not False or
            set(assessment.get("required_domains",[]))!=DOMAINS):
            return ["P205_OPERATIONAL_LEDGER_POLICY_DRIFT"]
        if rows[16].get("status")!="PASS":
            # Per-trial diagnostics are separate; no release result on HOLD.
            if (assessment.get("status") not in ("HOLD_NOT_MEASURED","HOLD_PARTIAL_OR_FAILED") or
                any(assessment.get(k) is not None for k in ("precision","recall","high_risk_fn"))):
                return ["P205_OPERATIONAL_LEDGER_FALSE_PASS"]
            return validate_checklist(_load(root,CATALOG),s,root=root)+validate_status(l,root=root)
        if not _hex(PREREGISTERED_COHORT_SHA256) or not _hex(REVIEWED_OPERATIONAL_CLOSEOUT_SHA256):
            return ["P205_OPERATIONAL_REAL_CLOSEOUT_NOT_ENROLLED"]
        cohort_raw=(root/COHORT_PATH).read_bytes();raw=(root/CLOSEOUT_PATH).read_bytes()
        if _sha(cohort_raw)!=PREREGISTERED_COHORT_SHA256 or _sha(raw)!=REVIEWED_OPERATIONAL_CLOSEOUT_SHA256:
            return ["P205_OPERATIONAL_PIN_DRIFT"]
        errors=validate_closeout(json.loads(raw),json.loads(cohort_raw),PREREGISTERED_COHORT_SHA256)
        if errors:return errors
        if (assessment.get("status")!="PASS_INTERNAL_ONLY" or
            assessment.get("closeout_sha256")!=REVIEWED_OPERATIONAL_CLOSEOUT_SHA256):
            return ["P205_OPERATIONAL_LEDGER_CLOSEOUT_NOT_BOUND"]
        if not any(type(e) is dict and e.get("kind")=="assessment" and e.get("verdict")=="PASS"
                   and e.get("ref")==CLOSEOUT_PATH and e.get("sha")==_blob(raw)
                   for e in rows[16].get("evidence",[])):
            return ["P205_OPERATIONAL_CHECKLIST_EVIDENCE_NOT_BOUND"]
        return validate_checklist(_load(root,CATALOG),s,root=root)+validate_status(l,root=root)
    except (OSError,ValueError,KeyError,TypeError):
        return ["P205_OPERATIONAL_INVALID_OR_MISSING"]
