function assert(ok,msg){if(!ok)throw Error(msg)}

function clone(x){return JSON.parse(JSON.stringify(x))}

function key(a,b){return [a,b].sort().join("|")}

function iso(s){return /^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s}

function admit(legacy,archive,review,pin,links){
 assert(legacy instanceof Map&&legacy.size===25,"LEGACY_REQUIRED");
 assert(review.topic==="T005"&&review.version===1&&review.status==="SCOPED_REVIEW_FOR_EXPERIMENT_ONLY"&&review.admission==="EXPERIMENT_ONLY","EXPERIMENT_REVIEW_REQUIRED");
 assert(/^[a-f0-9]{40}$/.test(pin.commit)&&/^[a-f0-9]{40}$/.test(pin.blob),"PIN_REQUIRED");
 assert(iso(review.as_of)&&review.cards.length===4,"INCOMPLETE_REVIEW");
 const active=new Map([...legacy].map(([id,c])=>[id,clone(c)])),ids=new Set(review.cards.map(c=>c.id));
 assert(ids.size===4&&[1,2,3,4].every(n=>ids.has("T005-0"+n)),"CARD_SET");
 for(const c of review.cards){
  assert(!active.has(c.id)&&c.status==="VERIFIED_SCOPED"&&c.rule?.trim()&&c.limits?.length&&iso(c.valid_through)&&c.valid_through>=review.as_of,"CARD_UNVERIFIED");
  assert(![...active.values()].some(x=>x.rule===c.rule),"DUPLICATE_RULE");
  assert(c.sources?.length&&c.sources.every(s=>review.source_audit.rows.some(r=>s===`${r.video}:${r.first}–${r.last}`)),"SOURCE_REQUIRED");
  assert(c.evidence?.length&&c.evidence.every(e=>e.use==="CURRENT_WEB"&&e.type==="WEB_BODY"&&e.url.startsWith("https://")&&e.scope&&e.date),"EVIDENCE_REQUIRED");
  assert(Array.isArray(c.dependencies)&&new Set(c.dependencies).size===c.dependencies.length&&!c.dependencies.includes(c.id),"DEPENDENCY_INVALID");
  active.set(c.id,{...clone(c),topic:review.topic,version:review.version,reviewed_on:review.as_of,review_by:c.valid_through,review_commit:pin.commit,review_blob:pin.blob});
 }
 const relations=new Map(archive.map(r=>[key(r.a,r.b),clone(r)])),newlinks=new Set();
 for(const r of links){const k=key(r.a,r.b);assert(active.has(r.a)&&active.has(r.b)&&r.a!==r.b&&(ids.has(r.a)||ids.has(r.b))&&!relations.has(k)&&!newlinks.has(k)&&r.reason?.trim(),"RELATION_INVALID");assert(r.kind==="COMPLEMENT","UNRESOLVED_OR_UNSUPPORTED_RELATION");newlinks.add(k);relations.set(k,clone(r))}
 function visit(id,stack){assert(!stack.has(id),"DEPENDENCY_CYCLE");const c=active.get(id);assert(c,"MISSING_DEPENDENCY");for(const d of c.dependencies)visit(d,new Set(stack).add(id))}
 for(const id of ids){visit(id,new Set());for(const dep of active.get(id).dependencies)assert(newlinks.has(key(id,dep)),"DEPENDENCY_RELATION_REQUIRED")}
 return {status:"EXPERIMENT_ONLY",active,archive:[...relations.values()],event:{topic:review.topic,version:review.version,review_commit:pin.commit,review_blob:pin.blob,ids:[...ids],links:clone(links)}}
}

export {admit};
