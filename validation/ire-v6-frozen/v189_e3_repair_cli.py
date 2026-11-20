"""V189 owner-private E3 repair/parent audit CLI. Never writes E4 or V6 approvals.

Usage:
 python v189_e3_repair_cli.py --source owner_original.srt --owner-db full_research_journal.sqlite \
   --second-db e3_second_pass.sqlite --adj-db e3_adjudication.sqlite \
   --repair-db e3_v189_omission_overlay.sqlite --owner-head <pinned64> status
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v184_e3_adjudication import E3Adjudication
from v189_e3_omission_repair_overlay import E3OmissionOverlay
from v189_e3_parent_alignment_screen import generate_packet,validate_live

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('source','owner-db','second-db','adj-db','repair-db','owner-head'):
        parser.add_argument('--'+flag,required=True)
    parser.add_argument('--video-id',default='LVE7XN_esTc')
    parser.add_argument('--window-size',type=int,default=125)
    parser.add_argument('--expected-windows',type=int,default=2)
    parser.add_argument('--create',action='store_true')
    parser.add_argument('--out',help='Output private JSON path; omitted means stdout')
    parser.add_argument('--packet',help='Pre-issued private challenge JSON')
    parser.add_argument('--answer',help='ChatGPT-reviewed private response JSON')
    parser.add_argument('--limit',type=int,default=12)
    parser.add_argument('action',choices=('status','prepare','submit','parent-packet','parent-validate'))
    x=parser.parse_args()
    raw=Path(x.source).read_bytes()
    engine=EngineChatSession(Path(x.owner_db),raw,x.video_id,
                             owner_source_sha256=sha256(raw),window_size=x.window_size,
                             expected_window_count=x.expected_windows)
    second=E3TwoTurnAudit(engine,Path(x.second_db),expected_owner_head=x.owner_head)
    adj=E3Adjudication(second,Path(x.adj_db))
    if x.action in ('parent-packet','parent-validate'):
        if x.action=='parent-packet': output=generate_packet(adj)
        else:
            if not x.packet or not x.answer:parser.error('parent-validate needs --packet and --answer')
            output=validate_live(adj,json.loads(Path(x.packet).read_text()),
                                    json.loads(Path(x.answer).read_text()))
    else:
        ledger=E3OmissionOverlay(adj,Path(x.repair_db),create=x.create)
        if x.action=='status':output=ledger.status()
        elif x.action=='prepare':output=ledger.prepare(limit=x.limit)
        else:
            if not x.packet or not x.answer:parser.error('submit needs --packet and --answer')
            output=ledger.submit(json.loads(Path(x.packet).read_text()),
                                 json.loads(Path(x.answer).read_text()))
    content=json.dumps(output,ensure_ascii=False,indent=2)
    if x.out:
        p=Path(x.out);p.write_text(content+'\n',encoding='utf-8');p.chmod(0o600)
    else:print(content)
if __name__=='__main__':main()