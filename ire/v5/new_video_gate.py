"""Validate five newly indexed SRTs without pretending their meaning is known."""
from pathlib import Path
from .advisory_knowledge_gate import DOMAINS,read_json,require

def verify_five(root, data=None):
    root=Path(root)
    data=data if data is not None else read_json(
        root/"ire/v5/advisory_knowledge/five_video_intake_20261104.json")
    require(data.get("schema")=="IRE_V5_FIVE_VIDEO_INTEGRATION_INTAKE_V1"
            and data.get("source_registered_count")==5
            and data.get("semantic_video_analyses_completed_in_this_stage")==0
            and data.get("integrated_financial_facts_approved")==0
            and data.get("advisory_go") is False,"FIVE_FALSE_PROGRESS")
    from .continuous_integration import build
    routed={x["video_id"]:x for x in build(root)["items"]}
    manifest={}
    for path in sorted((root/"ire/v5/source_catalog").glob("*.json")):
        for row in read_json(path)["files"]:
            vid=row["video_id"]
            if vid in manifest:
                require(manifest[vid]["source_sha256"]==row["source_sha256"],
                        "SOURCE_CATALOG_CONFLICT")
            else:
                manifest[vid]=row
    core=read_json(root/"ire/v5/advisory_knowledge/core20_candidates_20261104.json")
    core_map={row["claim_id"]:row for row in core["claims"]}
    rows=data.get("items")
    require(type(rows) is list and len(rows)==5,"FIVE_ITEM_COUNT_INVALID")
    ids=set()
    domains=set()
    cues=0
    for item in rows:
        vid=item.get("video_id")
        require(type(vid) is str and vid not in ids and vid in routed
                and vid in manifest,"FIVE_UNKNOWN_OR_DUPLICATE_VIDEO")
        ids.add(vid)
        prior=routed[vid]
        indexed=manifest[vid]
        require(item.get("roster_no")==prior["roster_no"]
                and item.get("source_sha256")==indexed["source_sha256"]
                and item.get("original_srt_cue_count")==indexed["cue_count"]
                and prior["type"]=="Long-form"
                and not prior["legacy_record_present"]
                and prior["srt_in_indexed_catalog"],
                "FIVE_ORIGINAL_VIDEO_ID_MISMATCH")
        domain=item.get("domain")
        require(domain in DOMAINS and domain not in domains,
                "FIVE_DOMAIN_COVERAGE_INVALID")
        domains.add(domain)
        refs=item.get("legacy_claim_ids_for_future_comparison")
        require(type(refs) is list and len(refs)>0 and len(set(refs))==len(refs)
                and all(cid in core_map and core_map[cid]["domain"]==domain for cid in refs),
                "FIVE_UNSUPPORTED_RELATION_CANDIDATE")
        require(item.get("stage")=="SOURCE_INDEXED_AWAITING_FULL_SRT_ANALYSIS"
                and item.get("merge_preview_status")=="TOPIC_ONLY_NOT_CLAIM_RELATION",
                "FIVE_ANALYSIS_OR_MERGE_FALSIFIED")
        require(item.get("source_indexed") is True and all(
            item.get(key) is False for key in (
                "source_text_semantically_read_this_stage",
                "full_cue_coverage_verified_for_semantics",
                "financial_evidence_reviewed_for_this_video",
                "knowledge_relations_adjudicated",
                "knowledge_merge_approved",
                "investment_advice_approved")),"FIVE_UNVERIFIED_ADVICE_APPROVAL")
        cues+=item["original_srt_cue_count"]
    require(domains==DOMAINS,"FIVE_MISSING_DOMAIN")
    return {"registered_videos":5,"source_cues":cues,
            "semantic_analyses_completed":0,"approved_new_relations":0,
            "advisory_go":False}
