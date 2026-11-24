"""Append-only review tranche check against an externally retained prior receipt.

No claim truth, release or journal integration is implied by this check.
"""
from .codec import json_digest
from .semantic_obligation_review import review_batch,need


def append_review(source,graph,old,candidates,prior_rows,new_rows,prior_receipt,*,expected_prior_receipt_sha256,**pins):
    need(type(prior_rows) is list and type(new_rows) is list and bool(new_rows),'TRANCHE_SHAPE')
    need(json_digest(prior_receipt)==expected_prior_receipt_sha256,'PRIOR_RECEIPT_PIN')
    before=review_batch(source,graph,old,candidates,prior_rows,**pins)
    need(before==prior_receipt,'PRIOR_REPLAY_DRIFT')
    added=review_batch(source,graph,old,candidates,new_rows,**pins)
    # The full review rejects duplicates across tranches, including modified repeats.
    combined=review_batch(source,graph,old,candidates,prior_rows+new_rows,**pins)
    need(combined['reviewed']==before['reviewed']+added['reviewed'],'TRANCHE_CENSUS')
    return {'schema':'IRE_V3_OBLIGATION_TRANCHE_APPEND_V1','prior_receipt_sha256':expected_prior_receipt_sha256,
            'added':added,'cumulative':combined,'prior_rows_unchanged':True,
            'publication_authorized':False,'financial_approval':False}
