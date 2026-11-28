"""Source-first passage retrieval diagnostic, no semantic truth certification."""
import json, time, sys, hashlib, sqlite3
from pathlib import Path
from contextlib import closing
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'c1_topic' if (ROOT.parent/'c1_topic'/'topic_index.py').exists() else ROOT.parent
sys.path.insert(0,str(BASE))
from topic_index import search, norm, sha, connect
DB=BASE/'index.db'
REF=ROOT/'reference.json'
assert sha(REF.read_bytes())=='ba48ae3babd039c210a3002408913f495cf419e5de66f4827d0ec323d407ee7d'
assert sha((ROOT/'sample_plan.json').read_bytes())=='834f5f519cc57d1b591ef9b834953746aed06b00b8498d2f93cc6761a2458cea'
assert sha((BASE/'topic_index.py').read_bytes())=='153cba03d77d82b6eff2a3d507f9a6b025385dcc750bddd155048b4debf7bedb'
before=sha(DB.read_bytes());assert before=='4c266ed78c7d0e6aa8b1686092621cafa46db74d11c25f5f809c86e5f6124e1f'
ref=json.loads(REF.read_text());plan=json.loads((ROOT/'sample_plan.json').read_text());samples={x['video_id']:x for x in plan['picks']};results=[];raw={}
with closing(connect(DB)) as c:
 for q in ref['queries']:
  t0=time.perf_counter();error=None
  try: res=search(DB,q['groups'],limit=30,per_source=3,context=8)
  except ValueError as exc: error=str(exc);res=dict(matched_sources=0,matched_windows=0,results=[],error=error)
  elapsed=1000*(time.perf_counter()-t0);raw[q['id']]=res
  targets=[]
  for target in q['targets']:
   s=samples[target['video']];lo,hi=target['start'],target['end'];assert s['start']<=lo<=hi<=s['end'];sid=s['sha']
   ranks=[i for i,r in enumerate(res['results'],1) if r['source_sha']==sid and r['context'][0]['cue']<=lo and r['context'][-1]['cue']>=hi]
   # A window can be eligible but excluded by rank, per-source limit or overlap suppression.
   eligible=[(r['first_cue'],r['last_cue']) for r in c.execute('SELECT first_cue,last_cue,body FROM windows WHERE sid=?',(sid,)) if max(1,r['first_cue']-8)<=lo and r['last_cue']+8>=hi and all(any(norm(t) in r['body'] for t in g) for g in q['groups'])]
   matched_ranks=[i for i,r in enumerate(res['results'],1) if r['source_sha']==sid]
   missing='INVALID_QUERY' if error else 'NONE' if ranks else 'RANK_OR_SUPPRESSION' if eligible else 'NO_ELIGIBLE_WINDOW_FOR_FULL_ANCHOR'
   targets.append(dict(**target,full_context=bool(ranks),ranks=ranks,same_source_ranks=matched_ranks,eligible_windows=eligible if not error else [],failure_class=missing))
  results.append(dict(id=q['id'],question=q['question'],matched_sources=res['matched_sources'],matched_windows=res['matched_windows'],returned=len(res['results']),error=error,elapsed_ms=round(elapsed,3),targets=targets))
all_t=[t for q in results for t in q['targets']];high=[t for t in all_t if t['risk']=='H'];n=sum(t['full_context'] for t in all_t);nh=sum(t['full_context'] for t in high);after=sha(DB.read_bytes());assert before==after
out=dict(status='PASS_SAMPLE' if n/len(all_t)>=ref['provisional_gate']['target_recovery_min'] and nh==len(high) else 'HOLD_SAMPLE',scope=ref['scope'],metric=ref['metric'],source_count=len(samples),sample_cues=sum(x['end']-x['start']+1 for x in samples.values()),questions=len(results),targets=len(all_t),recovered=n,high_risk_targets=len(high),high_risk_recovered=nh,eligible_targets=sum(bool(t['eligible_windows']) for t in all_t),recovery=n/len(all_t),reference_sha=sha(REF.read_bytes()),sample_plan_sha=sha((ROOT/'sample_plan.json').read_bytes()),code_sha=sha((BASE/'topic_index.py').read_bytes()),db_sha_before=before,db_sha_after=after,queries=results,formal_corpus_recall='UNMEASURED',independent_certification='UNVERIFIED',financial_validation='NOT_RUN')
(ROOT/'RESULT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(ROOT/'retrieval.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='queries'},ensure_ascii=False,indent=2))
for q in results: print(q['id'],q['matched_sources'],q['elapsed_ms'],[(t['start'],t['full_context'],t['ranks'],t['failure_class'],t['eligible_windows']) for t in q['targets']])
