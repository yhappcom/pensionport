import json, hashlib, time
from pathlib import Path
from engine import Engine, digest
from d4_quality import ContextEngine
p=Path('original'); man=json.loads((p/'MANIFEST.json').read_text()); assert all(hashlib.sha256((p/k).read_bytes()).hexdigest()==v for k,v in man.items())
trial=p/'trial1.db'; op=Path('D4_OPERATIONAL_THIRD_20261127.db'); before={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (trial,op,p/'trial2.db')}
e=ContextEngine(trial); sid=json.loads((p/'final.json').read_text())['source_id'];
with e.db() as c:
    cat=e.catalog(c); head=e.head(c)
a,b=sid+':I21',sid+':I20'
reg=dict(head=head,reviewed=True,edges=[{'from':a,'to':b,'kind':'REQUIRED_CONTEXT','reason':'실물보유 해지 방식 검토 시 특례 적용기간 및 이후 소득 일반과세를 함께 확인; 동일 회사 FAQ 범위, 자동 적용 아님.','from_sha':digest(cat[a]),'to_sha':digest(cat[b])}])
Path('trial_registry.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2))
queries=json.loads((p/'RESULT.json').read_text())['queries'][0]; results=[]
for q in queries:
    t=time.perf_counter(); r=e.query_context(q['terms'],reg); dt=time.perf_counter()-t
    direct=[x['item']['id'] for x in r['direct'] if x['item']['source_id']==sid]; ctx=[x['id'] for x in r['context'] if x['source_id']==sid]; req=q['required']; ok=set(req)<=set(direct+ctx) if req else not r['direct'] and not r['context']; assert ok
    other=ContextEngine(p/'trial2.db').query_context(q['terms'],reg); assert r==other
    results.append(dict(terms=q['terms'],required=req,direct=direct,context=ctx,passed=bool(ok),seconds=dt))
assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in before.items())
result=dict(manifest=len(man),prior_pass=sum(x['pass'] for x in queries),after_pass=sum(x['passed'] for x in results),total=len(queries),replay_equal=len(queries),db_unchanged=before,results=results,scope='diagnostic known query suite, manual single edge, not independent or semantic certification')
Path('repair_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)); print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False)); print(results[1]); print('range',min(x['seconds'] for x in results),max(x['seconds'] for x in results))
