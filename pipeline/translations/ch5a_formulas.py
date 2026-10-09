from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch5a"
C = "fsa-basel-cap-jp.ch5."

# Article 230-231: IRB-based method
v("C5A_RW", "RW", "リスク・ウェイト", "Risk weight", C + "art230.p1")
v("C5A_KIRB", "K_{IRB}", "内部格付手法による裏付資産の所要自己資本率", "Required capital ratio of the underlying assets under the internal ratings-based approach", C + "art232.p1",
  "裏付資産の所要自己資本の額の合計額を裏付資産のエクスポージャーの総額で除した値", "Total required capital amount of the underlying assets divided by the total amount of the exposures of the underlying assets")
v("C5A_A", "A", "アタッチメント・ポイント", "Attachment point", C + "art234.p1")
v("C5A_D", "D", "デタッチメント・ポイント", "Detachment point", C + "art234.p2")
v("C5A_KSSFA", "K_{SSFA}(K_{IRB})", "K_{IRB}超過部分の所要自己資本率", "Required capital ratio for the portion in excess of K_{IRB}", C + "art231.p1")
v("C5A_a", "a", "指数 a(＝−1/(p×K_{IRB}))", "Exponent a (= −1/(p × K_{IRB}))", C + "art231.p1")
v("C5A_u", "u", "u(＝D−K_{IRB})", "u (= D − K_{IRB})", C + "art231.p1")
v("C5A_l", "l", "l(＝max(A−K_{IRB}, 0))", "l (= max(A − K_{IRB}, 0))", C + "art231.p1")

f("p237i1", C + "art230.p1", ["C5A_RW = ((C5A_KIRB - C5A_A) / (C5A_D - C5A_A)) * 12.5 + ((C5A_D - C5A_KIRB) / (C5A_D - C5A_A)) * 12.5 * C5A_KSSFA"])
inline("p237i0", C + "art230.p1", "C5A_KSSFA")
inline("p237i2", C + "art230.p1", "C5A_KSSFA")
inline("p237i4", C + "art231.p1", "C5A_KSSFA")
f("p237i5", C + "art231.p1", ["C5A_KSSFA = (exp(C5A_a * C5A_u) - exp(C5A_a * C5A_l)) / (C5A_a * (C5A_u - C5A_l))"],
  nj="分母および指数中の「l」は、画像上は数字の「1」に似た字形で印刷されているが、本文の「l＝max(A－K_{IRB}，0)」に対応するlと読んだ。",
  ne="In the image the letter l in the denominator and in the exponent of the second term is printed in a glyph resembling the digit 1; it is read as l, the variable defined in the text as l = max(A − K_{IRB}, 0).")

# Article 235: parameter p inputs
v("C5A_N", "N", "エクスポージャーの実効的な個数", "Effective number of exposures", C + "art235.p4")
v("C5A_EAD_i", "EAD_{i}", "裏付資産に含まれる第i番目のエクスポージャーのEAD", "EAD of the i-th exposure included in the underlying assets", C + "art235.p4")
v("C5A_LGD", "LGD", "裏付資産の加重平均LGD", "Weighted average LGD of the underlying assets", C + "art235.p5")
v("C5A_LGD_i", "LGD_{i}", "第i番目のエクスポージャーの加重平均LGD", "Weighted average LGD of the i-th exposure", C + "art235.p5")
v("C5A_C1", "C_{1}", "裏付資産のうち最もEADの大きいエクスポージャーが裏付資産総額に占める割合", "Proportion of the exposure with the largest EAD to the total amount of the underlying assets", C + "art235.p7")
v("C5A_Cm", "C_{m}", "最もEADの大きいものから順にm個のエクスポージャーのEAD合計額が裏付資産のEAD総額に占める割合", "Proportion that the total EAD of the m exposures with the largest EADs represents of the total EAD of the underlying assets", C + "art235.p7")
v("C5A_m", "m", "エクスポージャーの個数(m)", "Number of exposures (m)", C + "art235.p7")
v("C5A_MT", "M_{T}", "証券化エクスポージャーの残存期間", "Residual maturity of the securitization exposure", C + "art235.p8")
v("C5A_CF_t", "CF_{t}", "期間tに証券化エクスポージャーの保有者に対し契約上支払われるキャッシュ・フロー", "Cash flow contractually paid to the holder of the securitization exposure in period t", C + "art235.p8")

f("p244i0", C + "art235.p4", ["C5A_N = (sum(i, C5A_EAD_i))^2 / sum(i, C5A_EAD_i^2)"])
f("p244i1", C + "art235.p5", ["C5A_LGD = sum(i, C5A_LGD_i * C5A_EAD_i) / sum(i, C5A_EAD_i)"])
f("p245i0", C + "art235.p7", ["C5A_N = (C5A_C1 * C5A_Cm + ((C5A_Cm - C5A_C1) / (C5A_m - 1)) * max(1 - C5A_m * C5A_C1, 0))^(-1)"])
f("p245i1", C + "art235.p8", ["C5A_MT = sum(t, t * C5A_CF_t) / sum(t, C5A_CF_t)"])
