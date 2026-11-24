"""Private P205 closeout proposal, derived only by replaying real evidence.

No caller-provided evaluation grade is accepted. A proposal never edits a
checklist, enrols trust, or authorizes financial publication. Public promotion
requires a separately reviewed, pre-enrolled closeout digest and same-SHA CI.
"""
from __future__ import annotations
from .assessment_campaign import assess_campaign
from .assessment_plan import production_registry_pin
from .codec import json_digest,sha256
from .errors import InvalidInput


def propose_closeout(plan, original, prediction, *, gold, alignment, production_evidence):
    result=assess_campaign(plan,original,prediction,gold=gold,alignment=alignment,
                           production_evidence=production_evidence)
    if not (result["evidence_level"]=="L4" and result["ready_for_p0_2_06"]
            and result["independent_gold_verified"] and plan["purpose"]=="HOLDOUT"):
        raise InvalidInput("P205_CLOSEOUT_REQUIRES_VERIFIED_L4_HOLDOUT")
    return {"schema":"IRE_P205_PRIVATE_ASSESSMENT_CLOSEOUT_V1",
            "campaign_id":plan["campaign_id"],"plan_sha256":json_digest(plan),
            "registry_sha256":production_registry_pin(plan),
            "engine_commit_sha":plan["engine_commit_sha"],
            "source_sha256":sha256(original),"prediction_sha256":sha256(prediction),
            "gold_sha256":json_digest(gold),"alignment_sha256":json_digest(alignment),
            "production_evidence_sha256":json_digest(production_evidence),
            "source_cues":plan["source"]["cue_count"],
            "prediction_atoms":plan["predictions"]["atom_count"],
            "gold_atoms":result["tp"]+result["fn"],
            "tp":result["tp"],"fp":result["fp"],"fn":result["fn"],
            "high_risk_fn":result["diagnostic_high_risk_fn"],
            "evidence_level":"L4","independent_gold_verified":True,
            "research_publication_authorized":False}
