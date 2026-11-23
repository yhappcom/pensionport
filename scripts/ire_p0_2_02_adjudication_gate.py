#!/usr/bin/env python3
"""P0-2-02 SHA-only frozen/source-first decision contract; private SRT not in CI."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
RECEIPT=Path("docs/IRE_P0_2_02_ETF250_ATOM_CROSS_ADJUDICATION_SHA_ONLY_20261123.json")
STATE=Path("docs/IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_20261122.json")
LEDGER=Path("docs/IRE_CANONICAL_CURRENT_RESEARCH_STATUS_20261122.json")
SHA=re.compile(r"^[a-f0-9]{64}$")
EXPECTED_COUNTS={"KEEP":32,"REATOMIZE":17,"QUARANTINE":4,"OPEN":15}
EXPECTED_SOURCE="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
EXPECTED_NATIVE="c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb"
EXPECTED_PRIVATE="b70c7ea8365ec6eed98575a23a550fb819dd2ac3a3ce27eabf323f65b099a55f"
def load(root,p):
    return json.loads((Path(root)/p).read_text(encoding="utf-8"))
def verify(root=ROOT,*,receipt=None,state=None,ledger=None):
    root=Path(root)
    r=receipt if receipt is not None else load(root,RECEIPT)
    s=state if state is not None else load(root,STATE)
    l=ledger if ledger is not None else load(root,LEDGER)
    bad=[]
    def need(ok,code):
        if not ok:bad.append("P202_"+code)
    from scripts.ire_checklist_gate import CATALOG, validate as validate_checklist
    need(not validate_checklist(load(root,CATALOG),s,root=root),"CHECKLIST_INVALID")
    rows=s.get("items",[])
    need(len(rows)==60 and all(x.get("status")=="PASS" for x in rows[:14])
         and rows[13].get("id")=="P0-2-02"
         and rows[14].get("id")=="P0-2-03"
         and rows[14].get("status") in {"READY","IN_PROGRESS","HOLD","FAIL","PASS"},
         "SOURCE_ADJUDICATION_NOT_PASSED")
    cursor=next((x["id"] for x in rows if x["status"]!="PASS"),"ALL_COMPLETE")
    dev=l.get("development_gate",{})
    need(dev.get("this_item")==cursor and dev.get("pending_next_item")==cursor,
         "LIVE_CURSOR_MISMATCH")
    need(r.get("schema")=="IRE_P0_2_02_PUBLIC_SHA_ONLY_ADJUDICATION_V1"
         and r.get("task_id")=="P0-2-02" and r.get("as_of")=="2026-11-23",
         "SCHEMA_TASK_DATE")
    for k,expected in (("original_srt_sha256",EXPECTED_SOURCE),
                       ("original_native_sha256",EXPECTED_NATIVE),
                       ("private_full_decision_json_sha256",EXPECTED_PRIVATE),
                       ("original_zip_sha256","9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397"),
                       ("p201_private_cue_review_zip_sha256","df54f80d153c4f07a80a261344282681c6fb8ddb7bb9bd6fbc9aa6b99ddce8c8"),
                       ("private_decision_package_zip_sha256","58106bff2c5fe91c36a676cba2325b09ebf9710058dec1f52824358e1991a040")):
        need(r.get(k)==expected,"EVIDENCE_SHA_"+k)
    d=r.get("dispositions",{})
    need(set(d)==set(EXPECTED_COUNTS)
         and all(d.get(k,{}).get("count")==n for k,n in EXPECTED_COUNTS.items()),
         "DISPOSITION_COUNTS")
    all_ids=[]
    for k in EXPECTED_COUNTS:
        ids=d.get(k,{}).get("ids",[])
        need(type(ids) is list and len(ids)==EXPECTED_COUNTS[k]
             and all(re.fullmatch(r"C\\d{5}",i or "") for i in ids),"DISPOSITION_IDS_"+k)
        all_ids.extend(ids)
    need(len(all_ids)==len(set(all_ids))==68,
         "DISPOSITION_DUPLICATE")
    need(r.get("original_source_cues_verified")==250
         and r.get("original_primary_quote_references_verified")==73
         and r.get("legacy_atoms_reviewed")==68
         and r.get("cross_atoms_total")==21
         and r.get("cross_foreign_source_edges_total")==49
         and r.get("cross_reference_roles")=={"context":49,"condition":29,"numeric":3,"exception":0,"primary_source":0},
         "SOURCE_AND_CROSS_EDGE_CENSUS")
    c=r.get("b0013_c00057",{})
    need(c.get("owner_child")=="B0013"
         and c.get("foreign_condition_cues")==[45,46,47]
         and c.get("index_etf_only_preserved") is True
         and c.get("disposition")=="KEEP_UNAPPROVED"
         and "C00057" in d.get("KEEP",{}).get("ids",[]),
         "FOREIGN_INDEX_CONDITION_LOST")
    for k in ("zero_original_atom_deletions","zero_conditions_exceptions_numeric_dropped",
              "zero_primary_source_cross_silent_rewrites","source_first_not_external_gold"):
        need(r.get(k) is True,"LOSSLESS_"+k)
    need(r.get("private_library_upload_succeeded") is True
         and r.get("private_library_file_id")=="libfile_87f51a386bb88191861d49f428d3e69f",
         "PRIVATE_LIBRARY_CUSTODY")
    need(r.get("original_cue_open_count")==67
         and r.get("independent_precision") is None
         and r.get("independent_recall") is None
         and r.get("independent_high_risk_fn") is None
         and r.get("e2_final_approved") is False
         and r.get("real_audio_verified") is False
         and r.get("real_video_frame_verified") is False
         and r.get("e3_children_approved")==0
         and r.get("e4_approvals")==0
         and r.get("e5_publications")==0
         and r.get("personal_advice_approved") is False,
         "FALSE_GOLD_AUDIO_OR_APPROVAL")
    return bad
if __name__=="__main__":
    problems=verify()
    for p in problems:print("P202_SHA_ONLY_GATE_ERROR",p,file=sys.stderr)
    if problems:sys.exit(1)
    print("P202_SHA_ONLY_GATE_PASS ATOMS=68 KEEP=32 REATOMIZE=17 QUARANTINE=4 OPEN=15 CROSS=21 EDGES=49 FINANCE_APPROVED=0")
