"""Historical P205 receipts, checked without requiring the live cursor to be HOLD.

This is history validation only, not authorization of a new checkpoint. The
current public gate remains separately fail-closed pending real L4 evidence.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

HISTORICAL_BLOBS = {
    "docs/IRE_P0_2_05_SOURCE_ONLY_BLIND_GOLD_READINESS_HOLD_SHA_20261123.json": "2dd1009402a09788e77cf2901a8e0bc0dd471321",
    "docs/IRE_P0_2_05_ETF250_BLIND_GOLD_PREREGISTRATION_20261123.json": "481a4b809c3058b16f56d54fe3bad820ed972dd8",
    "docs/IRE_P0_2_05_ETF250_SOURCE_FIRST_PROVISIONAL_71_PRE_CROSSWALK_SHA_ONLY_20261123.json": "f9168ad6bf03c4dca6190a27962faf518d2e5144",
    "docs/IRE_P0_2_05_ETF250_SOURCE71_NATIVE68_CROSSWALK_SHA_ONLY_HOLD_20261123.json": "1c6783d40484397d18596afe2bf6e215af94e5fe",
    "docs/IRE_P0_2_05_11_KIND_PAIR_SOURCE_GROUNDED_TRIAGE_SHA_ONLY_20261123.json": "9827abf2082055ed4074d57e4b417e5d41e575e5",
    "docs/IRE_P0_2_05_ROOT_CAUSE_REASSESSMENT_AND_GOLD_EVIDENCE_HOLD_20261123.json": "665092246f220f11a3c552da184f3dca3665dc3c"
}


def verify_history(root):
    root=Path(root)
    errors=[]
    for path,expected in HISTORICAL_BLOBS.items():
        try:
            data=(root/path).read_bytes()
            actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            if actual!=expected:
                errors.append("P205_HISTORY_BLOB_DRIFT:"+path)
        except OSError:
            errors.append("P205_HISTORY_BLOB_MISSING:"+path)
    if errors:
        return errors
    from scripts.ire_p0_2_05_gold_readiness_gate import verify as readiness
    from scripts.ire_p0_2_05_source71_compare_gate import verify as crosswalk
    from scripts.ire_p0_2_05_kind_triage_gate import verify as triage
    from scripts.ire_p0_2_05_root_cause_gate import verify as root_cause
    for check in (readiness,crosswalk,triage,root_cause):
        errors.extend(check(root,historical_only=True))
    return errors
