import unittest,copy
from v92_lineage_gate import verify_lineage,COUNT_BY_VERSION,digest
VIDS=['sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ']
class T(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=[];cls.sources={};
  for v,ct in COUNT_BY_VERSION.items():
   for i in range(ct):
    g='FIRST_FIVE' if v<=82 else 'VIDEO7';idx=sum(c for key,c in COUNT_BY_VERSION.items() if key<v and ((key<=82)==(v<=82)))+i
    vn=(idx%5)+1 if g=='FIRST_FIVE' else 7;vid=VIDS[vn-1] if vn<7 else '4CQ4FjGT2gA';w=f'W{idx%70+1:05d}' if vn==7 else f'W{idx%30+1:05d}';c=f'C{idx+1:05d}';src=digest([v,idx]);row={'version':v,'video_no':vn,'video_id':vid,'window_id':w,'claim_id':c,'cue_indices':[idx+1],'source_sha256':src,'cohort':g,**{x:False for x in ('fact_approved','independent_gold','personal_action_approved','official_parent_merged')}}
    cls.rows.append(row);cls.sources[(vid,w,c)]={'cue_indices':[idx+1],'source_sha256':src}
 def check(self,rows=None,sources=None,**kw):return verify_lineage(self.rows if rows is None else rows,self.sources if sources is None else sources,**kw)
 def test_valid_no_go(self):
  x=self.check();self.assertEqual(x['unique_source_claims'],390);self.assertFalse(x['p0_go']);self.assertIn('UNAVAILABLE',x['v75_recovery_state'])
 def test_missing(self):
  with self.assertRaises(ValueError):self.check(rows=self.rows[:-1])
 def test_duplicate(self):
  z=copy.deepcopy(self.rows);z[-1]=z[-2]
  with self.assertRaises(ValueError):self.check(rows=z)
 def test_wrong_original_hash(self):
  z=copy.deepcopy(self.rows);z[0]['source_sha256']='0'*64
  with self.assertRaises(ValueError):self.check(rows=z)
 def test_wrong_cue(self):
  z=copy.deepcopy(self.rows);z[0]['cue_indices']=[22]
  with self.assertRaises(ValueError):self.check(rows=z)
 def test_promote_rejected(self):
  z=copy.deepcopy(self.rows);z[0]['fact_approved']=True
  with self.assertRaises(ValueError):self.check(rows=z)
 def test_wrong_cohort(self):
  z=copy.deepcopy(self.rows);z[0]['cohort']='VIDEO7'
  with self.assertRaises(ValueError):self.check(rows=z)
 def test_historical_claim_not_certified(self):
  x=self.check(v75_original={'trusted_historical_custody':True},expected_older_ledger={'trusted_historical_custody':True});self.assertFalse(x['v75_parent_membership_verified'])
 def test_historical_fake_attestation(self):
  with self.assertRaises(ValueError):self.check(v75_original={},expected_older_ledger={})
if __name__=='__main__':unittest.main()