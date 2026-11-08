#!/usr/bin/env python3
"""Evidence-only government HTTPS response capture, never financial fact approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_BYTES = 2 * 1024 * 1024
SOURCES = {
    "nts_pension": {
        "url": "https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7889&mi=6609",
        "hosts": ("nts.go.kr", "www.nts.go.kr"),
        "phrases": ("연금소득금액계산방법", "1천500만원", "분리과세", "15%"),
        "effective_date": None,
    },
    "decree_40_3": {
        "url": "https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=03&joNo=0040&lsiSeq=290841&urlMode=lsScJoRltInfoR",
        "hosts": ("www.law.go.kr", "law.go.kr"),
        "phrases": ("소득세법시행령", "제40조의3", "과세제외금액", "이연퇴직소득", "36737", "2026.10.1."),
        "effective_date": "2026-10-01",
    },
}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.ignore = max(0, self.ignore-1)

    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)


def inspect(source_id, raw, final_url, status, content_type):
    if source_id not in SOURCES:
        raise ValueError("SOURCE_NOT_IN_ALLOWLIST")
    src = SOURCES[source_id]
    if type(raw) is not bytes or not raw or len(raw) > MAX_BYTES:
        raise ValueError("PUBLIC_BODY_SIZE_INVALID")
    u = urlsplit(final_url)
    if (u.scheme != "https" or u.hostname not in src["hosts"] or u.username
            or u.password or u.port not in (None, 443)):
        raise ValueError("UNTRUSTED_REDIRECT_OR_HOST")
    if status != 200:
        raise ValueError("BAD_OFFICIAL_HTTP_STATUS")
    if not content_type.lower().startswith("text/html"):
        raise ValueError("NOT_HTML")
    parser = _Text()
    parser.feed(raw.decode("utf-8", errors="replace"))
    visible = re.sub(r"\s+", "", "".join(parser.parts))
    missing = [s for s in src["phrases"] if s not in visible]
    if missing:
        raise ValueError("OFFICIAL_TEXT_OR_VERSION_MISSING:" + ",".join(missing))
    return {
        "source_id": source_id,
        "requested_url": src["url"],
        "resolved_url": final_url,
        "captured_body_sha256": hashlib.sha256(raw).hexdigest(),
        "captured_body_bytes": len(raw),
        "http_status": status,
        "content_type": content_type,
        "visible_original_legal_text_checks_passed": True,
        "visible_effective_date": src["effective_date"],
        "nts_page_published_date_confirmed": False,
        "https_ca_host_validation_used": True,
        "issuer_digital_signature_verified": False,
        "independent_semantic_support_verified": False,
        "finance_fact_approved": False,
        "p0_go": False,
        "status": "PUBLIC_RAW_SOURCE_ONLY_REVIEW_PENDING",
    }


def fetch(source_id):
    url = SOURCES[source_id]["url"]
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 IRE-V6-Gov-Source-Verification",
        "Accept": "text/html",
        "Accept-Encoding": "identity",
    })
    with urlopen(req, context=ssl.create_default_context(), timeout=35) as r:
        return r.read(MAX_BYTES+1), r.geturl(), r.status, r.headers.get("Content-Type", "")


def run(output):
    if output.exists() and any(output.iterdir()):
        raise ValueError("OUTPUT_DIRECTORY_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for key in sorted(SOURCES):
        raw, url, status, ctype = fetch(key)
        record = inspect(key, raw, url, status, ctype)
        filename = key+".html"
        (output/filename).write_bytes(raw)
        record["artifact_name"] = filename
        records.append(record)
        print("CAPTURED", key, record["captured_body_sha256"], flush=True)
    result = {
        "schema": "IRE_V6_OFFICIAL_RAW_SOURCE_EVIDENCE_V1",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "private_original_srt_included": False,
        "legal_applicability_independently_verified": False,
        "human_review_completed": False,
        "precision_recall_measured": False,
        "p0_go": False,
    }
    (output/"capture_manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
        encoding="utf-8",
    )
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = run(args.output)
    except (OSError, ValueError, UnicodeError) as e:
        print("OFFICIAL_SOURCE_CAPTURE_BLOCKED", type(e).__name__, str(e), file=sys.stderr)
        return 2
    print("PUBLIC_OFFICIAL_RAW_CAPTURE_SUCCESS_NOT_FACT_APPROVAL", len(result["records"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
