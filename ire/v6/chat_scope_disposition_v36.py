"""V36: exact-parent 13-case ChatGPT semantic-scope disposition on owner-original SRT.

The host determines meaning, source/current-law applicability, and master-claim
non-equivalence. The engine verifies immutable V35 case lineage, original SRT
cue/context bytes, provenance, review exhaustiveness and evidence caveats.

V36 source/meaning *triage* is NOT an independent claim truth audit, audio
transcription, verified broker product quote, personalized suitability check,
master-knowledge merge or blind precision/recall certification.
"""
from __future__ import annotations

from urllib.parse import urlsplit
from pathlib import Path
import zipfile

from .codec import json_digest, sha256
from .errors import InvalidInput
from .source import parse_srt

ZIP_SHA = '00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V35_RECEIPT_SHA = 'e0f5c5fb63c685af890c02111ab5d1c8a1bcad58b307288ffca04592c4d208b0'
MASTER116_ROOT_SHA = '0c5d5c84092795f273ba89f5595bf9aba484032db9a889939e3505a006a2c168'
VIDEO_HASHES = {
    'sz5N9WJS310':'2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f',
    '6VEfKF7BzZU':'a59b2fd424011c3f572aa52404411ff4ea435f6dd1e7e27e4f5c9e11f7218b72',
    'OiDTNstaSpM':'e94b12a1084a8b57c3b9c2a630e27f840ae5a827b3a71c62526e15380a7c57bd',
    'aNfGrcO6WPI':'853db2d4f01ab71bbc4f86b46714f4341aa32aa2bc07416f705a937b620ea12b',
}
# Immutable prior V35 OPEN case identity and its previously selected approved
# master-knowledge ROW hash. Values are not claims of actual semantic equality.
_PARENT = [
 ('sz5N9WJS310',390,'7a117bd47cfac023537ff11f846a0ec17275e4d58a2463801d2721a30aab3d45','GOMHEE-C45','647905ef772481a015a648a4915335df95036bbbaf31686f452bfbe356f6b53c'),
 ('sz5N9WJS310',561,'706a3c3daccd79663e18023a233323a1524d04f4cf962b8f0105294305d870de','GOMHEE-C78','d044c5736ae83732b4749243e0bd57cd592e413eab833c6b13cdd19ef5e8e0c5'),
 ('sz5N9WJS310',561,'aa4470a522fc74cae4d7f148b83778d485552e97b79cfae9e047dbdd80f0bb4e','GOMHEE-C78','d044c5736ae83732b4749243e0bd57cd592e413eab833c6b13cdd19ef5e8e0c5'),
 ('sz5N9WJS310',618,'05775faa49e4d20cf92157d10ad769048da3c05fa022fca22103c03e558414f6','GOMHEE-C45','647905ef772481a015a648a4915335df95036bbbaf31686f452bfbe356f6b53c'),
 ('sz5N9WJS310',618,'6eda09d0355bd4bce7ddfd8d2207d5ef2d07c62ab4431660d88e7fe5364e0761','GOMHEE-C45','647905ef772481a015a648a4915335df95036bbbaf31686f452bfbe356f6b53c'),
 ('6VEfKF7BzZU',425,'991710ac58a2fc358c4111ef02fd8aba458a106d8dc0e93a5008cabef4351a1c','GOMHEE-C20','662d07e810141db6ad4096d5b63e2100e7f35e255ff4a92dee36eae29f8ed34b'),
 ('6VEfKF7BzZU',520,'a1dadd5dea0011a8dce257ed11b02d40a0a86a204f5ad3876251a3c05581af85','GOMHEE-C65','c7bc4719d7f30dd6d08f5e0a7a5efe829f5fd38911b4f98c2910538735c45da0'),
 ('6VEfKF7BzZU',520,'d6046ba9699d88632fdf746dafc92f1bd9ce2856d39e4bf92db214ef4252d3a4','GOMHEE-C65','c7bc4719d7f30dd6d08f5e0a7a5efe829f5fd38911b4f98c2910538735c45da0'),
 ('6VEfKF7BzZU',520,'fc71e50ebe2ecc7988a5b3b54e45d257cd4cae6b2fe848e14bf67db3057388fd','GOMHEE-C65','c7bc4719d7f30dd6d08f5e0a7a5efe829f5fd38911b4f98c2910538735c45da0'),
 ('sz5N9WJS310',954,'b320c131c32a2e9b51a9849a9e9bc5aedf2b71af55c3896baa40d46008714fda','GOMHEE-C15','901c737367aef69b49368241973cba055b230f0fc03c1c8fc28bf67395d85fe4'),
 ('6VEfKF7BzZU',1218,'959baf639bb086693cca617effc8a1bfaeb11b65a1eace315a953ea939b930af','GOMHEE-C09','aada420fdac19ec3532b1da7d4ec16951682f206f00eb338df9aa2c979a900d4'),
 ('OiDTNstaSpM',132,'93c29f3a307e322392febec5ab638f2bbcaa401bc5f5b9674663c1a915632e7c','GOMHEE-C68','d305b3524f8bd5363844d3b81e77734b82d45e3301d67528514677093cf18387'),
 ('aNfGrcO6WPI',384,'2b6ac8feec251dc973cab3a50a21f28bc95319dd04f3723978410120e8a3ab8c','GOMHEE-C51','de821d4f1cc59cc0eef4ad8070a6e583cc4f6e3cd54ebb0618f27124799b57a4'),
]
TARGETS = {case: {'video_id':vid,'hinge_cue':cue,'master_claim_id':master,'master_row_sha256':master_sha}
           for vid,cue,case,master,master_sha in _PARENT}
