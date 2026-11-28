"""Read-only coverage inventory candidate for TOPIC_INDEX_1.
48-cue windows, compact untruncated candidate inventory. Not semantic retrieval.
"""
from contextlib import closing
from topic_index import connect, norm, require

# Prior existing query_plan Q1 aliases, not inferred financial equivalence.
ALIASES = {'isa': ('is','ism')}

class CoverageSearch:
    def __init__(self, path, width=48, stride=12):
        require(type(width) is int and type(stride) is int and 0<stride<=width<=100,'invalid width/stride')
        self.path=path;self.windows=[];self.aliases={}
        with closing(connect(path)) as c:
            for r in c.execute('SELECT sid,video_id FROM aliases ORDER BY sid,video_id'):
                self.aliases.setdefault(r['sid'],[]).append(r['video_id'])
            for s in c.execute('SELECT sid,n FROM sources ORDER BY sid'):
                sid=s['sid']; cues=[norm(r['text']) for r in c.execute('SELECT text FROM cues WHERE sid=? ORDER BY cue',(sid,))]
                require(len(cues)==s['n'],'cue count mismatch')
                for start in range(0,len(cues),stride):
                    last=min(start+width,len(cues));self.windows.append((sid,start+1,last,''.join(cues[start:last])))
                    if last==len(cues):break
    def inventory(self,groups):
        require(isinstance(groups,list) and groups and all(isinstance(g,list) and g and all(isinstance(t,str) and norm(t) for t in g) for g in groups),'empty group')
        gs=[set(map(norm,g)) for g in groups]
        require(all(len(t)>=2 for g in gs for t in g) or (len(gs)>=2 and any(all(len(t)>=2 for t in g) for g in gs)), 'single-character query requires another selective group')
        gs=[sorted(g|{a for t in g for a in ALIASES.get(t,())}) for g in gs]
        rows=[]
        for sid,start,end,body in self.windows:
            hits=[[t for t in g if t in body] for g in gs]
            if not all(hits):continue
            positions=[min(body.index(t) for t in h) for h in hits]
            score=sum(max(len(t) for t in h) for h in hits)*10+sum(min(3,sum(body.count(t) for t in h)) for h in hits)-min(max(positions)-min(positions),500)/100
            rows.append(dict(source_sha=sid,video_ids=self.aliases[sid],first_cue=start,last_cue=end,hits=hits,score=round(score,3)))
        rows.sort(key=lambda r:(-r['score'],r['source_sha'],r['first_cue']))
        return dict(status='RAW_UNVERIFIED',expanded_groups=gs,matched_windows=len(rows),matched_sources=len({r['source_sha'] for r in rows}),results=rows)
    def context(self,row,padding=8):
        require(type(padding) is int and 0<=padding<=100,'invalid padding')
        with closing(connect(self.path)) as c:
            return [dict(r) for r in c.execute('SELECT cue,start_ms,end_ms,text FROM cues WHERE sid=? AND cue BETWEEN ? AND ? ORDER BY cue',(row['source_sha'],max(1,row['first_cue']-padding),row['last_cue']+padding))]
