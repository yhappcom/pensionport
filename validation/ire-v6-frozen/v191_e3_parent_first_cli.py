"""Owner-private V191 E3 parent-first CLI. No API calls or approval entry points."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v191_e3_parent_first import E3ParentFirst


def _json(path):
    return json.loads(Path(path).read_text('utf-8'))


def _save(path,obj):
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        raise ValueError('Refusing to overwrite packet or owner-private answer')
    fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
        f.write('\n')


def main():
    ap=argparse.ArgumentParser(description='V191 owner-source E3 parent-first, E4 disabled')
    ap.add_argument('--original-srt',required=True)
    ap.add_argument('--owner-db',required=True)
    ap.add_argument('--second-db',required=True)
    ap.add_argument('--parent-db',required=True)
    ap.add_argument('--video-id',required=True)
    ap.add_argument('--source-sha256',required=True)
    ap.add_argument('--owner-head',required=True)
    ap.add_argument('--second-head',required=True)
    ap.add_argument('--max-span',type=int,default=14)
    ap.add_argument('--window-size',type=int,default=125)
    ap.add_argument('--create',action='store_true')
    sub=ap.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--end',type=int,required=True)
    prep.add_argument('--context-radius',type=int,default=3);prep.add_argument('--out',required=True)
    subm=sub.add_parser('submit');subm.add_argument('--packet',required=True)
    subm.add_argument('--answer',required=True)
    status=sub.add_parser('status');status.add_argument('--out')
    comp=sub.add_parser('compare');comp.add_argument('--out')
    opt=ap.parse_args()
    src=Path(opt.original_srt).read_bytes()
    if sha256(src)!=opt.source_sha256:raise ValueError('Owner source SHA does not match')
    owner=EngineChatSession(opt.owner_db,src,opt.video_id,owner_source_sha256=opt.source_sha256,
                            window_size=opt.window_size)
    second=E3TwoTurnAudit(owner,opt.second_db,expected_owner_head=opt.owner_head)
    session=E3ParentFirst(owner,second,opt.parent_db,
            expected_owner_head=opt.owner_head,expected_second_head=opt.second_head,
            create=opt.create,max_span=opt.max_span)
    if opt.action=='prepare':
        packet=session.prepare(opt.end,context_radius=opt.context_radius)
        _save(opt.out,packet);print('Source-only E3 parent packet written to private file')
    elif opt.action=='submit':
        print(json.dumps(session.submit(_json(opt.packet),_json(opt.answer)),ensure_ascii=False,indent=2))
    else:
        result=session.status() if opt.action=='status' else session.compare_unapproved()
        if opt.out:_save(opt.out,result)
        else:print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()