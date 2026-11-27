"""D1 technical fixtures only; no financial findings. Optional real SRT directory."""
import copy
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from engine import Engine, parse_srt, sha


def raw(label):
    return f"1\n00:00:00,000 --> 00:00:01,000\n{label}\n\n2\n00:00:00,500 --> 00:00:02,000\ncontext\n".encode()


def claim(i="a", cue=1, verdict="APPROVE", **changes):
    active = verdict in {"APPROVE", "CORRECT", "DUPLICATE"}
    data = dict(id=i, cues=[cue], topic="test-topic", statement="technical fixture, not a financial finding", speaker="fixture", time_scope="test only", reason="technical test", kind="FACT", verdict=verdict, knowledge="test-token" if active else "", evidence=[dict(issuer="test fixture", title="not real evidence", url="https://example.invalid/test", checked_on="2026-11-27", applies_on="test only", scope="test only", excerpt="synthetic", access="TEST")] if active else [], conditions=["test-condition"], exceptions=["test-exception"], numbers=[], depends_on=[], relations=[])
    data.update(changes)
    return data


def packet(p, claims, nonclaim=None):
    used = {i for x in claims for i in x["cues"]}
    rest = [x["id"] for x in p["cues"] if x["id"] not in used]
    return dict(mode=p["mode"], source_id=p["source_id"], head=p["head"], claims=claims, nonclaim=nonclaim if nonclaim is not None else ([dict(cues=rest, reason="technical coverage fixture only; not semantic review")] if rest else []), review_note="D1 mechanical test, not a completed research review")