assert len(TARGETS)==13
_CONTEXT = {
 ('sz5N9WJS310',390):(375,405,'PENSION_TAX_OPTION'),
 ('sz5N9WJS310',561):(531,575,'PENSION_NONCREDIT_BASIS'),
 ('sz5N9WJS310',618):(591,651,'WITHDRAWAL_DIVIDEND_EXAMPLE'),
 ('6VEfKF7BzZU',425):(415,446,'CMA_SETTLEMENT_ANECDOTE'),
 ('6VEfKF7BzZU',520):(485,535,'CMA_HISTORICAL_RATE'),
 ('sz5N9WJS310',954):(945,960,'TAX_POLICY_INVESTING_POSTURE'),
 ('6VEfKF7BzZU',1218):(1204,1228,'PERSONAL_STOCK_COUNT_PREFERENCE'),
 ('OiDTNstaSpM',132):(123,152,'IRP_ONE_MAN_WON_EARLY_START'),
 ('aNfGrcO6WPI',384):(376,405,'LOSS_POSITION_HOLD_EXPERIENCE'),
}
_CHILD_PINS={
 ('sz5N9WJS310',390):'59e0f919100e20327c61c7d97a4e2bee468b29a1ba84a4eb2d7ea86706fd9a2b',
 ('sz5N9WJS310',561):'fd509a6d0cc32cff3edc9943514ba8df15f62088216f822a0690db4b660dff29',
 ('sz5N9WJS310',618):'6252648bfe203abd00b37b842c54d5082792b5b6c23ef07383af0f91f80987f7',
 ('6VEfKF7BzZU',425):'399ec18e7fb86ca9a8736ae142013fa8f28b81a45f4491ab0c82b6e4a8e4c50f',
 ('6VEfKF7BzZU',520):'3ca29c6eccf9437dce5149c0e3600e56d573df6138fb569178246b99c9f062c1',
 ('sz5N9WJS310',954):'15ebfd36fc6c1952c8e3ef24d03b47420b0f1b1208f691520efcd9705d73d95b',
 ('6VEfKF7BzZU',1218):'841cab654a2f119a84d352cfc44dd46658e84816ebdb8fb689c18fe255a496fb',
 ('OiDTNstaSpM',132):'f854d0b2b88b99ba724f1f51841ffab5ad4560778c898506fb65f2fb1de0fb0f',
 ('aNfGrcO6WPI',384):'5cc69aa25970a7b1d1ec2e3818be4c6c22d1ae0c873e8538bb728bc2eeb5015f',
}
_CUE_PINS={
 ('sz5N9WJS310',390):'0f59bfc33aeaae699149df40b1a7d5c82467c47dad2873920ef9c5bbe7bcdc4e',
 ('sz5N9WJS310',561):'6272dd49f96ceff5fd9dbff42b1b804a1ee905053031ffce7c2537e980b55b41',
 ('sz5N9WJS310',618):'d9e801e3c3123081859a3fadf9a38e941252d30c7a7321ce425036b07cf3c311',
 ('6VEfKF7BzZU',425):'fea1bc3a8f45469fb25230014108b01865ef47a0474385f7de0fdc2258f387e3',
 ('6VEfKF7BzZU',520):'9c8de7c4c5e87403ba61f67250d45e1cdc57f8facbe0e46fcbd2dbf1b7a12085',
 ('sz5N9WJS310',954):'8ac2f41844404e0e741ab84ead60ebd724b70dfde40911e327f3bb155e0c82eb',
 ('6VEfKF7BzZU',1218):'4901a4c10c7826f9180f7a9333d2a3b8ebf8c9680a8d0215f2320e80c57ea021',
 ('OiDTNstaSpM',132):'7a7b8b4e996d2392f19a310400ae6e5f4c79cad7dfeb946265d588a77e919516',
 ('aNfGrcO6WPI',384):'45df81e71ba035eb46760763414f9f6ca6fb33fcfa6d21dea64b3983c794bf54',
}
# Minimum distinctive surrounding source-grounding, not a model meaning check.
_MARKERS={
 'PENSION_TAX_OPTION':['1,500','16.5'],
 'PENSION_NONCREDIT_BASIS':['ISA','300만','세공제'],
 'WITHDRAWAL_DIVIDEND_EXAMPLE':['120','500','620'],
 'CMA_SETTLEMENT_ANECDOTE':['CMA','결제'],
 'CMA_HISTORICAL_RATE':['2.15','2.85','RP형'],
 'TAX_POLICY_INVESTING_POSTURE':['투자를','세금'],
 'PERSONAL_STOCK_COUNT_PREFERENCE':['열','종목'],
 'IRP_ONE_MAN_WON_EARLY_START':['1만 원','IRP'],
 'LOSS_POSITION_HOLD_EXPERIENCE':['반도체','킵'],
}
_EVIDENCE_DOMAIN=('nts.go.kr','law.go.kr','kbsec.com')
# Context-bound chat propositions, not automatic fact or trading approvals.
_SCOPE_KINDS={'PENSION_TAX_OPTION','PENSION_NONCREDIT_BASIS','WITHDRAWAL_DIVIDEND_EXAMPLE',
              'CMA_SETTLEMENT_ANECDOTE','CMA_HISTORICAL_RATE'}
