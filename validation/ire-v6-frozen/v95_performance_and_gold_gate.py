"""V95 source-processing throughput/independent-gold quality measurement gate.
Do not treat synthetic tests or model self-ratings as independent precision/recall.
"""
from collections import Counter
from hashlib import sha256
import json,statistics,time

def require(ok,why):
    if not ok:raise ValueError('V95_'+why)
def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def independent_quality(gold,predictions,*,source_sha256=None,gold_sha256=None,prediction_sha256=None,independent_reviewer_attested=False):
    if gold is None or predictions is None or not independent_reviewer_attested:
        return {'status':'NO_SCORE','reason':'INDEPENDENT_PRECOMMITTED_GOLD_OR_REVIEWER_NOT_AVAILABLE',
                'precision':None,'recall':None,'high_risk_recall':None,'p0_go':False}
    require(type(gold) is list and type(predictions) is list,'TYPE')
    require(type(source_sha256) is str and len(source_sha256)==64,'SOURCE_PIN')
    require(digest(gold)==gold_sha256 and digest(predictions)==prediction_sha256,'SEALED_INPUT_MISMATCH')
    require(all(x.get('label') in {'FACT','NO_FACT'} and x.get('high_risk') in {True,False} for x in gold),'INVALID_GOLD')
    require(all(x.get('predicted') in {'FACT','NO_FACT'} for x in predictions),'INVALID_PREDICTION')
    gids=[x.get('id') for x in gold];pids=[x.get('id') for x in predictions]
    require(len(set(gids))==len(gids) and set(gids)==set(pids) and len(pids)==len(set(pids)),'MISSING_OR_DUPLICATE_PREDICTIONS')
    p={x['id']:x['predicted'] for x in predictions}; c=Counter()
    for g in gold:
        gt=g['label'];pred=p[g['id']]; c['total']+=1
        c['gold_positive']+=(gt=='FACT')
        if gt=='FACT' and pred=='FACT':c['tp']+=1
        if gt=='NO_FACT' and pred=='FACT':c['fp']+=1
        if gt=='FACT' and pred=='NO_FACT':c['fn']+=1
        if g['high_risk'] and gt=='FACT':
            c['high_gold']+=1;c['high_tp']+=(pred=='FACT')
    precision=c['tp']/(c['tp']+c['fp']) if c['tp']+c['fp'] else None
    recall=c['tp']/(c['tp']+c['fn']) if c['tp']+c['fn'] else None
    high=c['high_tp']/c['high_gold'] if c['high_gold'] else None
    # Real independent precision >= 95%, recall >= 90%, high-risk recall >=95%
    passed=(c['gold_positive']>=50 and c['high_gold']>=30 and precision is not None and recall is not None and high is not None and precision>=.95 and recall>=.90 and high>=.95)
    return {'status':'INDEPENDENT_REVIEW_ARITHMETIC_READY' if passed else 'THRESHOLDS_NOT_MET',
            'tp':c['tp'],'fp':c['fp'],'fn':c['fn'],'precision':precision,'recall':recall,'high_risk_recall':high,
            'scoring_thresholds_met':passed,
            # Reviewer credentials/timing/adjudication/semantic truth require external validation.
            'p0_go':False,'gold_authorship_validated_by_software':False}

def measure_source_processing(work,*,rounds=5,min_expected=1):
    """Only reports local CPU structural processing, *never* model inference throughput."""
    require(callable(work) and type(rounds) is int and 2<=rounds<=20,'INPUT')
    durations=[]; counts=[]
    for _ in range(rounds):
        t=time.perf_counter();n=work();elapsed=time.perf_counter()-t
        require(type(n) is int and n>=min_expected,'WORK_INCOMPLETE')
        durations.append(elapsed);counts.append(n)
    require(len(set(counts))==1,'NON_DETERMINISTIC_COUNTS')
    mid=statistics.median(durations)
    return {'schema':'V95_LOCAL_STRUCTURAL_THROUGHPUT_ONLY_V1','rounds':rounds,'source_cues_per_run':counts[0],
       'median_seconds':round(mid,6),'median_cues_per_second':round(counts[0]/mid,1) if mid>0 else None,
       'runtime_includes_model_semantic_review':False,'runtime_includes_external_rule_research':False,
       '791_video_end_to_end_runtime_estimated':False,'independent_semantic_quality_score':None,'p0_go':False}