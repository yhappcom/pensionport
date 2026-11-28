function runChecks(sl,shadow,active,archive,pins,p,a){
 const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y),copy=x=>JSON.parse(JSON.stringify(x)),key=(x,y)=>[x,y].sort().join("|"),results={};
 function t(n,fn){try{results[n]=!!fn()}catch(e){results[n]=false}}
 const c=p.cases[0],x=a.results[0],pre=sl.prepare(shadow,p.policy.profiles,c),rec=x.receipt,hold=(f,msg)=>{const y=f();return y.status==="HOLD"&&y.reason===msg},change=(fn)=>{let z=copy(rec);fn(z);return z};
 t("all_25_active",()=>shadow.cards.size===25);t("all_300_archived",()=>shadow.archive.size===300);t("120_explicit_preserved",()=>shadow.explicit.length===120);
 const six=[["T003-01","T003-04"],["T003-03","T003-04"],["T002-05","T003-05"],["T001-01","T004-01"],["T001-07","T004-01"],["T001-04","T004-05"]];
 t("all_six_prior_misses_preserved",()=>six.every(([a,b])=>sl.relationState(shadow,a,b)==="COMPLEMENT"));
 t("all_case_preparations_reproduced",()=>p.cases.every((q,i)=>eq(sl.prepare(shadow,p.policy.profiles,q),a.results[i].prepared)));
 t("all_case_finalizations_reproduced",()=>a.results.every(x=>eq(sl.finalize(x.prepared,x.receipt,x.receipt?x.answer:""),x.gate)));
 t("four_conditional_two_hold",()=>a.results.filter(x=>x.gate.status==="CONDITIONAL").length===4&&a.results.filter(x=>x.gate.status==="HOLD").length===2);
 t("all_mandatory_dependencies",()=>a.results.filter(x=>x.prepared.status==="REVIEW_REQUIRED").every(x=>x.prepared.selected.every(id=>shadow.cards.get(id).dependencies.every(dep=>x.prepared.selected.includes(dep)))));
 const attacks=[
 ["missing_obligation",z=>delete z.checks.CASH,"OBLIGATION_COVERAGE"],
 ["missing_required_card",z=>z.checks.CASH.cards.pop(),"OBLIGATION_NOT_RESOLVED"],
 ["unresolved_obligation",z=>z.checks.CASH.status="HOLD","OBLIGATION_NOT_RESOLVED"],
 ["empty_obligation_rationale",z=>z.checks.TAX.note="","OBLIGATION_NOT_RESOLVED"],
 ["missing_bridge",z=>z.bridges.pop(),"BRIDGE_COVERAGE"],
 ["duplicate_bridge",z=>z.bridges[1]=copy(z.bridges[0]),"BRIDGE_COVERAGE"],
 ["wrong_bridge_state",z=>z.bridges[0].state="DISTINCT","BRIDGE_NOT_RESOLVED"],
 ["wrong_snapshot",z=>z.binding.pins.registry="0".repeat(40),"BINDING_MISMATCH"],
 ["different_question",z=>z.binding.question+="?","BINDING_MISMATCH"],
 ["different_date",z=>z.binding.day="2026-11-29","BINDING_MISMATCH"],
 ["different_profile",z=>z.binding.profile="COMPARE","BINDING_MISMATCH"],
 ["missing_source",z=>z.evidence[0].refs.pop(),"EVIDENCE_MISMATCH"],
 ["wrong_source_version",z=>z.evidence[0].version++,"EVIDENCE_MISMATCH"],
 ["personal_trade_blocked",z=>z.personal_trade=true,"UNSUPPORTED_DISPOSITION"],
 ["unconditional_blocked",z=>z.disposition="APPROVED","UNSUPPORTED_DISPOSITION"],
 ["high_risk_open_blocked",z=>z.high_risk_open=true,"SEMANTIC_REVIEW_REQUIRED"],
 ["no_semantic_review_blocked",z=>z.semantic_review="NONE","SEMANTIC_REVIEW_REQUIRED"]];
 for(const [n,fn,msg] of attacks)t(n,()=>hold(()=>sl.finalize(pre,change(fn),x.answer),msg));
 t("answer_modified_after_review",()=>hold(()=>sl.finalize(pre,rec,x.answer+" 추가 매수"),"ANSWER_MISMATCH"));
 t("expired",()=>hold(()=>sl.prepare(shadow,p.policy.profiles,p.cases[4]),"MISSING_OR_EXPIRED"));
 t("unknown_profile",()=>hold(()=>sl.prepare(shadow,p.policy.profiles,p.cases[5]),"UNREGISTERED_PROFILE"));
 const gone=new Map(active);gone.delete("T001-04");const missing=sl.buildShadow(gone,archive.filter(e=>e.a!=="T001-04"&&e.b!=="T001-04"),pins);
 t("missing_dependency",()=>hold(()=>sl.prepare(missing,p.policy.profiles,c),"MISSING_OR_EXPIRED"));
 const unknownKey=pre.bridges[0].pair,unseen=sl.buildShadow(active,archive.filter(z=>key(z.a,z.b)!==unknownKey),pins),up=sl.prepare(unseen,p.policy.profiles,c);
 t("unknown_not_distinct",()=>up.bridges[0].state==="UNREVIEWED"&&sl.relationState(unseen,...unknownKey.split("|"))==="UNREVIEWED");
 const ur=copy(rec);ur.bridges[0].state="UNREVIEWED";ur.bridges[0].fresh_review=false;
 t("unknown_without_fresh_review_blocked",()=>hold(()=>sl.finalize(up,ur,x.answer),"UNKNOWN_RELATION_REVIEW_REQUIRED"));
 const reviewed=copy(ur);reviewed.bridges[0].fresh_review=true;
 t("unknown_with_scoped_review_allowed",()=>sl.finalize(up,reviewed,x.answer).status==="CONDITIONAL");
 t("question_review_does_not_publish_relation",()=>sl.relationState(unseen,...unknownKey.split("|"))==="UNREVIEWED");
 const conflict=sl.buildShadow(active,archive.map(z=>key(z.a,z.b)===unknownKey?{...z,kind:"CONFLICT"}:z),pins);
 t("explicit_conflict_blocks",()=>hold(()=>sl.prepare(conflict,p.policy.profiles,c),"UNRESOLVED_RELATION"));
 const other=archive.find(z=>pre.selected.includes(z.a)&&pre.selected.includes(z.b)&&!pre.bridges.some(b=>b.pair===key(z.a,z.b)));
 const conflictOutside=sl.buildShadow(active,archive.map(z=>key(z.a,z.b)===key(other.a,other.b)?{...z,kind:"CONFLICT"}:z),pins);
 t("known_conflict_outside_bridge_blocks",()=>hold(()=>sl.prepare(conflictOutside,p.policy.profiles,c),"UNRESOLVED_RELATION"));
 const equiv=sl.buildShadow(active,archive.map(z=>key(z.a,z.b)===unknownKey?{...z,kind:"EQUIVALENT"}:z),pins);
 t("unresolved_equivalence_blocks",()=>hold(()=>sl.prepare(equiv,p.policy.profiles,c),"UNRESOLVED_RELATION"));
 const fabricated=change(z=>z.answer="조건과 무관하게 100% 수익을 보장한다.");
 const misroute=sl.prepare(shadow,p.policy.profiles,{...c,profile:"COMPARE"});
 return {results,limitations:{fabricated_semantic_receipt_can_pass:sl.finalize(pre,fabricated,fabricated.answer).status==="CONDITIONAL",wrong_profile_not_automatically_detected:misroute.status==="REVIEW_REQUIRED",no_new_card_admission_implemented:true}};
}

export {runChecks};
