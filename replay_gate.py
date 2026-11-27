"""Read existing research copies; migrate disposable fixtures only, never promote."""
import argparse, json, tempfile, time
from pathlib import Path
from engine import Engine, sha, digest
from d4_gate import GateEngine

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('root',type=Path,help='Directory containing operational DB and original/ extracted #263 HOLD archive')
ROOT=parser.parse_args().root
op=ROOT/'D4_OPERATIONAL_THIRD_20261127.db'
trial=ROOT/'original/trial1.db'
trial2=ROOT/'original/trial2.db'
files=[op,trial,trial2]
before={str(x):sha(x.read_bytes()) for x in files}
assert before[str(op)]=='f289801aebde88908355f269bc5d5903046cd8f420db26ade3ccd421bc60b1ef'
assert before[str(trial)]==before[str(trial2)]=='2856648a415aceedc6befd565f08f9e81c9cde28d80372d4c7746484ce551d40'

def rejects(fn):
    try: fn()
    except ValueError: return True
    raise AssertionError('unexpected accept')

def rows(e):
    with e.db() as c:
        return [c.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall() for table in ('videos','items')]

def migrate(path,target):
    a=Engine(path); b=GateEngine.migrate(path,target,before[str(path)]); assert a.status()==b.status(); assert rows(a)==rows(b)
    assert rejects(lambda:Engine(target)); assert rejects(lambda:b.query(['ISA']));
    with b.db() as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
    return b

with tempfile.TemporaryDirectory() as d:
    d=Path(d)
    pending=migrate(op,d/'pending.db')
    assert rejects(lambda:pending.bootstrap_registry([],[],'incomplete fixture'))
    assert pending.status()['active']==37 and pending.status()['decisions']==61
    a=migrate(trial,d/'trial_a.db'); b=migrate(trial2,d/'trial_b.db')
    sid=json.loads((ROOT/'original/final.json').read_text())['source_id']; spec={'from':sid+':I21','to':sid+':I20','kind':'REQUIRED_CONTEXT','reason':'known diagnostic relation only: tax period in real-holding exit'}
    for g in (a,b):
        with g.db() as c: active=sorted(g.eligible(g.catalog(c)))
        # Mechanical fixture: not a semantic review of all 63 active records. Never promote.
        g.bootstrap_registry([spec],active,'DISPOSABLE DIAGNOSTIC FIXTURE ONLY; not an operational baseline review')
    cases=json.loads((ROOT/'original/RESULT.json').read_text())['queries'][0]; results=[]
    for q in cases:
        t=time.perf_counter(); x=a.query(q['terms']); elapsed=time.perf_counter()-t
        y=b.query(q['terms']); assert x==y
        found={z['item']['id'] for z in x['direct'] if z['item']['source_id']==sid}|{z['id'] for z in x['context'] if z['source_id']==sid}
        ok=set(q['required'])<=found if q['required'] else not x['direct'] and not x['context']; assert ok
        results.append(dict(terms=q['terms'],required=q['required'],found=sorted(found),seconds=elapsed))
    # Historical final is not a new gated result; reject replay without new review.
    assert rejects(lambda:a.finalize(json.loads((ROOT/'original/final.json').read_text())))
    assert a.audit(sid) is None
    result=dict(scope='technical migration and known diagnostic queries only',operational_status=pending.status(),operational_copy_registry='PENDING_BASELINE_REVIEW',legacy_rows_equal=True,legacy_entrypoint_blocked=True,bootstrap_incomplete_blocked=True,integrity='ok',diagnostic_query_pass=len(results),diagnostic_query_replay=len(results),results=results,historical_final_without_gate_blocked=True,originals_unchanged=all(sha(Path(k).read_bytes())==v for k,v in before.items()),original_sha256=before)
    assert result['originals_unchanged']
Path('gate_replay_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False))
