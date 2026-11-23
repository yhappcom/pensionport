"""Synthetic V6 scope propagation RED->GREEN; no owner source or secrets."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import sha256, json_digest
from ire.v6.errors import InvalidInput
from ire.v6.scope_link_audit import (
    audit_source_scope_inheritance,
    propose_scoped_context_overlay,
    simulate_unapproved_scope_overlay,
)


def make_srt(lines):
    parts=[]
    for i,line in enumerate(lines,1):
        parts.append(f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{line}")
    return ("\n\n".join(parts)+"\n").encode("utf8")


class ScopeLinkAuditTests(unittest.TestCase):
    def setUp(self):
        self.source=make_srt([
            "Introductory statement about financial education.",
            "This is a fictional sample ETF for teaching, not a live quote.",
            "The fictional ETF has a made-up NAV of 12,000 won.",
            "The fictional ETF has a made-up cost figure.",
            "This fictional example has no guaranteed returns.",
            "Index ETF comparison criteria apply to index ETFs only.",
            "This index ETF index-tracking metric is not universal.",
            "The speaker finishes the presentation.",
        ])
        self.raw={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
                  "source_sha256":sha256(self.source),"atoms":[
            {"claim_id":"C00001","kind":"HYPOTHETICAL",
             "source_refs":[{"cue_index":2,"quote":"fictional sample ETF"}],
             "condition_cue_indices":[],"context_cue_indices":[2],"exception_cue_indices":[]},
            {"claim_id":"C00002","kind":"HYPOTHETICAL",
             "source_refs":[{"cue_index":3,"quote":"made-up NAV"}],
             "condition_cue_indices":[],"context_cue_indices":[3],"exception_cue_indices":[]},
            {"claim_id":"C00003","kind":"HYPOTHETICAL",
             "source_refs":[{"cue_index":4,"quote":"made-up cost"}],
             "condition_cue_indices":[2],"context_cue_indices":[2,4],"exception_cue_indices":[]},
            {"claim_id":"C00004","kind":"RECOMMENDATION",
             "source_refs":[{"cue_index":7,"quote":"index-tracking metric"}],
             "condition_cue_indices":[6],"context_cue_indices":[6,7],"exception_cue_indices":[]},
        ]}
        self.rules=[{
            "rule_id":"FICTIONAL_SCOPED_SAMPLE", "scope_type":"FICTIONAL_EXAMPLE",
            "source_marker_cues":[{"cue_index":2,"quote":"fictional sample ETF"}],
            "required_cue_links":[2],"target_claim_ids":["C00001","C00002","C00003"],
            "require_automatic_coverage":True,"target_source_span":[2,4]},
            {
            "rule_id":"INDEX_ONLY_COMPARISON_1","scope_type":"INDEX_ONLY_COMPARISON",
            "source_marker_cues":[{"cue_index":6,"quote":"Index ETF comparison criteria"}],
            "required_cue_links":[6],"target_claim_ids":["C00004"],
            "require_automatic_coverage":False,"target_source_span":None,
        }]
        self.native_bytes=self.pack(self.raw)
        self.source_pin=sha256(self.source)
        self.native_pin=sha256(self.native_bytes)

    @staticmethod
    def pack(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode()

    def audit(self, **kwargs):
        kw=dict(original_srt=self.source,frozen_native=self.native_bytes,
                source_pin=self.source_pin,native_pin=self.native_pin,rules=self.rules)
        kw.update(kwargs)
        return audit_source_scope_inheritance(**kw)

    def overlay(self):
        return propose_scoped_context_overlay(self.source,self.native_bytes,
                                              source_pin=self.source_pin,native_pin=self.native_pin,
                                              rules=self.rules)

    def test_01_actual_red_finds_missing_dependent_scope_link_despite_kind_hypothetical(self):
        r=self.audit()
        self.assertEqual(r["status"],"HOLD_MISSING_STRUCTURAL_CONTEXT_SCOPE_LINKS")
        self.assertEqual(r["scoped_claim_rows"],4)
        self.assertEqual(r["missing_dependent_scope_link_count"],1)
        self.assertEqual(r["missing"][0]["claim_id"],"C00002")
        self.assertFalse(r["e2_approved"])
        self.assertIsNone(r["independent_precision"])

    def test_02_fictional_example_anchor_not_required_as_inherited_condition(self):
        r=self.audit()
        self.assertEqual(r["scope_marker_atom_count"],1)
        self.assertEqual([x["scope_status"] for x in r["detail"][:3]],
                         ["SOURCE_MARKER_ANCHOR","DEPENDENT_SCOPE_LINK_MISSING","DEPENDENT_WITH_SCOPE_LINK"])

    def test_03_index_only_link_covered_not_false_positive(self):
        r=self.audit()
        self.assertEqual(r["detail"][3]["scope_status"],"DEPENDENT_WITH_SCOPE_LINK")

    def test_04_generated_overlay_is_additive_unapproved_exactly_one_claim(self):
        ov=self.overlay()
        self.assertEqual(len(ov["changes"]),1)
        self.assertEqual(ov["changes"][0]["missing_cue_links"],[2])
        self.assertFalse(ov["owner_approved"])
        self.assertFalse(ov["e2_e3_e4_e5_release"])

    def test_05_in_memory_patch_green_original_sha_remains(self):
        before=self.native_bytes
        ov=self.overlay()
        green=simulate_unapproved_scope_overlay(self.source,self.native_bytes,
                                               source_pin=self.source_pin,native_pin=self.native_pin,
                                               rules=self.rules,overlay=ov)
        self.assertEqual(green["pre_overlay_missing"],1)
        self.assertEqual(green["post_overlay_missing"],0)
        self.assertEqual(before,self.native_bytes)
        self.assertFalse(green["p205_pass"])
        self.assertFalse(green["p206_unlocked"])

    def test_06_gold_metric_cannot_be_forged_from_structural_green(self):
        green=simulate_unapproved_scope_overlay(self.source,self.native_bytes,
                 source_pin=self.source_pin,native_pin=self.native_pin,
                 rules=self.rules,overlay=self.overlay())
        self.assertFalse(green["independent_gold"])
        self.assertFalse(green["confirmed_real_source_meaning"])

    def test_07_changed_original_raw_bytes_fail(self):
        with self.assertRaisesRegex(InvalidInput,"SRT_SHA_DRIFT"):
            self.audit(original_srt=self.source+b"unmatched")

    def test_08_changed_native_raw_bytes_fail(self):
        with self.assertRaisesRegex(InvalidInput,"PREDICTIONS_SHA_DRIFT"):
            self.audit(frozen_native=self.native_bytes+b" ")

    def test_09_native_pinned_source_not_same_rejected(self):
        d=copy.deepcopy(self.raw);d["source_sha256"]="0"*64
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"NATIVE_SOURCE_OR_ATOMS_INVALID"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_10_native_duplicate_claim_id_rejected(self):
        d=copy.deepcopy(self.raw);d["atoms"][2]["claim_id"]="C00001"
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"NATIVE_DUPLICATE_CLAIM"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_11_model_quote_spoof_rejected(self):
        d=copy.deepcopy(self.raw);d["atoms"][1]["source_refs"][0]["quote"]="There is a real ETF"
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"MODEL_QUOTE_NOT_VERBATIM"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_12_scope_marker_spoof_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["source_marker_cues"][0]["quote"]="not in original"
        with self.assertRaisesRegex(InvalidInput,"SOURCE_MARKER_MISSING_OR_FORGED"):
            self.audit(rules=t)

    def test_13_scope_marker_cue_reassigned_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["source_marker_cues"][0]["cue_index"]=1
        with self.assertRaisesRegex(InvalidInput,"SOURCE_MARKER_MISSING_OR_FORGED"):
            self.audit(rules=t)

    def test_14_selectively_hide_missing_claim_detected(self):
        t=copy.deepcopy(self.rules);t[0]["target_claim_ids"].remove("C00002")
        with self.assertRaisesRegex(InvalidInput,"TARGETS_DO_NOT_COVER_ALL_SCOPED_PREDICTIONS"):
            self.audit(rules=t)

    def test_15_add_claim_outside_span_detected(self):
        t=copy.deepcopy(self.rules);t[0]["target_claim_ids"].append("C00004")
        with self.assertRaisesRegex(InvalidInput,"TARGETS_DO_NOT_COVER_ALL_SCOPED_PREDICTIONS"):
            self.audit(rules=t)

    def test_16_no_automatic_target_scope_outside_span_accepted_as_explicit_subset(self):
        r=self.audit()
        self.assertEqual(r["scoped_claim_rows"],4)

    def test_17_duplicate_target_id_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["target_claim_ids"].append("C00001")
        with self.assertRaisesRegex(InvalidInput,"TARGETS_MISSING_DUPLICATE"):
            self.audit(rules=t)

    def test_18_unknown_target_id_rejected(self):
        t=copy.deepcopy(self.rules);t[1]["target_claim_ids"]=["C09999"]
        with self.assertRaisesRegex(InvalidInput,"TARGETS_MISSING_DUPLICATE"):
            self.audit(rules=t)

    def test_19_empty_targets_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["target_claim_ids"]=[]
        with self.assertRaisesRegex(InvalidInput,"TARGETS_MISSING_DUPLICATE"):
            self.audit(rules=t)

    def test_20_duplicate_rule_id_rejected(self):
        t=copy.deepcopy(self.rules);t[1]["rule_id"]=t[0]["rule_id"]
        with self.assertRaisesRegex(InvalidInput,"RULE_ID_DUPLICATE"):
            self.audit(rules=t)

    def test_21_no_rules_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"RULES_REQUIRED"):
            self.audit(rules=[])

    def test_22_bad_rule_schema_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["release_approved"]=True
        with self.assertRaisesRegex(InvalidInput,"RULE_SCHEMA_INVALID"):
            self.audit(rules=t)

    def test_23_rule_required_anchor_must_be_source_cited(self):
        t=copy.deepcopy(self.rules);t[0]["required_cue_links"]=[3]
        with self.assertRaisesRegex(InvalidInput,"RULE_REQUIRED_ANCHORS"):
            self.audit(rules=t)

    def test_24_rule_duplicate_source_marker_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["source_marker_cues"].append(t[0]["source_marker_cues"][0])
        with self.assertRaisesRegex(InvalidInput,"RULE_SOURCE_MARKER_MISSING_OR_FORGED"):
            self.audit(rules=t)

    def test_25_missing_native_condition_array_rejected(self):
        d=copy.deepcopy(self.raw);del d["atoms"][1]["condition_cue_indices"]
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"NATIVE_CUE_LINK_INVALID"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_26_duplicate_native_condition_link_rejected(self):
        d=copy.deepcopy(self.raw);d["atoms"][2]["condition_cue_indices"]=[2,2]
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"NATIVE_CUE_LINK_INVALID"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_27_link_out_of_source_range_rejected(self):
        d=copy.deepcopy(self.raw);d["atoms"][2]["condition_cue_indices"]=[99]
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"NATIVE_CUE_LINK_INVALID"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_28_independent_truth_not_certified_even_if_all_model_links_fixed(self):
        d=copy.deepcopy(self.raw)
        d["atoms"][1]["condition_cue_indices"]=[2]
        d["atoms"][1]["context_cue_indices"]=[2,3]
        b=self.pack(d)
        r=self.audit(frozen_native=b,native_pin=sha256(b))
        self.assertEqual(r["missing_dependent_scope_link_count"],0)
        self.assertFalse(r["confirmed_semantic_gold_accuracy"])
        self.assertFalse(r["ready_for_p0_2_06"])
        self.assertIsNone(r["independent_recall"])

    def test_29_partially_linked_in_context_without_condition_is_insufficient(self):
        d=copy.deepcopy(self.raw);d["atoms"][1]["context_cue_indices"]=[2,3]
        b=self.pack(d)
        r=self.audit(frozen_native=b,native_pin=sha256(b))
        self.assertEqual(r["missing_dependent_scope_link_count"],1)

    def test_30_partially_linked_in_condition_without_context_is_insufficient(self):
        d=copy.deepcopy(self.raw);d["atoms"][1]["condition_cue_indices"]=[2]
        b=self.pack(d)
        r=self.audit(frozen_native=b,native_pin=sha256(b))
        self.assertEqual(r["missing_dependent_scope_link_count"],1)

    def test_31_overlay_changed_claim_id_cannot_dryrun(self):
        ov=self.overlay();ov["changes"][0]["claim_id"]="C00001"
        with self.assertRaisesRegex(InvalidInput,"OVERLAY_NOT_VERBATIM"):
            simulate_unapproved_scope_overlay(self.source,self.native_bytes,
                    source_pin=self.source_pin,native_pin=self.native_pin,rules=self.rules,overlay=ov)

    def test_32_overlay_fabricated_signed_approval_cannot_dryrun(self):
        ov=self.overlay();ov["owner_approved"]=True
        with self.assertRaisesRegex(InvalidInput,"OVERLAY_NOT_VERBATIM"):
            simulate_unapproved_scope_overlay(self.source,self.native_bytes,
                    source_pin=self.source_pin,native_pin=self.native_pin,rules=self.rules,overlay=ov)

    def test_33_overlay_hidden_extra_link_cannot_dryrun(self):
        ov=self.overlay();ov["changes"].append({"rule_id":"FICTIONAL_SCOPED_SAMPLE","claim_id":"C00004","missing_cue_links":[2]})
        with self.assertRaisesRegex(InvalidInput,"OVERLAY_NOT_VERBATIM"):
            simulate_unapproved_scope_overlay(self.source,self.native_bytes,
                    source_pin=self.source_pin,native_pin=self.native_pin,rules=self.rules,overlay=ov)

    def test_34_missing_source_reference_cannot_launder(self):
        d=copy.deepcopy(self.raw);d["atoms"][1]["source_refs"]=[]
        b=self.pack(d)
        with self.assertRaisesRegex(InvalidInput,"MODEL_SOURCE_REFS_REQUIRED"):
            self.audit(frozen_native=b,native_pin=sha256(b))

    def test_35_bad_kind_rule_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["scope_type"]="SOME_KIND"
        with self.assertRaisesRegex(InvalidInput,"RULE_SCOPE_KIND_INVALID"):
            self.audit(rules=t)

    def test_36_integer_boolean_cue_indexes_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["source_marker_cues"][0]["cue_index"]=True
        with self.assertRaisesRegex(InvalidInput,"RULE_SOURCE_MARKER_MISSING"):
            self.audit(rules=t)

    def test_37_adversarial_duplicate_cue_link_rejected(self):
        t=copy.deepcopy(self.rules);t[0]["required_cue_links"]=[2,2]
        with self.assertRaisesRegex(InvalidInput,"RULE_REQUIRED_ANCHORS"):
            self.audit(rules=t)

    def test_38_forged_scope_semantic_quote_wrong_index_rejected(self):
        t=copy.deepcopy(self.rules);t[1]["source_marker_cues"][0]["quote"]="This is a fictional sample ETF"
        with self.assertRaisesRegex(InvalidInput,"RULE_SOURCE_MARKER_MISSING_OR_FORGED"):
            self.audit(rules=t)

    def test_39_all_input_claim_propositions_remain_unchanged_after_dryrun(self):
        original=copy.deepcopy(self.raw)
        ov=self.overlay()
        _=simulate_unapproved_scope_overlay(self.source,self.native_bytes,
             source_pin=self.source_pin,native_pin=self.native_pin,rules=self.rules,overlay=ov)
        self.assertEqual(original,self.raw)

    def test_40_rule_digest_changes_on_scope_anchor_change_without_claim_bytes(self):
        r=self.audit();t=copy.deepcopy(self.rules)
        t[0]["rule_id"]="FICTIONAL_SCOPED_REVISED"
        r2=self.audit(rules=t)
        self.assertNotEqual(r["scope_rules_sha256"],r2["scope_rules_sha256"])

if __name__ == "__main__": unittest.main()
