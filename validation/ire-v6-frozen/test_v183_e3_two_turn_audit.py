"""V183 synthetic E3 second-pass quality guards; NOT an independent gold set."""
import copy
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, ZERO, _digest
from v183_e3_two_turn_audit import E3TwoTurnAudit, ANSWER_SCHEMA


def data():
    captions=["ETF는 손실을 볼 수 있습니다.","상품마다 다르게 설명됩니다.",
              "이것은 질문인가요?","현금이 더 나을까요?","감사합니다."]
    return ("\n\n".join(f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},700\n{s}"
                      for i,s in enumerate(captions,1))).encode()


def claim():
    return {"proposition":"ETF는 손실을 볼 수 있다고 설명한다.","kind":"FACT",
            "quote":"ETF는 손실을 볼 수 있습니다.","context_cue_indices":[1],
            "conditions":["특정 투자 조건에 따라서"],"exceptions":["손실 회피 보장 없음"],
            "numeric_tokens":[],"high_risk":True,"needs_official_source":True}


def row(cue,disp,claims=None):
    return {"cue_index":cue['cue_index'],"source_text_sha256":cue['source_text_sha256'],
            "disposition":disp,"analysis":"원문과 전후 자막을 확인하고 단독 명제 여부를 보수적으로 재판정했습니다.",
            "speaker_role":"HOST","claims":claims or [],"limitations_checked":True}


