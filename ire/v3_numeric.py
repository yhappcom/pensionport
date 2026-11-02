"""IRE V3 deterministic arithmetic discrepancy checks over cited NEW-IRE claims.

Calculations use exact Decimal operands. The assistant supplies an equation,
units and source literals; each literal must exist in the new claim's original
quoted subtitle cues and its numeric value must agree with the literal's
Arabic number. Arithmetic consistency alone is NOT investment/financial truth.
"""
from __future__ import annotations

from decimal import Decimal
import re

from .source import require, text_norm
from .research import decimal_input
from .knowledge import validate_knowledge

SCHEMA = "IRE_V3_CITED_FINANCE_CALCULATION_V1"
ALLOWED = {"NET_AFTER_PERCENT", "REMAINDER_AFTER_PERIODIC",
           "MULTIPLY_PERIODIC", "PAYBACK_PERIOD"}
MONEY = {"원": Decimal(1), "만원": Decimal(10000),
         "억원": Decimal(100000000)}
COUNT = {"개월", "회"}
TIME = {"개월", "년"}
# Match a value and its *adjacent* financial unit as one lexical token.
# Literal substring membership is insufficient: "100만원" must not match
# "1100만원", and "100원" must not match "100만원".
NUMBER_WITH_UNIT = re.compile(
    r"(?<![0-9,.])(?P<number>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<unit>억\s*원|만\s*원|원|%|퍼센트|개월|회|년)"
)
NORMALIZE_UNIT = {"억 원": "억원", "만 원": "만원", "퍼센트": "%"}


def _exact_cited_literal(literal: str, cited_text: str) -> bool:
    # Reject a user-selected numeric substring of a longer financial amount.
    return re.search(r"(?<![0-9,.])" + re.escape(literal) +
                     r"(?![0-9,.])", cited_text) is not None


def _normalized_money_unit(unit: str) -> str:
    return NORMALIZE_UNIT.get(re.sub(r"\s+", " ", unit).strip(), unit)


def _read_measure(value: dict, cited_text: str, units: set[str]) -> tuple[Decimal, str]:
    require(type(value) is dict and set(value) == {
        "value", "unit", "source_literal"
    } and type(value["unit"]) is str and value["unit"] in units and
            type(value["source_literal"]) is str and
            1 <= len(value["source_literal"]) <= 128,
            "V3_CALC_MEASURE_SCHEMA_INVALID")
    literal = text_norm(value["source_literal"])
    require(_exact_cited_literal(literal, cited_text),
            "V3_CALC_SOURCE_LITERAL_NOT_CITED")
    matches = [(Decimal(m.group("number").replace(",", "")),
                _normalized_money_unit(m.group("unit")))
               for m in NUMBER_WITH_UNIT.finditer(literal)]
    require(any(unit == value["unit"] for _, unit in matches),
            "V3_CALC_SOURCE_UNIT_NOT_TRACEABLE")
    number = decimal_input(value["value"])
    require((number, value["unit"]) in matches,
            "V3_CALC_LITERAL_VALUE_NOT_TRACEABLE")
    require(abs(number) <= Decimal("1e16"),
            "V3_CALC_VALUE_OUT_OF_RANGE")
    return number, value["unit"]


