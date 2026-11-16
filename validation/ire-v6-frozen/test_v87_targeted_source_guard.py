"""Synthetic-only V87 safety regression. Never reads private original subtitles."""
from __future__ import annotations
import copy,unittest
from v87_targeted_source_guard import *

def source_cue():
    c={'video_no':7,'video_id':VIDEO_ID,'cue_index':101,'cue_text_private':'가상 연결어',
        'start_ms':2000,'end_ms':3000,'adjacent_cues_private':[{'cue_index':101,'text_private':'가상 연결어'}],
        'left_candidate':['W00003','C00015'],'right_candidate':['W00003','C00016'],
        'speech_act_category':'LEXICAL_TAIL'}
    c['cue_text_sha256']=sha(c['cue_text_private'].encode());return c

def gap_row():
    c=source_cue()
    return {**c,'adjacent_context_sha256':digest(c['adjacent_cues_private']),
            'semantic_kind':'QUESTION_TAIL','disposition':'MERGE_PREVIOUS',
            'meaning_private':'가상 질문의 종결어미는 앞 문장의 질문 범위 안에서만 해석되어야 한다.',
            'risk_private':'이 질문을 특정 금융상품의 수익률이 인증된 확정 행동 권고로 해석하면 안 된다.',
            'status':'SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD',
            **{f:False for f in FLAG_FIELDS+ADDITIONAL_FALSE}}

def parent_source():
    p={'window_id':'W00138','claim_id':'C01779','cue_indices':[5500,5501],
       'source_excerpt_private':'합성 발화 하나 | 합성 발화 둘',
       'start_ms':100,'end_ms':300,
       'adjacent_cues_private':[{'cue_index':5500,'text_private':'합성 발화 하나'}]}
    p['source_sha256']=sha(p['source_excerpt_private'].encode())
    p['adjacent_context_sha256']=digest(p['adjacent_cues_private']);return p

def parent_row():
    p=parent_source()
    return {**p,'video_no':7,'video_id':VIDEO_ID,'semantic_kind':'QUESTION_NOT_FACT',
            'risk_domain':'NPS_REPLAY',
            'speaker_meaning_private':'화자가 합성 질문을 한 것으로 해석하며 이는 대답과 서로 다른 원자 의미에 속한다.',
            'risk_limit_private':'합성 질문은 실제 금융제도에 대한 법률상 확정 규정이나 독립 정확도 인증이 아니다.',
            'status':'SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD',
            **{f:False for f in FLAG_FIELDS+ADDITIONAL_FALSE}}

