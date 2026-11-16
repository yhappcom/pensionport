"""Synthetic-only V84 source-custody tests. Uses no private SRT/prose fixtures."""
from __future__ import annotations
import copy, tempfile, unittest
from pathlib import Path
from v77_private_v33_replay import Cue, sha, digest
from v84_gap_extension_guard import (
  classify_speech_act, check_94_speechact_reviews,check_new5_manual_samples,
  new_video_census,audit_v83_private_custody,
  SPEECH_ACT_WARNING_ANCHORS,EXPECTED_CATEGORY_COUNTS,CATEGORIES)


def fake_94():
    all_keys=list(SPEECH_ACT_WARNING_ANCHORS)
    all_keys.extend((1,10000+i) for i in range(81))
    assert len(all_keys)==94
    texts=(['>> 네.']*51 + ['>> 음.']*35 + ['>> 안녕하세요.']*4+
           ['[웃음]']*2 + ['있어요.']*2)
    prev=[];now=[]
    for (n,idx),t in zip(all_keys,texts):
        video_id='SYNTH'+str(n);time=idx*1000
        neighbors=[{'cue_index':idx,'text_private':t,'start_ms':time,'end_ms':time+100}]
        p={'video_no':n,'video_id':video_id,'cue_index':idx,'cue_text_private':t,
          'cue_text_sha256':sha(t.encode('utf-8')),'start_ms':time,'end_ms':time+100,
          'adjacent_cues_private':neighbors,'context_interpretation_private':None}
        prev.append(p)
        now.append({'video_no':n,'video_id':video_id,'cue_index':idx,
          'cue_text_sha256':p['cue_text_sha256'],'start_ms':time,'end_ms':time+100,
          'source_adjacent_cues_sha256':digest(neighbors),
          'speech_act_category':classify_speech_act(t),
          'context_risk_code':SPEECH_ACT_WARNING_ANCHORS.get((n,idx)),
          'interpretation_private':'Synthetic speech act interpretation for regression only.',
          'caution_private':'Synthetic no-false-gold, no-financial-approval note.',
          'status':'SPEECH_ACT_CONTEXT_REVIEW_NOT_INDEPENDENT_GOLD',
          **{key:False for key in ('fact_approved','independent_gold','official_parent_merged',
                                   'personal_action_approved','v75_membership_verified','negative_gold_certified')}})
    for i in range(10):
        n=5;idx=20000+i;t='>> 네.'
        prev.append({'video_no':n,'video_id':'SYNTH5','cue_index':idx,
           'cue_text_private':t,'cue_text_sha256':sha(t.encode()),
           'start_ms':idx*1000,'end_ms':idx*1000+100,
           'adjacent_cues_private':[],
           'context_interpretation_private':'Previously reviewed in V83 synthetic fixture'})
    assert len(prev)==104 and len(now)==94
    return prev,now


def fake_six():
    vids={6:'3MyhYE2jmuE',7:'4CQ4FjGT2gA',8:'OfkY343OaNs',9:'YNOSY15ppf8',10:'VKr060rIirM'}
    cues={};reg={};rows=[]
    for n,vid in vids.items():
        texts=[f'Synthetic source claim for video {n}',f'Synthetic second claim for video {n}']
        cues[vid]=[Cue(i,100*i,100*i+99,t) for i,t in enumerate(texts,1)]
        reg[vid]={'W00001':[]}
        for i,t in enumerate(texts[:2 if n==10 else 1],1):
            cid=f'C{i:05d}'
            reg[vid]['W00001'].append({'claim_id':cid,'source_text_sha256':sha(t.encode()),'cue_indices':[i]})
            rows.append({'video_no':n,'video_id':vid,'window_id':'W00001','claim_id':cid,
              'cue_indices':[i],'source_excerpt_private':t,'source_sha256':sha(t.encode()),
              'speaker_meaning_private':'Synthetic meaning for source-checked original interview.',
              'scope_caution_private':'Synthetic scope warning for independent risk checking.',
              'status':'SOURCE_BOUND_FINANCE_MEANING_PRELIMINARY_OPEN',
              **{key:False for key in ('fact_approved','independent_gold','official_parent_merged',
                                       'personal_action_approved','v75_membership_verified')}})
    assert len(rows)==6
    return cues,reg,rows


class SpeechActs(unittest.TestCase):
    def test_assent(self):self.assertEqual(classify_speech_act('>> 네.'),'ASSENT_OR_CONFIRMATION')
    def test_confirm(self):self.assertEqual(classify_speech_act('>> 그죠?'),'ASSENT_OR_CONFIRMATION')
    def test_agree(self):self.assertEqual(classify_speech_act('맞아요.'),'ASSENT_OR_CONFIRMATION')
    def test_contemplation(self):self.assertEqual(classify_speech_act('>> 음'),'DISCOURSE_OR_SURPRISE')
    def test_surprise(self):self.assertEqual(classify_speech_act('>> 헐'),'DISCOURSE_OR_SURPRISE')
    def test_courtesy(self):self.assertEqual(classify_speech_act('>> 감사합니다.'),'COURTESY')
    def test_greeting(self):self.assertEqual(classify_speech_act('안녕하세요.'),'COURTESY')
    def test_laughter(self):self.assertEqual(classify_speech_act('[웃음]'),'LAUGHTER')
    def test_predicate(self):self.assertEqual(classify_speech_act('있어요.'),'PREDICATE_TAIL')
    def test_empty_unrecognized(self):self.assertEqual(classify_speech_act(''),'UNKNOWN_REQUIRES_REVIEW')
    def test_unknown_content_requires_review(self):self.assertEqual(classify_speech_act('300만원'),'UNKNOWN_REQUIRES_REVIEW')
    def test_category_count_pin(self):self.assertEqual(sum(EXPECTED_CATEGORY_COUNTS.values()),94)
    def test_no_actual_finance_approval(self):self.assertNotIn('FINANCIAL_APPROVED',CATEGORIES)

