"""Synthetic archive-custody controls; not proof of live issuer authenticity."""
import copy
import io
import json
import unittest
from zipfile import ZipFile
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.public_origin import replay_public_origin_archive


class PublicOriginTests(unittest.TestCase):
    def setUp(self):
        self.body=b'<html>Illustrative official source only</html>'
        self.url='https://kind.krx.co.kr/example.html'
        self.commit='a'*40
        self.row={'key':'KIND_EXAMPLE','requested_url':self.url,'final_url':self.url,
                  'http_status':200,'content_type':'text/html','date_header':None,
                  'sha256':sha256(self.body),'bytes':len(self.body),'transport':'HTTPS_STDLIB_DEFAULT_TLS',
                  'semantic_document_content_verified':False,'effective_date_verified':False,'v123_approved':False}
        self.receipt={'schema':'IRE_R304_PUBLIC_ORIGIN_CAPTURE_V1','code_commit':self.commit,
                      'captured_utc':'2026-11-26T05:47:47+00:00','results':[self.row],
                      'private_source_uploaded':False,'finance_fact_approved':False,'p0_go':False}

    def archive(self, extra=None, body=None):
        fp=io.BytesIO()
        with ZipFile(fp,'w') as z:
            z.writestr('receipt.json',json.dumps(self.receipt))
            z.writestr('KIND_EXAMPLE.html',self.body if body is None else body)
            if extra:z.writestr(extra,b'extra')
        return fp.getvalue()

    def replay(self, raw=None, expected=None, commit=None):
        raw=self.archive() if raw is None else raw
        return replay_public_origin_archive(raw,expected_archive_sha256=expected or sha256(raw),
                                             expected_commit=commit or self.commit)

    def test_valid_archive_is_not_finance_approval(self):
        r=self.replay();self.assertEqual(r['bodies'][self.url]['body'],self.body)
        self.assertFalse(r['issuer_authenticity_independently_verified']);self.assertFalse(r['finance_fact_approved'])

    def test_official_listing_site_without_approval(self):
        self.url='https://listing.krx.co.kr/contents/LST/06/06010600/LST06010600.jsp'
        self.row.update(requested_url=self.url,final_url=self.url)
        r=self.replay();self.assertEqual(r['bodies'][self.url]['body'],self.body)
        self.assertFalse(r['finance_fact_approved'])
        self.row['final_url']='https://listing.krx.co.kr.example.org/fake'
        with self.assertRaisesRegex(InvalidInput,'PUBLIC_ORIGIN_URL'):self.replay()

    def test_pin_drift(self):
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_BYTES'):self.replay(expected='0'*64)

    def test_body_drift_with_repacked_archive(self):
        with self.assertRaisesRegex(InvalidInput,'BODY_HASH'):self.replay(self.archive(body=self.body+b'X'))

    def test_commit_drift(self):
        with self.assertRaisesRegex(InvalidInput,'RECEIPT'):self.replay(commit='b'*40)

    def test_redirect_outside_issuer(self):
        self.row['final_url']='https://example.org/fake'
        with self.assertRaisesRegex(InvalidInput,'PUBLIC_ORIGIN_URL'):self.replay()

    def test_extra_members(self):
        with self.assertRaisesRegex(InvalidInput,'UNACCOUNTED_MEMBER'):self.replay(self.archive(extra='OTHER.html'))

    def test_path_traversal(self):
        with self.assertRaisesRegex(InvalidInput,'ZIP_CENSUS'):self.replay(self.archive(extra='../KIND.html'))

    def test_false_approval(self):
        self.row['v123_approved']=True
        with self.assertRaisesRegex(InvalidInput,'ROW_SCHEMA'):self.replay()

    def test_duplicate_census(self):
        self.receipt['results'].append(copy.deepcopy(self.row))
        with self.assertRaisesRegex(InvalidInput,'ROW_IDENTITY'):self.replay()
