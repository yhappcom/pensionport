#!/usr/bin/env python3
"""V3.1 explicit periodic-interest math, without changing frozen V3.0 model.

An annual EFFECTIVE quote is not a nominal APR; a model lacking that
convention must fail-closed rather than call an old corrected claim wrong.
"""
from decimal import Decimal,localcontext
from v30_verified_core import guard,decimal
REQUIRED=frozenset({
    "model_type","annual_rate","annual_rate_convention","periods",
    "cashflow_timing","currency","principal_or_monthly_contribution",
    "includes_fees_taxes",
})
CONVENTIONS=frozenset(("EFFECTIVE_ANNUAL","NOMINAL_ANNUAL_DIVIDED_BY_12"))
def reproduce_v31(model):
    guard(type(model) is dict and REQUIRED<=set(model)
          and model["annual_rate_convention"] in CONVENTIONS
          and model["model_type"] in ("MONTHLY_SAVINGS_FUTURE_VALUE",
                                     "MONTHLY_AMORTIZING_PAYOUT")
          and model["cashflow_timing"] in ("END_OF_MONTH","BEGINNING_OF_MONTH")
          and model["currency"] in ("KRW","USD","JPY","EUR")
          and model["includes_fees_taxes"] is False,
          "MATH_RATE_TYPE_CASHFLOW_TIMING_OR_TAX_ASSUMPTION_MISSING")
    n=model["periods"]
    guard(type(n) is int and 1<=n<=1200,
          "MATH_PERIOD_MUST_BE_EXPLICIT_BOUNDED_INTEGER")
    principal=decimal(model["principal_or_monthly_contribution"])
    annual=decimal(model["annual_rate"])
    guard(principal>=0 and Decimal("-0.9")<=annual<=Decimal("1"),
          "ANNUAL_RATE_OR_PRINCIPAL_UNSUPPORTED")
    with localcontext() as ctx:
        ctx.prec=60
        m=(annual/Decimal(12) if
           model["annual_rate_convention"]=="NOMINAL_ANNUAL_DIVIDED_BY_12"
           else (Decimal(1)+annual)**(Decimal(1)/Decimal(12))-Decimal(1))
        # Separate explicit cashflow timing for both models:
        # FV beginning-of-month deposits accrue one extra month.
        if model["model_type"]=="MONTHLY_SAVINGS_FUTURE_VALUE":
            base=principal*n if m==0 else (
                principal*((1+m)**n-1)/m)
            closed=base*(1+m if model["cashflow_timing"]=="BEGINNING_OF_MONTH"
                         else 1)
            iterative=Decimal(0)
            for _ in range(n):
                if model["cashflow_timing"]=="BEGINNING_OF_MONTH":
                    iterative=(iterative+principal)*(1+m)
                else:
                    iterative=iterative*(1+m)+principal
        else:
            factor=sum(
                (1+m)**(-i if model["cashflow_timing"]=="END_OF_MONTH"
                        else -(i-1))
                for i in range(1,n+1))
            # Closed form calculates annuity payment; independent sum
            # calculates its present value to check it.
            if m==0:closed=principal/n
            else:
                closed=(principal*m/(1-(1+m)**(-n)))
                if model["cashflow_timing"]=="BEGINNING_OF_MONTH":
                    closed/=1+m
            iterative=principal/factor
        delta=abs(closed-iterative)
        guard(delta<=max(Decimal("0.005"),abs(closed)*Decimal("0.00000000001")),
              "INDEPENDENT_PERIODIC_MATH_METHODS_DIVERGED")
        observed=None
        if "asserted_value" in model:
            allowed_error=decimal(model.get("asserted_tolerance","1"))
            guard(allowed_error>=0,"NEGATIVE_TOLERANCE_FORBIDDEN")
            observed=abs(decimal(model["asserted_value"])-closed)<=allowed_error
        return {
         "schema":"V31_TYPED_FINANCE_MATH_V1",
         "model_type":model["model_type"],
         "annual_rate":str(annual),
         "annual_rate_convention":model["annual_rate_convention"],
         "derived_monthly_rate":str(m),
         "cashflow_timing":model["cashflow_timing"],
         "periods":n,
         "currency":model["currency"],
         "calculated_value":str(closed.quantize(Decimal("0.01"))),
         "independent_iterative_value":str(iterative.quantize(Decimal("0.01"))),
         "two_methods_agree":True,
         "asserted_claim_matches_given_model":observed,
         "model_assumptions_verified_from_source":False,
         "real_tax_and_product_terms_verified":False,
         "investment_performance_certified":False,
         "research_complete":False,
        }
