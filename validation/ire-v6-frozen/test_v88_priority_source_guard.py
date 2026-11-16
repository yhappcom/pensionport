"""Public synthetic-only tests; NO owner SRT or gold finance labels."""
from __future__ import annotations
import copy,unittest
from types import SimpleNamespace
from v88_priority_source_guard import (EXPECTED,FALSE_FLAGS,CATEGORIES,STATUS,VIDEO_ID,
    sha,digest,check_disposition,check_one_review,verify_batch)

class V88SyntheticCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        n=max(int(w[1:]) for w in EXPECTED)*40
        cls.cues=[SimpleNamespace(index=i,start_ms=i*1000,end_ms=i*1000+800,text=f'SYNTHETIC_FAKE_CUE_{i:06d}_ONLY') for i in range(1,n+1)]
        cls.reg={}
        cls.rows=[]
        cls.screens=[]
        for w,cs in EXPECTED.items():
            q=int(w[1:]);reg=[]
            for k,cid in enumerate(cs,1):
                idx=(q-1)*40+3*k
                txt=cls.cues[idx-1].text
                reg.append({'claim_id':cid,'source_text_sha256':sha(txt.encode()),'cue_indices':[idx]})
                ctx=[{'cue_index':j,'start_ms':cls.cues[j-1].start_ms,'end_ms':cls.cues[j-1].end_ms,'text_private':cls.cues[j-1].text} for j in range(idx-2,idx+3)]
                cls.rows.append({'video_no':7,'video_id':VIDEO_ID,'window_id':w,'claim_id':cid,
                  'cue_indices':[idx],'source_excerpt_private':txt,'source_sha256':sha(txt.encode()),
                  'start_ms':cls.cues[idx-1].start_ms,'end_ms':cls.cues[idx-1].end_ms,
                  'adjacent_cues_private':ctx,'adjacent_context_sha256':digest(ctx),
                  'semantic_kind':'HISTORICAL_CASE','speaker_meaning_private':'합성 출처 문장에 관한 길이가 충분한 의미 해석이며 실제 금융 사실과 무관한 합성 시험용으로만 사용합니다.',
                  'scope_caution_private':'합성 시뮬레이션을 실전 금융 승인이나 독립 정답셋으로 절대로 해석하면 안 된다는 강한 적용 제한입니다.',
                  'risk_domain':'SYNTHETIC_ONLY','status':STATUS,'audio_verified':False,'law_current_verified':False,
                  **{k:False for k in FALSE_FLAGS}})
            cls.reg[w]=reg
            batch=cls.cues[(q-1)*40:q*40]
            cls.screens.append({'video_no':7,'video_id':VIDEO_ID,'window_id':w,'screen_status':'SOURCE_BOUND_AUTOMATED_SCREEN_NOT_GOLD',
              'source_window_sha256':sha(' '.join(x.text for x in batch).encode()),'first_cue':batch[0].index,
              'last_cue':batch[-1].index,'draft_parent_count':len(reg),'manual_reviewed_all_parents':False,
              'fact_approved':False,'independent_gold':False,'personal_action_approved':False})
        cls.prior={(f'W{i:05d}',f'C{n:05d}') for i in range(1,32) for n in range(1,3)}
        cls.prior |= {(f'W{i:05d}',f'C{3:05d}') for i in range(1,8)}
        assert len(cls.prior)==69
    def test_01_full_40_source_gate(self):
        x=verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens)
        self.assertEqual((x['new_parent_count'],x['cumulative_parent_count'],x['cumulative_windows_without_samples']),(40,109,228))
    def test_02_no_go(self):
        x=verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens)
        self.assertIs(x['p0_go'],False)
        self.assertEqual(x['approved_financial_facts'],0)
        self.assertEqual(x['official_new_unique_count'],0)
    def test_03_unchanged_digest(self):
        self.assertEqual(verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens)['new_parent_digest_sha256'],verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens)['new_parent_digest_sha256'])
    def test_04_source_order_independent(self):
        x=verify_batch(list(reversed(self.rows)),self.cues,self.reg,self.prior,list(reversed(self.screens)))
        self.assertEqual(x['new_parent_digest_sha256'],verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens)['new_parent_digest_sha256'])
    def test_05_category_census(self):self.assertEqual(len(CATEGORIES),7)
    def test_06_expected_census(self):self.assertEqual(sum(map(len,EXPECTED.values())),40)
    def test_07_40_unique_ids(self):self.assertEqual(len({(r['window_id'],r['claim_id']) for r in self.rows}),40)
    def test_08_original_screen_pinned(self):self.assertEqual(len(self.screens),10)
    def test_09_heterogeneous_prior(self):self.assertEqual(len({w for w,c in self.prior}),31)
    def test_10_original_context_pinned(self):self.assertEqual(len(self.rows[0]['adjacent_cues_private']),5)
    def test_11_no_real_audio(self):self.assertFalse(any(r['audio_verified'] for r in self.rows))
    def test_12_no_gold_labels(self):self.assertFalse(any(r['independent_gold'] for r in self.rows))
    def test_13_source_guard_disallows_foreign_video(self):
        r=copy.deepcopy(self.rows[0]);r['video_id']='wrong'
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_14_source_guard_disallows_foreign_number(self):
        r=copy.deepcopy(self.rows[0]);r['video_no']=6
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_15_source_guard_disallows_fake_id(self):
        r=copy.deepcopy(self.rows[0]);r['claim_id']='C99999'
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_16_dup_parent(self):
        a=copy.deepcopy(self.rows);a[1]=a[0]
        with self.assertRaises(ValueError):verify_batch(a,self.cues,self.reg,self.prior,self.screens)
    def test_17_missing_parent(self):
        with self.assertRaises(ValueError):verify_batch(self.rows[:-1],self.cues,self.reg,self.prior,self.screens)
    def test_18_extra_parent(self):
        with self.assertRaises(ValueError):verify_batch(self.rows+self.rows[:1],self.cues,self.reg,self.prior,self.screens)
    def test_19_missing_prior(self):
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,set(),self.screens)
    def test_20_prior_overlaps_window(self):
        pr=set(self.prior);pr.remove(next(iter(pr)));pr.add((self.rows[0]['window_id'],'C88888'))
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,pr,self.screens)
    def test_21_prior_31_windows_missing(self):
        pr={(f'W{i:05d}',f'C{n:05d}') for i in range(1,30) for n in range(1,4)}
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,pr,self.screens)
    def test_22_missing_screen(self):
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,self.screens[:-1])
    def test_23_duplicate_screen(self):
        s=copy.deepcopy(self.screens);s[1]=s[0]
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_24_screen_completed_claim_blocked(self):
        s=copy.deepcopy(self.screens);s[0]['manual_reviewed_all_parents']=True
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_25_screen_hash_change(self):
        s=copy.deepcopy(self.screens);s[0]['source_window_sha256']='0'*64
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_26_screen_start_change(self):
        s=copy.deepcopy(self.screens);s[0]['first_cue']+=1
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_27_screen_end_change(self):
        s=copy.deepcopy(self.screens);s[0]['last_cue']-=1
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_28_screen_parent_count_change(self):
        s=copy.deepcopy(self.screens);s[0]['draft_parent_count']+=1
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_29_screen_wrong_video(self):
        s=copy.deepcopy(self.screens);s[0]['video_id']='wrong'
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.reg,self.prior,s)
    def test_30_screen_wrong_source(self):
        cc=copy.deepcopy(self.cues);cc[(93-1)*40].text='SOURCE_MUTATED'
        with self.assertRaises(ValueError):verify_batch(self.rows,cc,self.reg,self.prior,self.screens)
    def test_31_source_excerpt_change(self):
        r=copy.deepcopy(self.rows[0]);r['source_excerpt_private']='fabricated'
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_32_source_sha_change(self):
        r=copy.deepcopy(self.rows[0]);r['source_sha256']='f'*64
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_33_wrong_cue_index(self):
        r=copy.deepcopy(self.rows[0]);r['cue_indices']=[1]
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_34_bad_start_time(self):
        r=copy.deepcopy(self.rows[0]);r['start_ms']+=100
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_35_bad_end_time(self):
        r=copy.deepcopy(self.rows[0]);r['end_ms']-=100
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_36_bad_neighbor_text(self):
        r=copy.deepcopy(self.rows[0]);r['adjacent_cues_private'][0]['text_private']='hacked'
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_37_bad_neighbor_hash(self):
        r=copy.deepcopy(self.rows[0]);r['adjacent_context_sha256']='e'*64
        with self.assertRaises(ValueError):check_one_review(r,self.cues,self.reg)
    def test_38_fake_semantic_type(self):
        r=copy.deepcopy(self.rows[0]);r['semantic_kind']='GOLD'
        with self.assertRaises(ValueError):check_disposition(r)
    def test_39_tiny_meaning(self):
        r=copy.deepcopy(self.rows[0]);r['speaker_meaning_private']='ok'
        with self.assertRaises(ValueError):check_disposition(r)
    def test_40_tiny_caution(self):
        r=copy.deepcopy(self.rows[0]);r['scope_caution_private']='ok'
        with self.assertRaises(ValueError):check_disposition(r)
    def test_41_tiny_domain(self):
        r=copy.deepcopy(self.rows[0]);r['risk_domain']='a'
        with self.assertRaises(ValueError):check_disposition(r)
    def test_42_status_go(self):
        r=copy.deepcopy(self.rows[0]);r['status']='GO'
        with self.assertRaises(ValueError):check_disposition(r)
    def test_43_false_audio(self):
        r=copy.deepcopy(self.rows[0]);r['audio_verified']=True
        with self.assertRaises(ValueError):check_disposition(r)
    def test_44_false_law(self):
        r=copy.deepcopy(self.rows[0]);r['law_current_verified']=True
        with self.assertRaises(ValueError):check_disposition(r)

for pos,flag in enumerate(FALSE_FLAGS,45):
    def make_test(field):
        def run(self):
            r=copy.deepcopy(self.rows[0]);r[field]=True
            with self.assertRaises(ValueError):check_disposition(r)
        return run
    setattr(V88SyntheticCustodyTests,f'test_{pos:02d}_false_{flag}',make_test(flag))
if __name__=='__main__':unittest.main()