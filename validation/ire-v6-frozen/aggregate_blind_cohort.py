"""Nine-video prospective blind-score aggregator; NO independent gold approval.

Accept only receipts produced by V6 source-bound blind arithmetic evaluation.
Each receipt's category arithmetic is rechecked. Neither a receipt nor this
aggregator establishes reviewer independence, semantic correctness or P0 GO.
Private subtitles/gold text are never included in output.
"""
from __future__ import annotations
import re
from ire.v6.codec import json_digest
from ire.v6.evaluation import _wilson95
from ire.v6.errors import InvalidInput

CATS = ("LEVERAGE", "OTHER", "PENSION", "RETURN", "TAX")
SHA = re.compile(r"[0-9a-f]{64}\Z")
FLAGS = ("actual_reviewer_identity_verified", "actual_blindness_independently_verified",
         "gold_completeness_independently_verified", "semantic_accuracy_certified",
         "engine_quality_certified", "p0_go")


def invalid(reason):
    raise InvalidInput("COHORT_BLIND_" + reason)


def rate(n, d):
    return {"numerator": n, "denominator": d,
            "parts_per_million": (n * 1000000 + d // 2) // d if d else None}


def check_measurement(m):
    if type(m) is not dict or m.get("schema") != "IRE_V6_BLIND_ARITHMETIC_V1":
        invalid("RECEIPT_SCHEMA")
    if any(m.get(k) is not False for k in FLAGS):
        invalid("UNTRUSTED_SELF_APPROVAL")
    for k in ("source_sha256", "plan_sha256", "gold_sha256",
              "predictions_sha256", "alignment_sha256"):
        if type(m.get(k)) is not str or not SHA.fullmatch(m[k]):
            invalid("DIGEST")
    c, cats = m.get("counts"), m.get("by_category")
    if type(c) is not dict or set(c) != {"tp", "fp", "fn", "predictions", "gold"}:
        invalid("COUNTS_SCHEMA")
    if any(type(v) is not int or v < 0 for v in c.values()):
        invalid("COUNTS_NONINTEGER")
    if c["tp"] + c["fp"] != c["predictions"] or c["tp"] + c["fn"] != c["gold"]:
        invalid("COUNTS_CONSERVATION")
    if type(cats) is not dict or set(cats) != set(CATS):
        invalid("CATEGORY_CENSUS")
    total = {"tp": 0, "fp": 0, "fn": 0}
    hp = hg = 0
    for name in CATS:
        r = cats[name]
        if type(r) is not dict or set(r) != {"tp", "fp", "fn", "precision", "recall"}:
            invalid("CATEGORY_SCHEMA")
        if any(type(r[k]) is not int or r[k] < 0 for k in total):
            invalid("CATEGORY_NONINTEGER")
        for k in total:
            total[k] += r[k]
        if r["precision"] != rate(r["tp"], r["tp"] + r["fp"]) or (
                r["recall"] != rate(r["tp"], r["tp"] + r["fn"])):
            invalid("CATEGORY_RATE")
        if name != "OTHER":
            hp += r["tp"]
            hg += r["tp"] + r["fn"]
    if any(total[k] != c[k] for k in total):
        invalid("CATEGORY_TOTAL")
    if (m.get("precision") != rate(c["tp"], c["predictions"]) or
            m.get("recall") != rate(c["tp"], c["gold"]) or
            m.get("high_risk_recall") != rate(hp, hg) or
            m.get("precision_wilson_95") != _wilson95(c["tp"], c["predictions"]) or
            m.get("recall_wilson_95") != _wilson95(c["tp"], c["gold"]) or
            m.get("high_risk_recall_wilson_95") != _wilson95(hp, hg)):
        invalid("OVERALL_RATE_OR_INTERVAL")
    return c, hp, hg


def audit_cohort(prereg, reports):
    """Compute provisional micro metrics only after all nine pinned slots exist."""
    if (type(prereg) is not dict or
            prereg.get("schema") != "IRE_V6_PROSPECTIVE_SOURCE_BLIND_PREREGISTRATION_V1" or
            prereg.get("selected_video_count") != 9 or
            prereg.get("selected_cue_count") != 6829 or
            prereg.get("required_independent_source_first_reviewers") != 2 or
            prereg.get("required_separate_dispute_adjudicators") != 1 or
            prereg.get("precision_min_ppm") != 950000 or
            prereg.get("recall_min_ppm") != 900000 or
            prereg.get("high_risk_recall_min_ppm") != 950000 or
            prereg.get("min_total_gold_atoms_for_conclusive_evaluation") != 50 or
            prereg.get("min_high_risk_gold_atoms_for_conclusive_evaluation") != 30 or
            set(prereg.get("high_risk_categories", [])) != set(CATS) - {"OTHER"} or
            prereg.get("p0_go") is not False):
        invalid("PREREG_DRIFT")
    if type(reports) is not list or len(reports) > 9:
        invalid("REPORT_COUNT")
    slots, sources, preds = set(), set(), set()
    totals = dict.fromkeys(("tp", "fp", "fn", "predictions", "gold"), 0)
    high_tp = high_gold = 0
    digests = []
    for row in reports:
        if type(row) is not dict or set(row) != {"slot", "measurement"}:
            invalid("REPORT_SCHEMA")
        slot, m = row["slot"], row["measurement"]
        if type(slot) is not str or not re.fullmatch(r"S0[1-9]", slot) or slot in slots:
            invalid("SLOT_DUPLICATE_OR_INVALID")
        slots.add(slot)
        c, ht, hg = check_measurement(m)
        if m["source_sha256"] in sources or m["predictions_sha256"] in preds:
            invalid("DUPLICATE_SOURCE_OR_PREDICTION")
        sources.add(m["source_sha256"])
        preds.add(m["predictions_sha256"])
        for k in totals:
            totals[k] += c[k]
        high_tp += ht
        high_gold += hg
        digests.append({"slot": slot, "receipt_sha256": json_digest(m)})
    base = {"schema": "IRE_V6_PROSPECTIVE_COHORT_SCORE_V1",
            "reports_received": len(reports), "reports_required": 9,
            "independent_gold_verified": False,
            "reviewer_independence_verified": False,
            "chronological_blind_seal_independently_verified": False,
            "source_cohort_membership_independently_verified": False,
            "semantic_accuracy_certified": False, "research_complete": False,
            "p0_go": False}
    if len(reports) != 9:
        return dict(base, status="COHORT_INCOMPLETE_NO_SCORE",
                    precision_recall_measured=False)
    if slots != {f"S{i:02d}" for i in range(1, 10)}:
        invalid("MISSING_SLOT")
    threshold = bool(totals["predictions"] and totals["gold"] and high_gold and
        totals["tp"] * 1000000 >= 950000 * totals["predictions"] and
        totals["tp"] * 1000000 >= 900000 * totals["gold"] and
        high_tp * 1000000 >= 950000 * high_gold)
    return dict(base, status="SYNTHETIC_OR_UNVERIFIED_GOLD_PROVISIONAL_SCORE",
                receipt_census_sha256=json_digest(sorted(digests, key=lambda r:r["slot"])),
                counts=totals, high_risk_gold=high_gold,
                precision=rate(totals["tp"], totals["predictions"]),
                recall=rate(totals["tp"], totals["gold"]),
                high_risk_recall=rate(high_tp, high_gold),
                precision_wilson_95=_wilson95(totals["tp"], totals["predictions"]),
                recall_wilson_95=_wilson95(totals["tp"], totals["gold"]),
                high_risk_recall_wilson_95=_wilson95(high_tp, high_gold),
                preregistered_thresholds_met_arithmetically=threshold,
                minimum_gold_sample_met=totals["gold"] >= 50 and high_gold >= 30,
                prereg_gold_commitment_present=bool(type(prereg.get("gold_commitment_sha256")) is str
                    and SHA.fullmatch(prereg["gold_commitment_sha256"])),
                held_out_predictions_commitment_present=bool(
                    type(prereg.get("held_out_predictions_sha256")) is str
                    and SHA.fullmatch(prereg["held_out_predictions_sha256"])),
                precision_recall_measured=False)
