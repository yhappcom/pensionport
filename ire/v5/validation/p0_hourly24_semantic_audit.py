"""Reusable source-anchored redacted semantic window audit; never asserts financial truth."""
from __future__ import annotations
import base64,hashlib,json,zlib
from pathlib import Path

def audit_bundle(path: Path, expected_data_sha256: str, expected_source_sha256: str,
                 first_window: int, last_window: int, first_cue: int, last_cue: int) -> dict:
    compressed=base64.b64decode(path.read_text("ascii").strip(),validate=True)
    decoder=zlib.decompressobj()
    raw=decoder.decompress(compressed,1_000_000)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("P0_BUNDLE_BAD_COMPRESSION")
    if hashlib.sha256(raw).hexdigest()!=expected_data_sha256:
        raise ValueError("P0_BUNDLE_CHANGED")
    d=json.loads(raw)
    if d["source_sha256"]!=expected_source_sha256 or d["p0_complete"] or d["independent_gold_recall_certified"] or d["formal_researchrun_submitted"]:
        raise ValueError("P0_UNVERIFIED_RELEASE")
    windows=d["windows"]
    expected=[f"W{i:05d}" for i in range(first_window,last_window+1)]
    if [w["window_id"] for w in windows]!=expected:
        raise ValueError("P0_WINDOW_GAP")
    cues=[c["cue"] for w in windows for c in w["cue_hashes"]]
    if cues!=list(range(first_cue,last_cue+1)):
        raise ValueError("P0_CUE_OWNERSHIP")
    anchors={(w["window_id"],c["cue"],c["text_sha256"]) for w in windows for c in w["cue_hashes"]}
    ids=set()
    for w in windows:
        if len(w["cue_hashes"])!=w["cue_count"] or w["first_cue"]!=w["cue_hashes"][0]["cue"] or w["last_cue"]!=w["cue_hashes"][-1]["cue"]:
            raise ValueError("P0_WINDOW_CUE_COUNT")
        if any(len(c["text_sha256"])!=64 for c in w["cue_hashes"]):
            raise ValueError("P0_BAD_CUE_HASH")
    for claim in d["claims"]:
        cid=claim["candidate_id"]
        if cid in ids or claim["approved"] or (claim["window_id"],claim["anchor_cue"],claim["anchor_sha256"]) not in anchors:
            raise ValueError("P0_UNSUPPORTED_CLAIM")
        ids.add(cid)
    if {cid for w in windows for cid in w["claim_ids"]}!=ids:
        raise ValueError("P0_CLAIM_CENSUS")
    if d["next_unreviewed_window"]!=f"W{last_window+1:05d}":
        raise ValueError("P0_NEXT_POINTER")
    return {"windows":len(windows),"cues":len(cues),"claims":len(ids),"next_window":d["next_unreviewed_window"],"p0_go":False}

if __name__=="__main__":
    p=Path(__file__).resolve().parent/"private_source_derived_20261107"/"hourly24_w25_w36.json.zlib.b64"
    print(json.dumps(audit_bundle(p,"98950e51935f58a8affa42b59487ff99351594c4577e21db92c57c6b20a050e3",
        "af4d89d0e69b219947fdf82cdd9f3229c1f7b1e14c05c924ac815d2511f6c531",25,36,432,647),sort_keys=True))
