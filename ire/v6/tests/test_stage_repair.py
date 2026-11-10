"""Only synthetic sources; no private SRT or ChatGPT score becomes gold."""
import copy
import unittest
from ire.v6.atomic_exchange import NUMBER
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest
from ire.v6.stage_repair import audit_chat_atom_splits, review_chat_risk_cases
from ire.v6.semantic_risk import audit_semantic_risks


def fixture(lines):
    raw = make_srt(lines)
    manifest = make_manifest(raw,cut=3)
    return verify_source(raw,manifest,expected_source_sha256=sha256(raw),
                         expected_manifest_sha256=json_digest(manifest))


def atom(src,cid,refs,ctx,proposition,*,stance='CONDITIONAL',conds=None):
    return {'claim_id':cid, 'owner_window_id':src.owner(refs[0]),
            'proposition':proposition,'kind':'FACT','stance':stance,
            'speaker':'NARRATOR','source_refs':[{'cue_index':i,'quote':src.cues[i-1].text} for i in refs],
            'context_cue_indices':ctx,'condition_cue_indices':conds or [],
            'exception_cue_indices':[],
            'numeric_references':[{'cue_index':i,'token':tok} for i in ctx
                                  for tok in NUMBER.findall(src.cues[i-1].text)],
            'as_of':None}


def exchange(src,atoms):
    hits={i:[] for i in range(1,len(src.cues)+1)}
    for a in atoms:
        for r in a['source_refs']:
            hits[r['cue_index']].append(a['claim_id'])
    return {'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':src.video_id,
            'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
            'atoms':atoms,
            'cue_dispositions':[{'cue_index':i,'cue_text_sha256':sha256(c.text.encode()),
                    'disposition':'CANDIDATES' if hits[i] else 'NO_ATOM',
                    'claim_ids':sorted(hits[i]),'numeric_tokens':NUMBER.findall(c.text),
                    'note':'' if hits[i] else '독립적인 주장 없음'}
                    for i,c in enumerate(src.cues,1)]}


class ChatSplitTests(unittest.TestCase):
    def setUp(self):
        self.src=fixture(['ISA는 기간 3년입니다.','연금 전환 경우 20년까지 고려합니다.','여기까지입니다.'])
        old=atom(self.src,'C00001',[1,2],[1,2],
                 'ISA 기간 3년과 전환 경우 20년을 설명한다.',conds=[2])
        self.before=exchange(self.src,[old])
        self.after=exchange(self.src,[
            atom(self.src,'C00002',[1],[1],'ISA 기간은 3년이라고 안내한다.',stance='AFFIRMED'),
            atom(self.src,'C00003',[2],[2],'연금 전환 경우 20년이라고 안내한다.',conds=[2])])
        self.plan=[{'old_claim_id':'C00001','new_claim_ids':['C00002','C00003']}]

    def test_source_exact_split_with_new_ids_and_no_gold(self):
        out=audit_chat_atom_splits(self.src,self.before,self.after,self.plan,[])
        self.assertEqual((out['split_count'],out['retired_candidate_count'],
                         out['split_child_count'],out['after_candidate_count']),(1,1,2,2))
        self.assertFalse(out['p0_go'])
        self.assertFalse(out['source_meaning_independently_verified'])

    def test_reject_unreported_child_deletion(self):
        bad=copy.deepcopy(self.after)
        bad['atoms']=[bad['atoms'][0]]
        bad=exchange(self.src,bad['atoms'])
        with self.assertRaises(InvalidInput):
            audit_chat_atom_splits(self.src,self.before,bad,self.plan,[])

    def test_reject_old_id_reuse_and_missing_anchors(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][0]['claim_id']='C00001'
        bad=exchange(self.src,bad['atoms'])
        with self.assertRaises(InvalidInput):
            audit_chat_atom_splits(self.src,self.before,bad,self.plan,[])
        more=copy.deepcopy(self.after)
        more['atoms'][1]['source_refs']=[{'cue_index':1,'quote':self.src.cues[0].text}]
        more['atoms'][1]['context_cue_indices']=[1]
        more['atoms'][1]['condition_cue_indices']=[]
        more['atoms'][1]['stance']='UNRESOLVED'
        more['atoms'][1]['proposition']='ISA 기간 3년을 설명한다.'
        more=exchange(self.src,more['atoms'])
        with self.assertRaises(InvalidInput):
            audit_chat_atom_splits(self.src,self.before,more,self.plan,[])

    def test_reject_unapproved_additional_atom(self):
        unexpected=atom(self.src,'C00004',[3],[3],'여기까지라는 안내다.',stance='AFFIRMED')
        bad=exchange(self.src,self.after['atoms']+[unexpected])
        with self.assertRaises(InvalidInput):
            audit_chat_atom_splits(self.src,self.before,bad,self.plan,[])
        self.assertEqual(audit_chat_atom_splits(self.src,self.before,bad,self.plan,['C00004'])
                         ['additional_missed_atom_count'],1)

    def test_reject_silent_rewrite_of_non_split_atom(self):
        previous=atom(self.src,'C00004',[3],[3],'여기까지라는 안내다.',stance='AFFIRMED')
        before=exchange(self.src,self.before['atoms']+[previous])
        changed=copy.deepcopy(previous);changed['proposition']='여기까지라는 안내입니다.'
        after=exchange(self.src,self.after['atoms']+[changed])
        with self.assertRaisesRegex(InvalidInput,'SILENT_OLD_CLAIM_REWRITE'):
            audit_chat_atom_splits(self.src,before,after,self.plan,[])


