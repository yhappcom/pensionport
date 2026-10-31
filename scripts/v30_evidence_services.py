#!/usr/bin/env python3
"""Evidence acquisition/verification and reproducible financial research.

Offline-by-default. Public HTTPS retrieval can be used with an explicit URL,
but network/TLS/issuer claims alone never establish legal applicability.
Documents, dataset provenance, formula assumptions and independent signatures
remain distinct requirements; missing one returns BLOCKED.
"""
import csv
import hashlib
import io
import ipaddress
import json
import math
import re
import socket
import urllib.parse
import urllib.request
from datetime import date
from decimal import Decimal, localcontext
from html.parser import HTMLParser
from pathlib import Path

from v30_verified_core import (
    guard, sha256, canonical, check_privacy, decimal, frame_check,
    verify_attestation, HASH_RE,
)

# Public issuer whitelist is intentionally conservative and configurable by
# program version, not fetched from arbitrary manifest/user request.
PUBLIC_ISSUER_DOMAINS=frozenset((
 "law.go.kr","www.law.go.kr","nts.go.kr","www.nts.go.kr",
 "fss.or.kr","www.fss.or.kr","fsc.go.kr","www.fsc.go.kr",
 "bok.or.kr","www.bok.or.kr","kofia.or.kr","www.kofia.or.kr",
 "krx.co.kr","www.krx.co.kr","nps.or.kr","www.nps.or.kr",
 "kcomwel.or.kr","www.kcomwel.or.kr","data.go.kr","www.data.go.kr",
))
MAX_EXTERNAL_BYTES=4_000_000

class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks=[]
        self.ignored=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"):self.ignored+=1
    def handle_endtag(self,tag):
        if tag in ("script","style"):self.ignored=max(0,self.ignored-1)
    def handle_data(self,data):
        if not self.ignored:self.chunks.append(data)

def safe_public_url(url):
    guard(isinstance(url,str) and len(url)<=2000,
          "PUBLIC_SOURCE_URL_REQUIRED")
    p=urllib.parse.urlparse(url)
    guard(p.scheme=="https" and
          p.username is None and p.password is None and
          p.port in (None,443) and p.hostname in PUBLIC_ISSUER_DOMAINS and
          not p.fragment,"UNTRUSTED_OFFICIAL_PUBLISHER_OR_URL")
    return url

def external_source_fetch(url,timeout=12):
    """Download ONLY explicitly approved official HTTPS host, no auto redirect.

    DNS resolution may still depend on external environment; resolution only
    blocks literal/private results. No public bytes are believed as true law
    without independent issuer/source validation.
    """
    safe_public_url(url)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            raise ValueError("OFFICIAL_REDIRECT_NOT_PREAPPROVED")
    opener=urllib.request.build_opener(NoRedirect)
    req=urllib.request.Request(url,headers={
        "User-Agent":"pensionport-V30-research/1.0",
        "Accept":"text/html,text/plain,application/json,application/pdf"})
    with opener.open(req,timeout=timeout) as resp:
        guard(resp.status==200,"OFFICIAL_FETCH_HTTP_ERROR")
        mime=resp.headers.get_content_type()
        guard(mime in ("text/html","text/plain","application/json",
                       "application/pdf"),
              "UNSUPPORTED_OFFICIAL_CONTENT_TYPE")
        data=resp.read(MAX_EXTERNAL_BYTES+1)
        guard(len(data)<=MAX_EXTERNAL_BYTES,
              "OVERSIZED_OFFICIAL_SOURCE")
    return {"url":url,"mime_type":mime,"sha256":sha256(data),
            "bytes":data,
            "state":"DOWNLOADED_UNREVIEWED_NEVER_AUTO_ACCEPTED"}

def visible_source_text(data,mime):
    guard(isinstance(data,bytes) and len(data)<=MAX_EXTERNAL_BYTES,
          "UNSAFE_OR_TOO_LARGE_EVIDENCE_BYTES")
    guard(mime in ("text/html","text/plain","application/json"),
          "PDF_OR_BINARY_NEEDS_AUTHENTICATED_EXTRACTED_TEXT_AND_PAGE_PROOF")
    text=data.decode("utf-8-sig")
    if mime=="text/html":
        parser=HTMLText()
        parser.feed(text)
        text=" ".join(parser.chunks)
    return " ".join(text.split())

