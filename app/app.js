// Generic regulation-feed reader. Contains no FSA/Basel-specific logic —
// everything here is driven by the shape defined in pipeline/schema/rule-feed.schema.json.

const state = {
  feedId: null,
  feed: null,      // { feed_id, root }
  manifest: null,
  byId: new Map(),  // node id -> { node, parent, ancestors: [ids] }
  lang: "ja",       // "ja" | "en" — mutually exclusive, no side-by-side
  activeArticleId: null,
  backStack: [],    // [{feedId, articleId}] — populated when a ref click jumps to a different feed
};

const els = {
  feedPicker: document.getElementById("feed-picker"),
  toc: document.getElementById("toc"),
  reader: document.getElementById("reader"),
  toggleClauses: document.getElementById("toggle-clauses"),
  popover: document.getElementById("ref-popover"),
  langButtons: document.querySelectorAll(".lang-btn"),
  legend: document.getElementById("legend"),
  backBtn: document.getElementById("back-btn"),
  stickyTop: document.querySelector(".sticky-top"),
};

const CLAUSE_LEGEND = [
  ["conditional", "condition (場合/とき)", "条件（場合／とき）"],
  ["proviso", "proviso (ただし)", "ただし書き"],
  ["exception", "exception", "例外"],
  ["enumeration_item", "list item", "列挙項目"],
  ["parenthetical", "parenthetical", "かっこ書き"],
  ["definition", "defines a term", "用語の定義"],
];

const UI_STRINGS = {
  cues: { ja: "視覚キュー", en: "Cues" },
  textSmaller: { ja: "文字を小さく", en: "Smaller text" },
  textLarger: { ja: "文字を大きく", en: "Larger text" },
  toggleDark: { ja: "ダークモード切替", en: "Toggle dark mode" },
  selectFeed: { ja: "規則を選択", en: "Select regulation" },
  notYetProcessed: {
    ja: "この条文はまだパイプラインで処理されていません（目次には表示されますが、内容は未投入です）。",
    en: "This article hasn't been through the content pipeline yet — it's in the table of contents for navigation, but has no populated text.",
  },
};

