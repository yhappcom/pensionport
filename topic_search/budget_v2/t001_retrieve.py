import json,time,hashlib
from pathlib import Path
from budget_search import select,CoverageSearch
p=json.load(open('t001_plan.json'));db=Path('/mnt/data/c1_topic/index.db');h=hashlib.sha256(db.read_bytes()).hexdigest();s=CoverageSearch(db);res=[]
for q in p['queries']:
 t=time.monotonic();inv=s.inventory(q['groups']);chosen=select(inv,p['limit_per_query']);rows=[dict(r,context=s.context(r,p['padding'])) for r in chosen];res.append(dict(id=q['id'],candidates=inv['matched_windows'],sources=inv['matched_sources'],ms=round((time.monotonic()-t)*1000,1),rows=rows));print(q['id'],inv['matched_windows'],inv['matched_sources'])
 for i,r in enumerate(rows,1):
  print(i,r['video_ids'],r['first_cue'],r['last_cue']);print(' '.join(f"{c['cue']}:{c['text']}" for c in r['context']))
assert h==hashlib.sha256(db.read_bytes()).hexdigest();Path('t001_retrieval.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
