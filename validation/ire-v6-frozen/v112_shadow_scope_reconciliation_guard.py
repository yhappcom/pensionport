"""V112: immutable V110/V111 source-cue linked overlay and 2026 pension-tax scope gate.

Source-bound status tracking is NOT a certification of semantic recall or a
personalized tax computation. Every 2026 tax branch remains non-personalized.
All owner transcripts and interpretations are held outside the public repository.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json, re

SOURCE_SHA = '00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V110_ZIP_SHA = 'f03b5147f01d2e976a26f080dae0e4ed53f447f0b4c6252ab812665a29aa135e'
V111_ZIP_SHA = 'da4ec9095a22d6eb800b2e35e199aaeeeb3a7c21687b92427cdd0fc0d88dbe47'
PENDING={'OPEN_AUDIO','OPEN_VISUAL','OPEN_ACCOUNT_VISUAL','OPEN_ACCOUNT_SCOPE'}
STATUS=PENDING|{'CONTEXT_RESOLVED','NOT_IN_V111_OPEN'}
REQUIRED_SOURCES={'TAX_EXCLUDED','DEFERRED_RETIREMENT','TAX_CREDITED_CONTRIBUTION','ACCOUNT_EARNINGS','PUBLIC_PENSION','OTHER_NON_PENSION_INCOME','UNKNOWN_SOURCE'}
TAX_RULES={
 'TAX_EXCLUDED':('EXCLUDED_IF_DOCUMENTED','require original contribution and tax-credit exclusion evidence'),
 'DEFERRED_RETIREMENT':('DEFERRED_RETIREMENT_SEPARATE_RULE','not automatically in 15m taxable private pension test'),
 'TAX_CREDITED_CONTRIBUTION':('PRIVATE_PENSION_THRESHOLD_CONDITIONAL','need pension receipt eligibility, annual total, potential election'),
 'ACCOUNT_EARNINGS':('PRIVATE_PENSION_THRESHOLD_CONDITIONAL','need pension receipt eligibility, annual total, potential election'),
 'PUBLIC_PENSION':('PUBLIC_PENSION_DIFFERENT_RULE','do not apply private pension 15m mechanically'),
 'OTHER_NON_PENSION_INCOME':('OTHER_INCOME_DIFFERENT_RULE','taxable account cashflow may have other categories'),
 'UNKNOWN_SOURCE':('UNKNOWN_ACCOUNT_SOURCE_HOLD','cannot compute taxes or apply 15m threshold'),
}
REQUIRED_FACT_FIELDS=(
 'account_type','fund_origin','tax_credit_history','contribution_and_earnings_balances',
 'deferred_retirement_income','pension_or_non_pension_withdrawal','receipt_age_and_years_and_limit',
 'withdrawal_amounts_by_source_per_year','pension_tax_election_and_other_income'
)
RULE_EVIDENCE_IDS={'NTS_2026_PENSION_SOURCE_TAX_TABLE','NTS_2026_1500_ELECTION','LAW_2026_ARTICLE_40_3_WITHDRAWAL_ORDER','LAW_2026_ARTICLE_40_2_PENSION_ELIGIBILITY'}
EXPECTED_EVIDENCE={
 'NTS_2026_PENSION_SOURCE_TAX_TABLE':('국세청','https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=2312'),
 'NTS_2026_1500_ELECTION':('국세청','https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=2312'),
 'LAW_2026_ARTICLE_40_3_WITHDRAWAL_ORDER':('국가법령정보센터','https://www.law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=126416'),
 'LAW_2026_ARTICLE_40_2_PENSION_ELIGIBILITY':('국가법령정보센터','https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1032953507'),
}

def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False)
def sha(x): return sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def digest(x):return sha(canonical(x))
def require(x,k):
 if not x:raise ValueError('V112_'+k)

def account_rule(source, *, receipt='UNKNOWN', original_proof=False):
 """A *routing* decision, never actual tax amount or personal applicability."""
 require(source in TAX_RULES,'SOURCE_KIND')
 require(receipt in {'PENSION','NON_PENSION','UNKNOWN'},'RECEIPT_KIND')
 category,why=TAX_RULES[source]
 if source in {'TAX_CREDITED_CONTRIBUTION','ACCOUNT_EARNINGS'} and receipt!='PENSION':
  category='NON_PENSION_OR_UNDETERMINED_TAX';why='15m pension threshold cannot apply before confirming legal pension receipt'
 if source=='TAX_EXCLUDED' and not original_proof:
  category='TAX_EXCLUSION_EVIDENCE_MISSING';why='tax excluded source must be documented, not inferred'
 return {'source_category':source,'receipt_mode':receipt,'branch':category,
         'status':'LEGAL_CLASSIFICATION_ONLY_NOT_PERSONAL_APPLICATION','reason':why,
         'tax_amount':None,'threshold_personally_applies':None,
         'eligible_for_finance_approval':False,'p0_go':False}

def validate_tax_review(review):
 require(type(review) is dict and review.get('schema')=='V112_PRIVATE_PENSION_ACCOUNT_TAX_SCOPE_NO_GOLD_V1','REVIEW_SCHEMA')
 require(review.get('linked_open_unit_id')=='V110_P10_U01','ACCOUNT_ID')
 require(review.get('status')=='OPEN_ACCOUNT_SCOPE','ACCOUNT_REMAINS_OPEN')
 require(review.get('original_v111_status')=='OPEN_ACCOUNT_SCOPE','V111_ACCOUNT_STATUS')
 for key in ('personal_tax_approved','financial_fact_auto_approved','p0_go','independent_gold'):
  require(review.get(key) is False,'FALSE_TAX_'+key)
 for key in ('tax_due','personal_threshold_applicable','pension_account_balances_known'):
  require(review.get(key) is None,'FAKE_PERSONAL_TAX_'+key)
 need=review.get('required_account_evidence');require(type(need) is list and set(need)==set(REQUIRED_FACT_FIELDS) and len(need)==len(REQUIRED_FACT_FIELDS),'MISSING_ACCOUNT_FACT_FIELDS')
 rules=review.get('branch_examples');require(type(rules) is list and len(rules)==len(REQUIRED_SOURCES),'SOURCE_BRANCH_CENSUS')
 seen=set()
 for entry in rules:
  src=entry.get('source_category');require(src in REQUIRED_SOURCES and src not in seen,'DUP_OR_BAD_TAX_BRANCH');seen.add(src)
  expected=account_rule(src,receipt=entry.get('receipt_mode'),original_proof=entry.get('original_proof') is True)
  require(entry.get('branch')==expected['branch'],'TAX_BRANCH_DRIFT')
  require(entry.get('tax_amount') is None and entry.get('threshold_personally_applies') is None,'TAX_FALSE_PERSONAL')
 require(seen==REQUIRED_SOURCES,'TAX_BRANCH_MISSING')
 require(type(review.get('verifiable_rule_evidence')) is list and set(review['verifiable_rule_evidence'])==RULE_EVIDENCE_IDS and len(review['verifiable_rule_evidence'])==4,'RULE_EVIDENCE_CENSUS')
 sources=review.get('official_sources');require(type(sources) is list and len(sources)==4,'OFFICIAL_SOURCE_CENSUS')
 seen_sources=set()
 for e in sources:
  eid=e.get('evidence_id');require(eid in EXPECTED_EVIDENCE and eid not in seen_sources,'OFFICIAL_ID')
  seen_sources.add(eid);require((e.get('issuer'),e.get('url'))==EXPECTED_EVIDENCE[eid],'OFFICIAL_URL_SPOOF')
  require(e.get('checked_2026_11_14') is True and e.get('html_bytes_pinned') is False,'OFFICIAL_UNPINNED_FLAG')
 require(review.get('speaker_claim_corrected_as_universal') is True and review.get('2026_nts_optional_15pct_separate_tax_noted') is True,'OMITTED_OPTIONAL_ELECTION')
 require(review.get('account_withdrawal_order_not_user_selectable_within_one_account') is True,'WITHDRAWAL_ORDER')
 require(type(review.get('reviewer_private_reasoning')) is str and len(review['reviewer_private_reasoning'])>=50,'REVIEW_REASON')
 require(type(review.get('remaining_private_limitation')) is str and len(review['remaining_private_limitation'])>=50,'REVIEW_LIMIT')
 return True

def audit_shadow(*,v110_zip_bytes,v111_zip_bytes,owner_archive_sha,unit_ledger,v110_docket,v111_dispositions,overlay,tax_review,source_cue_sha_by_video):
 require(type(v110_zip_bytes) is bytes and sha(v110_zip_bytes)==V110_ZIP_SHA,'V110_ZIP_DRIFT')
 require(type(v111_zip_bytes) is bytes and sha(v111_zip_bytes)==V111_ZIP_SHA,'V111_ZIP_DRIFT')
 require(owner_archive_sha==SOURCE_SHA,'OWNER_SHA')
 require(type(unit_ledger) is dict and len(unit_ledger.get('parents',[]))==52,'V110_52')
 require(type(unit_ledger.get('cross_parent_edges',[])) is list and len(unit_ledger.get('cross_parent_edges',[]))==25,'PARENT_EDGES')
 require(type(v110_docket) is list and len(v110_docket)==22,'V110_DOCKET')
 require(type(v111_dispositions) is dict and type(v111_dispositions.get('rows')) is list and len(v111_dispositions['rows'])==22,'V111_DISPOSITIONS')
 require(v111_dispositions.get('prior_private_zip_sha256')==V110_ZIP_SHA,'V111_SOURCE_PIN')
 require(type(overlay) is dict and overlay.get('schema')=='V112_85_UNIT_NONMUTATING_V111_DISPOSITION_SHADOW_V1','SHADOW_SCHEMA')
 require(overlay.get('v110_owner_zip_sha256')==V110_ZIP_SHA and overlay.get('v111_owner_zip_sha256')==V111_ZIP_SHA and overlay.get('original_owner_source_sha256')==SOURCE_SHA,'OVERLAY_ORIGIN')
 require(overlay.get('v110_ledger_frozen_sha256')==digest(unit_ledger),'V110_LEDGER_DRIFT')
 require(overlay.get('v111_dispositions_frozen_sha256')==digest(v111_dispositions),'V111_LEDGER_DRIFT')
 require(overlay.get('v110_open22_frozen_sha256')==digest(v110_docket),'V110_DOCKET_DRIFT')
 prior={r['unit_id']:r for r in v110_docket};require(len(prior)==22,'PRIOR_DUP')
 decisions={r['unit_id']:r for r in v111_dispositions['rows']};require(len(decisions)==22 and set(decisions)==set(prior),'DECISION_SCOPE_DRIFT')
 pmap={};unitmap={}
 for p in unit_ledger['parents']:
  pkey=(p.get('video_id'),p.get('draft_parent_id'))
  require(pkey not in pmap and type(pkey[0]) is str,'PARENT_ID_COLLISION')
  pmap[pkey]=p
  for u in p['units']:
   uid=u['unit_id'];require(uid not in unitmap,'UNIT_ID_COLLISION')
   unitmap[uid]=(p,u)
 require(len(unitmap)==85,'UNIT_85')
 gaps=unit_ledger.get('unassigned_cues');require(type(gaps) is list and len(gaps)==2,'UNASSIGNED_2')
 gapkeys=set()
 for g in gaps:
  key=(g.get('video_id'),g.get('cue_index'));require(key not in gapkeys and key[0] in source_cue_sha_by_video,'UNASSIGNED_DUP_OR_VIDEO')
  gapkeys.add(key);require(g.get('cue_sha256')==source_cue_sha_by_video[key[0]].get(key[1]),'UNASSIGNED_SOURCE_SHA')
  require(g.get('independent_gold') is False and g.get('claim_absence_certified') is False,'GAP_FALSE_APPROVAL')
 require(type(overlay.get('rows')) is list and len(overlay['rows'])==85,'OVERLAY_85')
 coverage=Counter();seen=set();v111_status=Counter();open_uids=[];source_covered=set()
 for r in overlay['rows']:
  uid=r.get('unit_id');require(uid in unitmap and uid not in seen,'UNIT_DUP_OR_EXTRA');seen.add(uid)
  p,u=unitmap[uid];vid=p['video_id'];indices=u['source_cue_indices']
  for key,v in (('video_id',vid),('window_id',p['window_id']),('draft_parent_id',p['draft_parent_id']),('unit_role',u['role']),('source_cue_indices',indices),('source_cues_digest_sha256',u['source_cues_digest_sha256'])):
   require(r.get(key)==v,'IDENTITY_DRIFT_'+key)
  actual=source_cue_sha_by_video.get(vid,{});require(type(actual) is dict,'ORIGINAL_VIDEO_MISSING')
  require(r['source_cues_digest_sha256']==sha(''.join(actual.get(i,'?') for i in indices)),'ORIGINAL_TEXT_HASH_DRIFT')
  source_covered.update((vid,i) for i in indices)
  original_status=decisions[uid]['status'] if uid in decisions else None
  status='CONTEXT_RESOLVED' if original_status=='CLOSED_CONTEXT' else original_status or 'NOT_IN_V111_OPEN'
  require(r.get('shadow_status')==status and status in STATUS,'STATUS_DRIFT')
  require(r.get('original_v111_disposition_sha256')==(digest(decisions[uid]) if uid in decisions else None),'DISPOSITION_HASH_DRIFT')
  require(r.get('finance_semantic_certified') is False and r.get('personal_advice_approved') is False and r.get('p0_go') is False,'FORBIDDEN_APPROVAL')
  require(r.get('independent_gold') is False,'FALSE_INDEPENDENT_GOLD')
  if uid in decisions:
   require(r.get('v111_context_reconciled') is True,'MISSING_V111_DISPOSITION')
   if status in PENDING:
    open_uids.append(uid);require(r.get('source_gap_remains_open') is True,'HIDDEN_OPEN')
   else: require(r.get('source_gap_remains_open') is False,'CLOSED_STILL_OPEN')
  else:
   require(r.get('v111_context_reconciled') is False and r.get('source_gap_remains_open') is None,'FAKE_NEW_COMPLETION')
  coverage[status]+=1
 require(set(unitmap)==seen,'UNIT_NOT_ALL_RECONCILED')
 require(len(source_covered)==158 and len(gapkeys)==2 and not (source_covered&gapkeys) and len(source_covered|gapkeys)==160,'CUE_COVERAGE_160')
 require(coverage==Counter({'NOT_IN_V111_OPEN':63,'CONTEXT_RESOLVED':10,'OPEN_AUDIO':7,'OPEN_VISUAL':3,'OPEN_ACCOUNT_VISUAL':1,'OPEN_ACCOUNT_SCOPE':1}),'CENSUS_DRIFT')
 require(set(open_uids)=={u for u in decisions if decisions[u]['status'] in PENDING},'OPEN_ID_LOSS')
 require(overlay.get('v110_underlying_ledger_modified') is False and overlay.get('v111_underlying_decisions_modified') is False,'ORIGINAL_OVERWRITTEN')
 require(overlay.get('formal_knowledge_approved_count')==0 and overlay.get('independent_gold') is False and overlay.get('p0_go') is False,'FALSE_OVERLAY_APPROVAL')
 require(overlay.get('certified_precision') is None and overlay.get('certified_recall') is None,'FALSE_OVERLAY_SCORE')
 validate_tax_review(tax_review)
 require(tax_review['linked_open_unit_id'] in open_uids,'TAX_SCOPE_CLOSED_BY_MISTAKE')
 return {'schema':'V112_85_UNIT_ACCOUNT_TAX_SCOPE_PUBLIC_SHA_ONLY_NO_GOLD_V1','source_archive_sha256':SOURCE_SHA,
 'v110_archive_sha256':V110_ZIP_SHA,'v111_archive_sha256':V111_ZIP_SHA,
 'source_cues_in_original_window':160,'source_cues_in_parent_units':len(source_covered),'parents':len(pmap),'units':len(unitmap),
 'previously_open_units':22,'context_resolved_units':10,'still_open_units':12,'no_v111_open_decision_units':63,
 'open_audio':7,'open_visual_or_account':4,'open_account_scope':1,'tax_scope_case_branches':len(tax_review['branch_examples']),
 'required_account_fields':len(tax_review['required_account_evidence']),
 'source_bound_unit_overlay_sha256':digest(overlay['rows']),
 'tax_scope_private_reasoning_sha256':sha(tax_review['reviewer_private_reasoning']),
 'tax_scope_private_remaining_limit_sha256':sha(tax_review['remaining_private_limitation']),
 'v110_v111_sources_untouched':True,'new_formally_approved_financial_claims':0,
 'current_tax_personal_application_resolved':False,'all_financial_semantic_claims_certified':False,
 'independent_gold':False,'certified_precision':None,'certified_recall':None,'p0_go':False,
 'personal_advice_approved':False,'master116_p4_merged':False}

def verify_public(public,computed):
 require(type(public) is dict and public==computed,'PUBLIC_SHA_DRIFT')
 require(public['independent_gold'] is False and public['p0_go'] is False and public['new_formally_approved_financial_claims']==0,'PUBLIC_FALSE_GO')
 return True