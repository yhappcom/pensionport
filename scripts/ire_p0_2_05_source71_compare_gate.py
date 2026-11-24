#!/usr/bin/env python3
"""P205 public SHA-only guard for SAME-CHAT source-first draft and topic crosswalk.

These are research TRIAGE artifacts. Public CI must never transform their 250-cue
coverage, 71 candidate topics, 68 frozen model atoms, or lexical links into
independently measured atomic gold precision/recall or authorized investment use.
"""
from __future__ import annotations
import json
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG, STATE, validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER, validate as status_validate
ROOT=Path(__file__).resolve().parents[1]
FIRST=Path('docs/IRE_P0_2_05_ETF250_SOURCE_FIRST_PROVISIONAL_71_PRE_CROSSWALK_SHA_ONLY_20261123.json')
COMPARE=Path('docs/IRE_P0_2_05_ETF250_SOURCE71_NATIVE68_CROSSWALK_SHA_ONLY_HOLD_20261123.json')
GOLD=Path('docs/IRE_P0_2_05_SOURCE_ONLY_BLIND_GOLD_READINESS_HOLD_SHA_20261123.json')
SOURCE='e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b'
NATIVE='c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb'
FROZEN_CANDIDATE='bbb9ce9ee3fabf5c49bdf9c3154a68955e360db4000cfb354070c307e215abfe'
FROZEN_ZIP='1cb97a80c658553447310acb4d36b071e1e05b945baee727203cfedc3c93b70f'
POST_COMPARE='9e67f6b3630821557f70351900e3dc9a4e80f55b3afc2e70a515d5d59aa12c2b'
POST_ZIP='e36f5e7e3098255394f97d4b001b4717f47874a3e0bc345bac76f03562d07fd0'

def load(root,path):return json.loads((Path(root)/path).read_text(encoding='utf8'))