class TestE3TwoTurn(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw=data()
        self.orig=Path(self.tmp.name)/'owner.sqlite'
        self.blind=Path(self.tmp.name)/'e3.sqlite'
        self.engine=EngineChatSession(self.orig,self.raw,'AbCdEf12345',
                 owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)
        for limit in (3,2):
            p=self.engine.prepare(source_first_only=True,limit=limit)
            responses=[]
            for t in p['target_cues']:
                idx=t['cue_index']
                disp='ASSERTION' if idx==1 else 'QUESTION' if idx==3 else 'OPEN' if idx==4 else 'NON_RESEARCH'
                responses.append(row(t,disp,[claim()] if idx==1 else []))
            self.engine.submit(p,{"schema":COMMIT,"challenge_sha256":p['challenge_sha256'],
                                  "review_executor":"CHATGPT_IN_CHAT","responses":responses})
        self.first_head=self.engine.progress()['checkpoint_head_sha256']
        self.audit=E3TwoTurnAudit(self.engine,self.blind,expected_owner_head=self.first_head,create=True)

    def answer(self, packet, overrides=None):
        default={1:('ASSERTION',[claim()]),2:('NON_RESEARCH',[]),
                 3:('QUESTION',[]),4:('OPEN',[]),5:('NON_RESEARCH',[])}
        default.update(overrides or {})
        return {"schema":ANSWER_SCHEMA,"challenge_sha256":packet['challenge_sha256'],
                "review_executor":"CHATGPT_IN_CHAT",
                "responses":[row(t,*default[t['cue_index']]) for t in packet['target_cues']]}

    def test_01_second_turn_packet_has_no_first_turn_labels_or_claims(self):
        p=self.audit.prepare(limit=3)
        self.assertEqual(p['cue_indices'],[1,2,3])
        self.assertEqual(p['selection_mode'],'SEQUENTIAL_CENSUS')
        self.assertFalse(p['first_pass_decisions_in_packet'])
        self.assertFalse(p['independent_chat_identity_proven'])
        self.assertTrue(all(set(x)=={'cue_index','text','source_text_sha256'} for x in p['target_cues']+p['surrounding_context']))
        self.assertNotIn('original_claims',json.dumps(p))
        self.assertNotIn('prior_analysis',json.dumps(p))

    def test_02_resume_second_turn_separate_engine_object_and_audit(self):
        p=self.audit.prepare(limit=3)
        receipt=self.audit.submit(p,self.answer(p))
        self.assertEqual(receipt['reviewed'],3)
        self.assertTrue(receipt['e4_approved'] is False)
        new_engine=EngineChatSession(self.orig,self.raw,'AbCdEf12345',
                 owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)
        reopened=E3TwoTurnAudit(new_engine,self.blind,expected_owner_head=self.first_head)
        q=reopened.prepare(limit=3)
        self.assertEqual(q['cue_indices'],[4,5])
        reopened.submit(q,self.answer(q))
        status=reopened.status()
        self.assertEqual(status['second_reviewed_cues'],5)
        self.assertEqual(status['unreviewed_cues'],0)
        self.assertEqual(status['adjudication_required_count'],1) # still OPEN
        self.assertFalse(status['e3_quality_certified'])
        self.assertFalse(status['e4_approved'])
        self.assertEqual(reopened.prepare()['type'],'E3_SECOND_PASS_SOURCE_CENSUS_COMPLETE_UNAPPROVED')

    def test_03_semantic_conflict_never_auto_approved(self):
        p=self.audit.prepare(cue_indices=[1,2],limit=2)
        answer=self.answer(p,{1:('NON_RESEARCH',[]),2:('NON_RESEARCH',[])})
        result=self.audit.submit(p,answer)
        self.assertEqual(result['disagreement_or_open_cues'],[1])
        reasons=result['comparison_items'][0]['difference_codes']
        self.assertIn('DISPOSITION',reasons)
        self.assertIn('ATOMIC_CLAIM_COUNT',reasons)
        status=self.audit.status()
        self.assertEqual(status['adjudication_required_count'],1)
        self.assertFalse(status['e3_quality_certified'])

    def test_04_qualifier_differences_are_flagged(self):
        p=self.audit.prepare(cue_indices=[1],limit=1)
        alternative=claim()
        alternative['conditions']=['다른 상황']
        result=self.audit.submit(p,self.answer(p,{1:('ASSERTION',[alternative])}))
        self.assertEqual(result['disagreement_or_open_cues'],[1])
        self.assertIn('CLAIM_CONDITIONS',result['comparison_items'][0]['difference_codes'])

    def test_05_quote_numeric_forgery_rejected_without_mutation(self):
        p=self.audit.prepare(cue_indices=[1],limit=1)
        invalid=claim()
        invalid['quote']='원본에 존재하지 않는 대목'
        with self.assertRaisesRegex(InvalidInput,'UNGROUNDED_CLAIM'):
            self.audit.submit(p,self.answer(p,{1:('ASSERTION',[invalid])}))
        invalid=claim()
        invalid['proposition']='ETF의 수익률이 300%라고 확정할 수 있다.'
        with self.assertRaisesRegex(InvalidInput,'UNGROUNDED_CLAIM'):
            self.audit.submit(p,self.answer(p,{1:('ASSERTION',[invalid])}))
        self.assertEqual(self.audit.status()['second_reviewed_cues'],0)

    def test_06_forged_source_only_packet_self_hash_rejected(self):
        p=self.audit.prepare(limit=3)
        fake=copy.deepcopy(p)
        fake['surrounding_context'][0]['text']='ETF는 무조건 안전합니다.'
        fake['challenge_sha256']=_digest({k:v for k,v in fake.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'PACKET_NOT_ISSUED'):
            self.audit.submit(fake,self.answer(fake))
        self.assertEqual(self.audit.status()['second_reviewed_cues'],0)

    def test_07_duplicate_stale_packet_rejected(self):
        p=self.audit.prepare(limit=3)
        self.audit.submit(p,self.answer(p))
        with self.assertRaisesRegex(InvalidInput,'PACKET_NOT_ISSUED'):
            self.audit.submit(p,self.answer(p))
        self.assertEqual(self.audit.status()['second_reviewed_cues'],3)

    def test_08_original_head_pin_refuses_wrong_source_or_old_checkpoint(self):
        with self.assertRaisesRegex(InvalidInput,'OWNER_ORIGINAL_JOURNAL_CHANGED'):
            E3TwoTurnAudit(self.engine,self.blind,expected_owner_head=ZERO)
        with self.assertRaisesRegex(InvalidInput,'FIRST_TURN_PIN_CHANGED'):
            # editing only the stored configuration should be rejected on open
            with sqlite3.connect(self.blind) as db:
                db.execute('UPDATE config SET value=? WHERE id=1',(json.dumps({'bad':True}),))
            E3TwoTurnAudit(self.engine,self.blind,expected_owner_head=self.first_head)

    def test_09_sqlite_altered_decision_detected(self):
        p=self.audit.prepare(limit=3)
        self.audit.submit(p,self.answer(p))
        with sqlite3.connect(self.blind) as db:
            db.execute("UPDATE judgments SET record='{}' WHERE cue_index=1")
        with self.assertRaisesRegex(InvalidInput,'SECOND_PASS_ROW_TAMPER'):
            self.audit.status()

    def test_10_no_audit_database_auto_reset_and_private_permissions(self):
        with self.assertRaisesRegex(InvalidInput,'NO_AUDIT_DB_AUTO_RESET'):
            E3TwoTurnAudit(self.engine,Path(self.tmp.name)/'absent.sqlite',
                           expected_owner_head=self.first_head)
        os.chmod(self.blind,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_PERMISSIONS'):
            E3TwoTurnAudit(self.engine,self.blind,expected_owner_head=self.first_head)

    def test_11_targeted_sample_not_pretended_representative(self):
        p=self.audit.prepare(cue_indices=[1,5],limit=2)
        self.assertEqual(p['selection_mode'],'TARGETED_NONREPRESENTATIVE')
        self.audit.submit(p,self.answer(p))
        self.assertEqual(self.audit.status()['unreviewed_cues'],3)
        q=self.audit.prepare(limit=3)
        self.assertEqual(q['cue_indices'],[2,3])
        self.assertFalse(self.audit.status()['selection_is_independent_gold'])

    def test_12_e3_audit_does_not_mutate_original_v176(self):
        head=self.first_head
        p=self.audit.prepare(limit=3)
        self.audit.submit(p,self.answer(p,{1:('NON_RESEARCH',[])}))
        self.assertEqual(self.engine.progress()['checkpoint_head_sha256'],head)
        with sqlite3.connect(self.orig) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],2)
        self.assertEqual(self.engine.compile_native_v6_stage()[1]['semantic_projection_gate']['unprojected_claims'],1)

if __name__=='__main__':
    unittest.main()