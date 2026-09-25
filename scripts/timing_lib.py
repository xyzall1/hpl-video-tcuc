"""Shared helpers: config loading, audio-tag stripping, subtitle cue splitting."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = re.compile(r"\[[^\]]*\]")


def load_config():
    cfg = json.loads((ROOT / "config.default.json").read_text())
    user = ROOT / "config.json"  # personal overrides (voice id, etc.); not shared
    if user.exists():
        _merge(cfg, json.loads(user.read_text()))
    return cfg


def _merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            _merge(a[k], v)
        else:
            a[k] = v


def strip_tags(s):
    return " ".join(TAG.sub("", s).split())


def _chunks(text, max_chars):
    """Split a sentence into subtitle chunks: prefer commas/semicolons/dashes, then word boundaries."""
    if len(text) <= max_chars:
        return [text]
    parts = re.split(r"(?<=[,;:—–])\s+", text)
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > max_chars:
            out.append(cur); cur = p
        else:
            cur = f"{cur} {p}".strip()
    out.append(cur)
    final = []
    for c in out:  # still too long: balance on words
        while len(c) > max_chars:
            words = c.split(); n = len(words)
            best = min(range(1, n), key=lambda k: abs(len(" ".join(words[:k])) - len(c) / 2))
            final.append(" ".join(words[:best])); c = " ".join(words[best:])
        final.append(c)
    return final


def split_cues(sentences, max_chars):
    """sentences: [{text, start, end, (chars, char_starts)}] -> cues [{start, end, text}].
    With character alignment, chunk start times are exact; otherwise proportional to length.
    Cues run until the next cue starts, so the pill stays up through breathing pauses."""
    cues = []
    for s in sentences:
        chunks = _chunks(s["text"], max_chars)
        starts = []
        if s.get("chars"):
            # rebuild the tag-free spoken string with a map back to char times
            raw = "".join(s["chars"]); keep, times = [], []
            depth = 0
            for ch, t in zip(raw, s["char_starts"]):
                if ch == "[": depth += 1; continue
                if ch == "]": depth = max(0, depth - 1); continue
                if depth == 0:
                    keep.append(ch); times.append(t)
            spoken = "".join(keep)
            pos = 0
            for c in chunks:
                first = c.split()[0]
                i = spoken.find(first, pos)
                if i < 0:
                    starts.append(None); continue
                starts.append(times[i]); pos = i + len(first)
        n = sum(len(c) for c in chunks)
        acc = 0
        for k, c in enumerate(chunks):
            prop = s["start"] + (s["end"] - s["start"]) * acc / n
            st = starts[k] if k < len(starts) and starts[k] is not None else prop
            if k == 0:
                st = s["start"]
            cues.append({"start": round(st, 3), "text": c})
            acc += len(c)
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else sentences[-1]["end"] + 0.4
        c["end"] = round(nxt, 3)
    return cues