_PRIOR_KINDS={'TAX_POLICY_INVESTING_POSTURE','PERSONAL_STOCK_COUNT_PREFERENCE',
              'IRP_ONE_MAN_WON_EARLY_START','LOSS_POSITION_HOLD_EXPERIENCE'}
_PRIOR_RELATIONS={'TOPICALLY_DISTINCT_NO_EQUIVALENCE','PERSONAL_PREFERENCE_NOT_ASSET_ALLOCATION_RULE',
                  'PROVIDER_CASE_NOT_DECUMULATION_EQUIVALENCE','CONDITIONAL_BEHAVIORAL_RELATION_NOT_EQUIVALENT'}


def read_actual_owner_original(zip_path:str):
    """Locally replay actual privately uploaded original; never upload raw cue text."""
    raw=Path(zip_path).read_bytes()
    if sha256(raw)!=ZIP_SHA:
        raise InvalidInput('V36_OWNER_ORIGINAL_ZIP_SHA_DRIFT')
    sources={}
    with zipfile.ZipFile(Path(zip_path)) as z:
        for vid,digest in VIDEO_HASHES.items():
            path=f'1-70/youtube-transcript-{vid}.srt'
            if path not in z.namelist():
                raise InvalidInput('V36_OWNER_ORIGINAL_VIDEO_MISSING')
            original=z.read(path)
            if sha256(original)!=digest:
                raise InvalidInput('V36_OWNER_ORIGINAL_SRT_SHA_DRIFT')
            sources[vid]=parse_srt(original)
    return sources