def check_cited_calculation(knowledge: dict, submission: dict) -> dict:
    validate_knowledge(knowledge)
    require(type(submission) is dict and set(submission) == {
        "schema", "global_claim_id", "operation", "operands",
        "reported_result"
    } and submission["schema"] == SCHEMA and
            submission["operation"] in ALLOWED,
            "V3_CALC_SUBMISSION_CONTRACT_INVALID")
    match = next((x for x in knowledge["claims"] if
                  x["global_claim_id"] == submission["global_claim_id"]), None)
    require(match is not None, "V3_CALC_UNREGISTERED_CLAIM")
    source = text_norm(" ".join(ref["quote"] for ref in match["source_refs"]))
    operands = submission["operands"]
    require(type(operands) is dict, "V3_CALC_OPERANDS_INVALID")
    op = submission["operation"]
    expected_keys = {
        "NET_AFTER_PERCENT": {"gross", "percent"},
        "REMAINDER_AFTER_PERIODIC": {"principal", "periodic", "periods"},
        "MULTIPLY_PERIODIC": {"periodic", "periods"},
        "PAYBACK_PERIOD": {"initial_cost", "monthly_increase"},
    }[op]
    require(set(operands) == expected_keys,
            "V3_CALC_OPERAND_NAMES_INVALID")
    values = {}
    for key, row in operands.items():
        units = ({"%"} if key == "percent" else
                 COUNT if key == "periods" else set(MONEY))
        values[key] = _read_measure(row, source, units)
    monetary_units = {
        unit for key, (_, unit) in values.items() if
        key not in ("percent", "periods")
    }
    require(len(monetary_units) == 1,
            "V3_CALC_MIXED_CURRENCY_UNIT_REQUIRES_EXPLICIT_CONVERSION")
    currency_unit = next(iter(monetary_units))
    scale = MONEY[currency_unit]
    if "percent" in values:
        require(Decimal(0) <= values["percent"][0] <= Decimal(100),
                "V3_CALC_PERCENT_OUT_OF_RANGE")
    if "periods" in values:
        require(values["periods"][0] >= 0 and
                values["periods"][0] == values["periods"][0].to_integral_value(),
                "V3_CALC_PERIOD_COUNT_INVALID")
    if op == "NET_AFTER_PERCENT":
        amount = values["gross"][0] * scale
        computed_won = amount * (1 - values["percent"][0] / 100)
        output_unit = currency_unit
        calculated = computed_won / scale
    elif op == "REMAINDER_AFTER_PERIODIC":
        computed_won = (values["principal"][0] -
                        values["periodic"][0] * values["periods"][0]) * scale
        output_unit = currency_unit
        calculated = computed_won / scale
    elif op == "MULTIPLY_PERIODIC":
        computed_won = (values["periodic"][0] *
                        values["periods"][0]) * scale
        output_unit = currency_unit
        calculated = computed_won / scale
    else:
        require(re.search(
            r"매\s*(?:월|달)|(?:한\s*)?달\s*(?:마다|에)|월\s*[0-9]",
            source) is not None,
            "V3_CALC_MONTHLY_FREQUENCY_NOT_SOURCE_TRACEABLE")
        require(values["monthly_increase"][0] > 0,
                "V3_CALC_PAYBACK_DENOMINATOR_ZERO_OR_NEGATIVE")
        calculated = (values["initial_cost"][0] /
                      values["monthly_increase"][0])
        output_unit = "개월"
        computed_won = None
    reported = submission["reported_result"]
    if reported is None:
        claimed = None
        consistent = None
        difference = None
    else:
        allowed_units = TIME if op == "PAYBACK_PERIOD" else set(MONEY)
        claimed, reported_unit = _read_measure(reported, source, allowed_units)
        if op == "PAYBACK_PERIOD":
            amount_to_compare = claimed * (12 if reported_unit == "년" else 1)
        else:
            amount_to_compare = claimed * MONEY[reported_unit] / scale
        difference = amount_to_compare - calculated
        consistent = abs(difference) <= Decimal("0.00000001")
    return {
        "schema": "IRE_V3_CITED_CALCULATION_AUDIT_V1",
        "global_claim_id": match["global_claim_id"],
        "operation": op,
        "computed_value": str(calculated),
        "computed_unit": output_unit,
        "reported_value": str(claimed) if claimed is not None else None,
        "reported_unit": reported["unit"] if reported is not None else None,
        "difference_in_computed_unit": str(difference) if difference is not None else None,
        "arithmetic_consistent": consistent,
        "source_literals_traceable": True,
        "currency_conversions_grounded_by_fixed_units": True,
        "tax_and_legal_assumptions_verified": False,
        "financial_truth_certified": False,
        "investment_recommendation_authorized": False,
    }


def main() -> int:
    """Private and immutable arithmetic audit. No personal numbers on stdout."""
    import argparse
    import json
    import os
    from pathlib import Path
    from .cli import private_file
    from .knowledge import read_private_snapshot
    from .checkpoint import safe_private_directory
    from .source import sha256

    parser = argparse.ArgumentParser(
        description="Check quoted financial arithmetic without model API")
    parser.add_argument("operation", choices=["verify"])
    parser.add_argument("--private-knowledge-snapshot", required=True)
    parser.add_argument("--private-calculation", required=True)
    parser.add_argument("--private-audit-dir", required=True)
    args = parser.parse_args()
    try:
        knowledge = read_private_snapshot(args.private_knowledge_snapshot)
        submission = json.loads(private_file(
            args.private_calculation).read_text(encoding="utf-8"))
        audit = check_cited_calculation(knowledge, submission)
        body = {
            **audit, "knowledge_snapshot_sha256": knowledge["snapshot_sha256"],
            "calculation_submission_sha256": sha256(json.dumps(
                submission, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False).encode("utf-8")),
        }
        encoded = json.dumps(body, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        digest = sha256(encoded)
        content = {
            **body, "audit_sha256": digest,
        }
        root = safe_private_directory(args.private_audit_dir)
        target = root / ("ire_v3_arithmetic_" + digest + ".json")
        raw = json.dumps(content, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            target.unlink(missing_ok=True)
            raise
        print(json.dumps({
            "schema": "IRE_V3_ARITHMETIC_PRIVATE_AUDIT_RECEIPT",
            "status": ("REVIEW_REQUIRED_DIFFERENCE" if
                       audit["arithmetic_consistent"] is False else
                       "CONSISTENT_UNVERIFIED" if
                       audit["arithmetic_consistent"] is True else
                       "CALCULATED_WITHOUT_REPORTED_VALUE"),
            "audit_sha256": digest,
            "private_audit_path": str(target),
            "financial_truth_approved": False,
            "model_api_calls": 0,
        }, ensure_ascii=False, sort_keys=True))
        return 2
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        print(json.dumps({
            "schema": "IRE_V3_ARITHMETIC_ERROR", "status": "FAILED_CLOSED"
        }))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())