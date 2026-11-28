function assert(ok,msg){if(!ok)throw Error(msg)}

function utf8(s){
 const b=[];for(const c of s){const n=c.codePointAt(0);assert(n<0xd800||n>0xdfff,"INVALID_UTF8");if(n<128)b.push(n);else if(n<2048)b.push(192|(n>>>6),128|(n&63));else if(n<65536)b.push(224|(n>>>12),128|((n>>>6)&63),128|(n&63));else b.push(240|(n>>>18),128|((n>>>12)&63),128|((n>>>6)&63),128|(n&63))}return b;
}

function sha1(bytes){
 const b=bytes.slice(),bits=b.length*8,rot=(x,n)=>(x<<n)|(x>>>(32-n));b.push(128);while(b.length%64!==56)b.push(0);const hi=Math.floor(bits/4294967296),lo=bits>>>0;for(const x of [hi,lo])for(let s=24;s>=0;s-=8)b.push((x>>>s)&255);
 let h=[0x67452301,0xefcdab89,0x98badcfe,0x10325476,0xc3d2e1f0];
 for(let i=0;i<b.length;i+=64){const w=[];for(let j=0;j<16;j++){let k=i+4*j;w[j]=(b[k]<<24)|(b[k+1]<<16)|(b[k+2]<<8)|b[k+3]}for(let j=16;j<80;j++)w[j]=rot(w[j-3]^w[j-8]^w[j-14]^w[j-16],1);let [a,c,d,e,f]=h;for(let j=0;j<80;j++){const g=j<20?(c&d)|(~c&e):j<40?c^d^e:j<60?(c&d)|(c&e)|(d&e):c^d^e,k=j<20?0x5a827999:j<40?0x6ed9eba1:j<60?0x8f1bbcdc:0xca62c1d6;const z=(rot(a,5)+g+f+k+w[j])|0;f=e;e=d;d=rot(c,30);c=a;a=z}h=h.map((x,j)=>(x+[a,c,d,e,f][j])|0)}
 return h.map(x=>(x>>>0).toString(16).padStart(8,"0")).join("");
}

function gitBlob(s){assert(typeof s==="string","RAW_TEXT_REQUIRED");const b=utf8(s);return sha1(utf8("blob "+b.length+"\0").concat(b))}

function verifyFile(file,expected){assert(file&&typeof file.content==="string","RAW_TEXT_REQUIRED");assert(file.sha===expected&&gitBlob(file.content)===expected,"BLOB_MISMATCH");return file.content}

function bindFiles(planFile,approvedPlanBlob,files){
 const p=JSON.parse(verifyFile(planFile,approvedPlanBlob)),t=p.trusted,verified={};
 for(const name of ["engine","ledger","registry","admission","shadow","review","experiment"]){const pin=t[name],hash=typeof pin==="string"?pin:pin.blob;verified[name]=verifyFile(files[name],hash);if(typeof pin==="object")assert(files[name].path===pin.path&&files[name].commit===pin.commit,"LOCATION_MISMATCH")}
 const review=JSON.parse(verified.review),experiment=JSON.parse(verified.experiment);
 assert(experiment.review_pin.blob===t.review.blob&&experiment.review_pin.commit===t.review.commit,"REVIEW_EVENT_MISMATCH");
 return {plan:p,verified,review,experiment};
}

function pair(a,b){return [a,b].sort().join("|")}

function prepareBound(shadow,sl,profiles,contract,request){
 const hold=reason=>({status:"HOLD",reason});
 if(!contract||request.id!==contract.id||request.question!==contract.question||request.day!==contract.day)return hold("QUESTION_CONTRACT_MISMATCH");
 if(!contract.required_profiles.length)return hold("OUTSIDE_SCOPE");
 if(!Array.isArray(request.profiles)||JSON.stringify([...new Set(request.profiles)].sort())!==JSON.stringify([...contract.required_profiles].sort())||request.profiles.length!==contract.required_profiles.length)return hold("PROFILE_COVERAGE");
 const obligations={},bridges=new Map();
 for(const name of contract.required_profiles){const p=profiles[name];if(!p)return hold("UNREGISTERED_PROFILE");for(const [k,ids] of Object.entries(p.obligations))obligations[k]=[...new Set([...(obligations[k]||[]),...ids])].sort();for(const [a,b] of p.bridges)bridges.set(pair(a,b),[a,b]);}
 const name=contract.required_profiles.slice().sort().join("+"),req={id:request.id,question:request.question,day:request.day,profile:name};
 let pre=sl.prepare(shadow,{[name]:{obligations,bridges:[...bridges.values()]}},req);if(pre.status!=="REVIEW_REQUIRED")return pre;
 if(!contract.required.every(id=>pre.selected.includes(id)))return hold("REQUIRED_CARD_MISSING");
 // Conservative coverage of all unknown pairs involving a new card inside the selected set.
 for(let i=0;i<pre.selected.length;i++)for(let j=i+1;j<pre.selected.length;j++){const a=pre.selected[i],b=pre.selected[j];if((a.startsWith("T005-")||b.startsWith("T005-"))&&sl.relationState(shadow,a,b)==="UNREVIEWED")bridges.set(pair(a,b),[a,b]);}
 pre=sl.prepare(shadow,{[name]:{obligations,bridges:[...bridges.values()]}},req);
 return pre;
}

export {gitBlob,verifyFile,bindFiles,prepareBound};
