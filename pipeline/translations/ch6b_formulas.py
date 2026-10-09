from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch6b"
C = "fsa-basel-cap-jp.ch6."
A7, A82, A83, A84, A85, A86 = (C + a for a in ("art253-7.", "art254-2.", "art254-3.", "art254-4.", "art254-5.", "art257."))
B2, B3, B31 = (C + a for a in ("art260-2.", "art260-3.", "art261-3."))

# --- 第二百五十三条の七 (Spearman)
v("C6B_RS", "r_{S}", "スピアマンの順位相関指標", "Spearman rank correlation metric", A7 + "p3")
v("C6B_COV", "cov(R_{HPL}, R_{RTPL})", "R_{HPL}とR_{RTPL}との間の共分散", "Covariance between R_{HPL} and R_{RTPL}", A7 + "p3")
v("C6B_SIG_H", "σ_{RHPL}", "R_{HPL}の標準偏差", "Standard deviation of R_{HPL}", A7 + "p3")
v("C6B_SIG_R", "σ_{RRTPL}", "R_{RTPL}の標準偏差", "Standard deviation of R_{RTPL}", A7 + "p3")
v("C6B_R_HPL", "R_{HPL}", "仮想損益を大きさに基づいて変換した順位データ", "Rank data obtained by converting the hypothetical P&L on the basis of magnitude", A7 + "p3")
v("C6B_R_RTPL", "R_{RTPL}", "リスク理論損益を大きさに基づいて変換した順位データ", "Rank data obtained by converting the risk-theoretical P&L on the basis of magnitude", A7 + "p3")
f("p337i0", A7 + "p3", ["C6B_RS = C6B_COV / (C6B_SIG_H * C6B_SIG_R)"],
  nj="分母の標準偏差は、画像上は σ_{R_{HPL}}・σ_{R_{RTPL}}（下付き文字の入れ子）と印刷されている。", ne="The standard deviations in the denominator are printed as σ with the nested subscripts R_{HPL} and R_{RTPL}.")
inline("p337i1", A7 + "p3", "C6B_SIG_H")
inline("p337i2", A7 + "p3", "C6B_SIG_R")

# --- 第二百五十四条の二 (ES with liquidity horizons)
v("C6B_ES", "ES", "期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount calculated by expected shortfall", A82 + "p1")
v("C6B_ES_T", "ES_{T}(P)", "ベース・ホライズンを前提としたポジションP＝(p_{i})に対する全てのリスク・ファクターのショックに係る期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall for shocks to all risk factors of position P = (p_{i}) on the assumption of the base horizon", A82 + "p1")
v("C6B_ES_Tj", "ES_{T}(P, j)", "ポジションP＝(p_{i})のリスク・ファクターの集合Q(p_{i}, j)の各ポジションp_{i}へのショックを勘案した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall taking into account shocks to each position p_{i} in the set Q(p_{i}, j) of risk factors of position P = (p_{i})", A82 + "p1")
v("C6B_LH_j", "LH_{j}", "第二項に規定する期間", "Period provided for in paragraph (2)", A82 + "p1")
v("C6B_LH_j1", "LH_{j−1}", "流動性ホライズンの区分(j−1)の期間", "Period of liquidity horizon category (j−1)", A82 + "p2", "LH_{j}の添字を一つ減らしたもの。", "LH with the index reduced by one.")
v("C6B_T", "T", "ベース・ホライズンの長さ", "Length of the base horizon", A82 + "p1")
f("p339i0", A82 + "p1", ["C6B_ES = sqrt(C6B_ES_T^2 + sum(j, (C6B_ES_Tj * sqrt((C6B_LH_j - C6B_LH_j1) / C6B_T))^2))"],
  nj="総和の添字はj≧2（画像では Σ の下に j≧2 と印刷）。数式の文法に下限の指定がないため注記する。", ne="The summation runs over j ≥ 2 (printed under the Σ); the formula grammar has no lower-bound slot, so it is noted here.")

