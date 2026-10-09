#!/usr/bin/env python3
"""
Finer-grained visual cues INSIDE a clause, without splitting it.

refine_clauses.py marks structure by cutting a paragraph into typed clauses. That works at
the top level, but stops at two places: a list item (cutting it would split one item into
several boxes) and a parenthetical aside (cutting through a nested paren would leave an
unmatched bracket — the "balance" the splitter is deliberately bounded to protect). So the
inside of those two was left unanalysed.

This pass leaves every clause's text and boundaries untouched and instead records
`cues`: [{type, start, end}] character ranges over the clause's own text. Ranges are only
ever drawn between points at the SAME paren depth (or around a whole balanced paren), so
they always nest properly — a cue can contain a whole aside, or sit inside one, but never
straddle a bracket. The renderer draws them as stacked colored underlines.

Detected (both languages, at every paren depth):
  - exception   a whole aside that excludes:  (…を除く。)  / (excluding …)
  - limitation  a whole aside that restricts: (…に限る。)  / (limited to …)
  - definition  a whole aside that defines:   (…をいう。…) / (meaning …) / (hereinafter …)
  - conditional a sentence-opening condition up to 場合には、/ときは、 / "Where …, "
  - proviso     ただし、… to the end of its sentence / "provided, however, that …"

Pure post-processing, no model calls, idempotent (cues are recomputed from scratch on
every run). Run after refine_clauses.py.

Usage:
    python3 annotate_cues.py <feed_id> <chapter_id>
"""
import json
import re
import sys
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"

OPEN, CLOSE = "(（", ")）"

# Item markers at the very start of an enumeration clause (一 / 二の二 / イ / (1) / (i) / (a)).
# Only used to start a sentence-opening condition AFTER the marker, so a loose match here
# can at worst shift a cue start by one character — it never affects the text itself.
JA_MARKER_RE = re.compile(r"^(?:[一二三四五六七八九十]+(?:の[一二三四五六七八九十]+)?|[イロハニホヘトチリヌルヲワカヨタレソツネナラム]|[(（][0-9０-９]+[)）])")
EN_MARKER_RE = re.compile(r"^\((?:[ivxl]+|[a-z]|\d+)(?:-\d+)?\)\s*")

JA_COND_TRIGGERS = ("場合においては、", "場合においても、", "場合において、", "場合には、", "場合は、", "ときは、", "ときには、")
EN_COND_START_RE = re.compile(r"(?:Where|When|If|In (?:the )?cases? (?:where|in which)|In the event that)\b")


def depths(text):
    """depth[i] = paren depth at character i, counting a bracket itself as inside."""
    out, d = [], 0
    for ch in text:
        if ch in OPEN:
            d += 1
            out.append(d)
        elif ch in CLOSE:
            out.append(d)
            d = max(0, d - 1)
        else:
            out.append(d)
    return out


def balanced_spans(text):
    """All balanced paren spans (start, end_exclusive, depth_of_brackets), any depth."""
    spans, stack = [], []
    for i, ch in enumerate(text):
        if ch in OPEN:
            stack.append(i)
        elif ch in CLOSE and stack:
            s = stack.pop()
            spans.append((s, i + 1, len(stack) + 1))
    return spans


def own_level(text, s, e, dep):
    """The aside's content with nested asides removed (keeps only its own depth level)."""
    level = dep[s]
    return "".join(ch for i, ch in enumerate(text[s + 1:e - 1], start=s + 1) if dep[i] == level)


def paren_cues(text, dep, lang):
    cues = []
    for s, e, _ in balanced_spans(text):
        inner = own_level(text, s, e, dep).strip()
        if lang == "ja":
            if re.search(r"を除く。(?:以下[^。]*。)?$", inner):
                t = "exception"
            elif re.search(r"に限る。(?:以下[^。]*。)?$", inner):
                t = "limitation"
            elif "をいう。" in inner or re.fullmatch(r"以下[^。]*「[^」]+」(?:と総称する|という)。", inner):
                t = "definition"
            else:
                continue
        else:
            low = inner.lower()
            if low.startswith("excluding"):
                t = "exception"
            elif low.startswith("limited to"):
                t = "limitation"
            elif low.startswith(("meaning", "hereinafter", "referred to as")):
                t = "definition"
            else:
                continue
        cues.append((s, e, t))
    return cues