def audit_chat_disposition_v36(sources:dict, parent_rows:list, host_rows:list, *, current_as_of:str,
                                parent_receipt_sha256:str, master116_rows_digest:str):
    """Verify exact 13 former-open identities and ChatGPT narrow classifications.

    Parent rows must originate from V35's immutable Git-blob-pinned receipt.
    This function cannot authenticate reviewer independence or issuer body.
    """
    if (current_as_of!='2026-11-11' or parent_receipt_sha256!=V35_RECEIPT_SHA or
        master116_rows_digest!=MASTER116_ROOT_SHA):
        raise InvalidInput('V36_ASOF_OR_PARENT_OR_MASTER_PIN_DRIFT')
    if type(parent_rows) is not list or type(host_rows) is not list or len(parent_rows)!=13 or len(host_rows)!=13:
        raise InvalidInput('V36_EXACT_THIRTEEN_REQUIRED')
    if type(sources) is not dict or set(sources)!=set(VIDEO_HASHES):
        raise InvalidInput('V36_FULL_PRIVATE_VIDEO_SCOPE_REQUIRED')
    by_case={}
    for p in parent_rows:
        if type(p) is not dict:
            raise InvalidInput('V36_PARENT_ROW_INVALID')
        cid=p.get('original_case_sha256')
        if cid not in TARGETS or cid in by_case:
            raise InvalidInput('V36_PARENT_CASE_UNEXPECTED_OR_DUPLICATE')
        t=TARGETS[cid]
        if (p.get('video_id')!=t['video_id'] or
            p.get('source_hinge_cue_index')!=t['hinge_cue'] or
            p.get('master_claim_id')!=t['master_claim_id'] or
            p.get('master_row_sha256')!=t['master_row_sha256'] or
            p.get('child_candidate_digest')!=_CHILD_PINS[(t['video_id'],t['hinge_cue'])] or
            p.get('combined_source_and_prior_review_status') not in (
                'ORIGINAL_ASR_OR_FINANCIAL_SCOPE_STILL_OPEN', 'PRIOR_RELATION_REVIEW_REQUIRED') or
            p.get('financial_fact_truth_certified') is not False):
            raise InvalidInput('V36_PARENT_V35_CASE_HASH_LINEAGE_DRIFT')
        by_case[cid]=p
    if set(by_case)!=set(TARGETS):
        raise InvalidInput('V36_PARENT_THIRTEEN_CASE_SET_MISMATCH')
    reviewed=set(); rows=[]
    for r in host_rows:
        required={'video_id','case_sha256','hinge_cue','cue_sha256',
                  'context_first','context_last','context_sha256',
                  'parent_child_digest','master_claim_id','master_row_sha256',
                  'meaning_kind','disposition','prior_relation','reason',
                  'current_rule_urls','last_checked','independent_audio_checked',
                  'current_broker_contract_verified','financial_fact_certified',
                  'master_auto_merge','personal_tax_or_trade_approval'}
        if type(r) is not dict or set(r)!=required:
            raise InvalidInput('V36_HOST_REVIEW_SCHEMA_INVALID')
        cid=r['case_sha256']
        if cid not in by_case or cid in reviewed:
            raise InvalidInput('V36_REVIEW_DUPLICATE_OR_UNKNOWN_CASE')
        reviewed.add(cid)
        t=TARGETS[cid];k=(t['video_id'],t['hinge_cue']); start,end,kind=_CONTEXT[k]
        if (r['video_id']!=k[0] or r['hinge_cue']!=k[1] or
            r['cue_sha256']!=_CUE_PINS[k] or r['context_first']!=start or
            r['context_last']!=end or r['meaning_kind']!=kind or
            r['master_claim_id']!=t['master_claim_id'] or
            r['master_row_sha256']!=t['master_row_sha256'] or
            r['parent_child_digest']!=by_case[cid]['child_candidate_digest']):
            raise InvalidInput('V36_ORIGINAL_OR_PRIOR_MEANING_LINEAGE_DRIFT')
        cues=sources[k[0]]
        if len(cues)<end or sha256(cues[k[1]-1].text.encode())!=r['cue_sha256']:
            raise InvalidInput('V36_ORIGINAL_CUE_SHA_DRIFT')
        text=' '.join(cues[x-1].text for x in range(start,end+1))
        if r['context_sha256']!=sha256(text.encode()):
            raise InvalidInput('V36_BOUNDING_CONTEXT_HASH_DRIFT')
        if any(marker not in text for marker in _MARKERS[kind]):
            raise InvalidInput('V36_DISTINCTIVE_CONTEXT_NOT_IN_ORIGINAL')
        if (r['last_checked']!='2026-11-11' or type(r['reason']) is not str or
            not 55<=len(r['reason'])<=1600 or
            any(r[x] is not False for x in ('independent_audio_checked',
                 'current_broker_contract_verified','financial_fact_certified',
                 'master_auto_merge','personal_tax_or_trade_approval'))):
            raise InvalidInput('V36_UNSUPPORTED_FACT_OR_INDEPENDENCE_APPROVAL')
        urls=r['current_rule_urls']
        if type(urls) is not list or len(urls)>4 or any(type(u) is not str or
            urlsplit(u).scheme!='https' or
            not any(urlsplit(u).hostname==host or
                    (urlsplit(u).hostname or '').endswith('.'+host)
                    for host in _EVIDENCE_DOMAIN) for u in urls):
            raise InvalidInput('V36_PRIMARY_EVIDENCE_URL_SCOPE_INVALID')
        if kind in _SCOPE_KINDS:
            if (r['disposition']!='SCOPED_HISTORICAL_EDUCATION_ONLY' or
                r['prior_relation']!='TOPICALLY_RELATED_NOT_MASTER_EQUIVALENCE'):
                raise InvalidInput('V36_FINANCIAL_SCOPE_MUST_REMAIN_NON_EQUIVALENT')
            if kind in ('PENSION_TAX_OPTION','PENSION_NONCREDIT_BASIS',
                        'WITHDRAWAL_DIVIDEND_EXAMPLE') and not any('nts.go.kr' in u for u in urls):
                raise InvalidInput('V36_TAX_REGULATION_PRIMARY_EVIDENCE_REQUIRED')
            if kind=='CMA_HISTORICAL_RATE' and not any('kbsec.com' in u for u in urls):
                raise InvalidInput('V36_CMA_PRODUCT_PRIMARY_TYPE_EVIDENCE_REQUIRED')
        elif kind in _PRIOR_KINDS:
            if (r['disposition']!='DISTINCT_PRIOR_RELATION_REVIEWED_CHAT_ONLY' or
                r['prior_relation'] not in _PRIOR_RELATIONS):
                raise InvalidInput('V36_PRIOR_NON_EQUIVALENCE_NOT_ESTABLISHED')
        else:
            raise InvalidInput('V36_UNKNOWN_MEANING_KIND')
        # Do not publish original Korean clauses / reviewer reasoning.
        rows.append({'case_sha256':cid,'video_id':k[0],'cue_index':k[1],
                     'source_cue_sha256':r['cue_sha256'],
                     'bounded_source_sha256':r['context_sha256'],
                     'parent_child_digest':r['parent_child_digest'],
                     'master_claim_id':r['master_claim_id'],
                     'master_row_sha256':r['master_row_sha256'],
                     'meaning_kind':kind,
                     'host_semantic_disposition':r['disposition'],
                     'prior_relation':r['prior_relation'],
                     'host_reason_sha256':sha256(r['reason'].encode()),
                     'primary_source_urls':urls,
                     'original_audio_or_current_product_terms_unverified':kind in (
                         'PENSION_NONCREDIT_BASIS','WITHDRAWAL_DIVIDEND_EXAMPLE',
                         'CMA_SETTLEMENT_ANECDOTE','CMA_HISTORICAL_RATE'),
                     'external_expert_financial_fact_certified':False,
                     'independent_blind_gold':False,
                     'master_knowledge_auto_merge':False})
    if reviewed!=set(TARGETS):
        raise InvalidInput('V36_NOT_ALL_THIRTEEN_ADJUDICATED')
    rows.sort(key=lambda x:x['case_sha256'])
    evidence_open=sum(x['original_audio_or_current_product_terms_unverified'] for x in rows)
    if evidence_open!=8:
        raise InvalidInput('V36_REVIEWED_BUT_UNVERIFIED_EVIDENCE_COUNT_DRIFT')
    report={
      'schema':'IRE_V6_V36_THIRTEEN_OPEN_CASES_CHAT_SCOPE_AND_PRIOR_REVIEW_HASH_ONLY',
      'current_as_of':current_as_of,
      'original_video_count':len(sources),
      'exact_v35_previous_open_cases':len(TARGETS),
      'exact_prior_open_cases_source_finance':9,
      'exact_prior_open_cases_master_relation':4,
      'revisited_actual_original_cue_contexts':len(_CONTEXT),
      'host_scope_decisions_recorded':len(rows),
      'semantic_scope_dispositions_remaining_unreviewed':0,
      'verified_financial_truth_decisions':0,
      'source_audio_or_current_product_terms_still_unverified':evidence_open,
      'independent_financial_accuracy_certified':False,
      'independent_gold_precision_recall_measured':False,
      'issuer_signed_legal_body_authenticated':False,
      'source_wide_1603_claims_atomized':False,
      'all_130_full_video_windows_researched':False,
      'all_791_researched':False,
      'master116_merge_approved':False,
      'personal_tax_or_trade_approval':False,'p0_go':False,
      'parent_v35_receipt_sha256':parent_receipt_sha256,
      'protected_master116_root_digest':master116_rows_digest,
      'reviewed_cases':rows,
      'status':'V36_ALL_13_SCOPE_CLASSIFIED_BUT_8_EXTERNAL_AUDIO_OR_PROVIDER_EVIDENCE_OPEN_P0_NO_GO',
    }
    report['receipt_sha256']=json_digest(report)
    return report
