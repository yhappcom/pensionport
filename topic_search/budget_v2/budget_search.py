"""Bounded read-only selection over existing coverage inventory. No semantic inference."""
from coverage_search import CoverageSearch
from topic_index import require

def select(inventory,limit=12):
    require(type(limit) is int and limit>0,'positive integer limit required')
    remaining=list(inventory['results']);chosen=[];counts={};spans={}
    # One passage per source before second, avoid redundant overlapping cores.
    while remaining and len(chosen)<limit:
        eligible=[r for r in remaining if not any(r['first_cue']<=b and a<=r['last_cue'] for a,b in spans.get(r['source_sha'],[]))]
        if not eligible:break
        row=min(eligible,key=lambda r:(counts.get(r['source_sha'],0),-r['score'],r['source_sha'],r['first_cue']))
        sid=row['source_sha'];chosen.append(row);counts[sid]=counts.get(sid,0)+1;spans.setdefault(sid,[]).append((row['first_cue'],row['last_cue']));remaining.remove(row)
    return chosen
