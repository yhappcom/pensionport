"""V163 B0001 evidence capture: public-source raw HTTPS only, zero approval.

No owner SRT/atom content in the CI workspace. All requests are bounded, TLS
validated, no cross-origin redirect. Owner-only ChatGPT review and native V123
must run separately after the original bytes are available.
"""
from __future__ import annotations
import datetime, hashlib, json, pathlib, ssl, urllib.parse, urllib.request

TARGETS={
    "wiley_dhandho_ch1":(
      "https://catalogimages.wiley.com/images/db/pdf/9780470043899.excerpt.pdf",
      "application/pdf",
      None),
    "korean_library_bibliography":(
      "https://www.ptlib.go.kr/sjsmall/menu/10939/program/30018/plusSearchResultDetail.do?bookKey=1148520178&currentPageNo=1&publishFormCode=BO&recKey=1148520174&searchCategory=ALL&searchOrder=DESC&searchPeriod=1M&searchSort=KEY&searchType=NEW&viewStatus=IMAGE",
      "text/html",
      ("투자를 어떻게 할 것인가","파브라이")),
}
MAX_BYTES=5_000_000

class SameOriginOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        old=urllib.parse.urlsplit(req.full_url)
        new=urllib.parse.urlsplit(newurl)
        if new.scheme!="https" or new.hostname!=old.hostname:
            raise ValueError("V163_CROSS_ORIGIN_REDIRECT")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def capture(out_dir):
    out_dir=pathlib.Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    result={"schema":"V163_B0001_ONLY_PUBLIC_ORIGINAL_HTTPS_BYTES_V1",
            "contains_owner_private_SRT":False,"native_V123_release_authorized":False,
            "V128_knowledge_published":False,"captures":{}}
    opener=urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        SameOriginOnlyRedirect())
    for key,(url,wanted,anchors) in TARGETS.items():
        parsed=urllib.parse.urlsplit(url)
        assert parsed.scheme=="https" and parsed.hostname and not parsed.username
        rec={"requested_url":url,"retrieved_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "original_body_sha256":None,"body_archived":False,"original_source_text_relevant":False}
        try:
            req=urllib.request.Request(url,headers={
                 "User-Agent":"V163-research-origin-20261117/1.0",
                 "Accept":"application/pdf,text/html;q=0.9",
                 "Accept-Encoding":"identity"})
            with opener.open(req,timeout=28) as resp:
                dest=urllib.parse.urlsplit(resp.geturl())
                if dest.hostname!=parsed.hostname or dest.scheme!="https":
                    raise ValueError("V163_FINAL_CROSS_ORIGIN_URL")
                data=resp.read(MAX_BYTES+1)
                if len(data)<200 or len(data)>MAX_BYTES:
                    raise ValueError("V163_UNEXPECTED_ORIGINAL_BODY_SIZE")
                ctype=resp.headers.get_content_type()
                if ctype!=wanted:
                    raise ValueError("V163_ORIGINAL_WRONG_MIME_"+ctype)
                if wanted=="application/pdf":
                    if not data.startswith(b"%PDF-"):
                        raise ValueError("V163_NONPDF_PAYLOAD")
                else:
                    txt=data.decode("utf-8","replace")
                    if not all(x in txt for x in anchors):
                        raise ValueError("V163_BIBLIOGRAPHY_ANCHORS_MISSING")
                suffix=".pdf" if wanted=="application/pdf" else ".html"
                (out_dir/(key+".original-https-body"+suffix)).write_bytes(data)
                rec.update(status="CAPTURED_ORIGINAL_TLS_BODY",final_url=resp.geturl(),
                           content_type=ctype,body_size_bytes=len(data),
                           original_body_sha256=hashlib.sha256(data).hexdigest(),
                           body_archived=True,
                           original_source_text_relevant=(anchors is not None),
                           does_not_certify_investment_returns=True)
        except Exception as exc:
            rec.update(status="HOLD_HTTP_OR_CONTENT",error_type=type(exc).__name__)
        result["captures"][key]=rec
    (out_dir/"V163_B0001_PRIMARY_CAPTURE_RECEIPT.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    import sys
    data=capture(sys.argv[1])
    print(json.dumps({"V123_approved":False,
          "results":{k:{"status":v["status"],"size":v.get("body_size_bytes"),
                         "sha256":v["original_body_sha256"]} for k,v in data["captures"].items()}},
          ensure_ascii=False,sort_keys=True))
