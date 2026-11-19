"""V187 private source-scope bridge CLI; no model API, no automatic approvals."""
import argparse
import json
import os
from pathlib import Path

from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v186_e3_qualifier_provenance import E3QualifierProvenance
from v187_e3_parent_scope_bridge import E3ParentScopeBridge


def _write_new_private_file(path, item):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(item,f,ensure_ascii=False,indent=2)


def main():
    p=argparse.ArgumentParser(description='Owner-only E3 cross-cue parent scope proof')
    p.add_argument('--source',required=True)
    p.add_argument('--owner-db',required=True)
    p.add_argument('--qualifier-db',required=True)
    p.add_argument('--scope-db',required=True)
    p.add_argument('--video-id',required=True)
    p.add_argument('--source-sha256',required=True)
    p.add_argument('--owner-head',required=True)
    p.add_argument('--qualifier-head',required=True)
    p.add_argument('--window-size',type=int,default=125)
    p.add_argument('--expected-windows',type=int,default=2)
    cmd=p.add_subparsers(dest='command',required=True)
    cmd.add_parser('init')
    cmd.add_parser('status')
    cmd.add_parser('stage')
    prepare=cmd.add_parser('prepare')
    prepare.add_argument('--term-id',action='append',required=True)
    prepare.add_argument('--parent-cue',type=int,required=True)
    prepare.add_argument('--bridge-cue',type=int,required=True)
    prepare.add_argument('--out',required=True)
    submit=cmd.add_parser('submit')
    submit.add_argument('--packet',required=True)
    submit.add_argument('--answer',required=True)
    opts=p.parse_args()
    raw=Path(opts.source).read_bytes()
    if sha256(raw)!=opts.source_sha256:
        raise SystemExit('SOURCE_SHA_MISMATCH_CLOSED')
    engine=EngineChatSession(opts.owner_db,raw,opts.video_id,
        owner_source_sha256=opts.source_sha256,
        window_size=opts.window_size,expected_window_count=opts.expected_windows)
    qualifier=E3QualifierProvenance(engine,opts.qualifier_db,
        expected_owner_head=opts.owner_head)
    bridge=E3ParentScopeBridge(engine,qualifier,opts.scope_db,
        expected_owner_head=opts.owner_head,
        expected_qualifier_head=opts.qualifier_head,create=opts.command=='init')
    if opts.command in ('init','status'):
        result=bridge.status()
    elif opts.command=='stage':
        _,summary=engine.compile_native_v6_stage(
            qualifier_provenance=qualifier,cross_cue_scope_bridge=bridge)
        result={'original_source_sha256':summary['source_sha256'],
                'native_v6_audit':summary['native_v6_audit'],
                'semantic_projection_gate':summary['semantic_projection_gate'],
                'e3_certified':False,'e4_approved':False,'e5_published':False}
    elif opts.command=='prepare':
        packet=bridge.prepare(term_ids=opts.term_id,
            parent_cue_index=opts.parent_cue,bridging_cue_index=opts.bridge_cue)
        _write_new_private_file(opts.out,packet)
        result={'private_source_packet_path':opts.out,
                'term_count':len(packet['term_ids']),
                'challenge_sha256':packet['challenge_sha256'],
                'e3_certified':False,'e4_approved':False,'e5_published':False}
    elif opts.command=='submit':
        packet=json.loads(Path(opts.packet).read_text())
        answer=json.loads(Path(opts.answer).read_text())
        result=bridge.submit(packet,answer)
    else:
        raise RuntimeError('UNSUPPORTED_ACTION')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()