# --- 第二百五十四条の三 (stressed ES)
v("C6B_ES_S", "ES", "市場混乱時を想定した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall assuming market stress", A83 + "p1")
v("C6B_ES_RS", "ES_{R,S}", "低減したリスク・ファクターについて、市場混乱時を想定した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall assuming market stress for the reduced set of risk factors", A83 + "p1")
v("C6B_ES_RC", "ES_{R,C}", "低減したリスク・ファクターに基づく直近十二月の期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall based on the most recent 12 months for the reduced set of risk factors", A83 + "p1")
v("C6B_ES_FC", "ES_{F,C}", "全てのリスク・ファクターに基づく直近十二月の期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall based on the most recent 12 months for all risk factors", A83 + "p1")
f("p341i0", A83 + "p1", ["C6B_ES_S = C6B_ES_RS * max(C6B_ES_FC / C6B_ES_RC, 1)"])

# --- 第二百五十四条の四 (IMCC)
v("C6B_IMCC", "IMCC", "モデル化可能なリスク・ファクターに基づくマーケット・リスク相当額", "Market risk equivalent amount based on modellable risk factors", A84 + "p1")
v("C6B_IMCC_C", "IMCC(C)", "全リスク・クラスを対象とした市場混乱時を想定した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall assuming market stress covering all risk classes", A84 + "p1")
v("C6B_IMCC_Ci", "IMCC(C_{i})", "五つの各リスク・クラスを対象とした市場混乱時を想定した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall assuming market stress covering each of the five risk classes", A84 + "p1")
v("C6B_ES_RSi", "ES_{R,S,i}", "低減したリスク・ファクターについて、五つの各リスク・クラスを対象とし、ストレス期間を想定して算出した期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall for the reduced set of risk factors, for each of the five risk classes, calculated assuming the stress period", A84 + "p1")
v("C6B_ES_RCi", "ES_{R,C,i}", "五つの各リスク・クラスを対象とし、低減したリスク・ファクターに基づく直近十二月の期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall based on the most recent 12 months for the reduced set of risk factors, for each of the five risk classes", A84 + "p1")
v("C6B_ES_FCi", "ES_{F,C,i}", "五つの各リスク・クラスを対象の全てのリスク・ファクターに基づく直近十二月の期待ショート・フォールにより算出したマーケット・リスク相当額", "Market risk equivalent amount by expected shortfall based on the most recent 12 months for all risk factors, for each of the five risk classes", A84 + "p1")
v("C6B_RHO_I", "ρ", "相関係数（IMCC）", "Correlation coefficient (IMCC)", A84 + "p1", "〇・五", "0.5")
v("C6B_B", "B", "リスク・クラスの総数", "Total number of risk classes", A84 + "p1")
f("p342i0", A84 + "p1", ["C6B_IMCC = C6B_RHO_I * C6B_IMCC_C + (1 - C6B_RHO_I) * sum(i, C6B_B, C6B_IMCC_Ci)"],
  nj="画像では総和（i＝1からBまで）の全体が括弧で括られている。", ne="In the image the whole summation (i = 1 to B) is enclosed in parentheses; here the factor (1 − ρ) multiplies it directly.")
f("p343i0", A84 + "p1", ["C6B_IMCC_C = C6B_ES_RS * (C6B_ES_FC / C6B_ES_RC)"],
  nj="第二百五十四条の三第一項の算式と異なり、max(…, 1)は付されていない（印刷どおり）。", ne="Unlike the formula in Article 254-3, paragraph (1), no max(…, 1) appears here (as printed).")
f("p343i1", A84 + "p1", ["C6B_IMCC_Ci = C6B_ES_RSi * (C6B_ES_FCi / C6B_ES_RCi)"],
  nj="第二百五十四条の三第一項の算式と異なり、max(…, 1)は付されていない（印刷どおり）。", ne="Unlike the formula in Article 254-3, paragraph (1), no max(…, 1) appears here (as printed).")

