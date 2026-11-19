"""Read-only V185 E3 owner-private diagnostic; never reads/writes public E4.

Usage (private):
 PYTHONPATH=<repo-root> python v185_e3_parent_qualifier_cli.py \
   --source owner_original.srt --owner-db full_research_journal.sqlite \
   --second-db e3_second_pass.sqlite --adjudication-db e3_adjudication.sqlite \
   --video-id LVE7XN_esTc --owner-sha256 <PIN> --owner-head <HEAD> \
   --window-size 125 --expected-window-count 2 --out e3_diagnostic.json
"""
import argparse, json, os
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v184_e3_adjudication import E3Adjudication
from v185_e3_parent_qualifier_audit import analyze_live_owner


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','owner-db','second-db','adjudication-db','video-id',
                 'owner-sha256','owner-head','out'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--window-size',type=int,required=True)
    parser.add_argument('--expected-window-count',type=int,required=True)
    parser.add_argument('--max-cue-shift',type=int,default=4)
    args=parser.parse_args(argv)
    raw=Path(args.source).read_bytes()
    if sha256(raw)!=args.owner_sha256:
        parser.error('ORIGINAL_SOURCE_SHA_MISMATCH')
    engine=EngineChatSession(args.owner_db,raw,args.video_id,
           owner_source_sha256=args.owner_sha256,
           window_size=args.window_size,expected_window_count=args.expected_window_count)
    second=E3TwoTurnAudit(engine,args.second_db,expected_owner_head=args.owner_head)
    adjudication=E3Adjudication(second,args.adjudication_db)
    data=analyze_live_owner(adjudication,max_cue_shift=args.max_cue_shift)
    target=Path(args.out)
    if target.exists() or target.is_symlink():
        parser.error('DIAGNOSTIC_OUTPUT_MUST_NOT_OVERWRITE')
    target.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    print(json.dumps({k:data[k] for k in (
        'schema','second_reviewed_cues','unreviewed_cues',
        'cue_level_claim_presence_differences','possible_cross_cue_parent_alignment_cues',
        'first_qualifier_provenance','e3_quality_certified','e4_approved','e5_published')},
        ensure_ascii=False,sort_keys=True))
    return data

if __name__=='__main__': main()