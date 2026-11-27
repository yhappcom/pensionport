"""Read-only original candidate; migrate twice and compare known query behavior."""
import json, sqlite3, time
from contextlib import closing
from pathlib import Path
from engine import sha,digest,Engine
from d4_gate import GateEngine
from d4_gate_v2 import ObligationGate

root=Path(__file__).parent
source=root/'D4_GATE_CANDIDATE_BASELINE_20261127.db'
expected='7ad9091c27b6b909cbec451e7241b7824e4e47aa25b1f1068c85cd67e7ca7a34'
assert sha(source.read_bytes())==expected
v1=GateEngine(source)
paths=[root/'candidate_v2_a.db',root/'candidate_v2_b.db']
v2=[ObligationGate.migrate(source,p,expected) for p in paths]
assert v1.status()==v2[0].status()==v2[1].status()
def snap(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as c:
        assert c.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        return {t:c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in ['videos','items','gate_freeze','gate_audit']}, c.execute('SELECT head FROM meta').fetchall(),c.execute('SELECT registry FROM gate_state').fetchall()
base=snap(source)
assert all(snap(p)==base for p in paths)
for cls in (Engine,GateEngine):
    try: cls(paths[0]); raise AssertionError('old entrypoint accepted v2')
    except ValueError: pass
qs=json.loads((root/'baseline/baseline_result.json').read_text())['queries'];out=[]
for q in qs:
    original=v1.query(q['terms']); st=time.perf_counter();a=v2[0].query(q['terms']);t=time.perf_counter()-st;b=v2[1].query(q['terms'])
    assert a==b==original
    direct=[x['item']['id'] for x in a['direct']];context=[x['id'] for x in a['context']];actual=set(direct+context)
    assert set(q['required'])<=actual and not set(q['forbidden'])&actual
    if not q['required']: assert not actual
    out.append(dict(id=q['id'],terms=q['terms'],direct=direct,context=context,equal=True,passed=True,seconds=t))
newhash=[sha(p.read_bytes()) for p in paths];assert newhash[0]==newhash[1];assert sha(source.read_bytes())==expected
result=dict(status='CANDIDATE_TECHNICAL_REPLAY_PASS',original_sha=expected,original_sha_after=sha(source.read_bytes()),v2_sha=newhash,prior_rows_preserved={t:len(v) for t,v in base[0].items()},head_preserved=True,registry_preserved=True,integrity='ok',foreign_key_violations=0,old_entrypoints_blocked=2,query_pass=len(out),query_replay_equal=len(out),queries=out,status_db=v2[0].status(),operational_promoted=False,limits=['known manual keyword tests on existing 37 active items','no new source semantic or finance evaluation','candidate only'])
(root/'replay_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='queries'},ensure_ascii=False,indent=2))
