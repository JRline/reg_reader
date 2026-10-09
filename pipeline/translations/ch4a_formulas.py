from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch4a"
C = "fsa-basel-cap-jp.ch4."
A129, A133, A135, A136, A141 = (C + a for a in ("art129.", "art133.", "art135.", "art136.", "art141."))

# --- Articles 129, 136-138: IRB risk-weight function
v("C4A_K", "K", "所要自己資本率", "Required capital ratio", A129 + "p1")
v("C4A_R", "R", "相関係数", "Correlation coefficient", A129 + "p1")
v("C4A_b", "b", "マチュリティ調整", "Maturity adjustment", A129 + "p1", "第一項第四号の算式で算出する。", "Calculated by the formula in paragraph (1), item (iv).")
v("C4A_LGD", "LGD", "デフォルト時損失率", "Loss given default", A133 + "p1")
v("C4A_PD", "PD", "デフォルト確率", "Probability of default", C + "art132.p1", "第百三十二条に定める一年間のPD。", "The one-year PD provided in Article 132.")
v("C4A_EL", "EL", "期待損失率", "Expected loss rate", A129 + "p1", "PDにLGDを乗じた率。PDが百パーセントの場合は第百九十四条第六項に定めるEL_{default}。", "The rate obtained by multiplying PD by LGD; where PD is 100%, EL_{default} provided in Article 194, paragraph (6).")
v("C4A_M", "M", "マチュリティ(実効マチュリティ)", "Maturity (effective maturity)", A135 + "p1", "第百三十五条に定める。PDが百パーセントの場合は一。", "Provided in Article 135; 1 where PD is 100%.")
v("C4A_G_PD", "G(PD)", "N{x}の逆関数G(x)のPDにおける値", "Value at PD of G(x), the inverse function of N{x}", A129 + "p1", "N{x}は標準正規分布の累積分布関数。", "N{x} is the cumulative distribution function of the standard normal distribution.")
v("C4A_G_999", "G(0.999)", "N{x}の逆関数G(x)の0.999における値", "Value at 0.999 of G(x), the inverse function of N{x}", A129 + "p1")
v("C4A_S", "S", "事業法人の売上高(単位：億円)", "Sales of the corporate (in units of 100 million yen)", A129 + "p2", "第一条第五十一号ただし書の場合は総資産。五億円に満たない場合は五億円。", "Total assets in the case of the proviso to Article 1, item (li); calculated as 500 million yen where less than that.")

KBASE = "C4A_K = (C4A_LGD * Phi((1 - C4A_R)^(-0.5) * C4A_G_PD + (C4A_R / (1 - C4A_R))^0.5 * C4A_G_999) - C4A_EL)"
KNOTE_J = "原文のN{x}は標準正規分布の累積分布関数であり、Phiで表示する。G(PD)・G(0.999)は逆関数G(x)の値として一つの記号で表す。原文の角括弧・波括弧は丸括弧で表す。"
KNOTE_E = "The printed N{x} (cumulative distribution function of the standard normal distribution) is rendered as Phi. G(PD) and G(0.999) (values of the inverse function G(x)) are each kept as a single symbol. Square and curly brackets are shown as round parentheses."
f("p160i0", A129 + "p1", [KBASE + " * (1 - 1.5 * C4A_b)^(-1) * (1 + (C4A_M - 2.5) * C4A_b)"], nj=KNOTE_J, ne=KNOTE_E)
FR = "((1 - exp(-50 * C4A_PD)) / (1 - exp(-50)))"
f("p161i0", A129 + "p1", ["C4A_R = 0.12 * " + FR + " + 0.24 * (1 - " + FR + ")"])
f("p161i1", A129 + "p2", ["C4A_R = 0.12 * " + FR + " + 0.24 * (1 - " + FR + ") - 0.04 * (1 - (C4A_S - 5) / 45)"])
f("p162i0", A129 + "p5", ["C4A_R = 0.12 * " + FR + " + 0.3 * (1 - " + FR + ")"])

# retail (Articles 136-138); the K formula is the one without the maturity adjustment
for anchor, art, r in (("p176i0", "art136.p1", "0.15"), ("p176i1", "art137.p1", "0.04")):
    f(anchor, C + art, [KBASE, "C4A_R = " + r], nj=KNOTE_J + "第二行の相関係数の値は、算式の下に括弧書きで印刷されている(相関係数(R)＝" + r + ")ものを算式の一部として示した。",
      ne=KNOTE_E + " The second line gives the value of R, which the PDF prints in parentheses beneath the formula (correlation coefficient (R) = " + r + ") and which the text extraction dropped.")
