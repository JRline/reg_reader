#!/usr/bin/env python3
"""
Deterministic citation extraction for Japanese regulatory text, plus the English citation
string each one becomes under this project's translation convention.

Used by build_chapter.py for chapters translated in-repo (Chapter 3 onward), where there's
no chatbot pass producing `refs`. Resolution (target ids) is NOT done here — that stays
with reresolve_refs.py / link_external_refs.py, exactly as for Chapter 2.

Convention (matches what Chapter 2's refs already use):
  第五条第二項第一号     -> Article 5, paragraph (2), item (i)
  第一号イ               -> item (i)(a)
  前条第二項             -> paragraph (2) of the preceding Article
  前項各号               -> each item of the preceding paragraph
  第一号から第四号まで    -> items (i) through (iv)
  法第二条第八項          -> Article 2, paragraph (8) of the Act
"""
import re

N = "[一二三四五六七八九十百千]+"
IROHA = "イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス"

# Longest names first so 金融商品取引法施行令 wins over 金融商品取引法 over 法.
LAWS = [
    ("連結財務諸表の用語、様式及び作成方法に関する規則", "the Consolidated Financial Statement Regulation"),
    ("協同組合による金融事業に関する法律施行令", "the Order for Enforcement of the Act on Financial Businesses by Cooperatives"),
    ("協同組合による金融事業に関する法律", "the Act on Financial Businesses by Cooperatives"),
    ("株式会社商工組合中央金庫法", "the Shoko Chukin Bank Limited Act"),
    ("金融商品取引法施行令", "the Order for Enforcement of the Financial Instruments and Exchange Act"),
    ("金融商品取引法", "the Financial Instruments and Exchange Act"),
    ("資金決済に関する法律", "the Payment Services Act"),
    ("最終指定親会社TLAC告示", "the TLAC Public Notice for Ultimate Designated Parent Companies"),
    ("連結財務諸表規則", "the Consolidated Financial Statement Regulation"),
    ("商品先物取引法", "the Commodity Derivatives Act"),
    ("貸金業法施行令", "the Order for Enforcement of the Money Lending Business Act"),
    ("信用金庫法", "the Shinkin Bank Act"),
    ("労働金庫法", "the Labour Bank Act"),
    ("保険業法", "the Insurance Business Act"),
    ("銀行法", "the Banking Act"),
    ("同告示", "the same Public Notice"),
    ("同法", "the same Act"),
    ("同令", "the same Order"),
    ("法", "the Act"),  # in this notification, 法 = 金融商品取引法 (defined in its Article 1)
    ("令", "the Order"),
]
# Notifications cited by their full title (no short law name). A citation right after one
# of these titles (optionally followed by its "(平成…告示第…号)" number) belongs to THAT
# notification, not to this one. Longest first: each leverage notice's title extends its
# capital notice's title.
_BANK = "銀行法第十四条の二の規定に基づき、銀行がその保有する資産等に照らし自己資本の充実の状況が適当であるかどうかを判断するための基準"
_BHC = "銀行法第五十二条の二十五の規定に基づき、銀行持株会社が銀行持株会社及びその子会社の保有する資産等に照らしそれらの自己資本の充実の状況が適当であるかどうかを判断するための基準"
_SHINKIN = "信用金庫法第八十九条第一項において準用する銀行法第十四条の二の規定に基づき、信用金庫及び信用金庫連合会がその保有する資産等に照らし自己資本の充実の状況が適当であるかどうかを判断するための基準"
_NOCHU = "農林中央金庫がその経営の健全性を判断するための基準"
_SHOKO = "株式会社商工組合中央金庫法第二十三条第一項の規定に基づき、株式会社商工組合中央金庫がその経営の健全性を判断するための基準"
_COOP = "協同組合による金融事業に関する法律第六条第一項において準用する銀行法第十四条の二の規定に基づき、信用協同組合及び信用協同組合連合会がその保有する資産等に照らし自己資本の充実の状況が適当であるかどうかを判断するための基準"
_ROKIN = "労働金庫法第九十四条第一項において準用する銀行法第十四条の二の規定に基づき、労働金庫及び労働金庫連合会がその保有する資産等に照らし自己資本の充実の状況が適当であるかどうかを判断するための基準"
_LEV = "の補完的指標として定めるレバレッジに係る健全性を判断するための基準"
NOTICES = sorted([
    (_BANK, "銀行告示", "the Bank Capital Adequacy Notice"),
    (_BANK + _LEV, "銀行レバレッジ告示", "the Bank Leverage Notice"),
    (_BHC, "銀行持株会社告示", "the Bank Holding Company Capital Adequacy Notice"),
    (_BHC + _LEV, "銀行持株会社レバレッジ告示", "the Bank Holding Company Leverage Notice"),
    (_SHINKIN, "信用金庫告示", "the Shinkin Bank Capital Adequacy Notice"),
    (_SHINKIN + _LEV, "信用金庫レバレッジ告示", "the Shinkin Bank Leverage Notice"),
    (_NOCHU, "農林中央金庫告示", "the Norinchukin Bank Capital Adequacy Notice"),
    (_NOCHU + _LEV, "農林中央金庫レバレッジ告示", "the Norinchukin Bank Leverage Notice"),
    (_SHOKO, "商工中金告示", "the Shoko Chukin Bank Capital Adequacy Notice"),
    (_SHOKO + _LEV, "商工中金レバレッジ告示", "the Shoko Chukin Bank Leverage Notice"),
    (_COOP, "信用協同組合告示", "the Credit Cooperative Capital Adequacy Notice"),
    (_ROKIN, "労働金庫告示", "the Labour Bank Capital Adequacy Notice"),
    ("農業協同組合等がその経営の健全性を判断するための基準", "農業協同組合等告示", "the Agricultural Cooperative Capital Adequacy Notice"),
    ("漁業協同組合等がその経営の健全性を判断するための基準", "漁業協同組合等告示", "the Fishery Cooperative Capital Adequacy Notice"),
], key=lambda t: -len(t[0]))
NOTICE_TITLE_TO_NAME = {t: n for t, n, _ in NOTICES}
NOTICE_EN = {n: e for _, n, e in NOTICES}
# Short names this notification defines in its Article 1 (法 = 金融商品取引法, 令 = its
# Enforcement Order) — the full instrument, for external_name.
DEFINED_NAMES = {
    "法": ("金融商品取引法", "the Financial Instruments and Exchange Act"),
    "令": ("金融商品取引法施行令", "the Order for Enforcement of the Financial Instruments and Exchange Act"),
}
NOTICE_SUFFIX_RE = re.compile(r"(?:\([^()]*告示第[^()]*号\))?$")
LAW_NAMES = [n for n, _ in LAWS]
LAW_EN = dict(LAWS)

