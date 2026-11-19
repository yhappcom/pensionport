"""Synthetic PDF research derivation: never an original-byte or issuer audit."""
import copy
import hashlib
import unittest

from v167_chat_research_loop import _evidence_summary
from v171_pdf_research_evidence import (prepare_pdf_research_evidence,
                                         verify_pdf_research_evidence)


class PdfSourceDerivativeTests(unittest.TestCase):
    def setUp(self):
        self.raw=b"%PDF-1.4\n"+b"compressed-non-UTF8-words\x81\x82"*8+b"\n%%EOF\n"
        self.text="Chapter 1 | Publisher text: Patel family history in the early 1970s. "*4
        self.quote="Patel family history in the early 1970s"
        self.kw={"url":"https://catalogimages.wiley.com/images/db/pdf/test.pdf",
                 "raw_pdf":self.raw,"extracted_text":self.text,"excerpt":self.quote,
                 "source_label":"publisher chapter 1", "as_of":"2026-11-19",
                 "page_number":1}

    def build(self): return prepare_pdf_research_evidence(**self.kw)

    def test_01_derived_text_is_not_falsely_presented_as_pdf_raw(self):
        result=self.build()
        verify_pdf_research_evidence(result,raw_pdf=self.raw,extracted_text=self.text)
        self.assertEqual(result.private_sidecar["raw_pdf_sha256"],hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(result.v167_row["body"],self.text.encode())
        self.assertNotEqual(result.v167_row["body"],self.raw)
        self.assertIn("DERIVED_PDF_TEXT_NOT_ISSUER_RAW_BYTES",result.v167_row["source_label"])
        self.assertFalse(result.private_sidecar["e4_approved"])

    def test_02_raw_pdf_is_rejected_by_legacy_quote_validator(self):
        # The precise defect: PDF content is compressed; the visible text is
        # not necessarily an uncompressed UTF-8 substring of the original PDF.
        bad={"url":self.kw["url"],"body":self.raw,"excerpt":self.quote,
             "source_label":"publisher", "retrieved_as_of":"2026-11-19"}
        with self.assertRaisesRegex(ValueError,"EVIDENCE_QUOTE_NOT_IN_BYTES"):
            _evidence_summary([bad])
        self.assertEqual(len(_evidence_summary([self.build().v167_row])),1)

    def test_03_source_pdf_digest_swap_fails(self):
        result=self.build()
        with self.assertRaisesRegex(ValueError,"RAW_PDF_CHANGED"):
            verify_pdf_research_evidence(result,raw_pdf=self.raw+b"junk",extracted_text=self.text)

    def test_04_derived_text_swap_fails(self):
        result=self.build()
        with self.assertRaisesRegex(ValueError,"DERIVED_TEXT_OR_QUOTE_CHANGED"):
            verify_pdf_research_evidence(result,raw_pdf=self.raw,extracted_text=self.text+"forged")

    def test_05_unauthorized_e4_boolean_cannot_be_set(self):
        result=self.build()
        result.private_sidecar["e4_approved"]=True
        from v166_e4_full_video_readiness import digest
        core={k:v for k,v in result.private_sidecar.items() if k!='sidecar_sha256'}
        result.private_sidecar['sidecar_sha256']=digest(core)
        with self.assertRaisesRegex(ValueError,'FALSE_AUTHORITY'):
            verify_pdf_research_evidence(result,raw_pdf=self.raw,extracted_text=self.text)

    def test_06_no_pdf_byte_lookalike(self):
        self.kw["raw_pdf"]=b"invalid-text-body"*10
        with self.assertRaisesRegex(ValueError,"RAW_PDF_BYTES_REQUIRED"):
            self.build()

    def test_07_reject_non_https_source(self):
        self.kw["url"]="http://catalogimages.wiley.com/ch1.pdf"
        with self.assertRaisesRegex(ValueError,"HTTPS_REQUIRED"):
            self.build()

    def test_08_quote_must_exist_in_actual_extracted_text(self):
        self.kw["excerpt"]="unavailable historical statistical data"
        with self.assertRaisesRegex(ValueError,"VISIBLE_TEXT_EXCERPT_NOT_VERIFIED"):
            self.build()

    def test_09_refuses_to_assert_extract_is_independently_audited(self):
        result=self.build()
        self.assertFalse(result.private_sidecar["text_extraction_independently_verified"])
        self.assertFalse(result.private_sidecar["raw_publisher_pdf_retrieval_authenticated"])
        self.assertFalse(result.private_sidecar["native_v123_approved"])
        self.assertFalse(result.private_sidecar["e5_authorized"])

if __name__ == "__main__": unittest.main()