# --- 第二百五十四条の五 (SES)
v("C6B_SES", "SES", "モデル化不可能なリスク・ファクターに基づくマーケット・リスク相当額を合計したもの", "Sum of the market risk equivalent amounts based on non-modellable risk factors", A85 + "p2")
v("C6B_ISES_i", "ISES_{NM,i}", "信用スプレッドのリスク・ファクターiに対するマーケット・リスク相当額", "Market risk equivalent amount for credit spread risk factor i", A85 + "p2")
v("C6B_ISES_j", "ISES_{NM,j}", "株式の個別リスクのリスク・ファクターjに対するマーケット・リスク相当額", "Market risk equivalent amount for idiosyncratic equity risk factor j", A85 + "p2")
v("C6B_SES_k", "SES_{NM,k}", "モデル化不可能なリスク・ファクターkに対するマーケット・リスク相当額", "Market risk equivalent amount for non-modellable risk factor k", A85 + "p2")
v("C6B_RHO_S", "ρ", "相関係数（SES）", "Correlation coefficient (SES)", A85 + "p2", "〇・六", "0.6")
f("p343i2", A85 + "p2", ["C6B_SES = sqrt(sum(i, C6B_ISES_i^2)) + sqrt(sum(j, C6B_ISES_j^2)) + sqrt((C6B_RHO_S * sum(k, C6B_SES_k))^2 + (1 - C6B_RHO_S^2) * sum(k, C6B_SES_k^2))"],
  nj="画像の総和にはI、J、Kを上限とする記号が付されているが、条文はこれらを定義していないため省略した。", ne="The summations carry upper limits I, J and K in the image, which the article does not define; they are omitted here.")

# --- 第二百五十七条 (k)
v("C6B_K", "k", "資本サーチャージの算式における係数", "Coefficient in the capital surcharge formula", A86 + "p1", "条文には説明がなく、算式のみで定められる。", "Not described in the article text; set only by the formula.")
v("C6B_SUM_A", "Σ_{i∈A}SA_{i}", "アンバー・ゾーンに分類されたトレーディング・デスクiについてのSA_{i}の合計", "Sum of SA_{i} over trading desks i classified in the amber zone (A)", A86 + "p1")
v("C6B_SUM_GA", "Σ_{i∈G,A}SA_{i}", "グリーン・ゾーン又はアンバー・ゾーンに分類されたトレーディング・デスクiについてのSA_{i}の合計", "Sum of SA_{i} over trading desks i classified in the green zone (G) or amber zone (A)", A86 + "p1")
f("p347i0", A86 + "p1", ["C6B_K = 0.5 * (C6B_SUM_A / C6B_SUM_GA)"],
  nj="総和の添字集合（i∈A、i∈G,A）は変数の記号に含めて表した。", ne="The index sets (i∈A, i∈G,A) of the summations are carried in the symbols of the two sums.")

