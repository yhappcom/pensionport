#!/usr/bin/env python3
"""V3.4: source-bound, conservative Korean atomic/financial-frame proposal engine.

All generated atoms and semantic frames are PROPOSALS, never human-verified facts.
No unreviewed cue may disappear, even when apparently nonfinancial or nonverbal.
Frozen V3.0-V3.3 modules and their first-use results are not modified.
"""
from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from collections import Counter
from v30_verified_core import parse_srt, sha256, canonical, guard, VID_RE, HASH_RE

SCHEMA = "V34_SOURCE_BOUND_ATOMIC_SEMANTIC_PROPOSALS_V1"
RX_WORD = re.compile(r"[a-z0-9가-힣]+", re.I)
RX_SPLIT = re.compile(r"(?<=[.!?。])\s+|(?<=[.!?。])(?=[가-힣])")
RX_CONTRAST = re.compile(r"\s+(?=하지만|그러나|반면에?|그런데)\s*")
RX_NUMBER = re.compile(r"(?<![0-9A-Za-z])(-?\d{1,3}(?:,\d{3})+|-?\d+(?:\.\d+)?)\s*(억원|만원|천원|원|%|퍼센트|개월|년|주|달러|USD|주식)", re.I)
RX_MENTION = re.compile(r"(?:\b(?:IRP|ISA|ETF|NAV|TR|PR)\b|연금저축|퇴직연금|국민연금|기준금리|예적금|예금|적금|채권|주식|세액공제|분배금|배당|환율|리밸런싱|포트폴리오)", re.I)
RX_NEGATED = re.compile(r"않(?:아|습|는|다)|아니(?:다|에요|고)|못(?:하|해)|없(?:다|습|어)|불가능|금지|제외")
RX_HYPOTHETICAL = re.compile(r"만약|가정(?:하면|해서|하자)|예를\s*들|라고\s*가정|경우라면|한다면|했을\s*때")
RX_CONDITIONAL = re.compile(r"경우|조건|이상|이하|초과|미만|부터|까지|한해서|때에만|라면|다면")

