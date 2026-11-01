"""Versioned adaptive source-cue grouping for new IRE V3 chat sessions.

This is a deterministic *window planner*, not a financial meaning extractor.
It makes bounded primary windows using pauses, financial-topic transitions,
sentence endings and size limits; all source cue IDs remain assigned exactly
once. V2 sessions never silently switch to this planner.
"""
from __future__ import annotations

import re
from .source import Cue, require, sha256
from .v3_semantic_candidates import financial_concepts

PLANNER_VERSION = "IRE_V3_ADAPTIVE_CUE_WINDOWS_20261102_B"
SENTENCE_END = re.compile(r"(?:[.!?。]|(?:습니다|입니다|됩니다|합니다|네요|어요|아요|예요|에요|죠|거든요))\s*$")


def adaptive_discourse_windows(
        cues: tuple[Cue, ...], *, min_cues: int = 5,
        max_cues: int = 18, max_chars: int = 1600,
        pause_ms: int = 2400, halo_cues: int = 3) -> list[dict]:
    """One-to-one primary cue census, flexible bounded windows.

    A completed clause plus a clear change in topic can end a window early.
    A long pause can also end a window once min_cues is satisfied. Incomplete
    clauses may continue beyond 10 cues, but never exceed max_cues/max_chars.
    Financial meaning remains for the current ChatGPT conversation to assess.
    """
    require(type(cues) is tuple and bool(cues) and
            all(type(c) is Cue for c in cues),
            "V3_ADAPTIVE_SOURCE_CUES_REQUIRED")
    require(all(type(x) is int for x in
                (min_cues, max_cues, max_chars, pause_ms, halo_cues)) and
            2 <= min_cues <= max_cues <= 30 and
            150 <= max_chars <= 5000 and 0 <= pause_ms <= 10000 and
            1 <= halo_cues <= 5,
            "V3_ADAPTIVE_CONFIG_INVALID")
    groups: list[list[Cue]] = []
    forced_continuation_groups: set[int] = set()
    current: list[Cue] = []
    total_chars = 0

    def flush():
        nonlocal current, total_chars
        if current:
            groups.append(current)
        current = []
        total_chars = 0

    for cue in cues:
        require(len(cue.text) <= max_chars,
                "V3_ADAPTIVE_SINGLE_CUE_EXCEEDS_CONTEXT_BUDGET")
        if current:
            prior = current[-1]
            gap = max(0, cue.start_ms - prior.end_ms)
            overflow = (len(current) >= max_cues or
                        total_chars + len(cue.text) + 1 > max_chars)
            left_topics = financial_concepts(
                " ".join(x.text for x in current))
            right_topics = financial_concepts(cue.text)
            clear_switch = (
                len(current) >= min_cues and
                bool(SENTENCE_END.search(prior.text)) and
                bool(left_topics) and bool(right_topics) and
                not bool(left_topics & right_topics))
            finished_pause = (len(current) >= min_cues and
                              gap >= pause_ms and
                              bool(SENTENCE_END.search(prior.text)))
            if overflow:
                # Prefer the latest complete sentence inside the bounded
                # context; carry any unfinished clause into the next window.
                # Never duplicate or lose primary cue ownership.
                cut = None
                for index in range(len(current) - 1, min_cues - 2, -1):
                    tail = current[index + 1:]
                    if (SENTENCE_END.search(current[index].text) and
                            len(tail) + 1 <= max_cues and
                            sum(len(c.text) + 1 for c in tail) +
                            len(cue.text) + 1 <= max_chars):
                        cut = index + 1
                        break
                if cut is not None and cut < len(current):
                    groups.append(current[:cut])
                    current = current[cut:]
                    total_chars = sum(len(c.text) + 1 for c in current)
                else:
                    # A hard size boundary can still split a phrase; surface
                    # its risk to chat analysis rather than claiming coverage.
                    if not SENTENCE_END.search(current[-1].text):
                        forced_continuation_groups.add(len(groups))
                    flush()
            elif clear_switch or finished_pause:
                flush()
        current.append(cue)
        total_chars += len(cue.text) + 1
    flush()

    owned = [cue.index for group in groups for cue in group]
    require(owned == [cue.index for cue in cues],
            "V3_ADAPTIVE_PRIMARY_CUE_CENSUS_MISMATCH")
    windows = []
    for pos, group in enumerate(groups):
        left = groups[pos - 1][-halo_cues:] if pos else []
        right = groups[pos + 1][:halo_cues] if pos + 1 < len(groups) else []
        text = " ".join(x.text for x in group)
        windows.append({
            "window_id": "W" + str(pos + 1).zfill(5),
            "source_cue_ids": [x.index for x in group],
            "start_ms": group[0].start_ms,
            "end_ms": group[-1].end_ms,
            "source_text": text,
            "source_text_sha256": sha256(text.encode("utf-8")),
            "left_context_cue_ids": [x.index for x in left],
            "left_context_text": " ".join(x.text for x in left),
            "right_context_cue_ids": [x.index for x in right],
            "right_context_text": " ".join(x.text for x in right),
            "semantic_interpretation": "NOT_PERFORMED",
            "completeness": "CONTEXT_ONLY_NOT_AN_ATOM",
            "continuation_boundary_review_required":
                pos in forced_continuation_groups,
        })
    return windows