class NinetyFourFailures(unittest.TestCase):
    def setUp(self):self.prev,self.rows=fake_94()
    def test_full_synthetic_control(self):
        r=check_94_speechact_reviews(self.prev,self.rows)
        self.assertEqual(r['new_source_context_speechacts_reviewed'],94)
        self.assertEqual(r['new_context_risk_flags'],13)
        self.assertEqual(r['category_counts'],EXPECTED_CATEGORY_COUNTS)
        self.assertFalse(r['formal_gold_precision_recall_measured'])
    def fails(self,which='REVIEW'):
        with self.assertRaisesRegex(ValueError,'V84_'):check_94_speechact_reviews(self.prev,self.rows)
    def test_duplicate_review_rejected(self):self.rows[0]=self.rows[1];self.fails()
    def test_missing_review_rejected(self):self.rows.pop();self.fails()
    def test_changed_source_sha_rejected(self):self.rows[0]['cue_text_sha256']='0'*64;self.fails()
    def test_changed_neighbor_context_rejected(self):self.rows[0]['source_adjacent_cues_sha256']='0'*64;self.fails()
    def test_changed_video_id_rejected(self):self.rows[0]['video_id']='OTHER';self.fails()
    def test_changed_timestamp_rejected(self):self.rows[0]['start_ms']+=1;self.fails()
    def test_wrong_category_rejected(self):self.rows[0]['speech_act_category']='PREDICATE_TAIL';self.fails()
    def test_false_gold_rejected(self):self.rows[0]['independent_gold']=True;self.fails()
    def test_false_finance_approval_rejected(self):self.rows[0]['fact_approved']=True;self.fails()
    def test_false_negative_gold_rejected(self):self.rows[0]['negative_gold_certified']=True;self.fails()
    def test_false_personal_advice_rejected(self):self.rows[0]['personal_action_approved']=True;self.fails()
    def test_false_v75_membership_rejected(self):self.rows[0]['v75_membership_verified']=True;self.fails()
    def test_false_official_merge_rejected(self):self.rows[0]['official_parent_merged']=True;self.fails()
    def test_risk_not_silenced(self):self.rows[0]['context_risk_code']=None;self.fails()
    def test_risk_not_fabricated(self):self.rows[-1]['context_risk_code']='FINANCIAL_TRUE';self.fails()
    def test_missing_interpretation_rejected(self):self.rows[0]['interpretation_private']='';self.fails()
    def test_missing_caution_rejected(self):self.rows[0]['caution_private']='';self.fails()
    def test_prior_v83_reclassification_rejected(self):self.prev[0]['context_interpretation_private']='Previously done';self.fails()
    def test_prior_record_duplication_rejected(self):self.prev[-1]=self.prev[0];self.fails()
    def test_unknown_speechact_rejected(self):self.prev[0]['cue_text_private']='수익률 15%';self.fails()
    def test_untrusted_review_status_rejected(self):self.rows[0]['status']='APPROVED';self.fails()

class NewVideosSynthetic(unittest.TestCase):
    def setUp(self):self.cues,self.reg,self.rows=fake_six()
    def fail_sample(self):
        with self.assertRaisesRegex(ValueError,'V84_'):check_new5_manual_samples(self.cues,self.reg,self.rows)
    def test_six_manual_source_checks_pass(self):
        r=check_new5_manual_samples(self.cues,self.reg,self.rows)
        self.assertEqual(r['manual_six_to_ten_parent_reviews'],6)
        self.assertFalse(r['independent_gold_precision_recall_measured'])
    def test_duplicate_sample_rejected(self):self.rows[0]=self.rows[1];self.fail_sample()
    def test_missing_video_sample_rejected(self):self.rows=self.rows[:5];self.fail_sample()
    def test_wrong_sample_prose_rejected(self):self.rows[0]['source_excerpt_private']='Fabrication';self.fail_sample()
    def test_wrong_sample_sha_rejected(self):self.rows[0]['source_sha256']='0'*64;self.fail_sample()
    def test_wrong_claim_key_rejected(self):self.rows[0]['claim_id']='C12345';self.fail_sample()
    def test_wrong_cue_indices_rejected(self):self.rows[0]['cue_indices']=[2];self.fail_sample()
    def test_false_approved_sample_rejected(self):self.rows[0]['fact_approved']=True;self.fail_sample()
    def test_false_gold_sample_rejected(self):self.rows[0]['independent_gold']=True;self.fail_sample()
    def test_false_advice_sample_rejected(self):self.rows[0]['personal_action_approved']=True;self.fail_sample()
    def test_false_old_queue_membership_rejected(self):self.rows[0]['v75_membership_verified']=True;self.fail_sample()
    def test_missing_meaning_rejected(self):self.rows[0]['speaker_meaning_private']='';self.fail_sample()
    def test_missing_caution_rejected(self):self.rows[0]['scope_caution_private']='';self.fail_sample()
    def test_fabricated_status_rejected(self):self.rows[0]['status']='FINANCIAL_APPROVED';self.fail_sample()
    def test_unpinned_zip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fake.zip';path.write_bytes(b'bad archive')
            with self.assertRaisesRegex(ValueError,'V84_OWNER_ZIP_SHA_MISMATCH'):new_video_census(path)
    def test_unpinned_v83_zip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fake.zip';path.write_bytes(b'bad archive')
            with self.assertRaisesRegex(ValueError,'V84_V83_PRIVATE_ZIP_CHANGED'):audit_v83_private_custody(path,Path(d)/'other.zip')

if __name__=='__main__':unittest.main()