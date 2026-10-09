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
  ["limitation", "limited to (に限る)", "限定（に限る）"],
];

const UI_STRINGS = {
  cues: { ja: "視覚キュー", en: "Cues" },
  textSmaller: { ja: "文字を小さく", en: "Smaller text" },
  textLarger: { ja: "文字を大きく", en: "Larger text" },
  toggleDark: { ja: "ダークモード切替", en: "Toggle dark mode" },
  selectFeed: { ja: "規則を選択", en: "Select regulation" },
  notice: {
    ja: "非公式・AI支援による翻訳の草稿です。法的助言ではなく、金融庁が承認したものでもありません。日本語の原文が優先します。必ず公式の資料でご確認ください。",
    en: "Unofficial, AI-assisted draft translation — not legal advice, and not endorsed by the Financial Services Agency. The Japanese text is authoritative; please verify against the official source.",
  },
  noticeClose: { ja: "閉じる", en: "Dismiss" },
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
  if (s.includes("百")) {
    const [h, rest] = s.split("百");
    return (h ? (KANJI_DIGITS[h] ?? 1) : 1) * 100 + kanjiToInt(rest);
  }
  if (s.includes("十")) {
    const [tensPart, onesPart] = s.split("十");
    const tens = tensPart ? (KANJI_DIGITS[tensPart] ?? 1) : 1;
    const ones = onesPart ? (KANJI_DIGITS[onesPart] ?? 0) : 0;
    return tens * 10 + ones;
  }
  return KANJI_DIGITS[s] ?? 0;
}
const UNIT_EN = { "条": "Article", "章": "Chapter", "節": "Section", "款": "Subsection", "目": "Division" };
function formatNumberEn(jpNumber, unit) {
  if (!jpNumber) return "";
  // 別表第一 -> Appended Table 1
  const appx = jpNumber.match(/^別表第([一二三四五六七八九十]+)/);
  if (appx) return `Appended Table ${kanjiToInt(appx[1])}`;
  // 第四十三条の三の二 -> Article 43-3-2 (any number of の-suffixes)
  const m = jpNumber.match(new RegExp(`^第([一二三四五六七八九十百]+)${unit}((?:の[一二三四五六七八九十]+)*)`));
  if (m) {
    const subs = (m[2].match(/[一二三四五六七八九十]+/g) || []).map(kanjiToInt);
    return `${UNIT_EN[unit]} ${[kanjiToInt(m[1]), ...subs].join("-")}`;
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
  if (node.type === "section") return formatNumberEn(node.number, "節");
  if (node.type === "subsection") return formatNumberEn(node.number, "款");
  if (node.type === "division") return formatNumberEn(node.number, "目");
  return formatNumberEn(node.number, "");
}
function displayHeading(node) {
  return state.lang === "en" ? (node.heading_en || node.heading) : node.heading;
}

// Two data sources, same shapes:
// - served mode (app/ under an HTTP server): fetch feeds/*.json directly.
// - static-site mode (site/, built by pipeline/build_site.py, opened via file://): browsers
//   block fetch() on file:// URLs, so the build wraps each JSON file in a tiny .js file that
//   registers it on window.REG_DATA, and we load those with <script> tags instead (script
//   tags are allowed from file://). index.html sets window.REG_STATIC_SITE to opt in.
const STATIC_SITE = Boolean(window.REG_STATIC_SITE);
window.REG_DATA = window.REG_DATA || {};
function loadScriptData(key, src) {
  if (window.REG_DATA[key]) return Promise.resolve(window.REG_DATA[key]);
  return new Promise((resolve, reject) => {
    const tag = document.createElement("script");
    tag.src = src;
    tag.onload = () => window.REG_DATA[key] ? resolve(window.REG_DATA[key]) : reject(new Error(`${src} did not register ${key}`));
    tag.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(tag);
  });
}
function loadFeedIndex() {
  return STATIC_SITE ? loadScriptData("index", "data/index.js") : loadJSON("../feeds/index.json");
}
async function loadFeedData(feedId) {
  if (STATIC_SITE) {
    const bundle = await loadScriptData(`feed:${feedId}`, `data/${feedId}.js`);
    return [bundle.manifest, bundle.feed, bundle.formulas || null, bundle.notation || null, bundle.tables || null];
  }
  const base = `../feeds/${feedId}`;
  const optional = (path) => loadJSON(path).catch(() => null); // most feeds have no formulas
  return Promise.all([
    loadJSON(`${base}/manifest.json`), loadJSON(`${base}/feed.json`),
    optional(`${base}/formulas.json`), optional(`${base}/notation.json`), optional(`${base}/tables.json`),
  ]);
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
  const list = await loadFeedIndex();
  els.feedPicker.innerHTML = "";
  for (const f of list.feeds) {
    const opt = document.createElement("option");
    opt.value = f.feed_id;
    opt.dataset.titleJa = f.title_ja || "";
    opt.dataset.titleEn = f.title_en || "";
    els.feedPicker.appendChild(opt);
  }
  labelFeedOptions();
  return list.feeds[0]?.feed_id;
}

// The static site's index carries manifest titles; served mode's feeds/index.json doesn't,
// so fall back to the bare feed_id there.
function feedLabel(feedId) {
  for (const opt of els.feedPicker.options) if (opt.value === feedId) return opt.textContent;
  return feedId;
}

function labelFeedOptions() {
  for (const opt of els.feedPicker.options) {
    const title = state.lang === "en" ? (opt.dataset.titleEn || opt.dataset.titleJa) : (opt.dataset.titleJa || opt.dataset.titleEn);
    opt.textContent = title || opt.value;
  }
}

async function loadFeed(feedId) {
  const [manifest, feed, formulas, notation, tables] = await loadFeedData(feedId);
  state.formulas = formulas;
  state.tables = tables;
  state.notation = notation;
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

// Grouping levels above articles (第二章 / 第一節 / 第一款 / 第一目). Chapter 2 has none
// below the chapter; Chapter 3 uses all three.
const STRUCTURAL_TYPES = ["chapter", "section", "subsection", "division"];

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
  appendRich(label, [displayNumber(node), displayHeading(node)].filter(Boolean).join(" ") || node.id);
  label.addEventListener("click", () => {
    if (node.type === "article") return renderArticleView(node.id);
    // A chapter/section heading opens its first article.
    const target = findAncestorOfType(node.id, "article") || findFirstOfType(node, "article");
    if (target) renderArticleView(target.id, target.id === node.id ? undefined : node.id);
  });
  li.appendChild(label);

  const childTypesToShow = STRUCTURAL_TYPES.includes(node.type) ? [...STRUCTURAL_TYPES.slice(1), "article"] : [];
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
      : (state.lang === "ja" ? `← ${feedLabel(prev.feedId)} に戻る` : `← Back to ${feedLabel(prev.feedId)}`);
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
  const groups = (entry.ancestors || []).map((id) => state.byId.get(id)?.node).filter((n) => n && STRUCTURAL_TYPES.includes(n.type));
  appendRich(crumb, [
    state.lang === "ja" ? (state.manifest?.title_ja || state.manifest?.title_en) : (state.manifest?.title_en || state.manifest?.title_ja),
    ...groups.map((g) => [displayNumber(g), displayHeading(g)].filter(Boolean).join(" ")),
  ].filter(Boolean).join(" / "));
  els.reader.appendChild(crumb);

  const h = document.createElement("h2");
  h.className = "node-heading";
  appendRich(h, [displayNumber(article), displayHeading(article)].filter(Boolean).join(" "));
  els.reader.appendChild(h);

  const summary = state.lang === "ja" ? article.summary_ja : article.summary_en;
  if (summary) {
    const s = document.createElement("div");
    s.className = "summary-line";
    appendRich(s, summary);
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
  } else if (!renderArticleView.firstDone) {
    // The very first render on page load stays at the top of the page, so the notice banner
    // above the reader is actually seen; every later navigation scrolls the reader into view.
    renderArticleView.firstDone = true;
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

  for (const f of (state.formulas?.formulas || []).filter((x) => x.node_id === node.id && !x.anchor)) {
    wrap.appendChild(renderFormulaBox(f));
  }

  return wrap;
}

// ---------- Formulas ----------
//
// feeds/<feed>/formulas.json holds each formula's STRUCTURE, written against variable ids
// (e.g. "CET1_ratio = CET1 / RWA >= 4.5%"), plus what each variable MEANS. How a variable
// is DISPLAYED comes only from notation.json, so a different notation standard is a
// swap of that one file. Grammar: numbers (4.5%, 12.5), variable ids, + - * /, ( ),
// max(...)/min(...), and = >= <= between terms. "/" is drawn as a stacked fraction.

function tokenizeFormula(src) {
  const re = /\s*(?:(\d+(?:\.\d+)?%?)|([A-Za-z_][A-Za-z0-9_]*)|(>=|<=|[-+*\/(),=^]))/y;
  const out = [];
  while (re.lastIndex < src.length) {
    const start = re.lastIndex;
    const m = re.exec(src);
    if (!m || re.lastIndex === start) {
      if (src.slice(start).trim()) throw new Error(`can't parse "${src.slice(start)}"`);
      break;
    }
    if (m[1]) out.push({ k: "num", v: m[1] });
    else if (m[2]) out.push({ k: "id", v: m[2] });
    else out.push({ k: "op", v: m[3] });
  }
  return out;
}

function parseFormula(src) {
  const toks = tokenizeFormula(src);
  let i = 0;
  const peek = () => toks[i];
  const take = (v) => (toks[i] && toks[i].v === v ? toks[i++] : null);
  const expect = (v) => { if (!take(v)) throw new Error(`expected "${v}" in ${src}`); };
  const primary = () => {
    const t = toks[i++];
    if (!t) throw new Error(`unexpected end of ${src}`);
    if (t.k === "num") return { t: "num", v: t.v };
    if (t.k === "id") {
      if (take("(")) {
        const args = [sum()];
        while (take(",")) args.push(sum());
        expect(")");
        return { t: "fn", name: t.v, args };
      }
      return { t: "var", id: t.v };
    }
    if (t.v === "(") { const x = sum(); expect(")"); return { t: "paren", x }; }
    if (t.v === "-") return { t: "neg", x: primary() };
    throw new Error(`unexpected "${t.v}" in ${src}`);
  };
  const power = () => {
    const base = primary();
    if (take("^")) return { t: "pow", base, exp: power() }; // right-associative
    return base;
  };
  const product = () => {
    let l = power();
    while (peek() && (peek().v === "*" || peek().v === "/")) l = { t: "bin", op: toks[i++].v, l, r: power() };
    return l;
  };
  const sum = () => {
    let l = product();
    while (peek() && (peek().v === "+" || peek().v === "-")) l = { t: "bin", op: toks[i++].v, l, r: product() };
    return l;
  };
  const parts = [sum()];
  const rels = [];
  while (peek() && ["=", ">=", "<="].includes(peek().v)) { rels.push(toks[i++].v); parts.push(sum()); }
  if (i < toks.length) throw new Error(`trailing "${toks[i].v}" in ${src}`);
  return { parts, rels };
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// "X_{sub}^{sup}" -> X with sub/superscript. Kept deliberately tiny: notation.json is the
// only input, and a notation standard needs little more than base + indices.
function renderSymbol(sym) {
  const frag = document.createDocumentFragment();
  const re = /([_^])\{([^}]*)\}/g;
  let pos = 0, m;
  while ((m = re.exec(sym))) {
    if (m.index > pos) frag.appendChild(document.createTextNode(sym.slice(pos, m.index)));
    frag.appendChild(el(m[1] === "_" ? "sub" : "sup", null, m[2]));
    pos = re.lastIndex;
  }
  if (pos < sym.length) frag.appendChild(document.createTextNode(sym.slice(pos)));
  return frag;
}

const unparen = (x) => (x.t === "paren" ? x.x : x);
const FN_DISPLAY = { Phi: "Φ" }; // standard normal CDF
const isSum = (x) => x.t === "bin" && (x.op === "+" || x.op === "-");

function renderExpr(x) {
  switch (x.t) {
    case "num": return el("span", "f-num", x.v);
    case "var": {
      const v = el("span", "fvar");
      v.tabIndex = 0;
      v.dataset.var = x.id;
      v.setAttribute("role", "button");
      v.appendChild(renderSymbol(state.notation?.symbols?.[x.id] || x.id));
      const meta = state.formulas?.variables?.[x.id];
      if (meta) v.setAttribute("aria-label", state.lang === "ja" ? meta.name_ja : meta.name_en);
      return v;
    }
    case "paren": {
      const s = el("span", "f-group");
      s.append(el("span", "f-paren", "("), renderExpr(x.x), el("span", "f-paren", ")"));
      return s;
    }
    case "neg": { const s = el("span", "f-group"); s.append("−", renderExpr(x.x)); return s; }
    case "pow": {
      const s = el("span", "f-group");
      s.appendChild(renderExpr(x.base));
      const sup = el("sup", "f-sup");
      sup.appendChild(renderExpr(unparen(x.exp)));
      s.appendChild(sup);
      return s;
    }
    case "fn": {
      if (x.name === "sqrt") {
        const s = el("span", "f-group f-sqrt");
        const rad = el("span", "f-radicand");
        rad.appendChild(renderExpr(unparen(x.args[0])));
        s.append(el("span", "f-radical", "√"), rad);
        return s;
      }
      if (x.name === "abs") {
        const s = el("span", "f-group");
        s.append(el("span", "f-paren", "|"), renderExpr(x.args[0]), el("span", "f-paren", "|"));
        return s;
      }
      if (x.name === "sum") {
        // sum(index, body) -> Σ with the index underneath; sum(index, upper, body) also
        // puts the upper bound above it.
        const s = el("span", "f-group");
        const sig = el("span", "f-sum-op");
        const under = el("span", "f-sum-index");
        under.appendChild(renderExpr(x.args[0]));
        if (x.args.length === 3) {
          const over = el("span", "f-sum-index");
          over.appendChild(renderExpr(x.args[1]));
          sig.appendChild(over);
        }
        sig.append(el("span", "f-sigma", "Σ"), under);
        s.append(sig, renderExpr(x.args[x.args.length - 1]));
        return s;
      }
      const s = el("span", "f-group");
      s.append(el("span", "f-fn", FN_DISPLAY[x.name] || x.name), el("span", "f-paren", "("));
      x.args.forEach((a, k) => { if (k) s.append(el("span", "f-comma", ", ")); s.appendChild(renderExpr(a)); });
      s.appendChild(el("span", "f-paren", ")"));
      return s;
    }
    case "bin": {
      if (x.op === "/") {
        const fr = el("span", "f-frac");
        const num = el("span", "f-num-part"); num.appendChild(renderExpr(unparen(x.l)));
        const den = el("span", "f-den-part"); den.appendChild(renderExpr(unparen(x.r)));
        fr.append(num, den);
        return fr;
      }
      if (x.op === "+" || x.op === "-") {
        // Flatten a left-nested chain (a + b − c ...) into one group of terms, so a long
        // sum can wrap between terms on a narrow screen (.f-sum is a wrapping flex row).
        const terms = [];
        let cur = x;
        while (cur.t === "bin" && (cur.op === "+" || cur.op === "-")) {
          terms.unshift([cur.op, cur.op === "-" && isSum(cur.r) ? { t: "paren", x: cur.r } : cur.r]);
          cur = cur.l;
        }
        const s = el("span", "f-group f-sum");
        s.appendChild(renderExpr(cur));
        for (const [op, term] of terms) {
          const piece = el("span", "f-term");
          piece.append(el("span", "f-op", op === "-" ? "−" : "+"), renderExpr(term));
          s.appendChild(piece);
        }
        return s;
      }
      const s = el("span", "f-group");
      const wrapSum = (y) => (x.op === "*" && isSum(y) ? { t: "paren", x: y } : y);
      s.appendChild(renderExpr(wrapSum(x.l)));
      s.appendChild(el("span", "f-op", x.op === "*" ? "×" : x.op === "-" ? "−" : "+"));
      const r = x.op === "-" && isSum(x.r) ? { t: "paren", x: x.r } : wrapSum(x.r);
      s.appendChild(renderExpr(r));
      return s;
    }
  }
  return document.createTextNode("?");
}

const FORMULA_SOURCE = {
  transcribed: { ja: "原文の数式（画像）から転記", en: "Transcribed from the source formula" },
  text_derived: { ja: "条文の文言から作成", en: "Written from the article text" },
  image_reconstructed: { ja: "⚠ 原文では画像の数式・未照合", en: "⚠ Image formula in source — not yet verified" },
};

function appendFormulaLine(into, line, used) {
  try {
    const { parts, rels } = parseFormula(line);
    parts.forEach((p, k) => {
      if (k) into.appendChild(el("span", "f-rel", { "=": "=", ">=": "≥", "<=": "≤" }[rels[k - 1]]));
      into.appendChild(renderExpr(p));
    });
    line.replace(/[A-Za-z_][A-Za-z0-9_]*/g, (id) => { if (state.formulas?.variables?.[id]) used.add(id); return id; });
  } catch (err) {
    into.textContent = line;
    into.classList.add("formula-error");
  }
}

function renderFormulaBox(f, tag = "div") {
  // A span (display:block via CSS) when it sits inside clause text, so the surrounding
  // inline markup stays valid.
  const box = el(tag, `formula-box source-${f.source}`);
  const head = el("span", "formula-head");
  head.appendChild(el("span", "formula-label", state.lang === "ja" ? f.label_ja : f.label_en));
  const src = FORMULA_SOURCE[f.source];
  if (src) head.appendChild(el("span", "formula-source", src[state.lang]));
  box.appendChild(head);
  const used = new Set();
  for (const line of f.lines) {
    const row = el("span", "formula-line");
    appendFormulaLine(row, line, used);
    box.appendChild(row);
  }
  const note = state.lang === "ja" ? f.note_ja : f.note_en;
  if (note) box.appendChild(el("span", "formula-note", note));
  // Hover/tap explains a variable in place; this list is the same information for
  // reading straight through (and for touch screens, where there is no hover).
  if (used.size) {
    const det = el("details", "formula-vars");
    det.appendChild(el("summary", null, state.lang === "ja" ? `記号の説明（${used.size}）` : `Variables (${used.size})`));
    const dl = el("dl");
    for (const id of used) {
      const dt = el("dt");
      dt.appendChild(renderSymbol(state.notation?.symbols?.[id] || id));
      const meta = state.formulas.variables[id];
      dl.append(dt, el("dd", null, state.lang === "ja" ? meta.name_ja : meta.name_en));
    }
    det.appendChild(dl);
    box.appendChild(det);
  }
  return box;
}

// Variable explanation popover: hover (mouse) or tap/focus (touch, keyboard).
const varTip = el("div", "var-tip");
varTip.hidden = true;
varTip.setAttribute("role", "tooltip");
document.body.appendChild(varTip);
let varTipFor = null;
let varTipHideTimer = null;
let varTipShownAt = 0;

function showVarTip(target) {
  const id = target.dataset.var;
  const meta = state.formulas?.variables?.[id];
  if (!meta) return;
  clearTimeout(varTipHideTimer);
  if (varTipFor !== target || varTip.hidden) varTipShownAt = Date.now();
  varTipFor = target;
  varTip.innerHTML = "";
  const sym = el("div", "var-tip-sym");
  sym.appendChild(renderSymbol(state.notation?.symbols?.[id] || id));
  varTip.appendChild(sym);
  varTip.appendChild(el("div", "var-tip-name", state.lang === "ja" ? meta.name_ja : meta.name_en));
  const desc = state.lang === "ja" ? meta.desc_ja : meta.desc_en;
  if (desc) varTip.appendChild(el("div", "var-tip-desc", desc));
  if (meta.defined_at && state.byId.has(meta.defined_at)) {
    const where = state.byId.get(meta.defined_at).node;
    const art = findAncestorOfType(meta.defined_at, "article");
    const label = [art ? displayNumber(art) : "", where.type === "paragraph" && where.number ? (state.lang === "ja" ? `第${where.number}項` : `para. ${displayNumber(where)}`) : ""].filter(Boolean).join(state.lang === "ja" ? "" : ", ");
    const link = el("button", "var-tip-link", (state.lang === "ja" ? "定義: " : "Defined in: ") + label + " →");
    link.addEventListener("click", () => {
      hideVarTip(true);
      if (art && art.id !== state.activeArticleId) {
        state.backStack.push({ feedId: state.feedId, articleId: state.activeArticleId, scrollY: getCurrentScrollY() });
      }
      if (art) renderArticleView(art.id, meta.defined_at);
    });
    varTip.appendChild(link);
  }
  varTip.hidden = false;
  const r = target.getBoundingClientRect();
  const w = Math.min(320, window.innerWidth - 24);
  varTip.style.width = `${w}px`;
  varTip.style.left = `${Math.max(12, Math.min(r.left, window.innerWidth - w - 12))}px`;
  const below = r.bottom + 8;
  const h = varTip.offsetHeight;
  varTip.style.top = `${below + h > window.innerHeight - 8 ? Math.max(8, r.top - h - 8) : below}px`;
}

function hideVarTip(now) {
  clearTimeout(varTipHideTimer);
  const go = () => { varTip.hidden = true; varTipFor = null; };
  if (now) go(); else varTipHideTimer = setTimeout(go, 250);
}

document.addEventListener("mouseover", (e) => {
  const v = e.target.closest?.(".fvar");
  if (v) showVarTip(v);
  else if (e.target.closest?.(".var-tip")) clearTimeout(varTipHideTimer);
});
document.addEventListener("mouseout", (e) => {
  if (e.target.closest?.(".fvar") || e.target.closest?.(".var-tip")) hideVarTip(false);
});
document.addEventListener("focusin", (e) => { const v = e.target.closest?.(".fvar"); if (v) showVarTip(v); });
document.addEventListener("click", (e) => {
  const v = e.target.closest?.(".fvar");
  // A tap fires mouseover (which opens the tip) right before click, so a click within a
  // moment of opening is that same tap — don't let it toggle the tip shut again.
  if (v) {
    if (varTipFor === v && !varTip.hidden && Date.now() - varTipShownAt > 400) hideVarTip(true);
    else showVarTip(v);
    return;
  }
  if (!e.target.closest?.(".var-tip")) hideVarTip(true);
});
window.addEventListener("scroll", () => { if (!varTip.hidden) hideVarTip(true); }, { passive: true });

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

// English translations mirror the same three levels: 一 -> (i), イ -> (a), (１) -> (1),
// optionally with a branch suffix like "(ii-2)" for 二の二. The letter level gets the same
// sequence check as イロハ, which also settles the (i)/(v)/(x) ambiguity: "(i)" is the
// ninth letter only when "(h)" came right before it, otherwise it's a roman numeral.
const EN_ROMAN_RE = /^(\([ivxl]+(?:-\d+)?\))/;
const EN_LETTER_RE = /^(\(([a-z])(?:-\d+)?\))/;
const LETTER_ORDER = "abcdefghijklmnopqrstuvwxyz";

function detectItemMarker(text, irohaIndex) {
  const mLetter = text.match(EN_LETTER_RE);
  if (mLetter && mLetter[2] === LETTER_ORDER[irohaIndex + 1]) {
    return { level: 2, marker: mLetter[1], rest: text.slice(mLetter[1].length), irohaPos: irohaIndex + 1 };
  }
  const mRoman = text.match(EN_ROMAN_RE);
  if (mRoman) return { level: 1, marker: mRoman[1], rest: text.slice(mRoman[1].length) };

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

// Each list item renders as ONE block (.enum-block) from its marker up to the next marker:
// an item's text is routinely broken into several clauses by asides ("(i) The amount..."
// + "(meaning ...)" + "."), and giving each enumeration_item clause its own block split a
// single item into several boxes with the aside — and stray punctuation — stranded between.
function renderClauses(node) {
  const frag = document.createDocumentFragment();
  const clauseKey = state.lang === "ja" ? "clauses_ja" : "clauses_en";
  const fullText = state.lang === "ja" ? node.text_ja : node.text_en;
  const clauses = (node[clauseKey] && node[clauseKey].length)
    ? node[clauseKey]
    : [{ clause_type: "main", text: fullText }];
  let irohaIndex = -1; // resets per paragraph; also reset whenever a new level-1 item starts a fresh nested list
  let currentDepth = 1; // carried onto a marker-less continuation, so it indents with the item it continues
  let itemBlock = null; // the .enum-block that following clauses belong to, until the next marker
  const openItemBlock = (depth) => {
    itemBlock = document.createElement("div");
    itemBlock.className = "enum-block";
    itemBlock.style.setProperty("--enum-depth", depth);
    frag.appendChild(itemBlock);
  };
  for (const clause of clauses) {
    const span = document.createElement("span");
    span.className = `clause clause-${clause.clause_type}`;
    if (clause.in_parenthetical) span.classList.add("in-parenthetical");
    let bodyText = clause.text;
    if (clause.clause_type === "enumeration_item") {
      const detected = detectItemMarker(clause.text, irohaIndex);
      if (detected) {
        currentDepth = detected.level;
        openItemBlock(currentDepth);
        const markerEl = document.createElement("span");
        markerEl.className = "item-marker";
        markerEl.textContent = detected.marker;
        itemBlock.appendChild(markerEl);
        bodyText = detected.rest.replace(/^\s+/, "");
        if (detected.level === 1) irohaIndex = -1;
        else if (detected.level === 2) irohaIndex = detected.irohaPos;
      } else if (!itemBlock) {
        openItemBlock(currentDepth);
      }
    }
    // Cue offsets index clause.text; the marker (and its trailing space) was cut off the
    // front of bodyText, so shift them by however much was removed.
    const cut = clause.text.length - bodyText.length;
    span.appendChild(renderTextWithRefs(bodyText, node.refs || [], shiftCues(clause.cues, cut, bodyText.length)));
    (itemBlock || frag).appendChild(span);
  }
  return frag;
}

// Text may carry three kinds of markup from extract_chapter_v2.py:
//   {{T:<id>}}  a table that sat here in the PDF            -> tables.json
//   {{F:<id>}}  an image formula (display or inline symbol) -> formulas.json `anchor`
//   X_{sub} / X^{sup}  sub/superscript characters (e.g. C_{collect}, AddOn^{(IR)})
const RICH_RE = /\{\{([TF]):([^}]+)\}\}|([_^])\{([^}]*)\}/g;
function appendRich(into, str) {
  const re = new RegExp(RICH_RE.source, "g");
  let pos = 0, m;
  while ((m = re.exec(str))) {
    if (m.index > pos) into.appendChild(document.createTextNode(str.slice(pos, m.index)));
    if (m[1] === "T") into.appendChild(renderTableToken(m[2]));
    else if (m[1] === "F") into.appendChild(renderFormulaToken(m[2]));
    else into.appendChild(el(m[3] === "_" ? "sub" : "sup", "text-script", m[4]));
    pos = re.lastIndex;
  }
  if (pos < str.length) into.appendChild(document.createTextNode(str.slice(pos)));
}

function renderTableToken(id) {
  const t = state.tables?.tables?.[id];
  if (!t) {
    const ph = el("span", "token-missing", state.lang === "ja" ? "［表：未整備］" : "[table not yet transcribed]");
    ph.title = id;
    return ph;
  }
  const wrap = el("span", "table-wrap");
  const table = el("table", "reg-table");
  const rows = (state.lang === "en" && t.rows_en) ? t.rows_en : t.rows_ja;
  const headerRows = t.header_rows ?? 1;
  const thead = el("thead"), tbody = el("tbody");
  rows.forEach((row, r) => {
    const tr = el("tr");
    for (const cell of row) {
      if (cell === null) continue; // covered by a neighbour's colspan/rowspan
      const spec = typeof cell === "object" ? cell : { text: cell };
      const td = el(r < headerRows ? "th" : "td");
      if (spec.colspan) td.colSpan = spec.colspan;
      if (spec.rowspan) td.rowSpan = spec.rowspan;
      appendRich(td, spec.text ?? "");
      tr.appendChild(td);
    }
    (r < headerRows ? thead : tbody).appendChild(tr);
  });
  if (thead.childNodes.length) table.appendChild(thead);
  table.appendChild(tbody);
  wrap.appendChild(table);
  const note = state.lang === "ja" ? t.note_ja : t.note_en;
  if (note) wrap.appendChild(el("span", "table-note", note));
  return wrap;
}

function renderFormulaToken(id) {
  const f = (state.formulas?.formulas || []).find((x) => x.anchor === id);
  if (!f) {
    const ph = el("span", "token-missing", state.lang === "ja" ? "［数式：未転記］" : "[formula not yet transcribed]");
    ph.title = id;
    return ph;
  }
  if (f.display === "inline") {
    const span = el("span", "formula-inline");
    for (const line of f.lines) appendFormulaLine(span, line, new Set());
    return span;
  }
  return renderFormulaBox(f, "span");
}

function shiftCues(cues, cut, len) {
  if (!cues?.length) return [];
  return cues
    .map((c) => ({ type: c.type, start: Math.max(0, c.start - cut), end: Math.min(len, c.end - cut) }))
    .filter((c) => c.end > c.start);
}

// In-clause cues (pipeline/annotate_cues.py) are ranges that always nest — they're drawn
// only between points at the same paren depth — so they form a tree: each becomes a span
// wrapping its children, drawn as an underline whose offset grows with how many cues it
// contains, so nested cues stack as separate lines instead of overprinting one another.
function buildCueTree(cues) {
  const sorted = [...cues].sort((a, b) => a.start - b.start || b.end - a.end);
  const roots = [];
  const stack = [];
  for (const c of sorted) {
    const node = { ...c, children: [] };
    while (stack.length && stack[stack.length - 1].end <= c.start) stack.pop();
    const parent = stack[stack.length - 1];
    if (parent && c.end <= parent.end) parent.children.push(node);
    else if (!parent) roots.push(node);
    else continue; // crossing range — never produced by the pipeline; skip rather than mis-nest
    stack.push(node);
  }
  const height = (n) => (n.h = n.children.length ? 1 + Math.max(...n.children.map(height)) : 0);
  roots.forEach(height);
  return roots;
}

function renderTextWithRefs(text, refs, cues = []) {
  const refKey = state.lang === "ja" ? "raw_text" : "text_en";
  const applicable = refs
    .filter((r) => r[refKey] && text.includes(r[refKey]))
    .sort((a, b) => b[refKey].length - a[refKey].length);
  const matches = [];
  for (const ref of applicable) {
    const needle = ref[refKey];
    const idx = text.indexOf(needle);
    if (idx !== -1 && !matches.some((m) => idx < m.end && idx + needle.length > m.start)) {
      matches.push({ start: idx, end: idx + needle.length, ref });
    }
  }
  matches.sort((a, b) => a.start - b.start);

  // Plain text + ref links for [a, b). A ref that crosses a cue edge is drawn as two
  // linked pieces, one on each side.
  const renderPlain = (a, b, into) => {
    let pos = a;
    for (const m of matches) {
      const s = Math.max(m.start, a), e = Math.min(m.end, b);
      if (s >= e) continue;
      if (s > pos) appendRich(into, text.slice(pos, s));
      const link = document.createElement("span");
      link.className = `ref ref-${m.ref.scope}`;
      appendRich(link, text.slice(s, e));
      link.addEventListener("click", (ev) => onRefClick(ev, m.ref));
      into.appendChild(link);
      pos = e;
    }
    if (pos < b) appendRich(into, text.slice(pos, b));
  };
  const renderRange = (a, b, nodes, into) => {
    let pos = a;
    for (const n of nodes) {
      if (n.start > pos) renderPlain(pos, n.start, into);
      const el = document.createElement("span");
      el.className = `cue cue-${n.type}`;
      el.style.setProperty("--cue-h", Math.min(n.h, 3));
      el.title = cueLabel(n.type);
      renderRange(n.start, n.end, n.children, el);
      into.appendChild(el);
      pos = n.end;
    }
    if (pos < b) renderPlain(pos, b, into);
  };
  const frag = document.createDocumentFragment();
  renderRange(0, text.length, buildCueTree(cues), frag);
  return frag;
}

function cueLabel(type) {
  const row = CLAUSE_LEGEND.find(([t]) => t === type);
  return row ? (state.lang === "ja" ? row[2] : row[1]) : type;
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

// Source line (page footer): constants only, so innerHTML is safe here.
const SOURCE_LINE = {
  ja: '出典：金融庁「最終指定親会社及びその子法人等の保有する資産等に照らし当該最終指定親会社及びその子法人等の自己資本の充実の状況が適当であるかどうかを判断するための基準を定める件」（<a href="https://www.fsa.go.jp/" target="_blank" rel="noopener">金融庁</a>公表）。引用法令・告示は<a href="https://laws.e-gov.go.jp/" target="_blank" rel="noopener">e-Gov法令検索</a>等の公式公表物による。英訳・数式の転記・表・相互参照は本プロジェクトによる非公式の作業であり、誤りを含み得ます。',
  en: 'Source: the Financial Services Agency\'s public notice establishing standards for determining whether the capital adequacy of an Ultimate Designated Parent Company and its subsidiaries is appropriate (<a href="https://www.fsa.go.jp/" target="_blank" rel="noopener">published by the FSA</a>); cited laws and notices from official publications such as <a href="https://laws.e-gov.go.jp/" target="_blank" rel="noopener">e-Gov Law Search</a>. The English translation, formula transcriptions, tables and cross-references are unofficial work of this project and may contain errors.',
};
// The notice banner: shown on first open, dismissible, and the dismissal is remembered
// (localStorage can be unavailable — private mode, some file:// setups — so every access is guarded).
const NOTICE_KEY = "reg-reader-notice-dismissed-v1";
function noticeDismissed() { try { return localStorage.getItem(NOTICE_KEY) === "1"; } catch (e) { return false; } }
document.getElementById("notice-close").addEventListener("click", () => {
  document.getElementById("notice").hidden = true;
  try { localStorage.setItem(NOTICE_KEY, "1"); } catch (e) { /* hidden for this visit only */ }
});
document.getElementById("notice").hidden = noticeDismissed();

function refreshStaticUI() {
  document.getElementById("notice-text").textContent = UI_STRINGS.notice[state.lang];
  document.getElementById("notice-close").setAttribute("aria-label", UI_STRINGS.noticeClose[state.lang]);
  document.getElementById("notice-close").title = UI_STRINGS.noticeClose[state.lang];
  document.getElementById("source-line").innerHTML = SOURCE_LINE[state.lang];
  document.getElementById("cues-label").textContent = UI_STRINGS.cues[state.lang];
  document.getElementById("text-smaller").title = UI_STRINGS.textSmaller[state.lang];
  document.getElementById("text-larger").title = UI_STRINGS.textLarger[state.lang];
  document.getElementById("toggle-dark").title = UI_STRINGS.toggleDark[state.lang];
  els.feedPicker.setAttribute("aria-label", UI_STRINGS.selectFeed[state.lang]);
  updateDocumentTitle();
  labelFeedOptions();
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
