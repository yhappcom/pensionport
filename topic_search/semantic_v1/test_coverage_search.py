import tempfile,unittest,zipfile,sys
from pathlib import Path
R=Path(__file__).resolve().parent;BASE=R.parent/'c1_topic' if (R.parent/'c1_topic'/'topic_index.py').exists() else R.parent;sys.path.insert(0,str(BASE))
from topic_index import build, sha, search
from coverage_search import CoverageSearch

def srt(texts):
 return '\n\n'.join(f'{i}\n00:{i//60:02}:{i%60:02},000 --> 00:{i//60:02}:{i%60:02},900\n{t}' for i,t in enumerate(texts,1)).encode()
class CoverageTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.db=root/'i.db';z=root/'s.zip';ts=['배경']*55;ts[2]='달러 RP';ts[25]='IS 계좌';ts[33]='매수';ts[40]='돈을 남기는 심리';
  with zipfile.ZipFile(z,'w') as f:
   f.writestr('youtube-transcript-AAAAAAAAAAA.srt',srt(ts));f.writestr('youtube-transcript-BBBBBBBBBBB.srt',srt(['돈이 아닌 다른 사례','소비']))
  build(self.db,[z]);self.c=CoverageSearch(self.db)
 def tearDown(self):self.tmp.cleanup()
 def test_distributed_terms_alias(self):
  q=[['달러 RP'],['ISA'],['매수']];self.assertEqual(search(self.db,q)['matched_sources'],0);r=self.c.inventory(q);self.assertEqual(r['matched_sources'],1);self.assertEqual(r['status'],'RAW_UNVERIFIED')
 def test_single_char_with_selective_term(self):self.assertEqual(self.c.inventory([['돈'],['심리']])['matched_sources'],1)
 def test_single_char_alone_rejected(self):self.assertRaises(ValueError,self.c.inventory,[['돈']])
 def test_context(self):
  r=self.c.inventory([['달러 RP'],['ISA'],['매수']])['results'][0];ctx=self.c.context(r);self.assertLessEqual(ctx[0]['cue'],3);self.assertGreaterEqual(ctx[-1]['cue'],34);self.assertEqual(ctx[2]['text'],'달러 RP')
 def test_deterministic_readonly(self):
  h=sha(self.db.read_bytes());q=[['배경']];self.assertEqual(self.c.inventory(q),CoverageSearch(self.db).inventory(q));self.assertEqual(h,sha(self.db.read_bytes()))
 def test_no_hit(self):self.assertFalse(self.c.inventory([['존재하지않는표현']])['results'])
 def test_all_windows_not_capped(self):self.assertGreater(self.c.inventory([['배경']])['matched_windows'],1)
if __name__=='__main__':unittest.main()
