#!/usr/bin/env python3
"""Public source-native 11 raw label discrepancy triage gate, zero false research GO.

Proof is restricted to hash custody, coherent four-way category census, and
negative release assertions. Real owner quotes are only in private Library and
never available to this public CI. Category diagnoses are same-chat opinions.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG,STATE,validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER,validate as current_status_validate
from scripts.ire_p0_2_05_gold_readiness_gate import verify as p205_baseline_verify
from scripts.ire_p0_2_05_source71_compare_gate import verify as crosswalk_verify

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=Path('docs/IRE_P0_2_05_11_KIND_PAIR_SOURCE_GROUNDED_TRIAGE_SHA_ONLY_20261123.json')
SRC='e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b'
NATIVE='c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb'
SOURCE_FIRST='bbb9ce9ee3fabf5c49bdf9c3154a68955e360db4000cfb354070c307e215abfe'
CROSSWALK='9e67f6b3630821557f70351900e3dc9a4e80f55b3afc2e70a515d5d59aa12c2b'
TRIAGE='ca05ca0edd04a9e07a52065c0eee7d33025c94af96425b44953d389bbe940b7c'
ZIP='39377a02dabc87d0b24aba6a88935f23c2241959abd57d6a3a60d49bc5610f06'
GROUPS={
    'DISTINCT_PROPOSITION_TOPIC_ONLY':4,
    'EVALUATION_PLUS_GUIDANCE':3,
    'EMPIRICAL_UTTERANCE_NOT_VERIFIED':3,
    'META_REPORTING_VS_EMBEDDED_CLAIM':1,
}


def load(root,path):return json.loads((Path(root)/path).read_text(encoding='utf8'))


def verify(root=ROOT,*,receipt=None,state=None,ledger=None,historical_only=False):
    root=Path(root)
    r=load(root,RECEIPT) if receipt is None else receipt
    s=load(root,STATE) if state is None else state
    l=load(root,LEDGER) if ledger is None else ledger
    errors=[]
    def check(ok,code):
        if not ok:errors.append('P205_11_PAIR_'+code)
    if not historical_only:
        check(not checklist_validate(load(root,CATALOG),s,root=root),'CHECKLIST_POLICY')
        check(not current_status_validate(l,root=root),'E2_E3_E4_E5_CANONICAL_STATUS')
        check(not p205_baseline_verify(root, state=s, ledger=l),'EXISTING_P205_GOLD_HOLD')
        check(not crosswalk_verify(root,state=s,ledger=l),'PREVIOUS_SOURCE71_NATIVE68_CROSSWALK_HOLD')
        rows=s.get('items',[])
        check(len(rows)==60 and all(x.get('status')=='PASS' for x in rows[:16])
              and rows[16].get('id')=='P0-2-05' and rows[16].get('status')=='HOLD'
              and all(x.get('status')=='BLOCKED' for x in rows[17:]),
              'PREVIOUS_16_PASS_NEXT_43_BLOCKED')
        dev=l.get('development_gate',{})
        details=dev.get('p0_2_05_independent_gold_readiness',{})
        check(dev.get('this_item')=='P0-2-05' and dev.get('pending_next_item')=='P0-2-05'
              and details.get('status')=='HOLD_NO_CERTIFIABLE_INDEPENDENT_ATOMIC_GOLD',
              'CURRENT_CURSOR_UNCHANGED')
    check(r.get('schema')=='IRE_P205_KIND_TRIAGE_11_PAIRS_PROVISIONAL_SHA_ONLY_V1'
          and r.get('item_id')=='P0-2-05' and r.get('as_of')=='2026-11-23',
          'SCHEMA_ID_DATE')
    for field,value in [('source_sha256',SRC),('frozen_native_sha256',NATIVE),
                        ('source_first_71_sha256',SOURCE_FIRST),('crosswalk_71_68_sha256',CROSSWALK),
                        ('kind_triage_private_json_sha256',TRIAGE),('kind_triage_private_zip_sha256',ZIP)]:
        check(r.get(field)==value,'FROZEN_HASH_'+field)
    check(r.get('kind_triage_private_library_file_id')=='libfile_49190596f1e481918c8221cc297a79a2'
          and r.get('kind_triage_private_library_path')==
          '/투자연구_비공개/ETF250/P205_PRIVATE_ETF250_11_KIND_TRIAGE_PROVISIONAL_HOLD_20261123.zip',
          'PRIVATE_ORIGINAL_CUSTODY')
    check(r.get('video_id')=='LVE7XN_esTc' and r.get('source_original_cues_checked')==250
          and r.get('source_provisional_claims')==71 and r.get('frozen_native_unapproved_claims')==68
          and r.get('topic_related_crosswalk_label_discrepancy_pairs')==11
          and r.get('triaged_groups')==GROUPS
          and sum(r.get('triaged_groups',{}).values())==11,
          'FOUR_CATEGORY_COUNT_AND_REAL_SOURCE_SCOPE')
    check(r.get('all_11_cue_quotes_and_native_source_quotes_verified_against_real_original') is True
          and r.get('triaged_groups_are_independently_approved') is False
          and r.get('semantic_truth_of_group_resolution_proven') is False
          and r.get('confirmed_engine_misclassification_count') is None
          and r.get('all_10_high_risk_review_queues_open') is True
          and r.get('high_risk_review_queue_count')==10,
          'CANNOT_CLAIM_CROSSWALK_SEMANTIC_TRUTH_OR_SILENTLY_CLOSE_RISK')
    check(all(r.get(k) is False for k in (
        'source_cues_outside_claim_context_confirmed_absent','strict_one_to_one_atomic_gold_proven',
        'triaged_groups_are_independently_approved','semantic_truth_of_group_resolution_proven')),
        'NO_FALSE_ATOMIC_COMPLETENESS_OR_GOLD')
    check(r.get('independent_reviewer_sessions')==0
          and r.get('independent_gold_atoms')==0
          and all(r.get(k) is None for k in (
              'independent_precision','independent_recall','independent_high_risk_false_negative_count')),
          'NO_FORGED_INDEPENDENT_METRICS')
    check(r.get('minimum_precision_basis_points')==9500
          and r.get('minimum_recall_basis_points')==9800
          and r.get('high_risk_fn_max')==0,
          'ASSESSMENT_TARGETS_CANNOT_CHANGE')
    check(r.get('source_first_diagnostic_remains_same_chat_nonindependent') is True
          and r.get('topic_only_relation_cannot_become_gold_match') is True
          and r.get('private_source_or_claim_text_in_public_github') is False
          and r.get('source_quote_cryptographic_check_not_semantic_entailment') is True
          and r.get('no_new_e2_e3_e4_e5_approvals') is True,
          'FALSE_SOURCE_SEMANTIC_APPROVAL')
    check(r.get('checklist_passed')==16 and r.get('item_state')=='HOLD'
          and r.get('next_item')=='P0-2-06' and r.get('next_status')=='BLOCKED'
          and r.get('main_branch_must_remain_unchanged') is True
          and r.get('software_stage')=='REVALIDATE_SAME_SHA_6_OF_6_REQUIRED'
          and r.get('financial_research_stage')=='UNMEASURABLE_INDEPENDENT_GOLD_HOLD',
          'SEQUENTIAL_GATE_FALSE_GO')
    check(r.get('technical_module')=='ire/v6/kind_triage.py'
          and r.get('technical_adversarial_tests')=='ire/v6/tests/test_p205_kind_triage.py'
          and (root/r['technical_module']).is_file()
          and (root/r['technical_adversarial_tests']).is_file(),
          'CODE_AND_TEST_PATHS_MISSING')
    return errors


def main():
    from scripts.ire_p205_history import verify_history
    from scripts.ire_p205_live_release import verify_current
    e=verify_history(ROOT)+verify_current(ROOT)
    for item in e:print('P205_11_KIND_DIAGNOSTIC_FAIL',item,file=sys.stderr)
    if e:return 1
    print('P205_HISTORICAL_AND_LIVE_GATE_PASS')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
