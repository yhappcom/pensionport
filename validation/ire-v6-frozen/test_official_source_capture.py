"""No-network negative controls for official raw HTTPS evidence."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "official_capture", Path(__file__).with_name("official_source_capture.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NTS = ("<p>연금소득금액 계산방법은 1천500만원 초과일 경우 15% 분리과세</p>").encode()
LAW = ("<div>소득세법 시행령 [시행 2026. 10. 1.] 대통령령 제36737호 "
       "제40조의3 과세제외금액 다음 이연퇴직소득</div>").encode()


class OfficialCaptureTests(unittest.TestCase):
    def inspect(self, kind, raw, url=None, status=200, ctype="text/html"):
        return mod.inspect(kind, raw, url or mod.SOURCES[kind]["url"], status, ctype)

    def test_html_nts_not_approved(self):
        record = self.inspect("nts_pension", NTS)
        self.assertFalse(record["finance_fact_approved"])
        self.assertIsNone(record["visible_effective_date"])

    def test_html_decree_version_bound_not_approved(self):
        record = self.inspect("decree_40_3", LAW)
        self.assertEqual(record["visible_effective_date"], "2026-10-01")
        self.assertFalse(record["issuer_digital_signature_verified"])
        self.assertFalse(record["p0_go"])

    def test_wrong_host(self):
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_REDIRECT"):
            self.inspect("nts_pension", NTS, "https://malicious.example/text")

    def test_http_downgrade(self):
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_REDIRECT"):
            self.inspect("nts_pension", NTS, "http://nts.go.kr/fake")

    def test_http_503(self):
        with self.assertRaisesRegex(ValueError, "BAD_OFFICIAL_HTTP"):
            self.inspect("nts_pension", NTS, status=503)

    def test_missing_effective_date(self):
        with self.assertRaisesRegex(ValueError, "OFFICIAL_TEXT_OR_VERSION"):
            self.inspect("decree_40_3", LAW.replace(b"2026. 10. 1.", b"2025. 1. 1."))

    def test_no_unapproved_url(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_NOT_IN_ALLOWLIST"):
            mod.inspect("private_user_srt", NTS, "https://nts.go.kr", 200, "text/html")

    def test_oversized_body(self):
        with self.assertRaisesRegex(ValueError, "PUBLIC_BODY_SIZE_INVALID"):
            self.inspect("nts_pension", b"x"*(mod.MAX_BYTES+1))

    def test_wrong_content_type(self):
        with self.assertRaisesRegex(ValueError, "NOT_HTML"):
            self.inspect("nts_pension", NTS, ctype="application/pdf")

    def test_script_only_fact_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "OFFICIAL_TEXT_OR_VERSION"):
            self.inspect("nts_pension", b"<body>no facts</body><script>"+NTS+b"</script>")


if __name__ == "__main__":
    unittest.main()