f("p176i2", C + "art138.p1", [KBASE], nj=KNOTE_J, ne=KNOTE_E)
FR35 = "((1 - exp(-35 * C4A_PD)) / (1 - exp(-35)))"
f("p177i0", C + "art138.p1", ["C4A_R = 0.03 * " + FR35 + " + 0.16 * (1 - " + FR35 + ")"])

# --- Article 133: LGD with collateral
v("C4A_LGD_star", "LGD^{*}", "信用リスク削減手法の効果を勘案したLGD", "LGD taking into account the effect of credit risk mitigation techniques", A133 + "p3")
v("C4A_LGD_U", "LGD_{U}", "エクスポージャーの区分に応じて設定される値", "Value set according to the category of exposure", A133 + "p3", "第二項各号に掲げるエクスポージャーの区分に応じて設定される値。", "The value set according to the category of exposure listed in the items of paragraph (2).")
v("C4A_LGD_S", "LGD_{S}", "担保資産の区分に応じた表のLGD", "LGD set in the table according to the category of collateral asset", A133 + "p3", "次項の表に掲げる担保資産の区分に応じ、同表において設定される値。", "The value set in the table of paragraph (4) according to the category of collateral asset.")
v("C4A_E", "E", "エクスポージャーの額", "Exposure amount", A133 + "p3")
v("C4A_E_S", "E_{S}", "担保の評価額", "Value of the collateral after haircuts", A133 + "p3", "C・(1－H_{C}－H_{fx})により計算される値。上限はE・(1＋H_{E})。", "The value calculated as C·(1 − H_{C} − H_{fx}), capped at E·(1 + H_{E}).")
v("C4A_H_E", "H_{E}", "取引の相手方に引き渡した資産に適用するボラティリティ調整率", "Haircut applied to the asset delivered to the counterparty", A133 + "p3", "エクスポージャーが第四十五条第一項の表の第七号に該当する場合に、前章第六節第三款の規定により適用する。", "Applied under Section 6, Subsection 3 of the preceding Chapter where the exposure falls under item (vii) of the table in Article 45, paragraph (1).")
v("C4A_LGD_ss", "LGD^{**}", "複数の担保の信用リスク削減手法の効果を勘案したLGD", "LGD taking into account the effect of credit risk mitigation techniques of multiple items of collateral", A133 + "p6")
v("C4A_LGD_Si", "LGD_{S_{i}}", "担保資産の区分iに応じて第四項により設定されるLGD_{S}", "LGD_{S} set under paragraph (4) according to collateral asset category i", A133 + "p6")
v("C4A_E_Si", "E_{S_{i}}", "担保資産の区分iに応じて計算されるC・(1－H_{C}－H_{fx})", "C·(1 − H_{C} − H_{fx}) calculated according to collateral asset category i", A133 + "p6", "ΣE_{S_i}がE・(1＋H_{E})を上回る場合は、E_{S_i}の合計がE・(1＋H_{E})と等しくなるよう調整する。", "Adjusted so that the sum of E_{S_i} equals E·(1 + H_{E}) if the sum would exceed it.")
v("C4A_LGD_floor", "LGD_{floor}", "信用リスク削減手法の効果を勘案したLGDの推計値の下限", "Floor of the LGD estimate taking into account the effect of credit risk mitigation techniques", A133 + "p8")
v("C4A_LGD_Ufloor", "LGD_{Ufloor}", "LGD_{U}に係る下限(二十五パーセント)", "Floor for LGD_{U} (25%)", A133 + "p8", "二十五パーセント。", "25%.")
v("C4A_LGD_Sfloor", "LGD_{Sfloor}", "担保資産の区分に応じた表のLGDの下限", "LGD floor set in the table according to the category of collateral asset", A133 + "p8", "次項の表に掲げる担保資産の区分に応じ、同表において設定される値。", "The value set in the table of paragraph (9) according to the category of collateral asset.")
DEN = "(C4A_E * (1 + C4A_H_E))"
f("p166i0", A133 + "p3", [f"C4A_LGD_star = C4A_LGD_U * ((C4A_E * (1 + C4A_H_E) - C4A_E_S) / {DEN}) + C4A_LGD_S * (C4A_E_S / {DEN})"])
f("p169i0", A133 + "p6", [f"C4A_LGD_ss = C4A_LGD_U * ((C4A_E * (1 + C4A_H_E) - sum(i, C4A_E_Si)) / {DEN}) + sum(i, C4A_LGD_Si * (C4A_E_Si / {DEN}))"])
inline("p170i0", A133 + "p6", "C4A_LGD_Si")
inline("p170i1", A133 + "p6", "C4A_E_Si")
f("p170i2", A133 + "p6", ["sum(i, C4A_E_Si)"], display="inline")
f("p170i3", A133 + "p6", ["sum(i, C4A_E_Si)"], display="inline")
f("p170i4", A133 + "p8", [f"C4A_LGD_floor = C4A_LGD_Ufloor * ((C4A_E * (1 + C4A_H_E) - C4A_E_S) / {DEN}) + C4A_LGD_Sfloor * (C4A_E_S / {DEN})"])

