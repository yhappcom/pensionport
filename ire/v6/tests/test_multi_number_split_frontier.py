"""V19 conservative source-first Korean multi-amount cue challenge (synthetic)."""
import copy
import unittest
from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import json_digest,sha256
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from ire.v6.semantic_frontier import source_first_semantic_frontier
from ire.v6.stage_repair import audit_chat_atom_splits
from ire.v6.errors import InvalidInput

class MultiNumberSourceFirstTests(unittest.TestCase):
    def setUp(self):
        raw=make_srt(['출생 시 2천만 원, 열살에 2천만 원을 증여합니다.', '다음 안내입니다.'])
        plan=make_manifest(raw,cut=2)
        self.src=verify_source(raw,plan,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(plan))
    def atom(self,cid,prop):
        text=self.src.cues[0].text
        return {'claim_id':cid,'owner_window_id':self.src.owner(1),
                'proposition':prop,'kind':'HYPOTHETICAL','stance':'UNRESOLVED',
                'speaker':'NARRATOR','source_refs':[{'cue_index':1,'quote':text}],
                'context_cue_indices':[1], 'condition_cue_indices':[],
                'exception_cue_indices':[],
                'numeric_references':[{'cue_index':1,'token':x} for x in NUMBER.findall(text)],
                'as_of':None}
    def exchange(self,atoms):
        ids=sorted(a['claim_id'] for a in atoms)
        return {'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':self.src.video_id,
                'source_sha256':self.src.source_sha256,'manifest_sha256':self.src.manifest_sha256,
                'atoms':atoms,'cue_dispositions':[
                  {'cue_index':i,'cue_text_sha256':sha256(c.text.encode()),
                   'disposition':'CANDIDATES' if i==1 else 'NO_ATOM',
                   'claim_ids':ids if i==1 else [],
                   'numeric_tokens':NUMBER.findall(c.text),
                   'note':'' if i==1 else '독립적인 주장 없음'}
                  for i,c in enumerate(self.src.cues,1)]}
    def test_new_frontier_flags_two_monetary_occurrences_merged_into_one(self):
        text=self.src.cues[0].text
        self.assertEqual(NUMBER.findall(text),['2천만 원','2천만 원'])
        e=self.exchange([self.atom('C00001','출생과 열살에 각각 2천만 원을 증여한다고 설명한다.')])
        f=source_first_semantic_frontier(self.src,e)
        self.assertEqual(f['review_cases_by_kind']['MULTIPLE_NUMERIC_TOKENS_SINGLE_OR_NO_CANDIDATE'],1)
        self.assertFalse(f['independent_semantic_accuracy_verified'])
        self.assertFalse(f['p0_go'])
    def test_two_separate_atoms_do_not_trigger_multi_number_single_warning(self):
        e=self.exchange([self.atom('C00001','출생에 2천만 원을 증여한다.'),
                         self.atom('C00002','열살에 2천만 원을 증여한다.')])
        f=source_first_semantic_frontier(self.src,e)
        self.assertEqual(f['review_cases_by_kind']['MULTIPLE_NUMERIC_TOKENS_SINGLE_OR_NO_CANDIDATE'],0)
        self.assertEqual(audit_host_atomic_exchange(self.src,e)['proposed_atomic_claims'],2)
    def test_split_replay_on_original_anchor_scope_and_identity(self):
        before=self.exchange([self.atom('C00001','출생과 열살에 각각 2천만 원을 증여한다.')])
        after=self.exchange([self.atom('C00002','출생에 2천만 원을 증여한다.'),
                             self.atom('C00003','열살에 2천만 원을 증여한다.')])
        plan=[{'old_claim_id':'C00001','new_claim_ids':['C00002','C00003']}]
        out=audit_chat_atom_splits(self.src,before,after,plan,[])
        self.assertEqual(out['split_count'],1)
        self.assertFalse(out['source_meaning_independently_verified'])
        bad=copy.deepcopy(after)
        bad['atoms'][0]['owner_window_id']='W00002'
        with self.assertRaises(InvalidInput):
            audit_chat_atom_splits(self.src,before,bad,plan,[])
    def test_multi_number_is_only_review_hint_not_law_truth(self):
        raw=make_srt(['매월 18만9,000원씩 10년간 납입합니다.'])
        plan=make_manifest(raw,cut=1)
        src=verify_source(raw,plan,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(plan))
        # A genuine single *scenario* may legitimately have two numerics.
        # This heuristic deliberately escalates to human/chat review; it does
        # not assert two actual semantic claims or force automatic split.
        self.assertEqual(NUMBER.findall(src.cues[0].text),['18만9,000원','10년'])

if __name__=='__main__':unittest.main()
