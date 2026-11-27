"""D4 repair candidate: explicit context retrieval and manual atomic scoring.
The frozen Engine remains the storage authority. No automatic semantic inference.
"""
from engine import Engine, digest, require, nonempty

FIELDS = ("proposition", "subject", "speaker_stance", "polarity", "conditions",
          "exceptions", "numbers_units", "time_scope")
KINDS = {"REQUIRED_CONTEXT", "CONDITION", "EXCEPTION"}


def ids(rows):
    out = {}
    for x in rows:
        k = x['id']
        require(nonempty(k) and k not in out, 'invalid/duplicate atom id')
        require(all(nonempty(x[f]) for f in FIELDS), 'explicit semantic fields required')
        require(x['cues'] and all(type(i) is int and i > 0 for i in x['cues']), 'source anchors required')
        require(x['risk'] in {'H', 'M', 'L'}, 'invalid risk')
        out[k] = x
    return out


def assess(reference, output, reviews, frozen_sha, source_id, cue_count):
    """Count separately enumerated atoms; judgments are supplied by ChatGPT.
    Each output may be credited once, and only if every required field matches.
    A second matching output for an already credited reference is a duplicate FP.
    """
    require(digest(reference) == frozen_sha, 'reference changed')
    require(reference['source_id'] == output['source_id'] == source_id, 'source mismatch')
    require(reference['unit'] == output['unit'] == 'ATOM', 'compound groups not scorable')
    require(reference['atomization_reviewed'] is True and output['atomization_reviewed'] is True,
            'manual atomicity review required')
    refs, outs = ids(reference['atoms']), ids(output['atoms'])
    require(refs and outs, 'empty denominator')
    for x in list(refs.values()) + list(outs.values()):
        require(all(i <= cue_count for i in x['cues']), 'invalid source anchor')
    seen, candidates = set(), {}
    for row in reviews:
        o, r = row['output'], row['reference']
        require(o in outs and o not in seen and nonempty(row['reason']), 'invalid/duplicate review')
        seen.add(o)
        require(r is None or r in refs, 'unknown reference')
        flags = row['fields']
        require(set(flags) == set(FIELDS) and all(type(v) is bool for v in flags.values()), 'field adjudication required')
        if r is not None and all(flags.values()):
            require(set(outs[o]['cues']) & set(refs[r]['cues']), 'no shared source anchor')
            candidates.setdefault(r, []).append(o)
    require(seen == set(outs), 'unreviewed output atoms')
    matched = {r: sorted(v)[0] for r, v in candidates.items()}
    missed = sorted(set(refs) - set(matched))
    extra = sorted(set(outs) - set(matched.values()))
    high = [r for r in missed if refs[r]['risk'] == 'H']
    n = len(matched)
    return dict(reference_count=len(refs), output_count=len(outs), matched=matched,
                missed=missed, extra=extra, high_risk_missed=high,
                precision=n/len(outs), recall=n/len(refs),
                threshold_met=100*n >= 95*len(outs) and 100*n >= 98*len(refs) and not high,
                assessment='MANUAL_INTERNAL_ONLY', output_sha=digest(output), review_sha=digest(reviews))


class ContextEngine(Engine):
    """Read-only contextual search extension; no writes to research records."""
    def query_context(self, terms, registry):
        with self.db() as c:
            head = self.head(c)
            require(registry['head'] == head, 'stale context registry')
            require(registry['reviewed'] is True, 'context registry not reviewed')
            catalog = self.catalog(c)
            active = self.eligible(catalog)
            edges = {}
            seen = set()
            for e in registry['edges']:
                a, b = e['from'], e['to']
                require(a in active and b in active and a != b, 'inactive/unknown context edge')
                require(e['kind'] in KINDS and nonempty(e['reason']), 'invalid context edge')
                require(e['from_sha'] == digest(catalog[a]) and e['to_sha'] == digest(catalog[b]), 'context endpoint changed')
                require((a,b) not in seen, 'duplicate context edge')
                seen.add((a,b))
                edges.setdefault(a, []).append(e)
            direct = self.candidates(c, terms)
            roots = {x['item']['qualified_id'] for x in direct}
            reached = roots | {d['qualified_id'] for x in direct for d in x['dependencies']}
            pending = sorted(reached)
            paths = []
            while pending:
                a = pending.pop(0)
                for e in sorted(edges.get(a, []), key=lambda x: x['to']):
                    b = e['to']
                    paths.append(e)
                    if b not in reached:
                        reached.add(b)
                        pending.append(b)
                for b in sorted(catalog[a]['depends_on']):
                    require(b in active, 'inactive dependency')
                    if b not in reached:
                        reached.add(b)
                        pending.append(b)
            return dict(head=head, direct=direct, context=[catalog[k] for k in sorted(reached-roots)],
                        traversed=paths, registry_sha=digest(registry), mode=self.mode)
