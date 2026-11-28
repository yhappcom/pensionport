import hashlib,json,time
from pathlib import Path
from topic_index import search,sha
p=json.loads(Path('query_plan.json').read_text());rows=[];all_results={};times=[]
before=sha(Path('index.db').read_bytes())
for q in p['queries']:
    kw={k:p[k] for k in ('limit','per_source','context')};t=time.perf_counter();r=search('index.db',q['groups'],**kw);elapsed=time.perf_counter()-t;times.append(elapsed)
    r2=search('index.db',q['groups'],**kw);assert r==r2
    full=search('index.db',q['groups'],limit=10000,per_source=10000,context=p['context'])
    def find(res,v,a,b):
        return [i for i,w in enumerate(res['results'],1) if v in [x['video_id'] for x in w['aliases']] and w['context'][0]['cue']<=a and w['context'][-1]['cue']>=b]
    targets=[dict(video=v,first=a,last=b,top30=find(r,v,a,b),uncapped=find(full,v,a,b)) for v,a,b in q['expected']]
    row=dict(id=q['id'],question=q['question'],matched_sources=r['matched_sources'],matched_windows=r['matched_windows'],returned=len(r['results']),expected=targets,pass_top30=all(x['top30'] for x in targets) and (not r['results'] if q.get('no_match') else True),elapsed_ms=round(elapsed*1000,3),replay_equal=True)
    rows.append(row);all_results[q['id']]=r;print(json.dumps(row,ensure_ascii=False))
assert before==sha(Path('index.db').read_bytes())
result=dict(plan_sha=sha(Path('query_plan.json').read_bytes()),db_sha=before,rows=rows,top30_targets=sum(bool(x['top30']) for r in rows for x in r['expected']),uncapped_targets=sum(bool(x['uncapped']) for r in rows for x in r['expected']),target_count=sum(len(r['expected']) for r in rows),queries_pass=sum(r['pass_top30'] for r in rows),query_count=len(rows),replay_equal=len(rows),db_unchanged=True,limits=['Known source anchors selected manually; not independent or exhaustive semantic retrieval recall','Full diagnostic removes per-source and total caps but still suppresses overlapping windows','No-match synthetic string is a technical check only'])
Path('query_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');Path('retrieved.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2)+'\n')
