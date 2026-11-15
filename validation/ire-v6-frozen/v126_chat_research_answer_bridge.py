"""V126.2 private host-ChatGPT Q&A bridge over cumulative research evidence.

No LLM or internet calls here. ChatGPT writes/reviews the answer in the chat and
supplies claim-specific *original* official-body bytes for financial statements.
This checks provenance and completeness, NOT government HTTP authenticity or
semantic correctness. Does not authorize personal orders/portfolio advice.
"""
from __future__ import annotations

from datetime import date
from html import unescape
from urllib.parse import urlsplit
import re

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven

OFFICIAL_HOSTS = frozenset({"law.go.kr", "www.law.go.kr", "nts.go.kr", "www.nts.go.kr",
                          "fsc.go.kr", "www.fsc.go.kr", "moel.go.kr", "www.moel.go.kr",
                          "kofia.or.kr", "www.kofia.or.kr", "www.bok.or.kr", "bok.or.kr",
                          "korea.kr", "www.korea.kr", "krx.co.kr", "www.krx.co.kr"})
HASH = re.compile(r"[0-9a-f]{64}\Z")
EXECUTE = re.compile(r"(?:매수|매도|이체|송금|주문|출금).{0,15}(?:대신\s*실행|해\s*줘|해주세요)")


def _block(code):
    raise QualityNotProven("V126_CHAT_ANSWER_" + code)


def _on_date(value, code):
    if type(value) is not str:
        _block(code)
    try:
        got = date.fromisoformat(value)
        if got.isoformat() != value:
            _block(code)
        return got
    except ValueError:
        _block(code)


def _visible(raw):
    content = raw.decode("utf-8-sig",errors="strict")
    # Only a literal source-quote check. Untrusted web HTML cannot instruct the chat.
    return re.sub(r"\s+", "", unescape(re.sub(r"<[^>]+>", " ", content)))


def prepare_question_packet(store, question, *, selected_knowledge_ids, as_of):
    """Explicit ChatGPT-selected active records, never untrusted automatic relevance."""
    _on_date(as_of,"QUESTION_AS_OF_INVALID")
    ev = store.evidence_for_question(question,selected_knowledge_ids=selected_knowledge_ids)
    if not ev["claims"]:
        _block("NO_APPROVED_RESEARCH_CANDIDATES")
    return {"schema":"IRE_V126_CHAT_RESEARCH_QUESTION_PACKET_V1",
            "question":question,"as_of":as_of,
            "evidence":ev,"evidence_sha256":json_digest(ev),
            "issuer_primary_body_refresh_needed":ev["financial_claims_requiring_current_primary_source"]>0,
            "chat_reviewer_required":True,
            "personal_portfolio_not_integrated":True,
            "p0_go":False}