# A controlled taxonomy with overlapping facets. Product identity never proves
# event identity: e.g. ISA maturity != bond maturity, tax credit != payout tax.
ENTITY_ALIASES = {
 "IRP": (r"\bIRP\b|개인형\s*퇴직연금", "ACCOUNT"),
 "ISA": (r"\bISA\b|개인종합자산관리계좌|개인\s*종합\s*자산\s*관리", "ACCOUNT"),
 "PENSION_SAVINGS": (r"연금저축|연금\s*계좌", "ACCOUNT"),
 "NATIONAL_PENSION": (r"국민연금", "PENSION"),
 "RETIREMENT_PENSION": (r"퇴직연금|퇴직\s*급여", "PENSION"),
 "ETF": (r"\bETF\b|상장지수펀드", "FUND"),
 "BOND": (r"채권|국채|회사채", "BOND"),
 "EQUITY": (r"주식|주가|개별종목", "STOCK"),
 "DEPOSIT": (r"예금|적금|예적금", "DEPOSIT"),
 "PORTFOLIO": (r"포트폴리오|자산배분|리밸런싱", "PORTFOLIO"),
 "FOREX": (r"환율|환전|외환", "CURRENCY"),
}
EVENT_RULES = {
 "PENSION_TAX_CONTRIBUTION": r"세액공제|소득공제|납입.*(?:공제|세금)|공제.*납입",
 "PENSION_TAX_WITHDRAWAL": r"(?:인출|수령|연금\s*받).{0,20}(?:세금|세율|과세)|(?:과세|세금).{0,20}(?:인출|수령)",
 "ETF_NAV_DISCOUNT": r"\bNAV\b|괴리율|순자산가치|기준가격.*(?:ETF|펀드)",
 "ETF_TRACKING": r"추적오차|추종오차|지수.*(?:추적|추종)|(?:추적|추종).*지수",
 "ETF_FEE": r"운용보수|총보수|ETF.{0,15}보수|보수율",
 "POLICY_RATE": r"기준금리|정책금리|중앙은행.*금리|한국은행.*금리",
 "PRODUCT_YIELD": r"이자율|예금금리|적금금리|수익률|배당수익률",
 "GOVERNMENT_MATCH": r"정부기여금|정부.{0,8}(?:매칭|지원|기여금)|국가.{0,8}기여금",
 "ETF_DISTRIBUTION": r"분배금|분배락|ETF.{0,12}(?:분배|배당)",
 "BOND_MATURITY": r"채권.{0,12}만기|국채.{0,12}만기|만기.{0,12}(?:채권|국채)",
 "ACCOUNT_MATURITY": r"ISA.{0,12}만기|만기.{0,12}ISA|적금.{0,12}만기|만기.{0,12}적금",
 "PENSION_CONTRIBUTION": r"(?:연금|IRP).{0,15}(?:납입|적립)|(?:납입|적립).{0,15}(?:연금|IRP)",
 "PENSION_WITHDRAWAL": r"(?:연금|IRP).{0,15}(?:인출|수령)|(?:인출|수령).{0,15}(?:연금|IRP)",
 "PORTFOLIO_ALLOCATION": r"자산배분|리밸런싱|포트폴리오.*(?:비중|분산)|분산투자",
 "FOREIGN_EXCHANGE": r"환율|환전|달러.{0,15}(?:매수|매도)",
 "EQUITY_RISK": r"주식.{0,15}(?:손실|위험|변동성)|주가.{0,12}(?:하락|급등)|종목.{0,10}위험",
}
ACTION_RULES = {
 "TAX": r"과세|세액공제|소득공제|세율|세금|비과세",
 "WITHDRAW": r"인출|수령|출금|해지",
 "CONTRIBUTE": r"납입|추납|적립|입금",
 "TRADE": r"매수|매도|거래|매매",
 "REBALANCE": r"리밸런싱|자산배분|비중\s*조절",
 "DISTRIBUTE": r"배당|분배|지급",
 "MATURE": r"만기|상환",
 "CALCULATE": r"계산|복리|원금|시뮬레이션",
 "COMPARE": r"비교|차이|대비|반면",
 "ADVISE": r"추천|권유|조언|하세요|해야\s*합니다",
}
_COMPILED_ENTITIES = {key:(re.compile(pattern,re.I),kind) for key,(pattern,kind) in ENTITY_ALIASES.items()}
_COMPILED_EVENTS = {key:re.compile(pattern,re.I) for key,pattern in EVENT_RULES.items()}
_COMPILED_ACTIONS = {key:re.compile(pattern,re.I) for key,pattern in ACTION_RULES.items()}

def normalize(text):
    return re.sub(r"\s+", " ", text).strip()

def segment_cue(text):
    """Bounded segmentation; uncertainty about speech/clauses is explicit."""
    full = normalize(text)
    guard(full, "EMPTY_CUE_PROPOSAL")
    parts = [x.strip() for x in RX_SPLIT.split(full) if x.strip()]
    out = []
    for part in parts:
        chunks = RX_CONTRAST.split(part)
        out.extend(x.strip() for x in chunks if x.strip())
    return out or [full]

def make_draft(raw_srt, expected_sha256, video_id, max_claims=25000):
    guard(type(video_id) is str and VID_RE.fullmatch(video_id), "V34_VIDEO_ID_REQUIRED")
    cues = parse_srt(raw_srt, expected_sha256)
    guard(len(cues) <= max_claims, "V34_REQUIRES_CHUNKED_SOURCE_PLAN")
    claims = []
    mapping = []
    for cue in cues:
        refs = []
        for part in segment_cue(cue.text):
            guard(len(claims) < max_claims, "V34_CLAIM_BOUND_EXCEEDED")
            ident = video_id + "-A" + str(len(claims)+1).zfill(5)
            prior = normalize(cues[cue.index-2].text) if cue.index > 1 else ""
            claims.append({
                "claim_id":ident, "video_id":video_id,
                "source_srt_sha256":expected_sha256,
                "cue_indices":[cue.index], "source_quote":part,
                "quote_sha256":sha256(part.encode("utf-8")),
                "context_previous_sha256":sha256(prior.encode("utf-8")),
                "claim_status":"PROPOSED_UNREVIEWED",
                "materiality":"UNCLASSIFIED_REVIEW_REQUIRED",
                "atomization_confidence":"UNVERIFIED_SEGMENTATION",
                "source_exposure":"NOT_ATTESTED",
            })
            refs.append(ident)
        mapping.append({"cue_index":cue.index,"claim_ids":refs,
                        "classification":"REVIEW_REQUIRED",
                        "human_exclusion_authorized":False})
    report = {
        "schema":SCHEMA, "video_id":video_id, "source_srt_sha256":expected_sha256,
        "source_cue_count":len(cues), "proposed_claim_count":len(claims),
        "cues":mapping, "claims":claims,
        "all_cues_mapped_to_proposals":True,
        "all_semantic_statements_independently_extracted":False,
        "source_audio_verified":False, "reviewed_atomic_ledger":False,
        "automatic_research_approval":False
    }
    validate_draft(report,raw_srt,expected_sha256)
    return report