ART = rf"(?:第{N}条(?:の{N})*|前{N}条|前条|次条|同条)"
PARA = rf"(?:第{N}項|前{N}項|前各項|前項|次項|同項)"
ITEM = rf"(?:第{N}号(?:の{N})*|前{N}号|前各号|前号|次号|同号)"
SUBI = rf"(?:[{IROHA}](?![ァ-ヶー]))"
SUB3 = r"(?:[(（][０-９0-9]+[)）])"
TAIL = rf"(?:{SUBI}{SUB3}?|{SUB3})?(?:各号|各項)?"
CORE = rf"(?:{ART}{PARA}?{ITEM}?|{PARA}{ITEM}?|{ITEM})"
UNIT = rf"(?:第{N}章(?:の{N})*)?(?:第{N}節)?(?:第{N}款)?(?:第{N}目)?"
CITE = rf"(?:{CORE}{TAIL}|(?=第{N}[章節款目]){UNIT})"
RANGE = rf"(?:から{CITE}まで)?"
LAW_ALT = "|".join(re.escape(n) for n in LAW_NAMES)
REF_RE = re.compile(rf"(?P<law>{LAW_ALT})?(?P<cite>{CITE}{RANGE})")
KANJI_RE = re.compile(r"[一-鿿々]")

DIG = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def k2i(s):
    total, cur = 0, 0
    for ch in s:
        if ch in DIG:
            cur = DIG[ch]
        else:
            unit = {"十": 10, "百": 100, "千": 1000}[ch]
            total += (cur or 1) * unit
            cur = 0
    return total + cur


def roman(n):
    vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, r in vals:
        while n >= v:
            out += r
            n -= v
    return out


WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
FW = str.maketrans("０１２３４５６７８９", "0123456789")


def _num_chain(s):
    return "-".join(str(k2i(x)) for x in re.findall(N, s))


