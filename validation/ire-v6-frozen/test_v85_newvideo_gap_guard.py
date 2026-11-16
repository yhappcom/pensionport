"""Synthetic-only V85 custody and fail-closed tests. No actual owner transcripts."""
from __future__ import annotations
import copy,tempfile,unittest
from pathlib import Path
from v77_private_v33_replay import Cue,sha,digest
from v85_newvideo_gap_guard import (
  categorize,expected_unassigned,validate_gap_records,validate_31_candidates,
  SAMPLE_KEYS,CRITICAL_LEXICAL_KEYS,COUNT_PIN,audit_previous_v84,ASSERT_FALSE)
VID={6:'3MyhYE2jmuE',7:'4CQ4FjGT2gA',8:'OfkY343OaNs',9:'YNOSY15ppf8',10:'VKr060rIirM'}


def fake_context():
    allcues={};allregs={};outputs=[]
    maxidx={6:807,7:10190,8:1010,9:900,10:15}
    text_by_cat={'ASSENT':'>> 네.','DISCOURSE':'>> 음.','COURTESY':'감사합니다.',
                 'LAUGHTER':'[웃음]','LEXICAL_TAIL':'경우에는'}
    for n,vid in VID.items():
        cs=COUNT_PIN[n];size=maxidx[n];crit={idx for a,idx in CRITICAL_LEXICAL_KEYS if a==n}
        used=set(crit);cats={i:'LEXICAL_TAIL' for i in used}
        for cat,count in cs.items():
            target=count-(len(crit) if cat=='LEXICAL_TAIL' else 0)
            for _ in range(target):
                i=next(i for i in range(1,size+1) if i not in used)
                used.add(i);cats[i]=cat
        cues=[Cue(i,1000*i,1000*i+300,text_by_cat.get(cats.get(i),'Synthetic parent source.')) for i in range(1,size+1)]
        assigned=[i for i in range(1,size+1) if i not in used]
        regs={'W00001':[{'claim_id':'C99999','cue_indices':assigned}]}
        allcues[vid]=cues;allregs[vid]=regs
        expected=expected_unassigned(regs,cues,vid,n)
        for e in expected:
            e['adjacent_context_sha256']=digest(e['adjacent_cues_private'])
            e['critical_lexical']=(n,e['cue_index']) in CRITICAL_LEXICAL_KEYS
            e['lexical_independent_claim_status']=('OPEN_NEEDS_CONTEXT_OR_AUDIO'
               if e['speech_act_category']=='LEXICAL_TAIL' else 'NOT_ASSESSED_SEMANTIC_GOLD')
            e['interpretation_private']='Synthetic interpretation for a source-bound cue.'
            e['scope_warning_private']='Synthetic caution to never certify a financial fact.'
            e['status']='SOURCE_BOUND_AUX_CONTEXT_NOT_ATOMIC_FACT'
            e.update({f:False for f in ASSERT_FALSE})
            outputs.append(e)
    assert len(outputs)==295
    return allcues,allregs,outputs


def fake_semantic():
    allcues={};allregs={};rows=[]
    for n,vid in VID.items():
        allcues[vid]=[];allregs[vid]={}
        for ix,(wid,cid) in enumerate(SAMPLE_KEYS[n],1):
            txt=f'Synthetic private source unit {n}:{wid}:{cid}.'
            allcues[vid].append(Cue(ix,ix*1000,ix*1000+200,txt))
            allregs[vid].setdefault(wid,[]).append({'claim_id':cid,'cue_indices':[ix],
                                                       'source_text_sha256':sha(txt.encode())})
        cc=allcues[vid]
        for ix,(wid,cid) in enumerate(SAMPLE_KEYS[n],1):
            txt=cc[ix-1].text
            context=[{'cue_index':i,'text':cc[i-1].text} for i in range(max(1,ix-2),min(len(cc),ix+2)+1)]
            rows.append({'video_no':n,'video_id':vid,'window_id':wid,'claim_id':cid,
              'source_excerpt_private':txt,'source_sha256':sha(txt.encode()),
              'cue_indices':[ix],'start_ms':cc[ix-1].start_ms,'end_ms':cc[ix-1].end_ms,
              'adjacent_context_private':context,'utterance_kind':'QUESTION',
              'speaker_meaning_private':'This is a synthetic source-grounded meaning interpretation.',
              'scope_caution_private':'This caution does not grant any investment or tax approval.',
              'status':'SOURCE_BOUND_PRELIMINARY_SEMANTIC_NOT_GOLD',
              **{f:False for f in ASSERT_FALSE}})
    prev=[{'video_id':VID[n],'window_id':w,'claim_id':c} for n,w,c in [(6,'W00007','C00082'),(7,'W00003','C00031'),(8,'W00001','C00006'),(9,'W00002','C00018'),(10,'W00001','C00004'),(10,'W00001','C00005')]]
    return allcues,allregs,rows,prev

