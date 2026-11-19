"""Private source E4 engine/ChatGPT handoff CLI.

Usage (never upload owner SRT or SQLite journal to public GitHub):\n  # Add --new-session ONLY on first intentional run, or restore the owner checkpoint.\n  # For established sessions use --resume-head SHA --resume-reviewed N.
  python v176_chat_engine_cli.py --srt private.srt --sha PIN --db private.db \
      --video-id VIDEO next --limit 8 --out challenge.json
  python v176_chat_engine_cli.py --srt private.srt --sha PIN --db private.db \
      --video-id VIDEO commit --challenge challenge.json --answer chat.json
  python v176_chat_engine_cli.py --srt private.srt --sha PIN --db private.db \
      --video-id VIDEO progress

All live semantic answers must come from the active ChatGPT host. The CLI has
no model API, auto-approval or write-to-E5 command.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from v176_chat_engine_loop import EngineChatSession


def _private_json(path, obj):
    p=Path(path);p.parent.mkdir(parents=True, exist_ok=True)
    fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w',encoding='utf8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
        f.write('\n')
    os.chmod(p,0o600)


def main(argv=None):
    ap=argparse.ArgumentParser(description='V176 interactive engine-owned E4 research loop, no LLM API')
    ap.add_argument('--srt',required=True)
    ap.add_argument('--db',required=True)
    ap.add_argument('--sha',required=True,help='External original SRT sha256 pin')
    ap.add_argument('--video-id',required=True)
    ap.add_argument('--window-size',type=int,default=120)
    ap.add_argument('--windows',type=int,default=13)
    ap.add_argument('--new-session',action='store_true',
                    help='Explicit permission to create a NEW empty research journal; NEVER set when resuming')
    ap.add_argument('--resume-head',help='Externally retained last 64-character journal head for old session')
    ap.add_argument('--resume-reviewed',type=int,help='Externally retained count of reviewed source cues')
    sub=ap.add_subparsers(dest='action',required=True)
    next_=sub.add_parser('next');next_.add_argument('--limit',type=int,default=8)
    next_.add_argument('--radius',type=int,default=3)
    next_.add_argument('--out')
    meaning=sub.add_parser('next-meaning');meaning.add_argument('--limit',type=int,default=20)
    meaning.add_argument('--radius',type=int,default=5)
    meaning.add_argument('--out')
    submit=sub.add_parser('commit');submit.add_argument('--challenge',required=True)
    submit.add_argument('--answer',required=True)
    risk=sub.add_parser('repair-noatom');risk.add_argument('--cue',type=int,required=True)
    risk.add_argument('--radius',type=int,default=10);risk.add_argument('--out')
    repair=sub.add_parser('repair-atom');repair.add_argument('--cue',type=int,required=True)
    repair.add_argument('--radius',type=int,default=10)
    repair.add_argument('--out')
    sub.add_parser('progress')
    staged=sub.add_parser('native-stage');staged.add_argument('--out',help='PRIVATE ONLY: full exchange JSON path')
    args=ap.parse_args(argv)
    # V176's Python EngineChatSession is intentionally able to create a new
    # journal for fresh videos. The operator-facing CLI MUST NEVER silently
    # convert a missing *old* owner journal into an empty one during a restart.
    db_path=Path(args.db)
    if args.new_session:
        if db_path.exists() or db_path.is_symlink():
            ap.error('V177_NEW_SESSION_REQUIRES_ABSENT_JOURNAL')
        if args.action not in ('next','next-meaning'):
            ap.error('V177_NEW_SESSION_ONLY_FOR_FIRST_CHALLENGE')
        if args.resume_head is not None or args.resume_reviewed is not None:
            ap.error('V177_FRESH_AND_RESUME_PINS_CONFLICT')
    else:
        if not db_path.is_file() or db_path.is_symlink():
            ap.error('V177_MISSING_EXISTING_JOURNAL_DO_NOT_RESET_USE_PRIVATE_CHECKPOINT')
        if (args.resume_head is None) != (args.resume_reviewed is None):
            ap.error('V177_RESUME_HEAD_AND_COUNT_MUST_BOTH_BE_GIVEN')
        import stat
        if stat.S_IMODE(db_path.stat().st_mode) & 0o077:
            ap.error('V177_INSECURE_PRIVATE_JOURNAL_PERMISSIONS')
    raw=Path(args.srt).read_bytes()
    engine=EngineChatSession(args.db,raw,args.video_id,owner_source_sha256=args.sha,
                             window_size=args.window_size,
                             expected_window_count=args.windows)
    if args.resume_head is not None:
        status=engine.progress()
        if (status['checkpoint_head_sha256'] != args.resume_head or
                status['cue_reviewed'] != args.resume_reviewed):
            ap.error('V177_RESUME_PIN_MISMATCH_DO_NOT_RESET')
    if args.action in ('next','next-meaning'):
        result=engine.prepare(limit=args.limit,context_radius=args.radius,
                              source_first_only=(args.action=='next-meaning'))
        if args.out: _private_json(args.out,result)
    elif args.action=='repair-atom':
        result=engine.prepare_atom_repair(args.cue,context_radius=args.radius)
        if args.out:_private_json(args.out,result)
    elif args.action=='repair-noatom':
        result=engine.prepare_nonresearch_risk_revisit(args.cue,context_radius=args.radius)
        if args.out:_private_json(args.out,result)
    elif args.action=='commit':
        task=json.loads(Path(args.challenge).read_text(encoding='utf8'))
        answer=json.loads(Path(args.answer).read_text(encoding='utf8'))
        if task.get('type') in ('RESOLVE_CONTEXT_CUES','REPAIR_ATOM_SOURCE_CONTEXT','REVISIT_NONRESEARCH_ATOM_RISK'):
            result=engine.submit_context_revisit(task,answer)
        elif task.get('type')=='SEARCH_ORIGINAL_PRIMARY_EVIDENCE':
            result=engine.submit_evidence_proposals(task,answer)
        else:
            result=engine.submit(task,answer)
    elif args.action=='progress': result=engine.work_summary()
    else:
        exchange,result=engine.compile_native_v6_stage()
        if args.out:_private_json(args.out,exchange)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':sys.exit(main())