#!/usr/bin/env python3
"""P205 current owner ETF250 evidence readiness: deny fabricated GO, preserve RED-GREEN proof."""
from __future__ import annotations
import ast,json,sys
from pathlib import Path

from scripts.ire_p0_2_05_gold_readiness_gate import verify as old_hold_verify
from scripts.ire_checklist_gate import STATE
from scripts.ire_current_status_gate import LEDGER
ROOT=Path(__file__).resolve().parents[1]
RECEIPT=Path('docs/IRE_P0_2_05_ROOT_CAUSE_REASSESSMENT_AND_GOLD_EVIDENCE_HOLD_20261123.json')
SRT_SHA='e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b'
NATIVE_SHA='c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb'
PACKET_SHA='e9b8966995c0b91b05516458d95d4df1fc5bd27bd44fd7ead7298b80c9c1d8cb'

def load(root,p):return json.loads((Path(root)/p).read_text(encoding='utf8'))

def _production_pin(root):
    """Read the committed trust-root literal without importing crypto in governance CI."""
    path=Path(root)/'ire/v6/gold_release.py'
    tree=ast.parse(path.read_text(encoding='utf8'),filename=str(path))
    pins=[node.value for node in tree.body if isinstance(node,(ast.Assign,ast.AnnAssign))
          and any(isinstance(t,ast.Name) and t.id=='PINNED_P205_HOST_REVIEW_REGISTRY_SHA256'
                  for t in (node.targets if isinstance(node,ast.Assign) else [node.target]))]
    if len(pins)!=1 or not isinstance(pins[0],ast.Constant):
        return 'MISSING_OR_DYNAMIC_PIN'
    return pins[0].value


def verify(root=ROOT,*,receipt=None,state=None,ledger=None):
    root=Path(root)
    r=load(root,RECEIPT) if receipt is None else receipt
    s=load(root,STATE) if state is None else state
    l=load(root,LEDGER) if ledger is None else ledger
    errors=[]
    def need(flag,label):
        if not flag:errors.append('P205_ROOT_CAUSE_'+label)
    need(not old_hold_verify(root,state=s,ledger=l), 'PRIOR_FROZEN_NO_GOLD_GATE_MUST_PASS')
    need(r.get('schema')=='IRE_P205_REDIAGNOSED_GOLD_EVALUATION_BLOCKERS_AND_REMEDIATION_SHA_ONLY_V1'
         and r.get('item_id')=='P0-2-05' and r.get('date')=='2026-11-23', 'RECEIPT_SCHEMA')
    need(r.get('protected_original_source_srt_sha256')==SRT_SHA
         and r.get('protected_original_frozen_native_sha256')==NATIVE_SHA
         and r.get('protected_source_only_intake_zip_sha256')==PACKET_SHA,
         'SOURCE_PREDICTION_AND_BLIND_PACKET_HASHES')
    need(r.get('original_source_cues')==250 and r.get('original_prediction_atoms')==68
         and r.get('source_only_intake_cues')==250 and
         r.get('source_only_intake_original_source_bytes_identical') is True and
         r.get('source_only_intake_prediction_text_absent') is True,
         'UNALTERED_SOURCE_ONLY_CENSUS')
    need(r.get('eligible_independently_adjudicated_gold_atoms')==0
         and r.get('actual_authenticated_blind_review_records')==0
         and r.get('actual_host_pinned_public_key_sets')==0
         and r.get('current_source_only_gold_cue_slots_filled')==0
         and r.get('current_gold_atoms_frozen')==0,
         'CURRENT_REAL_GOLD_AND_SIGNED_REVIEW_FILES_ABSENT')
    need(all(r.get(k) is None for k in ('current_atomic_precision',
          'current_atomic_recall','current_high_risk_false_negative_count')),
         'NO_FABRICATED_REAL_ACCURACY_MEASUREMENTS')
    need(r.get('required_atomic_precision_basis_points')==9500
         and r.get('required_atomic_recall_basis_points')==9800
         and r.get('required_high_risk_false_negative_max')==0,
         'FROZEN_95_98_ZERO_FN_THRESHOLDS')
    defects=r.get('original_gold_eval_defects')
    need(type(defects) is list and len(defects)==5 and
         {x.get('id') for x in defects if type(x) is dict}=={'B01','B02','B03','B04','B05'},
         'ROOT_CAUSE_FIVE_ACTUAL_BLOCKERS')
    need(r.get('red_proof_commit')=='e0351444a92c7f0ba25daa6a93173df37514190d'
         and r.get('red_proof_ci_run_id')==45138413937
         and r.get('red_proof_v6_failures')==7
         and r.get('source_gold_trace_fix_commit')=='c545bc51b058c4770408439d516cb8bc9dacd7d4'
         and r.get('source_gold_trace_fix_ci_run_id')==45138653757
         and r.get('source_gold_trace_extra_unit_tests')==8,
         'ACTUAL_RED_TO_GREEN_COMMIT_RUN_EVIDENCE')
    need(r.get('positive_production_review_contract_initial_commit')=='d5bc87b1653bfc119c609644a559393ad578e430'
         and r.get('positive_production_review_contract_synthetic_tests')==23
         and r.get('production_registry_pinned_in_code_now') is False
         and r.get('production_root_hash_from_caller_accepted') is False
         and r.get('all_synthetic_tests_are_real_financial_accuracy_measurements') is False,
         'EXPLICIT_NO_SELF_SIGNED_PRODUCTION_RELEASE')
    need(_production_pin(root) is None,
         'PRODUCTION_HOST_TRUST_ROOT_MUST_REMAIN_UNENROLLED')
    need(all((root/p).is_file() for p in (
         'ire/v6/gold_traceability.py','ire/v6/gold_release.py',
         'ire/v6/tests/test_p205_gold_release.py','ire/v6/tests/test_p205_atomic_gold.py')),
         'RELEASE_CODE_AND_SYNTHETIC_ADVERSARIAL_TESTS_PRESENT')
    need(r.get('high_risk_topic_queues_open')==10
         and all(r.get(k)==0 for k in ('e3_approvals','e4_owner_approvals','e5_publications')),
         'NO_HIGH_RISK_OR_E3_E4_E5_FAKE_RELEASE')
    need(r.get('checklist_pass_count')==16 and r.get('p205_status')=='HOLD'
         and r.get('p206_status')=='BLOCKED'
         and r.get('successor_blocked_count')==43 and
         r.get('actual_status')=='HOLD_GOLD_ABSENT_AND_HOST_PROVENANCE_NOT_ENROLLED',
         'NO_SEQUENTIAL_ADVANCE')
    need(r.get('protected_main_unchanged') is True and
         r.get('existing_two_branch_policy_preserved') is True,
         'BRANCH_POLICY')
    need(l.get('development_gate',{}).get('this_item')=='P0-2-05'
         and s['items'][16].get('status')=='HOLD'
         and all(it.get('status')=='BLOCKED' for it in s['items'][17:]),
         'LIVE_CHECKLIST_CURSOR')
    return errors

def main():
    errs=verify()
    for err in errs:print('P205_ROOT_CAUSE_GATE_BLOCK',err,file=sys.stderr)
    if errs:return 1
    print('P205_ROOT_CAUSE_HOLD_GATE_PASS source=250 native=68 independent_gold=0 '
          'original_gold_trace_RED7_to_GREEN0 positive_contract=TESTED '
          'external_host_trust_root=NOT_ENROLLED independent_metrics=NULL P206=BLOCKED')
    return 0

if __name__=='__main__':raise SystemExit(main())
