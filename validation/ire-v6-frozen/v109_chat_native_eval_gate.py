"""V109 chat-native source-first semantic QA: no external reviewers, NO independent gold.

The user requests all work in ChatGPT; the former V105 four-window external blind
cohort is now explicitly reused for a same-chat pilot, and cannot be reused as
unseen independent holdout later. This module verifies source custody and audit
trail ONLY; the model cannot self-certify factual recall/precision.
Private source and model explanations MUST NOT be committed publicly.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
import json, re

SOURCE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
PACKET_SHA='ea9020d688917ce11272b45033b8160b68f9680eae9974770eb7ad6549efea81'
VALID_STANCES={'FACT_CANDIDATE','OPINION','QUESTION','HYPOTHESIS','CONDITION','EXCEPTION','REBUTTAL','UNCERTAIN','NON_FACT_DIALOGUE'}
VALID_RISKS={'HIGH','MEDIUM','LOW','NONE'}
VALID_ACTIONS={'OPEN_SOURCE_CONTEXT','RESTRICT_UNIVERSALIZATION','OPEN_MISSING_DIAGRAM','RESTRICT_LAW_SCOPE',
 'CURRENT_OFFICIAL_SOURCE_CONTRADICTS_BROAD_WORDING','CONDITIONAL_EXAMPLE_ONLY',
 'PRODUCT_RISK_QUALIFIER_REQUIRED','HYPOTHESIS_AND_ARITHMETIC_SPLIT',
 'FLAG_MULTIPERIOD_NUMERIC_CONFLICT','HYPOTHESIS_ONLY','CONFIRM_NARROW_HISTORICAL_FACT',
 'UNVERIFIED_PERSONAL_ACCOUNT','OPEN_ACCOUNT_TYPES_AND_ASR','EDUCATION_NOT_PERSONAL_ADVICE',
 'OPINION_CONTEXT_ONLY','UNVERIFIED_GENERALIZATION','NON_FACT_EDUCATIONAL_LIMIT',
 'OPINION_NOT_TRADE_ADVICE'}
FIN=re.compile(r'(ISA|IRP|ETF|TDF|CMA|연금|수익|금리|이자|채권|주식|배당|계좌|보험|퇴직|원금|투자|손실|펀드|납입|추납|매도|매수|공제|세금|세액|세율|상환|수령|이체|절세|비과세)',re.I)
NUM=re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')
COND=re.compile(r'(만약|경우|조건|해야|하면|이라면|때|한도|이내|미만|이상|넘|초과|전까지|이후|부터|까지|적용)')
NEG=re.compile(r'(하지만|그런데|다만|아니|안 되|못|제외|별도|차이|반대|예외|따라서|수정|정확히)')
UNCERT=re.compile(r'(같아요|것 같|아마|일 수도|모르|아니겠|이겠|할까요|일까요|인가요|생각|가정|예를 들)')

def require(condition, code):
 if not condition:raise ValueError('V109_'+code)
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(value):return sha256(value if isinstance(value,bytes) else value.encode('utf-8')).hexdigest()
def digest(obj):return sha(canonical(obj))

def frozen_lexical_kinds(t):
 regs=(('LEXICAL_FINANCE',FIN),('LEXICAL_NUMBER',NUM),('LEXICAL_SCOPE',COND),
       ('LEXICAL_NEGATION',NEG),('LEXICAL_UNCERTAIN',UNCERT))
 return [name for name,pattern in regs if pattern.search(t)]

def audit_chat_native(*,lock,packet,forecast,prelock,pass_a,pass_a_bytes,pass_b,atomization,
                      expected_parent_rows,actual_owner_zip_sha,expected_packet_sha=PACKET_SHA,
                      expected_source_zip_sha=SOURCE_SHA):
 """Actual transcript-derived records provided privately; result is strictly SHA/count only."""
 require(type(lock)==dict and type(packet)==dict and type(forecast)==dict and type(prelock)==dict,'INPUT_TYPE')
 require(actual_owner_zip_sha==expected_source_zip_sha==lock.get('source_zip_sha256')==packet.get('source_archive_sha256'),'ARCHIVE_SHA')
 require(packet.get('packet_sha256')==expected_packet_sha==prelock.get('source_packet_sha256'),'PACKET_PIN')
 require(lock.get('schema')=='V105_UNSEEN_OWNER_SOURCE_PRE_REVIEW_LOCK_V1' and lock.get('cue_count')==160,'V105_LOCK')
 require(packet.get('prediction_disclosed') is False and packet.get('independent_gold') is False,'SOURCE_NOT_GOLD')
 require(prelock.get('schema')=='V109_PRE_INTERPRETATION_CHAT_NATIVE_LOCK_V1' and prelock.get('source_archive_sha256')==expected_source_zip_sha,'PRELOCK')
 windows=lock['selected'];require(type(windows)==list and len(windows)==4,'WINDOWS_4')
 scopes={(w['video_id'],w['window_id']):w for w in windows};require(len(scopes)==4,'DUP_WINDOWS')
 cues=packet.get('owner_private_cues');require(type(cues)==list and len(cues)==160,'CUES_160')
 bycue={};groups=defaultdict(list)
 for cue in cues:
  k=(cue.get('video_id'),cue.get('window_id'));i=cue.get('cue_index')
  require(k in scopes and type(i) is int and (k[0],i) not in bycue,'CUE_SCOPE_OR_DUP')
  require(type(cue.get('text_private')) is str and bool(cue['text_private']) and cue.get('cue_sha256')==sha(cue['text_private']),'CUE_SOURCE_SHA')
  require(type(cue.get('start_ms')) is int and type(cue.get('end_ms')) is int and cue['start_ms']<=cue['end_ms'],'CUE_TIME')
  bycue[(k[0],i)]=cue;groups[k].append(cue)
 for key,sc in scopes.items():
  rows=groups[key];first,last=sc['first_cue'],sc['last_cue']
  require(len(rows)==40 and [r['cue_index'] for r in rows]==list(range(first,last+1)),'WINDOW_40_CONTIGUOUS')
  require(sha(' '.join(r['text_private'] for r in rows))==sc['source_window_sha256'],'WINDOW_SHA')
 require(digest([[r['video_id'],r['cue_index'],r['cue_sha256']] for r in cues])==expected_packet_sha,'SOURCE_PACKET_DIGEST')
 require(type(forecast.get('forecast')) is list and len(forecast['forecast'])==160,'FORECAST_160')
 require(forecast.get('independent_gold') is False and forecast.get('p0_go') is False,'FORECAST_FAKE_GOLD')
 require(forecast.get('source_archive_sha256')==expected_source_zip_sha,'FORECAST_SOURCE')
 fseen=set();flag_positions=set()
 for r in forecast['forecast']:
  key=(r.get('video_id'),r.get('cue_index'));cue=bycue.get(key)
  require(cue is not None and key not in fseen,'FORECAST_SCOPE_DUP');fseen.add(key)
  kinds=frozen_lexical_kinds(cue['text_private'])
  require(r.get('window_id')==cue['window_id'] and r.get('cue_sha256')==cue['cue_sha256'],'FORECAST_CUE')
  require(r.get('lexical_kinds')==kinds and r.get('lexical_any') is bool(kinds),'FORECAST_MANIPULATION')
  require(r.get('not_financial_accuracy_certified') is True,'FORECAST_FALSE_CERT')
  if kinds:flag_positions.add(key)
 require(fseen==set(bycue),'FORECAST_NOT_FULL_CUES')
 fsha=digest(forecast['forecast'])
 require(forecast.get('forecast_digest_sha256')==prelock.get('lexical_forecast_sha256')==fsha,'FROZEN_FORECAST_SHA')
 require(prelock.get('source_cues')==160 and prelock.get('lexical_any_cues')==len(flag_positions) and prelock.get('lexical_none_cues')==160-len(flag_positions),'PRELOCK_COUNTS')
 require(prelock.get('independent_gold') is False and prelock.get('certified_precision') is None and prelock.get('p0_go') is False,'PRELOCK_FAKE_SCORE')
 require(type(pass_a)==dict and type(pass_a_bytes)==bytes,'PASS_A_INPUTS')
 require(pass_a.get('schema')=='V109_CHAT_FIRST_READING_52_V33_PARENTS_NOT_GOLD_V1','PASS_A_SCHEMA')
 require(pass_a.get('source_archive_sha256')==expected_source_zip_sha,'PASS_A_SOURCE')
 require(pass_a.get('independent_gold') is False and pass_a.get('precision') is None and pass_a.get('recall') is None and pass_a.get('p0_go') is False,'PASS_A_FALSE_SCORE')
 parents=pass_a.get('parents');require(type(parents)==list and len(parents)==52,'PASS_A_52')
 require(type(expected_parent_rows)==list and len(expected_parent_rows)==52,'EXPECTED_V33_52')
 expect={(r['video_id'],r['draft_parent_id']):r for r in expected_parent_rows};require(len(expect)==52,'EXPECTED_DUP')
 parentseen=set();assigned=set();stances=Counter()
 for p in parents:
  key=(p.get('video_id'),p.get('draft_parent_id'))
  require(key in expect and key not in parentseen,'PARENT_DUP_OR_EXTRA');parentseen.add(key)
  src=expect[key];v=key[0];wid=p.get('window_id');indices=p.get('source_cue_indices')
  require(wid==src['window_id'] and indices==src['source_cue_indices'] and p.get('source_parent_sha256')==src['source_parent_sha256'],'PARENT_V33_LINK')
  require(type(indices)==list and bool(indices) and len(indices)==len(set(indices)),'PARENT_SPAN')
  actual=' | '.join(bycue[(v,i)]['text_private'] for i in indices)
  require(sha(actual)==src['source_parent_sha256'],'PARENT_ORIGINAL_BYTES')
  for idx in indices:
   q=(v,idx);require(q not in assigned,'PARENT_OVERLAP');assigned.add(q)
  require(p.get('stance') in VALID_STANCES and len(p.get('speaker_meaning_private',''))>=8 and len(p.get('scope_and_risk_private',''))>=8,'PARENT_MEANING_SCOPE')
  require(p.get('official_fact_approved') is False and p.get('independent_gold') is False and p.get('personal_advice_approved') is False,'PARENT_FAKE_APPROVAL')
  require(p.get('chat_pass')=='A_FIRST_READING_NOT_GOLD','PARENT_NOT_CHAT_FIRST')
  stances[p['stance']]+=1
 require(parentseen==set(expect),'PARENT_NOT_ALL_REVIEWED')
 gaps=pass_a.get('unassigned_cues');require(type(gaps)==list,'GAPS_LIST')
 gapset=set()
 for x in gaps:
  k=(x.get('video_id'),x.get('cue_index'))
  require(k in bycue and k not in assigned and k not in gapset,'GAP_SCOPE_DUP');gapset.add(k)
  require(x.get('window_id')==bycue[k]['window_id'] and x.get('cue_sha256')==bycue[k]['cue_sha256'],'GAP_SHA')
  require(type(x.get('role_private')) is str and len(x['role_private'])>=10 and x.get('claim_absence_certified') is False and x.get('independent_gold') is False,'GAP_NO_FALSE_ABSENCE')
 require(assigned|gapset==set(bycue) and not (assigned&gapset),'GAP_CONSERVATION')
 require(type(pass_b)==dict and pass_b.get('schema')=='V109_CHAT_COUNTEREXAMPLE_REVIEW_NOT_GOLD_V1','PASS_B_SCHEMA')
 require(pass_b.get('source_archive_sha256')==expected_source_zip_sha and pass_b.get('pass_a_sha256')==sha(pass_a_bytes),'PASS_B_PARENT_PIN')
 require(pass_b.get('frozen_forecast_digest_sha256')==fsha,'PASS_B_FORECAST_PIN')
 for name in ('independent_gold','p0_go'):
  require(pass_b.get(name) is False,'PASS_B_FAKE_'+name)
 for name in ('certified_precision','certified_recall','certified_high_risk_recall'):
  require(pass_b.get(name) is None,'PASS_B_FAKE_'+name)
 require(pass_b.get('independent_human_reviews')==0 and pass_b.get('formal_finance_knowledge_approvals')==0,'PASS_B_FALSE_WORK')
 issues=pass_b.get('issues');require(type(issues)==list and len(issues)==19,'ISSUES_19')
 evidence=pass_b.get('official_evidence');require(type(evidence)==dict and len(evidence)==4,'OFFICIAL_SOURCE_SCOPE')
 for e in evidence.values():
  require(e.get('issuer') in {'국세청','한국거래소','SK hynix'} and (e.get('url','').startswith('https://www.nts.go.kr/') or e.get('url','').startswith('https://www.krx.co.kr/') or e.get('url','').startswith('https://www.skhynix.com/')),'OFFICIAL_ISSUER_URI')
  require(e.get('current_law_full_scope_certified') is False,'SOURCE_NOT_LEGAL_APPROVAL')
 seen=set();noalert=0;affected=set();provisional_high=0
 for i in issues:
  iid=i.get('issue_id');v=i.get('video_id');w=i.get('window_id');a=i.get('first_cue');b=i.get('last_cue')
  require(type(iid) is str and iid and iid not in seen,'ISSUE_DUP');seen.add(iid)
  require((v,w) in scopes and type(a) is int and type(b) is int and a<=b and a>=scopes[(v,w)]['first_cue'] and b<=scopes[(v,w)]['last_cue'],'ISSUE_WINDOW')
  require(i.get('source_span_sha256')==sha(''.join(bycue[(v,j)]['cue_sha256'] for j in range(a,b+1))),'ISSUE_SOURCE_SPAN')
  parentids=i.get('linked_v33_parent_ids');require(type(parentids)==list and bool(parentids) and len(set(parentids))==len(parentids),'ISSUE_PARENTS')
  for cid in parentids:
   key=(v,cid);require(key in expect and bool(set(expect[key]['source_cue_indices'])&set(range(a,b+1))),'ISSUE_WRONG_PARENT');affected.add(key)
  require(i.get('risk_level_provisional') in VALID_RISKS and i.get('action_provisional') in VALID_ACTIONS and len(i.get('reviewer_counterexample_private',''))>=28,'ISSUE_MEANING')
  official=i.get('official_evidence_id');require(official is None or official in evidence,'ISSUE_UNKNOWN_OFFICIAL')
  actual=any((v,j) in flag_positions for j in range(a,b+1))
  require(i.get('lexical_prelock_direct_cue_inside_span') is actual,'ISSUE_FLAG_MISMATCH')
  noalert+=not actual;provisional_high+=i['risk_level_provisional']=='HIGH'
  for f in ('same_chat_independent_gold','certified_actual_error','fact_approved','p0_go'):
   require(i.get(f) is False,'ISSUE_FALSE_'+f)
 require(pass_b.get('stats')=={'issue_spans':19,'issue_spans_lexical_any':19-noalert,
    'issue_spans_no_lexical_alert':noalert,'linked_affected_parents':len(affected),
    'high_risk_provisional_spans':provisional_high},'ISSUES_CENSUS')
 require(type(atomization)==dict and atomization.get('schema')=='V109_INTERNAL_CROSS_CUE_ATOMS_NOT_GOLD_V1','ATOMS_SCHEMA')
 require(atomization.get('source_archive_sha256')==expected_source_zip_sha and atomization.get('independent_gold') is False and atomization.get('p0_go') is False,'ATOM_FALSE_GOLD')
 require(atomization.get('all_52_draft_parents_completely_atomized') is False and atomization.get('certified_precision') is None and atomization.get('certified_recall') is None,'ATOM_FALSE_COMPLETION')
 atoms=atomization.get('source_atoms_provisional');require(type(atoms)==list and len(atoms)>=1,'ATOMS_LIST')
 atomseen=set()
 for a in atoms:
  aid=a.get('atom_id');v=a.get('video_id');w=a.get('window_id');ix=a.get('source_cue_indices')
  require(type(aid) is str and aid not in atomseen,'ATOM_DUP');atomseen.add(aid)
  require((v,w) in scopes and type(ix) is list and bool(ix) and len(ix)==len(set(ix)),'ATOM_SOURCE')
  require(all((v,j) in bycue and bycue[(v,j)]['window_id']==w for j in ix),'ATOM_CROSS_WINDOW')
  require(a.get('source_cues_digest_sha256')==sha(''.join(bycue[(v,j)]['cue_sha256'] for j in ix)),'ATOM_SHA')
  require(a.get('stance_provisional') in VALID_STANCES and len(a.get('speaker_atomic_meaning_private',''))>=10 and len(a.get('preserved_conditions_private',''))>=10,'ATOM_MEANING')
  require(a.get('official_evidence_id') is None or a['official_evidence_id'] in evidence,'ATOM_EVIDENCE')
  for f in ('source_semantic_truth_certified','independent_gold','personal_advice_approved','p0_go'):
   require(a.get(f) is False,'ATOM_FALSE_'+f)
 return {'schema':'V109_SOURCE_PINNED_CHAT_INTERNAL_QA_NO_GOLD_V1',
   'owner_source_sha256':expected_source_zip_sha,'source_cues_read':len(bycue),
   'source_windows_read':len(scopes),'v33_draft_parent_meaning_annotations':len(parents),
   'unassigned_cues_flagged_open':len(gapset),'first_pass_parent_stances':dict(sorted(stances.items())),
   'frozen_lexical_any_cues':len(flag_positions),'frozen_lexical_none_cues':len(bycue)-len(flag_positions),
   'internal_counterexample_spans':len(issues),'internal_counterexample_spans_with_lexical_signal':len(issues)-noalert,
   'internal_counterexample_spans_without_lexical_signal':noalert,
   'internal_counterexample_affected_parents':len(affected),'internal_provisional_high_risk_spans':provisional_high,
   'provisional_cross_cue_atomic_parts':len(atoms),'human_independent_reviewer_count':0,
   'v105_external_unseen_cohort_repurposed_in_chat':True,'can_reuse_v105_as_future_unseen_independent_gold':False,
   'chat_internal_audit_complete_not_knowledge_approved':True,
   'current_finance_law_automatically_certified':False,'all_draft_parents_atomized':False,
   'certified_precision':None,'certified_recall':None,'certified_high_risk_recall':None,
   'certified_workflow_speedup':None,'new_formally_approved_financial_claims':0,
   'independent_gold':False,'p0_go':False,'personal_advice_approved':False,
   'frozen_forecast_digest_sha256':fsha,
   'private_parent_meaning_digest_sha256':digest([[p['video_id'],p['draft_parent_id'],sha(p['speaker_meaning_private']),sha(p['scope_and_risk_private'])] for p in parents]),
   'private_counterexample_digest_sha256':digest([[i['issue_id'],i['source_span_sha256'],sha(i['reviewer_counterexample_private'])] for i in issues]),
   'private_atomic_parts_digest_sha256':digest([[a['atom_id'],a['source_cues_digest_sha256'],sha(a['speaker_atomic_meaning_private'])] for a in atoms])}

def check_public_receipt(receipt,computed):
 require(type(receipt)==dict and type(computed)==dict,'PUBLIC_TYPES')
 for k,v in computed.items():require(receipt.get(k)==v,'RECEIPT_DRIFT_'+k)
 for k in ('certified_precision','certified_recall','certified_high_risk_recall','certified_workflow_speedup'):
  require(receipt.get(k) is None,'RECEIPT_FAKE_SCORE_'+k)
 for k in ('independent_gold','p0_go','personal_advice_approved','can_reuse_v105_as_future_unseen_independent_gold'):
  require(receipt.get(k) is False,'RECEIPT_FAKE_GO_'+k)
 require(not any('private' in k.lower() and k not in {'private_parent_meaning_digest_sha256','private_counterexample_digest_sha256','private_atomic_parts_digest_sha256'} for k in receipt),'RECEIPT_PRIVATE_PROSE')
 return True