// Deterministic kanji-numeral -> Arabic conversion, for displaying article/chapter numbers
// in English without needing a translated copy of every number (e.g. '第十一条の二' -> 'Article 11-2').
const KANJI_DIGITS = { "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9 };
function kanjiToInt(s) {
  if (!s) return 0;
  if (s.includes("十")) {
    const [tensPart, onesPart] = s.split("十");
    const tens = tensPart ? (KANJI_DIGITS[tensPart] ?? 1) : 1;
    const ones = onesPart ? (KANJI_DIGITS[onesPart] ?? 0) : 0;
    return tens * 10 + ones;
  }
  return KANJI_DIGITS[s] ?? 0;
}
function formatNumberEn(jpNumber, unit) {
  if (!jpNumber) return "";
  const m = jpNumber.match(new RegExp(`^第([一二三四五六七八九十百]+)${unit}(の([一二三四五六七八九十]+))?`));
  if (m) {
    const main = kanjiToInt(m[1]);
    const sub = m[3] ? kanjiToInt(m[3]) : null;
    const label = unit === "条" ? "Article" : "Chapter";
    return `${label} ${main}${sub ? "-" + sub : ""}`;
  }
  // Bare paragraph numbers like "２", "３" — full-width digits, or already numeric.
  const halfWidth = jpNumber.replace(/[０-９]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
  return halfWidth;
}
function displayNumber(node) {
  if (!node.number) return "";
  if (state.lang !== "en") return node.number;
  if (node.type === "chapter") return formatNumberEn(node.number, "章");
  if (node.type === "article") return formatNumberEn(node.number, "条");
  return formatNumberEn(node.number, "");
}
function displayHeading(node) {
  return state.lang === "en" ? (node.heading_en || node.heading) : node.heading;
}

async function loadJSON(path) {
  // no-store: feed.json gets updated by pipeline/batch scripts between page loads, and
  // browsers otherwise cache these fetches aggressively (observed surviving even a hard
  // reload), which silently shows stale content after a re-ingest.
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

function indexTree(node, parent, ancestors) {
  state.byId.set(node.id, { node, parent, ancestors });
  for (const child of node.children || []) {
    indexTree(child, node, [...ancestors, node.id]);
  }
}

function findAncestorOfType(nodeId, type) {
  let entry = state.byId.get(nodeId);
  while (entry) {
    if (entry.node.type === type) return entry.node;
    entry = entry.parent ? state.byId.get(entry.parent.id) : null;
  }
  return null;
}

async function loadFeedList() {
  const list = await loadJSON("../feeds/index.json");
  els.feedPicker.innerHTML = "";
  for (const f of list.feeds) {
    const opt = document.createElement("option");
    opt.value = f.feed_id;
    opt.textContent = f.feed_id;
    els.feedPicker.appendChild(opt);
  }
  return list.feeds[0]?.feed_id;
}

async function loadFeed(feedId) {
  const base = `../feeds/${feedId}`;
  const [manifest, feed] = await Promise.all([
    loadJSON(`${base}/manifest.json`),
    loadJSON(`${base}/feed.json`),
  ]);
  state.feedId = feedId;
  state.manifest = manifest;
  state.feed = feed;
  state.byId.clear();
  indexTree(feed.root, null, []);
  els.feedPicker.value = feedId;
  updateDocumentTitle();
  renderTOC();
  const firstArticle = findFirstOfType(feed.root, "article");
  if (firstArticle) renderArticleView(firstArticle.id);
}

function updateDocumentTitle() {
  const m = state.manifest;
  if (!m) return;
  document.title = state.lang === "en" ? (m.title_en || m.title_ja) : (m.title_ja || m.title_en);
}

function findFirstOfType(node, type) {
  if (node.type === type) return node;
  for (const c of node.children || []) {
    const found = findFirstOfType(c, type);
    if (found) return found;
  }
  return null;
}

// ---------- TOC ----------

function renderTOC() {
  els.toc.innerHTML = "";
  const root = document.createElement("ul");
  for (const chapter of state.feed.root.children || []) {
    root.appendChild(renderTOCNode(chapter));
  }
  els.toc.appendChild(root);
}

function renderTOCNode(node) {
  const li = document.createElement("li");
  li.className = `type-${node.type}`;
  li.dataset.tocId = node.id;

  const label = document.createElement("span");
  label.className = "node-label";
  label.dataset.id = node.id;
  label.textContent = [displayNumber(node), displayHeading(node)].filter(Boolean).join(" ") || node.id;
  label.addEventListener("click", () => {
    const target = node.type === "article" ? node.id : (findAncestorOfType(node.id, "article")?.id || node.id);
    renderArticleView(target, node.id);
  });
  li.appendChild(label);

  const childTypesToShow = node.type === "chapter" ? ["article"] : [];
  const childList = document.createElement("ul");
  let any = false;
  for (const c of node.children || []) {
    if (childTypesToShow.includes(c.type)) {
      childList.appendChild(renderTOCNode(c));
      any = true;
    }
  }
  if (any) li.appendChild(childList);
  return li;
}

function renderLegend() {
  els.legend.innerHTML = CLAUSE_LEGEND.map(([type, labelEn, labelJa]) =>
    `<span><span class="swatch clause-${type}" style="background:var(--clause-${type.replace('enumeration_item','enum')}, var(--text-muted))"></span>${state.lang === "ja" ? labelJa : labelEn}</span>`
  ).join("");
}

function updateBackButton() {
  const btn = els.backBtn;
  if (state.backStack.length === 0) {
    btn.hidden = true;
    btn.onclick = null;
  } else {
    const prev = state.backStack[state.backStack.length - 1];
    const sameFeed = prev.feedId === state.feedId;
    btn.textContent = sameFeed
      ? (state.lang === "ja" ? "← 前の場所に戻る" : "← Back to where you were")
      : (state.lang === "ja" ? `← ${prev.feedId} に戻る` : `← Back to ${prev.feedId}`);
    btn.hidden = false;
    btn.onclick = goBack;
  }
  syncTopbarHeight();
}

// The sticky topbar's height varies (back button/legend show or hide, narrow viewports
// wrap the context bar to two lines), so the TOC/layout sizing below it tracks the real
// rendered height via a CSS var instead of a guessed constant.
function syncTopbarHeight() {
  if (!els.stickyTop) return;
  document.documentElement.style.setProperty("--topbar-height", `${els.stickyTop.offsetHeight}px`);
}
window.addEventListener("resize", syncTopbarHeight);

// Captured right before a ref-click navigates elsewhere, so `goBack` can restore the exact
// scroll position the user was at — a node-block is a whole paragraph (sometimes dozens of
// clauses long), so snapping to its top on the way back would still lose the exact line.
function getCurrentScrollY() {
  return window.scrollY;
}

function setActiveTOC(nodeId) {
  els.toc.querySelectorAll(".node-label.active").forEach((el) => el.classList.remove("active"));
  const el = els.toc.querySelector(`.node-label[data-id="${cssEscape(nodeId)}"]`);
  if (el) el.classList.add("active");
}

function cssEscape(s) {
  return s.replace(/[^a-zA-Z0-9_\-]/g, (c) => `\\${c}`);
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// ---------- Reader ----------

function renderArticleView(articleId, scrollToId) {
  const entry = state.byId.get(articleId);
  if (!entry) return;
  const article = entry.node;
  const chapter = findAncestorOfType(articleId, "chapter");
  state.activeArticleId = articleId;

  setActiveTOC(articleId);
  els.reader.innerHTML = "";
  updateBackButton();

  const crumb = document.createElement("div");
  crumb.className = "breadcrumb";
  crumb.textContent = [state.manifest?.title_ja && state.lang === "ja" ? state.manifest.title_ja : state.manifest?.title_en, chapter ? [displayNumber(chapter), displayHeading(chapter)].filter(Boolean).join(" ") : null].filter(Boolean).join(" / ");
  els.reader.appendChild(crumb);

  const h = document.createElement("h2");
  h.className = "node-heading";
  h.textContent = [displayNumber(article), displayHeading(article)].filter(Boolean).join(" ");
  els.reader.appendChild(h);

  const summary = state.lang === "ja" ? article.summary_ja : article.summary_en;
  if (summary) {
    const s = document.createElement("div");
    s.className = "summary-line";
    s.textContent = summary;
    els.reader.appendChild(s);
  }

  const blocks = renderTextBearingDescendants(article);
  if (blocks.length === 0) {
    const note = document.createElement("div");
    note.className = "placeholder-note";
    note.textContent = UI_STRINGS.notYetProcessed[state.lang];
    els.reader.appendChild(note);
  } else {
    blocks.forEach((n) => els.reader.appendChild(n));
  }

  if (scrollToId && scrollToId !== articleId) {
    const block = els.reader.querySelector(`[data-node-id="${cssEscape(scrollToId)}"]`);
    if (block) {
      block.scrollIntoView({ behavior: "smooth", block: "center" });
      block.classList.add("flash");
      setTimeout(() => block.classList.remove("flash"), 1400);
    }
  } else {
    els.reader.scrollIntoView({ behavior: "instant", block: "start" });
  }
}

function renderTextBearingDescendants(node) {
  const blocks = [];
  if (node.text_ja) blocks.push(renderNodeBlock(node));
  for (const child of node.children || []) blocks.push(...renderTextBearingDescendants(child));
  return blocks;
}

function renderNodeBlock(node) {
  const wrap = document.createElement("div");
  wrap.className = "node-block";
  wrap.dataset.nodeId = node.id;

  if (node.number) {
    const num = document.createElement("span");
    num.className = "para-number";
    num.textContent = node.number;
    wrap.appendChild(num);
  }

  const textEl = document.createElement("div");
  textEl.className = "ja-text";
  textEl.appendChild(renderClauses(node));
  wrap.appendChild(textEl);

  return wrap;
}

// Source docs nest enumerations up to three levels deep, each with its own marker style:
// 一/二/三... (level 1) -> イ/ロ/ハ... (level 2) -> (１)/(２)... (level 3). Items aren't
// separate nodes in this schema (see EXTRACTION_GUIDE.md), so the marker lives inline at
// the start of the clause's own text — detect it here purely for indent/emphasis styling.
//
// Level 2 needs care: a single katakana character is also how countless ordinary words
// start (リスク, ロット, ハイブリッド...), so "starts with a kana in the iroha set" alone
// is far too permissive — it would flag words like "リスク・アセットの額..." as a list
// marker. The real signal is SEQUENCE: a genuine イロハ marker is always the next unused
// character in traditional iroha order within its list, so we only accept a candidate
// that matches the expected next character, tracked per enumeration run in renderClauses.
const LEVEL1_RE = /^([一二三四五六七八九十]+(?:の[一二三四五六七八九十]+)?)/;
const LEVEL2_RE = /^([イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス])/;
const LEVEL3_RE = /^([\(（][0-9０-９]+[\)）])/;
const IROHA_ORDER = "イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス";

function detectItemMarker(text, irohaIndex) {
  const m1 = text.match(LEVEL1_RE);
  if (m1) return { level: 1, marker: m1[1], rest: text.slice(m1[1].length) };

  const m2 = text.match(LEVEL2_RE);
  if (m2 && m2[1] === IROHA_ORDER[irohaIndex + 1]) {
    return { level: 2, marker: m2[1], rest: text.slice(m2[1].length), irohaPos: irohaIndex + 1 };
  }

  const m3 = text.match(LEVEL3_RE);
  if (m3) return { level: 3, marker: m3[1], rest: text.slice(m3[1].length) };

  return null;
}

function renderClauses(node) {
  const frag = document.createDocumentFragment();
  const clauseKey = state.lang === "ja" ? "clauses_ja" : "clauses_en";
  const fullText = state.lang === "ja" ? node.text_ja : node.text_en;
  const clauses = (node[clauseKey] && node[clauseKey].length)
    ? node[clauseKey]
    : [{ clause_type: "main", text: fullText }];
  let irohaIndex = -1; // resets per paragraph; also reset whenever a new level-1 item starts a fresh nested list
  let currentDepth = 1; // carried onto a marker-less continuation clause, so it indents with the item it continues rather than snapping back to depth 1
  for (const clause of clauses) {
    const span = document.createElement("span");
    span.className = `clause clause-${clause.clause_type}`;
    if (clause.in_parenthetical) span.classList.add("in-parenthetical");
    let bodyText = clause.text;
    if (clause.clause_type === "enumeration_item") {
      const detected = detectItemMarker(clause.text, irohaIndex);
      if (detected) {
        currentDepth = detected.level;
        span.style.setProperty("--enum-depth", currentDepth);
        const markerEl = document.createElement("span");
        markerEl.className = "item-marker";
        markerEl.textContent = detected.marker;
        span.appendChild(markerEl);
        bodyText = detected.rest;
        if (detected.level === 1) irohaIndex = -1;
        else if (detected.level === 2) irohaIndex = detected.irohaPos;
      } else {
        span.style.setProperty("--enum-depth", currentDepth);
      }
    }
    span.appendChild(renderTextWithRefs(bodyText, node.refs || []));
    frag.appendChild(span);
  }
  return frag;
}

function renderTextWithRefs(text, refs) {
  const frag = document.createDocumentFragment();
  const refKey = state.lang === "ja" ? "raw_text" : "text_en";
  const applicable = refs
    .filter((r) => r[refKey] && text.includes(r[refKey]))
    .sort((a, b) => b[refKey].length - a[refKey].length);

  if (applicable.length === 0) {
    frag.appendChild(document.createTextNode(text));
    return frag;
  }

  const matches = [];
  for (const ref of applicable) {
    const needle = ref[refKey];
    const idx = text.indexOf(needle);
    if (idx !== -1 && !matches.some((m) => idx < m.end && idx + needle.length > m.start)) {
      matches.push({ start: idx, end: idx + needle.length, ref });
    }
  }
  matches.sort((a, b) => a.start - b.start);

  let pos = 0;
  for (const m of matches) {
    if (m.start > pos) frag.appendChild(document.createTextNode(text.slice(pos, m.start)));
    const a = document.createElement("span");
    a.className = `ref ref-${m.ref.scope}`;
    a.textContent = text.slice(m.start, m.end);
    a.addEventListener("click", (e) => onRefClick(e, m.ref));
    frag.appendChild(a);
    pos = m.end;
  }
  if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
  return frag;
}

async function onRefClick(e, ref) {
  e.stopPropagation();
  if (ref.resolution_status === "resolved" && ref.target_ids?.length) {
    const targetId = ref.target_ids[ref.target_ids.length - 1];
    if (!ref.target_feed || ref.target_feed === state.feedId) {
      const article = findAncestorOfType(targetId, "article");
      if (article) {
        if (article.id !== state.activeArticleId) {
          state.backStack.push({ feedId: state.feedId, articleId: state.activeArticleId, scrollY: getCurrentScrollY() });
        }
        renderArticleView(article.id, targetId);
        return;
      }
    } else {
      state.backStack.push({ feedId: state.feedId, articleId: state.activeArticleId, scrollY: getCurrentScrollY() });
      await loadFeed(ref.target_feed);
      const article = findAncestorOfType(targetId, "article");
      if (article) {
        renderArticleView(article.id, targetId);
      }
      return;
    }
  }
  showPopover(e, ref);
}

async function goBack() {
  const prev = state.backStack.pop();
  if (!prev) return;
  if (prev.feedId !== state.feedId) {
    await loadFeed(prev.feedId);
  }
  if (prev.articleId) renderArticleView(prev.articleId);
  if (typeof prev.scrollY === "number") window.scrollTo(0, prev.scrollY);
}

function showPopover(e, ref) {
  const p = els.popover;
  if (ref.scope === "external") {
    const name = state.lang === "ja" ? (ref.external_name || ref.raw_text) : (ref.external_name_en || ref.external_name || ref.raw_text);
    const summary = state.lang === "ja" ? ref.external_item_summary_ja : ref.external_item_summary_en;
    let html = `<strong>${escapeHtml(name)}</strong>`;
    if (summary) {
      html += `<br>${escapeHtml(summary)}`;
      if (ref.external_item_summary_confidence === "general_knowledge") {
        html += state.lang === "ja"
          ? `<br><span class="confidence-flag">⚠ 一般知識に基づく未検証の要約です</span>`
          : `<br><span class="confidence-flag">⚠ Unverified — based on general knowledge, not the source text</span>`;
      }
    } else {
      html += state.lang === "ja"
        ? `<br><span style="opacity:.7">この条項の要約はまだありません: "${escapeHtml(ref.raw_text)}"</span>`
        : `<br><span style="opacity:.7">No summary yet for this specific citation: "${escapeHtml(ref.raw_text)}"</span>`;
    }
    p.innerHTML = html;
  } else if (ref.resolution_status === "internal_unavailable") {
    p.textContent = state.lang === "ja"
      ? `文書内の参照（未収録の範囲）: "${ref.raw_text}"`
      : `Internal reference to a part of this document not yet loaded: "${ref.raw_text}"`;
  } else {
    p.textContent = state.lang === "ja"
      ? `未解決の参照: "${ref.raw_text}"`
      : `Unresolved reference: "${ref.raw_text}"`;
  }
  p.style.left = `${Math.min(e.clientX + 8, window.innerWidth - 300)}px`;
  p.style.top = `${e.clientY + 12}px`;
  p.hidden = false;
  setTimeout(() => { p.hidden = true; }, 4500);
}

document.addEventListener("click", (e) => {
  if (!els.popover.hidden && !e.target.closest(".ref") && !e.target.closest(".ref-popover")) {
    els.popover.hidden = true;
  }
});

// ---------- Controls ----------

els.toggleClauses.addEventListener("change", () => {
  document.body.classList.toggle("cues-off", !els.toggleClauses.checked);
});
document.getElementById("text-larger").addEventListener("click", () => adjustFontScale(0.1));
document.getElementById("text-smaller").addEventListener("click", () => adjustFontScale(-0.1));
function adjustFontScale(delta) {
  const cur = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--font-scale")) || 1;
  const next = Math.min(1.6, Math.max(0.8, cur + delta));
  document.documentElement.style.setProperty("--font-scale", next);
}
document.getElementById("toggle-dark").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme");
  document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
});
els.feedPicker.addEventListener("change", (e) => loadFeed(e.target.value));

function refreshStaticUI() {
  document.getElementById("cues-label").textContent = UI_STRINGS.cues[state.lang];
  document.getElementById("text-smaller").title = UI_STRINGS.textSmaller[state.lang];
  document.getElementById("text-larger").title = UI_STRINGS.textLarger[state.lang];
  document.getElementById("toggle-dark").title = UI_STRINGS.toggleDark[state.lang];
  els.feedPicker.setAttribute("aria-label", UI_STRINGS.selectFeed[state.lang]);
  updateDocumentTitle();
  renderLegend();
  updateBackButton();
}

els.langButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.classList.contains("active")) return;
    els.langButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.lang = btn.dataset.lang;
    document.documentElement.lang = state.lang;
    refreshStaticUI();
    renderTOC();
    if (state.activeArticleId) renderArticleView(state.activeArticleId);
  });
});

// ---------- Boot ----------

refreshStaticUI();
loadFeedList().then((firstFeedId) => {
  if (firstFeedId) loadFeed(firstFeedId);
});