def validate_draft(draft, raw_srt, expected_sha256):
    cues=parse_srt(raw_srt, expected_sha256)
    guard(type(draft) is dict and draft.get("schema")==SCHEMA
          and draft.get("source_srt_sha256")==expected_sha256
          and len(draft.get("cues",[]))==len(cues)
          and draft.get("source_cue_count")==len(cues)
          and draft.get("all_semantic_statements_independently_extracted") is False
          and draft.get("reviewed_atomic_ledger") is False,
          "V34_SOURCE_LEDGER_TAMPER_OR_FALSE_REVIEW")
    claims=draft.get("claims",[])
    guard(type(claims) is list and len(claims)==draft.get("proposed_claim_count")
          and len(claims)<=25000, "V34_CLAIM_CENSUS_TAMPER")
    byid={}
    for n,row in enumerate(claims,1):
        cid=draft["video_id"]+"-A"+str(n).zfill(5)
        indices=row.get("cue_indices")
        guard(row.get("claim_id")==cid and indices and len(indices)==1
              and type(indices[0]) is int and 1<=indices[0]<=len(cues)
              and row.get("source_srt_sha256")==expected_sha256
              and row.get("quote_sha256")==sha256(row.get("source_quote","").encode("utf-8"))
              and normalize(row["source_quote"]) in normalize(cues[indices[0]-1].text)
              and row.get("claim_status")=="PROPOSED_UNREVIEWED"
              and row.get("materiality")=="UNCLASSIFIED_REVIEW_REQUIRED",
              "V34_PROPOSED_CLAIM_NOT_TRACEABLE_TO_SOURCE")
        byid[cid]=indices[0]
    for n,row in enumerate(draft["cues"],1):
        ids=row.get("claim_ids",[])
        guard(row.get("cue_index")==n and isinstance(ids,list) and ids
              and len(ids)==len(set(ids))
              and all(byid.get(cid)==n for cid in ids)
              and row.get("classification")=="REVIEW_REQUIRED"
              and row.get("human_exclusion_authorized") is False,
              "V34_FULL_CUE_COVERAGE_OR_CUE_REVERSE_LINK_INVALID")
    guard(sum(len(x["claim_ids"]) for x in draft["cues"])==len(claims)
          and all(draft["video_id"]==c["video_id"] for c in claims),
          "V34_CUE_ATOM_BIJECTION_INVALID")
    return True

def _numbers(text):
    numbers=[]
    for match in RX_NUMBER.finditer(text):
        value=match.group(1).replace(",","")
        try:dec=Decimal(value)
        except InvalidOperation:continue
        if not dec.is_finite():continue
        unit=match.group(2).upper()
        unit_scale={"만원":10000,"억원":100000000,"천원":1000}
        normalized=str(dec*unit_scale.get(unit,1))
        kind=("PERCENT_RATE" if unit in ("%", "퍼센트") else
              "MONEY" if unit in ("원","천원","만원","억원","달러","USD") else
              "PERIOD" if unit in ("개월","년","주") else "QUANTITY")
        numbers.append({"text":match.group(0),"value":value,"unit":unit,
                        "normalized_value":normalized,"kind":kind,
                        "rate_basis":"UNRESOLVED" if kind=="PERCENT_RATE" else "NOT_APPLICABLE"})
    return numbers