class SpeechActClassification(unittest.TestCase):
    def test_assent(self):self.assertEqual(categorize('>> 네.'),'ASSENT')
    def test_confirm(self):self.assertEqual(categorize('>> 맞아요.'),'ASSENT')
    def test_indeed(self):self.assertEqual(categorize('예예.'),'ASSENT')
    def test_contemplation(self):self.assertEqual(categorize('>> 음.'),'DISCOURSE')
    def test_surprise(self):self.assertEqual(categorize('와.'),'DISCOURSE')
    def test_greeting(self):self.assertEqual(categorize('>> 안녕하세요.'),'COURTESY')
    def test_thanks(self):self.assertEqual(categorize('감사합니다.'),'COURTESY')
    def test_laughter(self):self.assertEqual(categorize('[웃음]'),'LAUGHTER')
    def test_short_negation_remains_open(self):self.assertEqual(categorize('없었고.'),'LEXICAL_TAIL')
    def test_short_year_remains_open(self):self.assertEqual(categorize('2024년에.'),'LEXICAL_TAIL')
    def test_cue_count_pin(self):self.assertEqual(sum(sum(x.values()) for x in COUNT_PIN.values()),295)
    def test_risk_anchor_pin(self):self.assertEqual(len(CRITICAL_LEXICAL_KEYS),18)

class Gap295FailClosed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cc,cls.reg,cls.base=fake_context()
    def setUp(self):self.rows=copy.deepcopy(self.base)
    def deny(self):
        with self.assertRaisesRegex(ValueError,'V85_'):validate_gap_records(self.cc,self.reg,self.rows)
    def test_complete_synthetic_control(self):
        r=validate_gap_records(self.cc,self.reg,self.rows)
        self.assertEqual(r['unassigned_cues'],295)
        self.assertEqual(r['lexical_cues_open'],46)
        self.assertEqual(r['source_risk_anchor_count'],18)
    def test_one_missing_denied(self):self.rows.pop();self.deny()
    def test_extra_untrusted_denied(self):self.rows.append(copy.deepcopy(self.rows[0]));self.deny()
    def test_duplicate_cue_denied(self):self.rows[0]=copy.deepcopy(self.rows[1]);self.deny()
    def test_video_id_changed_denied(self):self.rows[0]['video_id']='FOREIGN';self.deny()
    def test_source_text_tampered_denied(self):self.rows[0]['cue_text_private']='Other';self.deny()
    def test_source_sha_tampered_denied(self):self.rows[0]['cue_text_sha256']='0'*64;self.deny()
    def test_adjacent_source_tampered_denied(self):self.rows[0]['adjacent_cues_private']=[];self.deny()
    def test_neighbor_sha_tampered_denied(self):self.rows[0]['adjacent_context_sha256']='0'*64;self.deny()
    def test_start_time_tampered_denied(self):self.rows[0]['start_ms']+=1;self.deny()
    def test_end_time_tampered_denied(self):self.rows[0]['end_ms']+=1;self.deny()
    def test_left_candidate_tampered_denied(self):self.rows[0]['left_candidate']=['BAD'];self.deny()
    def test_right_candidate_tampered_denied(self):self.rows[0]['right_candidate']=['BAD'];self.deny()
    def test_category_tampered_denied(self):self.rows[0]['speech_act_category']='OTHER';self.deny()
    def test_critical_warning_removed_denied(self):
        p=next(x for x in self.rows if x['critical_lexical']);p['critical_lexical']=False;self.deny()
    def test_critical_warning_forged_denied(self):
        p=next(x for x in self.rows if not x['critical_lexical']);p['critical_lexical']=True;self.deny()
    def test_lexical_falsely_negative_gold_denied(self):
        p=next(x for x in self.rows if x['speech_act_category']=='LEXICAL_TAIL')
        p['lexical_independent_claim_status']='NONCLAIM_GOLD';self.deny()
    def test_nonlexical_falsely_negative_gold_denied(self):self.rows[0]['lexical_independent_claim_status']='NONCLAIM_GOLD';self.deny()
    def test_interpretation_omitted_denied(self):self.rows[0]['interpretation_private']='';self.deny()
    def test_scope_warning_omitted_denied(self):self.rows[0]['scope_warning_private']='';self.deny()
    def test_provisional_status_forged_denied(self):self.rows[0]['status']='APPROVED';self.deny()
    def test_finance_approval_denied(self):self.rows[0]['fact_approved']=True;self.deny()
    def test_blind_gold_forged_denied(self):self.rows[0]['independent_gold']=True;self.deny()
    def test_negative_gold_forged_denied(self):self.rows[0]['negative_gold_certified']=True;self.deny()
    def test_personal_action_forged_denied(self):self.rows[0]['personal_action_approved']=True;self.deny()
    def test_old_queue_membership_forged_denied(self):self.rows[0]['v75_membership_verified']=True;self.deny()
    def test_official_parent_merge_forged_denied(self):self.rows[0]['official_parent_merged']=True;self.deny()

