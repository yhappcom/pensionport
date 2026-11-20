"""Owner-private E3 qualifier provenance review CLI; no model API and no E4."""
import argparse
import json
from pathlib import Path

from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v186_e3_qualifier_provenance import E3QualifierProvenance


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--owner-srt',type=Path,required=True)
    ap.add_argument('--owner-db',type=Path,required=True)
    ap.add_argument('--qualifier-db',type=Path,required=True)
    ap.add_argument('--video-id',required=True)
    ap.add_argument('--owner-source-sha256',required=True)
    ap.add_argument('--owner-head',required=True)
    ap.add_argument('--window-size',type=int,default=125)
    ap.add_argument('--window-count',type=int,default=2)
    ap.add_argument('--create',action='store_true')
    sp=ap.add_subparsers(dest='action',required=True)
    p=sp.add_parser('prepare');p.add_argument('--limit',type=int,default=16)
    p.add_argument('--radius',type=int,default=4)
    p.add_argument('--out',type=Path,required=True)
    p=sp.add_parser('submit');p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--answer',type=Path,required=True)
    p.add_argument('--out',type=Path)
    p=sp.add_parser('status');p.add_argument('--out',type=Path)
    p=sp.add_parser('native-stage');p.add_argument('--out',type=Path)
    args=ap.parse_args()
    raw=args.owner_srt.read_bytes()
    if sha256(raw)!=args.owner_source_sha256:
        raise SystemExit('OWNER_SOURCE_BYTES_SHA_MISMATCH')
    engine=EngineChatSession(args.owner_db,raw,args.video_id,
        owner_source_sha256=args.owner_source_sha256,
        window_size=args.window_size,expected_window_count=args.window_count)
    owner=E3QualifierProvenance(engine,args.qualifier_db,
        expected_owner_head=args.owner_head,create=args.create)
    if args.action=='prepare':
        result=owner.prepare(limit=args.limit,context_radius=args.radius)
    elif args.action=='submit':
        result=owner.submit(json.loads(args.packet.read_text()),
                            json.loads(args.answer.read_text()))
    elif args.action=='status':
        result=owner.status()
    else:
        _,s=engine.compile_native_v6_stage(qualifier_provenance=owner)
        result=s
    dest=getattr(args,'out',None)
    if dest is not None:
        if dest.exists() or dest.is_symlink():
            raise SystemExit('REFUSE_OVERWRITE_EXISTING_PRIVATE_OUTPUT')
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2))
        dest.chmod(0o600)
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()