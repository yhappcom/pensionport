"""V171: explicitly *derived* text for publisher PDF research (never E4 proof).

V167 validates that evidence excerpts occur within `body` bytes. A typical
compressed PDF has no such UTF-8 substring, even when the rendered page does.
For research ONLY this adapter preserves the actual raw PDF digest in a private
sidecar, and gives V167 clearly labelled *derived text bytes*. The raw PDF
SHA MUST NOT be replaced by the extracted-text SHA in formal primary-source
verification. For E4, re-fetch and authenticate the original PDF and compare
an independently checked extraction/page. This adapter does not do that.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import _evidence_summary

SCHEMA = "IRE_V171_PDF_DERIVED_RESEARCH_TEXT_SIDECAR_V1"


def _need(ok, reason):
    if not ok:
        raise ValueError("V171_PDF_RESEARCH_" + reason)


def _sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class PdfResearchEvidence:
    """Private transport; never upload full PDF/text without access controls."""
    v167_row: dict
    private_sidecar: dict


def prepare_pdf_research_evidence(*, url: str, raw_pdf: bytes,
                                  extracted_text: str, excerpt: str,
                                  source_label: str, as_of: str,
                                  page_number: int,
                                  extractor: str = "pdftotext -layout") -> PdfResearchEvidence:
    _need(type(raw_pdf) is bytes and len(raw_pdf) >= 100 and
          raw_pdf.startswith(b"%PDF-") and b"%%EOF" in raw_pdf[-2048:],
          "RAW_PDF_BYTES_REQUIRED")
    _need(type(url) is str and len(url) <= 1500, "URL")
    parsed = urlsplit(url)
    _need(parsed.scheme == "https" and parsed.hostname is not None and
          parsed.username is None and parsed.password is None and
          parsed.port in (None, 443) and not parsed.fragment, "HTTPS_REQUIRED")
    _need(type(extracted_text) is str and len(extracted_text) >= 100 and
          type(excerpt) is str and len(excerpt.strip()) >= 15 and
          excerpt in extracted_text, "VISIBLE_TEXT_EXCERPT_NOT_VERIFIED")
    _need(type(source_label) is str and source_label.strip()
          and type(extractor) is str and 3 <= len(extractor) <= 120,
          "DERIVATION_LABEL_REQUIRED")
    _need(type(page_number) is int and page_number >= 1, "PAGE_REQUIRED")
    _need(type(as_of) is str and date.fromisoformat(as_of).isoformat() == as_of,
          "DATE_REQUIRED")
    extracted = extracted_text.encode("utf-8")
    # V167's `body` is the DERIVED transcript, NOT bytes from a publisher PDF.
    # Preserve that distinction in every emitted field; no native approval.
    label = ("DERIVED_PDF_TEXT_NOT_ISSUER_RAW_BYTES | " + source_label.strip()
             + " | raw_pdf_sha256=" + _sha(raw_pdf)
             + " | extraction_sha256=" + _sha(extracted)
             + " | page_hint=" + str(page_number))
    row = {"url": url, "body": extracted, "excerpt": excerpt,
           "source_label": label, "retrieved_as_of": as_of}
    # Validate with the exact V167 verifier, so downstream hashes agree.
    summary = _evidence_summary([row])[0]
    core = {"schema": SCHEMA, "url": url,
            "raw_pdf_sha256": _sha(raw_pdf),
            "raw_pdf_size_bytes": len(raw_pdf),
            "derived_text_sha256": _sha(extracted),
            "derived_text_size_bytes": len(extracted),
            "excerpt_sha256": _sha(excerpt.encode("utf-8")),
            "v167_research_evidence_sha256": digest(summary),
            "page_hint_not_page_verified": page_number,
            "extractor_label_unverified": extractor,
            "raw_publisher_pdf_retrieval_authenticated": False,
            "text_extraction_independently_verified": False,
            "source_age_and_applicability_certified": False,
            "native_v123_approved": False, "e4_approved": False,
            "e5_authorized": False}
    return PdfResearchEvidence(row, {**core, "sidecar_sha256": digest(core)})


def verify_pdf_research_evidence(payload: PdfResearchEvidence, *,
                                 raw_pdf: bytes, extracted_text: str) -> None:
    """Reject raw-PDF/text/excerpt/label substitutions in saved draft evidence."""
    _need(isinstance(payload, PdfResearchEvidence), "TYPE")
    sidecar, row = payload.private_sidecar, payload.v167_row
    _need(type(sidecar) is dict and sidecar.get("schema") == SCHEMA and
          sidecar.get("sidecar_sha256") == digest({k: v for k, v in sidecar.items()
                                                   if k != "sidecar_sha256"}),
          "SIDECAR_DRIFT")
    _need(type(raw_pdf) is bytes and _sha(raw_pdf) == sidecar["raw_pdf_sha256"]
          and len(raw_pdf) == sidecar["raw_pdf_size_bytes"],
          "RAW_PDF_CHANGED")
    text_bytes = extracted_text.encode("utf-8")
    _need(_sha(text_bytes) == sidecar["derived_text_sha256"]
          and len(text_bytes) == sidecar["derived_text_size_bytes"]
          and row["body"] == text_bytes and
          _sha(row["excerpt"].encode("utf-8")) == sidecar["excerpt_sha256"]
          and row["url"] == sidecar["url"], "DERIVED_TEXT_OR_QUOTE_CHANGED")
    _need(digest(_evidence_summary([row])[0]) ==
          sidecar["v167_research_evidence_sha256"], "V167_EVIDENCE_DRIFT")
    _need(all(sidecar[k] is False for k in (
        "raw_publisher_pdf_retrieval_authenticated",
        "text_extraction_independently_verified",
        "source_age_and_applicability_certified", "native_v123_approved",
        "e4_approved", "e5_authorized")), "FALSE_AUTHORITY")