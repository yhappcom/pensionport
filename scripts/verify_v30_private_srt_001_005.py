#!/usr/bin/env python3
"""Private #1-5 SRT local replay against frozen V3.0; never upload original text.

Input: source-backed user's 1-100.zip, an ordinary trusted local file. Outputs
only counts, original hashes, independent arithmetic and BLOCKED cases.
CI cannot run this without user originals; CI prints no original SRT content.
"""
import argparse
from collections import Counter
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import zipfile

from v30_verified_core import policy_gate,parse_srt,blob_sha,sha256
from v30_claim_extraction import propose_atomic_draft
from v30_research_pipeline import scan_source_state
from v30_evidence_services import math_reproduce

ROSTER={
  1:("sz5N9WJS310","5bd8c20cff81446fb5fe058f92953f6ce4457962",23),
  2:("6VEfKF7BzZU","cb9827570e78684f678030ca220b56190a2cef1a",9),
  3:("OiDTNstaSpM","53281c9bc9ce85692267d6ff7e00ebaf5b4ecc27",15),
  4:("aNfGrcO6WPI","b551925f3e823b4f46e3e1aebaa6cd2e5ae802af",6),
  5:("qtluAViPpsQ","a845a8e3d8a463035900c376187250adc76a5e12",9),
}
def need(flag,what):
    if not flag:raise ValueError(what)