def verify(root=ROOT, *,first=None,compare=None,ledger=None,state=None,gold=None,historical_only=False):
    root=Path(root)
    f=first if first is not None else load(root,FIRST)
    c=compare if compare is not None else load(root,COMPARE)
    s=state if state is not None else load(root,STATE)
    l=ledger if ledger is not None else load(root,LEDGER)
    g=gold if gold is not None else load(root,GOLD)
    errors=[]
    def need(ok,why):
        if not ok: errors.append('P205_SOURCE71_NATIVE68_'+why)
    if not historical_only:
        need(not checklist_validate(load(root,CATALOG),s,root=root), 'CHECKLIST_OR_HUMAN_MD_INVALID')
        need(not status_validate(l,root=root),'CANONICAL_E2_E3_E4_E5_HOLD_STATUS_INVALID')
        items=s.get('items',[])
        need(len(items)==60 and all(x.get('status')=='PASS' for x in items[:16])
             and items[16].get('id')=='P0-2-05' and items[16].get('status')=='HOLD'
             and all(x.get('status')=='BLOCKED' for x in items[17:]),
             'P205_HOLD_AND_43_FOLLOWING_BLOCKED')
        d=l.get('development_gate',{})
        need(d.get('this_item')=='P0-2-05' and d.get('pending_next_item')=='P0-2-05',
             'UNAUTHORIZED_P206_CURSOR')
    need(f.get('schema')=='IRE_P205_SOURCE_FIRST_PROVISIONAL_71_PRE_CROSSWALK_SHA_ONLY_V1'
         and f.get('item_id')=='P0-2-05' and f.get('video_id')=='LVE7XN_esTc'
         and f.get('date')=='2026-11-23','FROZEN_SOURCE_REVIEW_SCOPE')
    need(f.get('frozen_provisional_zip_sha256')==FROZEN_ZIP
         and f.get('frozen_provisional_json_sha256')==FROZEN_CANDIDATE
         and f.get('frozen_private_library_file_id')=='libfile_2ad6efe4f654819185cdf788d14f3a8f'
         and f.get('original_source_srt_sha256')==SOURCE,'FIRST_SOURCE_PACKAGE_HASH_OR_OWNER_CUSTODY')
    need(f.get('source_only_cues_checked')==250 and f.get('provisional_atomic_candidate_count')==71
         and f.get('high_risk_provisional_candidate_count')==36
         and f.get('source_context_linked_cue_count')==240
         and f.get('source_nonsubstantive_cue_count')==10
         and f.get('source_coverage_missing_indices')==[], 'SOURCE250_FIRSTPASS_DRAFT_COUNTERS')
    need(f.get('used_original_v228_prediction_content_to_draft_this_round') is False
         and f.get('prior_same_chat_context_accessible') is True
         and f.get('genuine_blindness_independently_attested') is False
         and f.get('source_first_candidate_is_financial_truth') is False
         and f.get('provisional_candidate_is_independent_gold') is False
         and f.get('source_atomic_exhaustiveness_proven') is False
         and f.get('distinct_independent_reviewer_sessions_attested')==0,
         'SOURCE_ONLY_CANNOT_SELF_AUTHORIZE_AS_GOLD')
    need(f.get('gold_independent_atom_count')==0
         and f.get('independent_precision') is None
         and f.get('independent_recall') is None
         and f.get('high_risk_FN') is None
         and f.get('pre_crosswalk_freeze') is True
         and f.get('no_prediction_alignment_computed_yet') is True,
         'PROVISIONAL_GOLD_OR_PRE_CROSSWALK_LAUNDERING')
    need(c.get('schema')=='IRE_P205_SOURCE71_NATIVE68_CROSSWALK_SHA_ONLY_HOLD_V1'
         and c.get('item_id')=='P0-2-05' and c.get('original_video_id')=='LVE7XN_esTc'
         and c.get('original_srt_sha256')==SOURCE
         and c.get('frozen_prediction_sha256')==NATIVE,
         'POST_COMPARE_SCOPE')
    need(c.get('pre_comparison_frozen_source_first_sha256')==FROZEN_CANDIDATE
         and c.get('source_first_zip_sha256')==FROZEN_ZIP
         and c.get('post_comparison_crosswalk_json_sha256')==POST_COMPARE
         and c.get('post_comparison_crosswalk_zip_sha256')==POST_ZIP
         and c.get('crosswalk_library_file_id')=='libfile_3c5554759c4c8191bc47f0db8923e8d9',
         'DIAGNOSTIC_AFTER_FREEZE_AND_OWNER_CUSTODY')
    need(c.get('original_source_cues')==250 and c.get('source_first_provisional_candidates')==71
         and c.get('high_risk_source_first_candidates')==36
         and c.get('original_native_prediction_count')==68
         and c.get('source_first_quote_and_cue_sha_mismatch_count')==0
         and c.get('source_first_cues_linked_to_context_or_primary')==240
         and c.get('source_first_discourse_nonclaim_cues')==10
         and c.get('source_first_uncovered_cues')==0,
         'POST_COMPARE_SOURCE_COUNTS_AND_QUOTE_PROOFS')
    need(c.get('source_candidates_without_separate_native_topic_link')==2
         and c.get('source_only_standalone_candidate_ids')==['P205-SRC-003','P205-SRC-014']
         and c.get('source_candidates_related_to_multiple_native_atoms')==8
         and c.get('native_atoms_related_to_multiple_source_candidates')==10
         and c.get('kind_label_disagreement_related_pairs')==11
         and c.get('high_risk_manual_review_category_count')==10,
         'SPLIT_MERGE_KIND_DISAGREEMENTS_CANNOT_BE_SILENCED')
    need(c.get('source_first_cues_certified_atom_exhaustive') is False
         and c.get('missing_independently_verified_gold') is True
         and c.get('independent_gold_certified_atom_count')==0
         and c.get('independent_blind_reviewer_session_count')==0
         and c.get('lexical_or_topic_relation_as_TP') is False
         and c.get('unmatched_topic_relation_as_FN') is False
         and c.get('manually_reviewed_same_chat_is_independent') is False,
         'TOPIC_RELATION_IS_NOT_TP_FP_FN')
    need(c.get('independent_precision') is None and c.get('independent_recall') is None
         and c.get('high_risk_FN') is None
         and c.get('no_e2_final_approval') is True
         and c.get('no_e3_e4_e5_publication') is True
         and c.get('same_phase_required')=='P0-2-05'
         and c.get('next_phase_blocked')=='P0-2-06'
         and c.get('item_status')=='HOLD',
         'NO_ACCURACY_OR_FINANCIAL_APPROVAL_ON_SAME_CHAT_REVIEW')
    need(g.get('status')=='HOLD_INDEPENDENT_BLIND_ATOMIC_GOLD_NOT_AVAILABLE'
         and g.get('independently_adjudicated_gold_atomic_claims')==0
         and g.get('precision') is None and g.get('recall') is None
         and g.get('high_risk_false_negative_count') is None,
         'PRIOR_HOLD_NOT_OVERRIDDEN')
    return errors

if __name__=='__main__':
    problems=verify()
    for x in problems:print('P205_SOURCE71_NATIVE68_BLOCK',x)
    if problems:raise SystemExit(1)
    print('P205_SOURCE71_NATIVE68_SHA_HOLD_GATE_PASS original_cues=250 provisional=71 '
          'native=68 kind_disagreement_pairs=11 high_risk_provisional=36 '
          'independent_gold=0 precision=NULL recall=NULL P206=BLOCKED')