def containers(text, dep):
    """Regions whose own-level text is scanned for sentence cues: the clause itself
    (depth 0) and the interior of every balanced aside."""
    yield 0, len(text), 0
    for s, e, d in balanced_spans(text):
        yield s + 1, e - 1, d


def sentence_starts(text, dep, a, b, level, lang):
    """Offsets in [a, b) at `level` where a sentence begins: the region start (after an
    item marker, if any), and right after each 。 / ". " at that level."""
    first = a
    head = text[a:b]
    m = (JA_MARKER_RE if lang == "ja" else EN_MARKER_RE).match(head)
    if m and a == 0:
        first = a + m.end()
    while first < b and text[first] in " 　":
        first += 1
    starts = [first]
    for i in range(a, b):
        if dep[i] != level:
            continue
        if lang == "ja" and text[i] == "。" and i + 1 < b:
            starts.append(i + 1)
        elif lang == "en" and text[i] in ".:;" and i + 2 < b and text[i + 1] == " ":
            starts.append(i + 2)
    return starts


def sentence_end(text, dep, i, b, level, lang):
    for j in range(i, b):
        if dep[j] == level and ((lang == "ja" and text[j] == "。") or (lang == "en" and text[j] in ".;" and (j + 1 == b or text[j + 1] == " "))):
            return j + 1
    return b


def sentence_cues(text, dep, lang):
    cues = []
    for a, b, level in containers(text, dep):
        for st in sentence_starts(text, dep, a, b, level, lang):
            end = sentence_end(text, dep, st, b, level, lang)
            if lang == "ja":
                if text.startswith("ただし、", st):
                    cues.append((st, end, "proviso"))
                    continue
                # Earliest condition trigger at this level, within this sentence.
                best = None
                for trig in JA_COND_TRIGGERS:
                    k = st
                    while True:
                        k = text.find(trig, k, end)
                        if k == -1:
                            break
                        if dep[k] == level:
                            if best is None or k < best[0]:
                                best = (k, k + len(trig))
                            break
                        k += 1
                if best:
                    cues.append((st, best[1], "conditional"))
            else:
                k = text.lower().find("provided, however, that", st, end)
                if k != -1 and dep[k] == level:
                    cues.append((k, end, "proviso"))
                if EN_COND_START_RE.match(text, st):
                    comma = next((j for j in range(st, end) if dep[j] == level and text[j] == ","
                                  and not text.startswith(" etc.", j + 1)), None)
                    if comma is not None:
                        cues.append((st, comma + 2 if text[comma + 1:comma + 2] == " " else comma + 1, "conditional"))
    return cues


def is_nested_properly(cues):
    for i, (s1, e1, _) in enumerate(cues):
        for s2, e2, _ in cues[i + 1:]:
            if s1 < s2 < e1 < e2 or s2 < s1 < e2 < e1:
                return False
    return True


def annotate(clause, lang):
    text = clause["text"]
    if not text:
        return []
    dep = depths(text)
    raw = paren_cues(text, dep, lang) + sentence_cues(text, dep, lang)
    out = []
    for s, e, t in sorted(set(raw), key=lambda c: (c[0], -c[1])):
        whole = s == 0 and e == len(text)
        if whole and t == clause["clause_type"]:
            continue  # the clause itself already says this
        if e - s < 2:
            continue
        out.append((s, e, t))
    if not is_nested_properly(out):
        # Can't happen by construction (every range is level-bounded), but never emit a
        # crossing pair — drop to the paren-only cues, which are always nested.
        out = [c for c in out if c[2] in ("exception", "limitation", "definition")]
    return [{"type": t, "start": s, "end": e} for s, e, t in out]


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id = sys.argv[1:3]
    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)

    counts = {}
    for node in walk(chapter):
        for lang in ("ja", "en"):
            for clause in node.get(f"clauses_{lang}", []):
                cues = annotate(clause, lang)
                if cues:
                    clause["cues"] = cues
                    for c in cues:
                        key = (lang, clause["clause_type"], c["type"])
                        counts[key] = counts.get(key, 0) + 1
                else:
                    clause.pop("cues", None)

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    print("cues written (lang, inside clause type, cue type): count")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"\nWrote {feed_path}")


if __name__ == "__main__":
    main()
