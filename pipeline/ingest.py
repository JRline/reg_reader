#!/usr/bin/env python3
"""
Merges chatbot-populated raw chunk JSON (pipeline/raw/*.json) into a feed.json
that conforms to schema/rule-feed.schema.json.

What the chatbot is trusted to do: translate, type clauses (in both languages
independently), spot citation phrases (in both languages, including inside
parenthetical asides). What this script does instead of trusting the chatbot:
- resolve citation phrases into actual node ids, deterministically
- look up one-line summaries for external references from a shared registry
- verify every ref actually occurs in the text it claims to come from (QA gate)
- verify clause reconstruction in both languages (QA gate)

Usage:
    python3 ingest.py <feed_id> <article_id> <chapter_number> <chapter_heading>

Example:
    python3 ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2.art3 第二章 算式等
"""
import json
import re
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent
RAW_DIR = PIPELINE_DIR / "raw"
SCHEMA_PATH = PIPELINE_DIR / "schema" / "rule-feed.schema.json"
FEEDS_DIR = PIPELINE_DIR.parent / "feeds"
SHARED_EXTERNAL_REFS_PATH = FEEDS_DIR / "_shared" / "external_refs.json"

# Article headings/numbers aren't in the raw paragraph chunks (they belong to the article,
# not any one paragraph) — a real pipeline would read this from a document outline extracted
# once from the PDF's heading markup. Hardcoded here for this test.
ARTICLE_META = {
    "fsa-basel-cap-jp.ch2.art3": {"number": "第三条", "heading": "連結の範囲", "heading_en": "Scope of Consolidation"},
}


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_json_if_exists(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_raw_paragraphs(article_id: str):
    pattern = re.compile(re.escape(article_id) + r"\.p(\d+)\.json$")
    matches = []
    for f in RAW_DIR.glob(f"{article_id}.p*.json"):
        m = pattern.search(f.name)
        if m:
            matches.append((int(m.group(1)), f))
    matches.sort(key=lambda x: x[0])
    if not matches:
        raise SystemExit(f"No raw chunks found for {article_id} in {RAW_DIR}")
    return [json.loads(f.read_text(encoding="utf-8")) for _, f in matches]


def load_term_registry(feed_id: str):
    path = FEEDS_DIR / feed_id / "term_registry.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_comment", None)
        return data, path
    return {}, path


def save_term_registry(registry: dict, path: Path):
    out = {"_comment": "Document-wide shorthand terms. See ingest.py."}
    out.update(registry)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def load_external_refs_registry():
    data = load_json_if_exists(SHARED_EXTERNAL_REFS_PATH) or {}
    data.pop("_comment", None)
    return data


INTERNAL_REF_PATTERNS = [
    (re.compile(r"^前二項"), 2),
    (re.compile(r"^前項"), 1),
]


def resolve_internal_ref(raw_text: str, siblings: list, index: int):
    for pattern, count in INTERNAL_REF_PATTERNS:
        if pattern.match(raw_text):
            if index - count < 0:
                return []  # would cross into a preceding article — not loaded in this test
            return [siblings[i] for i in range(index - count, index)]
    return []


def resolve_external_name(raw_text: str, term_registry: dict):
    """If raw_text starts with a known document-wide shorthand term, expand it to the
    term's full JAPANESE name. Deliberately does NOT fall back to term_en — that's an
    English translation, and falling back to it here would put English text into a
    field (external_name) that the rest of the pipeline treats as Japanese (e.g. as the
    lookup key into feeds/_shared/external_refs.json, which is keyed in Japanese)."""
    for term_ja in sorted(term_registry.keys(), key=len, reverse=True):
        if raw_text.startswith(term_ja) and term_registry[term_ja].get("expands_to"):
            return term_registry[term_ja]["expands_to"]
    return None