class V87Safety(unittest.TestCase):
    def rejects(self,call):
        with self.assertRaises(ValueError):call()
    def test_source_hash_positive(self):self.assertEqual(len(digest({'a':'합성'})),64)
    def test_non_gold_status_positive(self):self.assertIs(non_gold_disposition()['p0_go'],False)
    def test_gap_positive(self):self.assertEqual(len(verify_one_gap(gap_row(),source_cue())),64)
    def test_parent_positive(self):self.assertEqual(len(verify_one_parent(parent_row(),parent_source())),64)
    def test_chain_positive(self):
        e,h=event_chain([('WINDOW','W00001',sha(b'alpha')),('GAP','G01',sha(b'bravo'))]);self.assertEqual(len(e),2);self.assertEqual(e[1][4],e[0][-1]);self.assertEqual(h,e[-1][-1])
    def test_chain_deterministic(self):
        it=[('PARENT','W1:C1',sha(b'x'))];self.assertEqual(event_chain(it),event_chain(it))
    def test_six_screens_positive(self):
        screens=[{'window_id':f'W{i:05d}','flagged':False} for i in range(1,270)]
        selected=[screens[int(w[1:])-1] for w in TARGET_WINDOWS]
        self.assertEqual(len(verify_six_window_screens(selected,screens)),64)
    def test_six_screen_269_missing(self):
        sc=[{'window_id':f'W{i:05d}'} for i in range(1,269)]
        self.rejects(lambda:verify_six_window_screens([],sc))
    def test_six_screen_bad_order(self):
        sc=[{'window_id':f'W{i:05d}'} for i in range(1,270)]
        xs=[sc[int(w[1:])-1] for w in TARGET_WINDOWS];xs.reverse()
        self.rejects(lambda:verify_six_window_screens(xs,sc))
    def test_six_screen_modified(self):
        sc=[{'window_id':f'W{i:05d}','x':0} for i in range(1,270)]
        xs=[dict(sc[int(w[1:])-1]) for w in TARGET_WINDOWS];xs[1]['x']=1
        self.rejects(lambda:verify_six_window_screens(xs,sc))
    def test_census_37(self):self.assertEqual(sum(map(len,EXPECTED_PARENT.values())),37)
    def test_windows_six(self):self.assertEqual(len(TARGET_WINDOWS),6)
    def test_cue_status_unsafe(self):
        r=gap_row();r['status']='APPROVED';self.rejects(lambda:verify_one_gap(r,source_cue()))
    def test_legal_approval_no(self):
        d=non_gold_disposition();self.assertFalse(d['v75_source_lineage_verified'])
    def test_disjoint_list_required(self):
        self.rejects(lambda:verify_parent_reviews([],[],{},set()))
    def test_gap_list_28_required(self):self.rejects(lambda:verify_gap_reviews([],[],[]))
    def test_source_original_archive_pin(self):self.assertEqual(len(OWNER_SHA),64)
    def test_known_source_archive_not_present(self):self.rejects(lambda:verify_pinned_archive('/path/absent/file.zip',OWNER_SHA,'OWNER'))
    def test_wrong_chain_hex(self):self.rejects(lambda:event_chain([('X','Y','g'*64)]))
    def test_empty_chain(self):self.rejects(lambda:event_chain([]))
    def test_chain_duplicate_key(self):self.rejects(lambda:event_chain([('X','Y','0'*64),('X','Y','0'*64)]))
    def test_chain_missing_kind(self):self.rejects(lambda:event_chain([('','Y','0'*64)]))
    def test_chain_missing_key(self):self.rejects(lambda:event_chain([('X','','0'*64)]))
    def test_chain_short_hash(self):self.rejects(lambda:event_chain([('X','Y','a'*63)]))

# Explicit generated negative controls count as separate tests, each mutates one
# independent source field or unauthorized approval flag.
for name,bad in [
 ('gap_video_no',8),('gap_video_id','wrong'),('gap_cue_index',102),
 ('gap_start_ms',2001),('gap_end_ms',3001),('gap_cue_text_private','변조'),
 ('gap_cue_text_sha256','0'*64),('gap_adjacent_cues_private',[]),
 ('gap_adjacent_context_sha256','f'*64),('gap_left_candidate',None),
 ('gap_right_candidate',None),('gap_speech_act_category','ASSENT'),
 ('gap_semantic_kind','CERTIFIED_FACT'),('gap_disposition','NEGATIVE_GOLD'),
 ('gap_meaning_private',''),('gap_risk_private','')]:
    field=name.removeprefix('gap_')
    def make(field=field,bad=bad):
        def t(self):
            r=gap_row();r[field]=bad
            with self.assertRaises(ValueError):verify_one_gap(r,source_cue())
        return t
    setattr(V87Safety,'test_'+name,make())
for name,bad in [
 ('parent_video_no',8),('parent_video_id','wrong'),('parent_window_id','W00002'),
 ('parent_claim_id','C99999'),('parent_cue_indices',[3]),
 ('parent_start_ms',111),('parent_end_ms',320),
 ('parent_source_excerpt_private','변조'),('parent_source_sha256','a'*64),
 ('parent_adjacent_cues_private',[]),('parent_adjacent_context_sha256','b'*64),
 ('parent_semantic_kind','APPROVED'),('parent_risk_domain',''),
 ('parent_speaker_meaning_private',''),('parent_risk_limit_private','')]:
    field=name.removeprefix('parent_')
    def make(field=field,bad=bad):
        def t(self):
            r=parent_row();r[field]=bad
            with self.assertRaises(ValueError):verify_one_parent(r,parent_source())
        return t
    setattr(V87Safety,'test_'+name,make())
for n,flag in enumerate(FLAG_FIELDS+ADDITIONAL_FALSE,1):
    def make(flag=flag):
        def t(self):
            r=parent_row();r[flag]=True
            with self.assertRaises(ValueError):verify_one_parent(r,parent_source())
        return t
    setattr(V87Safety,f'test_denies_approval_{n}_{flag}',make())

if __name__=='__main__':unittest.main()