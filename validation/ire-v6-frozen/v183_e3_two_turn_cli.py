"""Private CLI for V183 E3 blind source-only cross-turn review. E4 is not used."""
import argparse
import json
from pathlib import Path

from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit


def main(argv=None):
    p=argparse.ArgumentParser(description='V183 E3 source-only second-turn comparison; no E4 approval')
    for name in ('source','owner-db','audit-db','video-id','owner-head'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--window-size',type=int,default=125)
    p.add_argument('--new-audit-db',action='store_true')
    sub=p.add_subparsers(dest='action',required=True)
    prepare=sub.add_parser('prepare')
    prepare.add_argument('--limit',type=int,default=12)
    prepare.add_argument('--radius',type=int,default=6)
    prepare.add_argument('--cues',help='Comma-separated exact source indices; targeted, not a random sample')
    prepare.add_argument('--out')
    submit=sub.add_parser('submit')
    submit.add_argument('--packet',required=True)
    submit.add_argument('--answer',required=True)
    submit.add_argument('--out')
    status=sub.add_parser('status')
    status.add_argument('--out')
    args=p.parse_args(argv)
    source=Path(args.source).read_bytes()
    eng=EngineChatSession(args.owner_db,source,args.video_id,
                          owner_source_sha256=sha256(source),window_size=args.window_size)
    audit=E3TwoTurnAudit(eng,args.audit_db,expected_owner_head=args.owner_head,
                         create=args.new_audit_db)
    if args.action=='prepare':
        selected=([int(x) for x in args.cues.split(',')] if args.cues else None)
        result=audit.prepare(cue_indices=selected,limit=args.limit,context_radius=args.radius)
    elif args.action=='submit':
        result=audit.submit(json.loads(Path(args.packet).read_text()),
                            json.loads(Path(args.answer).read_text()))
    else:
        result=audit.status()
    text=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if args.out:
        Path(args.out).write_text(text)
    else:
        print(text,end='')
    return 0

if __name__=='__main__':
    raise SystemExit(main())