"""Synthetic PDF text provenance tests; PDFs are not official financial facts."""
from __future__ import annotations
import importlib.util
import io
import unittest

from ire.evidence import independently_fetch_candidate


@unittest.skipUnless(importlib.util.find_spec("pypdf") and
                     importlib.util.find_spec("reportlab"),
                     "optional PDF dependencies absent; capability unverified")
class V3PdfPrimarySourceTests(unittest.TestCase):
    URL="https://www.law.go.kr/example/synthetic-finance-201"

    @staticmethod
    def pdf(text):
        from reportlab.pdfgen import canvas
        bio=io.BytesIO()
        pdf=canvas.Canvas(bio)
        pdf.setFont("Helvetica",12)
        pdf.drawString(30,750,text)
        pdf.save()
        return bio.getvalue()

    def test_pdf_original_bytes_and_quote_trace_without_auto_approval(self):
        text="Synthetic investment policy fee 4.5 percent charged per year."
        raw=self.pdf(text)
        result=independently_fetch_candidate(
            self.URL,read_fn=lambda url:(raw,"application/pdf",url),
            fetched_at="2026-11-02T00:00:00Z")
        self.assertEqual(result["content_type"],"application/pdf")
        self.assertIn(text,result["visible_text"])
        self.assertFalse(result["extracted_text_truncated"])
        self.assertFalse(result["actual_publisher_identity_cryptographically_verified"])
        self.assertFalse(result["independent_financial_fact_approved"])
        self.assertEqual(result["source_read_mode"],"INJECTED_SYNTHETIC_READER")

    def test_scanned_pdf_without_text_is_not_claimed_verified(self):
        raw=self.pdf(" ")
        with self.assertRaisesRegex(ValueError,"EVIDENCE_PDF_READ_FAILED"):
            independently_fetch_candidate(self.URL,read_fn=lambda url:(
                raw,"application/pdf",url))

    def test_invalid_pdf_or_html_masquerading_as_pdf_rejected(self):
        with self.assertRaisesRegex(ValueError,"EVIDENCE_PDF_MAGIC_OR_SIZE_INVALID"):
            independently_fetch_candidate(self.URL,read_fn=lambda url:(
                b"<html><body>Fake official policy</body></html>",
                "application/pdf",url))

    def test_pdf_with_text_cut_is_marked_as_incomplete(self):
        # Excerpt truncation is a hard scope-adjudication blocker.
        text="Synthetic finance source text describing a sample rule."
        doc=independently_fetch_candidate(
            self.URL,read_fn=lambda url:(self.pdf(text),"application/pdf",url))
        self.assertFalse(doc["extracted_text_truncated"])