def effective_monthly_accumulation(p,yearly_effective,n):
    with localcontext() as ctx:
        ctx.prec=44
        rm=(Decimal(1)+yearly_effective)**(Decimal(1)/Decimal(12))-Decimal(1)
        return p*((1+rm)**n-1)/rm

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--original-zip",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    root=args.root.resolve()
    policy_gate(root)
    index=json.loads((root/"data/subtitles/content_index_001_070.json").read_text())["items"]
    hist=json.loads((root/"v5/research_completion_001_010.json").read_text())
    need(hist["certified_count"]==0,"HISTORICAL_COMPLETENESS_CHANGED")
    out=[]
    with zipfile.ZipFile(args.original_zip) as archive:
        for no,(vid,study_sha,expected_claims) in ROSTER.items():
            fname=f"1-100/youtube-transcript-{vid}.srt"
            data=archive.read(fname)
            entry=index[vid]
            need(entry["roster_no"]==no,"SOURCE_ROSTER_CHANGED")
            cues=parse_srt(data,entry["subtitle_sha256"])
            need(len(cues)==entry["cue_count"],"SOURCE_CUE_COUNT_CHANGED")
            draft=propose_atomic_draft(cues,vid)
            source_path=root/"data/analysis_events"/(vid+".json")
            need(blob_sha(source_path)==study_sha,"FROZEN_V3_STUDY_CHANGED")
            src=json.loads(source_path.read_text(encoding="utf-8"))
            v5=json.loads((root/f"v5/retrofit/v5_{no:03d}_{vid}_bounded_closeout.json").read_text(encoding="utf-8"))
            legacy={r["claim_id"]:r["verification"] for r in src["core_claims"]}
            v5map={r["id"]:r["verdict"] for r in v5["claim_coverage"]["claims"]}
            need(len(legacy)==expected_claims and legacy==v5map,
                 "V3_V5_HISTORICAL_CLAIM_DISAGREEMENT")
            # No reviewed material/no human signature; deliberately attempt
            # a false "completed" ledger and prove V3.0 refuses it.
            fake={
                "schema":"V30_ATOMIC_LEDGER_V2","cues":[],
                "claims":[],
            }
            manifest={
                "schema":"V30_FULL_SOURCE_MANIFEST_V1",
                "video_number":no,"video_id":vid,
                "test_fixture":False,
                "srt_sha256":entry["subtitle_sha256"],
                "original_cue_count":entry["cue_count"],
                "historical_event_git_blob_sha":study_sha,
                "legacy_verdicts":legacy,
            }
            blocked=False;reason=None
            try:scan_source_state(root,manifest,data,fake,authorities=None)
            except (ValueError,TypeError,KeyError) as exc:
                blocked=True
                reason=str(exc)
            need(blocked and "ATOMIC_CUE_COVERAGE" in reason,
                 "INCOMPLETE_REAL_ORIGINAL_LEDGER_WAS_NOT_BLOCKED")
            status=Counter(legacy.values())
            out.append({
                "video_number":no,"video_id":vid,
                "source_original_zip_file_entry":fname,
                "original_srt_sha256_computed":sha256(data),
                "source_srt_sha256_matches_github":True,
                "source_raw_bytes":len(data),
                "parsed_source_cues":len(cues),
                "source_registry_cues":entry["cue_count"],
                "historical_core_claims":len(legacy),
                "legacy_v3_equals_legacy_v5_verdicts":True,
                "historical_verdict_counts":dict(sorted(status.items())),
                "historical_v5_external_blockers":len(v5["external_blockers"]),
                "v30_generated_unverified_atomic_proposals":
                    draft["generated_atomic_proposals"],
                "v30_likely_material_unverified_proposals":
                    draft["likely_material_proposals"],
                "v30_ambiguous_unverified_proposals":
                    draft["ambiguous_proposals"],
                "source_cue_count_fully_processed":True,
                "verified_atomic_statements":0,
                "source_audio_or_video_verified":False,
                "full_human_source_semantic_coverage_completed":False,
                "intentionally_incomplete_ledger_rejected":blocked,
                "incomplete_ledger_error":reason,
                "v5_research_complete_certificate":False,
            })
    # #1-06 was explicitly labeled effective annual 7%, while V30 nominal
    # model hardcodes 0.07/12; calculate both to expose assumption mismatch.
    yrs={}
    for years in (7,10):
        n=years*12
        m={
            "model_type":"MONTHLY_SAVINGS_FUTURE_VALUE",
            "principal_or_monthly_contribution":"300000",
            "nominal_annual_rate":"0.07","months":n,
            "cashflow_timing":"END_OF_MONTH",
            "monthly_rate_convention":"NOMINAL_ANNUAL_DIVIDED_BY_12",
            "includes_fees_taxes":False,"currency":"KRW",
        }
        nominal=math_reproduce(m)
        effective=effective_monthly_accumulation(
            Decimal(300000),Decimal("0.07"),n)
        yrs[str(years)]={
            "existing_v3_claim_rate_convention":"EFFECTIVE_ANNUAL_7_PERCENT",
            "existing_v3_approx_million_KRW":
                32.14 if years==7 else 51.32,
            "v30_available_nominal_annual_over12_KRW":nominal["formula_value"],
            "separately_recomputed_effective_annual_KRW":
                str(effective.quantize(Decimal("0.01"))),
            "difference_due_to_rate_convention_KRW":
                str((Decimal(nominal["formula_value"])-effective).quantize(
                    Decimal("0.01"))),
            "v30_nominal_claims_to_verify_effective_model":False,
        }
    result={
        "schema":"V30_001_005_ACTUAL_PRIVATE_SRT_OFFLINE_REPLAY_V1",
        "method":"Real original SRT bytes loaded locally from user Google Drive ZIP, checked by EXACT frozen GitHub V3.0 modules. No original bytes copied into GitHub.",
        "original_archive_sha256":sha256(args.original_zip.read_bytes()),
        "sources":out,
        "totals":{
            "real_original_video_count":len(out),
            "cues_reparsed":sum(r["parsed_source_cues"] for r in out),
            "historical_core_claims":sum(r["historical_core_claims"] for r in out),
            "prior_V5_unresolved_external_blocker_records":
                sum(r["historical_v5_external_blockers"] for r in out),
            "v30_unreviewed_atomic_proposals":
                sum(r["v30_generated_unverified_atomic_proposals"] for r in out),
            "v30_likely_material_unreviewed":
                sum(r["v30_likely_material_unverified_proposals"] for r in out),
            "v30_ambiguous_unreviewed":
                sum(r["v30_ambiguous_unverified_proposals"] for r in out),
            "failed_closed_incomplete_ledger_videos":sum(
                r["intentionally_incomplete_ledger_rejected"] for r in out),
            "source_audio_checked":0,
            "v30_independent_research_complete_certificates":0,
        },
        "numeric_counterexample_v3_claim_001_06_effective_vs_nominal":yrs,
        "real_financial_facts_reverified_by_this_replay":False,
        "historical_core_claims_did_not_become_new_independent_gold":True,
        "private_source_srt_in_result":False,
        "automatic_knowledge_approvals":0,
        "production_ready":False,
    }
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,IndexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
