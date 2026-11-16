"""Synthetic multi-window full-source scheduler tests. No owner text."""
import unittest,copy
from dataclasses import dataclass
from v98_full_source_hybrid_queue import full_source_hybrid,check_full_source_public_receipt
from v98_hybrid_source_guard import sha

@dataclass
class Cue:
 index:int
 start_ms:int
 end_ms:int
 text:str

class TestV98Full(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cues={'SYNTH_A':[Cue(i,i*100,i*100+90,f'SYNTH cue {i}') for i in range(1,81)],
            'SYNTH_B':[Cue(i,i*200,i*200+190,f'SYNTH other {i}') for i in range(1,26)]}
  cls.regs={};cls.flags={}
  for vid,cues in cls.cues.items():
   cls.regs[vid]={}
   for w,first in enumerate(range(1,len(cues)+1,40),1):
    last=min(first+39,len(cues));ids=[i for i in range(first,last+1) if i!=first+2]
    cls.regs[vid][f'W{w:05d}']=[{'claim_id':f'C{w:05d}',
      'cue_indices':ids,'source_text_sha256':sha(' | '.join(cues[i-1].text for i in ids))}]
   cls.flags[vid]=[{'cue_index':7,'kind':'QUALIFIER_REVIEW','cue_sha256':sha(cues[6].text)}] if vid=='SYNTH_A' else []
  cls.hash='f'*64
  cls.ok=full_source_hybrid(cls.cues,cls.regs,cls.flags,expected_source_sha=cls.hash,
                           source_archive_sha=cls.hash,include_private_queue=True)
 def verify(self,cues=None,regs=None,flags=None,**kw):
  return full_source_hybrid(self.cues if cues is None else cues,
    self.regs if regs is None else regs,self.flags if flags is None else flags,
    expected_source_sha=self.hash,source_archive_sha=kw.pop('archive_sha',self.hash),**kw)
 def test_105_cues_all_pending(self):
  x=self.ok;self.assertEqual(x['source_cues_routed'],105);self.assertEqual(x['original_windows'],3)
  self.assertTrue(x['source_first_all_cues_routed']);self.assertFalse(x['source_first_full_semantic_review_completed'])
 def test_unassigned_one_per_window(self):self.assertEqual(self.ok['unassigned_cues_pending'],3)
 def test_signal_free_all_baseline(self):self.assertEqual(self.ok['per_video']['SYNTH_B']['priority_cues'],0)
 def test_prioritize_in_window_only(self):self.assertEqual(self.ok['per_video']['SYNTH_A']['priority_cues'],14)
 def test_zero_signal_windows(self):self.assertEqual(self.ok['zero_signal_windows'],2)
 def test_private_not_in_receipt(self):
  x={k:v for k,v in self.ok.items() if not k.startswith('private_')}
  self.assertTrue(check_full_source_public_receipt(x,self.ok))
 def test_false_completion(self):
  x={k:v for k,v in self.ok.items() if not k.startswith('private_')};x['source_first_full_semantic_review_completed']=True
  with self.assertRaises(ValueError):check_full_source_public_receipt(x,self.ok)
 def test_false_precision(self):
  x={k:v for k,v in self.ok.items() if not k.startswith('private_')};x['certified_precision']=.99
  with self.assertRaises(ValueError):check_full_source_public_receipt(x,self.ok)
 def test_modified_routing(self):
  x={k:v for k,v in self.ok.items() if not k.startswith('private_')};x['priority_cues']=105
  with self.assertRaises(ValueError):check_full_source_public_receipt(x,self.ok)
 def test_missing_cue(self):
  a=copy.deepcopy(self.cues);a['SYNTH_A'].pop()
  with self.assertRaises(ValueError):self.verify(cues=a)
 def test_malformed_timestamp(self):
  a=copy.deepcopy(self.cues);a['SYNTH_A'][0].end_ms=-4
  with self.assertRaises(ValueError):self.verify(cues=a)
 def test_wrong_parent_hash(self):
  a=copy.deepcopy(self.regs);a['SYNTH_A']['W00001'][0]['source_text_sha256']='0'*64
  with self.assertRaises(ValueError):self.verify(regs=a)
 def test_global_claim_id_repeated_across_windows(self):
  a=copy.deepcopy(self.regs)
  a["SYNTH_A"]["W00002"][0]["claim_id"]="C00001"
  with self.assertRaises(ValueError):self.verify(regs=a)
 def test_parent_overlap(self):
  a=copy.deepcopy(self.regs);a['SYNTH_A']['W00001'].append(a['SYNTH_A']['W00001'][0].copy());a['SYNTH_A']['W00001'][-1]['claim_id']='OTHER'
  with self.assertRaises(ValueError):self.verify(regs=a)
 def test_missing_parent_window(self):
  a=copy.deepcopy(self.regs);del a['SYNTH_A']['W00002']
  with self.assertRaises(ValueError):self.verify(regs=a)
 def test_forged_alert(self):
  a=copy.deepcopy(self.flags);a['SYNTH_A'][0]['cue_sha256']='a'*64
  with self.assertRaises(ValueError):self.verify(flags=a)
 def test_duplicate_alert(self):
  a=copy.deepcopy(self.flags);a['SYNTH_A'].append(a['SYNTH_A'][0])
  with self.assertRaises(ValueError):self.verify(flags=a)
 def test_wrong_archive(self):
  with self.assertRaises(ValueError):self.verify(archive_sha='0'*64)
 def test_public_privacy(self):
  x={k:v for k,v in self.ok.items() if not k.startswith('private_')};x['private_pending_cue_routes']=[1]
  with self.assertRaises(ValueError):check_full_source_public_receipt(x,self.ok)

if __name__=='__main__':unittest.main()