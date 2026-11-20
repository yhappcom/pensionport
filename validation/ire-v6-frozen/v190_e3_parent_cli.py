"""V190 owner-private parent semantic review / 6 atom-repair manifest CLI.

Example (private files only):
python v190_e3_parent_cli.py --source owner_original.srt \
  --owner-db full_research_journal.sqlite --second-db e3_second_pass.sqlite \
  --adj-db e3_adjudication.sqlite --omission-db e3_v189_omission_overlay.sqlite \
  --parent-screen-packet V189_PARENT_SOURCE_SCREEN_PACKET.json \
  --parent-screen-answer V189_PARENT_SOURCE_SCREEN_ANSWER.json \
  --v190-db e3_v190_parent_graph.sqlite --owner-head <sha256> status
"""
import argparse,json
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession
from v183_e3_two_turn_audit import E3TwoTurnAudit
from v184_e3_adjudication import E3Adjudication
from v189_e3_omission_repair_overlay import E3OmissionOverlay
from v190_e3_parent_graph import E3ParentGraphReview


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','owner-db','second-db','adj-db','omission-db',
                'parent-screen-packet','parent-screen-answer','v190-db','owner-head'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--video-id',default='LVE7XN_esTc')
    p.add_argument('--window-size',type=int,default=125)
    p.add_argument('--expected-windows',type=int,default=2)
    p.add_argument('--create',action='store_true')
    p.add_argument('--packet');p.add_argument('--answer')
    p.add_argument('--limit',type=int,default=8)
    p.add_argument('--out',help='Private JSON output; standard output when omitted')
    p.add_argument('action',choices=('status','prepare','submit','provisional-candidates'))
    x=p.parse_args()
    raw=Path(x.source).read_bytes()
    engine=EngineChatSession(Path(x.owner_db),raw,x.video_id,
       owner_source_sha256=sha256(raw),window_size=x.window_size,
       expected_window_count=x.expected_windows)
    second=E3TwoTurnAudit(engine,Path(x.second_db),expected_owner_head=x.owner_head)
    adj=E3Adjudication(second,Path(x.adj_db))
    omission=E3OmissionOverlay(adj,Path(x.omission_db))
    ledger=E3ParentGraphReview(adj,omission,Path(x.v190_db),
       v189_screen_packet=json.loads(Path(x.parent_screen_packet).read_text()),
       v189_screen_answer=json.loads(Path(x.parent_screen_answer).read_text()),
       create=x.create)
    if x.action=='status':result=ledger.status()
    elif x.action=='prepare':result=ledger.prepare(limit=x.limit)
    elif x.action=='provisional-candidates':result=ledger.provisional_new_claims()
    else:
        if not x.packet or not x.answer:p.error('submit requires --packet AND --answer')
        result=ledger.submit(json.loads(Path(x.packet).read_text()),
                             json.loads(Path(x.answer).read_text()))
    s=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if x.out:
        dest=Path(x.out)
        dest.write_text(s,encoding='utf8')
        dest.chmod(0o600)
    else:print(s,end='')


if __name__=='__main__':main()