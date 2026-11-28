function invariant(ok,msg){if(!ok)throw Error(msg)}

function canonical(x){return Array.isArray(x)?"["+x.map(canonical).join(",")+"]":x!==null&&typeof x==="object"?"{"+Object.keys(x).sort().map(k=>JSON.stringify(k)+":"+canonical(x[k])).join(",")+"}":JSON.stringify(x)}

function key(a,b){return [a,b].sort().join("|")}

function copy(x){return JSON.parse(JSON.stringify(x))}

function validDate(s){return typeof s==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s}

function buildShadow(active,archive,pins){
  invariant(active instanceof Map&&active.size>0,"ACTIVE_REQUIRED");
  invariant(["engine","ledger","registry","plan"].every(k=>/^[a-f0-9]{40}$/.test(pins[k])),"PINS_REQUIRED");
  const cards=new Map([...active].map(([id,c])=>[id,copy(c)])),relations=new Map();
  for(const rel of archive){invariant(cards.has(rel.a)&&cards.has(rel.b)&&rel.a!==rel.b&&["DISTINCT","COMPLEMENT","CONFLICT","EQUIVALENT"].includes(rel.kind),"BAD_RELATION");relations.set(key(rel.a,rel.b),copy(rel))}
  const explicit=[...relations.values()].filter(r=>r.kind!=="DISTINCT");
  return {cards,archive:relations,explicit,pins:copy(pins)};
}

function relationState(shadow,a,b){
  invariant(shadow.cards.has(a)&&shadow.cards.has(b)&&a!==b,"UNKNOWN_CARD");
  return shadow.archive.get(key(a,b))?.kind||"UNREVIEWED";
}

function prepare(shadow,profiles,request){
  invariant(request&&typeof request.id==="string"&&typeof request.question==="string"&&request.question.trim()&&validDate(request.day),"INVALID_REQUEST");
  const binding={id:request.id,question:request.question,day:request.day,profile:request.profile,pins:copy(shadow.pins)};
  const profile=Object.prototype.hasOwnProperty.call(profiles,request.profile)?profiles[request.profile]:null;
  if(!profile)return {status:"HOLD",reason:"UNREGISTERED_PROFILE",binding};
  const ids=new Set(),missing=new Set(),visiting=new Set();
  function visit(id){if(visiting.has(id)){missing.add(id);return}if(ids.has(id))return;const c=shadow.cards.get(id);if(!c||c.status!=="VERIFIED_SCOPED"||request.day<c.reviewed_on||request.day>c.valid_through){missing.add(id);return}visiting.add(id);for(const dep of c.dependencies)visit(dep);visiting.delete(id);ids.add(id)}
  for(const list of Object.values(profile.obligations))for(const id of list)visit(id);
  for(const [a,b] of profile.bridges){visit(a);visit(b)}
  if(missing.size)return {status:"HOLD",reason:"MISSING_OR_EXPIRED",missing:[...missing].sort(),binding};
  const selected=[...ids].sort(),conflict=shadow.explicit.filter(r=>ids.has(r.a)&&ids.has(r.b)&&["CONFLICT","EQUIVALENT"].includes(r.kind));
  if(conflict.length)return {status:"HOLD",reason:"UNRESOLVED_RELATION",conflict,binding};
  const bridges=profile.bridges.map(([a,b])=>({pair:key(a,b),state:relationState(shadow,a,b)}));
  const evidence=selected.map(id=>({id,version:shadow.cards.get(id).version,review_blob:shadow.cards.get(id).review_blob,refs:shadow.cards.get(id).evidence.filter(e=>e.use==="CURRENT_WEB").map(e=>({id:e.id,url:e.url}))}));
  return {status:"REVIEW_REQUIRED",binding,obligations:copy(profile.obligations),selected,bridges,evidence};
}

function finalize(prepared,receipt,answer){
  if(prepared.status!=="REVIEW_REQUIRED")return {status:"HOLD",reason:prepared.reason};
  const hold=reason=>({status:"HOLD",reason});
  if(!receipt||canonical(receipt.binding)!==canonical(prepared.binding))return hold("BINDING_MISMATCH");
  if(typeof answer!=="string"||!answer.trim()||answer!==receipt.answer)return hold("ANSWER_MISMATCH");
  if(receipt.disposition!=="CONDITIONAL"||receipt.personal_trade!==false)return hold("UNSUPPORTED_DISPOSITION");
  if(canonical(receipt.evidence)!==canonical(prepared.evidence))return hold("EVIDENCE_MISMATCH");
  if(!receipt.checks||canonical(Object.keys(receipt.checks).sort())!==canonical(Object.keys(prepared.obligations).sort()))return hold("OBLIGATION_COVERAGE");
  for(const [name,ids] of Object.entries(prepared.obligations)){const c=receipt.checks[name];if(!c||!["SATISFIED","CONDITIONAL"].includes(c.status)||canonical([...ids].sort())!==canonical([...(c.cards||[])].sort())||typeof c.note!=="string"||!c.note.trim())return hold("OBLIGATION_NOT_RESOLVED")}
  if(!Array.isArray(receipt.bridges)||receipt.bridges.length!==prepared.bridges.length||new Set(receipt.bridges.map(b=>b.pair)).size!==prepared.bridges.length)return hold("BRIDGE_COVERAGE");
  for(const b of prepared.bridges){const c=receipt.bridges.find(x=>x.pair===b.pair);if(!c||c.state!==b.state||c.review_scope!=="QUESTION_ONLY"||!["COMPATIBLE","COMPLEMENT","DISTINCT"].includes(c.resolution)||typeof c.note!=="string"||!c.note.trim())return hold("BRIDGE_NOT_RESOLVED");if(b.state==="UNREVIEWED"&&c.fresh_review!==true)return hold("UNKNOWN_RELATION_REVIEW_REQUIRED");if(["CONFLICT","EQUIVALENT"].includes(b.state))return hold("UNRESOLVED_RELATION")}
  if(receipt.semantic_review!=="CHATGPT_SCOPED"||receipt.high_risk_open!==false)return hold("SEMANTIC_REVIEW_REQUIRED");
  return {status:"CONDITIONAL",answer,selected:prepared.selected,evidence:prepared.evidence,binding:prepared.binding};
}

export {buildShadow,relationState,prepare,finalize};
