function check(b,e){if(!b)throw Error(e)}

function clone(x){return JSON.parse(JSON.stringify(x))}

function canonical(x){return Array.isArray(x)?"["+x.map(canonical).join(",")+"]":x!==null&&typeof x==="object"?"{"+Object.keys(x).sort().map(k=>JSON.stringify(k)+":"+canonical(x[k])).join(",")+"}":JSON.stringify(x)}

function date(s){return typeof s==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s}

function pair(a,b){return [a,b].sort().join("|")}

function empty(){return {schema:1,events:[]}}

function verify(m){
check(m&&m.status==="APPROVED_SCOPED"&&/^T\d{3,}$/.test(m.topic)&&Number.isInteger(m.version)&&m.version>0,"APPROVAL_REQUIRED");
check(date(m.reviewed_on)&&date(m.review_by)&&m.reviewed_on<=m.review_by,"DATE_INVALID");
check([m.review_commit,m.review_blob,m.source_blob].every(s=>/^[a-f0-9]{40}$/.test(s)),"PIN_REQUIRED");
check(Array.isArray(m.expected_ids)&&m.expected_ids.length>0&&Array.isArray(m.cards)&&m.cards.length===m.expected_ids.length,"INCOMPLETE_TOPIC");
check(new Set(m.expected_ids).size===m.expected_ids.length&&canonical(m.cards.map(c=>c.id).sort())===canonical([...m.expected_ids].sort()),"CARD_SET_MISMATCH");
for(const c of m.cards){
check(c.id.startsWith(m.topic+"-")&&c.status==="VERIFIED_SCOPED"&&typeof c.rule==="string"&&c.rule.trim()&&Array.isArray(c.sources)&&c.sources.length&&Array.isArray(c.evidence)&&c.evidence.length&&Array.isArray(c.limits)&&c.limits.length,"CARD_UNVERIFIED");
check(c.evidence.every(e=>typeof e.url==="string"&&e.url.startsWith("https://")&&e.scope&&e.date&&["CURRENT_WEB","HISTORICAL_CONTEXT"].includes(e.use))&&c.evidence.some(e=>e.use==="CURRENT_WEB"),"EVIDENCE_REQUIRED");
check(c.sources.every(s=>/^[\w-]+:\d+[–-]\d+$/.test(s)),"SOURCE_REQUIRED");
check(date(c.valid_through)&&c.valid_through>=m.reviewed_on&&c.valid_through<=m.review_by,"CARD_DATE_INVALID");
check(Array.isArray(c.dependencies)&&new Set(c.dependencies).size===c.dependencies.length&&!c.dependencies.includes(c.id),"DEPENDENCY_INVALID");
}
check(Array.isArray(m.exclusions)&&m.exclusions.every(x=>["HOLD","CONTEXT"].includes(x.status)),"EXCLUSION_INVALID")
}

