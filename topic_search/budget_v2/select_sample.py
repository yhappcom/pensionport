import sys,hashlib,json,zipfile,re
from pathlib import Path
sys.path.insert(0,'/mnt/data/c1_topic')
from engine import parse_srt
seed='C1-fresh-budget-20261128-v2'
prior=json.load(open('/mnt/data/c1_semantic/sample_plan.json'))
excluded={x['sha'] for x in prior['picks']}
picks=[];raws=[]
for name in ['1-100.zip','101-200.zip','201-300.zip']:
 with zipfile.ZipFile('/mnt/data/'+name) as z:
  ns=[n for n in z.namelist() if n.endswith('.srt') and not n.startswith('__MACOSX/')]
  for n in sorted(ns,key=lambda n:hashlib.sha256((seed+n).encode()).hexdigest()):
   raw=z.read(n);sha=hashlib.sha256(raw).hexdigest()
   if sha in excluded:continue
   cues=parse_srt(raw);start=1+int(hashlib.sha256((seed+sha).encode()).hexdigest()[:12],16)%max(1,len(cues)-49);end=min(start+49,len(cues))
   picks.append(dict(archive=name,member=n,sha=sha,video=re.search(r'youtube-transcript-([\w-]{11})',n).group(1),start=start,end=end));raws.append(cues[start-1:end]);break
plan=dict(seed=seed,selection='one hash-ranked nonprior member per archive; hash-selected 50-cue span; before retrieval',picks=picks,budget=dict(max_contexts_per_query=12,padding=8,width=48,stride=12),target_recovery_min=.95,high_risk_misses_max=0)
Path('sample_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(plan,ensure_ascii=False,indent=2));
for p,cs in zip(picks,raws):
 print('\n',p['video']);print('\n'.join(f"{c['id']} {c['text']}" for c in cs))
