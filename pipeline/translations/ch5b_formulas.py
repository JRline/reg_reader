"""Formulas for the Chapter 5 slice 第二百三十九条の四–第二百四十八条 (SSFA under the standardized approach-compliant method)."""
from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch5b"
C = "fsa-basel-cap-jp.ch5."
A240, A241, A242 = C + "art240.p1", C + "art241.p1", C + "art242.p2"

v("CH5B_RW", "RW", "リスク・ウェイト", "Risk weight", C + "art240.p1",
  "第二百四十条第一項第三号の算式により算出される比率。", "The ratio calculated by the formula in Article 240, paragraph (1), item (iii).")
v("CH5B_KA", "K_{A}", "延滞率を勘案した裏付資産の所要自己資本率", "Required capital ratio of the underlying assets taking the delinquency rate into account", C + "art242.p1")
v("CH5B_A", "A", "アタッチメント・ポイント", "Attachment point", A241)
v("CH5B_D", "D", "デタッチメント・ポイント", "Detachment point", A241)
v("CH5B_KSSFA", "K_{SSFA}(K_{A})", "K_A超過部分の所要自己資本率", "Required capital ratio of the portion exceeding K_A", A241,
  "次に掲げる算式により算出される値。", "The value calculated by the formula given in Article 241.")
v("CH5B_a", "a", "パラメーターa", "Parameter a", A241, "a＝－(1／(p＊K_{A}))。pは1(再証券化エクスポージャーは1.5)。", "a = -(1/(p * K_A)), where p is 1 (1.5 for re-securitization exposures).")
v("CH5B_u", "u", "パラメーターu", "Parameter u", A241, "u＝D－K_{A}。", "u = D - K_A.")
v("CH5B_l", "l", "パラメーターl", "Parameter l", A241, "l＝max(A－K_{A}，0)。", "l = max(A - K_A, 0).")
v("CH5B_EAD1", "EAD_{Subpool1}", "延滞状況を把握していない原資産に係る部分以外のエクスポージャーの総額", "Total exposures of the underlying assets other than the portion relating to original assets with untracked delinquency status", A242)
v("CH5B_EAD2", "EAD_{Subpool2}", "延滞状況を把握していない原資産に係る部分のエクスポージャーの総額", "Total exposures of the underlying assets relating to original assets with untracked delinquency status", A242)
v("CH5B_EADT", "EAD_{Total}", "裏付資産のエクスポージャーの総額", "Total exposures of the underlying assets", A242)
v("CH5B_KA_SP1", "K_{A}^{Subpool1}", "延滞状況を把握していない原資産に係る部分以外の部分について算出したK_A", "K_A calculated for the portion other than that relating to original assets with untracked delinquency status", A242)

inline("p253i0", A240, "CH5B_KSSFA")
f("p253i1", A240, ["CH5B_RW = ((CH5B_KA - CH5B_A) / (CH5B_D - CH5B_A)) * 12.5 + ((CH5B_D - CH5B_KA) / (CH5B_D - CH5B_A)) * 12.5 * CH5B_KSSFA"])
inline("p253i2", A240, "CH5B_KSSFA")
inline("p254i1", A241, "CH5B_KSSFA")
f("p254i2", A241, ["CH5B_KSSFA = (exp(CH5B_a * CH5B_u) - exp(CH5B_a * CH5B_l)) / (CH5B_a * (CH5B_u - CH5B_l))"],
  nj="分母は印字上「a(u−1)」と読めるが、第二百四十一条本文が定義するlと同じ字形の「1」が分子の指数(a・l)にも現れるため、l(エル)と判読した。",
  ne="The denominator prints as \"a(u-1)\", but the same glyph appears in the numerator exponent (a·l), and the article defines l; it is read as the letter l (u - l), not the digit 1.")
f("p255i0", A242, ["CH5B_KA = (CH5B_EAD1 / CH5B_EADT) * CH5B_KA_SP1 + CH5B_EAD2 / CH5B_EADT"],
  nj="印字のとおり転記した。第二項のEAD_{Subpool2}の項には係数(0.5)が印字されていない(第一項の算式のW・0.5とは異なる)。",
  ne="Transcribed as printed: the EAD_Subpool2 term carries no 0.5 factor (cf. W · 0.5 in paragraph (1)); not altered.")
inline("p255i1", A242, "CH5B_KA_SP1")
inline("p255i2", A242, "CH5B_KA_SP1")