# --- 第二百六十条の二 (delta/vega)
v("C6B_K_b", "K_{b}", "各バケットに対するマーケット・リスク相当額", "Market risk equivalent amount for each bucket", B2 + "p4")
v("C6B_WS_k", "WS_{k}", "リスク・ファクターkに対するリスク加重後の感応度", "Risk-weighted sensitivity for risk factor k", B2 + "p3")
v("C6B_WS_l", "WS_{l}", "リスク・ファクターlに対するリスク加重後の感応度", "Risk-weighted sensitivity for risk factor l", B2 + "p3")
v("C6B_RHO_kl", "ρ_{kl}", "リスク・ファクターkとlとの間の相関係数", "Correlation coefficient between risk factors k and l", B2 + "p4")
v("C6B_GAMMA", "γ_{bc}", "バケットbとcとの間の相関係数", "Correlation coefficient between buckets b and c", B2 + "p5")
v("C6B_S_b", "S_{b}", "リスク加重後の感応度WS_{b}のバケットbの合計額", "Total of the risk-weighted sensitivities WS_{b} of bucket b", B2 + "p5")
v("C6B_S_c", "S_{c}", "リスク加重後の感応度WS_{c}のバケットcの合計額", "Total of the risk-weighted sensitivities WS_{c} of bucket c", B2 + "p5")
v("C6B_MR_RC", "MR_{class}", "各リスク・クラスにおけるデルタ・リスク及びベガ・リスクに対するマーケット・リスク相当額", "Market risk equivalent amount for delta risk and vega risk in each risk class", B2 + "p5", "画像では左辺は文章で印刷されている。", "Printed in words on the left-hand side in the image.")
f("p350i0", B2 + "p4", ["C6B_K_b = sqrt(max(0, sum(k, C6B_WS_k^2) + sum(k, sum(l, C6B_RHO_kl * C6B_WS_k * C6B_WS_l))))"],
  nj="二重総和の内側はl≠k（画像のΣの下に印刷）。", ne="The inner summation excludes l = k (printed under the Σ in the image).")
f("p350i1", B2 + "p5", ["C6B_MR_RC = sqrt(sum(b, C6B_K_b^2) + sum(b, sum(c, C6B_GAMMA * C6B_S_b * C6B_S_c)))"],
  nj="左辺は画像では文章（各リスク・クラスにおけるデルタ・リスク及びベガ・リスクに対する各マーケット・リスク相当額）。二重総和の内側はc≠b。", ne="The left-hand side is printed in words in the image. The inner summation excludes c = b.")
f("p350i2", B2 + "p5", ["C6B_S_b = sum(k, C6B_WS_k)"])
f("p350i3", B2 + "p5", ["C6B_S_c = sum(k, C6B_WS_k)"],
  nj="cのバケットに属するリスク・ファクターkについての総和。", ne="Summation over the risk factors k belonging to bucket c.")
f("p351i0", B2 + "p6", ["C6B_S_b = max(min(sum(k, C6B_WS_k), C6B_K_b), -C6B_K_b)"])
f("p351i1", B2 + "p6", ["C6B_S_c = max(min(sum(k, C6B_WS_k), C6B_K_c), -C6B_K_c)"])
v("C6B_K_c", "K_{c}", "バケットcに対するマーケット・リスク相当額", "Market risk equivalent amount for bucket c", B2 + "p4")

# --- 第二百六十条の三 (curvature)
v("C6B_CVR_P", "CVR_{k}^{+}", "リスク・ファクターkが上方に移動した場合におけるカーベチャー・リスクのリスク加重後の感応度（デルタ・リスクのリスク加重後の感応度を除く。）", "Risk-weighted sensitivity of curvature risk (excluding that of delta risk) where risk factor k moves upward", B3 + "p2")
v("C6B_CVR_M", "CVR_{k}^{−}", "リスク・ファクターkが下方に移動した場合におけるカーベチャー・リスクのリスク加重後の感応度（デルタ・リスクのリスク加重後の感応度を除く。）", "Risk-weighted sensitivity of curvature risk (excluding that of delta risk) where risk factor k moves downward", B3 + "p2")
v("C6B_V_X", "V_{i}(x_{k})", "リスク・ファクターkのx_{k}における商品iの時価", "Market value of instrument i at x_{k} of risk factor k", B3 + "p2")
v("C6B_V_UP", "V_{i}(x_{k}^{RW (Curvature)+})", "リスク・ファクターkが上方に移動した場合の商品iの時価", "Market value of instrument i where risk factor k moves upward", B3 + "p2")
v("C6B_V_DN", "V_{i}(x_{k}^{RW (Curvature)−})", "リスク・ファクターkが下方に移動した場合の商品iの時価", "Market value of instrument i where risk factor k moves downward", B3 + "p2")
v("C6B_RW_C", "RW_{k}^{(Curvature)}", "商品iのリスク・ファクターkに適用されるリスク・ウェイト", "Risk weight applicable to risk factor k of instrument i", B3 + "p2")
v("C6B_S_ik", "s_{ik}", "商品iのリスク・ファクターkのデルタ・リスクの感応度", "Delta risk sensitivity of risk factor k of instrument i", B3 + "p2")
f("p351i2", B3 + "p2", ["C6B_CVR_P = -sum(i, C6B_V_UP - C6B_V_X - C6B_RW_C * C6B_S_ik)"],
  nj="算式中の上方移動後の水準の上付き文字は(Curvature)+と印刷され（定義側ではRW (Curvature)+）、同一の量と読んだ。", ne="The upward-shifted level is printed with superscript (Curvature)+ in the formula but RW (Curvature)+ in its definition; read as the same quantity.")
