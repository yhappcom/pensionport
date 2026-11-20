"""V189 synthetic adversarial tests; do NOT represent owner financial gold."""
import copy,os,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import _digest
import test_v184_e3_adjudication as v184fixture
from v189_e3_omission_repair_overlay import E3OmissionOverlay,ANSWER_SCHEMA

class TestOmissionOverlay(unittest.TestCase):
    def setUp(self):
        self.base=v184fixture.TestAdjudication('test_packet_has_first_and_second_with_original_context')
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        # Finish the 4th synthetic second-pass cue so the V189 census gate is strict.
        q=self.base.audit.prepare(limit=1)
        self.base.audit.submit(q,{'schema':v184fixture.SECOND_ANSWER,
            'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT',
            'responses':[{'cue_index':4,
               'source_text_sha256':q['target_cues'][0]['source_text_sha256'],
               'disposition':'NON_RESEARCH','speaker_role':'HOST','claims':[],
               'analysis':'원문에 투자 주장 없이 마무리되므로 새 원자는 보존하지 않습니다.',
               'limitations_checked':True}]})
        p=self.base.reviewer.prepare(limit=1)
        self.base.reviewer.submit(p,self.base.response(p))
        self.path=Path(self.base.tmp.name)/'repair.sqlite'
        self.ledger=E3OmissionOverlay(self.base.reviewer,self.path,create=True)
    def answer(self,p,resolution='PROVISIONAL_NEW_CLAIM'):
        target=p['targets'][0]
        r=target['first_nearby_claims'][0]
        reference={k:r[k] for k in ('pass','cue_index','ordinal','claim_sha256')}
        return {'schema':ANSWER_SCHEMA,'challenge_sha256':p['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT','answers':[{
                   'cue_index':1,'original_category':target['original_category'],
                   'resolution':resolution,'reviewed_source_quote':'ETF는 장점이 있습니다.',
                   'source_quote_cue_index':1,'source_context_cue_indices':[1,2],
                   'other_pass_claim_ref':reference if resolution=='PROVISIONAL_NEW_CLAIM' else None,
                   'covered_pass_claim_ref':None,
                   'semantic_rationale':'첫 검토의 원문 주장과 후속 검토의 누락 가능성을 비교하여, 누락된 원자를 원본 해시로만 임시 연결하되 어떠한 실물 금융사실도 승인하지 않습니다. 원본의 화자 의견을 별도 보존하고 대체 주장으로 자동 승격하지 않습니다.',
                   'claim_truth_certified':False,'independent_gold_certified':False,
                   'e3_certified':False,'v123_approved':False,'e4_approved':False,
                   'e5_published':False}]}
    def test_01_source_only_candidate_not_native_rewrite(self):
        orig=self.base.eng.progress()['checkpoint_head_sha256']
        p=self.ledger.prepare()
        self.ledger.submit(p,self.answer(p))
        status=self.ledger.status()
        self.assertEqual((status['reviewed'],status['provisional_additions']),(1,1))
        self.assertFalse(status['e3_quality_certified'])
        self.assertEqual(self.base.eng.progress()['checkpoint_head_sha256'],orig)
    def test_02_resume_replays_exact_hash(self):
        p=self.ledger.prepare();self.ledger.submit(p,self.answer(p))
        resumed=E3OmissionOverlay(self.base.reviewer,self.path)
        self.assertEqual(self.ledger.status()['overlay_head'],resumed.status()['overlay_head'])
    def test_03_forged_packet_self_hash_rejected(self):
        p=self.ledger.prepare()
        x=copy.deepcopy(p);x['source_context'][0]['text']='마법의 안전한 ETF입니다.'
        x['challenge_sha256']=_digest({k:v for k,v in x.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_PACKET'):
            self.ledger.submit(x,self.answer(x))
    def test_04_source_quote_forgery_rejected(self):
        p=self.ledger.prepare();a=self.answer(p)
        a['answers'][0]['reviewed_source_quote']='100% 원금보장'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_QUOTE_OR_CONTEXT_NOT_PINN'):
            self.ledger.submit(p,a)
    def test_05_claim_reference_forgery_rejected(self):
        p=self.ledger.prepare();a=self.answer(p)
        a['answers'][0]['other_pass_claim_ref']['claim_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'CLAIM_REFERENCE_SOURCE_MISMATCH'):
            self.ledger.submit(p,a)
    def test_06_wrong_pass_reference_rejected(self):
        p=self.ledger.prepare();a=self.answer(p)
        a['answers'][0]['other_pass_claim_ref']['pass']='SECOND'
        with self.assertRaisesRegex(InvalidInput,'CLAIM_REFERENCE_SOURCE_MISMATCH'):
            self.ledger.submit(p,a)
    def test_07_approval_forgery_rejected(self):
        p=self.ledger.prepare();a=self.answer(p)
        a['answers'][0]['e3_certified']=True
        with self.assertRaisesRegex(InvalidInput,'ANSWER_TARGET_OR_AUTHORITY'):
            self.ledger.submit(p,a)
    def test_08_stale_duplicate_submit_rejected(self):
        p=self.ledger.prepare();a=self.answer(p);self.ledger.submit(p,a)
        with self.assertRaisesRegex(InvalidInput,'TARGET_SELECTION_INVALID|STALE_OR_FORGED_PACKET'):
            self.ledger.submit(p,a)
    def test_09_stored_row_tamper_detected(self):
        p=self.ledger.prepare();self.ledger.submit(p,self.answer(p))
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE judgments SET record='{}'")
        with self.assertRaisesRegex(InvalidInput,'JUDGMENT_RECORD_TAMPER'):
            self.ledger.status()
    def test_10_private_database_required(self):
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_DB_PERMISSIONS'):
            E3OmissionOverlay(self.base.reviewer,self.path,create=False)
    def test_11_unresolved_cannot_emit_patch(self):
        p=self.ledger.prepare();a=self.answer(p,resolution='CLAIM_BOUNDARY_OR_SCOPE_UNRESOLVED')
        self.ledger.submit(p,a)
        self.assertEqual(self.ledger.status()['provisional_additions'],0)
        self.assertFalse(self.ledger.status()['e4_approved'])

if __name__=='__main__':unittest.main()