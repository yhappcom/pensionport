function check(ok,msg){if(!ok)throw Error(msg)}

function clone(x){return JSON.parse(JSON.stringify(x))}

function key(a,b){return [a,b].sort().join("|")}

function iso(s){return typeof s==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s}

function openOperating(hash,manifestFile,anchor,files,derive){
 const read=(file,pin,commit)=>{check(file&&typeof file.content==="string","FILE_MISSING");check(file.path===pin.path&&file.commit===(commit||pin.commit),"LOCATION_MISMATCH");check(file.sha===pin.blob&&hash(file.content)===pin.blob,"BLOB_MISMATCH");return file.content};
 check(manifestFile.sha===anchor&&hash(manifestFile.content)===anchor,"MANIFEST_MISMATCH");
 const m=JSON.parse(manifestFile.content);check(m.schema===1&&m.policy==="B_SCOPED_DIRECT_V1"&&m.status==="OPERATING_SCOPED","POLICY_MISMATCH");
 read(files.helper,m.hash_helper);read(files.policy,m.policy_doc);const code=read(files.engine,m.legacy.engine,m.legacy.commit),ledger=JSON.parse(read(files.ledger,m.legacy.ledger,m.legacy.commit)),registry=JSON.parse(read(files.registry,m.legacy.registry,m.legacy.commit));
 const d=derive(code,ledger,registry),active=new Map([...d.active].map(([id,c])=>[id,clone(c)])),relations=new Map(),approved=[];
 for(const event of ledger.events)for(const r of registry[event.key].relations)relations.set(key(r.a,r.b),clone(r));
 for(const pin of m.approvals){
  const a=JSON.parse(read(files.approvals[pin.topic],pin));check(a.topic===pin.topic&&a.status==="APPROVED_SCOPED"&&a.policy===m.policy&&iso(a.approved_on)&&iso(a.review_by)&&a.approved_on<=a.review_by,"APPROVAL_REQUIRED");
  check(JSON.stringify(a.review)===JSON.stringify(pin.review),"REVIEW_PIN_MISMATCH");
  const v=JSON.parse(read(files.reviews[pin.topic],a.review));check(v.topic===a.topic&&v.version===a.version&&Array.isArray(v.cards)&&v.cards.length&&JSON.stringify(v.cards.map(c=>c.id))===JSON.stringify(a.expected_ids),"REVIEW_CARD_MISMATCH");
  const ids=new Set(a.expected_ids);check(ids.size===v.cards.length,"DUPLICATE_CARD");
  for(const c of v.cards){check(!active.has(c.id)&&c.status==="VERIFIED_SCOPED"&&typeof c.rule==="string"&&c.rule.trim()&&Array.isArray(c.limits)&&c.limits.length&&iso(c.valid_through)&&c.valid_through>=a.approved_on&&c.valid_through<=a.review_by,"CARD_INVALID");check(c.sources?.length&&c.sources.every(s=>v.source_audit.rows.some(r=>s===`${r.video}:${r.first}–${r.last}`)),"SOURCE_REQUIRED");check(c.evidence?.length&&c.evidence.every(e=>e.use==="CURRENT_WEB"&&e.url.startsWith("https://")&&e.scope&&e.date),"EVIDENCE_REQUIRED");check(Array.isArray(c.dependencies)&&new Set(c.dependencies).size===c.dependencies.length&&!c.dependencies.includes(c.id),"DEPENDENCY_INVALID");check(![...active.values()].some(x=>x.rule===c.rule),"DUPLICATE_RULE");active.set(c.id,{...clone(c),topic:a.topic,version:a.version,reviewed_on:a.approved_on,review_by:a.review_by,review_commit:a.review.commit,review_blob:a.review.blob,approval_blob:pin.blob,approval_limits:clone(a.limits),exclusions:clone(a.exclusions)});}
  for(const r of a.direct_relations){const k=key(r.a,r.b);check(active.has(r.a)&&active.has(r.b)&&r.a!==r.b&&(ids.has(r.a)||ids.has(r.b))&&!relations.has(k)&&r.kind==="COMPLEMENT"&&r.reason?.trim(),"RELATION_INVALID");relations.set(k,clone(r));}
  for(const id of ids)for(const dep of active.get(id).dependencies)check(relations.get(key(id,dep))?.kind==="COMPLEMENT","DEPENDENCY_RELATION_REQUIRED");
  approved.push(pin.topic);
 }
 function visit(id,stack){check(!stack.has(id)&&active.has(id),"DEPENDENCY_INVALID");for(const dep of active.get(id).dependencies)visit(dep,new Set(stack).add(id))}
 for(const id of active.keys())visit(id,new Set());
 return {active,relations,approved,manifest_blob:anchor};
}

function queryOperating(s,topics,day){
 check(iso(day)&&Array.isArray(topics)&&topics.length&&topics.every(t=>/^T\d{3}$/.test(t)),"INVALID_QUERY");
 function eligible(id,stack=new Set()){const c=s.active.get(id);if(!c||stack.has(id)||c.status!=="VERIFIED_SCOPED"||day<c.reviewed_on||day>c.valid_through)return false;return c.dependencies.every(dep=>eligible(dep,new Set(stack).add(id)))}
 const ids=new Set();function add(id){if(ids.has(id)||!eligible(id))return;ids.add(id);for(const dep of s.active.get(id).dependencies)add(dep)}
 for(const c of s.active.values())if(topics.includes(c.topic))add(c.id);
 const selected=[...ids].sort();const conflicts=[...s.relations.values()].filter(r=>ids.has(r.a)&&ids.has(r.b)&&["CONFLICT","EQUIVALENT"].includes(r.kind));
 if(conflicts.length)return {status:"HOLD",reason:"UNRESOLVED_RELATION",cards:[],conflicts};
 const cards=selected.map(id=>{const c=clone(s.active.get(id));c.evidence=c.evidence.filter(e=>e.use==="CURRENT_WEB");return c});
 return {status:cards.length?"CANDIDATES_ONLY":"HOLD",reason:cards.length?"CHATGPT_MEANING_REVIEW_REQUIRED":"NO_CURRENT_APPROVED_KNOWLEDGE",cards,manifest_blob:s.manifest_blob,topics:[...topics],day};
}

function relationState(s,a,b){check(a!==b&&s.active.has(a)&&s.active.has(b),"UNKNOWN_CARD");return s.relations.get(key(a,b))?.kind||"UNREVIEWED"}

export {openOperating,queryOperating,relationState};
