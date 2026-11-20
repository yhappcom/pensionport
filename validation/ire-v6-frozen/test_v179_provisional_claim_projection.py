"""Synthetic V179 field shape bridge, never approved finance authority."""
import copy,tempfile,unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v178_coldstart_chat_packet_bridge import import_chat_packet,SCHEMA


def sample():
    texts=['ETF도 주식시장에 거래됩니다.','주식시장 가격은 변동할 수 있습니다.']
    raw='\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i},900\n{t}'
                    for i,t in enumerate(texts,1)).encode()
    rows=[{'cue_index':i,'source_text_sha256':sha256(t.encode()),
           'disposition':'ASSERTION' if i==1 else 'NON_RESEARCH',
           'analysis':'실제 발화와 투자 사실 근거를 구분한 예비 의미 검토로 승인을 내리지 않았습니다.',
           'speaker_role':'HOST','limitations_checked':True,
           'claims':([{'claim_id':'CS-V179-1',
                     'proposition':'ETF는 주식시장에서 거래되는 상품이라고 발언한다.',
                     'kind':'FACT','quote':'ETF도 주식시장에 거래됩니다.',
                     'context_cue_indices':[1], 'conditions':[],
                     'exceptions':['주식시장 운영시간·매매정지 등을 제외한다.'],
                     'numeric_tokens':[],'high_risk':True,'needs_official_source':True,
                     'evidence_verified':False,'native_v123_approved':False}]
                     if i==1 else [])} for i,t in enumerate(texts,1)]
    p={'schema':SCHEMA,'owner_source_sha256':sha256(raw),'first_cue':1,'last_cue':2,
       'chat_authored_review_source':'ACTIVE_CONVERSATION_NONCRYPTO',
       'original_journal_head_sha256':'0'*64,'supplied_prior_research':False,
       'native_approval':False,'rows':rows}
    return raw,p

class ProjectionProvenance(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.db=Path(t.name)/'private.db';self.raw,self.packet=sample()
    def ingest(self,packet=None,db=None):
        p=packet if packet is not None else self.packet
        return import_chat_packet(db or self.db,self.raw,'AbCdEf12345',p,
          original_sha256=sha256(self.raw),expected_head='0'*64,
          expected_cues_reviewed=0,allow_new_session=True,window_size=2)
    def test_01_real_chat_metadata_not_native_atom_is_projected(self):
        src=copy.deepcopy(self.packet)
        r=self.ingest()
        self.assertEqual(r['provisional_claim_fields_safely_projected'],1)
        self.assertEqual(r['last_cue_committed'],2)
        self.assertEqual(self.packet,src)
        self.assertFalse(r['v123_approved'])
    def test_02_direct_native_claim_remains_native(self):
        p=copy.deepcopy(self.packet)
        for k in ['claim_id','evidence_verified','native_v123_approved']:
            del p['rows'][0]['claims'][0][k]
        r=self.ingest(p)
        self.assertEqual(r['provisional_claim_fields_safely_projected'],0)
    def test_03_fake_approval_is_not_silently_discarded(self):
        p=copy.deepcopy(self.packet);p['rows'][0]['claims'][0]['native_v123_approved']=True
        with self.assertRaisesRegex(InvalidInput,'FORGED_OR_DUPLICATE_RESEARCH_CLAIM_AUTHORITY'):
            self.ingest(p)
        self.assertFalse(self.db.exists())
    def test_04_fake_evidence_confirmation_is_not_silently_discarded(self):
        p=copy.deepcopy(self.packet);p['rows'][0]['claims'][0]['evidence_verified']=True
        with self.assertRaises(InvalidInput): self.ingest(p)
        self.assertFalse(self.db.exists())
    def test_05_unknown_claim_key_is_not_dropped(self):
        p=copy.deepcopy(self.packet);p['rows'][0]['claims'][0]['e4_signed_approval']=True
        with self.assertRaisesRegex(InvalidInput,'UNEXPECTED_RESEARCH_TO_NATIVE_ATOM_FIELD'):
            self.ingest(p)
        self.assertFalse(self.db.exists())
    def test_06_wrong_source_sha_is_not_a_native_journal(self):
        p=copy.deepcopy(self.packet);p['owner_source_sha256']='0'*64
        with self.assertRaises(InvalidInput): self.ingest(p)
        self.assertFalse(self.db.exists())
    def test_07_packet_must_match_externally_pinned_prior_head(self):
        p=copy.deepcopy(self.packet)
        p['original_journal_head_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'PACKET_PRIOR_JOURNAL_HEAD_MISMATCH'):
            self.ingest(p)
        self.assertFalse(self.db.exists())

if __name__=='__main__': unittest.main()