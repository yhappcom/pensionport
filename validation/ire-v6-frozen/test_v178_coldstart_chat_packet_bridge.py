"""Synthetic-only native V176 cold-start interface contract; no real LLM invocation."""
import copy, hashlib, tempfile, unittest
from pathlib import Path
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, ZERO
from v178_coldstart_chat_packet_bridge import import_chat_packet, SCHEMA
from test_v176_chat_engine_loop import fixture, respond

class TestV178NativeChatPacketColdStart(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'owner_private.sqlite'
        self.raw=fixture();self.sha=hashlib.sha256(self.raw).hexdigest()
        self.video='AbCdEf12345'
        self.native=EngineChatSession
        # Create reviewer rows with actual V176 challenge shape. Only tests use
        # fixture callback; real packet rows come from active ChatGPT review.
        source=EngineChatSession(Path(self.tmp.name)/'synthetic_source.sqlite',
                 self.raw,self.video,owner_source_sha256=self.sha,window_size=3)
        q=source.prepare(limit=3,source_first_only=True)
        self.a=respond(q)
        source.submit(q,self.a)
        q2=source.prepare(limit=2,source_first_only=True)
        self.b=respond(q2)
    def packet(self,rows,start):
        return {'schema':SCHEMA,'owner_source_sha256':self.sha,
                'first_cue':start,'last_cue':start+len(rows)-1,
                'chat_authored_review_source':'ACTIVE_CONVERSATION_NONCRYPTO',
                'original_journal_head_sha256':'0'*64,
                'supplied_prior_research':False,'native_approval':False,
                'rows':copy.deepcopy(rows)}
    def runit(self,packet,*,head=ZERO,count=0,create=False,raw=None,db=None):
        return import_chat_packet(db or self.db,self.raw if raw is None else raw,
                 self.video,packet,original_sha256=self.sha,
                 expected_head=head,expected_cues_reviewed=count,
                 allow_new_session=create,window_size=3)
    def test_01_true_native_initial_chat_rows(self):
        r=self.runit(self.packet(self.a['responses'],1),create=True)
        self.assertEqual(r['last_cue_committed'],3)
        self.assertEqual(r['remaining_original_cues'],2)
        self.assertFalse(r['e4_approved'])
        self.assertFalse(r['prior_research_imported'])
    def test_02_native_two_turn_resume_same_source(self):
        first=self.runit(self.packet(self.a['responses'],1),create=True)
        second=self.runit(self.packet(self.b['responses'],4),
                 head=first['native_checkpoint_head_sha256'],count=3)
        self.assertEqual(second['last_cue_committed'],5)
        self.assertEqual(second['remaining_original_cues'],0)
        self.assertFalse(second['e5_released'])
    def test_03_no_db_resumption_cannot_reset(self):
        with self.assertRaisesRegex(InvalidInput,'MISSING_EXISTING_SESSION'):
            self.runit(self.packet(self.a['responses'],1))
        self.assertFalse(self.db.exists())
    def test_04_forged_source_bytes_cannot_start(self):
        with self.assertRaisesRegex(InvalidInput,'RAW_SOURCE_SHA_MISMATCH'):
            self.runit(self.packet(self.a['responses'],1),create=True,raw=self.raw+b'bad')
    def test_05_packet_gap_cannot_start(self):
        p=self.packet(self.a['responses'],1)
        p['rows'][1]['cue_index']=9
        with self.assertRaisesRegex(InvalidInput,'EXACT_CONTIGUOUS_PACKET_CENSUS'):
            self.runit(p,create=True)
    def test_06_fake_native_approval_cannot_start(self):
        p=self.packet(self.a['responses'],1);p['native_approval']=True
        with self.assertRaisesRegex(InvalidInput,'SOURCE_ONLY_AND_NO_APPROVAL'):
            self.runit(p,create=True)
    def test_07_prior_research_flag_cannot_start(self):
        p=self.packet(self.a['responses'],1);p['supplied_prior_research']=True
        with self.assertRaisesRegex(InvalidInput,'SOURCE_ONLY_AND_NO_APPROVAL'):
            self.runit(p,create=True)
    def test_08_forged_original_quote_rejected_by_native(self):
        p=self.packet(self.a['responses'],1)
        p['rows'][1]['disposition']='ASSERTION'
        p['rows'][1]['claims']=[{'proposition':'금액이 갑자기 몇 배 오른다.','kind':'FACT',
            'quote':'없는 가짜 인용','context_cue_indices':[2],
            'conditions':[],'exceptions':[],'numeric_tokens':[],
            'high_risk':True,'needs_official_source':True}]
        with self.assertRaisesRegex(InvalidInput,'ATOM_NOT_GROUNDED_IN_ORIGINAL'):
            self.runit(p,create=True)
        self.assertEqual(EngineChatSession(self.db,self.raw,self.video,
                        owner_source_sha256=self.sha,window_size=3).progress()['cue_reviewed'],0)
    def test_09_wrong_resume_head_blocks_without_writing(self):
        f=self.runit(self.packet(self.a['responses'],1),create=True)
        with self.assertRaisesRegex(InvalidInput,'PREVIOUS_TURN_HEAD_OR_COUNT_MISMATCH'):
            self.runit(self.packet(self.b['responses'],4),head='1'*64,count=3)
        self.assertEqual(EngineChatSession(self.db,self.raw,self.video,
                        owner_source_sha256=self.sha,window_size=3).progress()['cue_reviewed'],3)
    def test_10_original_source_syntax_is_native_audited(self):
        p=self.packet(self.a['responses'],1)
        with self.assertRaises(Exception):
            self.runit(p,raw=b'\xff'*len(self.raw),create=True)
    def test_11_packet_has_no_source_approval_shortcut(self):
        p=self.packet(self.a['responses'],1)
        p['rows'][0]['financial_fact_certified']=True
        with self.assertRaisesRegex(InvalidInput,'EXACT_CONTIGUOUS_PACKET_CENSUS'):
            self.runit(p,create=True)

if __name__=='__main__':unittest.main()