f("p351i3", B3 + "p2", ["C6B_CVR_M = -sum(i, C6B_V_DN - C6B_V_X + C6B_RW_C * C6B_S_ik)"],
  nj="算式中の下方移動後の水準の上付き文字は(Curvature)−と印刷され（定義側ではRW (Curvature)−）、同一の量と読んだ。", ne="The downward-shifted level is printed with superscript (Curvature)− in the formula but RW (Curvature)− in its definition; read as the same quantity.")
inline("p351i4", B3 + "p2", "C6B_CVR_P")
inline("p351i5", B3 + "p2", "C6B_CVR_M")
inline("p351i6", B3 + "p2", "C6B_V_UP")
inline("p351i7", B3 + "p2", "C6B_V_DN")
inline("p351i8", B3 + "p2", "C6B_RW_C")

v("C6B_K_bP", "K_{b}^{+}", "バケットbについて、リスク・ファクターが上方に移動した場合のマーケット・リスク相当額", "Market risk equivalent amount of bucket b where risk factors move upward", B3 + "p5")
v("C6B_K_bM", "K_{b}^{−}", "バケットbについて、リスク・ファクターが下方に移動した場合のマーケット・リスク相当額", "Market risk equivalent amount of bucket b where risk factors move downward", B3 + "p5")
v("C6B_CVR_Pl", "CVR_{l}^{+}", "リスク・ファクターlが上方に移動した場合におけるカーベチャー・リスクのリスク加重後の感応度", "Risk-weighted sensitivity of curvature risk where risk factor l moves upward", B3 + "p2")
v("C6B_CVR_Ml", "CVR_{l}^{−}", "リスク・ファクターlが下方に移動した場合におけるカーベチャー・リスクのリスク加重後の感応度", "Risk-weighted sensitivity of curvature risk where risk factor l moves downward", B3 + "p2")
v("C6B_RHO_CV", "ρ_{kl}", "リスク・ファクター間の相関係数であり、デルタ・リスクの相関関数を二乗した値", "Correlation coefficient between risk factors, being the value obtained by squaring the delta risk correlation function", B3 + "p5")
v("C6B_PSI_P", "Ψ(CVR_{k}^{+}, CVR_{l}^{+})", "CVR_{k}及びCVR_{l}がいずれも負の場合には零、それ以外の場合には一", "Zero where CVR_{k} and CVR_{l} are both negative, and one otherwise", B3 + "p5")
v("C6B_PSI_M", "Ψ(CVR_{k}^{−}, CVR_{l}^{−})", "CVR_{k}及びCVR_{l}がいずれも負の場合には零、それ以外の場合には一", "Zero where CVR_{k} and CVR_{l} are both negative, and one otherwise", B3 + "p5")
f("p352i0", B3 + "p5", ["C6B_K_b = max(C6B_K_bP, C6B_K_bM)"])
f("p352i1", B3 + "p5", [
  "C6B_K_bP = sqrt(max(0, sum(k, max(C6B_CVR_P, 0)^2) + sum(k, sum(l, C6B_RHO_CV * C6B_CVR_P * C6B_CVR_Pl * C6B_PSI_P))))",
  "C6B_K_bM = sqrt(max(0, sum(k, max(C6B_CVR_M, 0)^2) + sum(k, sum(l, C6B_RHO_CV * C6B_CVR_M * C6B_CVR_Ml * C6B_PSI_M))))"],
  nj="二重総和の内側はl≠k。Ψ(…)は関数の呼び出しではなく、条文の定義する変数として扱った。", ne="The inner summation excludes l = k. Ψ(…) is treated as a variable (as defined in the article) rather than as a function call.")
