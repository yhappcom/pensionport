"""V149 bounded TLS raw-body law capture (no issuer digital-signature claim).

Crawled text, model excerpts, HTML snippets and manually supplied hashes are
NOT a substitute for original HTTPS response bytes. Live failure is HOLD.
All personal eligibility remains unknown until taxpayer/account facts are checked.
"""
from __future__ import annotations
import hashlib,html,json,re,ssl,urllib.request,urllib.parse
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

SPECS={
 'ISA_91_18':{'url':'https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1018255825',
              'article':'제91조의18','law':'조세특례제한법','effective':'2026-09-18',
              'terms':('비과세','400만원','200만원')},
 'PENSION_59_3':{'url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1032951711',
                 'article':'제59조의3','law':'소득세법','effective':'2026-07-01',
                 'terms':('연금저축','600만원','900만원')},
}
class OfficialBodyError(ValueError):pass

class _Visible(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.ignored=0
    def handle_starttag(self,tag,attrs):
        if tag.lower() in {'script','style','noscript'}:self.ignored+=1
    def handle_endtag(self,tag):
        if tag.lower() in {'script','style','noscript'} and self.ignored:self.ignored-=1
    def handle_data(self,data):
        if not self.ignored:self.parts.append(data)

def _visible(raw):
    if type(raw) is not bytes or not 150<=len(raw)<=4*1024*1024:raise OfficialBodyError('BODY_REQUIRED_SIZE')
    try:s=raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:raise OfficialBodyError('BODY_NOT_UTF8') from e
    h=_Visible();h.feed(s)
    return re.sub(r'\s+','',html.unescape(' '.join(h.parts)))

def _hostname(url):
    v=urllib.parse.urlsplit(url)
    if v.scheme!='https' or v.hostname not in {'www.law.go.kr','law.go.kr'} or v.username or v.password or v.port not in (None,443):
        raise OfficialBodyError('NONOFFICIAL_OR_INSECURE_SOURCE')
    return v

def audit_original_bytes(rule_id:str, original_raw:bytes, *,requested_url:str,final_url:str,
                         captured_on:str,as_of:str)->dict:
    """Inspect original bytes without inventing a website signature or personal eligibility."""
    if rule_id not in SPECS:raise OfficialBodyError('RULE_ID_UNRECOGNIZED')
    spec=SPECS[rule_id];_hostname(requested_url);_hostname(final_url)
    if requested_url!=spec['url']:raise OfficialBodyError('WRONG_RULE_URL')
    today=date.fromisoformat(as_of); captured=date.fromisoformat(captured_on)
    if captured>today or today<date.fromisoformat(spec['effective']):raise OfficialBodyError('FUTURE_EFFECTIVE_OR_CAPTURE')
    txt=_visible(original_raw)
    if any(re.sub(r'\s+','',word) not in txt for word in (spec['law'],spec['article'],*spec['terms'])):
        raise OfficialBodyError('ARTICLE_OR_LITERAL_NOT_IN_BYTES')
    effective=spec['effective']
    # The publisher's published effective date must be present *in the exact body*.
    # Search only a stable normalized text pattern; never infer from URL/date alone.
    when=effective.replace('-','.')
    year,month,day=map(int,effective.split('-'))
    pat=rf'\[시행{year}\.{month}\.{day}\.'
    if re.search(pat,txt) is None:
        raise OfficialBodyError('EFFECTIVE_DATE_NOT_IN_ORIGINAL_BYTES')
    return {'schema':'IRE_V149_OFFICIAL_RAW_HTTP_BODY_REPLAY_V1','rule_id':rule_id,
            'requested_url':requested_url,'final_https_url':final_url,
            'body_sha256':hashlib.sha256(original_raw).hexdigest(),
            'byte_count':len(original_raw),'captured_on':captured.isoformat(),
            'assessed_as_of':today.isoformat(),'effective_from':effective,
            'original_http_bytes_locally_rehashed':True,
            'article_and_limit_literals_present_in_original_bytes':True,
            'tls_session_executed_by_this_function':False,
            'issuer_digitally_signed_body_verified':False,
            'individual_account_or_tax_eligibility_verified':False,
            'whole_video_v123_approved':False,'p0_e_go':False}

class _AllowedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        _hostname(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def try_live_fetch(rule_id:str, *,as_of:str='2026-11-16',timeout:float=10, raw_store:Path|None=None)->dict:
    """Verified HTTPS via urllib / standard CA store; raw body is not crawled text.

    Network unavailable/blocked -> explicit HOLD, never cached-text fallback.
    """
    if rule_id not in SPECS:raise OfficialBodyError('UNKNOWN_RULE')
    spec=SPECS[rule_id];_hostname(spec['url'])
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context()),_AllowedRedirect())
    request=urllib.request.Request(spec['url'],headers={'User-Agent':'Mozilla/5.0 (V149-Research-Scope-Verification)', 'Accept-Encoding':'identity','Accept':'text/html'})
    try:
        with opener.open(request,timeout=timeout) as response:
            final=response.geturl();_hostname(final)
            if response.status!=200:raise OfficialBodyError('HTTP_NON_200')
            mime=response.headers.get_content_type()
            if mime not in {'text/html','text/plain'}:raise OfficialBodyError('BAD_CONTENT_TYPE')
            raw=response.read(4*1024*1024+1)
        receipt=audit_original_bytes(rule_id,raw,requested_url=spec['url'],final_url=final,
                                    captured_on=as_of,as_of=as_of)
        receipt['tls_session_executed_by_this_function']=True
        if raw_store is not None:
            folder=Path(raw_store);folder.mkdir(parents=True,exist_ok=True)
            owner_bytes=folder/(rule_id+'.original_http_body.bin')
            owner_bytes.write_bytes(raw)
            if hashlib.sha256(owner_bytes.read_bytes()).hexdigest()!=receipt['body_sha256']:
                raise OfficialBodyError('STORED_RAW_BYTES_CHANGED')
            receipt['original_raw_artifact_filename']=owner_bytes.name
            receipt['original_raw_artifact_rehashed']=True
        receipt['status']='HTTPS_TRANSPORT_RAW_BODY_CAPTURED_SCOPE_REVIEW_STILL_REQUIRED'
        return receipt
    except (OSError,ValueError,TimeoutError) as exc:
        return {'schema':'IRE_V149_OFFICIAL_RAW_HTTP_BODY_REPLAY_V1','rule_id':rule_id,
                'status':'OFFICIAL_RAW_SOURCE_UNAVAILABLE_HOLD','failure_type':type(exc).__name__,
                'body_sha256':None,'original_http_bytes_locally_rehashed':False,
                'issuer_digitally_signed_body_verified':False,
                'individual_account_or_tax_eligibility_verified':False,'p0_e_go':False}

def capture_all(as_of='2026-11-16', raw_dir:Path|None=None)->dict:
    captures=[try_live_fetch(key,as_of=as_of,raw_store=raw_dir) for key in SPECS]
    return {'schema':'IRE_V149_CURRENT_LAW_2_SOURCE_CAPTURE_V1','as_of':as_of,
            'sources':captures,'fetched_raw_body_count':sum(z.get('original_http_bytes_locally_rehashed') is True for z in captures),
            'both_sources_verified':all(z.get('original_http_bytes_locally_rehashed') is True for z in captures),
            'personal_eligibility_verified':False,'issuer_digital_signature_verified':False,
            'p0_e_go':False,'status':'SOURCE_SCOPE_REVIEW_REQUIRED' if all(z.get('original_http_bytes_locally_rehashed') is True for z in captures) else 'HOLD_MISSING_OFFICIAL_RAW_BYTES'}

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--as-of',default='2026-11-16');a.add_argument('--output',type=Path);a.add_argument('--raw-dir',type=Path);args=a.parse_args()
    out=capture_all(args.as_of,args.raw_dir) if args.live else {'status':'HOLD_NO_LIVE_FETCH','as_of':args.as_of,'p0_e_go':False}
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
