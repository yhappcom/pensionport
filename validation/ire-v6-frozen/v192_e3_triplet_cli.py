"""Private V192 E3 triple review and sealed source-only reference CLI.

Use outside GitHub/Actions with owner-private files; does not run V123/E4/E5.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v191_e3_parent_first import E3ParentFirst
from v192_e3_triplet_alignment import E3TripletAlignment
from v192_e3_frozen_reference import verify_reference,score_without_gold


def main(argv=None):
    parser=argparse.ArgumentParser(description='V192 owner-private E3 comparison; no approval')
    sub=parser.add_subparsers(dest='action',required=True)
    for action in ('status','prepare','submit'):
        p=sub.add_parser(action)
        for n in ('owner_source','video_id','owner_db','second_db','parent_db','triple_db',
                  'source_sha','owner_head','second_head','parent_head','triple_head'):
            p.add_argument('--'+n.replace('_','-'),required=True)
        p.add_argument('--window-size',type=int,default=125)
        p.add_argument('--expected-window-count',type=int,default=2)
        p.add_argument('--limit',type=int,default=4)
        if action=='submit':
            p.add_argument('--packet-file',required=True)
            p.add_argument('--answer-file',required=True)
    p=sub.add_parser('reference-verify')
    p.add_argument('--reference-file',required=True)
    p.add_argument('--reference-sha',required=True)
    p.add_argument('--source-sha',required=True)
    args=parser.parse_args(argv)
    if args.action=='reference-verify':
        ref=verify_reference(args.reference_file,
           expected_reference_sha256=args.reference_sha,
           expected_source_sha256=args.source_sha)
        print(json.dumps(score_without_gold(ref),ensure_ascii=False,indent=2));return
    raw=Path(args.owner_source).read_bytes()
    if sha256(raw)!=args.source_sha:raise InvalidInput('V192_CLI_SOURCE_PIN_CHANGED')
    owner=EngineChatSession(args.owner_db,raw,args.video_id,owner_source_sha256=args.source_sha,
                            window_size=args.window_size,
                            expected_window_count=args.expected_window_count)
    second=E3TwoTurnAudit(owner,args.second_db,expected_owner_head=args.owner_head)
    parent=E3ParentFirst(owner,second,args.parent_db,
                        expected_owner_head=args.owner_head,
                        expected_second_head=args.second_head,max_span=14)
    triple=E3TripletAlignment(parent,args.triple_db,
             expected_owner_head=args.owner_head,
             expected_second_head=args.second_head,
             expected_parent_head=args.parent_head)
    if triple.status()['alignment_head']!=args.triple_head:
        raise InvalidInput('V192_CLI_ALIGNMENT_HEAD_CHANGED')
    if args.action=='status':result=triple.status()
    elif args.action=='prepare':result=triple.prepare(limit=args.limit)
    else:
        packet=json.loads(Path(args.packet_file).read_text())
        answer=json.loads(Path(args.answer_file).read_text())
        result=triple.submit(packet,answer)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()