"""Synthetic regression: monetary units and ChatGPT self-reference never certify gold."""
import copy
import unittest
from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.internal_reference import score_chat_internal_reference
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest

class ChatInternalReferenceTests(unittest.TestCase):
    def setUp(self):
        raw=make_srt(['전환금액은 최대 300만 원입니다.','연금기간은 20년입니다.','안내 끝입니다.'])
        manifest=make_manifest(raw,cut=2)
        src=verify_source(raw,manifest,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(manifest))
        self.src=src
        def atom(cid,idx,prop,tok):
            return {'claim_id':cid,'owner_window_id':src.owner(idx),'proposition':prop,
                'kind':'FACT','stance':'AFFIRMED','speaker':'NARRATOR',
                'source_refs':[{'cue_index':idx,'quote':src.cues[idx-1].text}],
                'context_cue_indices':[idx],'condition_cue_indices':[],
                'exception_cue_indices':[],
                'numeric_references':[{'cue_index':idx,'token':tok}],'as_of':None}
        self.pred={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':src.video_id,
            'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
            'atoms':[atom('C00001',1,'최대 300만 원','300만 원'),atom('C00002',2,'기간 20년','20년')],
            'cue_dispositions':[{'cue_index':i,'cue_text_sha256':sha256(c.text.encode()),
                'disposition':'CANDIDATES' if i<3 else 'NO_ATOM',
                'claim_ids':['C00001' if i==1 else 'C00002'] if i<3 else [],
                'numeric_tokens':NUMBER.findall(c.text),
                'note':'' if i<3 else '추가 독립주장 없음'} for i,c in enumerate(src.cues,1)]}
        self.ref={'schema':'IRE_V6_CHAT_INTERNAL_REFERENCE_V1','video_id':src.video_id,
            'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
            'claims':[{'ref_id':g,'category':cat,'proposition':p,'cue_indices':[i],
                'cue_text_sha256':[sha256(src.cues[i-1].text.encode())]}
                for g,cat,i,p in [('G00001','TAX',1,'공제 300만 원'),
                                    ('G00002','PENSION',2,'기간 20년'),
                                    ('G00003','OTHER',3,'안내 종료')]]}
        self.align={'schema':'IRE_V6_CHAT_INTERNAL_ALIGNMENT_V1',
            'reference_sha256':json_digest(self.ref),
            'candidate_sha256':audit_host_atomic_exchange(src,self.pred)['atom_candidate_digest'],
            'exact_pairs':[{'ref_id':'G00001','claim_id':'C00001'}],
            'partial_pairs':[{'claim_id':'C00002','ref_ids':['G00002'],
                              'reason':'부분일치이며 확인 필요'}],
            'unmatched_reference_ids':['G00003'],'all_claims_compared':True}
    def test_unit_spacing_and_duration(self):
        self.assertEqual(NUMBER.findall('300만 원, 20년, 3개월, 40%'),
            ['300만 원','20년','3개월','40%'])
    def test_unit_forgery_rejected(self):
        for bad in ['300억 원','300원','300달러']:
            sample=copy.deepcopy(self.pred);sample['atoms'][0]['proposition']='최대 '+bad
            with self.subTest(bad=bad),self.assertRaises(InvalidInput):
                audit_host_atomic_exchange(self.src,sample)
    def test_same_unit_whitespace_variant_is_allowed(self):
        sample=copy.deepcopy(self.pred)
        sample['atoms'][0]['proposition']='최대 300만원'
        self.assertEqual(audit_host_atomic_exchange(self.src,sample)['proposed_atomic_claims'],2)
    def test_year_to_month_forgery_rejected(self):
        sample=copy.deepcopy(self.pred);sample['atoms'][1]['proposition']='기간 20개월'
        with self.assertRaises(InvalidInput):audit_host_atomic_exchange(self.src,sample)
    def test_internal_score_never_gold(self):
        result=score_chat_internal_reference(self.src,self.pred,self.ref,self.align)
        self.assertEqual((result['counts']['tp'],result['counts']['fp'],result['counts']['fn']),(1,1,2))
        self.assertEqual(result['precision']['parts_per_million'],500000)
        self.assertEqual(result['recall']['parts_per_million'],333333)
        self.assertFalse(result['human_adjudication_verified'])
        self.assertFalse(result['reference_independence_verified'])
        self.assertFalse(result['p0_go'])
    def test_forged_source_ref_rejected(self):
        fake=copy.deepcopy(self.ref);fake['claims'][0]['cue_text_sha256']=['0'*64]
        align=copy.deepcopy(self.align);align['reference_sha256']=json_digest(fake)
        with self.assertRaises(InvalidInput):
            score_chat_internal_reference(self.src,self.pred,fake,align)
    def test_replay_drift_rejected(self):
        for key in ['reference_sha256','candidate_sha256']:
            align=copy.deepcopy(self.align);align[key]='0'*64
            with self.subTest(key=key),self.assertRaises(InvalidInput):
                score_chat_internal_reference(self.src,self.pred,self.ref,align)
    def test_missing_or_duplicate_alignment_rejected(self):
        for kind in ['missing','double','reuse']:
            align=copy.deepcopy(self.align)
            if kind=='missing':align['unmatched_reference_ids']=[]
            if kind=='double':align['exact_pairs'].append(align['exact_pairs'][0])
            if kind=='reuse':align['partial_pairs'][0]['claim_id']='C00001'
            with self.subTest(kind=kind),self.assertRaises(InvalidInput):
                score_chat_internal_reference(self.src,self.pred,self.ref,align)
if __name__=='__main__':unittest.main()