def infer_frame(atom):
    """An abstaining inference proposal: typed events do not certify meaning."""
    guard(type(atom) is dict and atom.get("claim_status")=="PROPOSED_UNREVIEWED"
          and type(atom.get("source_quote")) is str
          and type(atom.get("quote_sha256")) is str
          and atom["quote_sha256"]==sha256(atom["source_quote"].encode("utf-8")),
          "V34_INFERENCE_REQUIRES_SOURCE_BOUND_PROPOSAL")
    text=atom["source_quote"]
    entities=[{"id":name,"kind":kind} for name,(rx,kind) in _COMPILED_ENTITIES.items()
              if rx.search(text)]
    events=[name for name,rx in _COMPILED_EVENTS.items() if rx.search(text)]
    actions=[name for name,rx in _COMPILED_ACTIONS.items() if rx.search(text)]
    if RX_NEGATED.search(text):modality="NEGATED"
    elif RX_HYPOTHETICAL.search(text):modality="HYPOTHETICAL"
    elif RX_CONDITIONAL.search(text):modality="CONDITIONAL"
    else:modality="ASSERTED_PROVISIONAL"
    # A single fragment may carry distinct events; do not silently choose one.
    event = events[0] if len(events)==1 else "UNRESOLVED"
    guard(len(text)<=16000,"V34_CLAIM_TEXT_TOO_LONG")
    numbers=_numbers(text)
    flags=[]
    if len(events)>1:flags.append("MULTI_EVENT_OR_SCOPE_REVIEW")
    if not events:flags.append("UNKNOWN_FINANCIAL_EVENT")
    if not entities:flags.append("UNKNOWN_FINANCIAL_ENTITY")
    if not actions:flags.append("UNKNOWN_FINANCIAL_ACTION")
    if len(numbers)>1:flags.append("MULTIPLE_MEASUREMENTS_REVIEW")
    if any(n["rate_basis"]=="UNRESOLVED" for n in numbers):
        flags.append("RATE_BASIS_AND_DENOMINATOR_REVIEW")
    if len(text)<10:flags.append("CONTEXT_DEPENDENCE_REVIEW")
    if not RX_MENTION.search(text) and not events:flags.append("NONFINANCIAL_OR_IMPLICIT_REVIEW")
    return {
        "schema":"V34_FINANCIAL_FRAME_PROPOSAL_V1",
        "claim_id":atom["claim_id"],
        "source_srt_sha256":atom["source_srt_sha256"],
        "quote_sha256":atom["quote_sha256"],
        "entities":entities, "event_candidates":events, "event_kind":event,
        "action_candidates":actions, "action":actions[0] if len(actions)==1 else "UNRESOLVED",
        "modality":modality, "conditions":{
            "has_condition":bool(RX_CONDITIONAL.search(text)),
            "population":"UNRESOLVED",
            "exception":"UNRESOLVED",
            "trigger":"UNRESOLVED"},
        "jurisdiction":"UNRESOLVED","effective_date":"UNRESOLVED",
        "measurements":numbers,"ambiguity_flags":sorted(set(flags)),
        "annotation_status":"PROPOSED_UNREVIEWED",
        "financial_fact_verified":False,
        "automatic_knowledge_merge":False
    }

def attach_frames(draft):
    guard(draft.get("schema")==SCHEMA and draft.get("reviewed_atomic_ledger") is False,
          "V34_ONLY_DRAFTS_CAN_RECEIVE_MODEL_PROPOSALS")
    frames=[infer_frame(atom) for atom in draft["claims"]]
    guard(len(frames)==draft["proposed_claim_count"],"V34_SEMANTIC_COVERAGE_MISMATCH")
    return {
        "schema":"V34_SEMANTIC_CENSUS_V1",
        "source_sha256":draft["source_srt_sha256"],
        "draft_sha256":sha256(canonical(draft)),
        "frames":frames,
        "total_proposals":len(frames),
        "unresolved_events":sum(x["event_kind"]=="UNRESOLVED" for x in frames),
        "unreviewed_frames":len(frames),
        "all_material_claims_verified":False,
        "human_semantic_accuracy_proven":False,
        "review_status":"BLOCKED_PENDING_INDEPENDENT_REVIEW"
    }
