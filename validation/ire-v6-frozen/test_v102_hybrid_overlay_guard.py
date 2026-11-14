"""Synthetic only. No private transcript or real finance labels in GitHub."""
import copy,unittest
from collections import Counter
from dataclasses import dataclass
from v102_hybrid_overlay_guard import reconcile,sha,digest,NEW_SCOPE,NEW_SPLITS,REVIEWED,FALSE,SOURCE_ARCHIVE_SHA,V98_ARCHIVE_SHA,V101_ARCHIVE_SHA

@dataclass
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str

class TestV102(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cues={};cls.regs={};cls.old=[];cls.new=[];cls.parents=[];cls.gaps=[];cls.splits=[];cls.baseline=[]
        # Entire six-video source route simulated as 15857 unique identity rows.
        for v,w,no,pc,pr in NEW_SCOPE:
            first=(int(w[1:])-1)*40+1
            cues=[Cue(i,i*1000,i*1000+850,'SYNTHETIC_PRIVATE_STYLE_CUE_'+v+'_'+str(i)) for i in range(1,first+40)]
            cls.cues[v]=cues;cls.regs[v]={w:[]}
            numbers=list(range(first,first+40))
            if v=='4CQ4FjGT2gA':numbers=numbers[1:]
            baseid=103 if v=='sz5N9WJS310' else 498
            sizes=[len(numbers)//pc+(1 if i<len(numbers)%pc else 0) for i in range(pc)]
            off=0;assigned={}
            for j,sz in enumerate(sizes):
                ix=numbers[off:off+sz];off+=sz
                cid=f'C{baseid+j:05d}'
                p={'claim_id':cid,'cue_indices':ix,'source_text_sha256':sha(' | '.join(cues[i-1].text for i in ix))}
                cls.regs[v][w].append(p)
                for i in ix:assigned[i]=cid
                cls.parents.append({'video_id':v,'window_id':w,'parent_id':cid,'cue_indices':ix,
                   'parent_sha256':p['source_text_sha256'],'source_text_private':' | '.join(cues[i-1].text for i in ix),
                   'semantic_kind':'HYPOTHETICAL','speaker_meaning_private':'Synthetic source contextual meaning to be evaluated only by a chat model.',
                   'reviewer_scope_caution_private':'Never approve synthetic finance claims or treat them as gold facts.',
                   'review_status':REVIEWED,**{f:False for f in FALSE}})
            for i in range(first,first+40):
                c=cues[i-1]
                context=[{'cue_index':j,'text_private':cues[j-1].text} for j in range(max(1,i-2),min(len(cues),i+2)+1)]
                cls.new.append({'video_id':v,'window_id':w,'cue_index':i,'start_ms':c.start_ms,'end_ms':c.end_ms,
                    'source_text_private':c.text,'cue_sha256':sha(c.text),'context_private':context,'context_sha256':digest(context),
                    'parent_id':assigned.get(i)})
                route=('PRIORITY_' if i<first+pr else 'BASELINE_')+('PARENT_PENDING' if i in assigned else 'UNASSIGNED_PENDING')
                cls.baseline.append([v,w,i,sha(c.text),assigned.get(i),route,False,False])
            if v=='4CQ4FjGT2gA':
                c=cues[first-1]
                cls.gaps.append({'video_id':v,'window_id':w,'cue_index':first,'source_text_private':c.text,'cue_sha256':sha(c.text),
                    'speech_act':'ASSENT','reason_private':'An interjection is not independently certified finance truth.',
                    'negative_gold':False,'review_status':REVIEWED,**{f:False for f in FALSE}})
        for v,w,cid in NEW_SPLITS:
            p=next(x for x in cls.parents if x['video_id']==v and x['window_id']==w and x['parent_id']==cid)
            ix=p['cue_indices'];mid=len(ix)//2
            cls.splits.append({'video_id':v,'window_id':w,'parent_id':cid,'parts':[
                {'cue_indices':ix[:mid],'meaning_private':'Synthetic part one meaning, not an expert conclusion.','gold':False},
                {'cue_indices':ix[mid:],'meaning_private':'Synthetic part two meaning, not an expert conclusion.','gold':False}],
                'review_status':REVIEWED,**{f:False for f in FALSE}})
        prior_v='SYNTHETIC_V101'
        cls.cues[prior_v]=[Cue(i,i*1000,i*1000+900,'SYNTHETIC_PRIOR_CHAT_CUE_'+str(i)) for i in range(1,241)]
        r=[]
        for i in range(1,241):
            w=f'W{((i-1)//40+1):05d}';c=cls.cues[prior_v][i-1]
            context=[{'cue_index':j,'text_private':cls.cues[prior_v][j-1].text} for j in range(max(1,i-2),min(240,i+2)+1)]
            row={'video_id':prior_v,'window_id':w,'cue_index':i,'source_text_private':c.text,'cue_sha256':sha(c.text),
                'context_private':context,'context_sha256':digest(context),'parent_id':f'C{i:05d}'}
            cls.old.append(row);r.append([prior_v,w,i,row['cue_sha256'],row['parent_id'],
                'PRIORITY_PARENT_PENDING' if i<=133 else 'BASELINE_PARENT_PENDING',False,False])
        cls.baseline+=r
        for i in range(15537):
            cls.baseline.append(['SYNTHETIC_OTHER',f'W{(i//40+1):05d}',i+1,sha('leftover synthetic '+str(i)),
                 'SYNTH_PARENT','BASELINE_PARENT_PENDING',False,False])
        assert len(cls.baseline)==15857
        src_receipt=digest(sorted([[r['video_id'],r['window_id'],r['cue_index'],r['cue_sha256'],r['context_sha256']] for r in cls.old]))
        cls.old_receipt={'source_bound_cues_context_reviewed_chat':240,'source_bound_parent_draft_readings_chat':81,
                         'source_bound_gap_speech_acts_chat':7,'source_receipt_sha256':src_receipt,
                         'independent_gold':False,'p0_go':False}
        cls.v96={('sz5N9WJS310',332)}
    def runcheck(self,**overrides):
        data=dict(baseline=self.baseline,v101_selected=self.old,v101_receipt=self.old_receipt,
                  new_selected=self.new,new_parents=self.parents,new_gaps=self.gaps,new_splits=self.splits,
                  cues_by_video=self.cues,registries=self.regs,
                  source_zip_sha=SOURCE_ARCHIVE_SHA,v98_zip_sha=V98_ARCHIVE_SHA,v101_zip_sha=V101_ARCHIVE_SHA,
                  prior_shadow_parent_keys=set(),v96_reviewed_cue_keys=self.v96,v97_windows=set())
        data.update(overrides)
        return reconcile(**data)
    def test_complete_and_no_go(self):
        r,overlay=self.runcheck();self.assertEqual(len(overlay),320);self.assertEqual(r['still_pending_cues'],15537)
        self.assertEqual(r['cumulative_priority_reviewed'],172);self.assertEqual(r['new_v102_cues_not_previously_v96_adjudicated'],79)
        self.assertFalse(r['p0_go']);self.assertFalse(r['independent_gold']);self.assertIsNone(r['certified_recall'])
    def test_overlay_v98_unchanged(self):
        before=digest(self.baseline);r,overlay=self.runcheck();self.assertEqual(digest(self.baseline),before)
        self.assertTrue(all(o['official_knowledge_merged'] is False for o in overlay))
    def test_baseline_deleted(self):
        with self.assertRaises(ValueError):self.runcheck(baseline=self.baseline[:-1])
    def test_baseline_duplicate(self):
        b=copy.deepcopy(self.baseline);b[-1]=b[-2]
        with self.assertRaises(ValueError):self.runcheck(baseline=b)
    def test_baseline_pretend_completed(self):
        b=copy.deepcopy(self.baseline);b[0][6]=True
        with self.assertRaises(ValueError):self.runcheck(baseline=b)
    def test_baseline_pretend_independent(self):
        b=copy.deepcopy(self.baseline);b[0][7]=True
        with self.assertRaises(ValueError):self.runcheck(baseline=b)
    def test_baseline_parent_route_drift(self):
        b=copy.deepcopy(self.baseline);b[0][4]=None
        with self.assertRaises(ValueError):self.runcheck(baseline=b)
    def test_v101_missing(self):
        with self.assertRaises(ValueError):self.runcheck(v101_selected=self.old[:-1])
    def test_v101_stance_faked(self):
        d=copy.deepcopy(self.old_receipt);d['independent_gold']=True
        with self.assertRaises(ValueError):self.runcheck(v101_receipt=d)
    def test_v101_cue_spoof(self):
        d=copy.deepcopy(self.old);d[0]['source_text_private']='tamper'
        with self.assertRaises(ValueError):self.runcheck(v101_selected=d)
    def test_v101_receipt_mismatch(self):
        d=copy.deepcopy(self.old_receipt);d['source_receipt_sha256']='f'*64
        with self.assertRaises(ValueError):self.runcheck(v101_receipt=d)
    def test_new_80_required(self):
        with self.assertRaises(ValueError):self.runcheck(new_selected=self.new[:-1])
    def test_new_cue_sha_spoof(self):
        d=copy.deepcopy(self.new);d[0]['cue_sha256']='f'*64
        with self.assertRaises(ValueError):self.runcheck(new_selected=d)
    def test_new_context_spoof(self):
        d=copy.deepcopy(self.new);d[0]['context_private'][0]['text_private']='spoof'
        with self.assertRaises(ValueError):self.runcheck(new_selected=d)
    def test_new_parent_route_collision(self):
        d=copy.deepcopy(self.new);d[0]['parent_id']='WRONG'
        with self.assertRaises(ValueError):self.runcheck(new_selected=d)
    def test_new_missing_parent_reading(self):
        with self.assertRaises(ValueError):self.runcheck(new_parents=self.parents[:-1])
    def test_new_parent_source_sha_fake(self):
        p=copy.deepcopy(self.parents);p[0]['parent_sha256']='f'*64
        with self.assertRaises(ValueError):self.runcheck(new_parents=p)
    def test_new_parent_fake_gold(self):
        p=copy.deepcopy(self.parents);p[0]['independent_gold']=True
        with self.assertRaises(ValueError):self.runcheck(new_parents=p)
    def test_new_parent_fake_fact_approved(self):
        p=copy.deepcopy(self.parents);p[0]['financial_fact_approved']=True
        with self.assertRaises(ValueError):self.runcheck(new_parents=p)
    def test_new_parent_missing_meaning(self):
        p=copy.deepcopy(self.parents);p[0]['reviewer_scope_caution_private']='bad'
        with self.assertRaises(ValueError):self.runcheck(new_parents=p)
    def test_new_parent_prior_shadow_collision(self):
        p=self.parents[0];key=(p['video_id'],p['window_id'],p['parent_id'])
        with self.assertRaises(ValueError):self.runcheck(prior_shadow_parent_keys={key})
    def test_v96_expected_overlap_only(self):
        with self.assertRaises(ValueError):self.runcheck(v96_reviewed_cue_keys=set())
    def test_v96_unexpected_overlap_rejected(self):
        with self.assertRaises(ValueError):self.runcheck(v96_reviewed_cue_keys={('sz5N9WJS310',332),('4CQ4FjGT2gA',1282)})
    def test_v97_prior_window_rejected(self):
        with self.assertRaises(ValueError):self.runcheck(v97_windows={('4CQ4FjGT2gA','W00033')})
    def test_source_pin_wrong(self):
        with self.assertRaises(ValueError):self.runcheck(source_zip_sha='f'*64)
    def test_v101_pin_wrong(self):
        with self.assertRaises(ValueError):self.runcheck(v101_zip_sha='f'*64)
    def test_v98_pin_wrong(self):
        with self.assertRaises(ValueError):self.runcheck(v98_zip_sha='f'*64)
    def test_gap_missing(self):
        with self.assertRaises(ValueError):self.runcheck(new_gaps=[])
    def test_gap_fake_negative_gold(self):
        g=copy.deepcopy(self.gaps);g[0]['negative_gold']=True
        with self.assertRaises(ValueError):self.runcheck(new_gaps=g)
    def test_split_missing(self):
        with self.assertRaises(ValueError):self.runcheck(new_splits=self.splits[:-1])
    def test_split_mismapped(self):
        s=copy.deepcopy(self.splits);s[0]['parts'][0]['cue_indices']=[999999]
        with self.assertRaises(ValueError):self.runcheck(new_splits=s)
    def test_split_forged_gold(self):
        s=copy.deepcopy(self.splits);s[0]['parts'][0]['gold']=True
        with self.assertRaises(ValueError):self.runcheck(new_splits=s)
    def test_split_unaccounted(self):
        s=copy.deepcopy(self.splits);s[0]['parts'][1]['cue_indices']=s[0]['parts'][0]['cue_indices']
        with self.assertRaises(ValueError):self.runcheck(new_splits=s)
    def test_new_prior_v101_collision(self):
        d=copy.deepcopy(self.old);d[0]=copy.deepcopy(self.new[0])
        with self.assertRaises(ValueError):self.runcheck(v101_selected=d)
    def test_priority_drift(self):
        b=copy.deepcopy(self.baseline);b[0][5]='BASELINE_PARENT_PENDING'
        with self.assertRaises(ValueError):self.runcheck(baseline=b)
if __name__=='__main__':unittest.main()