def _en_one(cite, item_override=None, para_override=None):
    """English for one citation (no range, no law name). *_override replaces the item /
    paragraph wording (used to fold a range like 第一号から第四号まで into one phrase)."""
    m = re.fullmatch(rf"(?P<art>{ART})?(?P<para>{PARA})?(?P<item>{ITEM})?(?P<subi>{SUBI})?(?P<sub3>{SUB3})?(?P<each>各号|各項)?", cite)
    if not m:
        u = re.fullmatch(rf"(?:第({N})章((?:の{N})*))?(?:第({N})節)?(?:第({N})款)?(?:第({N})目)?", cite)
        if not u:
            return None
        parts = []
        if u.group(5): parts.append(f"Division {k2i(u.group(5))}")
        if u.group(4): parts.append(f"Subsection {k2i(u.group(4))}")
        if u.group(3): parts.append(f"Section {k2i(u.group(3))}")
        if u.group(1): parts.append(f"Chapter {'-'.join([str(k2i(u.group(1)))] + [str(k2i(x)) for x in re.findall(N, u.group(2) or '')])}")
        return ", ".join(parts) if len(parts) == 1 else " of ".join(parts)
    art, para, item, subi, sub3, each = (m.group(k) for k in ("art", "para", "item", "subi", "sub3", "each"))

    def art_en(a):
        if a == "前条": return "the preceding Article"
        if a == "次条": return "the following Article"
        if a == "同条": return "the same Article"
        mm = re.fullmatch(rf"前({N})条", a)
        if mm: return f"the preceding {WORDS.get(k2i(mm.group(1)), k2i(mm.group(1)))} Articles"
        return f"Article {_num_chain(a)}"

    def para_en(p):
        if para_override:
            return para_override
        rel = {"前項": "the preceding paragraph", "次項": "the following paragraph", "同項": "the same paragraph", "前各項": "the preceding paragraphs"}
        if p in rel: return rel[p]
        mm = re.fullmatch(rf"前({N})項", p)
        if mm: return f"the preceding {WORDS.get(k2i(mm.group(1)), k2i(mm.group(1)))} paragraphs"
        return f"paragraph ({k2i(p[1:-1])})"

    def item_en(it):
        if item_override:
            return item_override
        rel = {"前号": "the preceding item", "次号": "the following item", "同号": "the same item", "前各号": "the preceding items"}
        if it in rel: return rel[it]
        mm = re.fullmatch(rf"前({N})号", it)
        if mm: return f"the preceding {WORDS.get(k2i(mm.group(1)), k2i(mm.group(1)))} items"
        nums = [k2i(x) for x in re.findall(N, it)]
        return "item (" + roman(nums[0]) + "".join(f"-{x}" for x in nums[1:]) + ")"  # 第二号の二 -> item (ii-2)

    sub = ""
    if subi: sub += f"({chr(ord('a') + IROHA.index(subi))})"
    if sub3: sub += f"({sub3[1:-1].translate(FW)})"

    absolute_art = art and art.startswith("第")
    pieces = []
    # Absolute: "Article 5, paragraph (2), item (i)(a)". Relative containers read
    # inside-out: "item (i) of the preceding paragraph", "paragraph (2) of the same Article".
    if each:
        what = "each item" if each == "各号" else "each paragraph"
    if absolute_art or not art:
        if art: pieces.append(art_en(art))
        if para:
            pe = para_en(para)
            if not para.startswith("第") and item:
                inner = item_en(item) + sub
                base = f"{inner} of {pe}"
                return f"{what} of {base}" if each else base
            pieces.append(pe)
        if item:
            if not item.startswith("第"):
                # relative item: "(a) of the preceding item", "the preceding item"
                ie = f"{sub} of {item_en(item)}" if sub else item_en(item)
                base = f"{ie} of " + ", ".join(pieces) if pieces else ie
                return f"{what} of {base}" if each else base
            pieces.append(item_en(item) + sub)
        elif sub:
            pieces[-1] += sub
        base = ", ".join(pieces)
    else:
        inner = []
        if para: inner.append(para_en(para))
        if item: inner.append(item_en(item) + sub)
        inner = [x for x in inner]
        base = (", ".join(inner) + " of " + art_en(art)) if inner else art_en(art)
    return f"{what} of {base}" if each else base


def to_en(raw):
    """English citation string for a raw Japanese citation, or None if unsupported."""
    m = REF_RE.fullmatch(raw)
    if not m:
        return None
    law, cite = m.group("law"), m.group("cite")
    rng = re.fullmatch(rf"({CITE})から({CITE})まで", cite)
    if rng:
        first, second = rng.group(1), rng.group(2)
        a, b = _en_one(first), _en_one(second)
        if not a or not b:
            return None
        # Fold "X item (i) から item (iv) まで" into X's own wording: "items (i) through (iv)"
        # sits where the single item would ("…items (i) through (iv) of paragraph (2) of
        # the same Article", "Article 5, paragraph (2), items (i) through (iv)").
        if re.fullmatch(rf"{ITEM}", second) and re.search(rf"第{N}号(?:の{N})*$", first):
            fi = re.search(rf"第{N}号(?:の{N})*$", first).group(0)
            en = _en_one(first, item_override=f"items {_en_one(fi)[5:]} through {b[5:]}")
        elif re.fullmatch(rf"{PARA}", second) and re.search(rf"第{N}項$", first):
            fp = re.search(rf"第{N}項$", first).group(0)
            en = _en_one(first, para_override=f"paragraphs {_en_one(fp)[10:]} through {b[10:]}")
        else:
            en = f"{a} through {b}"
    else:
        en = _en_one(cite)
    if not en:
        return None
    return f"{en} of {LAW_EN[law]}" if law else en


