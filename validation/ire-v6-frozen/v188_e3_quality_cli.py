"""Read-only V188 E3 quality handoff audit CLI (no approvals)."""
import argparse,json
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v184_e3_adjudication import E3Adjudication
from v188_e3_quality_gate import evaluate_live

def main(argv=None):
    p=argparse.ArgumentParser(description='V188 source-only dual-pass and causal gate; E3 must stay HOLD')
    for n in ['source','owner-db','second-db','adjudication-db','video-id','owner-head']:
        p.add_argument('--'+n,required=True)
    p.add_argument('--window-size',type=int,default=125)
    p.add_argument('--parent-shift',type=int,default=8)
    p.add_argument('--out')
    args=p.parse_args(argv)
    raw=Path(args.source).read_bytes()
    owner=EngineChatSession(args.owner_db,raw,args.video_id,
         owner_source_sha256=sha256(raw),window_size=args.window_size)
    second=E3TwoTurnAudit(owner,args.second_db,expected_owner_head=args.owner_head)
    adj=E3Adjudication(second,args.adjudication_db)
    result=evaluate_live(adj,max_cue_shift=args.parent_shift)
    text=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if args.out:Path(args.out).write_text(text,encoding='utf-8')
    else:print(text,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())