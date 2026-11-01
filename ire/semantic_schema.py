"""Strict Structured Outputs contract for original-only financial proposition extraction.

The schema constrains syntactic outputs; exact citation, cue census, and
financial meaning still require independent runtime and human validation.
"""
from __future__ import annotations

ATOM_KINDS=[
    "REGULATION","PRODUCT","NUMERIC","STRATEGY","EMPIRICAL",
    "MECHANISM","OPINION","OTHER"]
MODALITIES=[
    "ASSERTION","CONDITIONAL","NEGATION","HYPOTHESIS","QUESTION",
    "PREFERENCE","UNRESOLVED"]
CUE_STATES=["LINKED","NONCLAIM_CANDIDATE","UNRESOLVED"]

def _obj(properties):
    return {
        "type":"object",
        "properties":properties,
        "required":list(properties),
        "additionalProperties":False
    }

NULLABLE_STRING={"type":["string","null"]}
NUMBER=_obj({
    "value_text":{"type":"string"},
    "unit":{"type":"string"},
    "measure_kind":{"type":"string"},
    "reference_cue":{"type":"integer"}
})
FINANCIAL_FRAME=_obj({
    "subject":NULLABLE_STRING,
    "product":NULLABLE_STRING,
    "financial_event":NULLABLE_STRING,
    "action":NULLABLE_STRING,
    "object":NULLABLE_STRING,
    "jurisdiction":NULLABLE_STRING,
    "effective_date":NULLABLE_STRING,
    "conditions":{"type":"array","items":{"type":"string"}},
    "exceptions":{"type":"array","items":{"type":"string"}},
    "measurements":{"type":"array","items":NUMBER},
    "modality":{"type":"string","enum":MODALITIES}
})
SOURCE_REF=_obj({
    "cue_index":{"type":"integer"},
    "quote":{"type":"string"}
})
ATOM=_obj({
    "proposition":{"type":"string"},
    "claim_types":{"type":"array","items":{
        "type":"string","enum":ATOM_KINDS}},
    "frame":FINANCIAL_FRAME,
    "source_refs":{"type":"array","items":SOURCE_REF}
})
DISPOSITION=_obj({
    "cue_index":{"type":"integer"},
    "status":{"type":"string","enum":CUE_STATES},
    "reason":{"type":["string","null"]}
})
SEMANTIC_SCHEMA=_obj({
    "claims":{"type":"array","items":ATOM},
    "cue_dispositions":{"type":"array","items":DISPOSITION}
})