def check_chat_research_answer(store, packet, *, answer_text, chat_answer_review,
                               primary_bodies):
    """Fail closed on stale source / unrelated law / missing ChatGPT answer review."""
    if type(packet) is not dict or packet.get("schema")!="IRE_V126_CHAT_RESEARCH_QUESTION_PACKET_V1":
        _block("QUESTION_PACKET_SCHEMA_INVALID")
    q=packet.get("question")
    ev=packet.get("evidence")
    if (type(q) is not str or type(ev) is not dict or not ev.get("claims") or
            packet.get("evidence_sha256")!=json_digest(ev)):
        _block("QUESTION_OR_EVIDENCE_DRIFT")
    if store.audit()["head_sha256"]!=ev["knowledge_head_sha256"]:
        _block("PRIVATE_KNOWLEDGE_HEAD_STALE")
    claims={x["knowledge_id"]:x for x in ev["claims"]}
    if len(claims)!=len(ev["claims"]):
        _block("EVIDENCE_DUPLICATE")
    check=store.evidence_for_question(q,selected_knowledge_ids=sorted(claims))
    if {x["knowledge_id"]:x for x in check["claims"]}!=claims:
        _block("KNOWLEDGE_TOMBSTONED_OR_MODIFIED")
    if (type(answer_text) is not str or not 30<=len(answer_text)<=12000 or
            EXECUTE.search(answer_text)):
        _block("ANSWER_NOT_SAFE_OR_MISSING")
    review=chat_answer_review
    required={"schema","review_executor","question_sha256","evidence_sha256",
              "answer_sha256","as_of","selected_knowledge_ids","source_first_checked",
              "counterexamples_checked","no_personal_order_execution",
              "no_formal_financial_fact_approval","chat_private_review_sha256"}
    if (type(review) is not dict or set(review)!=required or
            review.get("schema")!="IRE_V126_CHAT_RESEARCH_ANSWER_REVIEW_V1" or
            review.get("review_executor")!="CHATGPT_IN_CHAT" or
            review.get("question_sha256")!=sha256(q.encode("utf-8")) or
            review.get("evidence_sha256")!=packet["evidence_sha256"] or
            review.get("answer_sha256")!=sha256(answer_text.encode("utf-8")) or
            review.get("as_of")!=packet["as_of"] or
            review.get("selected_knowledge_ids")!=sorted(claims) or
            any(review.get(k) is not True for k in ("source_first_checked",
                                                      "counterexamples_checked",
                                                      "no_personal_order_execution",
                                                      "no_formal_financial_fact_approval")) or
            type(review.get("chat_private_review_sha256")) is not str or
            HASH.fullmatch(review["chat_private_review_sha256"]) is None):
        _block("CHAT_FINAL_ANSWER_REVIEW_MISSING_OR_UNBOUND")
    current=_on_date(packet["as_of"],"CURRENT_DATE_REQUIRED")
    if type(primary_bodies) is not dict:
        _block("OFFICIAL_PRIMARY_BODY_MAP_REQUIRED")
    financial={kid for kid,c in claims.items() if c["finance_current_law_review_required"]}
    if set(primary_bodies)!=financial:
        _block("FINANCE_CLAIM_BODY_CENSUS_MISMATCH")
    citations=[]
    for kid in sorted(financial):
        src=primary_bodies[kid]
        if type(src) is not dict or set(src)!={"url","body","body_sha256",
                                                "effective_from","captured_on",
                                                "literal_source_quote",
                                                "claim_scope_chat_reviewed"}:
            _block("OFFICIAL_PRIMARY_BODY_SCHEMA")
        url=urlsplit(src["url"]) if type(src.get("url")) is str else None
        if (url is None or url.scheme!="https" or url.hostname not in OFFICIAL_HOSTS or
                url.username or url.password or url.port not in (None,443)):
            _block("NOT_ALLOWLISTED_OFFICIAL_ISSUER")
        raw=src["body"]
        if (type(raw) is not bytes or not 1<=len(raw)<=8*1024*1024 or
                src["body_sha256"]!=sha256(raw) or
                src["claim_scope_chat_reviewed"] is not True):
            _block("PRIMARY_BYTE_OR_CHAT_SCOPE_NOT_VERIFIED")
        effective=_on_date(src["effective_from"],"LAW_EFFECTIVE_DATE_REQUIRED")
        captured=_on_date(src["captured_on"],"CAPTURE_DATE_REQUIRED")
        if effective>current or captured>current:
            _block("FUTURE_LAW_OR_SOURCE_CAPTURE")
        quote=src["literal_source_quote"]
        if type(quote) is not str or len(quote.strip())<5 or re.sub(r"\s+","",quote) not in _visible(raw):
            _block("LAW_EXCERPT_NOT_IN_ORIGINAL_BODY")
        citations.append({"knowledge_id":kid,"official_url":src["url"],
                          "body_sha256":src["body_sha256"],
                          "effective_from":src["effective_from"]})
    return {"schema":"IRE_V126_CHAT_VETTED_GENERAL_ANSWER_V1",
            "status":"CHAT_RESEARCH_ANSWER_REVIEWED_NOT_PERSONAL_ADVICE",
            "answer_text":answer_text,"question_sha256":sha256(q.encode("utf-8")),
            "current_as_of":packet["as_of"],
            "knowledge_head_sha256":ev["knowledge_head_sha256"],
            "selected_knowledge_ids":sorted(claims),
            "chat_answer_review_sha256":json_digest(review),
            "official_primary_sources_rehashed":citations,
            "issuer_http_origination_independently_verified":False,
            "independent_semantic_recall_verified":False,
            "personal_account_or_trading_advice_approved":False,
            "financial_facts_formally_approved":0,"p0_go":False}