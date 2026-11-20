"""V194 synthetic security / two-user-command phase regressions only. Not financial gold."""
import copy,hashlib,io,json,os,tempfile,unittest,zipfile
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession,COMMIT
from v194_e3_turn1_freeze import freeze,restore_verify,check_native_research

RAW=(b'1\n00:00:01,000 --> 00:00:02,000\nHello.\n\n'
     b'2\n00:00:03,000 --> 00:00:04,000\nCMA is a cash management account.\n\n'
     b'3\n00:00:05,000 --> 00:00:06,000\nIt may lose value.\n\n'
     b'4\n00:00:07,000 --> 00:00:08,000\nThank you.\n')
VIDEO='cmaSynt0001'
SHA=sha256(RAW)
MSG_SHA=sha256('진행해 주세요'.encode())

class TestActualFirstUserCommandFreeze(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name);self.db=self.d/'owner.sqlite';self.z=self.d/'private.zip'
        eng=EngineChatSession(self.db,RAW,VIDEO,owner_source_sha256=SHA,window_size=120)
        pkt=eng.prepare(limit=4,source_first_only=True)
        x=[]
        for cue in pkt['target_cues']:
            i=cue['cue_index'];is_claim=i==2
            claim={'proposition':'CMA stands for a cash management account.',
                  'kind':'FACT','quote':cue['text'] if 'text' in cue else 'CMA is a cash management account.',
                  'context_cue_indices':[2], 'conditions':[], 'exceptions':[],
                  'numeric_tokens':[],'high_risk':False,'needs_official_source':True}
            x.append({'cue_index':i,'source_text_sha256':cue['source_text_sha256'],
                      'disposition':'ASSERTION' if is_claim else 'NON_RESEARCH',
                      'analysis':'The caption was assessed for source-grounded meaning and is pending final review.',
                      'speaker_role':'HOST','claims':[claim] if is_claim else [],
                      'limitations_checked':True})
        eng.submit(pkt,{'schema':COMMIT,'challenge_sha256':pkt['challenge_sha256'],
                        'review_executor':'CHATGPT_IN_CHAT','responses':x})
        self.eng=eng;self.status=eng.progress()
        self.study={'schema':'IRE_V194_CHATGPT_RESEARCH_FIRST_TURN_PRIVATE_V1',
                    'video_id':VIDEO,'research_phase':'RESEARCH_AND_FREEZE',
                    'source_sha256':SHA,'cue_count':4,'claim_count':1,
                    'e3_final_review_run':False,'host_verified_two_turns':False,
                    'e3_final_approved':False,'v123_e4_invoked':False,
                    'e5_knowledge_published':False,'quality_precision':None,
                    'quality_recall':None,'official_claim_verified_count':0,
                    'frozen_v176_head':self.status['checkpoint_head_sha256'],
                    'parents':[{'parent_id':'P001','start_cue':1,'end_cue':4,
                      'semantic_parent':'An introduction to a CMA cash account',
                      'claim_cues':[2],'no_claim_cues':[1,3,4],
                      'parent_completeness_status':'FIRST_TURN_PROVISIONAL'}],
                    'claims':[{'cue_index':2,'proposition':'CMA stands for a cash management account.',
                      'kind':'FACT','quote':'CMA is a cash management account.',
                      'evidence_cues':[2],'speaker':'HOST','high_risk':False,
                      'needs_official_source':True,'financial_fact_verified':False,
                      'e3_semantic_approved':False}],
                    'unresolved_cue_issues':[{'cue_index':3,'task':'Check original issuer information before use.'}],
                    'official_sources_preliminary':[]}

    def frozen(self):
        return freeze(original=RAW,research=self.study,sqlite_path=self.db,
                      archive_path=self.z,manual_first_user_ref='user:example_first_command_unverified',
                      manual_first_user_message_sha256=MSG_SHA,video_id=VIDEO)
    def restore(self,r):
        return restore_verify(archive_path=self.z,expected_archive_sha256=r['archive_sha256'],
                              expected_manifest_sha256=r['manifest_sha256'],
                              expected_source_sha256=SHA,
                              expected_owner_head_sha256=r['owner_head_sha256'])
    def test_01_real_native_pinned_synthetic(self):
        x=check_native_research(RAW,self.study,self.db,video_id=VIDEO)
        self.assertEqual((x['cue_count'],x['parent_count'],x['claim_count']),(4,1,1))
    def test_02_first_turn_freeze_does_not_auto_e3(self):
        r=self.frozen();self.assertEqual(r['phase'],'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND')
        self.assertFalse(r['e3_final_review']);self.assertFalse(r['platform_turn_identity_verified'])
    def test_03_fresh_second_process_restore_without_second_user_turn(self):
        r=self.frozen();s=self.restore(r)
        self.assertEqual(s['zip_members_verified'],5)
        self.assertFalse(s['turn2_review_performed']);self.assertFalse(s['e3_approved'])
    def test_04_changed_user_message_id_does_not_authenticate(self):
        r=self.frozen();self.assertFalse(r['platform_turn_identity_verified'])
    def test_05_missing_owner_journal_is_not_recreated(self):
        self.db.unlink()
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_SOURCE_DB_REQUIRED'):
            self.frozen()
    def test_06_owner_journal_wrong_permissions(self):
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_SOURCE_DB_REQUIRED'):
            self.frozen()
    def test_07_reject_claim_not_in_original(self):
        self.study['claims'][0]['quote']='CMA guarantees capital.'
        with self.assertRaisesRegex(InvalidInput,'CLAIM_NOT_NATIVE_PINNED'):
            self.frozen()
    def test_08_reject_parent_cue_gap(self):
        self.study['parents'][0]['no_claim_cues']=[1,4]
        with self.assertRaisesRegex(InvalidInput,'PARENT_CUE_CENSUS'):
            self.frozen()
    def test_09_reject_fake_final_review(self):
        self.study['e3_final_review_run']=True
        with self.assertRaisesRegex(InvalidInput,'NO_FINANCE_OR_E3_APPROVAL'):
            self.frozen()
    def test_10_reject_fake_independent_precision(self):
        self.study['quality_precision']=0.99
        with self.assertRaisesRegex(InvalidInput,'NO_FINANCE_OR_E3_APPROVAL'):
            self.frozen()
    def test_11_reject_fake_official_finance_certification(self):
        self.study['official_claim_verified_count']=1
        with self.assertRaisesRegex(InvalidInput,'NO_FINANCE_OR_E3_APPROVAL'):
            self.frozen()
    def test_12_no_checkpoint_overwrite(self):
        self.frozen()
        with self.assertRaisesRegex(InvalidInput,'NO_OVERWRITE'):
            self.frozen()
    def test_13_reject_wrong_external_archive_sha(self):
        r=self.frozen()
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_HASH_MISMATCH'):
            restore_verify(archive_path=self.z,expected_archive_sha256='0'*64,
                           expected_manifest_sha256=r['manifest_sha256'],
                           expected_source_sha256=SHA,expected_owner_head_sha256=r['owner_head_sha256'])
    def test_14_reject_wrong_source_pin(self):
        r=self.frozen()
        with self.assertRaisesRegex(InvalidInput,'FROZEN_PHASE_OR_APPROVAL_FORGERY'):
            restore_verify(archive_path=self.z,expected_archive_sha256=r['archive_sha256'],
                           expected_manifest_sha256=r['manifest_sha256'],
                           expected_source_sha256='0'*64,expected_owner_head_sha256=r['owner_head_sha256'])
    def test_15_reject_corrupt_archive_even_with_matching_manifest_pin(self):
        r=self.frozen()
        with zipfile.ZipFile(self.z) as z:content={n:z.read(n) for n in z.namelist()}
        content['cma_first_research.json']+=b'\n'
        with zipfile.ZipFile(self.z,'w') as z:
            for name,blob in content.items():z.writestr(name,blob)
        with self.assertRaisesRegex(InvalidInput,'FILE_HASH_MISMATCH'):
            restore_verify(archive_path=self.z,expected_archive_sha256=sha256(self.z.read_bytes()),
                           expected_manifest_sha256=r['manifest_sha256'],
                           expected_source_sha256=SHA,expected_owner_head_sha256=r['owner_head_sha256'])
    def test_16_reject_same_user_ref_bad_prefix(self):
        with self.assertRaisesRegex(InvalidInput,'FIRST_USER_MESSAGE_EVIDENCE_MISSING'):
            freeze(original=RAW,research=self.study,sqlite_path=self.db,
                   archive_path=self.z,manual_first_user_ref='python:process2',
                   manual_first_user_message_sha256=MSG_SHA,video_id=VIDEO)

if __name__=='__main__':unittest.main()