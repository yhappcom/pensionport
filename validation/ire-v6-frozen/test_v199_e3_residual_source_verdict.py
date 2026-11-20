"""Synthetic adversarial testing for V199. No private SRT or case judgments here."""
import copy, os, sqlite3, unittest
from pathlib import Path
import test_v197_e3_repaired_source_projection as fixture
from v197_e3_repaired_source_projection import make_risk_register
from v198_e3_final_correction_adjudication import E3CorrectionAdjudication, VERDICT as V198_VERDICT
from ire.v6.errors import InvalidInput
from v196_e3_second_review_repair import _sha
from v199_e3_residual_source_verdict import (
    E3SixResidualVerdicts, ROW, RULES, build_84_contextual_risk_view, PUBLIC_WEB_CONTEXT,
    SPOT_CHECKS, SPOT_SCHEMA, validate_web_text_spot_checks,
)

class TestV199SixResiduals(unittest.TestCase):
    def setUp(self):
        # Synthetic replay shaped like the actual 16 correction serials; no owner
        # data or test classes from other suites are imported into discovery.
        self.old=fixture.TestV197RepairedView('test_01_realistic_full_120_census_and_84_risk_holds')
        self.old.setUp();self.addCleanup(self.old.doCleanups)
        kinds={7:('PRESERVE_QUARANTINE_SOURCE_REPHRASE','Speaker-only rephrasing.'),
               20:('PARENT_RELATION_REVIEW_REQUIRED',None),
               82:('PARENT_RELATION_REVIEW_REQUIRED',None),
               100:('REMOVE_NONATOMIC_PROPOSED',None),
               114:('REMOVE_NONATOMIC_PROPOSED',None)}
        for s in [12,14,15,28,31,48,68,71,99,109,112]:
            kinds[s]=('SOURCE_REWRITE_PROPOSED','A candidate source-only rephrase of cue '+str(s))
        self.old.amends.clear()
        for s,(kind,ptext) in kinds.items():
            self.old._patch(s,kind,ptext,19 if s==20 else 81 if s==82 else None)
            a=self.old.amends[s]
            a.update({'source_quote_cue_index':s,'source_quote':self.old.review.cues[s],
                'rationale':'Review this original speaker text without certifying external financial truth.',
                'remaining_evidence_task':'Official issuer product terms and the actual audio must be checked first.'})
        for s in [100,114]:
            self.old.review.judgments[s]['e3_disposition']='HOLD_REMOVE_FALSE_ATOM_CANDIDATE'
        for s in [100,114]:
            self.old.amends[s]['prior_second_judgment_sha256']=_sha(self.old.review.judgments[s])
        self.review=self.old.review
        # Preserve the 84-total synthetic risk census while making the 12 spot
        # serials reflect the real V199 risk-candidate distribution.
        for serial,risk_flag in [(78,False),(80,False),(83,False),(52,True),(112,True),(113,True)]:
            self.review.atoms[serial-1]['high_risk']=risk_flag
            self.review.judgments[serial]['first_turn_high_risk_flag']=risk_flag
        self.old.amends[112]['first_claim_sha256']=_sha(self.review.atoms[111])
        self.old.amends[112]['prior_second_judgment_sha256']=_sha(self.review.judgments[112])
        self.old.risk=make_risk_register(self.review,self.review.judgments)
        self.v198=E3CorrectionAdjudication(self.review,self.old.repair,
             Path(self.old.tmp.name)/'v198_residual_synthetic.sqlite',
             expected_repair_head=fixture.REPAIR,risk_register=self.old.risk,create=True)
        with self.old.repair._db() as db:_,amends,_=self.old.repair._audit(db)
        old_judgments=self.review.judgments
        answers=[]
        for s in sorted(amends):
            a=amends[s]
            kind=a['repair_kind']
            decision=('HOLD_PARENT_EQUIVALENCE' if s in (20,82) else
                      'REJECT_UNFAITHFUL_REWRITE' if s in (28,112) else
                      'HOLD_AUDIO_OR_CONTEXT' if s in (31,68) else
                      'ACCEPT_NONATOMIC_EXCLUSION_FROM_PROVISIONAL_VIEW' if s in (100,114) else
                      'ACCEPT_SOURCE_FORM_ONLY')
            answers.append({'schema':V198_VERDICT,'serial':s,
              'first_claim_sha256':_sha(self.review.atoms[s-1]),
              'second_judgment_sha256':_sha(old_judgments[s]),
              'proposal_sha256':_sha(a),
              'source_quote_cue_index':s,'source_quote':self.review.cues[s],
              'decision':decision,
              'accepted_source_form_only':decision=='ACCEPT_SOURCE_FORM_ONLY',
              'review_rationale':'This is a synthetic source statement, not an approved financial fact or advice.',
              'next_evidence_task':'Independent terms and any audio ambiguities require separate verification.',
              'old_quarantine_retained':True,'first_research_unchanged':True,
              'second_review_unchanged':True,'repair_proposal_unchanged':True,
              'financial_fact_approved':False,'independent_gold':False,
              'e3_approved':False,'e4_approved':False,'e5_published':False})
        self.v198.submit(self.v198.packet(sorted(amends)),answers)
        self.head=self.v198.status()['adjudication_head_sha256']
        self.db=Path(self.old.tmp.name)/'v199.sqlite'
        self.v199=E3SixResidualVerdicts(self.v198,self.db,
                               expected_v198_head=self.head,create=True)
    def row(self,s):
        a=self.v198.review.atoms[s-1];ix=a['cue_index']
        indices=[ix,ix+1] if s in (28,112) else [ix]
        return {'schema':ROW,'serial':s,'original_claim_sha256':_sha(a),
          'v198_verdict_sha256':_sha(self.v198.decisions()[s]),
          'conclusion':RULES[s][0], 'parent_serial':RULES[s][1],
          'source_clauses':[{'cue_index':i,'source_quote':self.v198.review.cues[i],
             'source_paraphrase':'Only records what was spoken at this original cue, not truth.'}
              for i in indices],
          'official_context_refs':['KOFIA_CMA_GUIDELINE'],
          'review_rationale':'The speaker said the source claim, but the risk and context are still not verified independently.',
          'next_evidence_task':'Obtain original audio and product-specific primary terms before allowing any investment use.',
          'audio_verified':False,'raw_issuer_bytes_verified':False,
          'financial_fact_verified':False,'first_journal_unchanged':True,
          'second_journal_unchanged':True,'v198_journal_unchanged':True,
          'risk_84_blocked':True,'quarantines_28_preserved':True,
          'independent_gold':False,'e3_approved':False,'e4_approved':False,
          'e5_published':False}
    def submit(self,s):
        serials=s if type(s)==list else [s]
        return self.v199.submit(self.v199.prepare(serials),[self.row(i) for i in serials])
    def full(self):
        for batch in [[20,28,31],[68,82,112]]:self.submit(batch)
    def test_01_full_six_holds(self):
        self.full();x=self.v199.status()
        self.assertEqual((x['reviewed'],x['events'],x['remaining']),(6,2,0))
        self.assertFalse(x['e3_approved'])
    def test_02_initially_not_certified(self):
        self.assertEqual(self.v199.status()['remaining'],6)
        self.assertIsNone(self.v199.status()['gold_precision'])
    def test_03_full_risk_web_context_is_not_finance_evidence(self):
        self.full();x=build_84_contextual_risk_view(self.v199)
        self.assertEqual((len(x['risk_records']),x['quarantines']),(84,28))
        self.assertTrue(all(r['financial_use_blocked'] for r in x['risk_records']))
        self.assertTrue(all(r['raw_official_document_bytes_sha256'] is None for r in x['risk_records']))
    def test_04_cannot_build_evidence_view_with_five_cases(self):
        self.submit([20,28,31,68,82])
        with self.assertRaisesRegex(InvalidInput,'SIX_REVIEWS_MUST_BE_COMPLETE'):
            build_84_contextual_risk_view(self.v199)
    def test_05_same_case_rejected(self):
        self.submit(20)
        with self.assertRaisesRegex(InvalidInput,'ALREADY_REVIEWED'):self.submit(20)
    def test_06_wrong_first_hash(self):
        r=self.row(20);r['original_claim_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'WRONG_ORIGINAL'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_07_wrong_v198_verdict_hash(self):
        r=self.row(20);r['v198_verdict_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'WRONG_ORIGINAL'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_08_conclusion_forgery(self):
        r=self.row(20);r['conclusion']=RULES[82][0]
        with self.assertRaisesRegex(InvalidInput,'WRONG_ORIGINAL'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_09_wrong_parent(self):
        r=self.row(20);r['parent_serial']=30
        with self.assertRaisesRegex(InvalidInput,'WRONG_ORIGINAL'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_10_source_quote_invented(self):
        r=self.row(31);r['source_clauses'][0]['source_quote']='Unconditional principal guarantee'
        with self.assertRaisesRegex(InvalidInput,'FABRICATED_OR_NONLOCAL'):
            self.v199.submit(self.v199.prepare([31]),[r])
    def test_11_source_nonlocal(self):
        r=self.row(31);r['source_clauses'][0]['cue_index']=2
        with self.assertRaisesRegex(InvalidInput,'FABRICATED_OR_NONLOCAL'):
            self.v199.submit(self.v199.prepare([31]),[r])
    def test_12_two_independent_clauses_required_at_28(self):
        r=self.row(28);r['source_clauses'].pop()
        with self.assertRaisesRegex(InvalidInput,'MUST_PRESERVE_BOTH'):
            self.v199.submit(self.v199.prepare([28]),[r])
    def test_13_two_independent_clauses_required_at_112(self):
        r=self.row(112);r['source_clauses'].pop()
        with self.assertRaisesRegex(InvalidInput,'MUST_PRESERVE_BOTH'):
            self.v199.submit(self.v199.prepare([112]),[r])
    def test_14_fake_issuer_link_cannot_be_supplied(self):
        r=self.row(20);r['official_context_refs']=['EVIL_FINANCE']
        with self.assertRaisesRegex(InvalidInput,'UNTRUSTED_OR_FORGED'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_15_no_unverified_issuer_raw_byte_claim(self):
        r=self.row(20);r['raw_issuer_bytes_verified']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_16_no_fake_audio_proof(self):
        r=self.row(31);r['audio_verified']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.v199.submit(self.v199.prepare([31]),[r])
    def test_17_no_financial_truth_pass(self):
        r=self.row(82);r['financial_fact_verified']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.v199.submit(self.v199.prepare([82]),[r])
    def test_18_no_e3_e4_e5_forgery(self):
        for field in ['e3_approved','e4_approved','e5_published','independent_gold']:
            with self.subTest(field=field):
                r=self.row(20);r[field]=True
                with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
                    self.v199.submit(self.v199.prepare([20]),[r])
    def test_19_forged_self_hashed_packet(self):
        p=self.v199.prepare([20]);p['items'][0]['original_proposition']='fiction'
        p['packet_sha256']=_sha({k:v for k,v in p.items() if k!='packet_sha256'})
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_PACKET'):
            self.v199.submit(p,[self.row(20)])
    def test_20_private_db_permission(self):
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'EXISTING_PRIVATE_DB'):
            E3SixResidualVerdicts(self.v198,self.db,expected_v198_head=self.head)
    def test_21_event_tamper(self):
        self.submit(20)
        with sqlite3.connect(self.db) as con:con.execute("UPDATE events SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'EVENT_HASH_CHAIN_TAMPER'):
            self.v199.status()
    def test_22_verdict_tamper(self):
        self.submit(20)
        with sqlite3.connect(self.db) as con:con.execute("UPDATE decisions SET verdict_sha='x'")
        with self.assertRaisesRegex(InvalidInput,'VERDICT_TABLE_HASH_TAMPER'):
            self.v199.status()
    def test_23_reopen_with_same_pinned_head(self):
        self.full()
        reload=E3SixResidualVerdicts(self.v198,self.db,expected_v198_head=self.head)
        self.assertEqual(self.v199.status(),reload.status())
    def test_24_stale_v198_head(self):
        with self.assertRaisesRegex(InvalidInput,'V198_FINAL_16_VERDICTS_NOT_PINNED'):
            E3SixResidualVerdicts(self.v198,Path(self.old.tmp.name)/'another.sqlite',
                                   expected_v198_head='0'*64,create=True)
    def test_25_missing_risk_84(self):
        self.v198.risk_register['risk_records'].pop()
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS|PRIOR_JOURNAL'):
            self.v199.status()
    def test_26_private_context_registry_not_attested_raw(self):
        self.assertTrue(all(x['url'].startswith('https://') for x in PUBLIC_WEB_CONTEXT.values()))
        self.assertFalse(self.v199.config['official_issuer_raw_bytes_certified'])
    def test_27_extra_keys_in_verdict_forbidden(self):
        r=self.row(20);r['financially_safe']=True
        with self.assertRaisesRegex(InvalidInput,'VERDICT_SCHEMA_INVALID'):
            self.v199.submit(self.v199.prepare([20]),[r])
    def test_28_duplicate_source_clauses_forbidden(self):
        r=self.row(28);r['source_clauses'][1]=copy.deepcopy(r['source_clauses'][0])
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_OR_DISORDERED'):
            self.v199.submit(self.v199.prepare([28]),[r])

    def synthetic_spots(self):
        self.full(); cases=[]
        for s in SPOT_CHECKS:
            atom=self.review.atoms[s-1];ix=atom['cue_index']
            cases.append({'serial':s,'claim_sha256':_sha(atom),
                'source_cue_index':ix,'source_quote':self.review.cues[ix],
                'web_text_refs':['KOFIA_CMA_GUIDELINE'],
                'finding':'INSUFFICIENT_ISSUER_EVIDENCE',
                'analysis':'The synthetic claim cannot be accepted as financially true from an unrelated public web page.',
                'issuer_scope_limit':'Specific financial product terms and dates have not been verified in this test.',
                'official_raw_bytes_sha256':None,
                'product_terms_individually_verified':False,'financial_use_blocked':True,
                'e3_approved':False,'e4_approved':False,'e5_published':False})
        return {'schema':SPOT_SCHEMA,'source_sha256':self.v199.config['source_sha256'],
            'v199_head_sha256':self.v199.status()['v199_head_sha256'],
            'cases':cases,'issuer_raw_sha256_certified':False,
            'financial_truth_certified':False,'e3_approved':False,
            'e4_approved':False,'e5_published':False}
    def test_29_twelve_source_bound_high_risk_spots(self):
        result=validate_web_text_spot_checks(self.v199,self.synthetic_spots())
        self.assertEqual((result['sample_size'],result['risk_cases_not_covered_by_spot_check']),(12,72))
        self.assertFalse(result['financial_truth_certified'])
    def test_30_spot_check_forged_issuer_source_blocked(self):
        x=self.synthetic_spots();x['cases'][0]['web_text_refs']=['UNTRUSTED_SITE']
        with self.assertRaisesRegex(InvalidInput,'SPOT_UNREGISTERED_ISSUER_SOURCE'):
            validate_web_text_spot_checks(self.v199,x)
    def test_31_spot_check_missing_risk_case_blocked(self):
        x=self.synthetic_spots();x['cases'].pop()
        with self.assertRaisesRegex(InvalidInput,'TWELVE_REAL_HIGH_RISK_SAMPLES_REQUIRED'):
            validate_web_text_spot_checks(self.v199,x)
    def test_32_spot_check_financial_certificate_forgery_blocked(self):
        x=self.synthetic_spots();x['cases'][0]['product_terms_individually_verified']=True
        with self.assertRaisesRegex(InvalidInput,'SPOT_ILLEGAL_FINANCIAL_CERTIFICATION'):
            validate_web_text_spot_checks(self.v199,x)

if __name__=='__main__':unittest.main()