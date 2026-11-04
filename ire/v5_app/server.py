"""Loopback-only V5 application server.

Use on an operator-controlled host with a V5 private store restored from an
AES-GCM encrypted checkpoint. No cloud deployment or external LLM API.

ChatGPT, via user-authorized local/desktop tools, fetches /v1/next, performs
source interpretation, official research and prior-knowledge review, then
posts the V5 event. Python may validate/record, never invent financial claims.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import threading
from typing import Callable

from ire.v5.engine import ResearchRun, RunError, sha256, canonical, require
from ire.v5.portable import reopen_private_store

MAX_EVENT_BYTES = 200_000
KINDS = {"MODEL_ANALYSIS_REQUIRED": "MODEL_ANALYSIS",
         "MODEL_CORRECTION_REQUIRED": "MODEL_CORRECTION",
         "OFFICIAL_EVIDENCE_REVIEW_REQUIRED": "EVIDENCE_REVIEW",
         "PRIOR_KNOWLEDGE_REVIEW_REQUIRED": "PRIOR_RELATION_REVIEW"}


class AppCore:
    """Reopens the verified chain on every operation and uses CAS receipt heads."""
    def __init__(self, private_store: str | Path):
        self.root = Path(private_store).expanduser().resolve()
        self._mutex = threading.Lock()
        self._load()

    def _load(self) -> ResearchRun:
        return reopen_private_store(self.root)

    def state(self) -> dict:
        with self._mutex:
            run = self._load()
            return {"schema": "IRE_V5_LOCAL_APP_STATE_V1", "research": run.status(),
                    "next_phase": run.next_task()["phase"]}

    def next_task(self) -> dict:
        with self._mutex:
            return self._load().next_task()

    def next_bundle(self) -> dict:
        """At most 8 source packets; no model calls or automatic answers."""
        with self._mutex:
            run=self._load()
            pending=[wid for wid in run.active if wid not in run.model]
            task=run.next_task()
            return {"schema":"IRE_V5_APP_SOURCE_BUNDLE_V1",
                    "video_id":run.manifest["video_id"],
                    "packets":[run.packet(wid) for wid in pending[:8]],
                    "pending_uninterpreted_windows":len(pending),
                    "expected_chain_head":run.head,
                    "expected_task_sha256":task["task_sha256"],
                    "next_phase":task["phase"],
                    "requires_live_chat_interpretation":True,
                    "private_source_verified_by_github":False}

    def accept(self, submitted: dict) -> dict:
        require(type(submitted) is dict and set(submitted) == {
            "event_type", "payload", "expected_chain_head", "expected_task_sha256"},
            "V5_APP_SUBMISSION_SCHEMA_INVALID")
        with self._mutex:
            run = self._load()
            task = run.next_task()
            expected_kind = KINDS.get(task["phase"])
            allowed_single=(expected_kind is not None and
                            submitted["event_type"] == expected_kind)
            allowed_batch=(expected_kind is not None and
                           submitted["event_type"]=="BATCH_ACCEPT")
            require(allowed_single or allowed_batch,"V5_APP_WRONG_PHASE")
            require(submitted["expected_chain_head"] == run.head and
                    submitted["expected_task_sha256"] == task["task_sha256"],
                    "V5_APP_STALE_TASK_OR_HEAD")
            result = run.append(submitted["event_type"], submitted["payload"])
            return {
                "schema": "IRE_V5_APP_INTAKE_V1", "accepted_event_type": submitted["event_type"],
                "receipt_sequence": result["sequence"], "receipt_sha256": result["event_sha256"],
                "next_phase": run.next_task()["phase"],
                "source_truth_certified": False, "independent_financial_fact_approved": False,
            }

    def seal(self, submitted: dict) -> dict:
        require(type(submitted) is dict and set(submitted) == {
            "expected_chain_head", "expected_task_sha256"},
            "V5_APP_SEAL_SCHEMA_INVALID")
        with self._mutex:
            run = self._load()
            task = run.next_task()
            require(task["phase"] == "SEAL_RESEARCH_REPORT_REQUIRED" and
                    submitted["expected_chain_head"] == run.head and
                    submitted["expected_task_sha256"] == task["task_sha256"],
                    "V5_APP_SEAL_BEFORE_SOURCE_REVIEW_OR_STALE")
            result = run.close()
            return {"schema": "IRE_V5_APP_SEAL_V1", "research": result,
                    "p0_full_research_go": False}


class Handler(BaseHTTPRequestHandler):
    """Never logs request bodies or authorization tokens."""
    app: AppCore
    secret: str

    def log_message(self, format: str, *args) -> None:
        pass  # structured logs must not leak private text, tokens or paths

    def _json(self, status: int, data: dict):
        encoded = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _authorized(self) -> bool:
        received = self.headers.get("Authorization", "")
        return hmac.compare_digest(received, "Bearer " + self.secret)

    def _body(self) -> dict:
        value = self.headers.get("Content-Length", "")
        if not value.isdigit() or int(value) <= 0 or int(value) > MAX_EVENT_BYTES:
            raise RunError("V5_APP_INPUT_TOO_LARGE_OR_MISSING")
        body = self.rfile.read(int(value))
        value = json.loads(body)
        require(type(value) is dict, "V5_APP_JSON_OBJECT_REQUIRED")
        return value

    def do_GET(self):
        try:
            if self.path == "/health":
                self._json(200, {"status": "operational", "model_inference_in_server": False,
                                 "github_is_an_always_on_host": False})
            elif not self._authorized():
                self._json(401, {"error": "UNAUTHORIZED"})
            elif self.path == "/v1/state":
                self._json(200, self.app.state())
            elif self.path == "/v1/next":
                self._json(200, self.app.next_task())
            elif self.path == "/v1/next-bundle":
                self._json(200, self.app.next_bundle())
            else:
                self._json(404, {"error": "NOT_FOUND"})
        except (RunError, ValueError, OSError) as e:
            self._json(409, {"error": "REPLAY_OR_STATE_REJECTED", "reason": str(e)})

    def do_POST(self):
        if not self._authorized():
            self._json(401, {"error": "UNAUTHORIZED"})
            return
        try:
            data = self._body()
            if self.path == "/v1/receipt":
                result = self.app.accept(data)
            elif self.path == "/v1/seal":
                result = self.app.seal(data)
            else:
                self._json(404, {"error": "NOT_FOUND"})
                return
            self._json(200, result)
        except (RunError, ValueError, KeyError, OSError) as e:
            self._json(409, {"error": "EVENT_REJECTED", "reason": str(e)})


def create_server(app: AppCore, secret: str, port: int) -> ThreadingHTTPServer:
    require(type(secret) is str and len(secret) >= 24,
            "V5_APP_TOKEN_REQUIRED_MIN_24_CHARS")
    require(type(port) is int and 0 <= port < 65536, "V5_APP_BAD_PORT")
    # Using a subclass avoids shared mutable global handler fields.
    local_handler = type("V5PrivateResearchHandler", (Handler,), {"app": app, "secret": secret})
    return ThreadingHTTPServer(("127.0.0.1", port), local_handler)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--store", required=True)
    p.add_argument("--port", type=int, default=8766)
    args = p.parse_args()
    secret = os.environ.get("IRE_V5_APP_TOKEN", "")
    server = create_server(AppCore(args.store), secret, args.port)
    print(json.dumps({"status": "LISTENING_LOOPBACK_ONLY",
                      "address": f"127.0.0.1:{server.server_address[1]}",
                      "external_llm_api_used": False}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
