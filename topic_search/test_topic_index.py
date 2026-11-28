import tempfile,unittest,zipfile,sqlite3
from pathlib import Path
from topic_index import build,search,verify,stats,sha,connect

def srt(texts):
    return '\n\n'.join(f'{i}\n00:00:{i:02},000 --> 00:00:{i:02},900\n{t}' for i,t in enumerate(texts,1)).encode()
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.z=self.root/'a.zip';self.db=self.root/'i.db'
        with zipfile.ZipFile(self.z,'w') as z:
            b=srt(['연금','전환','ISA 만기','60일','조건'])
            z.writestr('youtube-transcript-AAAAAAAAAAA.srt',b)
            z.writestr('youtube-transcript-AAAAAAAAAAA (1).srt',b)
            z.writestr('youtube-transcript-BBBBBBBBBBB_public_auto_timed_20261017.srt',srt(['우선주','배당']))
            z.writestr('__MACOSX/._bad.srt',b'junk')
        build(self.db,[self.z])
    def tearDown(self):self.tmp.cleanup()
    def test_dedup(self):self.assertEqual((stats(self.db)['aliases'],stats(self.db)['sources']),(3,2))
    def test_cross_cue(self):self.assertEqual(search(self.db,[['연금전환']])['matched_sources'],1)
    def test_and_or(self):self.assertEqual(search(self.db,[['ISA','ISM'],['60일']])['matched_sources'],1)
    def test_no_match(self):self.assertFalse(search(self.db,[['전혀없는문구']])['results'])
    def test_short(self):self.assertEqual(search(self.db,[['만기']])['matched_sources'],1)
    def test_raw(self):
        a=search(self.db,[['우선주']])['results'][0];self.assertEqual(a['status'],'RAW_UNVERIFIED');self.assertEqual(a['context'][0]['text'],'우선주')
    def test_readonly(self):
        c=connect(self.db)
        try:
            with self.assertRaises(sqlite3.OperationalError):c.execute('DELETE FROM sources')
        finally:c.close()
    def test_verify(self):self.assertEqual(verify(self.db)['verified_sources'],2)
    def test_no_overwrite(self):
        h=sha(self.db.read_bytes());self.assertRaises(ValueError,build,self.db,[self.z]);self.assertEqual(h,sha(self.db.read_bytes()))
    def test_bad_archive(self):
        bad=self.root/'bad.zip';bad.write_bytes(b'not zip');dest=self.root/'failed.db';self.assertRaises(zipfile.BadZipFile,build,dest,[bad]);self.assertFalse(dest.exists());self.assertFalse(dest.with_suffix('.db.building').exists())
    def test_invalid_query(self):
        for g in [[],[['가']],[['연금'],['연금']],['연금']]:self.assertRaises(ValueError,search,self.db,g)
    def test_replay(self):
        dst=self.root/'second.db';build(dst,[self.z]);self.assertEqual(sha(self.db.read_bytes()),sha(dst.read_bytes()))
if __name__=='__main__':unittest.main()
