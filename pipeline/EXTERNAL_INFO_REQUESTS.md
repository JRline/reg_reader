# External information requests

This environment can't reach `www.fsa.go.jp`, `elaws.e-gov.go.jp` or
`www.japaneselawtranslation.go.jp`. That is a network-policy block, so everything below
needs an agent with normal web access. The source PDF of *this* notification
(`pipeline/source/saishu1.pdf`) **is** in the repo, so its own other chapters are not on
this list. They are extraction work, not lookups (see the end of this file).

Generated from the feed data after the Chapter 3 build. The "Cited at" column names
`fsa-basel-cap-jp` article ids, e.g. `ch3.art30` = 第三十条.

## How to deliver

For each provision, return a block like the one below. Plain Markdown or JSON is fine. The
pipeline turns it into a feed (same shape as `feeds/jp-banking-act/`).

```
instrument:  銀行法 (昭和五十六年法律第五十九号)
provision:   第十四条の二
heading:     (見出し as printed, or none)
as_of:       the amendment/version date of the text you copied
source_url:  the exact page
text_ja:     verbatim, one entry per 項; 号 as separate entries under their 項;
             keep the original kanji numerals, parentheses and 「」 exactly
text_en:     the official English translation, ONLY if one exists
             (Japanese Law Translation DB) — give its version date; otherwise leave empty
```

Rules:

- **Verbatim.** Don't normalise punctuation, numerals or full-width/half-width characters.
  The pipeline matches citation strings against the text character for character.
- **No paraphrase in `text_ja`.** If a provision can't be found, say so. Don't
  reconstruct it.
- **English.** Only an official translation goes in `text_en`. Note how current it is,
  since JLT translations often lag amendments. Machine or own translations are done on this
  side.
- **Scope.** Only the cited provision is needed, plus the definitions it relies on if
  they're short. Whole laws aren't needed.

## Priority 1: the other institutions' capital and leverage notices (≈130 citations)

Almost all of these are in **第三十条** (exposures to deposit-taking institutions, the
eight 号 イ–カ listing every regulated deposit-taker type), with a few in 第三十条の二
and 第三十条の三. Each notice is cited for the same three things:

- the definition of its minimum/buffer ratios
- the "Pillar 1 compliant" article
- the article on the leverage ratio