v("C6B_MR_CV", "MR_{curv}", "各リスク・クラスにおけるカーベチャー・リスクに対するマーケット・リスク相当額", "Market risk equivalent amount for curvature risk in each risk class", B3 + "p6", "画像では左辺は文章で印刷されている。", "Printed in words on the left-hand side in the image.")
v("C6B_GAMMA_CV", "γ_{bc}", "デルタ・リスクの相関関数を二乗した値", "Value obtained by squaring the delta risk correlation function", B3 + "p6")
v("C6B_S_bCV", "S_{b}", "バケットbについてのCVRの合計（上方又は下方に移動した場合）", "Total of CVR for bucket b (upward or downward shift)", B3 + "p6")
v("C6B_S_cCV", "S_{c}", "バケットcについてのCVRの合計（上方又は下方に移動した場合）", "Total of CVR for bucket c (upward or downward shift)", B3 + "p6")
v("C6B_PSI_S", "Ψ(S_{b}, S_{c})", "S_{b}及びS_{c}のいずれも負の場合には零、それ以外の場合には一", "Zero where S_{b} and S_{c} are both negative, and one otherwise", B3 + "p6")
f("p352i2", B3 + "p6", ["C6B_MR_CV = sqrt(max(0, sum(b, C6B_K_b^2) + sum(b, sum(c, C6B_GAMMA_CV * C6B_S_bCV * C6B_S_cCV * C6B_PSI_S))))"],
  nj="左辺は画像では文章（各リスク・クラスにおけるカーベチャー・リスクに対するマーケット・リスク相当額）。二重総和の内側はc≠b。", ne="The left-hand side is printed in words in the image. The inner summation excludes c = b.")
f("p352i3", B3 + "p6", ["C6B_S_bCV = sum(k, C6B_CVR_P)", "C6B_S_bCV = sum(k, C6B_CVR_M)"],
  nj="印刷では二段の場合分け。上段は上方に移動した場合、下段は下方に移動した場合。", ne="Printed as a two-case definition: the first line applies where the risk factors move upward, the second where they move downward.")