class ThirtyOneFailClosed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cc,cls.reg,cls.base,cls.prev=fake_semantic()
    def setUp(self):self.rows=copy.deepcopy(self.base);self.prev_rows=copy.deepcopy(self.prev)
    def deny(self):
        with self.assertRaisesRegex(ValueError,'V85_'):validate_31_candidates(self.cc,self.reg,self.rows,self.prev_rows)
    def test_complete_synthetic_control(self):
        r=validate_31_candidates(self.cc,self.reg,self.rows,self.prev_rows)
        self.assertEqual(r['new_source_bound_semantic_parent_reviews'],31)
        self.assertEqual(r['previous_v84_six_overlap'],0)
    def test_missing_record_denied(self):self.rows.pop();self.deny()
    def test_duplicate_record_denied(self):self.rows[0]=copy.deepcopy(self.rows[1]);self.deny()
    def test_wrong_video_denied(self):self.rows[0]['video_id']='OTHER';self.deny()
    def test_wrong_source_text_denied(self):self.rows[0]['source_excerpt_private']='Injected';self.deny()
    def test_wrong_source_sha_denied(self):self.rows[0]['source_sha256']='0'*64;self.deny()
    def test_cue_indices_changed_denied(self):self.rows[0]['cue_indices']=[999];self.deny()
    def test_wrong_timestamp_denied(self):self.rows[0]['end_ms']+=100;self.deny()
    def test_neighbors_tampered_denied(self):self.rows[0]['adjacent_context_private']=[];self.deny()
    def test_fake_past_review_duplicate_denied(self):
        self.prev_rows[0]={'video_id':self.rows[0]['video_id'],
           'window_id':self.rows[0]['window_id'],'claim_id':self.rows[0]['claim_id']};self.deny()
    def test_claim_key_changed_denied(self):self.rows[0]['claim_id']='C99999';self.deny()
    def test_untrusted_type_denied(self):self.rows[0]['utterance_kind']='FACT_CERTIFIED';self.deny()
    def test_meaning_missing_denied(self):self.rows[0]['speaker_meaning_private']='';self.deny()
    def test_risk_missing_denied(self):self.rows[0]['scope_caution_private']='';self.deny()
    def test_status_forged_denied(self):self.rows[0]['status']='INDEPENDENT_GOLD';self.deny()
    def test_finance_approval_forged_denied(self):self.rows[0]['fact_approved']=True;self.deny()
    def test_personal_action_forged_denied(self):self.rows[0]['personal_action_approved']=True;self.deny()
    def test_old_queue_forged_denied(self):self.rows[0]['v75_membership_verified']=True;self.deny()
    def test_blind_gold_forged_denied(self):self.rows[0]['independent_gold']=True;self.deny()
    def test_negative_gold_forged_denied(self):self.rows[0]['negative_gold_certified']=True;self.deny()
    def test_official_merge_forged_denied(self):self.rows[0]['official_parent_merged']=True;self.deny()

class OldPrivateArchiveFence(unittest.TestCase):
    def test_fake_unpinned_v84_zip_denied(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'bad.zip';fake.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'V85_V84_PRIVATE_ZIP_CHANGED'):
                audit_previous_v84('owner','v83',fake)

if __name__=='__main__':unittest.main()