| Short name used in the feed | Full title (abbrev.) | Number | Provisions cited |
|---|---|---|---|
| 銀行告示 | 銀行法第十四条の二の規定に基づき、銀行がその保有する資産等に照らし自己資本の充実の状況が適当であるかどうかを判断するための基準 | 平成十八年金融庁告示第十九号 | 第一条第十号の二, 第十号の三; 第二条 (+第一号); 第二条の二第一項; 第十四条 (+第一号); 第十四条の二第一項; 第二十五条; 第三十七条 |
| 銀行レバレッジ告示 | (bank) …補完的指標として定めるレバレッジに係る健全性を判断するための基準 | 平成三十一年金融庁告示第十一号 | 第二条第一項, 第二項; 第五条第一項 |
| 銀行持株会社告示 | 銀行法第五十二条の二十五の規定に基づき、銀行持株会社が…自己資本の充実の状況が適当であるかどうかを判断するための基準 | 平成十八年金融庁告示第二十号 | 第一条第十号の二, 第十号の三; 第二条 (+第一号); 第二条の二第一項; 第十四条 |
| 銀行持株会社レバレッジ告示 | (BHC leverage) | 平成三十一年金融庁告示第十二号 | 第二条第一項 |
| 信用金庫告示 | 信用金庫法第八十九条第一項において準用する銀行法第十四条の二の規定に基づき、信用金庫及び信用金庫連合会が…判断するための基準 | 平成十八年金融庁告示第二十一号 | 第一条第九号の二, 第九号の三; 第二条; 第十一条; 第十九条 (+第一号); 第十九条の二第一項; 第三十一条 (+第一号); 第三十一条の二第一項 |
| 信用金庫レバレッジ告示 | (shinkin leverage) | 平成三十一年金融庁告示第十四号 | 第二条第一項, 第二項; 第五条第一項 |
| 農林中央金庫告示 | 農林中央金庫がその経営の健全性を判断するための基準 | 平成十八年金融庁・農林水産省告示第四号 | 第二条 (+第一号); 第二条の二第一項; 第十四条 (+第一号); 第十四条の二第一項 |
| 農林中央金庫レバレッジ告示 | (Norinchukin leverage) | 平成三十一年金融庁・農林水産省告示第四号 | 第二条第一項, 第二項; 第五条第一項 |
| 商工中金告示 | 株式会社商工組合中央金庫がその経営の健全性を判断するための基準 | 平成二十年金融庁・財務省・経済産業省告示第二号 | 第二条 (+第一号); 第二条の二第一項; 第十四条 (+第一号); 第十四条の二第一項 |
| 商工中金レバレッジ告示 | (Shoko Chukin leverage) | 平成三十一年金融庁・財務省・経済産業省告示第三号 | 第二条第一項, 第二項; 第五条第一項 |
| 信用協同組合告示 | 協同組合による金融事業に関する法律第六条第一項において準用する銀行法第十四条の二の規定に基づき、信用協同組合及び信用協同組合連合会が…判断するための基準 | 平成十八年金融庁告示第二十二号 | 第一条第二号; 第二条; 第十一条 |
| 労働金庫告示 | 労働金庫法第九十四条第一項において準用する銀行法第十四条の二の規定に基づき、労働金庫及び労働金庫連合会が…判断するための基準 | 平成十八年金融庁・厚生労働省告示第七号 | 第一条第七号の三; 第二条; 第十一条 |
| 農業協同組合等告示 | 農業協同組合等がその経営の健全性を判断するための基準 | 平成十八年金融庁・農林水産省告示第二号 | 第一条第七号ニ; 第二条; 第十条 |
| 漁業協同組合等告示 | 漁業協同組合等がその経営の健全性を判断するための基準 | 平成十八年金融庁・農林水産省告示第三号 | 第一条第七号ホ; 第二条; 第十条 |

The full titles are in 第三十条第七項 of this notification (`ch3.art30.p7`) if exact
wording is needed for search. They are published on the FSA site (告示 pages under
`fsa.go.jp/common/law/`), and the bank, BHC and co-op ones are also on e-Gov.

## Priority 2: statutes (e-Gov)