def draft(e, p, claims):
    d = packet(p, claims)
    e.save_draft(d)
    r = e.resume(p["source_id"], ["test-token"])
    assert r["draft"] == d
    return dict(d, draft_sha=r["draft_sha"])


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"
        self.e = Engine(self.path, "test")

    def prepared(self, label="first"):
        return self.e.prepare(raw(label), ["test-token"])

    def first(self):
        p = self.prepared()
        f = draft(self.e, p, [claim()])
        self.e.finalize(f)
        return p["source_id"] + ":a", f

    def test_parser(self):
        self.assertEqual(len(parse_srt(raw("a"))), 2)
        self.assertEqual(parse_srt(raw("a"))[1]["start_ms"], 500)
        for b in [b"", b"broken", raw("a").replace(b"\n2\n", b"\n3\n"), raw("a").replace(b"00:00:01,000", b"00:00:00,000")]:
            with self.assertRaises(ValueError):
                parse_srt(b)

    def test_empty_research_and_mode(self):
        prod = Engine(Path(self.tmp.name) / "research.db")
        self.assertEqual(prod.status()["active"], 0)
        self.assertEqual(prod.query(["test-token"])["candidates"], [])
        with self.assertRaises(ValueError):
            Engine(self.path)
        p = prod.prepare(raw("prod"), [])
        with self.assertRaises(ValueError):
            prod.save_draft(packet(p, [claim()]))

    def test_two_turn_and_retry(self):
        p = self.prepared()
        self.assertEqual(self.e.prepare(raw("first"), [] )["source_id"], p["source_id"])
        f = draft(self.e, p, [claim(), claim("b", 2, "CONTEXT", kind="OPINION", topic="hidden-token")])
        e = Engine(self.path, "test")
        self.assertEqual(e.query(["test-token"])["candidates"], [])
        receipt = e.finalize(f)
        self.assertEqual(e.finalize(f), receipt)
        self.assertEqual(e.status()["finalized"], 1)
        self.assertEqual(e.status()["active"], 1)
        result = e.query(["test-token"])["candidates"][0]["item"]
        self.assertEqual(result["source"], [p["cues"][0]])
        self.assertEqual(result["conditions"], ["test-condition"])
        self.assertEqual(result["exceptions"], ["test-exception"])
        self.assertEqual(e.query(["hidden-token"])["candidates"], [])
        self.assertEqual(e.query(["unrelated"])["candidates"], [])
        with self.assertRaises(ValueError):
            e.finalize(dict(f, review_note="changed"))

    def test_reject_invalid_final(self):
        p = self.prepared()
        f = draft(self.e, p, [claim()])
        variants = [dict(f, draft_sha="wrong"), dict(f, head="wrong"), dict(f, nonclaim=[]), dict(f, claims=[claim(cue=3)]), dict(f, claims=[claim(kind="OPINION")]), dict(f, claims=[claim(evidence=[])]), dict(f, claims=[claim(depends_on=["missing"])]), dict(f, claims=[claim(depends_on=["b"]), claim("b", 2, "HOLD")], nonclaim=[]), dict(f, claims=[claim(depends_on=["b"]), claim("b", 2, depends_on=["a"])], nonclaim=[])]
        before = self.e.status()
        for bad in variants:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.e.finalize(bad)
                self.assertEqual(self.e.status(), before)

    def test_rollback_after_first_insert(self):
        p = self.prepared()
        f = draft(self.e, p, [claim(), claim("b", 2)])
        before = self.e.status()
        with self.e.db(True) as c:
            c.execute("CREATE TRIGGER fail_second BEFORE INSERT ON items WHEN NEW.id LIKE '%:b' BEGIN SELECT RAISE(ABORT,'forced failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.e.finalize(f)
        self.assertEqual(self.e.status(), before)
        self.assertIsNone(self.e.resume(p["source_id"], [])["final"])
        with self.e.db(True) as c:
            c.execute("DROP TRIGGER fail_second")
        self.e.finalize(f)
        self.assertEqual(self.e.status()["active"], 2)

    def test_integration_and_correction(self):
        k, _ = self.first()
        p = self.prepared("second")
        self.assertEqual(len(p["candidates"]), 1)
        duplicate = claim(verdict="DUPLICATE", relations=[dict(type="SAME", target=k, reason="test equivalence")])
        extension = claim("b", 2, knowledge="extension-token", depends_on=[k], relations=[dict(type="EXTENDS", target=k, reason="test extension")])
        self.e.finalize(draft(self.e, p, [duplicate, extension]))
        result = self.e.query(["test-token"])["candidates"][0]
        self.assertEqual(len(result["additional_sources"]), 1)
        self.assertEqual(self.e.query(["extension-token"])["candidates"][0]["dependencies"][0]["qualified_id"], k)
        q = self.prepared("third")
        correction = claim(verdict="CORRECT", knowledge="corrected-token", relations=[dict(type="CORRECTS", target=k, reason="test correction")])
        self.e.finalize(draft(self.e, q, [correction]))
        self.assertEqual(self.e.status()["decisions"], 4)
        self.assertEqual(self.e.status()["active"], 1)
        self.assertEqual(self.e.query(["test-token", "extension-token"])["candidates"], [])
        self.assertEqual(len(self.e.query(["corrected-token"])["candidates"]), 1)
        self.assertIsNotNone(self.e.resume(k.split(":")[0], [])["final"])

    def test_conflict_and_stale_head(self):
        k, _ = self.first()
        a = self.prepared("pending")
        f = draft(self.e, a, [claim()])
        b = self.prepared("conflict")
        hold = claim(verdict="HOLD", relations=[dict(type="CONFLICTS", target=k, reason="test unresolved conflict")])
        self.e.finalize(draft(self.e, b, [hold]))
        self.assertEqual(self.e.status()["active"], 0)
        with self.assertRaises(ValueError):
            self.e.finalize(f)
        f["head"] = self.e.resume(a["source_id"], [])["head"]
        self.e.finalize(f)
        self.assertEqual(self.e.status()["active"], 1)

    @unittest.skipUnless(os.environ.get("SRT_DIR"), "SRT_DIR not provided")
    def test_actual_srt_transport(self):
        paths = sorted(Path(os.environ["SRT_DIR"]).glob("*.srt"))
        self.assertTrue(paths)
        for p in paths:
            data = p.read_bytes()
            prepared = self.e.prepare(data, [])
            self.assertEqual(prepared["source_id"], sha(data))
            self.assertEqual(prepared["cues"], parse_srt(data))
            f = draft(self.e, prepared, [claim(), claim("b", 2, "HOLD", topic="hold-token")])
            reopened = Engine(self.path, "test")
            reopened.finalize(f)
            self.assertEqual(reopened.resume(prepared["source_id"], [])["final"], f)
            self.assertEqual(reopened.query(["hold-token"])["candidates"], [])
        self.assertEqual(self.e.status()["finalized"], len(paths))
        self.assertEqual(self.e.status()["active"], len(paths))
        with self.e.db() as c:
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
