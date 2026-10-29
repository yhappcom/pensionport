#!/usr/bin/env python3
"""Read-only, deterministic V4 model regression and provenance gate.

No external libraries or network calls. Does NOT validate future returns,
market data, the legal truth of external links, audiovisual claims, or personal
investment suitability. Historical model JSON is never rewritten.

Usage:
  python -B scripts/verify_v4_quant_models.py --self-test
  python -B scripts/verify_v4_quant_models.py --root .
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

MODEL_FILE = "data/synthesis/investment_knowledge_v4/models/decision_models_001_005_20261030.json"
MANIFEST_FILE = "data/synthesis/investment_knowledge_v4/reviews/v4_001_005_deep_research_manifest_20261030.json"
IDS = {
    "M01_ACCUMULATION", "M01_NPS_TOPUP", "M01_NPS_DELAY",
    "M01_WITHDRAWAL", "M01_ISA_TAX", "M02_DCA_PRICE_PATH",
    "M03_DEPLOYMENT", "M04_LOSS_RECOVERY", "M05_BUDGET_TDF_FEES",
}
VIDEOS = ["sz5N9WJS310", "6VEfKF7BzZU", "OiDTNstaSpM", "aNfGrcO6WPI", "qtluAViPpsQ"]


class GateError(ValueError):
    pass


class Audit:
    def __init__(self):
        self.checks = 0

    def require(self, name, condition):
        self.checks += 1
        if not condition:
            raise GateError(name)

    def equal(self, name, actual, expected):
        self.require(name, actual == expected)

    def close(self, name, actual, expected, tolerance=2.0):
        self.require(name + ":numeric",
                     isinstance(expected, (int, float))
                     and not isinstance(expected, bool)
                     and isinstance(actual, (int, float))
                     and math.isfinite(actual)
                     and math.isfinite(expected))
        self.require(name + ":difference",
                     math.isclose(actual, expected, rel_tol=0.0,
                                  abs_tol=tolerance))


def read_json(path):
    def reject_nan(value):
        raise GateError("Non-finite JSON constant: " + str(value))
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=reject_nan)


def future_value(payment, annual_rate, months):
    monthly = annual_rate / 12
    if monthly == 0:
        return payment * months
    return payment * ((1 + monthly) ** months - 1) / monthly


def present_value(payment, start_month, end_month, annual_discount):
    rate = (1 + annual_discount) ** (1 / 12) - 1
    return sum(payment / (1 + rate) ** (m + 1)
               for m in range(start_month, end_month))


def run_model_tests(document):
    a = Audit()
    a.equal("schema", document["schema_version"],
            "V4_001_005_NUMERIC_MODEL_1.0")
    models = document["models"]
    names = [m["id"] for m in models]
    a.equal("all nine model IDs have explicit test coverage",
            set(names), IDS)
    a.equal("duplicate models forbidden", len(names), len(IDS))
    m = {item["id"]: item for item in models}
    for item in models:
        a.require("source video within studies 001-005",
                  1 <= item["source_video"] <= 5)
        a.require("documented formula", bool(item.get("formula")))
        if item["id"] != "M01_ACCUMULATION":
            a.require("documented model limits", bool(item.get("limitation")))
    a.equal("no empirical validation misstatement",
            document["verification"]["independent_backtest"],
            "NOT_PERFORMED")
    a.equal("personal action blocked",
            document["verification"]["actual_client_after_tax_ranking"],
            "BLOCKED")
    a.equal("paths are synthetic",
            document["verification"]["input_market_data"], "SYNTHETIC")

    x = m["M01_ACCUMULATION"]
    for month in x["inputs"]["months"]:
        a.close("accumulation month " + str(month),
                future_value(x["inputs"]["monthly_krw"],
                             x["inputs"]["nominal_annual_rate"], month),
                x["result_krw"][str(month)])

    x = m["M01_NPS_TOPUP"]
    i = x["inputs"]
    for age in i["death_ages"]:
        for rate in i["annual_discount"]:
            start = (i["start_age"] - i["investment_age"]) * 12
            end = (age - i["investment_age"]) * 12
            month_rate = (1 + rate) ** (1 / 12) - 1
            amount = -i["paid_now_krw"] + sum(
                i["extra_monthly_krw"] / (1 + month_rate) ** month
                for month in range(start, end))
            a.close("topup age={} rate={}".format(age, rate),
                    amount, x["npv_krw"][str(age)][str(rate)])

    x = m["M01_NPS_DELAY"]
    i = x["inputs"]
    for age in i["death_ages"]:
        for rate in i["discount"]:
            end = (age - 65) * 12
            immediate = present_value(i["immediate_monthly_krw"],
                                      0, end, rate)
            delayed = present_value(i["delayed_monthly_krw"],
                                    i["delay_months"], end, rate)
            a.close("delay age={} rate={}".format(age, rate),
                    immediate - delayed,
                    x["pv_difference_immediate_minus_delayed_krw"][str(age)][str(rate)])

    x = m["M01_WITHDRAWAL"]
    i, result = x["inputs"], x["results"]
    annual_rates = i["net_return_assumptions"]
    a.equal("all withdrawal paths included",
            set(result["depletion_months"].keys()),
            {str(rate) for rate in annual_rates})
    for annual in annual_rates:
        bal, month_of_depletion = i["opening_balance_krw"], None
        for month in range(1, 1201):
            bal = bal * (1 + annual / 12) - i["monthly_cash_krw"]
            if bal <= 0:
                month_of_depletion = month
                break
        a.equal("withdrawal {} depletion".format(annual),
                month_of_depletion,
                result["depletion_months"][str(annual)])
    nominal_basis = i["hypothetical_deposits_krw"] + i["isa_rollovers_krw"]
    a.equal("tax-excluded hypothetical basis arithmetic", nominal_basis,
            result["nominal_tax_basis_max_before_credits_krw"])
    a.equal("full nominal source basis months",
            nominal_basis // i["monthly_cash_krw"],
            result["months_if_all_580m_qualify"])
    a.equal("12m tax-credited example months",
            (nominal_basis - 12_000_000) // i["monthly_cash_krw"],
            result["months_if_12m_credited"])
    a.equal("16 years nominal total withdrawals",
            16 * 12 * i["monthly_cash_krw"],
            result["srt_16yr_4m_withdrawal_krw"])

    x = m["M01_ISA_TAX"]
    i, r = x["inputs"], x["results_tax_krw"]
    base = i["eligible_net_gain_krw"]
    a.close("ISA ordinary taxable proxy", base * i["comparison_tax_including_local"],
            r["ordinary_taxable_proxy"])
    a.close("ISA ordinary case", max(0, base - i["ordinary_allowance_krw"])
            * i["tax_including_local"], r["isa_ordinary"])
    a.close("ISA preferential case",
            max(0, base - i["preferential_allowance_krw"])
            * i["tax_including_local"], r["isa_preferential"])

    x = m["M02_DCA_PRICE_PATH"]
    i = x["inputs"]
    n = i["monthly_purchases"]
    a.equal("every price scenario has corresponding result",
            set(i["synthetic_price_paths"]),
            set(x["returns_percent"]))
    for name, prices in i["synthetic_price_paths"].items():
        a.equal("price path length "+name, len(prices), n+1)
        a.require("strictly positive path prices "+name,
                  all(isinstance(v, (int, float)) and v > 0
                      for v in prices))
        total = i["initial_krw"]
        monthly = total / n
        cash, shares = total, 0.0
        for month in range(n):
            shares += monthly / prices[month]
            cash -= monthly
            if month < n-1:
                cash *= 1 + i["nominal_cash_yield"] / 12
        immediate = (prices[-1] / prices[0] - 1) * 100
        staged = ((shares * prices[-1] + cash) / total - 1) * 100
        a.close(name+" immediate", immediate,
                x["returns_percent"][name]["immediate"], 0.011)
        a.close(name+" staged", staged,
                x["returns_percent"][name]["staged"], 0.011)
    a.require("DCA counterexample: staged wins dip/recovery",
              x["returns_percent"]["decline_recover"]["staged"]
              > x["returns_percent"]["decline_recover"]["immediate"])
    a.require("DCA counterexample: immediate wins steadily rising",
              x["returns_percent"]["steady_rise"]["staged"]
              < x["returns_percent"]["steady_rise"]["immediate"])

    x = m["M03_DEPLOYMENT"]
    i = x["inputs"]
    principal, n, rate = (i["principal_krw"],
                          i["horizon_months"], i["cash_rate"])
    monthly = i["staged_monthly_krw"]
    pacing = x["source_pacing_reconciliation"]
    a.close("annual salary pacing", principal / 70_000_000,
            pacing["salary_proxy_years"], 0.00001)
    a.close("monthly salary pacing", principal / monthly,
            pacing["monthly_pace_months"], 0.00001)
    a.equal("rounded number of investment months",
            math.ceil(principal / monthly),
            pacing["calendar_months_with_partial_last"])
    a.equal("36 month deployment", monthly * 36,
            pacing["invested_in_36months_krw"])
    a.equal("36 month remaining", principal - monthly*36,
            pacing["left_in_36months_krw"])
    paths = {
        "equity_up_7pct": [(1.07)**(1/12)-1] * n,
        "equity_down_7pct": [(0.93)**(1/12)-1] * n,
        "flat": [0.0] * n,
        "first_year_down25_then_up7":
            [(0.75)**(1/12)-1] * 12 + [(1.07)**(1/12)-1] * (n-12),
    }
    amounts = {
        "immediate": principal,
        "staged_36m": principal / 36,
        "staged_4_5m": monthly,
        "staged_60m": principal / n,
    }
    a.equal("all retirement scenario paths included",
            set(paths), set(x["results_after_60months_krw"]))
    for name, monthly_returns in paths.items():
        for allocation, amount in amounts.items():
            cash, equity = principal, 0.0
            for month_return in monthly_returns:
                purchased = min(cash, amount)
                cash -= purchased
                equity = (equity + purchased) * (1 + month_return)
                cash *= 1 + rate / 12
            a.close(name+" "+allocation, cash + equity,
                    x["results_after_60months_krw"][name][allocation])
    a.require("retirement market path flip on rising market",
              x["results_after_60months_krw"]["equity_up_7pct"]["immediate"]
              > x["results_after_60months_krw"]["equity_up_7pct"]["staged_4_5m"])
    a.require("retirement market path flip on falling market",
              x["results_after_60months_krw"]["equity_down_7pct"]["immediate"]
              < x["results_after_60months_krw"]["equity_down_7pct"]["staged_4_5m"])

    x = m["M04_LOSS_RECOVERY"]
    i = x["inputs"]
    a.equal("loss scenario coverage",
            set(x["results_percent"]),
            {str(loss) for loss in i["loss_fraction"]})
    for loss in i["loss_fraction"]:
        a.require("loss is a fraction in (0,1)", 0 < loss < 1)
        a.close("loss recovery "+str(loss),
                100 * loss/(1-loss),
                x["results_percent"][str(loss)], 0.00001)

    x = m["M05_BUDGET_TDF_FEES"]
    i, r = x["inputs"], x["results"]
    a.equal("source budget addition",
            sum(i["source_allocation_krw"]),
            r["source_total_krw"])
    a.equal("available monthly money",
            i["hypothetical_net_income_krw"] - i["hypothetical_fixed_costs_krw"]
            - i["hypothetical_monthly_debt_krw"],
            r["hypothetical_disposable_krw"])
    low, high = i["tdf_fee_assumptions"]
    assert_low = future_value(i["tdf_monthly_krw"],
                              i["tdf_gross_assumed_return"] - low, i["months"])
    assert_high = future_value(i["tdf_monthly_krw"],
                               i["tdf_gross_assumed_return"] - high, i["months"])
    a.close("TDF lower fee", assert_low, r["tdf_fee_0_3pct_fv_krw"])
    a.close("TDF higher fee", assert_high, r["tdf_fee_1pct_fv_krw"])
    a.close("TDF fee difference", assert_low-assert_high, r["gap_krw"])
    a.require("lower fee increases hypothetical balance", assert_low>assert_high)
    return a.checks


def validate_index(root, document):
    a = Audit()
    manifest = read_json(root / MANIFEST_FILE)
    a.equal("model count in manifest",
            manifest["count"]["simulated_models"], len(IDS))
    a.equal("existing V3 claim total not inflated",
            manifest["count"]["existing_v3_claims"], 62)
    a.equal("no newly registered V3 claims",
            manifest["count"]["newly_registered_video_claims"], 0)
    a.equal("no approved personal action",
            manifest["count"]["actionable_personal_investment_approvals"], 0)
    a.equal("manifest model path", manifest["model_file"], MODEL_FILE)
    reviews = manifest["video_reviews"]
    a.equal("review count", len(reviews), 5)
    a.equal("unique video IDs", [x["video_id"] for x in reviews], VIDEOS)
    a.equal("source review V3 claim totals",
            sum(x["old_claim_count"] for x in reviews), 62)
    by_id = {m["id"]: m for m in document["models"]}
    linked = set()
    for n, r in enumerate(reviews, 1):
        a.equal("video numbering", r["video_number"], n)
        review = read_json(root / r["review_file"])
        a.equal("review source ID", review["video_id"], r["video_id"])
        a.equal("review V4 bounded status", review["outcome"],
                "V4_DEEP_RESEARCH_COMPLETE_WITH_EXTERNAL_OPEN")
        a.equal("review claim references",
                len(review["claim_triage"]), r["old_claim_count"])
        a.equal("review unresolved item count",
                len(review["unresolved"]), r["open_count"])
        a.require("audio not claimed verified",
                  review["source"]["original_audio_verified"] is False)
        a.require("frames not claimed verified",
                  review["source"]["onscreen_frames_verified"] is False)
        a.require("review blocks L3/L4 actions",
                  review["decision_use"]["L3_approved"] is False
                  and review["decision_use"]["L4_approved"] is False
                  and review["decision_use"]["action_approval_count"] == 0)
        pilot = read_json(root / review["existing_evidence"]["pilot_path"])
        old = read_json(root / review["existing_evidence"]["v3_path"])
        a.equal("original source SHA reference",
                review["source"]["original_SRT_SHA256"],
                pilot["source_audit"]["original_srt_sha256"])
        a.equal("no approval inflation from V3",
                (old["analysis_status"], old["approval"]),
                ("COMPLETE", "APPROVED"))
        a.equal("pilot claim IDs match source review",
                {c["claim_id"] for c in pilot["claims"]},
                {c["claim_id"] for c in review["claim_triage"]})
        a.equal("V3 claim IDs match source review",
                {c["claim_id"] for c in old["core_claims"]},
                {c["claim_id"] for c in review["claim_triage"]})
        for model_id in review["model_ids"]:
            a.require("review model link exists", model_id in by_id)
            if model_id != "M01_ISA_TAX":  # explicitly reused by study 002
                a.equal("model linked to correct video",
                        by_id[model_id]["source_video"], n)
            linked.add(model_id)
    a.equal("every numerical model included in video review",
            linked, IDS)
    return a.checks


def self_test(document):
    checks = run_model_tests(document)
    mutated = copy.deepcopy(document)
    mutated["models"][0]["result_krw"]["84"] += 10000
    try:
        run_model_tests(mutated)
    except GateError:
        pass
    else:
        raise GateError("mutation test failed to reject incorrect result")
    removed = copy.deepcopy(document)
    removed["models"].pop()
    try:
        run_model_tests(removed)
    except GateError:
        pass
    else:
        raise GateError("mutation test failed to reject missing model")
    return {"mode": "self_test", "status": "PASS",
            "recalculation_checks": checks, "negative_tests": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        data = read_json(root / MODEL_FILE)
        if args.self_test:
            result = self_test(data)
        else:
            n1 = run_model_tests(data)
            n2 = validate_index(root, data)
            result = {"mode": "repository_gate", "status": "PASS",
                      "models_recalculated": len(IDS),
                      "model_checks": n1, "provenance_checks": n2,
                      "total_checks": n1+n2,
                      "scope": "Deterministic hypothetical arithmetic and source links only; not market backtesting or personal advice"}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (GateError, ValueError, KeyError, TypeError, OSError, ZeroDivisionError, OverflowError) as exc:
        print(json.dumps({"status":"FAIL", "error":str(exc),
                          "type":type(exc).__name__}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