# --- Article 141: other retail LGD floor
v("C4A_LGD_Rfloor", "LGD_{Rfloor}", "信用リスク削減手法の効果を勘案したその他リテール向けエクスポージャーのLGDの推計値の下限", "Floor of the LGD estimate for other retail exposures taking into account the effect of credit risk mitigation techniques", A141 + "p3")
v("C4A_LGD_RUfloor", "LGD_{RUfloor}", "LGD_{RUfloor}(三十パーセント)", "LGD_{RUfloor} (30%)", A141 + "p3", "三十パーセント。", "30%.")
v("C4A_LGD_RSfloor", "LGD_{RSfloor}", "担保資産の区分に応じた表のLGDの下限", "LGD floor set in the table according to the category of collateral asset", A141 + "p3", "次項の表に掲げる担保資産の区分に応じ、同表において設定される値。", "The value set in the table of paragraph (4) according to the category of collateral asset.")
f("p178i0", A141 + "p3", [f"C4A_LGD_Rfloor = C4A_LGD_RUfloor * ((C4A_E * (1 + C4A_H_E) - C4A_E_S) / {DEN}) + C4A_LGD_RSfloor * (C4A_E_S / {DEN})"])

# --- Article 135: effective maturity
v("C4A_t", "t", "期間", "Period", A135 + "p1")
v("C4A_CF", "CF_{t}", "期間tにおいて債務者が債権者に契約上支払いうるキャッシュ・フロー", "Cash flow the obligor may contractually pay to the creditor in period t", A135 + "p1")
v("C4A_EE_eff", "EE_{eff,t_{k}}", "実効EE_{tk}", "Effective EE_{tk}", A135 + "p7", "実効EE_{tk}＝max(実効EE_{tk－1}、EE_{tk})。実効EE_{t0}はカレント・エクスポージャー。", "Effective EE_{tk} = max(effective EE_{tk−1}, EE_{tk}); effective EE_{t0} is the current exposure.")
v("C4A_EE", "EE_{t_{k}}", "将来の時点t_{k}における期待エクスポージャー", "Expected exposure at future time t_{k}", A135 + "p7", "EE_{t0}はカレント・エクスポージャー。", "EE_{t0} is the current exposure.")
v("C4A_dt", "Δt_{k}", "t_{k}－t_{k－1}", "t_{k} − t_{k−1}", A135 + "p7")
v("C4A_df", "df_{k}", "将来の期間t_{k}にわたるリスクフリー・レートによる割引率", "Discount factor at the risk-free rate over the future period t_{k}", A135 + "p7")
v("C4A_m", "m", "一年を超えない最後の時点t_{m}の添字", "Index of the last time t_{m} that does not exceed one year", A135 + "p7")
v("C4A_n", "n", "満期の時点を超えない最後の時点t_{n}の添字", "Index of the last time t_{n} that does not exceed the time of maturity", A135 + "p7")
v("C4A_idx_k1", "k=1", "和の添字(k＝1からmまで)", "Summation index (k = 1 to m)", A135 + "p7")
v("C4A_idx_km", "k=m+1", "和の添字(k＝m＋1からnまで)", "Summation index (k = m + 1 to n)", A135 + "p7")
f("p174i0", A135 + "p1", ["C4A_M = sum(t, C4A_t * C4A_CF) / sum(t, C4A_CF)"])
NUM = "sum(C4A_idx_k1, C4A_m, C4A_EE_eff * C4A_dt * C4A_df)"
f("p175i0", A135 + "p7", [f"C4A_M = ({NUM} + sum(C4A_idx_km, C4A_n, C4A_EE * C4A_dt * C4A_df)) / {NUM}"])