def review_primary_evidence(claim,doc,body,authority=None):
    """Official evidence truth remains pending unless separately attested."""
    frame_check(claim["frame"],claim["claim_types"])
    guard(isinstance(doc,dict) and doc.get("source_id")
          and doc.get("claim_ids") and claim["claim_id"] in doc["claim_ids"],
          "PRIMARY_SOURCE_CLAIM_LINK_MISSING")
    safe_public_url(doc["source_url"])
    guard(type(body) is bytes and len(body)>0 and
          len(body)<=MAX_EXTERNAL_BYTES and
          doc.get("document_sha256")==sha256(body),
          "PRIMARY_SOURCE_EXACT_BYTES_OR_SHA_MISSING")
    mime=doc["mime_type"]
    text=visible_source_text(body,mime)
    quote=" ".join(doc.get("verbatim_quote","").split())
    guard(quote and len(quote)>=8 and quote in text,
          "PRIMARY_SOURCE_EXACT_QUOTE_NOT_IN_DOCUMENT")
    loc=doc.get("exact_location")
    guard(isinstance(loc,str) and len(loc)>=5,
          "PRIMARY_SOURCE_SECTION_OR_PARAGRAPH_REQUIRED")
    start=doc.get("effective_from")
    end=doc.get("effective_to")
    try:
        active_from=date.fromisoformat(start)
        active_to=date.fromisoformat(end) if end is not None else None
        required=date.fromisoformat(claim["frame"]["effective_date"])
    except (TypeError,ValueError) as err:
        raise ValueError("OFFICIAL_SOURCE_LEGAL_EFFECTIVE_DATES_INVALID") from err
    guard(active_from<=required and
          (active_to is None or required<=active_to) and
          (active_to is None or active_to>=active_from),
          "OFFICIAL_SOURCE_OUTSIDE_CLAIM_EFFECTIVE_PERIOD")
    guard(isinstance(doc.get("exceptions_reviewed"),str)
          and len(doc["exceptions_reviewed"])>=12 and
          isinstance(doc.get("applicability_scope"),str)
          and len(doc["applicability_scope"])>=12,
          "OFFICIAL_SOURCE_MISSING_SCOPE_OR_EXCEPTIONS")
    guard(doc.get("jurisdiction")==claim["frame"]["jurisdiction"],
          "OFFICIAL_SOURCE_JURISDICTION_MISMATCH")
    record={
        "source_id":doc["source_id"],"sha256":sha256(body),
        "linked_claim_id":claim["claim_id"],
        "exact_quote_present":True,
        "effective_on_claim_date":True,
        "publisher_url_whitelisted":True,
        "source_authenticity_independently_audited":False,
        "legal_applicability_independently_audited":False,
        "auditor_id":None,
    }
    if authority is not None and doc.get("independent_review"):
        payload={k:record[k] for k in ("source_id","sha256","linked_claim_id")}
        payload.update(source_scope=doc["applicability_scope"],
                       exceptions=doc["exceptions_reviewed"])
        auditor=verify_attestation(doc["independent_review"],payload,
                                   "primary_auditor",authority)
        record.update(source_authenticity_independently_audited=True,
                      legal_applicability_independently_audited=True,
                      auditor_id=auditor)
    record["evidence_status"]=(
        "INDEPENDENTLY_REVIEWED_PRIMARY_SOURCE"
        if record["legal_applicability_independently_audited"]
        else "PENDING_SOURCE_AUTHENTICITY_AND_SCOPE_REVIEW")
    return record

def math_reproduce(model):
    """Two genuinely different numeric methods: analytic and iteration."""
    guard(model.get("model_type") in ("MONTHLY_SAVINGS_FUTURE_VALUE",
                                     "MONTHLY_AMORTIZING_PAYOUT"),
          "UNSUPPORTED_FINANCIAL_FORMULA")
    p=decimal(model["principal_or_monthly_contribution"])
    rate=decimal(model["nominal_annual_rate"])
    n=model["months"]
    guard(type(n) is int and 1<=n<=1200 and
          p>=0 and Decimal("-0.90")<=rate<=Decimal("1") and
          model.get("cashflow_timing")=="END_OF_MONTH" and
          model.get("monthly_rate_convention")=="NOMINAL_ANNUAL_DIVIDED_BY_12",
          "INCOMPATIBLE_FINANCIAL_MODEL_ASSUMPTIONS")
    guard(model.get("currency") in ("KRW","USD","JPY","EUR") and
          model.get("includes_fees_taxes") is False,
          "MISSING_CURRENCY_OR_UNSUPPORTED_TAX_ASSUMPTIONS")
    with localcontext() as ctx:
        ctx.prec=48
        m=rate/Decimal(12)
        if model["model_type"]=="MONTHLY_SAVINGS_FUTURE_VALUE":
            formula=p*n if m==0 else p*((Decimal(1)+m)**n-1)/m
            iterative=Decimal(0)
            for _ in range(n):iterative=iterative*(1+m)+p
        else:
            formula=p/n if m==0 else p*m/(1-(1+m)**(-n))
            # independently calculate annuity present-value factor by
            # summation, instead of duplicating the closed-form formula.
            factor=sum((1+m)**(-i) for i in range(1,n+1))
            iterative=p/factor
        tolerance=max(Decimal("0.01"),abs(formula)*Decimal("0.000000001"))
        guard(abs(formula-iterative)<=tolerance,
              "INDEPENDENT_NUMERIC_REPRODUCTION_FAILED")
        supplied=model.get("asserted_value")
        deviation=(abs(decimal(supplied)-formula) if supplied is not None else None)
        stated_tolerance=decimal(model.get("asserted_tolerance","1"))
        guard(stated_tolerance>=0,"INVALID_NUMERIC_TOLERANCE")
        return {
            "model_type":model["model_type"],
            "formula_value":str(formula.quantize(Decimal("0.01"))),
            "independent_iterative_value":str(iterative.quantize(Decimal("0.01"))),
            "difference":str(abs(formula-iterative)),
            "independent_methods_agree":True,
            "historical_asserted_value_matches_model":(
                deviation<=stated_tolerance if deviation is not None else None),
            "asserted_value_deviation":str(deviation) if deviation is not None else None,
            "model_assumptions_confirmed_by_original_source":False,
            "real_product_contract_validated":False,
            "unit":model["currency"],
            "research_evidence_status":"ARITHMETIC_ONLY_NOT_FINANCIAL_FACT_VERIFIED",
        }