def process_ref(ref: dict, siblings: list, index: int, feed_id: str, term_registry: dict,
                 external_refs_registry: dict, node_id: str, warnings: list):
    ref = dict(ref)
    ref.setdefault("target_ids", [])

    if ref["scope"] == "internal":
        targets = resolve_internal_ref(ref["raw_text"], siblings, index)
        if targets:
            ref["target_ids"] = targets
            ref["target_feed"] = feed_id
            ref["resolution_status"] = "resolved"
        else:
            ref["target_feed"] = None
            ref["resolution_status"] = "unresolved"
    else:  # external
        if not ref.get("external_name"):
            resolved = resolve_external_name(ref["raw_text"], term_registry)
            if resolved:
                ref["external_name"] = resolved
        already_linked = ref.get("target_feed") and ref.get("target_ids")
        if already_linked:
            # Content author has digitized this external law and pre-linked it
            # (e.g. via a manually-built feed, not this script) — don't clobber that.
            ref["resolution_status"] = "resolved"
        else:
            ref["target_feed"] = None
            ref["target_ids"] = []
            ref["resolution_status"] = (
                "external_unavailable" if ref.get("external_name") else "unresolved"
            )
        name_entry = external_refs_registry.get(ref.get("external_name") or "")
        ref["external_name_en"] = name_entry["name_en"] if name_entry else None
        if ref.get("external_name") and not name_entry:
            warnings.append(
                f"{node_id}: no entry in feeds/_shared/external_refs.json for "
                f"external_name='{ref['external_name']}' — add one so the English name resolves"
            )
        cites_specific_provision = re.search(r"[条項号]", ref["raw_text"])
        if cites_specific_provision and not ref.get("external_item_summary_ja"):
            warnings.append(
                f"{node_id}: ref '{ref['raw_text']}' cites a specific provision but has no "
                f"external_item_summary — the chatbot should describe what THAT citation covers"
            )
        ref.setdefault("external_item_summary_ja", None)
        ref.setdefault("external_item_summary_en", None)
        ref.setdefault("external_item_summary_confidence", None)

    return ref


def check_reconstruction(clauses: list, full_text: str, label: str, node_id: str, warnings: list):
    if not clauses:
        return
    joined = "".join(c["text"] for c in clauses)
    if joined != full_text:
        warnings.append(f"{node_id}: {label} clause concatenation does NOT match {label} text — flag for review")


def check_refs_present(refs: list, text_ja: str, text_en: str, node_id: str, warnings: list):
    for r in refs:
        if r["raw_text"] not in text_ja:
            warnings.append(
                f"{node_id}: ref raw_text '{r['raw_text']}' was NOT found verbatim in text_ja "
                f"(including inside parentheses) — likely a fabricated/incorrect citation, fix the raw chunk"
            )
        if r.get("text_en") and text_en and r["text_en"] not in text_en:
            warnings.append(
                f"{node_id}: ref text_en '{r['text_en']}' was NOT found verbatim in text_en — "
                f"the English anchor won't be clickable, fix the raw chunk"
            )


INTERNAL_REF_HINT_RE = re.compile(r"(前[条項]|次[条項]|第[一二三四五六七八九十百]+[条項号])")


def check_not_a_placeholder(node: dict, warnings: list):
    """Catches raw chunks that were never actually processed by a model — e.g. a script
    that mechanically wrapped text_ja into one clause and left everything else blank.
    check_reconstruction alone can't catch this: an empty text_en trivially 'reconstructs'
    against an empty clause list, so a null translation sails through that check silently."""
    node_id = node["id"]
    text_ja = node.get("text_ja") or ""
    text_en = node.get("text_en") or ""

    if text_ja and not text_en.strip():
        warnings.append(
            f"{node_id}: text_en is EMPTY while text_ja has content — this chunk was never "
            f"actually translated. Re-run it through the chatbot; do not ingest as-is."
        )
        return  # the checks below are redundant noise once this one has fired

    clauses_ja = node.get("clauses_ja") or []
    if len(clauses_ja) <= 1 and len(text_ja) > 120:
        warnings.append(
            f"{node_id}: {len(text_ja)}-character text_ja was broken into only "
            f"{len(clauses_ja)} clause(s) — suspiciously coarse for a paragraph this long, "
            f"check whether clause segmentation actually ran"
        )

    if not node.get("refs") and INTERNAL_REF_HINT_RE.search(text_ja):
        warnings.append(
            f"{node_id}: text_ja contains what looks like a citation (前項/前条/第◯条 style) "
            f"but refs is empty — check whether ref extraction actually ran"
        )


