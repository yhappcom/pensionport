#!/usr/bin/env python3
"""P205 independent atomic-gold readiness release-negative SHA-only gate.

Public GitHub CI cannot access private user SRT or produce independent gold.
It checks plan/owner-private evidence custody and denies fabricated FP/FN scores.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG, STATE, validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER, validate as status_validate

ROOT=Path(__file__).resolve().parents[1]
P205=Path('docs/IRE_P0_2_05_SOURCE_ONLY_BLIND_GOLD_READINESS_HOLD_SHA_20261123.json')
PLAN=Path('docs/IRE_P0_2_05_ETF250_BLIND_GOLD_PREREGISTRATION_20261123.json')
SRC_SHA='e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b'
NATIVE_SHA='c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb'
ZIP_SHA='e9b8966995c0b91b05516458d95d4df1fc5bd27bd44fd7ead7298b80c9c1d8cb'
PACKET_SHA='bbd326a8c7b2e39acc65161400ae97b221616f13514cbb3e5492eac6019734b6'
V228_SHA='9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397'
PLAN_BLOB='481a4b809c3058b16f56d54fe3bad820ed972dd8'


def load(root,p):
    return json.loads((Path(root)/p).read_text(encoding='utf8'))


def verify(root=ROOT, *, receipt=None, state=None, ledger=None, plan=None):
    root=Path(root)
    r=receipt if receipt is not None else load(root,P205)
    s=state if state is not None else load(root,STATE)
    l=ledger if ledger is not None else load(root,LEDGER)
    p=plan if plan is not None else load(root,PLAN)
    errors=[]
    def need(cond, name):
        if not cond:errors.append('P205_'+name)
    need(not checklist_validate(load(root,CATALOG),s,root=root),'CHECKLIST_60_ITEM_POLICY_INVALID')
    need(not status_validate(l,root=root),'OFFICIAL_E1_E5_HOLD_STATUS_INVALID')
    rows=s.get('items',[])
    position=next((i for i,v in enumerate(rows) if v.get('status')!='PASS'),len(rows))
    live=rows[position]['id'] if position<len(rows) else 'ALL_COMPLETE'
    need(len(rows)==60 and position==16 and all(v.get('status')=='PASS' for v in rows[:16])
         and rows[16].get('id')=='P0-2-05' and rows[16].get('status') in
         {'READY','IN_PROGRESS','HOLD','FAIL'} and rows[17].get('id')=='P0-2-06'
         and all(v.get('status')=='BLOCKED' for v in rows[17:]),
         'PREVIOUS_16_PASS_AND_P205_ACTIVE_P206_BLOCKED')
    gate=l.get('development_gate',{})
    need(gate.get('this_item')==live and gate.get('pending_next_item')==live,
         'LEDGER_CANNOT_ADVANCE_TO_P206_WITHOUT_INDEPENDENT_GOLD')
    need(r.get('schema')=='IRE_P0_2_05_SOURCE_ONLY_BLIND_GOLD_READINESS_HOLD_SHA_V1'
         and r.get('item_id')=='P0-2-05' and r.get('as_of')=='2026-11-23'
         and r.get('status')=='HOLD_INDEPENDENT_BLIND_ATOMIC_GOLD_NOT_AVAILABLE',
         'RECEIPT_SCHEMA_OR_HOLD_VERDICT')
    need(p.get('schema')=='IRE_P0_2_05_ETF250_PREREGISTERED_BLIND_ATOMIC_GOLD_PLAN_V1'
         and p.get('item_id')=='P0-2-05' and p.get('as_of')=='2026-11-23'
         and p.get('status')=='FROZEN_RUBRIC_NOT_INDEPENDENT_GOLD'
         and p.get('gold_locked_or_metrics_scored_before_revision') is False
         and p.get('preregistration_revision')=='V2_PRE_GOLD_LOCK_INTEGER_BASIS_POINTS_FIX'
         and p.get('prior_unscored_plan_git_blob_sha')=='be5985b5c58a766ee27f56a2f4bb0259fa2fceb1',
         'PREREGISTERED_BEFORE_METRICS_AND_VERSIONED_RUBRIC')
    need(p.get('assessment',{}).get('sampling')=='NO_SAMPLING_FULL_250_CUES'
         and p.get('assessment',{}).get('gold_unit')=='ATOMIC_SEMANTIC_CLAIM_NOT_CAPTION'
         and p.get('assessment',{}).get('thresholds')=={
            'atomic_precision_min_bp':9500,'atomic_recall_min_bp':9800,
            'high_risk_false_negative_max':0},
         'TARGETS_95_98_ZERO_HIGH_RISK_FN_ATOM_LEVEL')
    need(p.get('source',{}).get('original_srt_sha256')==SRC_SHA
         and p.get('source',{}).get('original_zip_sha256')==V228_SHA
         and p.get('source',{}).get('cue_count')==250
         and p.get('predictions',{}).get('frozen_v228_native_sha256')==NATIVE_SHA
         and p.get('predictions',{}).get('original_unapproved_atom_count')==68,
         'PLAN_PINNED_REAL_SOURCE_250_PREDICTION_68')
    need(p.get('independence_contract',{}).get('two_separate_blind_adjudications_and_consensus_required') is True
         and p.get('independence_contract',{}).get('chatgpt_same_conversation_reviewer_without_proven_blinding_is_independent') is False
         and p.get('independence_contract',{}).get('internally_reconstructed_source_first_gold_is_not_independent') is True
         and p.get('current_eligible_independent_gold_file_count')==0
         and p.get('current_gold_rows_independently_certified')==0
         and p.get('precision') is None and p.get('recall') is None
         and p.get('high_risk_false_negative_count') is None,
         'NO_FAKE_BLINDED_GOLD_FROM_PRIOR_CHAT_SELF_LABELS')
    for k,v in [('source_srt_sha256',SRC_SHA),
                ('source_v228_zip_sha256',V228_SHA),
                ('source_native_prediction_json_sha256',NATIVE_SHA),
                ('preregistration_rubric_git_blob_sha',PLAN_BLOB),
                ('gold_candidate_source_only_intake_sha256',ZIP_SHA),
                ('gold_candidate_source_only_intake_json_sha256',PACKET_SHA)]:
        need(r.get(k)==v,'EVIDENCE_HASH_'+k)
    need(r.get('gold_source_only_private_library_file_id')==
         'libfile_19a5e7e565f0819199ac8c0b50fe49a8'
         and r.get('gold_source_only_private_library_path')==
         '/투자연구_비공개/ETF250/P205_PRIVATE_ETF250_SOURCE_ONLY_BLIND_INTAKE_UNSCORED_20261123.zip',
         'GOLD_BLIND_SOURCE_PACKET_OWNER_CUSTODY')
    need(r.get('original_source_cues_available')==250
         and r.get('source_only_blind_packet_cues')==250
         and r.get('source_only_blind_packet_review_slots_currently_unreviewed')==250
         and r.get('frozen_legacy_candidate_atom_count')==68
         and r.get('source_only_blind_packet_original_candidate_atom_text_included') is False
         and r.get('source_only_blind_packet_prior_p201_p202_p203_labels_included') is False,
         'SOURCE_ONLY_PACKET_CANNOT_LEAK_PREDICTIONS_OR_REVIEW_LABELS')
    need(r.get('prior_p201_source_first_primary_label_counts')==
         {'FACT':92,'OPINION':61,'QUESTION':3,'NO_ATOM':27,'OPEN':67}
         and r.get('prior_p201_is_independent_atomic_gold') is False
         and r.get('previous_p203_private_meaning_review_is_independently_blind') is False,
         'OLD_SOURCE_FIRST_CUE_LABELS_CANNOT_BE_CALLED_INDEPENDENT_ATOMIC_GOLD')
    zero=['independently_adjudicated_gold_atomic_claims','independently_adjudicated_gold_source_cues',
          'trusted_independent_reviewer_public_keys_enrolled']
    need(all(r.get(k)==0 for k in zero)
         and all(r.get(k) is False for k in (
           'blinded_reviewer_one_authenticated','blinded_reviewer_two_authenticated',
           'distinct_reviewer_host_sessions_verified','blinded_two_review_consensus_locked',
           'gold_locked_before_alignment_proven','actual_owner_gold_precision_measured',
           'actual_owner_gold_recall_measured','actual_owner_gold_high_risk_FN_measured',
           'independent_blind_review_and_cue_fullness_certified'))
         and r.get('reviewer_gold_sha256_frozen') is None
         and r.get('prediction_to_gold_alignment_sha256_frozen') is None,
         'NO_UNATTESTED_REVIEWER_OR_IMPUTED_BLIND_CANDIDATE')
    need(r.get('precision') is None and r.get('recall') is None
         and r.get('high_risk_false_negative_count') is None
         and r.get('minimum_precision_basis_points')==9500
         and r.get('minimum_recall_basis_points')==9800
         and r.get('maximum_high_risk_false_negative_count')==0,
         'INDEPENDENT_MEASUREMENT_MUST_BE_UNMEASURABLE_NOT_ZERO_OR_ONE')
    need(r.get('synthetic_gold_evaluation_cases_added')==28
         and r.get('synthetic_gold_evaluation_cases_are_independent_financial_proof') is False
         and r.get('gold_evaluation_algorithm_path')=='ire/v6/gold_eval.py'
         and r.get('synthetic_gold_evaluation_tests_path')==
         'ire/v6/tests/test_p205_atomic_gold.py',
         'SYNTHETIC_UNIT_TESTS_NOT_INDEPENDENT_FINANCE_CERTIFICATION')
    need(r.get('real_etf_e2_accuracy_final_pass') is False
         and r.get('real_etf_e3_v123_approved_children')==0
         and r.get('real_etf_e4_owner_authorizations')==0
         and r.get('real_etf_e5_knowledge_publications')==0
         and r.get('personal_investment_advice_authorized') is False,
         'FALSE_E2_E3_E4_E5_OR_PERSONAL_FINANCE_RELEASE')
    need(r.get('protected_main_unchanged') is True
         and r.get('existing_two_branch_policy_preserved') is True
         and r.get('checklist_passed_item_count')==16
         and r.get('blocked_item_count_including_successors')==43
         and r.get('next_item')=='P0-2-06'
         and r.get('next_item_status')=='BLOCKED'
         and r.get('final_verdict')=='HOLD_DO_NOT_ADVANCE_CHECKLIST_OR_RELEASE_RESEARCH',
         'NO_SEQUENTIAL_ADVANCE_AFTER_HOLD')
    return errors


def main():
    failures=verify()
    for f in failures:
        print('P205_GOLD_READINESS_BLOCK',f,file=sys.stderr)
    if failures:
        return 1
    print('P205_BLIND_GOLD_READINESS_HOLD_GATE_PASS source=250 native_atoms=68 '
          'gold_independent=0 reviewer_attestation=0 independent_precision=NULL '
          'independent_recall=NULL high_risk_FN=UNMEASURABLE P206=BLOCKED')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
