"""V100 read-only knowledge crosswalk quarantine. No writes to Master116/P4/P3.

An existing topic or P4 educational node may be *related*, but is not an
independently evidenced financial fact or semantic entailment of new private SRT.
"""
from __future__ import annotations
from v98_hybrid_source_guard import require,digest
import re

MASTER_BLOB_SHA='0ac2fbb2100d68a95cabebdb1b10dfe77fc3f5b4'
P4_BLOB_SHA='bfb446ffb1dd40caa1ed03088d088c9a1ba7490f'
MASTER_PATH='ire/v5/legacy_consolidation/master_index_20261105.json'
P4_PATH='ire/v5/advisory_knowledge/p4_integrated_scoped_education22_20261106.json'
ALLOW_NODES={'EDU-DCA-DIVERSIFICATION','EDU-GENERAL-DCA-ARITH-01'}
EXPECTED_REVIEWED=20
ACTUAL_P4_NODE_IDS=(
 'EDU-DCA-DIVERSIFICATION','EDU-ETF-NAV-TRACKING',
 'EDU-ETF-TOTAL-COST-DECISION','EDU-GENERAL-DCA-ARITH-01',
 'EDU-IRP-LIFECYCLE','EDU-KR-ISA-LIMIT-2026-01',
 'EDU-KR-ISA-TO-PENSION-2026-01','EDU-KR-PENSION-55-5',
 'EDU-KR-PENSION-CREDIT-600-900','EDU-KR-PENSION-IN-KIND-TRANSFER',
 'EDU-KR-PRIVATE-PENSION-1500-2026-01','EDU-PENSION-DEFERRED-TAX',
 'EDU-RETIREMENT-ACCOUNT-AUDIT','V5-001-40-DEEMED_PENSION_WITHDRAWAL_ORDER',
 'V5-001-40-DIVIDEND_2000_VS_PENSION_1500','V5-001-40-ISA_MATURITY_TO_PENSION',
 'V5-001-40-NPS_CPI_VS_INVESTMENT','V5-001-40-NPS_DEFERRAL',
 'V5-001-40-NPS_PAYMENT','V5-001-40-NPS_RETROACTIVE_ELIGIBILITY',
 'V5-001-40-PENSION_BASIS_PROVENANCE','V5-001-40-PRIVATE_PENSION_1500_TAX')

def readonly_preview(entries,master,p4,*,source_sha,approved_identity_before,approved_identity_after):
    """The caller reads pinned *actual* immutable Git blobs and extracts metadata.

    master/p4 contain IDs and status, but the preview emits only hashed IDs and
    numbers. Quarantined candidate links cannot edit the original knowledge.
    """
    require(master.get('git_blob_sha')==MASTER_BLOB_SHA,'MASTER_SHA')
    require(p4.get('git_blob_sha')==P4_BLOB_SHA,'P4_SHA')
    require(master.get('path')==MASTER_PATH and p4.get('path')==P4_PATH,'BASELINE_PATH')
    ids=master.get('claim_ids'); nodes=p4.get('nodes')
    require(type(ids) is list and ids==[f'GOMHEE-C{i:02d}' for i in range(1,117)],'MASTER116')
    require(type(nodes) is list and len(nodes)==22,'P4_NODES22')
    nodeids=[]
    for n in nodes:
        require(type(n) is dict and type(n.get('knowledge_id')) is str,'NODE_ID')
        require(n.get('status') in {'EXISTING_PROVISIONAL_EDUCATION_NOT_CURRENT_LAW_APPROVAL',
               'SCOPED_EDUCATION_OFFLINE_OFFICIAL_EXTRACT_REPLAYED'},'NODE_STATUS')
        nodeids.append(n['knowledge_id'])
    require(nodeids==list(ACTUAL_P4_NODE_IDS),'PINNED_P4_NODE_IDS')
    require(ALLOW_NODES<=set(nodeids),'ALLOW_NODES_MISSING')
    require(master.get('fact_approvals_from_metadata_index')==0,'MASTER_FALSE_APPROVAL')
    require(p4.get('P3_formal_claim_approvals')==0 and p4.get('B04_formal_master_merges')==0,'P4_FALSE_APPROVAL')
    require(type(entries) is list and len(entries)==EXPECTED_REVIEWED,'ISSUES20')
    expected_identity=digest([MASTER_BLOB_SHA,P4_BLOB_SHA,ids,nodeids])
    require(approved_identity_before==expected_identity and approved_identity_after==expected_identity,'APPROVED_MUTATED')
    require(type(source_sha) is str and re.fullmatch(r'[0-9a-f]{64}',source_sha) is not None,'SOURCE_PIN')
    seen=set();sha_rows=[];links=0;unlinked=0
    for row in entries:
        require(type(row) is dict,'ROW_TYPE')
        key=(row.get('video_id'),row.get('window_id'),row.get('first_cue'),row.get('last_cue'))
        require(key not in seen,'DUP_ISSUE');seen.add(key)
        require(type(key[2]) is int and type(key[3]) is int and key[2]<=key[3],'CUE_RANGE')
        require(type(row.get('source_span_sha256')) is str and len(row['source_span_sha256'])==64,'ISSUE_SOURCE')
        candidates=row.get('related_education_ids')
        require(type(candidates) is list and len(candidates)==len(set(candidates)),'CANDIDATE_TYPE')
        require(set(candidates)<=ALLOW_NODES,'UNKNOWN_OR_UNSAFE_NODE')
        require(row.get('relation')=='RELATED_CANDIDATE_NOT_EQUIVALENT' if candidates else row.get('relation')=='UNRESOLVED_NO_MATCH','RELATION')
        for prop in ('fact_approved','auto_merge','personal_advice_approved','independent_gold',
                     'source_semantics_certified','legal_current_approved'):
            require(row.get(prop) is False,'FALSE_PROMOTION_'+prop)
        if candidates:links+=1
        else:unlinked+=1
        sha_rows.append([*key,row['source_span_sha256'],sorted(candidates),row['relation']])
    require(links+unlinked==20,'CENSUS')
    return {'schema':'V100_READONLY_MASTER116_P4_CROSSWALK_NOT_APPROVAL_V1',
        'original_source_archive_sha256':source_sha,
        'master_blob_sha':MASTER_BLOB_SHA,'p4_blob_sha':P4_BLOB_SHA,
        'approved_knowledge_identity_before':approved_identity_before,
        'approved_knowledge_identity_after':approved_identity_after,
        'legacy_claims_read_only':116,'p4_education_nodes_read_only':22,
        'private_issue_spans_provisional':20,'related_education_candidates':links,
        'unresolved_no_match':unlinked,'candidate_source_receipt_sha256':digest(sorted(sha_rows)),
        'formal_knowledge_merges':0,'new_facts_approved':0,
        'new_p3_advice_approvals':0,'personalized_advice_approved':False,
        'historical_v75_identity_reconciled':False,'independent_gold':False,
        'semantic_equivalence_certified':False,'p0_go':False}