def empirical_reproduce(data,metadata):
    """Recompute actual-supplied reproducible series, not synthetic 'proof'.

    This is a testable evaluation hook; a dataset being supplied does not
    establish an authentic observed public market dataset.
    """
    guard(type(data) is bytes and 0<len(data)<=10_000_000 and
          metadata.get("dataset_sha256")==sha256(data),
          "EMPIRICAL_DATA_BYTES_HASH_MISMATCH")
    guard(metadata.get("real_world_data") is True and
          metadata.get("synthetic_only") is False and
          metadata.get("provider") and metadata.get("source_url")
          and metadata.get("benchmark") and
          metadata.get("costs_and_taxes") and metadata.get("bias_assessment")
          and metadata.get("out_of_sample_definition"),
          "EMPIRICAL_SOURCE_AND_METHOD_REQUIRED")
    safe_public_url(metadata["source_url"])
    try:
        rows=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    except (UnicodeDecodeError,csv.Error) as err:
        raise ValueError("EMPIRICAL_CSV_PARSING_FAILED") from err
    guard(len(rows)>=25,"EMPIRICAL_DATA_TOO_SHORT")
    last=None; v=[];b=[]
    for row in rows:
        try:d=date.fromisoformat(row["date"])
        except (ValueError,KeyError,TypeError) as err:
            raise ValueError("EMPIRICAL_DATE_INVALID") from err
        guard(last is None or d>last,"EMPIRICAL_NONMONOTONIC_DATES")
        last=d
        x=decimal(row["price"]);y=decimal(row["benchmark_price"])
        guard(x>0 and y>0,"INVALID_EMPIRICAL_PRICE")
        v.append(x);b.append(y)
    dts=[decimal(row["price"])/v[i-1]-1 for i,row in enumerate(rows)
         if i>0]
    deltas=[v[i]/v[i-1]-1 for i in range(1,len(v))]
    fees=decimal(metadata.get("round_trip_cost_fraction","0"))
    tax=decimal(metadata.get("tax_rate_on_positive_gain","0"))
    guard(0<=fees<Decimal("0.2") and 0<=tax<Decimal("0.6"),
          "EMPIRICAL_COST_TAX_OUTSIDE_SUPPORTED_MODEL")
    gross=v[-1]/v[0]-1
    net=(v[-1]/v[0])*(1-fees)-1-tax*max(gross,Decimal(0))
    benchmark=b[-1]/b[0]-1
    peak=v[0];drawdown=Decimal(0)
    for q in v:
        peak=max(peak,q)
        drawdown=min(drawdown,q/peak-1)
    ex_start=date.fromisoformat(metadata["out_of_sample_start"])
    guard(rows[1]["date"]<ex_start.isoformat()<
          rows[-2]["date"],"NO_GENUINE_SEPARATE_TEMPORAL_OOS")
    i=next(idx for idx,row in enumerate(rows) if row["date"]>=ex_start.isoformat())
    oos=v[-1]/v[i]-1
    return {
       "source_data_sha256":sha256(data),
       "sample_count":len(rows),
       "gross_cumulative_return":str(gross),
       "cost_and_tax_adjusted_cumulative_return":str(net),
       "benchmark_cumulative_return":str(benchmark),
       "max_drawdown":str(drawdown),
       "out_of_sample_start":ex_start.isoformat(),
       "out_of_sample_cumulative_return":str(oos),
       "cost_model":"ONE_ROUND_TRIP_SPREAD_PLUS_TAX_ON_POSITIVE_ABSOLUTE_GAIN",
       "dataset_issuer_independently_authenticated":False,
       "historical_market_truth_verified_by_internal_math":False,
       "empirical_status":"CALCULATED_FROM_UNTRUSTED_EXTERNALLY_SUPPLIED_DATA",
    }
