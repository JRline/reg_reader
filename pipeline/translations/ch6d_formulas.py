from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch6d"
C = "fsa-basel-cap-jp.ch6."
A3 = C + "art267-3."
A9 = C + "art269-2."

v("CH6D_HBR_b", "HBR_{b}", "バケットbにおけるヘッジ効果の係数", "Hedge benefit ratio in bucket b", A3 + "p3")
v("CH6D_netJTD", "netJTD_{i}", "商品iのネットのJTDリスク・ポジション", "Net JTD risk position of product i", A3 + "p3")
v("CH6D_RW", "RW_{i}", "リスク・ウェイト", "Risk weight of product i", A3 + "p4", "第二項に定めるリスク・ウェイト(第二百六十九条の二第三項では商品iに適用するリスク・ウェイト)。", "The risk weight under paragraph (2) (in Article 269-2, paragraph (3), the risk weight applied to product i).")
v("CH6D_DRC_b", "DRC_{b}", "バケットbにおけるデフォルト・リスクに対するマーケット・リスク相当額", "Market risk equivalent amount for default risk in bucket b", A3 + "p4")
v("CH6D_ILONG", "i∈long", "バケットbにおけるロング・ポジションとなっている商品iについての和の添字", "Summation index over products i that are long positions in bucket b", A3 + "p3")
v("CH6D_ISHORT", "i∈short", "バケットbにおけるショート・ポジションとなっている商品iについての和の添字", "Summation index over products i that are short positions in bucket b", A3 + "p3")
v("CH6D_ILONG_C", "i∈Long", "バケットbにおけるロング・ポジションとなっている商品iについての和の添字", "Summation index over products i that are long positions in bucket b", A9 + "p3")
v("CH6D_ISHORT_C", "i∈Short", "バケットbにおけるショート・ポジションとなっている商品iについての和の添字", "Summation index over products i that are short positions in bucket b", A9 + "p3")
v("CH6D_DRC_CTP", "DRC_{CTP}", "証券化商品(CTP)のデフォルト・リスクに対するマーケット・リスク相当額", "Market risk equivalent amount for default risk of securitization products (CTP)", A9 + "p3")
v("CH6D_HBR_CTP", "HBR_{CTP}", "コリレーション・トレーディング・ポートフォリオに含まれる全てのポジションを用いて算出した証券化商品(CTP)のヘッジ効果の係数", "Hedge benefit ratio of securitization products (CTP) calculated using all positions in the correlation trading portfolio", A9 + "p3")

f("p393i0", A3 + "p3", ["CH6D_HBR_b = sum(CH6D_ILONG, CH6D_netJTD) / (sum(CH6D_ILONG, CH6D_netJTD) + sum(CH6D_ISHORT, abs(CH6D_netJTD)))"])
f("p393i1", A3 + "p4", ["CH6D_DRC_b = max((sum(CH6D_ILONG, CH6D_RW * CH6D_netJTD)) - CH6D_HBR_b * (sum(CH6D_ISHORT, CH6D_RW * abs(CH6D_netJTD))), 0)"],
  nj="画像では第一の和の RW の添字 i と netJTD_i が重なって印字されている。第二の和および第二百六十九条の二第三項の同型の算式に合わせ RW_i・netJTD_i と読んだ。",
  ne="In the image the subscript i of RW and netJTD_i overlap in the first sum, and no multiplication dot is printed. Read as RW_i · netJTD_i, matching the second sum and the same-form formula in Article 269-2, paragraph (3).")
f("p398i0", A9 + "p3", ["CH6D_DRC_CTP = max(sum(b, max(CH6D_DRC_b, 0) + 0.5 * min(CH6D_DRC_b, 0)), 0)"])
f("p398i1", A9 + "p3", ["CH6D_DRC_b = (sum(CH6D_ILONG_C, CH6D_RW * CH6D_netJTD)) - CH6D_HBR_CTP * (sum(CH6D_ISHORT_C, CH6D_RW * abs(CH6D_netJTD)))"])
f("p398i2", A9 + "p3", ["CH6D_HBR_CTP = sum(CH6D_ILONG_C, CH6D_netJTD) / (sum(CH6D_ILONG_C, CH6D_netJTD) + sum(CH6D_ISHORT_C, abs(CH6D_netJTD)))"])
