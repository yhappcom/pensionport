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
NUMBER = re.compile(r"(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?(?![A-Za-z0-9])")


def _read_measure(value: dict, cited_text: str, units: set[str]) -> tuple[Decimal, str]:
    require(type(value) is dict and set(value) == {
        "value", "unit", "source_literal"
    } and type(value["unit"]) is str and value["unit"] in units and
            type(value["source_literal"]) is str and
            1 <= len(value["source_literal"]) <= 128,
            "V3_CALC_MEASURE_SCHEMA_INVALID")
    literal = text_norm(value["source_literal"])
    require(literal in cited_text, "V3_CALC_SOURCE_LITERAL_NOT_CITED")
    unit_re = {
        "원": r"(?<![만억])원",
        "만원": r"만\s*원",
        "억원": r"억\s*원",
        "%": r"%|퍼센트",
        "개월": r"개월",
        "회": r"회",
        "년": r"년",
    }[value["unit"]]
    require(re.search(unit_re, literal) is not None,
            "V3_CALC_SOURCE_UNIT_NOT_TRACEABLE")
    number = decimal_input(value["value"])
    source_numbers = [Decimal(m.group().replace(",", ""))
                      for m in NUMBER.finditer(literal)]
    require(number in source_numbers, "V3_CALC_LITERAL_VALUE_NOT_TRACEABLE")
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
