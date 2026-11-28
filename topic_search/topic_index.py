"""SRT-only topic discovery. Results are raw, unverified speaker material.
Deterministic literal retrieval; no semantic completeness or approval claim.
"""
import argparse, hashlib, json, re, sqlite3, unicodedata, zipfile
from pathlib import Path
from contextlib import closing
from engine import parse_srt
WINDOW, STRIDE = 24, 12
VERSION = 'TOPIC_INDEX_1'

def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return ''.join(unicodedata.normalize('NFKC',s).casefold().split())
def require(v,msg):
    if not v: raise ValueError(msg)

def build(path, archives):
    path=Path(path); require(not path.exists(),'destination exists')
    archives=sorted(map(Path,archives),key=lambda p:p.name)
    require(len({p.name for p in archives})==len(archives),'duplicate archive name')
    tmp=path.with_suffix(path.suffix+'.building');require(not tmp.exists(),'staging exists')
    try:
        with closing(sqlite3.connect(tmp)) as c, c:
            c.execute('PRAGMA foreign_keys=ON')
            c.executescript('''CREATE TABLE meta(version TEXT NOT NULL);
            CREATE TABLE archives(name TEXT PRIMARY KEY, sha TEXT NOT NULL, bytes INTEGER NOT NULL);
            CREATE TABLE sources(sid TEXT PRIMARY KEY, raw BLOB NOT NULL, n INTEGER NOT NULL, duration_ms INTEGER NOT NULL);
            CREATE TABLE aliases(archive TEXT REFERENCES archives(name), member TEXT, sid TEXT REFERENCES sources(sid), video_id TEXT, PRIMARY KEY(archive,member));
            CREATE TABLE cues(sid TEXT REFERENCES sources(sid), cue INTEGER, start_ms INTEGER, end_ms INTEGER, text TEXT, PRIMARY KEY(sid,cue));
            CREATE TABLE windows(id INTEGER PRIMARY KEY,sid TEXT REFERENCES sources(sid), first_cue INTEGER,last_cue INTEGER, body TEXT);
            CREATE INDEX window_source ON windows(sid,first_cue);
            CREATE VIRTUAL TABLE search_fts USING fts5(body,content='windows',content_rowid='id',tokenize='trigram');''')
            c.execute('INSERT INTO meta VALUES(?)',(VERSION,))
            for a in archives:
                raw=a.read_bytes();c.execute('INSERT INTO archives VALUES(?,?,?)',(a.name,sha(raw),len(raw)))
                with zipfile.ZipFile(a) as z:
                    require(z.testzip() is None,'archive CRC failure')
                    for n in sorted(z.namelist()):
                        if n.startswith('__MACOSX/') or not n.lower().endswith('.srt'):continue
                        b=z.read(n);sid=sha(b)
                        m=re.fullmatch(r'youtube-transcript-([\w-]{11})(?: \(\d+\)|_public_auto_timed_\d{8})?\.srt',Path(n).name,re.I)
                        require(m is not None,'unknown video ID: '+n)
                        if c.execute('SELECT 1 FROM sources WHERE sid=?',(sid,)).fetchone() is None:
                            cues=parse_srt(b);c.execute('INSERT INTO sources VALUES(?,?,?,?)',(sid,b,len(cues),cues[-1]['end_ms']))
                            c.executemany('INSERT INTO cues VALUES(?,?,?,?,?)',[(sid,x['id'],x['start_ms'],x['end_ms'],x['text']) for x in cues])
                            for start in range(0,len(cues),STRIDE):
                                w=cues[start:start+WINDOW];body=norm(''.join(x['text'] for x in w))
                                c.execute('INSERT INTO windows(sid,first_cue,last_cue,body) VALUES(?,?,?,?)',(sid,w[0]['id'],w[-1]['id'],body))
                                if start+WINDOW>=len(cues):break
                        c.execute('INSERT INTO aliases VALUES(?,?,?,?)',(a.name,n,sid,m.group(1)))
            c.execute("INSERT INTO search_fts(search_fts) VALUES('rebuild')")
            require(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','integrity failure')
            require(not c.execute('PRAGMA foreign_key_check').fetchall(),'foreign key failure')
            c.execute("INSERT INTO search_fts(search_fts,rank) VALUES('integrity-check',1)")
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True);raise
    return stats(path)

def connect(path):
    c=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    c.row_factory=sqlite3.Row
    require(c.execute('SELECT version FROM meta').fetchone()[0]==VERSION,'wrong index version')
    return c

def stats(path):
    with closing(connect(path)) as c:
        return dict(version=VERSION,archives=[dict(r) for r in c.execute('SELECT * FROM archives ORDER BY name')],**{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('aliases','sources','cues','windows')},duration_ms=c.execute('SELECT sum(duration_ms) FROM sources').fetchone()[0],video_ids=c.execute('SELECT count(DISTINCT video_id) FROM aliases').fetchone()[0],id_conflicts=[dict(r) for r in c.execute('SELECT video_id,count(DISTINCT sid) variants FROM aliases GROUP BY video_id HAVING variants>1')])

