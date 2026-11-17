"""Capture raw HTTPS response bytes from two *public* primary-source web pages.

Use only with public URLs and in a disposable CI workspace. Full source bodies
are external copyrighted web content: retain for bounded verification only,
never publish user-private SRT or falsely certify current financial rules.
"""
from __future__ import annotations
import datetime, hashlib, json, pathlib, ssl, urllib.parse, urllib.request

TARGETS={
 'wiley_book_2007':'https://www.wiley-vch.de/en/areas-interest/finance-economics-law/finance-investments-13fi/investments-securities-13fi3/the-dhandho-investor-978-0-470-04389-9',
 'skhynix_fy2017':'https://news.skhynix.com/en/sk-hynix-inc-reports-fiscal-year-2017-and-fourth-quarter-results/',
}
ALLOWED={'www.wiley-vch.de','news.skhynix.com'}
MAX_BYTES=2_000_000

class SameIssuerOnlyRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  url=urllib.parse.urlsplit(newurl)
  if url.scheme!='https' or url.hostname!=urllib.parse.urlsplit(req.full_url).hostname:
   raise ValueError('CROSS_ORIGIN_REDIRECT_REJECTED')
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_public_pages(out_dir):
 out_dir=pathlib.Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
 result={'schema':'V162_ORIGINAL_HTTPS_PUBLIC_ISSUER_BODY_ATTEMPT',
         'source_capture_not_claim_truth_certification':True,
         'source_audio_verified':False,
         'V123_claim_approved':False,
         'V128_knowledge_published':False,
         'captures':{}}
 opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context()),SameIssuerOnlyRedirect())
 for key,url in TARGETS.items():
  parsed=urllib.parse.urlsplit(url)
  assert parsed.scheme=='https' and parsed.hostname in ALLOWED and not parsed.username
  entry={'requested_url':url,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'original_http_body_archived':False,'raw_body_sha256':None,
         'factual_claims_chat_verified':False,'personal_financial_advice_approved':False}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'V162-research-original-proof/1.0',
                                                'Accept':'text/html','Accept-Encoding':'identity'})
   with opener.open(req,timeout=25) as resp:
    actual_url=resp.geturl();actual_parsed=urllib.parse.urlsplit(actual_url)
    if actual_parsed.scheme!='https' or actual_parsed.hostname!=parsed.hostname:
     raise ValueError('FINAL_URL_ORIGIN_MISMATCH')
    content_type=resp.headers.get_content_type()
    if content_type not in {'text/html','application/xhtml+xml'}:raise ValueError('UNEXPECTED_CONTENT_TYPE')
    data=resp.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES or len(data)<1000:raise ValueError('UNEXPECTED_BODY_SIZE')
    decoded=data.decode('utf-8','replace')
    checks={'wiley_book_2007':['Dhandho','Pabrai','Patel'],
            'skhynix_fy2017':['2017','13.72','data center']}
    if not all(x.lower() in decoded.lower() for x in checks[key]):
     raise ValueError('PRIMARY_SOURCE_EXPECTED_ANCHORS_MISSING')
    path=out_dir/(key+'.raw-response.html');path.write_bytes(data)
    entry.update({'status':'FETCHED_RAW_HTTPS_BYTES_UNDER_DOMAIN_TLS',
                  'final_url':actual_url,'http_status':resp.status,
                  'content_type':content_type,
                  'body_size_bytes':len(data),
                  'raw_body_sha256':hashlib.sha256(data).hexdigest(),
                  'original_http_body_archived':True,
                  'source_page_relevance_anchors_found':True})
  except Exception as e:
   entry.update(status='HOLD_PRIMARY_HTTP_FETCH_FAILED',error_class=type(e).__name__)
  result['captures'][key]=entry
 (out_dir/'V162_OFFICIAL_HTTP_CAPTURE_RECEIPT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result

if __name__=='__main__':
 import sys
 output=fetch_public_pages(sys.argv[1] if len(sys.argv)>1 else '/tmp/v162_public_official_capture')
 print(json.dumps({'schema':output['schema'],'captures':{
  k:{'status':v['status'],'raw_body_sha256':v['raw_body_sha256'],
     'body_size_bytes':v.get('body_size_bytes',0)} for k,v in output['captures'].items()}},sort_keys=True))
