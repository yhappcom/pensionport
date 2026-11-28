function runBound(host,hostBlob,planFile,approvedPlanBlob,files,request,receipt,answer){
 const bound=host.bindFiles(planFile,approvedPlanBlob,files),load=(s,n)=>Function(s.replace(/export \{[^}]+\};\s*$/,"")+";return {"+n+"};")();
 const legacy=load(bound.verified.engine,"derive"),ad=load(bound.verified.admission,"admit"),sl=load(bound.verified.shadow,"buildShadow,prepare,finalize,relationState"),l=JSON.parse(bound.verified.ledger),r=JSON.parse(bound.verified.registry),d=legacy.derive(l,r),map=new Map();
 for(const e of l.events)for(const rel of r[e.key].relations)map.set([rel.a,rel.b].sort().join("|"),rel);
 const ex=ad.admit(d.active,[...map.values()],bound.review,bound.experiment.review_pin,bound.experiment.event.links);
 const pins={...bound.experiment.base_pins,bound_plan:approvedPlanBlob,bound_host:hostBlob},shadow=sl.buildShadow(ex.active,ex.archive,pins);
 const contract=bound.plan.cases.find(c=>c.id===request.id),prepared=host.prepareBound(shadow,sl,bound.experiment.profiles,contract,request);
 const gate=receipt===undefined?null:sl.finalize(prepared,receipt,answer);
 return {legacy_count:d.active.size,experiment_count:ex.active.size,archive_count:ex.archive.length,prepared,gate};
}

export {runBound};