def _notice_before(text, start):
    """Name of the full-title notification immediately preceding `start`, if any."""
    head = text[:start]
    tail = NOTICE_SUFFIX_RE.search(head)
    head = head[:tail.start()] if tail else head
    for title, name, _ in NOTICES:
        if head.endswith(title):
            return name
    # "…(平成十九年金融庁告示第五十九号。以下「単体自己資本規制比率告示」という。)第一条":
    # a citation right after a paren that carries a law/notice number belongs to that
    # instrument — named by its 「short name」 when the paren gives one.
    before = text[:start]
    if before.endswith(")"):
        depth, k = 0, len(before) - 1
        while k >= 0:
            depth += {")": 1, "(": -1}.get(before[k], 0)
            if depth == 0:
                break
            k -= 1
        inner = before[k + 1:-1] if k >= 0 else ""
        if re.search(r"(?:告示|府令|省令|規則|命令|法律|政令)第[一二三四五六七八九十百千]+号", inner):
            alias = re.search(r"以下「([^」]+)」という", inner)
            if alias:
                return alias.group(1)
            # otherwise the instrument's name is what precedes its number paren
            name = re.split(r"[、。()「」]", before[:k])[-1] if k > 0 else ""
            return name[-60:] or "（未特定の告示）"
    if head.endswith("基準"):
        return "（未特定の告示）"  # some other notification — external, unidentified
    return None


def extract(text_ja):
    """[{raw_text, scope, external_name, external_name_en}] in order of appearance."""
    out = []
    last_notice = None
    last_law = None
    prev_end, prev_law, prev_law_en = -1, None, None
    for m in REF_RE.finditer(text_ja):
        law, cite = m.group("law"), m.group("cite")
        if not cite:
            continue
        start = m.start()
        # A law/notice NUMBER ("平成十八年金融庁告示第十九号", "法律第五十九号") is not a citation.
        if not law and re.search(r"(?:告示|法律|政令|府令|省令|命令|条約|規則|／)$", text_ja[:start]):
            continue
        if law in ("法", "令"):
            # bare 法/令 only when it isn't the tail of a compound (手法, 方法, 命令 …)
            if start > 0 and KANJI_RE.match(text_ja[start - 1]):
                law, start = None, start + 1
        raw = text_ja[start:m.end()]
        if not raw or raw in ("第", ):
            continue
        law_en = LAW_EN.get(law) if law else None
        if not law:
            notice = _notice_before(text_ja, start)
            if notice:
                law, law_en = notice, NOTICE_EN.get(notice)
                last_notice = notice
            elif prev_law and text_ja[prev_end:start] in ("及び", "並びに", "又は", "若しくは", "、", "及び同告示"):
                # "基準第二条及び第十四条": the second article belongs to the same instrument
                law, law_en = prev_law, prev_law_en
        elif law == "同告示" and last_notice:
            law, law_en = last_notice, NOTICE_EN.get(last_notice)
        prev_end, prev_law, prev_law_en = m.end(), law, law_en
        # The instrument a short name stands for, so link_external_refs.py can find its feed
        # (raw_text keeps the short form; to_en() still renders it as "the Act").
        name, name_en = DEFINED_NAMES.get(law, (law, law_en))
        if law == "同法" and last_law:
            name, name_en = last_law
        elif law and law not in ("同告示", "同令"):
            last_law = (name, name_en)
        out.append({
            "raw_text": raw,
            "scope": "external" if law else "internal",
            "external_name": name,
            "external_name_en": name_en,
        })
    return out


if __name__ == "__main__":
    tests = ["第五条第二項第一号", "第一号イ", "前条第二項", "前項各号", "同条第二項第一号から第四号まで", "法第二条第八項",
             "第二条各号", "第二条の二第一項", "前二項", "第六節第三款第二目", "銀行法第十四条の二第一号", "第四十三条の三の二",
             "第五条第二項第一号ニ", "前号イ", "第八項各号", "第三章", "第七十六条第二項第一号", "同項第三号(１)"]
    for t in tests:
        print(t, "->", to_en(t))
    print(extract("…標準的手法第一条及び法第二条第三十項に規定する。前条第二項の規定により、第一号から第三号までに掲げる"))
