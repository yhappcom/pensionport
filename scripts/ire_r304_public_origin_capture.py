"""Capture bounded public issuer response bytes, never certify their meaning.

Run on the existing integration branch's GitHub Actions host when the local
ChatGPT execution environment lacks direct HTTPS. No private transcript,
portfolio, claim or credential is supplied. The artifact is public-source-only.
"""
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import ssl
import sys
import urllib.parse
import urllib.request

URLS = {
    'LAW234':'https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000932974',
    'DEC262':'https://law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=62257',
    'FSC':'https://www.fsc.go.kr/no010101/86178?srchKey=sj&srchText=ETF',
    'KIND_LP':'https://kind.krx.co.kr/external/2025/07/11/000008/20250711000003/68648.htm',
    'KIND_FX':'https://kind.krx.co.kr/external/2026/04/02/000081/20260402000099/68648.htm',
    'KIND_PRODUCT':'https://kind.krx.co.kr/disclosure/etfisudetail.do?isuCd=KR7133690008&menuIndex=0&method=searchEftIsuDetail',
    'KRX_TE':'https://pdf.krx.co.kr/ebook_new/access/ecatalogt.jsp?Dir=23&callmode=normal&catimage=&eclang=ko&start=37&um=s',
    'KIND_ETN':'https://kind.krx.co.kr/external/2026/06/02/000078/20260601002266/68319.htm',
}
HOSTS = {'www.law.go.kr','law.go.kr','www.fsc.go.kr','fsc.go.kr',
         'kind.krx.co.kr','pdf.krx.co.kr','www.krx.co.kr','krx.co.kr'}
LIMIT = 2_500_000


def check_url(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password or u.port not in (None,443):
        raise ValueError('UNAPPROVED_HTTPS_ORIGIN')


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def capture(key, url, root):
    try:
        check_url(url)
        opener=urllib.request.build_opener(OfficialRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 IRE public evidence capture',
                    'Accept':'text/html,application/xhtml+xml','Accept-Encoding':'identity'})
        with opener.open(req,timeout=15) as resp:
            final=resp.geturl();check_url(final)
            mime=resp.headers.get('Content-Type','')
            if resp.status!=200 or not any(t in mime.lower() for t in ('text/html','application/xhtml+xml')):
                raise ValueError('INVALID_HTTP_RESPONSE')
            if resp.headers.get('Content-Encoding','identity').lower() not in ('','identity'):
                raise ValueError('NON_IDENTITY_CONTENT_ENCODING')
            body=resp.read(LIMIT+1)
            if not 0<len(body)<=LIMIT:raise ValueError('EMPTY_OR_OVERSIZE_RESPONSE')
            (root/(key+'.html')).write_bytes(body)
            return {'key':key,'requested_url':url,'final_url':final,'http_status':resp.status,
                    'content_type':mime,'date_header':resp.headers.get('Date'),
                    'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),
                    'transport':'HTTPS_STDLIB_DEFAULT_TLS','semantic_document_content_verified':False,
                    'effective_date_verified':False,'v123_approved':False}
    except Exception as exc:
        return {'key':key,'requested_url':url,'failed_closed':True,
                'error_type':type(exc).__name__,'reason':str(exc)[:240]}


def main():
    root=pathlib.Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda kv:capture(*kv,root), URLS.items()))
    receipt={'schema':'IRE_R304_PUBLIC_ORIGIN_CAPTURE_V1','code_commit':os.getenv('GITHUB_SHA'),
             'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'results':results,'private_source_uploaded':False,'finance_fact_approved':False,
             'p0_go':False}
    (root/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    return 1 if any(r.get('failed_closed') for r in results) else 0


if __name__=='__main__':
    sys.exit(main())