function derive(l,r){
check(l&&l.schema===1&&Array.isArray(l.events),"LEDGER_INVALID");let active=new Map(),topics=new Map(),seen=new Set(),links=new Map();
for(const e of l.events){
check(e&&e.seq===seen.size+1&&!seen.has(e.key),"EVENT_INVALID");const m=r[e.key];verify(m);
check(e.key===m.topic+"@"+m.version&&e.review_blob===m.review_blob&&e.review_commit===m.review_commit,"EVENT_PIN_MISMATCH");
const old=topics.get(m.topic);check(!old||m.version>old.version,"VERSION_ROLLBACK");
if(old)check(canonical([...old.expected_ids].sort())===canonical([...m.expected_ids].sort()),"CARD_SET_CHANGE_REQUIRES_REVIEW");
const next=new Map(active);for(const id of old?.expected_ids||[])next.delete(id);
for(const c of m.cards){check(!next.has(c.id),"ID_COLLISION");next.set(c.id,{...c,topic:m.topic,version:m.version,reviewed_on:m.reviewed_on,review_by:m.review_by,review_commit:m.review_commit,review_blob:m.review_blob})}
const required=new Set();for(const c of m.cards)for(const id of next.keys())if(id!==c.id)required.add(pair(c.id,id));
check(Array.isArray(m.relations)&&m.relations.length===required.size,"RELATION_COVERAGE");
const pairs=new Set();for(const rel of m.relations){const k=pair(rel.a,rel.b);check(required.has(k)&&!pairs.has(k)&&typeof rel.reason==="string"&&rel.reason.trim(),"RELATION_INVALID");pairs.add(k);check(["DISTINCT","COMPLEMENT","EQUIVALENT","CONFLICT"].includes(rel.kind),"RELATION_INVALID");check(rel.kind!=="CONFLICT","UNRESOLVED_CONFLICT");check(rel.kind!=="EQUIVALENT","EQUIVALENCE_REQUIRES_CANONICAL_MERGE");check(next.get(rel.a).rule!==next.get(rel.b).rule,"DUPLICATE_RULE")}
for(const c of next.values())for(const d of c.dependencies)check(next.has(d),"MISSING_DEPENDENCY");
function visit(id,stack){check(!stack.has(id),"DEPENDENCY_CYCLE");const s=new Set(stack).add(id);for(const d of next.get(id).dependencies)visit(d,s)}
for(const id of next.keys())visit(id,new Set());
for(const k of required)links.delete(k);for(const rel of m.relations)if(rel.kind==="COMPLEMENT")links.set(pair(rel.a,rel.b),rel);
active=next;topics.set(m.topic,m);seen.add(e.key)
}
return {active,seen,links}
}

function publish(l,r,key){const d=derive(l,r),m=r[key];verify(m);if(d.seen.has(key))return clone(l);const next={schema:1,events:[...l.events,{seq:l.events.length+1,key,review_blob:m.review_blob,review_commit:m.review_commit}]};derive(next,r);return clone(next)}

function query(l,r,topic,day){check(date(day),"QUERY_DATE_REQUIRED");check(typeof topic==="string"&&/^T\d{3,}$/.test(topic),"TOPIC_REQUIRED");const d=derive(l,r);function available(id){const c=d.active.get(id);return c&&day>=c.reviewed_on&&day<=c.valid_through&&c.dependencies.every(available)}
return clone([...d.active.values()].filter(c=>c.topic===topic&&available(c.id)).map(c=>({...c,evidence:c.evidence.filter(e=>e.use==="CURRENT_WEB"),related:[...d.links.values()].filter(x=>(x.a===c.id||x.b===c.id)&&available(x.a)&&available(x.b)).map(x=>x.a===c.id?x.b:x.a)})))}

