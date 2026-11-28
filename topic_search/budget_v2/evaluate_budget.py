import json,hashlib,time
from pathlib import Path
from budget_search import select,CoverageSearch
DB=Path('/mnt/data/c1_topic/index.db')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert sha('reference.json')=='e1697ab1081154726f0cecb0c1b378922a2dbd127ea509f8020e67fee45857d1'
assert sha('sample_plan.json')=='bb10cc3c62056303a695d2d5ccf9fb5ccac27b428a38ff0170008fe0be7b8525'
assert sha('budget_search.py')=='e747708e00e34ed3f98a83f112d9c8bf0eb0d7e5c6704af15ee85ccc726654f1'
before=sha(DB);t=time.monotonic();s=CoverageSearch(DB);init=time.monotonic()-t
results=[];allcontexts={}
for q in json.load(open('reference.json'))['queries']:
 t=time.monotonic();inv=s.inventory(q['groups']);selected=select(inv,12);contexts=[dict(r,context=s.context(r,8)) for r in selected];allcontexts[q['id']]=contexts
 targets=[]
 for target in q['targets']:
  def covers(r):return target['video'] in r['video_ids'] and max(1,r['first_cue']-8)<=target['start'] and r['last_cue']+8>=target['end']
  full=next((i for i,r in enumerate(inv['results'],1) if covers(r)),None)
  rank=next((i for i,r in enumerate(contexts,1) if covers(r) and {c['cue'] for c in r['context']}>=set(range(target['start'],target['end']+1))),None)
  baseline=next((i for i,r in enumerate(inv['results'][:12],1) if covers(r)),None)
  targets.append(dict(target,inventory_rank=full,budget_rank=rank,plain_top12_rank=baseline))
 results.append(dict(id=q['id'],candidates=inv['matched_windows'],sources=inv['matched_sources'],selected=len(contexts),review_cues=sum(len(r['context']) for r in contexts),elapsed_ms=round((time.monotonic()-t)*1000,1),targets=targets))
alltargets=[t for r in results for t in r['targets']];high=[t for t in alltargets if t['risk']=='H'];count=lambda field,ts:sum(t[field] is not None for t in ts)
assert sha(DB)==before
result=dict(status='INTERNAL_SAMPLE_DIAGNOSTIC',db_sha=before,init_seconds=init,queries=results,targets=len(alltargets),high_risk=len(high),inventory_recovered=count('inventory_rank',alltargets),budget_recovered=count('budget_rank',alltargets),plain_top12_recovered=count('plain_top12_rank',alltargets),high_risk_budget=count('budget_rank',high),high_risk_inventory=count('inventory_rank',high),total_contexts=sum(r['selected'] for r in results),total_cues=sum(r['review_cues'] for r in results),db_unchanged=True)
write('RESULT.json',result);write('retrieval.json',allcontexts);print(json.dumps(result,ensure_ascii=False,indent=2))
