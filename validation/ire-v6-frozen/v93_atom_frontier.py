"""V93 source-first omission *risk* census, not semantic recall certification.
Enumerate every cue, independent of candidate capture, preserving all original
cue and candidate identities without releasing text in public receipts.
"""
import hashlib,json,re
from collections import Counter
FIN=re.compile(r'(ISA|IRP|ETF|TDF|CMA|연금|수익|금리|이자|채권|주식|리츠|증여|세금|배당|계좌|보험|퇴직|원금|투자|손실|펀드|납입|추납|매도|매수)',re.I)
NUM=re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')
QUAL=re.compile(r'(?:하지만|다만|그런데|반대로|예외|경우|만약|조건|아니|그게 아니|정확히|수정|제외|않|보다|인가요|될까요)')
COMPOUND=re.compile(r'(?:그리고|그런데|반면|그러나|따라서|한편|또한|하지만|이거나|또는|\bvs\b)')
ASR=re.compile(r'(?:무슨 말|다시 말씀|잘 안 들|발음|자막|정확히)')

def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def require(b,m):
    if not b:raise ValueError('V93_'+m)

def scan_source(cues,registry,*,expected_video_id,expected_cues,expected_windows):
    """Bounded linear-ish structural audit; output contains no raw cue text."""
    require(len(cues)==expected_cues,'CUE_COUNT')
    require(len(registry)==expected_windows,'WINDOW_COUNT')
    index_map={};all_parents=set()
    for w,rows in registry.items():
        require(type(w) is str and re.fullmatch(r'W\d{5}',w)!=None,'WINDOW_ID')
        for row in rows:
            cid=row['claim_id'];key=(w,cid)
            require(key not in all_parents,'DUP_PARENT');all_parents.add(key)
            ix=row['cue_indices'];require(ix and len(set(ix))==len(ix),'DUP_PARENT_CUE')
            for i in ix:
                require(type(i) is int and 1<=i<=len(cues),'INVALID_CUE_INDEX')
                require((i-1)//40+1==int(w[1:]),'CROSS_WINDOW_PARENT')
                index_map.setdefault(i,[]).append(key)
    risk_count=Counter();risk_pins=[];unassigned=0;max_assigned=0;checked=0
    for i,c in enumerate(cues,1):
        require(c.index==i and c.end_ms>=c.start_ms,'SOURCE_ORDER')
        t=c.text
        linked=index_map.get(i,[])
        if not linked:unassigned+=1
        else:max_assigned=max(max_assigned,len(linked))
        kinds=[]
        if not linked and FIN.search(t):kinds.append('UNCAPTURED_FINANCE_CUE')
        if not linked and NUM.search(t):kinds.append('UNCAPTURED_NUMERIC_CUE')
        if QUAL.search(t):kinds.append('QUALIFIER_REVIEW')
        if COMPOUND.search(t) and FIN.search(t):kinds.append('COMPOUND_REVIEW')
        if len(NUM.findall(t))>=2 and FIN.search(t):kinds.append('MULTINUMERIC_REVIEW')
        if ASR.search(t):kinds.append('ASR_REVIEW')
        if len(linked)>1:kinds.append('OVERLAPPING_CANDIDATE_REVIEW')
        for kind in kinds:
            risk_count[kind]+=1
            risk_pins.append([i,kind,hashlib.sha256(t.encode('utf-8')).hexdigest()])
        checked+=1
    require(checked==expected_cues,'INCOMPLETE_SOURCE_SCAN')
    return {'schema':'V93_SOURCE_FIRST_RISK_NOT_ATOM_RECALL_V1','video_id':expected_video_id,
        'source_cues_checked':checked,'source_windows_checked':len(registry),'draft_parent_count':len(all_parents),
        'source_cues_without_draft_parent':unassigned,'max_parent_overlap_per_cue':max_assigned,
        'risk_count_by_kind':dict(sorted(risk_count.items())),
        'risk_case_count':len(risk_pins),'risk_case_receipt_sha256':digest(risk_pins),
        'source_excerpt_public':False,'independent_omission_accuracy_certified':False,
        'full_atomic_decomposition_certified':False,'p0_go':False}

def review_subclaims(parent,subclaims):
    """Do not equate all-parent coverage with subclaim coverage."""
    require(type(subclaims) is list and len(subclaims)>0,'SUBCLAIMS_REQUIRED')
    indices=set(parent['cue_indices']);covered=set()
    for s in subclaims:
        refs=s.get('cue_indices')
        require(type(refs) is list and refs,'ATOM_NO_REFS')
        require(set(refs)<=indices,'ATOM_OUTSIDE_PARENT')
        require(s.get('stance') in {'FACT_CANDIDATE','OPINION','QUESTION','HYPOTHESIS','CONDITION','EXCEPTION','REBUTTAL','UNCERTAIN'},'STANCE')
        require(s.get('independent_fact_approved') is False,'FALSE_APPROVAL')
        covered.update(refs)
    require(covered==indices,'PARENT_CUE_NOT_ACCOUNTED')
    return {'draft_subclaim_count':len(subclaims),'parent_cues_accounted':len(indices),'semantic_truth_certified':False}