| Law | Provisions | Cited at |
|---|---|---|
| 銀行法 (昭和五十六年法律第五十九号) | 第十四条の二; 第五十二条の二十五 | ch3.art30 |
| 〃 | 第十六条の二第一項第五号, 第五号の二, 第九号 | ch3.art77 |
| 金融商品取引法 (昭和二十三年法律第二十五号; "法" in this notification) | 第二条第二十七項, 第三十項 | ch3.art30, art47, art49 |
| 〃 | 第五十七条の十七第二項 | ch3.art47 |
| 信用金庫法 | 第八十九条第一項 | ch3.art30 |
| 株式会社商工組合中央金庫法 | 第二十三条第一項 | ch3.art30 |
| 協同組合による金融事業に関する法律 | 第六条第一項 | ch3.art30 |
| 労働金庫法 | 第九十四条第一項 | ch3.art30 |
| 商品先物取引法 | 第二条第二十項 | ch3.art47, art49 |
| 貸金業法施行令 (昭和五十八年政令第百八十一号) | 第一条の二第三号 | ch3.art77, art81 |
| 中小企業信用保険法 (昭和二十五年法律第二百六十四号) | 第二条第五項; 第十二条 | ch3.art41 |
| 公的年金制度の健全性及び信頼性の確保のための厚生年金保険法等の一部を改正する法律 (平成二十五年法律第六十三号) | 附則第三条第十一号 (definition of 存続厚生年金基金) | ch3.art77 |
| 株式会社地域経済活性化支援機構法 (平成二十一年法律第六十三号) | definition of 株式会社地域経済活性化支援機構 (the law's Art. 1/2 is enough) | ch3.art42 |
| 弁護士法/外国弁護士による法律事務の取扱い等に関する法律 ("外国弁護士法") | 第二条第三号 (the definition cited in 第二百二十五条 of Chapter 5) | ch5.art225 |
| 特定債務等の調整の促進のための特定調停に関する法律 (平成十一年法律第百五十八号) | 第二条第三項 | ch5.art245-2 |
| 金融商品取引業等に関する内閣府令 (平成十九年内閣府令第五十二号) | 第百二十三条第一項第二十一号の十, 第二十一号の十一 | ch6.art252-2 |
| 金融商品取引法 | 第二条第十六項 (the same Act as above) | ch6.art252-2 |
| 連結財務諸表の用語、様式及び作成方法に関する規則 | the article cited as 「同条第八号」 at ch2.art5 (context: the article cited just before it in that paragraph) | ch2.art5 |

`jp-fiea` already holds FIEA 第二条第八項. 第二十七項/第三十項 can be added to the same
feed. `jp-banking-act` holds only 第五十二条の二十三.

## Priority 3: other FSA notices

| Instrument | Provisions | Cited at |
|---|---|---|
| 最終指定親会社TLAC告示 | 第四条第二項第四号 (the feed `jp-tlac-notification` has only Art. 1–2) | ch3.art43-3-2 (also ch2.art7-2 cites 第四条第一項/第二項) |
| 最終指定親会社が経営の健全性の状況を記載した書面に記載すべき事項を定める件 (平成二十二年十二月金融庁告示第百三十二号) | 第三条 | ch3.art58 |
| 取引先リスク相当額及び基礎的リスク相当額の算出の基準等を定める件 (平成十九年金融庁告示第五十九号, "単体自己資本規制比率告示") | 第一条第四十号 | ch3.art65 |
| 特別金融商品取引業者及びその子法人等の…基準を定める件 (平成二十二年金融庁告示第百二十八号) | the provision cited at ch2.art4 | ch2.art4 |

**Added with Chapter 1 and the 附則** (cited in 第一条's definitions and in the amending 附則):

| Law | Provisions | Cited at |
|---|---|---|
| 金融商品取引法 | 第二条第九項, 第十七項, 第二十一項第五号, 第二十二項第六号, 第二十三項, 第二十九項; 第二十八条第一項; 第五十七条の十二第一項, 第三項; 第五十七条の十七第一項 (also the version before the 附則's amendments); 第五十八条; 第六十七条第二項 | ch1.art1, fusoku.s00, s03 |
| 預金保険法 | 第二条第一項, 第五項 | ch1.art1 |
| 農業協同組合法 (昭和二十二年法律第百三十二号) | 第十条第一項第三号 | ch1.art1 |
| 水産業協同組合法 (昭和二十三年法律第二百四十二号) | 第十一条第一項第四号, 第八十七条第一項第四号, 第九十三条第一項第二号, 第九十七条第一項第二号 | ch1.art1 |
| 商品先物取引法 | 第二条第四項, 第十七項, 第十八項 | ch1.art1 |
| 銀行法 | 第二条第十三項, 第十条第二項第八号 | ch1.art1 |
| 保険業法 | 第二条第二項, 第十六項, 第十八項 | ch1.art1 |
| 財務諸表等の用語、様式及び作成方法に関する規則 (昭和三十八年大蔵省令第五十九号) | 第八条第三項 | ch1.art1 |
| 銀行TLAC告示 / 銀行持株会社TLAC告示 (both 平成三十一年金融庁告示) | 第一条第八号; 第四条第三項, 第四項 | ch1.art1 |
| the amended notices' own provisions named in the 附則 (銀行告示 第七十九条の二第三項第一号ロ; 銀行持株会社告示 第五十七条の二第三項第一号ロ; 信用金庫告示 第七十四条第三項第一号ロ; 信用協同組合告示 第五十一条第三項第一号ロ) | as listed | fusoku.s12 |
| (the 附則 s13 amends an unnamed notice: 第一条, 第二条の二, 第三条第一項, 第二十三条, 第三十一条, 第四十七条第一項第二号ロ — identify which notice 平成二七年一一月二六日金融庁告示第七八号 amends) | | fusoku.s13 |

## Priority 4: two formula readings to confirm

Both are transcribed from images in `saishu1.pdf`, and both carry a ⚠ note in the reader.
A higher-resolution or HTML copy of the notice (FSA site, or the 官報 text) settles them.

1. **第四十七条第十四項 (`f-ch3-p106i2`, equity add-on).** The outer exponent of
   `AddOn_Equity = ((Σ ρ·AddOn)² + Σ (1−ρ²)·AddOn²)^(1/2)` is barely legible. It was
   transcribed as **1/2**, which matches Basel CRE52 and the credit formula in 第十三項.
   Confirm it isn't 1/3.
2. **第七十六条第三項 (`f-ch3-p133i1`, haircut scaling).** The PDF prints
   `H = H_M × √((N_R − (T_M − 1)) / T_M)`. Basel CRE22.59 and this notification's own
   第四十七条第三項第一号 have **`N_R + (T_M − 1)`**. Is the minus in the official text,
   i.e. a misprint in the notice itself?

**Added with Chapters 4–7 (all transcribed from the PDF image; each has a ⚠ note in the reader):**

3. **第二百三十一条 / 第二百三十五条 etc. (K_SSFA formula, `f-ch5a-p237i5`, `f-ch5b-p254i2`).** The denominator and
   the exponent print a glyph that looks like the digit 1 in "a(u−1)" / "e^(a·1)". Both were read as the
   lowercase letter l, the variable the article defines as `l = max(A − K, 0)`. Confirm it isn't the digit.
4. **第二百四十五条 (`f-ch5b-p255i0`, sub-pool K_A).** The second term EAD_Subpool2/EAD_Total prints with no
   ×0.5, whereas Basel has ×0.5 and paragraph (1) of the same article uses W·0.5. Possible misprint.
5. **第二百四十八条の四の二十四 (`p293t1` table, rows 10 and 15).** The text layer reads "一二・〇" stacked over two
   lines; transcribed as 12.0, as in `p290t1`. Confirm.
6. **第二百四十八条の四の八 (`f-ch52-p283i0`).** Is the left-hand subscript k or b (WS_k vs WS_b)?
7. **Chapter 7 第二百八十三条第二項 formulas** carry overlines (three-year averages) that the formula grammar can't draw;
   the reader's note says so. A look at the image confirms what the overline covers.
8. **第百二十九条 and 第百三十五条 (Chapter 4).** The text of 第百二十九条第一項第二号's ただし書 sits after the
   definition of N rather than M, and 第百三十五条第七項 cites 前条第五項 where 第百三十四条第七項 seems intended
   — check against the official text whether these are misprints.

## Priority 5: English terminology (optional, improves translation quality)

All `text_en` in Chapters 2–3 is `llm_draft`. Useful references:

- The official English translations of 銀行法 and 金融商品取引法 (Japanese Law Translation
  DB), for defined-term consistency: 子法人等, 自己資本規制比率, 特定取引勘定 …
- The FSA's English summaries of the Basel III final-rule implementation, if any. These
  give the FSA's own English names for 標準的手法, 信用リスク・アセット, ADC向け
  エクスポージャー, etc.
- The BIS Basel Framework, chapters CRE20–CRE22 (standardised approach and CRM) and
  CRE51–CRE52 (counterparty credit risk). Chapter 3 tracks these closely. A table mapping
  Chapter 3 articles to CRE paragraphs would let the reader link each article to its
  Basel source.

## Not on this list, because the repo already has it

This notification is now complete in the reader (Chapters 1–7, 別表, 附則). What stays unresolved
within it is by design: item-level citations (前号/次号/第N号), 「」-quoted replacement phrases, and 附則
citations that point into amending notices not in the feed.