# --- 第二百六十一条の三 (delta sensitivities)
v("C6B_S_kr", "s_{k,r_t}", "一般金利リスクのデルタ・リスクの感応度", "Delta risk sensitivity of general interest rate risk", B31 + "p1")
v("C6B_S_kcs", "s_{k,cs_t}", "非証券化商品、証券化商品(非CTP)及び証券化商品(CTP)に係る信用スプレッド・リスクのデルタ・リスクの感応度", "Delta risk sensitivity of credit spread risk relating to non-securitization products, securitization products (non-CTP) and securitization products (CTP)", B31 + "p1")
v("C6B_V_rUP", "V_{i}(r_{t}+0.0001, cs_{t})", "リスクフリー・レートに0.0001を加えた場合の商品iの市場価値", "Market value of instrument i with 0.0001 added to the risk-free rate", B31 + "p1")
v("C6B_V_csUP", "V_{i}(r_{t}, cs_{t}+0.0001)", "信用スプレッドに0.0001を加えた場合の商品iの市場価値", "Market value of instrument i with 0.0001 added to the credit spread", B31 + "p1")
v("C6B_V_rcs", "V_{i}(r_{t}, cs_{t})", "リスクフリー・レート及び信用スプレッドを変数とする関数であり、商品iの市場価値を表すもの", "Function of the risk-free rate and the credit spread as variables, representing the market value of instrument i", B31 + "p1")
v("C6B_S_EQ", "s_{k}", "株式等のデルタ・リスクの感応度", "Delta risk sensitivity of equities, etc.", B31 + "p1")
v("C6B_V_EQUP", "V_{i}(1.01EQ_{k})", "株式等kの現物価格を一パーセント上昇させた場合の商品iの市場価値", "Market value of instrument i with the spot price of equity, etc. k increased by 1 percent", B31 + "p1")
v("C6B_V_EQ", "V_{i}(EQ_{k})", "株式等kの現物価格を変数とする関数であり、商品iの市場価値を表すもの", "Function of the spot price of equity, etc. k as a variable, representing the market value of instrument i", B31 + "p1")
v("C6B_S_RTS", "s_{k}", "株式等レポ・レートのデルタ・リスクの感応度", "Delta risk sensitivity of equity repo rates, etc.", B31 + "p1")
v("C6B_V_RTSUP", "V_{i}(RTS_{k}+0.0001)", "株式等kのレポ・レートに0.0001を加えた場合の商品iの市場価値", "Market value of instrument i with 0.0001 added to the repo rate of equity, etc. k", B31 + "p1")
v("C6B_V_RTS", "V_{i}(RTS_{k})", "株式等kのレポ・レートを変数とする関数であり、商品iの市場価値を表すもの", "Function of the repo rate of equity, etc. k as a variable, representing the market value of instrument i", B31 + "p1")
v("C6B_S_CTY", "s_{k}", "コモディティのデルタ・リスクの感応度", "Delta risk sensitivity of the commodity", B31 + "p1")
v("C6B_V_CTYUP", "V_{i}(1.01CTY_{k})", "コモディティkの現物価格を一パーセント上昇させた場合の商品iの市場価値", "Market value of instrument i with the spot price of commodity k increased by 1 percent", B31 + "p1")
v("C6B_V_CTY", "V_{i}(CTY_{k})", "コモディティkの現物価格を変数とする関数であり、商品iの市場価値を表すもの", "Function of the spot price of commodity k as a variable, representing the market value of instrument i", B31 + "p1")
v("C6B_S_FX", "s_{k}", "外国為替リスクのデルタ・リスクの感応度", "Delta risk sensitivity of foreign exchange risk", B31 + "p1")
v("C6B_V_FXUP", "V_{i}(1.01FX_{k})", "為替レートを一パーセント上昇させた場合の商品iの市場価値", "Market value of instrument i with the exchange rate of currency k increased by 1 percent", B31 + "p1")
v("C6B_V_FX", "V_{i}(FX_{k})", "通貨kの直物為替レートを変数とする関数であり、商品iの市場価値を表すもの", "Function of the spot exchange rate of currency k as a variable, representing the market value of instrument i", B31 + "p1")
f("p359i0", B31 + "p1", ["C6B_S_kr = (C6B_V_rUP - C6B_V_rcs) / 0.0001"])
inline("p359i1", B31 + "p1", "C6B_S_kr")
f("p359i2", B31 + "p1", ["C6B_S_kcs = (C6B_V_csUP - C6B_V_rcs) / 0.0001"])
inline("p359i3", B31 + "p1", "C6B_S_kcs")
f("p359i4", B31 + "p1", ["C6B_S_EQ = (C6B_V_EQUP - C6B_V_EQ) / 0.01"])
f("p359i5", B31 + "p1", ["C6B_S_RTS = (C6B_V_RTSUP - C6B_V_RTS) / 0.0001"])
f("p359i6", B31 + "p1", ["C6B_S_CTY = (C6B_V_CTYUP - C6B_V_CTY) / 0.01"])
f("p360i0", B31 + "p1", ["C6B_S_FX = (C6B_V_FXUP - C6B_V_FX) / 0.01"])
