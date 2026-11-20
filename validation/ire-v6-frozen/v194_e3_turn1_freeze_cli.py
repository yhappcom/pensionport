"""Private operator CLI for 1-turn source freezing and next-turn verification."""
import argparse,json,sys
from pathlib import Path
from ire.v6.codec import sha256
from v194_e3_turn1_freeze import freeze,restore_verify

def main(argv=None):
 p=argparse.ArgumentParser(description='V194 first user turn research freeze only. No final E3 approval.')
 sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('freeze');a.add_argument('--original',required=True);a.add_argument('--research',required=True)
 a.add_argument('--owner-db',required=True);a.add_argument('--private-zip',required=True)
 a.add_argument('--video-id',required=True);a.add_argument('--manual-first-user-ref',required=True)
 a.add_argument('--manual-first-user-text-sha',required=True)
 b=sub.add_parser('verify');b.add_argument('--private-zip',required=True);b.add_argument('--archive-sha',required=True)
 b.add_argument('--manifest-sha',required=True);b.add_argument('--source-sha',required=True);b.add_argument('--owner-head',required=True)
 args=p.parse_args(argv)
 if args.command=='freeze':
  r=freeze(original=Path(args.original).read_bytes(),research=json.loads(Path(args.research).read_text()),
      sqlite_path=Path(args.owner_db),archive_path=Path(args.private_zip),
      manual_first_user_ref=args.manual_first_user_ref,
      manual_first_user_message_sha256=args.manual_first_user_text_sha,video_id=args.video_id)
 else:r=restore_verify(archive_path=Path(args.private_zip),expected_archive_sha256=args.archive_sha,
    expected_manifest_sha256=args.manifest_sha,expected_source_sha256=args.source_sha,
    expected_owner_head_sha256=args.owner_head)
 print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__':main()