"""Clean-start research storage. ChatGPT supplies all semantic judgments."""
import argparse
import hashlib
import json
import re
import sqlite3
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(dump(value).encode())


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and all(nonempty(x) for x in value)


def parse_srt(raw):
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    def ms(t):
        h, m, s, n = map(int, re.split(r"[:,]", t))
        require(m < 60 and s < 60, "invalid timestamp")
        return ((h * 60 + m) * 60 + s) * 1000 + n
    for block in re.split(r"\n[ \t]*\n+", text.strip("\n")):
        lines = block.split("\n")
        require(len(lines) >= 3 and lines[0].strip().isdigit(), "invalid SRT block")
        match = re.fullmatch(r"(\d{2,}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2,}:\d{2}:\d{2},\d{3})", lines[1].strip())
        require(match is not None, "invalid SRT time range")
        start, end = map(ms, match.groups())
        i = int(lines[0])
        require(i == len(cues) + 1 and start < end and (not cues or start >= cues[-1]["start_ms"]), "invalid cue sequence")
        body = "\n".join(lines[2:])
        require(nonempty(body), "empty cue")
        cues.append(dict(id=i, start_ms=start, end_ms=end, text=body))
    require(cues, "empty SRT")
    return cues


ACTIVE = {"APPROVE", "CORRECT"}
VERDICTS = ACTIVE | {"DUPLICATE", "CONTEXT", "HOLD", "EXCLUDE"}
RELATIONS = {"SAME", "EXTENDS", "CORRECTS", "CONFLICTS", "DISTINCT"}


