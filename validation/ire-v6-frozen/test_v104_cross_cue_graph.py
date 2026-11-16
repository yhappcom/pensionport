import unittest,sys,copy
sys.path.insert(0,__file__.rsplit('/',1)[0])
from v104_cross_cue_graph import tokenize,propose_tax_chain,review_arithmetic,sha,digest
PIN='0'*64

def fixture():
 t=['과거 청년 소득 공제 펀드입니다','600만원을 납입하면','40% 소득 공제해요','그래서 240만원 공제가 됩니다','저는 15% 세율을 가정했습니다','세금 절감은 36만원이었어요','그러면 실효 6% 절세입니다','단점은 3년 동안 상품 변경이 안 됩니다']
 c=[{'index':i+1,'text':x} for i,x in enumerate(t)]
 roles=[('CONTRIBUTION',2,'AMOUNT','6000000','KRW'),('INCOME_DEDUCTION_RATE',3,'RATE','40','%'),('DEDUCTIBLE_BASIS',4,'AMOUNT','2400000','KRW'),('ASSUMED_TAX_RATE',5,'RATE','15','%'),('TAX_SAVING',6,'AMOUNT','360000','KRW'),('EFFECTIVE_SAVING_RATE',7,'RATE','6','%')]
 g={'video_id':'synthetic','source_cue_indices':list(range(1,9)),
 'source_span_sha256':digest([[z['index'],sha(z['text'])] for z in c]),
 'nodes':[{'role':role,'cue_index':i,'cue_sha256':sha(c[i-1]['text']),'kind':kind,'value':num,'unit':unit} for role,i,kind,num,unit in roles],
 'reviewer_scope_note_private':'This is a synthetic arithmetic exercise, not legal advice.',
 'speaker_identity_certified':False,'current_law_approved':False,'independent_gold':False,'p0_go':False}
 return c,g
class TestV104(unittest.TestCase):
 def check(self,c=None,g=None):
  a,b=fixture();return review_arithmetic(b if g is None else g,a if c is None else c,archive_sha256=PIN,expected_archive_sha256=PIN)
 def test_positive_math(self):
  x=self.check();self.assertEqual(x['arithmetic_status'],'ARITHMETIC_CONSISTENT_SCOPE_OPEN');self.assertFalse(x['financial_fact_approved'])
 def test_number_roles_and_provenance(self):
  c,_=fixture();a,b=tokenize(c,video_id='synthetic');self.assertEqual(len(a),7);self.assertTrue(any(x['type']=='HISTORICAL_APPLICABILITY_UNKNOWN' for x in b))
 def test_suggest(self):
  c,_=fixture();a=propose_tax_chain(c,video_id='synthetic',window_id='W00001');self.assertEqual(len(a),1);self.assertFalse(a[0]['current_law_applicability_verified'])
 def test_bad_source(self):
  c,g=fixture();c[0]['text']='tampered'
  with self.assertRaises(ValueError):self.check(c,g)
 def test_bad_graph_sha(self):
  c,g=fixture();g['source_span_sha256']='f'*64
  with self.assertRaises(ValueError):self.check(c,g)
 def test_role_missing(self):
  c,g=fixture();g['nodes']=g['nodes'][:-1];g['nodes']=g['nodes'][:-1]
  with self.assertRaises(ValueError):self.check(c,g)
 def test_wrong_amount(self):
  c,g=fixture();g['nodes'][0]['value']='60000'
  with self.assertRaises(ValueError):self.check(c,g)
 def test_wrong_unit(self):
  c,g=fixture();g['nodes'][0]['unit']='USD'
  with self.assertRaises(ValueError):self.check(c,g)
 def test_duplicate_role(self):
  c,g=fixture();g['nodes'].append(copy.deepcopy(g['nodes'][0]))
  with self.assertRaises(ValueError):self.check(c,g)
 def test_fake_gold(self):
  c,g=fixture();g['independent_gold']=True
  with self.assertRaises(ValueError):self.check(c,g)
 def test_fake_law(self):
  c,g=fixture();g['current_law_approved']=True
  with self.assertRaises(ValueError):self.check(c,g)
 def test_bad_archive_pin(self):
  c,g=fixture()
  with self.assertRaises(ValueError):review_arithmetic(g,c,archive_sha256='f'*64,expected_archive_sha256=PIN)
 def test_multi_cue_drift(self):
  c,g=fixture();c[1]['index']=99
  with self.assertRaises(ValueError):self.check(c,g)
 def test_arithmetic_conflict_open(self):
  c,g=fixture();c[5]['text']='세금 절감은 35만원이었어요';g['nodes'][4]['value']='350000';g['nodes'][4]['cue_sha256']=sha(c[5]['text']);g['source_span_sha256']=digest([[z['index'],sha(z['text'])] for z in c]);self.assertEqual(self.check(c,g)['arithmetic_status'],'ARITHMETIC_CONFLICT_OPEN')
 def test_source_bound_condition(self):
  c,g=fixture();g['scope_context_refs']=[{'cue_index':8,'cue_sha256':sha(c[7]['text']),'role':'CONDITION_TRIGGER','review_note_private':'Synthetic condition needs contract text verification.'}]
  r=self.check(c,g);self.assertEqual(r['condition_trigger_source_count'],1)
 def test_spoof_condition_source(self):
  c,g=fixture();g['scope_context_refs']=[{'cue_index':8,'cue_sha256':'0'*64,'role':'CONDITION_TRIGGER','review_note_private':'Synthetic condition needs contract text verification.'}]
  with self.assertRaises(ValueError):self.check(c,g)
 def test_noncondition_cannot_trigger(self):
  c,g=fixture();g['scope_context_refs']=[{'cue_index':2,'cue_sha256':sha(c[1]['text']),'role':'CONDITION_TRIGGER','review_note_private':'Synthetic condition needs contract text verification.'}]
  with self.assertRaises(ValueError):self.check(c,g)
 def test_context_ref_outside_source(self):
  c,g=fixture();g['scope_context_refs']=[{'cue_index':99,'cue_sha256':'a'*64,'role':'CONDITION_TRIGGER','review_note_private':'Synthetic condition needs contract text verification.'}]
  with self.assertRaises(ValueError):self.check(c,g)
 def test_missing_scope_note(self):
  c,g=fixture();g['reviewer_scope_note_private']=''
  with self.assertRaises(ValueError):self.check(c,g)
 def test_wrong_surface_rate(self):
  c,g=fixture();g['nodes'][1]['value']='100'
  with self.assertRaises(ValueError):self.check(c,g)
if __name__=='__main__':unittest.main()