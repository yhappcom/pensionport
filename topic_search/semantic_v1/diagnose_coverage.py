import sys,json,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;BASE=R.parent/'c1_topic' if (R.parent/'c1_topic'/'topic_index.py').exists() else R.parent;sys.path.insert(0,str(BASE))
from topic_index import sha
from coverage_search import CoverageSearch
ref=json.loads((R/'reference.json').read_text()); assert sha((R/'reference.json').read_bytes())=='ba48ae3babd039c210a3002408913f495cf419e5de66f4827d0ec323d407ee7d'
p=BASE/'index.db';before=sha(p.read_bytes());t=time.perf_counter();cs=CoverageSearch(p);build=time.perf_counter()-t
base=json.loads((R/'RESULT.json').read_text());results=[];raw={}
for q in ref['queries']:
 t=time.perf_counter();r=cs.inventory(q['groups']);ms=1000*(time.perf_counter()-t);raw[q['id']]=r; ts=[]
 for a in q['targets']:
  ranks=[i for i,x in enumerate(r['results'],1) if a['video'] in x['video_ids'] and x['first_cue']-8<=a['start'] and x['last_cue']+8>=a['end']]
  verified=False
  if ranks:
   ctx=cs.context(r['results'][ranks[0]-1]);verified=ctx[0]['cue']<=a['start'] and ctx[-1]['cue']>=a['end'];assert verified
  ts.append(dict(**a,inventory_recovered=verified,best_rank=ranks[0] if ranks else None,top30=bool(ranks and ranks[0]<=30)))
 results.append(dict(id=q['id'],elapsed_ms=round(ms,3),matched_windows=r['matched_windows'],matched_sources=r['matched_sources'],targets=ts))
all_t=[a for q in results for a in q['targets']];assert before==sha(p.read_bytes());out=dict(status='KNOWN_SAMPLE_DIAGNOSTIC_ONLY',scope='same sample after observed failures; no new independent evaluation or promotion',window_count=len(cs.windows),build_seconds=build,targets=len(all_t),inventory_recovered=sum(a['inventory_recovered'] for a in all_t),top30_recovered=sum(a['top30'] for a in all_t),high_risk_inventory=sum(a['inventory_recovered'] for a in all_t if a['risk']=='H'),high_risk_top30=sum(a['top30'] for a in all_t if a['risk']=='H'),total_candidates=sum(q['matched_windows'] for q in results),db_sha=before,queries=results)
(R/'COVERAGE_RESULT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(R/'coverage_inventory.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='queries'},ensure_ascii=False,indent=2));
for q in results:print(q['id'],q['matched_windows'],q['elapsed_ms'],[(a['start'],a['best_rank']) for a in q['targets']])