class Engine:
    def __init__(self, path, mode="research"):
        require(mode in {"research", "test"}, "invalid mode")
        self.path, self.mode = str(path), mode
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("CREATE TABLE IF NOT EXISTS meta(mode TEXT NOT NULL, head TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS videos(id TEXT PRIMARY KEY, raw BLOB NOT NULL, draft TEXT, final TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, video TEXT NOT NULL REFERENCES videos(id), data TEXT NOT NULL)")
            row = c.execute("SELECT mode,head FROM meta").fetchall()
            if not row:
                c.execute("INSERT INTO meta VALUES (?,?)", (mode, digest([])))
            else:
                require(len(row) == 1 and row[0][0] == mode, "database mode mismatch")

    @contextmanager
    def db(self, write=False):
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute("PRAGMA foreign_keys=ON")
            c.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            require(c.execute("SELECT mode FROM meta").fetchall() == [(self.mode,)], "database mode mismatch")
            yield c

    def source(self, c, sid):
        row = c.execute("SELECT raw,draft,final FROM videos WHERE id=?", (sid,)).fetchone()
        require(row is not None and sha(row[0]) == sid, "source missing or changed")
        return parse_srt(row[0]), row[1], row[2]

    def head(self, c):
        return c.execute("SELECT head FROM meta").fetchone()[0]

    def catalog(self, c):
        return {k: json.loads(v) for k, v in c.execute("SELECT id,data FROM items ORDER BY rowid")}

    def eligible(self, catalog):
        blocked = {r["target"] for x in catalog.values() for r in x["relations"] if r["type"] in {"CORRECTS", "CONFLICTS"}}
        active = {k for k, x in catalog.items() if x["verdict"] in ACTIVE and k not in blocked}
        while True:
            good = {k for k in active if all(d in active for d in catalog[k]["depends_on"])}
            if good == active:
                return good
            active = good

    def candidates(self, c, terms):
        require(strings(terms), "terms must be strings")
        catalog = self.catalog(c)
        active = self.eligible(catalog)
        found = []
        for k in sorted(active):
            item = catalog[k]
            support = [x for x in catalog.values() if x["verdict"] == "DUPLICATE" and any(r["type"] == "SAME" and r["target"] == k for r in x["relations"]) and all(d in active for d in x["depends_on"])]
            hay = dump([item["knowledge"], item["topic"], item["conditions"], item["exceptions"], [x["topic"] for x in support]]).casefold()
            score = sum(t.casefold() in hay for t in set(terms))
            if score:
                needed = set(item["depends_on"])
                for x in support:
                    needed.update(x["depends_on"])
                while True:
                    expanded = needed | {d for dep in needed for d in catalog[dep]["depends_on"]}
                    if expanded == needed:
                        break
                    needed = expanded
                found.append(dict(score=score, item=item, additional_sources=support, dependencies=[catalog[d] for d in sorted(needed)]))
        return sorted(found, key=lambda x: (-x["score"], x["item"]["qualified_id"]))

    def prepare(self, raw, terms):
        cues, sid = parse_srt(raw), sha(raw)
        with self.db(True) as c:
            c.execute("INSERT OR IGNORE INTO videos(id,raw) VALUES (?,?)", (sid, raw))
            return self.packet(c, sid, terms)

    def packet(self, c, sid, terms):
        cues, draft, final = self.source(c, sid)
        return dict(mode=self.mode, source_id=sid, cues=cues, head=self.head(c), candidates=self.candidates(c, terms), draft=json.loads(draft) if draft else None, draft_sha=digest(json.loads(draft)) if draft else None, final=json.loads(final) if final else None)

    def resume(self, sid, terms):
        with self.db() as c:
            return self.packet(c, sid, terms)

    def validate(self, packet, cues, final):
        require(packet["mode"] == self.mode and packet["source_id"], "packet mode/source mismatch")
        require(nonempty(packet["review_note"]), "review note required")
        available = {x["id"]: x for x in cues}
        covered, ids, items = set(), set(), []
        sid = packet["source_id"]
        for x in packet["claims"]:
            require(re.fullmatch(r"[A-Za-z0-9_-]+", x["id"]) and x["id"] not in ids, "invalid/duplicate claim ID")
            ids.add(x["id"])
            require(all(nonempty(x[k]) for k in ("topic", "statement", "speaker", "time_scope", "reason")), "claim context required")
            require(x["kind"] in {"FACT", "OPINION", "ASSUMPTION", "QUESTION", "OTHER"} and x["verdict"] in VERDICTS, "invalid kind/verdict")
            require(all(strings(x[k]) for k in ("conditions", "exceptions", "numbers", "depends_on")), "invalid condition/number/dependency list")
            require(x["cues"] and len(set(x["cues"])) == len(x["cues"]) and all(type(i) is int and i in available for i in x["cues"]), "invalid source location")
            covered.update(x["cues"])
            if x["verdict"] in ACTIVE | {"DUPLICATE"}:
                require(x["kind"] == "FACT" and nonempty(x["knowledge"]) and x["evidence"], "fact knowledge and evidence required")
            else:
                require(x["knowledge"] == "", "non-approved knowledge must be empty")
            for e in x["evidence"]:
                require(all(nonempty(e[k]) for k in ("issuer", "title", "url", "checked_on", "applies_on", "scope", "excerpt", "access")), "evidence metadata required")
                u = urlsplit(e["url"])
                require(u.scheme == "https" and u.hostname and (self.mode == "test" or not u.hostname.endswith(".invalid")), "invalid evidence URL")
                date.fromisoformat(e["checked_on"])
                require(e["access"] in {"WEB", "BYTES", "TEST"} and (self.mode == "test" or e["access"] != "TEST"), "invalid evidence access")
                if e["access"] == "BYTES":
                    require(re.fullmatch(r"[0-9a-f]{64}", e.get("sha256", "")), "evidence byte hash required")
            for r in x["relations"]:
                require(r["type"] in RELATIONS and nonempty(r["target"]) and nonempty(r["reason"]), "invalid relation")
            item = dict(x, qualified_id=sid + ":" + x["id"], source_id=sid, source=[available[i] for i in x["cues"]])
            item["depends_on"] = [d if ":" in d else sid + ":" + d for d in x["depends_on"]]
            items.append(item)
        nonclaim = set()
        for x in packet["nonclaim"]:
            require(nonempty(x["reason"]) and x["cues"], "nonclaim reason required")
            for i in x["cues"]:
                require(type(i) is int and i in available and i not in covered and i not in nonclaim, "invalid/overlapping nonclaim cue")
                nonclaim.add(i)
        if final:
            require(covered | nonclaim == set(available), "incomplete source coverage")
        return items, len(covered | nonclaim)

    def save_draft(self, packet):
        sid = packet["source_id"]
        with self.db(True) as c:
            cues, old, final = self.source(c, sid)
            require(final is None, "already finalized")
            data = dump(packet)
            if old is not None:
                require(old == data, "draft already saved; resume it")
                return digest(packet)
            require(packet["head"] == self.head(c), "stale knowledge head")
            self.validate(packet, cues, False)
            c.execute("UPDATE videos SET draft=? WHERE id=?", (data, sid))
            return digest(packet)

    def finalize(self, packet):
        sid, data = packet["source_id"], dump(packet)
        with self.db(True) as c:
            cues, draft, old = self.source(c, sid)
            if old is not None:
                require(old == data, "video already finalized with different result")
                return digest(packet)
            require(draft is not None and packet["draft_sha"] == digest(json.loads(draft)), "draft mismatch")
            require(packet["head"] == self.head(c), "stale knowledge head")
            items, _ = self.validate(packet, cues, True)
            catalog = self.catalog(c)
            prior = self.eligible(catalog)
            new = {x["qualified_id"]: x for x in items}
            require(not set(new) & set(catalog), "duplicate qualified ID")
            all_items = catalog | new
            changes = set()
            for k, x in new.items():
                require(all(d in all_items and d != k for d in x["depends_on"]), "unknown/self dependency")
                same = [r for r in x["relations"] if r["type"] == "SAME"]
                require((len(same) == 1) if x["verdict"] == "DUPLICATE" else not same, "duplicate relation required only for DUPLICATE")
                for r in x["relations"]:
                    require(r["target"] in prior, "relation target not active prior knowledge")
                    if r["type"] in {"CORRECTS", "CONFLICTS"}:
                        require(x["verdict"] == ("CORRECT" if r["type"] == "CORRECTS" else "HOLD") and r["target"] not in changes, "invalid conflicting change")
                        changes.add(r["target"])
            # Dependency cycles cannot be treated as verified support.
            pending = set(new)
            while pending:
                ready = {k for k in pending if not set(new[k]["depends_on"]) & pending}
                require(ready, "dependency cycle")
                pending -= ready
            active = self.eligible(all_items)
            for k, x in new.items():
                if x["verdict"] in ACTIVE:
                    require(k in active, "approved claim has unresolved dependency")
                elif x["verdict"] == "DUPLICATE":
                    require(all(d in active for d in x["depends_on"]) and all(r["target"] in active for r in x["relations"] if r["type"] == "SAME"), "duplicate target/dependency inactive")
                c.execute("INSERT INTO items VALUES (?,?,?)", (k, sid, dump(x)))
            c.execute("UPDATE videos SET final=? WHERE id=?", (data, sid))
            c.execute("UPDATE meta SET head=?", (digest([self.head(c), digest(packet)]),))
            return digest(packet)

    def query(self, terms):
        with self.db() as c:
            return dict(mode=self.mode, head=self.head(c), candidates=self.candidates(c, terms))

    def status(self):
        with self.db() as c:
            catalog = self.catalog(c)
            n, d, f = c.execute("SELECT count(*),count(draft),count(final) FROM videos").fetchone()
            return dict(mode=self.mode, head=self.head(c), sources=n, drafts=d, finalized=f, decisions=len(catalog), active=len(self.eligible(catalog)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--mode", choices=["research", "test"], default="research")
    p.add_argument("command", choices=["prepare", "resume", "draft", "finalize", "query", "status"])
    p.add_argument("args", nargs="*")
    a = p.parse_args()
    e = Engine(a.db, a.mode)
    if a.command == "prepare":
        result = e.prepare(Path(a.args[0]).read_bytes(), a.args[1:])
    elif a.command == "resume":
        result = e.resume(a.args[0], a.args[1:])
    elif a.command in {"draft", "finalize"}:
        packet = json.loads(Path(a.args[0]).read_text(encoding="utf-8"))
        result = dict(mode=a.mode, receipt=(e.save_draft if a.command == "draft" else e.finalize)(packet), status=e.status())
    elif a.command == "query":
        result = e.query(a.args)
    else:
        result = e.status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