def build_article_node(article_id: str, feed_id: str, term_registry: dict,
                        external_refs_registry: dict):
    raw_paragraphs = load_raw_paragraphs(article_id)
    sibling_ids = [f"{article_id}.p{i+1}" for i in range(len(raw_paragraphs))]

    children = []
    warnings = []
    for i, raw in enumerate(raw_paragraphs):
        node = dict(raw)
        node["type"] = "paragraph"
        node.setdefault("translation_status", "llm_draft")
        node["children"] = []

        check_reconstruction(node.get("clauses_ja", []), node["text_ja"], "ja", node["id"], warnings)
        check_reconstruction(node.get("clauses_en", []), node["text_en"], "en", node["id"], warnings)
        check_refs_present(node.get("refs", []), node["text_ja"], node.get("text_en", ""), node["id"], warnings)
        check_not_a_placeholder(node, warnings)

        node["refs"] = [
            process_ref(r, sibling_ids, i, feed_id, term_registry, external_refs_registry, node["id"], warnings)
            for r in node.get("refs", [])
        ]

        for term in node.get("defined_terms", []):
            term.setdefault("definition_node_id", node["id"])
            term.setdefault("expands_to_ja", None)
            if term["term_ja"] not in term_registry:
                term_registry[term["term_ja"]] = {
                    "term_en": term.get("term_en"),
                    "expands_to": term.get("expands_to_ja"),
                    "defined_at": node["id"],
                }

        children.append(node)

    meta = ARTICLE_META.get(article_id, {"number": None, "heading": None, "heading_en": None})
    summary = load_json_if_exists(RAW_DIR / f"{article_id}.summary.json") or {}

    article_node = {
        "id": article_id,
        "type": "article",
        "number": meta["number"],
        "heading": meta["heading"],
        "heading_en": meta.get("heading_en"),
        "text_ja": None,
        "text_en": None,
        "summary_ja": summary.get("summary_ja"),
        "summary_en": summary.get("summary_en"),
        "translation_status": "pending",
        "clauses_ja": [],
        "clauses_en": [],
        "refs": [],
        "defined_terms": [],
        "children": children,
    }
    if not summary:
        warnings.append(f"{article_id}: no {article_id}.summary.json found — run the second-stage summary template")

    return article_node, warnings


def merge_into_feed(feed_id: str, chapter_id: str, chapter_number: str, chapter_heading: str, article_node: dict):
    feed_path = FEEDS_DIR / feed_id / "feed.json"
    if feed_path.exists():
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
    else:
        feed = {
            "feed_id": feed_id,
            "root": {
                "id": feed_id, "type": "document", "number": None, "heading": None,
                "text_ja": None, "text_en": None, "children": [],
            },
        }

    root = feed["root"]
    chapter = next((c for c in root["children"] if c["id"] == chapter_id), None)
    if chapter is None:
        chapter = {
            "id": chapter_id, "type": "chapter", "number": chapter_number, "heading": chapter_heading,
            "text_ja": None, "text_en": None, "clauses_ja": [], "clauses_en": [],
            "refs": [], "defined_terms": [], "children": [],
        }
        root["children"].append(chapter)

    existing_idx = next((i for i, a in enumerate(chapter["children"]) if a["id"] == article_node["id"]), None)
    if existing_idx is not None:
        chapter["children"][existing_idx] = article_node
    else:
        chapter["children"].append(article_node)

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    return feed, feed_path


def validate(feed: dict, schema: dict):
    try:
        import jsonschema
    except ImportError:
        print("(jsonschema not installed — skipping formal validation)")
        return
    jsonschema.validate(instance=feed, schema=schema)
    print("Schema validation: PASSED")


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    feed_id, article_id, chapter_number, chapter_heading = sys.argv[1:5]
    chapter_id = f"{feed_id}.{article_id.split('.')[1]}"

    schema = load_schema()
    term_registry, term_registry_path = load_term_registry(feed_id)
    external_refs_registry = load_external_refs_registry()

    article_node, warnings = build_article_node(article_id, feed_id, term_registry, external_refs_registry)
    feed, feed_path = merge_into_feed(feed_id, chapter_id, chapter_number, chapter_heading, article_node)
    save_term_registry(term_registry, term_registry_path)

    print(f"Merged {article_id} into {feed_path}")
    if article_node["summary_en"]:
        print(f"Summary: {article_node['summary_en']}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\nNo warnings.")

    print("\nReference resolution summary:")
    for p in article_node["children"]:
        for r in p["refs"]:
            extra = ""
            if r.get("external_item_summary_en"):
                extra = f" | item_summary[{r.get('external_item_summary_confidence')}]={r['external_item_summary_en']}"
            print(f"  [{p['id']}] \"{r['raw_text']}\" -> "
                  f"scope={r['scope']} status={r['resolution_status']} "
                  f"target_ids={r.get('target_ids')} external_name={r.get('external_name')}{extra}")

    print()
    validate(feed, schema)


if __name__ == "__main__":
    main()
