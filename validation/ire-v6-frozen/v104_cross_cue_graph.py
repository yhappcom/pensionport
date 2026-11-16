"""V104 source-bound cross-cue financial arithmetic candidate graph.

This is a REVIEW QUEUE, not financial fact validation. Never infers
statute, account ownership, verified speaker, tax eligibility or gold labels.
No owner transcript strings appear in this public module.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import hashlib, json, re

AMOUNT = re.compile(r'(?<![0-9A-Za-z])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d{4,}(?:\.\d+)?)\s*(억\s*원|만\s*원|천\s*원|원)')
RATE = re.compile(r'(?<![0-9A-Za-z])(\d+(?:\.\d+)?)\s*%')
PERIOD = re.compile(r'(?<![0-9A-Za-z])(\d+(?:\.\d+)?)\s*(년|개월|일)')
HISTORIC = re.compile(r'(없어졌|없어지|과거|당시|예전에|옛날|한때|종료|폐지)')
COND = re.compile(r'(다만|하지만|단점|조건|예외|제외|만약|그런데|안\s*되|못\s*하|불가|제한)')
FINANCE_TAX = re.compile(r'(소득\s*공제|세액\s*공제|연금|세율|절세|환급|세금|세우|납입|공제)')
ALLOWED_ROLES={'CONTRIBUTION','INCOME_DEDUCTION_RATE','DEDUCTIBLE_BASIS','ASSUMED_TAX_RATE','TAX_SAVING','EFFECTIVE_SAVING_RATE','TERM','CONDITION','EXCEPTION','PRODUCT_HISTORY','OTHER_NUMBER'}
LABELS={'CANDIDATE_LINK_REVIEW_REQUIRED','ARITHMETIC_CONSISTENT_SCOPE_OPEN','ARITHMETIC_CONFLICT_OPEN','OPERAND_MISSING_OPEN'}

def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(data):return hashlib.sha256(data if isinstance(data,bytes) else data.encode('utf-8')).hexdigest()
def digest(obj):return sha(canonical(obj))
def require(expr,code):
 if not expr:raise ValueError('V104_'+code)
def _decimal(x):
 require(type(x) in (str,int) and not isinstance(x,bool),'NUMERIC_TYPE')
 try:y=Decimal(str(x))
 except InvalidOperation:raise ValueError('V104_NUMERIC_PARSE')
 require(y.is_finite() and y>=0,'NUMERIC_FINITE')
 return y

def tokenize(cues,*,video_id):
 """Source cue list is (index,text) pairs, generally within a frozen window.
    Return private suggestions; strip cue text before public storage.
 """
 require(type(cues)==list and len(cues)>0,'SOURCE_LIST')
 indices=[x['index'] for x in cues]
 require(all(type(i) is int and i>0 for i in indices) and indices==list(range(indices[0],indices[0]+len(indices))),'SOURCE_CONTIGUITY')
 nodes=[];warnings=[]
 for c in cues:
  require(type(c['text']) is str and bool(c['text']),'SOURCE_TEXT')
  t=c['text'];i=c['index'];h=sha(t)
  for typ,rx in [('AMOUNT',AMOUNT),('RATE',RATE),('PERIOD',PERIOD)]:
   for m in rx.finditer(t):
    unit=(m.group(2).replace(' ','') if typ!='RATE' else '%')
    raw=m.group(1).replace(',','')
    mult={'억 원':100000000,'만원':10000,'만 원':10000,'천 원':1000,'천원':1000,'원':1}.get(m.group(2),1) if typ=='AMOUNT' else 1
    number=_decimal(raw)*mult
    nodes.append({'cue_index':i,'source_sha256':h,'kind':typ,'value':str(number),'unit':'KRW' if typ=='AMOUNT' else unit,
                  'role':'UNASSIGNED','surface_span_sha256':sha(m.group(0))})
  if HISTORIC.search(t):warnings.append({'cue_index':i,'cue_sha256':h,'type':'HISTORICAL_APPLICABILITY_UNKNOWN'})
  if COND.search(t):warnings.append({'cue_index':i,'cue_sha256':h,'type':'CONDITION_OR_EXCEPTION_REVIEW'})
 return nodes,warnings

def propose_tax_chain(cues,*,video_id,window_id,max_cues=22):
 """Find plausible multi-cue income deduction calculation: never certify law.
    Scan a bounded context around an explicit income-deduction phrase.
 """
 require(type(max_cues) is int and 5<=max_cues<=40,'MAX_CONTEXT')
 nodes,warnings=tokenize(cues,video_id=video_id)
 text=[c['text'] for c in cues];idx=[c['index'] for c in cues]
 candidates=[]
 anchors=[j for j,t in enumerate(text) if re.search(r'소득\s*공제',t)]
 seen=set()
 for anchor in anchors:
  left=max(0,anchor-4);right=min(len(cues),anchor+max_cues)
  subset=cues[left:right]; t=' '.join(z['text'] for z in subset)
  if not FINANCE_TAX.search(t):continue
  money=[x for x in nodes if x['kind']=='AMOUNT' and subset[0]['index']<=x['cue_index']<=subset[-1]['index']]
  rates=[x for x in nodes if x['kind']=='RATE' and subset[0]['index']<=x['cue_index']<=subset[-1]['index']]
  if not money or not rates:continue
  # Multiple occurrences of '소득공제' in one explanation must not inflate
  # distinct claim counts. Fingerprint the cited numeric cue set instead.
  signature=tuple(sorted((n['cue_index'],n['kind'],n['value']) for n in money+rates))
  if signature in seen:continue
  seen.add(signature)
  cues_sha=[{'cue_index':z['index'],'cue_sha256':sha(z['text'])} for z in subset]
  candidates.append({'video_id':video_id,'window_id':window_id,'start_cue':subset[0]['index'],'end_cue':subset[-1]['index'],
        'cue_receipt_sha256':digest(cues_sha),'numeric_nodes':money+rates,
        'warnings':[z for z in warnings if subset[0]['index']<=z['cue_index']<=subset[-1]['index']],
        'speaker_continuity_verified':False,'current_law_applicability_verified':False,
        'all_claims_found':False,'human_context_review_required':True,'independent_gold':False,'p0_go':False})
 return candidates

def review_arithmetic(graph, source_cues, *, archive_sha256, expected_archive_sha256):
 """Check explicit reviewer-selected cross-cue roles and equations; not truth.

    Each node must exist in the candidate source, be numerically exact and
    cite its original cue. Each role can appear at most once per graph.
 """
 require(archive_sha256==expected_archive_sha256 and re.fullmatch('[a-f0-9]{64}',archive_sha256)!=None,'ARCHIVE_PIN')
 require(type(graph)==dict and type(source_cues)==list and len(source_cues)>0,'GRAPH_INPUT')
 indices=[c['index'] for c in source_cues]
 require(len(indices)<=80 and indices==list(range(indices[0],indices[0]+len(indices))),'CUE_CONTIGUITY_AND_SPAN_CAP')
 bycue={c['index']:c for c in source_cues}
 graph_ids=graph.get('source_cue_indices')
 require(type(graph_ids)==list and graph_ids and len(graph_ids)==len(set(graph_ids)) and set(graph_ids)<=set(indices),'GRAPH_SOURCE_INDICES')
 require(graph.get('source_span_sha256')==digest([[i,sha(bycue[i]['text'])] for i in graph_ids]),'GRAPH_SPAN_SHA')
 roles={};role_sources={}
 for node in graph.get('nodes',[]):
  require(type(node)==dict,'NODE')
  role=node.get('role');i=node.get('cue_index');k=node.get('kind');unit=node.get('unit')
  require(role in ALLOWED_ROLES and role not in roles,'ROLE_DUP_OR_UNKNOWN')
  require(i in graph_ids and node.get('cue_sha256')==sha(bycue[i]['text']),'NODE_SOURCE')
  allowed=tokenize([bycue[i]],video_id=graph.get('video_id',''))[0]
  wanted=_decimal(node.get('value'))
  require(any(x['kind']==k and x['unit']==unit and _decimal(x['value'])==wanted for x in allowed),'NODE_VALUE_NOT_IN_ORIGINAL')
  roles[role]=wanted;role_sources[role]=i
 require({'CONTRIBUTION','INCOME_DEDUCTION_RATE','DEDUCTIBLE_BASIS','ASSUMED_TAX_RATE','TAX_SAVING'}<=roles.keys(),'MISSING_CHAIN_ROLE')
 calc_basis=roles['CONTRIBUTION']*roles['INCOME_DEDUCTION_RATE']/Decimal(100)
 calc_tax=roles['DEDUCTIBLE_BASIS']*roles['ASSUMED_TAX_RATE']/Decimal(100)
 match_basis=abs(calc_basis-roles['DEDUCTIBLE_BASIS'])<=Decimal('1')
 match_tax=abs(calc_tax-roles['TAX_SAVING'])<=Decimal('1')
 effective=roles['TAX_SAVING']/roles['CONTRIBUTION']*100 if roles['CONTRIBUTION']>0 else None
 effective_match=(effective is not None and ('EFFECTIVE_SAVING_RATE' not in roles or abs(effective-roles['EFFECTIVE_SAVING_RATE'])<=Decimal('.01')))
 status='ARITHMETIC_CONSISTENT_SCOPE_OPEN' if match_basis and match_tax and effective_match else 'ARITHMETIC_CONFLICT_OPEN'
 context_refs=graph.get('scope_context_refs',[])
 require(type(context_refs)==list,'CONTEXT_REFS_TYPE')
 seenrefs=set();trigger_count=0
 for ref in context_refs:
  i=ref.get('cue_index');role=ref.get('role')
  require(i in graph_ids and role in {'CONDITION_TRIGGER','CONTEXT_CONTINUATION','HISTORICAL_SCOPE'},'CONTEXT_REF_SCOPE')
  require((i,role) not in seenrefs,'DUPLICATE_CONTEXT_REF');seenrefs.add((i,role))
  require(ref.get('cue_sha256')==sha(bycue[i]['text']),'CONTEXT_SOURCE_SHA')
  require(type(ref.get('review_note_private')) is str and len(ref['review_note_private'])>=20,'CONTEXT_REASON')
  if role=='CONDITION_TRIGGER':
   require(COND.search(bycue[i]['text']) or PERIOD.search(bycue[i]['text']),'NON_CONDITION_TRIGGER')
   trigger_count+=1
  if role=='HISTORICAL_SCOPE':
   require(HISTORIC.search(bycue[i]['text']),'NON_HISTORICAL_SCOPE')
 require(not context_refs or trigger_count>=1,'NO_CONDITION_TRIGGER')
 require(graph.get('reviewer_scope_note_private') and len(graph['reviewer_scope_note_private'])>=20,'SCOPE_NOTE')
 require(graph.get('speaker_identity_certified') is False and graph.get('current_law_approved') is False and graph.get('independent_gold') is False and graph.get('p0_go') is False,'FALSE_APPROVAL')
 return {'schema':'V104_CROSS_CUE_MONEY_RATE_DEDUCTION_REVIEW_NOT_FINANCIAL_FACT_V1',
 'graph_source_digest':graph['source_span_sha256'],'node_count':len(roles),'cue_count':len(graph_ids),
 'linked_context_source_count':len(context_refs),'condition_trigger_source_count':trigger_count,
 'role_source_indices':role_sources,'arithmetic_status':status,'basis_arithmetic_matches':match_basis,
 'tax_arithmetic_matches':match_tax,'effective_rate_arithmetic_matches':effective_match,
 'historical_or_current_law_unverified':True,'speaker_identity_unverified':True,
 'independent_gold':False,'financial_fact_approved':False,'p0_go':False}