function runTests(registry,v3,v2){
const m=registry["T001@3"],l=publish(empty(),registry,"T001@3"),out=[];
function eq(a,b){check(canonical(a)===canonical(b),"ASSERT_EQUAL")}
function reject(f,e){try{f()}catch(x){check(String(x).includes(e),"WRONG_ERROR "+x);return}throw Error("NOT_REJECTED "+e)}
function t(name,f){try{f();out.push({name,status:"PASS"})}catch(e){out.push({name,status:"FAIL",reason:String(e)})}}
function alt(f){const n=clone(m);f(n);return {"T001@3":n}}
const q=(l,r,d="2026-11-28")=>query(l,r,"T001",d);
t("actual 8 cards",()=>eq(q(l,registry).length,8));
t("actual rule exact",()=>eq(q(l,registry).map(c=>c.rule),v3.cards.map(c=>c.rule)));
t("actual source exact",()=>eq(q(l,registry).map(c=>c.sources),v2.cards.map(c=>c.source)));
t("idempotent",()=>eq(publish(l,registry,"T001@3"),l));
t("serialization restart",()=>eq(q(clone(l),clone(registry)),q(l,registry)));
t("no historical evidence in active lookup",()=>check(q(l,registry).every(c=>c.status==="VERIFIED_SCOPED"&&c.evidence.every(e=>e.use==="CURRENT_WEB")),"LEAK"));
t("last day",()=>eq(q(l,registry,"2026-12-31").length,8));
t("expired",()=>eq(q(l,registry,"2027-01-01").length,0));
t("before review",()=>eq(q(l,registry,"2026-11-27").length,0));
t("invalid date",()=>reject(()=>q(l,registry,"2026-02-30"),"QUERY_DATE_REQUIRED"));
t("unknown topic",()=>eq(query(l,registry,"T999","2026-11-28"),[]));
t("unpublished",()=>eq(q(empty(),registry),[]));
t("hold rejected",()=>reject(()=>publish(empty(),alt(n=>n.cards[0].status="HOLD"),"T001@3"),"CARD_UNVERIFIED"));
t("partial rejected",()=>reject(()=>publish(empty(),alt(n=>n.cards.pop()),"T001@3"),"INCOMPLETE_TOPIC"));
t("missing evidence rejected",()=>reject(()=>publish(empty(),alt(n=>n.cards[0].evidence=[]),"T001@3"),"CARD_UNVERIFIED"));
t("missing pair rejected",()=>reject(()=>publish(empty(),alt(n=>n.relations.pop()),"T001@3"),"RELATION_COVERAGE"));
t("conflict rejected",()=>reject(()=>publish(empty(),alt(n=>n.relations[0].kind="CONFLICT"),"T001@3"),"UNRESOLVED_CONFLICT"));
t("equivalent pending merge rejected",()=>reject(()=>publish(empty(),alt(n=>n.relations[0].kind="EQUIVALENT"),"T001@3"),"EQUIVALENCE_REQUIRES_CANONICAL_MERGE"));
t("duplicate text rejected",()=>reject(()=>publish(empty(),alt(n=>n.cards[1].rule=n.cards[0].rule),"T001@3"),"DUPLICATE_RULE"));
t("missing dependency",()=>reject(()=>publish(empty(),alt(n=>n.cards[0].dependencies=["T999-01"]),"T001@3"),"MISSING_DEPENDENCY"));
t("cycle",()=>reject(()=>publish(empty(),alt(n=>{n.cards[0].dependencies=["T001-02"];n.cards[1].dependencies=["T001-01"]}),"T001@3"),"DEPENDENCY_CYCLE"));
t("dependent expiry",()=>{const r=alt(n=>n.cards[2].valid_through="2026-11-30");eq(q(publish(empty(),r,"T001@3"),r,"2026-12-01").map(c=>c.id),m.expected_ids.filter(id=>!["T001-03","T001-07"].includes(id)))});
t("rollback on invalid revision",()=>{const old=canonical(l),n=clone(m);n.version=4;n.relations[0].kind="CONFLICT";reject(()=>publish(l,{...registry,"T001@4":n},"T001@4"),"UNRESOLVED_CONFLICT");eq(canonical(l),old)});
t("bad event pin",()=>{const bad=clone(l);bad.events[0].review_blob="0".repeat(40);reject(()=>q(bad,registry),"EVENT_PIN_MISMATCH")});
t("synthetic revision",()=>{const n=clone(m);n.version=4;n.reviewed_on="2026-12-01";const r={...registry,"T001@4":n},next=publish(l,r,"T001@4");eq(next.events.length,2);eq(q(next,r,"2026-12-01").map(c=>c.version),Array(8).fill(4))});
t("lookup mutation isolated",()=>{const x=q(l,registry);x[0].rule="changed";eq(q(l,registry)[0].rule,v3.cards[0].rule)});
t("complement actual relation",()=>check(q(l,registry).find(c=>c.id==="T001-07").related.includes("T001-04"),"MISSING"));
return {ledger:l,tests:out}
}

export {empty,publish,query,derive,runTests};
