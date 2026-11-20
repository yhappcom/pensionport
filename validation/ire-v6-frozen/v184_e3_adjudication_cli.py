"""Owner-private E3 source adjudication CLI. No E4, no model API, no approval."""
import argparse
import json
from pathlib import Path

from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v184_e3_adjudication import E3Adjudication


def main(argv=None):
    p=argparse.ArgumentParser(description='V184 E3 blind-disagreement arbitration (HOLD only)')
    for x in ('source','owner-db','second-pass-db','adjudication-db','video-id','owner-head'):
        p.add_argument('--'+x,required=True)
    p.add_argument('--window-size',type=int,default=125)
    p.add_argument('--new-adjudication-db',action='store_true')
    sub=p.add_subparsers(dest='action',required=True)
    prepare=sub.add_parser('prepare')
    prepare.add_argument('--cues',help='Explicit sorted source indices (optional)')
    prepare.add_argument('--radius',type=int,default=4)
    prepare.add_argument('--limit',type=int,default=12)
    prepare.add_argument('--out')
    submit=sub.add_parser('submit')
    submit.add_argument('--packet',required=True)
    submit.add_argument('--answer',required=True)
    submit.add_argument('--out')
    status=sub.add_parser('status')
    status.add_argument('--out')
    a=p.parse_args(argv)
    original=Path(a.source).read_bytes()
    engine=EngineChatSession(a.owner_db,original,a.video_id,
                             owner_source_sha256=sha256(original),
                             window_size=a.window_size)
    second=E3TwoTurnAudit(engine,a.second_pass_db,
                           expected_owner_head=a.owner_head)
    audit=E3Adjudication(second,a.adjudication_db,
                         create=a.new_adjudication_db)
    if a.action=='prepare':
        selected=([int(x) for x in a.cues.split(',')] if a.cues else None)
        result=audit.prepare(cue_indices=selected,limit=a.limit,
                             context_radius=a.radius)
    elif a.action=='submit':
        result=audit.submit(json.loads(Path(a.packet).read_text()),
                            json.loads(Path(a.answer).read_text()))
    else:
        result=audit.status()
    output=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if a.out:
        Path(a.out).write_text(output)
    else:
        print(output,end='')
    return 0


if __name__=='__main__':
    raise SystemExit(main())