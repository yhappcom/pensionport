"""Primary-source discovery adapter for *newly generated* financial claims.

Discover candidate URLs via actual Responses API web_search; never cite old
studies. A web citation is NOT verified primary evidence, nor an approval.
External research sends claim text to the configured model provider.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from .source import require
from .evidence import issuer_for

MAX_RESEARCH_RESPONSE=5_000_000


def is_official_candidate(url: str) -> bool:
    """Candidate for independent source fetching, not a truth certificate."""
    return issuer_for(url) is not None


def screen_discovery_response(result: dict, claim_id: str) -> dict:
    """Search tool citations are source *candidates*, not official attestations."""
    require(type(result) is dict and result.get("status")=="completed",
            "WEB_DISCOVERY_RESPONSE_INCOMPLETE")
    items=result.get("output")
    require(type(items) is list and len(items)<=100,
            "WEB_DISCOVERY_OUTPUT_INVALID")
    searches=[o for o in items if type(o) is dict and
              o.get("type")=="web_search_call" and
              o.get("status")=="completed"]
    citations=[]
    for item in items:
        if type(item) is not dict or item.get("type")!="message":
            continue
        for chunk in item.get("content",[]):
            if type(chunk) is not dict or chunk.get("type")!="output_text":
                continue
            for citation in chunk.get("annotations",[]):
                if type(citation) is not dict or citation.get("type")!="url_citation":
                    continue
                url=citation.get("url")
                if is_official_candidate(url):
                    citations.append(url)
    links=sorted(set(citations)) if searches else []
    return {
        "claim_id":claim_id,
        "schema":"IRE_OFFICIAL_DISCOVERY_CANDIDATES_V1",
        "search_executed":bool(searches),
        "official_domain_candidate_urls":links,
        "candidate_count":len(links),
        "publisher_identity_verified":False,
        "document_text_independently_fetched":False,
        "current_statutory_force_verified":False,
        "finance_claim_fact_verified":False,
        "result":"UNVERIFIED_CANDIDATES" if links and searches
                 else "NO_VERIFIABLE_OFFICIAL_DISCOVERY",
    }


def _response_urlopen(req, timeout: int):
    return urllib.request.urlopen(req,timeout=timeout)


def discover_official_candidates(claim: dict, model: str, api_key: str,
                                 timeout_seconds: int = 90,
                                 transport=None) -> dict:
    require(type(claim) is dict and type(claim.get("claim_id")) is str
            and type(claim.get("proposition")) is str,
            "INVALID_OFFICIAL_DISCOVERY_ATOM")
    require(re.fullmatch(r"[a-zA-Z0-9_.:/-]{2,150}",model or "") is not None,
            "INVALID_DISCOVERY_MODEL_ID")
    require(isinstance(api_key,str) and bool(api_key),
            "OFFICIAL_DISCOVERY_API_KEY_MISSING")
    require(type(timeout_seconds) is int and 10<=timeout_seconds<=180,
            "INVALID_DISCOVERY_TIMEOUT")
    # No prior evaluations, knowledge ledger, existing researchers or conclusions.
    prompt={
        "task":"Find *primary* documents for this newly extracted claim.",
        "claim_id":claim["claim_id"],
        "proposition":claim["proposition"],
        "scope":{"jurisdiction":claim["frame"]["jurisdiction"],
                 "effective_date":claim["frame"]["effective_date"],
                 "conditions":claim["frame"]["conditions"],
                 "exceptions":claim["frame"]["exceptions"]},
        "instructions":[
            "Use web search for official issuer, regulator, government, law or exchange pages.",
            "Do not use or mention earlier investment research or old interpretations.",
            "A result is a candidate, not validation of the proposition.",
            "Explain if original material does not establish scope, effective date or exceptions."
        ]
    }
    payload={
        "model":model,
        "store":False,
        "tools":[{"type":"web_search","search_context_size":"medium"}],
        "tool_choice":"required",
        "max_output_tokens":1700,
        "input":[
            {"role":"system","content":
             "Find independent official source candidates only. "
             "Do not approve financial claims; prior studies are forbidden."},
            {"role":"user","content":json.dumps(prompt,ensure_ascii=False)}
        ]
    }
    request=urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        headers={"Authorization":"Bearer "+api_key,
                 "Content-Type":"application/json"},
        method="POST")
    try:
        client=transport or _response_urlopen
        with client(request,timeout_seconds) as response:
            raw=response.read(MAX_RESEARCH_RESPONSE+1)
    except urllib.error.HTTPError as exc:
        raise ValueError("WEB_DISCOVERY_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError) as exc:
        raise ValueError("WEB_DISCOVERY_TRANSPORT_UNAVAILABLE") from None
    require(len(raw)<=MAX_RESEARCH_RESPONSE,"WEB_DISCOVERY_OVERSIZE")
    try:
        body=json.loads(raw)
    except (ValueError,UnicodeError):
        raise ValueError("WEB_DISCOVERY_INVALID_RESPONSE_JSON") from None
    return screen_discovery_response(body,claim["claim_id"])
