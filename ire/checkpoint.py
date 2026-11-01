"""Private, resumable semantic model checkpoints.

Every cached response is pinned to source, prompt, model and exact discourse
window. Private raw model output never enters Git or the public CI artifact.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import secrets
from .source import require,sha256,DIGEST

PROJECT_ROOT=Path(__file__).resolve().parents[1]


def safe_private_directory(value: str) -> Path:
    require(type(value) is str and bool(value),
            "SEMANTIC_CHECKPOINT_PATH_REQUIRED")
    path=Path(value).expanduser().resolve()
    require(not path.is_relative_to(PROJECT_ROOT),
            "CHECKPOINT_INSIDE_REPOSITORY_FORBIDDEN")
    if path.exists():
        require(path.is_dir() and
                path.stat().st_mode & 0o077 == 0,
                "CHECKPOINT_PRIVATE_DIRECTORY_PERMISSIONS_INVALID")
    else:
        path.mkdir(parents=True,mode=0o700)
    return path


def atomic_private_json(location: Path, value: dict) -> None:
    require(type(value) is dict, "CHECKPOINT_JSON_OBJECT_REQUIRED")
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,
                   separators=(",",":"),allow_nan=False).encode("utf-8")
    require(len(raw)<4_000_000, "SEMANTIC_MODEL_CHECKPOINT_OVERSIZE")
    temp=location.with_name(location.name+"."+secrets.token_hex(8)+".tmp")
    fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp,location)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


class SemanticCheckpointLedger:
    def __init__(self, directory: str, video_id: str,
                 source_sha: str, model_name: str, prompt_sha: str,
                 windows: list[dict]):
        root=safe_private_directory(directory)
        expected={
            "schema":"IRE_SEMANTIC_CHECKPOINT_V1",
            "video_id":video_id,
            "source_sha256":source_sha,
            "model_sha256":sha256(model_name.encode("utf-8")),
            "prompt_sha256":prompt_sha,
            "discourse_window_census":len(windows),
            "discourse_window_hashes":[
                {"window_id":x["window_id"],
                 "source_cue_ids":x["source_cue_ids"],
                 "source_text_sha256":x["source_text_sha256"]}
                for x in windows]
        }
        stem=sha256(json.dumps(expected,sort_keys=True,
                ensure_ascii=False).encode("utf-8"))[:24]
        self.folder=root/stem
        if self.folder.exists():
            require(self.folder.stat().st_mode & 0o077 ==0,
                    "CHECKPOINT_PRIVATE_DIRECTORY_PERMISSIONS_INVALID")
        else:
            self.folder.mkdir(mode=0o700)
        location=self.folder/"manifest.json"
        if location.exists():
            require(json.loads(location.read_text(encoding="utf-8"))==
                    expected,"CHECKPOINT_MODEL_SOURCE_OR_WINDOW_DRIFT")
        else:
            atomic_private_json(location,expected)
        self.valid_windows={x["window_id"]:x["source_text_sha256"]
                            for x in windows}

    def read(self, window: dict) -> dict | None:
        name=window["window_id"]
        require(name in self.valid_windows,"CHECKPOINT_UNKNOWN_WINDOW")
        where=self.folder/(name+".json")
        if not where.exists():return None
        value=json.loads(where.read_text(encoding="utf-8"))
        require(type(value) is dict and set(value)=={
            "source_text_sha256","model_response"},
            "CHECKPOINT_WINDOW_SCHEMA_INVALID")
        require(value["source_text_sha256"]==self.valid_windows[name],
                "CHECKPOINT_CUE_HASH_CHANGED")
        require(type(value["model_response"]) is dict,
                "CHECKPOINT_RESPONSE_NOT_OBJECT")
        return value["model_response"]

    def save(self, window: dict, model_response: dict) -> None:
        name=window["window_id"]
        require(name in self.valid_windows and
                self.valid_windows[name]==window["source_text_sha256"],
                "CHECKPOINT_UNKNOWN_OR_CHANGED_WINDOW")
        where=self.folder/(name+".json")
        require(not where.exists(),"CHECKPOINT_OVERWRITE_FORBIDDEN")
        atomic_private_json(where,{
            "source_text_sha256":self.valid_windows[name],
            "model_response":model_response
        })