class ChatRiskDocketTests(unittest.TestCase):
    def setUp(self):
        self.src=fixture(['자산배분이라면 목표대로 매수하세요.',
                          '모든 자산이 다 오르는 것은 아닙니다.',
                          '채권을 매도하면 반등을 놓칠 수 있습니다.'])
        self.orig=exchange(self.src,[
            atom(self.src,'C00001',[1],[1],'목표대로 매수하라고 권유한다.',conds=[1]),
            atom(self.src,'C00002',[2],[2],'모든 자산이 동시에 오르는 것은 아니다.',stance='NEGATED'),
            atom(self.src,'C00003',[3],[3],'채권을 팔면 수익을 놓칠 수 있다.',stance='UNRESOLVED')])
        risks=audit_semantic_risks(self.src,self.orig)
        self.assertEqual(risks['cases_by_reason']['NEARBY_CORRECTION_NOT_IN_CONTEXT'],2)
        self.decisions=[{'case_sha256':x['case_sha256'],
              'source_cue_sha256':sha256(self.src.cues[x['cue_index']-1].text.encode()),
              'decision':'CROSS_CLAUSE_CONTEXT','linked_claim_id':'C00002',
              'reason':'인접한 부정문은 별개의 상승 동시성 명제이다.'}
              for x in risks['review_cases']]

    def test_cross_clause_alerts_remain_visible_but_triaged(self):
        r=review_chat_risk_cases(self.src,self.orig,self.orig,self.decisions)
        self.assertEqual((r['original_alert_count'],r['cross_clause_scoped_alerts_raw_still_present'],
                          r['raw_post_review_alert_count'],r['outstanding_chat_triage_count']),(2,2,2,0))
        self.assertFalse(r['source_meaning_independently_verified'])
        self.assertFalse(r['p0_go'])

    def test_missing_or_duplicated_decisions_rejected(self):
        for variant in [self.decisions[:1],self.decisions[:1]*2]:
            with self.assertRaises(InvalidInput):
                review_chat_risk_cases(self.src,self.orig,self.orig,variant)

    def test_forged_cue_sha_and_noncarrier_claim_rejected(self):
        for name in ['cue_sha','carrier']:
            bad=copy.deepcopy(self.decisions)
            if name=='cue_sha':bad[0]['source_cue_sha256']='0'*64
            else:bad[0]['linked_claim_id']='C00001'
            with self.assertRaises(InvalidInput):
                review_chat_risk_cases(self.src,self.orig,self.orig,bad)

    def test_rewrite_condition_requires_real_condition_index(self):
        src=fixture(['초보라면 ISA를 분할매수하라고 권유합니다.'])
        before=exchange(src,[atom(src,'C00001',[1],[1],
                                  '초보라면 ISA를 분할매수하세요.',stance='UNRESOLVED')])
        old_r=audit_semantic_risks(src,before)
        self.assertEqual(old_r['cases_by_reason']['UNMAPPED_CONDITION_IN_MODEL_CONTEXT'],1)
        after=copy.deepcopy(before)
        after['atoms'][0]['stance']='CONDITIONAL'
        after['atoms'][0]['condition_cue_indices']=[1]
        decision=[{'case_sha256':old_r['review_cases'][0]['case_sha256'],
                   'source_cue_sha256':sha256(src.cues[0].text.encode()),
                   'decision':'REMODELED_CONDITION','linked_claim_id':'C00001',
                   'reason':'원문 조건을 권고 조건으로 직접 결박하였다.'}]
        self.assertEqual(review_chat_risk_cases(src,before,after,decision)
                         ['directly_remodeled_alerts'],1)
        fake=copy.deepcopy(after);fake['atoms'][0]['condition_cue_indices']=[]
        fake['atoms'][0]['stance']='UNRESOLVED'
        with self.assertRaises(InvalidInput):
            review_chat_risk_cases(src,before,fake,decision)

    def test_unreviewed_cases_are_not_auto_closed(self):
        unresolved=copy.deepcopy(self.decisions)
        unresolved[0]['decision']='OPEN'
        x=review_chat_risk_cases(self.src,self.orig,self.orig,unresolved)
        self.assertEqual(x['outstanding_chat_triage_count'],1)
        self.assertFalse(x['research_complete'])

if __name__=='__main__':
    unittest.main()
