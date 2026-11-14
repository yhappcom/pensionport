"""V106 monotonic task-stage timing and honest UNMEASURED semantic stages.

This module measures processes that it wraps; it cannot instrument ChatGPT's
hidden model inference, manual review or external reviewer latency.
"""
from __future__ import annotations
import time,statistics,json,hashlib

STAGES=('SOURCE_IO_PARSE','PARENT_REGISTRY','BASELINE_RISK_SCREEN','MULTICUE_CANDIDATE_GRAPH','HYBRID_ROUTE','OFFICIAL_REFERENCE_RETRIEVAL','MODEL_CONTEXT_SEMANTIC_REVIEW','REGULATORY_SCOPE_CHECK','OPEN_CASE_RESOLUTION','INDEPENDENT_ADJUDICATION')
OPERATIONAL={'SOURCE_IO_PARSE','PARENT_REGISTRY','BASELINE_RISK_SCREEN','MULTICUE_CANDIDATE_GRAPH','HYBRID_ROUTE'}

def require(q,c):
 if not q:raise ValueError('V106_'+c)
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

def stage_measured_callable(stage, operation, *, repetitions=10):
 require(stage in OPERATIONAL and callable(operation),'STAGE_NOT_INSTRUMENTED')
 require(type(repetitions) is int and 3<=repetitions<=100,'REPETITIONS')
 observed=[];output=None
 for _ in range(repetitions):
  wall_start=time.perf_counter_ns();cpu_start=time.process_time_ns()
  a=operation()
  cpu_end=time.process_time_ns();wall_end=time.perf_counter_ns()
  require(wall_end>=wall_start and cpu_end>=cpu_start,'CLOCK_MONOTONIC')
  if output is not None:require(a==output,'NONDETERMINISTIC_RESULTS')
  output=a;observed.append({'wall_seconds':(wall_end-wall_start)/1e9,'cpu_seconds':(cpu_end-cpu_start)/1e9})
 def summary(k):
  z=sorted(x[k] for x in observed)
  return {'min_seconds':round(z[0],7),'median_seconds':round(statistics.median(z),7),'p95_seconds':round(z[int(.95*(len(z)-1))],7)}
 return {'stage':stage,'wall':summary('wall_seconds'),'cpu':summary('cpu_seconds'),
         'repetitions':repetitions,'result_digest_sha256':digest(output),
         'scope':'LOCAL_SYNC_FUNCTION_ONLY','chat_model_time_measured':False,'human_reviewer_time_measured':False}

def external_stage_bookend(stage,*,start_utc=None,end_utc=None,observer=None,includes_tool_wait=False):
 """Accept true, separately observed wall endpoints. If missing, NO estimate.
    This records a session envelope; it is not isolated model token latency.
 """
 require(stage in STAGES and stage not in OPERATIONAL,'EXTERNAL_STAGE_NAME')
 if start_utc is None or end_utc is None:
  return {'stage':stage,'status':'UNMEASURED','elapsed_wall_seconds':None,
          'model_inference_latency_seconds':None,'independent_reviewer_seconds':None}
 from datetime import datetime,timezone
 def parse(x):
  require(type(x) is str and ('+' in x or x.endswith('Z')),'OFFSET_REQUIRED')
  d=datetime.fromisoformat(x.replace('Z','+00:00'));require(d.tzinfo is not None,'TIMEZONE_REQUIRED')
  return d.astimezone(timezone.utc)
 a,b=parse(start_utc),parse(end_utc)
 dur=(b-a).total_seconds();require(0<=dur<=86400,'BAD_DURATION')
 require(observer in {'SHELL_BOUNDARY_OBSERVER','EXTERNAL_RATER_TIMESHEET','TOOL_LATENCY_WRAPPER'},'PROVENANCE_REQUIRED')
 return {'stage':stage,'status':'OBSERVED_SESSION_ENVELOPE',
   'elapsed_wall_seconds':dur,'observer':observer,'includes_tool_wait':bool(includes_tool_wait),
   'model_inference_latency_seconds':None,'independent_reviewer_seconds':None,
   'not_isolated_model_or_human_runtime':True}

def full_workflow_feasibility(stage_receipts,*,source_cues,video_count):
 require(type(stage_receipts)==list and type(source_cues) is int and source_cues>0 and type(video_count) is int and video_count>0,'INPUT')
 by={r['stage']:r for r in stage_receipts};require(len(by)==len(stage_receipts),'DUP_STAGE')
 require(set(by)<=set(STAGES),'UNKNOWN_STAGE')
 measured={k:v for k,v in by.items() if k in OPERATIONAL and v.get('repetitions')}
 missing=[k for k in ('MODEL_CONTEXT_SEMANTIC_REVIEW','OFFICIAL_REFERENCE_RETRIEVAL','REGULATORY_SCOPE_CHECK','OPEN_CASE_RESOLUTION','INDEPENDENT_ADJUDICATION') if by.get(k,{}).get('status')!='OBSERVED_SESSION_ENVELOPE']
 return {'schema':'V106_STAGE_OBSERVATION_NOT_COMPLETED_791_FORECAST_V1',
   'source_cues':source_cues,'source_videos':video_count,
   'structural_stages_measured':sorted(measured),'operational_stage_count':len(measured),
   'unmeasured_workflow_stages':missing,'full_end_to_end_duration_seconds':None,
   'verified_791_video_completion_forecast':None,'certified_financial_accuracy':None,
   'independent_gold':False,'p0_go':False}