"""Real byte structure, synthetic monetary expressions only; no fake gold."""
from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import sha256, json_digest, canonical
from ire.v6.errors import InvalidInput, DomainConflict
from ire.v6.source import verify_source
from ire.v6.store import TransactionStore
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest, VIDEO


class HostAtomExchangeTests(unittest.TestCase):
    def setUp(self):
        self.raw=make_srt([
            "연금저축의 예상 수익은 10%입니다.",
            "하지만 실제로는 8%일 수 있습니다.",
            "다만 세금 조건은 소득에 따라 달라집니다.",
            "일반 교육 안내입니다.",
        ])
        self.manifest=make_manifest(self.raw,cut=2)
        self.source=verify_source(self.raw,self.manifest,
            expected_source_sha256=sha256(self.raw),
            expected_manifest_sha256=json_digest(self.manifest))
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=TransactionStore(Path(self.tmp.name)/"private"/"host.db")
        self.store.create_scope(scope_id="host_scope",video_id=VIDEO,
            source_sha256=sha256(self.raw),
            manifest_sha256=json_digest(self.manifest),command_id="genesis")
        self.exchange=self.sample()

    def sample(self):
        source=self.source
        def candidate(idx,cid):
            return {"cue_index":idx,"cue_text_sha256":sha256(source.cues[idx-1].text.encode()),
                    "disposition":"CANDIDATES","claim_ids":[cid],
                    "numeric_tokens":NUMBER.findall(source.cues[idx-1].text),"note":""}
        last={"cue_index":4,"cue_text_sha256":sha256(source.cues[3].text.encode()),
              "disposition":"NO_ATOM","claim_ids":[],
              "numeric_tokens":[],"note":"교육 안내만 포함"}
        def atom(cid,idx,proposition,stance,context,conditions,number):
            return {"claim_id":cid,"owner_window_id":source.owner(idx),
                    "proposition":proposition,"kind":"FACT","stance":stance,
                    "speaker":"NARRATOR",
                    "source_refs":[{"cue_index":idx,"quote":source.cues[idx-1].text}],
                    "context_cue_indices":context,
                    "condition_cue_indices":conditions,
                    "exception_cue_indices":[],
                    "numeric_references":[{"cue_index":idx,"token":number}] if number else [],
                    "as_of":None}
        return {"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
            "video_id":VIDEO,"source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "cue_dispositions":[candidate(1,"C00001"),candidate(2,"C00002"),
                               candidate(3,"C00003"),last],
            "atoms":[
                atom("C00001",1,"예상 10% 수익률입니다.","AFFIRMED",[1],[], "10%"),
                atom("C00002",2,"실제는 8%일 수 있습니다.","CORRECTED",[1,2],[], "8%"),
                atom("C00003",3,"세금 조건은 소득에 따라 달라집니다.","CONDITIONAL",
                     [2,3],[3],None),
            ]}

    def attest(self):
        self.store.attest_source(scope_id="host_scope",command_id="source",
            expected_head=self.store.snapshot("host_scope")["ledger_head_sha256"],
            raw=self.raw,manifest=self.manifest)
        inv={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":self.source.cue_census_sha256}]}
        data=canonical(inv)
        sha=sha256(data)
        self.store.attest_owner_inventory(scope_id="host_scope",command_id="owner",
            expected_head=self.store.snapshot("host_scope")["ledger_head_sha256"],
            raw=self.raw,manifest=self.manifest,inventory_bytes=data,
            expected_inventory_sha256=sha)
        return data,sha

    def test_all_cues_number_context_and_stance_bound_but_not_semantic_gold(self):
        result=audit_host_atomic_exchange(self.source,self.exchange)
        self.assertEqual(result["original_scoped_cues_enumerated"],4)
        self.assertEqual(result["proposed_atomic_claims"],3)
        self.assertEqual(result["cues_with_qualifiers"],2)
        self.assertEqual(result["unresolved_cues"],0)
        self.assertTrue(result["all_numeric_cue_tokens_reconciled"])
        self.assertFalse(result["semantic_claims_independently_verified"])
        self.assertFalse(result["all_atomic_claims_exhausted"])
        self.assertFalse(result["research_complete"])

    def test_missing_duplicated_or_out_of_order_cue_is_rejected(self):
        for mutation in ("missing","duplicate","unordered"):
            e=copy.deepcopy(self.exchange)
            if mutation=="missing":e["cue_dispositions"].pop()
            elif mutation=="duplicate":e["cue_dispositions"][1]["cue_index"]=1
            else:e["cue_dispositions"][0],e["cue_dispositions"][1]=(
                e["cue_dispositions"][1],e["cue_dispositions"][0])
            with self.subTest(mutation=mutation),self.assertRaises(InvalidInput):
                audit_host_atomic_exchange(self.source,e)

    def test_numeric_omission_wrong_unit_or_forged_anchor_rejected(self):
        changes=[
            lambda e:e["cue_dispositions"][0].update(numeric_tokens=[]),
            lambda e:e["atoms"][0]["numeric_references"][0].update(token="10원"),
            lambda e:e["atoms"][0]["source_refs"][0].update(quote="가짜 주장"),
            lambda e:e["atoms"][0].update(proposition="예상 15%입니다."),
        ]
        for change in changes:
            e=copy.deepcopy(self.exchange);change(e)
            with self.assertRaises(InvalidInput):
                audit_host_atomic_exchange(self.source,e)

    def test_negated_qualifier_cue_cannot_self_label_unconditional(self):
        e=copy.deepcopy(self.exchange)
        e["atoms"][1]["stance"]="AFFIRMED"
        with self.assertRaisesRegex(InvalidInput,"QUALIFIED_ASSERTION"):
            audit_host_atomic_exchange(self.source,e)

    def test_cross_cue_context_and_conditions_are_mandatory(self):
        e=copy.deepcopy(self.exchange)
        e["atoms"][2]["context_cue_indices"]=[2]
        with self.assertRaisesRegex(InvalidInput,"CONDITION_OR_CONTEXT"):
            audit_host_atomic_exchange(self.source,e)

    def test_no_atom_with_financial_keywords_is_marked_not_auto_clean(self):
        e=copy.deepcopy(self.exchange)
        e["cue_dispositions"][0]["disposition"]="NO_ATOM"
        e["cue_dispositions"][0]["claim_ids"]=[]
        e["cue_dispositions"][0]["note"]="유의미한 주장이 없다고 모델이 표시함"
        e["atoms"].pop(0)
        result=audit_host_atomic_exchange(self.source,e)
        self.assertGreaterEqual(result["suspicious_no_atom_cues"],1)
        self.assertFalse(result["all_atomic_claims_exhausted"])

    def test_operator_pin_and_same_snapshot_binds_private_source(self):
        data,sha=self.attest()
        result=self.store.snapshot_with_atomic_exchange(
            scope_id="host_scope",raw=self.raw,manifest=self.manifest,
            inventory_bytes=data,expected_inventory_sha256=sha,
            exchange=self.exchange)
        self.assertEqual(result["atomic_audit"]["proposed_atomic_claims"],3)
        self.assertFalse(result["p0_go"])
        self.assertFalse(result["research_complete"])
        self.assertFalse(result["independent_semantic_recall_verified"])
        with self.assertRaises(InvalidInput):
            self.store.snapshot_with_atomic_exchange(
                scope_id="host_scope",raw=self.raw+b"x",manifest=self.manifest,
                inventory_bytes=data,expected_inventory_sha256=sha,
                exchange=self.exchange)

    def test_unattested_store_cannot_claim_host_result(self):
        inv={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":self.source.cue_census_sha256}]}
        data=canonical(inv)
        with self.assertRaises(DomainConflict):
            self.store.snapshot_with_atomic_exchange(
                scope_id="host_scope",raw=self.raw,manifest=self.manifest,
                inventory_bytes=data,expected_inventory_sha256=sha256(data),
                exchange=self.exchange)


if __name__=="__main__":
    unittest.main()
