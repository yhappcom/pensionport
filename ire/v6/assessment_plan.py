"""Versioned assessment registration; no caller-controlled production trust."""
from __future__ import annotations
from datetime import datetime
import re
from copy import deepcopy
from .codec import json_digest, require_hash, require_identifier, VIDEO
from .errors import InvalidInput

LEGACY_SCHEMA = "IRE_P0_2_05_ETF250_PREREGISTERED_BLIND_ATOMIC_GOLD_PLAN_V1"
CAMPAIGN_SCHEMA = "IRE_V6_ATOMIC_ASSESSMENT_CAMPAIGN_V2"
THRESHOLDS = {"atomic_precision_min_bp":9500, "atomic_recall_min_bp":9800,
              "high_risk_false_negative_max":0}
# Reviewed code enrolment must bind both plan and real trust registry.
# No real campaign has been enrolled; synthetic tests never alter this file.
PINNED_CAMPAIGNS = {}
EXPOSED_SOURCE_SHA256 = frozenset({
    "e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b",
})
EXPOSED_VIDEO_IDS = frozenset({"LVE7XN_esTc"})


def timestamp(value):
    if type(value) is not str:
        raise InvalidInput("ASSESSMENT_TIMESTAMP_REQUIRED")
    try:
        result = datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise InvalidInput("ASSESSMENT_TIMESTAMP_INVALID") from exc
    if result.tzinfo is None:
        raise InvalidInput("ASSESSMENT_TIMESTAMP_OFFSET_REQUIRED")
    return result


def validate_campaign(plan):
    if (type(plan) is not dict or set(plan) != {
        "schema","campaign_id","engine_commit_sha","purpose","registered_at",
        "source","predictions","assessment","source_only_packet_sha256"}
        or plan["schema"] != CAMPAIGN_SCHEMA):
        raise InvalidInput("ASSESSMENT_CAMPAIGN_SCHEMA_INVALID")
    require_identifier(plan["campaign_id"], name="ASSESSMENT_CAMPAIGN_ID")
    if (type(plan["engine_commit_sha"]) is not str or
        not re.fullmatch(r"[0-9a-f]{40}",plan["engine_commit_sha"])):
        raise InvalidInput("ASSESSMENT_ENGINE_COMMIT_INVALID")
    if plan["purpose"] not in ("DEVELOPMENT","HOLDOUT"):
        raise InvalidInput("ASSESSMENT_CAMPAIGN_PURPOSE_INVALID")
    timestamp(plan["registered_at"])
    src,pred=plan["source"],plan["predictions"]
    if type(src) is not dict or set(src)!={"video_id","cue_count","original_srt_sha256"}:
        raise InvalidInput("ASSESSMENT_SOURCE_SCHEMA_INVALID")
    if type(pred) is not dict or set(pred)!={"frozen_native_sha256","atom_count"}:
        raise InvalidInput("ASSESSMENT_PREDICTION_SCHEMA_INVALID")
    require_identifier(src["video_id"],VIDEO,"ASSESSMENT_VIDEO_ID")
    require_hash(src["original_srt_sha256"],"ASSESSMENT_SOURCE_SHA")
    require_hash(pred["frozen_native_sha256"],"ASSESSMENT_PREDICTION_SHA")
    require_hash(plan["source_only_packet_sha256"],"ASSESSMENT_PACKET_SHA")
    if (type(src["cue_count"]) is not int or src["cue_count"]<=0 or
        type(pred["atom_count"]) is not int or pred["atom_count"]<0):
        raise InvalidInput("ASSESSMENT_CENSUS_INVALID")
    if plan["assessment"]!={"thresholds":THRESHOLDS}:
        raise InvalidInput("ASSESSMENT_FIXED_THRESHOLDS_REQUIRED")
    if plan["purpose"]=="HOLDOUT" and (
        src["original_srt_sha256"] in EXPOSED_SOURCE_SHA256 or
        src["video_id"] in EXPOSED_VIDEO_IDS):
        raise InvalidInput("ASSESSMENT_DEVELOPMENT_SOURCE_NOT_HOLDOUT")
    return plan


def source_prediction_fields(plan):
    if type(plan) is not dict:
        raise InvalidInput("P205_PREREGISTRATION_PLAN_SCHEMA_INVALID")
    if plan.get("schema")==LEGACY_SCHEMA:
        return (plan["source"]["original_srt_sha256"],plan["source"]["cue_count"],
                plan["predictions"]["frozen_v228_native_sha256"],
                plan["predictions"]["original_unapproved_atom_count"])
    validate_campaign(plan)
    return (plan["source"]["original_srt_sha256"],plan["source"]["cue_count"],
            plan["predictions"]["frozen_native_sha256"],plan["predictions"]["atom_count"])


def register_campaign(previous, plan):
    """Append a plan; do not rewrite a prior entry or reuse a holdout."""
    validate_campaign(plan)
    if type(previous) is not list:
        raise InvalidInput("ASSESSMENT_CATALOG_INVALID")
    seen_ids=set()
    seen_sources=set()
    seen_videos=set()
    for i,old in enumerate(previous + [{"plan":plan,"plan_sha256":json_digest(plan),
            "previous_entry_sha256":json_digest(previous[-1]) if previous else None}]):
        if (type(old) is not dict or set(old)!={"plan","plan_sha256","previous_entry_sha256"}
            or old["plan_sha256"]!=json_digest(validate_campaign(old["plan"]))
            or old["previous_entry_sha256"]!=(json_digest(previous[i-1]) if i else None)):
            raise InvalidInput("ASSESSMENT_CATALOG_CHAIN_INVALID")
        p=old["plan"]
        cid=p["campaign_id"]
        src=p["source"]["original_srt_sha256"]
        vid=p["source"]["video_id"]
        if cid in seen_ids:
            raise InvalidInput("ASSESSMENT_CAMPAIGN_ID_ALREADY_USED")
        if p["purpose"]=="HOLDOUT" and (src in seen_sources or vid in seen_videos):
            raise InvalidInput("ASSESSMENT_REUSED_SOURCE_NOT_HOLDOUT")
        seen_ids.add(cid);seen_sources.add(src);seen_videos.add(vid)
    return deepcopy(previous)+[{"plan":deepcopy(plan),"plan_sha256":json_digest(plan),
         "previous_entry_sha256":json_digest(previous[-1]) if previous else None}]


def production_registry_pin(plan):
    validate_campaign(plan)
    if plan["purpose"]!="HOLDOUT":
        return None
    enrolled=PINNED_CAMPAIGNS.get(plan["campaign_id"])
    if type(enrolled) is not dict or set(enrolled)!={"plan_sha256","registry_sha256"}:
        return None
    if enrolled["plan_sha256"]!=json_digest(plan):
        return None
    return require_hash(enrolled["registry_sha256"],"ASSESSMENT_PINNED_REGISTRY_SHA")