def search(path,groups,limit=30,per_source=3,context=8):
    require(isinstance(groups,list) and groups and all(isinstance(g,list) and g and all(isinstance(t,str) and len(norm(t))>=2 for t in g) for g in groups),'nonempty groups, terms >=2 normalized characters required')
    require(type(limit) is int and limit>0 and type(per_source) is int and per_source>0 and type(context) is int and 0<=context<=100,'invalid search limits')
    groups=[sorted(set(map(norm,g))) for g in groups]
    require(len({tuple(g) for g in groups})==len(groups),'duplicate groups')
    with closing(connect(path)) as c:
        # All groups required; aliases OR. FTS trigram prefilter, two-character terms exact LIKE scan.
        sets=[]
        for group in groups:
            hit=set()
            for t in group:
                if len(t)>=3:
                    hit.update(r[0] for r in c.execute('SELECT rowid FROM search_fts WHERE search_fts MATCH ?',('"'+t.replace('"','""')+'"',)))
                else:
                    hit.update(r[0] for r in c.execute('SELECT id FROM windows WHERE instr(body,?)>0',(t,)))
            sets.append(hit)
            if not hit: return dict(status='RAW_UNVERIFIED',matched_windows=0,matched_sources=0,results=[])
        ids=set.intersection(*sets); ranked=[]
        for k in ids:
            w=c.execute('SELECT * FROM windows WHERE id=?',(k,)).fetchone();body=w['body']
            hits=[[t for t in g if t in body] for g in groups]
            if not all(hits):continue
            # Proximity of best group positions and specificity, not finance validity.
            positions=[min(body.index(t) for t in h) for h in hits]
            span=max(positions)-min(positions)
            score=sum(max(len(t) for t in h) for h in hits)*10 + sum(min(3,sum(body.count(t) for t in h)) for h in hits)-min(span,500)/100
            ranked.append((score,w,hits))
        ranked.sort(key=lambda x:(-x[0],x[1]['sid'],x[1]['first_cue']))
        out=[];selected={}
        for score,w,hits in ranked:
            sid=w['sid'];ranges=selected.setdefault(sid,[])
            if len(ranges)>=per_source or any(w['first_cue']<=b and a<=w['last_cue'] for a,b in ranges):continue
            ranges.append((w['first_cue'],w['last_cue']))
            cues=[dict(r) for r in c.execute('SELECT cue,start_ms,end_ms,text FROM cues WHERE sid=? AND cue BETWEEN ? AND ? ORDER BY cue',(sid,max(1,w['first_cue']-context),w['last_cue']+context))]
            aliases=[dict(r) for r in c.execute('SELECT archive,member,video_id FROM aliases WHERE sid=? ORDER BY archive,member',(sid,))]
            out.append(dict(source_sha=sid,aliases=aliases,first_cue=w['first_cue'],last_cue=w['last_cue'],hits=hits,score=round(score,3),context=cues,status='RAW_UNVERIFIED'))
            if len(out)>=limit:break
        return dict(status='RAW_UNVERIFIED',matched_windows=len(ranked),matched_sources=len({w['sid'] for _,w,_ in ranked}),results=out)

def verify(path):
    with closing(connect(path)) as c:
        count=0
        for s in c.execute('SELECT * FROM sources'):
            require(sha(s['raw'])==s['sid'],'source hash mismatch');parsed=parse_srt(s['raw'])
            saved=[dict(r) for r in c.execute('SELECT cue AS id,start_ms,end_ms,text FROM cues WHERE sid=? ORDER BY cue',(s['sid'],))]
            require(parsed==saved and len(parsed)==s['n'] and parsed[-1]['end_ms']==s['duration_ms'],'cue mismatch')
            expected=[]
            for start in range(0,len(parsed),STRIDE):
                w=parsed[start:start+WINDOW];expected.append((w[0]['id'],w[-1]['id'],norm(''.join(x['text'] for x in w))))
                if start+WINDOW>=len(parsed):break
            actual=[tuple(r) for r in c.execute('SELECT first_cue,last_cue,body FROM windows WHERE sid=? ORDER BY first_cue',(s['sid'],))]
            require(expected==actual,'window mismatch');count+=1
        return dict(verified_sources=count,integrity=c.execute('PRAGMA integrity_check').fetchone()[0],foreign_key_violations=len(c.execute('PRAGMA foreign_key_check').fetchall()))

def main():
    p=argparse.ArgumentParser();p.add_argument('db');p.add_argument('action',choices=['build','stats','verify','search']);p.add_argument('args',nargs='*');a=p.parse_args()
    result=build(a.db,a.args) if a.action=='build' else stats(a.db) if a.action=='stats' else verify(a.db) if a.action=='verify' else search(a.db,json.loads(a.args[0]))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
