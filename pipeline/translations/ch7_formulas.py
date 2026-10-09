from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch7"
C = "fsa-basel-cap-jp.ch7."
A1 = C + "art283.p1"
A2 = C + "art283.p2"
T1 = C + "artappx1.p1"
v("CH7_ILDC", "ILDC", "金利要素", "Interest component (ILDC)", A2, "BICの構成要素のうち、預金業務等の規模部分", "The part of the BIC components reflecting the scale of deposit-taking business, etc.")
v("CH7_SC", "SC", "役務要素", "Services component (SC)", A2, "BICの構成要素のうち、役務取引等の規模部分", "The part of the BIC components reflecting the scale of fee and commission transactions, etc.")
v("CH7_FC", "FC", "金融商品要素", "Financial instruments component (FC)", A2, "BICの構成要素のうち、金融商品取引の規模部分", "The part of the BIC components reflecting the scale of financial instruments transactions")
v("CH7_IINC", "資金運用収益", "資金運用収益", "Interest income", T1)
v("CH7_IEXP", "資金調達費用", "資金調達費用", "Interest expenses", T1)
v("CH7_IEA", "金利収益資産", "金利収益資産", "Interest-earning assets", T1)
v("CH7_DIV", "受取配当金", "受取配当金", "Dividends received", T1)
v("CH7_FINC", "役務取引等収益", "役務取引等収益", "Fee and commission income", T1)
v("CH7_FEXP", "役務取引等費用", "役務取引等費用", "Fee and commission expenses", T1)
v("CH7_OINC", "その他業務収益", "その他業務収益", "Income from other operations", T1)
v("CH7_OEXP", "その他業務費用", "その他業務費用", "Expenses on other operations", T1)
v("CH7_TRD", "トレーディング商品のネット損益", "トレーディング商品のネット損益", "Net profit or loss on trading products", T1)
v("CH7_NTRD", "トレーディング商品以外の勘定のネット損益", "トレーディング商品以外の勘定のネット損益", "Net profit or loss on accounts other than trading products", T1)
OL = ("The printed formula has an overline over each operand (for the first formula, over Abs(…), over the interest-earning assets and over the dividends received); "
      "paragraph (2) says each overlined part uses the total of the averages over the most recent three years. The overlines are not drawn here.")
OLJ = "原文の算式では各項(第一式では Abs(…)、金利収益資産、受取配当金)に上線が付されている。第二項により、上線部分は直近三年間の平均値を合計した額を用いる。ここでは上線を表示していない。"
f("p420i0", A2, ["CH7_ILDC = min(abs(CH7_IINC - CH7_IEXP), 2.25% * CH7_IEA) + CH7_DIV"], nj=OLJ, ne=OL)
f("p420i1", A2, ["CH7_SC = max(CH7_FINC, CH7_FEXP) + max(CH7_OINC, CH7_OEXP)"], nj=OLJ.replace("第一式では Abs(…)、金利収益資産、受取配当金","各項"), ne="The printed formula has an overline over each of the four operands; paragraph (2) says each overlined part uses the total of the averages over the most recent three years. The overlines are not drawn here.")
f("p420i2", A2, ["CH7_FC = abs(CH7_TRD) + abs(CH7_NTRD)"], nj=OLJ.replace("第一式では Abs(…)、金利収益資産、受取配当金","各Abs(…)"), ne="The printed formula has an overline over each Abs(…) term; paragraph (2) says each overlined part uses the total of the averages over the most recent three years. The overlines are not drawn here.")
