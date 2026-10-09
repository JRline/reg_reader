from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch52"
C2 = "fsa-basel-cap-jp.ch5-2."
C3 = "fsa-basel-cap-jp.ch5-3."

# ---------------- Chapter 5-3, Article 248-7 ----------------
A7 = C3 + "art248-7.p1"
v("CH52_K_CMi", "K_{CMi}", "所要自己資本額", "Required capital amount", A7)
v("CH52_K_CCP", "K_{CCP}", "適格中央清算機関に係る所要自己資本額（EAD_{i}の合計に0.2及び0.08を乗じた額）", "Required capital amount of the qualifying central counterparty (sum of EAD_{i} times 0.2 times 0.08)", A7)
v("CH52_DFpref_i", "DF_{i}^{pref}", "適格中央清算機関に直接清算参加者iが拠出した清算基金の額", "Amount of the default fund contributed to the qualifying central counterparty by direct clearing participant i", A7)
v("CH52_DF_CCP", "DF_{CCP}", "適格中央清算機関が有する資本その他これに類するものであって、直接清算参加者の債務不履行により生ずる損失を清算基金と同時に又は先立ち負担するものの額", "Amount of the capital and similar resources of the qualifying central counterparty that bear default losses simultaneously with, or ahead of, the default fund", A7)
v("CH52_DFpref_CM", "DF_{CM}^{pref}", "適格中央清算機関に直接清算参加者が拠出した清算基金の額の合計", "Total amount of the default fund contributed to the qualifying central counterparty by direct clearing participants", A7)
v("CH52_EAD_i", "EAD_{i}", "適格中央清算機関が有する直接清算参加者iに対するトレード・エクスポージャーの額", "Amount of the trade exposure the qualifying central counterparty has to direct clearing participant i", A7)
f("p307i0", A7, ["CH52_K_CMi = max(CH52_K_CCP * (CH52_DFpref_i / (CH52_DF_CCP + CH52_DFpref_CM)), 0.08 * 0.02 * CH52_DFpref_i)"])
f("p307i1", A7, ["CH52_K_CCP = sum(i, CH52_EAD_i) * 0.2 * 0.08"],
  nj="Σ の範囲は EAD_{i} のみとして表示している（0.2及び0.08を乗じる位置は結果に影響しない）。",
  ne="The summation is shown over EAD_{i} only; whether 0.2 and 0.08 sit inside or outside the sum does not change the result.")
inline("p307i2", A7, "CH52_DFpref_i")
inline("p307i3", A7, "CH52_DFpref_CM")

# ---------------- Chapter 5-2, Article 248-3-3 ----------------
B1 = C2 + "art248-3-3.p1"; B2 = C2 + "art248-3-3.p2"; B4 = C2 + "art248-3-3.p4"; B5 = C2 + "art248-3-3.p5"; B7 = C2 + "art248-3-3.p7"
v("idx_c", "c", "和の添字（取引相手方c）", "Summation index (counterparty c)", B1)
v("idx_NS", "NS", "和の添字（ネッティング・セットNS）", "Summation index (netting set NS)", B2)
v("idx_hc", "h∈c", "和の添字（取引相手方cの単一の債務者を参照するヘッジ取引h）", "Summation index (single-name hedge h of counterparty c)", B4)
v("CH52_K_full", "K_{full}", "完全なBA―CVAによる所要自己資本額", "Required capital amount under the full BA-CVA", B1)
v("CH52_K_reduced", "K_{reduced}", "ヘッジ効果を反映しない場合の所要自己資本額", "Required capital amount without reflecting hedging effects", B1)
v("CH52_K_hedged", "K_{hedged}", "ヘッジ効果を反映した場合の所要自己資本額", "Required capital amount reflecting hedging effects", B1)
v("CH52_beta", "β", "β（〇・二五）", "β (0.25)", B1)
v("CH52_rho", "ρ", "ρ（〇・五）", "ρ (0.5)", B1)
v("CH52_SCVA_c", "SCVA_{c}", "取引相手方cとの全てのネッティング・セットに対するCVA資本賦課", "CVA capital charge for all netting sets with counterparty c", B1)
v("CH52_SNH_c", "SNH_{c}", "取引相手方cのCVAリスクに対する全てのシングル・ネーム・ヘッジを用いたヘッジ効果の値", "Value of the hedging effect of all single-name hedges on the CVA risk of counterparty c", B1)
v("CH52_IH", "IH", "インデックスを用いたヘッジ取引から生ずる全ての取引相手方のCVAリスクに対するヘッジ効果の値", "Value of the hedging effect on the CVA risk of all counterparties arising from index hedge transactions", B1)
v("CH52_HMA_c", "HMA_{c}", "取引相手方cのCVAリスクに対する全てのヘッジ取引の値", "Value of all hedge transactions on the CVA risk of counterparty c", B1)
v("CH52_alpha", "α", "α（一・四）", "α (1.4)", B2)
v("CH52_RW_c", "RW_{c}", "取引相手方cのリスク・ウェイト", "Risk weight of counterparty c", B2)
v("CH52_M_NS", "M_{NS}", "ネッティング・セットNSの実効マチュリティ", "Effective maturity of netting set NS", B2)
v("CH52_EAD_NS", "EAD_{NS}", "ネッティング・セットNSの与信相当額", "Credit equivalent amount of netting set NS", B2)
v("CH52_DF_NS", "DF_{NS}", "ネッティング・セットNSのディスカウント・ファクター", "Discount factor of netting set NS", B2)
v("CH52_r_hc", "r_{hc}", "ヘッジ取引hの取引相手方cとの関係に応じた値", "Value according to the relationship of hedge h to counterparty c", B4)
v("CH52_RW_h", "RW_{h}", "単一の債務者を参照するヘッジ取引hのリスク・ウェイト", "Risk weight of hedge transaction h referencing a single obligor", B4)
v("CH52_M_h_SN", "M_{h}^{SN}", "単一の債務者を参照するヘッジ取引hの実効マチュリティ", "Effective maturity of hedge transaction h referencing a single obligor", B4)
v("CH52_B_h_SN", "B_{h}^{SN}", "単一の債務者を参照するヘッジ取引hの想定元本額", "Notional amount of hedge transaction h referencing a single obligor", B4)
v("CH52_DF_h_SN", "DF_{h}^{SN}", "単一の債務者を参照するヘッジ取引hのディスカウント・ファクター", "Discount factor of hedge transaction h referencing a single obligor", B4)
v("CH52_RW_i", "RW_{i}", "インデックス・ヘッジに適用されるリスク・ウェイト", "Risk weight applied to index hedge i", C2 + "art248-3-3.p6")
v("CH52_M_i_ind", "M_{i}^{ind}", "インデックス・ヘッジiの残存マチュリティ", "Remaining maturity of index hedge i", B5)
v("CH52_B_i_ind", "B_{i}^{ind}", "インデックス・ヘッジiの想定元本額", "Notional amount of index hedge i", B5)
v("CH52_DF_i_ind", "DF_{i}^{ind}", "インデックス・ヘッジiのディスカウント・ファクター", "Discount factor of index hedge i", B5)

f("p277i0", B1, ["CH52_K_reduced = sqrt((CH52_rho * sum(idx_c, CH52_SCVA_c))^2 + (1 - CH52_rho^2) * sum(idx_c, CH52_SCVA_c^2))"])
f("p277i1", B1, ["CH52_K_hedged = sqrt((CH52_rho * sum(idx_c, (CH52_SCVA_c - CH52_SNH_c)) - CH52_IH)^2 + (1 - CH52_rho^2) * sum(idx_c, (CH52_SCVA_c - CH52_SNH_c)^2) + sum(idx_c, CH52_HMA_c))"])
f("p277i2", B2, ["CH52_SCVA_c = (1 / CH52_alpha) * CH52_RW_c * sum(idx_NS, CH52_M_NS * CH52_EAD_NS * CH52_DF_NS)"])
f("p277i3", B2, ["CH52_DF_NS = (1 - exp(-0.05 * CH52_M_NS)) / (0.05 * CH52_M_NS)"])
f("p278i0", B4, ["CH52_SNH_c = sum(idx_hc, CH52_r_hc * CH52_RW_h * CH52_M_h_SN * CH52_B_h_SN * CH52_DF_h_SN)"])
inline("p279i0", B4, "CH52_M_h_SN")
inline("p279i1", B4, "CH52_B_h_SN")
inline("p279i2", B4, "CH52_DF_h_SN")
f("p279i3", B4, ["CH52_DF_h_SN = (1 - exp(-0.05 * CH52_M_h_SN)) / (0.05 * CH52_M_h_SN)"])
f("p279i4", B5, ["CH52_IH = sum(i, CH52_RW_i * CH52_M_i_ind * CH52_B_i_ind * CH52_DF_i_ind)"])
inline("p279i5", B5, "CH52_M_i_ind")
inline("p279i6", B5, "CH52_B_i_ind")
inline("p279i7", B5, "CH52_DF_i_ind")
f("p279i8", B5, ["CH52_DF_i_ind = (1 - exp(-0.05 * CH52_M_i_ind)) / (0.05 * CH52_M_i_ind)"])
f("p279i9", B7, ["CH52_HMA_c = sum(idx_hc, (1 - CH52_r_hc^2) * (CH52_RW_h * CH52_M_h_SN * CH52_B_h_SN * CH52_DF_h_SN)^2)"])

# ---------------- Chapter 5-2, Article 248-4-8 ----------------
D2 = C2 + "art248-4-8.p2"; D3 = C2 + "art248-4-8.p3"; D4 = C2 + "art248-4-8.p4"; D5 = C2 + "art248-4-8.p5"; D6 = C2 + "art248-4-8.p6"
v("idx_kb", "k∈b", "和の添字（バケットbに含まれるリスク・ファクターk）", "Summation index (risk factor k in bucket b)", D5)
v("idx_lb", "l∈b, l≠k", "和の添字（バケットbに含まれるk以外のリスク・ファクターl）", "Summation index (risk factor l in bucket b other than k)", D5)
v("idx_kc", "k∈c", "和の添字（バケットcに含まれるリスク・ファクターk）", "Summation index (risk factor k in bucket c)", D6)
v("idx_b", "b", "和の添字（バケットb）", "Summation index (bucket b)", D6)
v("idx_cb", "c≠b", "和の添字（b以外のバケットc）", "Summation index (bucket c other than b)", D6)
v("CH52_s_k_CVA", "s_{k}^{CVA}", "CVAカバー取引を対象に計測されるCVAの合計値に対するリスク・ファクターkの感応度（ネット感応度）", "Net sensitivity of risk factor k of the total CVA measured for the CVA cover transactions", D2)
v("CH52_s_k_Hdg", "s_{k}^{Hdg}", "全ての適格SA―CVAヘッジ取引の市場価格の合計値に対するリスク・ファクターkの感応度（ネット感応度）", "Net sensitivity of risk factor k of the total market value of all eligible SA-CVA hedge transactions", D2)
v("CH52_RW_k", "RW_{k}", "リスク・ファクターkのリスク・ウェイト", "Risk weight of risk factor k", D3)
v("CH52_WS_k_CVA", "WS_{k}^{CVA}", "ネット感応度s_{k}^{CVA}に係る加重感応度", "Weighted sensitivity of net sensitivity s_{k}^{CVA}", D3)
v("CH52_WS_k_Hdg", "WS_{k}^{Hdg}", "ネット感応度s_{k}^{Hdg}に係る加重感応度", "Weighted sensitivity of net sensitivity s_{k}^{Hdg}", D3)
v("CH52_WS_k", "WS_{k}", "リスク・ファクターkのネット加重感応度", "Net weighted sensitivity of risk factor k", D4)
v("CH52_WS_l", "WS_{l}", "リスク・ファクターlのネット加重感応度", "Net weighted sensitivity of risk factor l", D5)
v("CH52_K_b", "K_{b}", "バケットbのCVAリスク相当額", "CVA risk equivalent amount of bucket b", D5)
v("CH52_K_c", "K_{c}", "バケットcのCVAリスク相当額", "CVA risk equivalent amount of bucket c", D6)
v("CH52_rho_kl", "ρ_{kl}", "リスク・ファクターの感応度の相関係数", "Correlation coefficient between the sensitivities of the risk factors", D5)
v("CH52_R", "R", "ヘッジング・ディスアローアンス（〇・〇一）", "Hedging disallowance (0.01)", D5, "CVAリスクが完全にヘッジされない可能性を考慮したCVAリスク相当額の追加分をいう。", "The additional amount of the CVA risk equivalent amount that takes into account the possibility that CVA risk is not fully hedged.")
v("CH52_K_class", "K", "リスク・クラスごとのCVAリスク相当額", "CVA risk equivalent amount for the risk class", D6)
v("CH52_m_CVA", "m_{CVA}", "乗数", "Multiplier", C2 + "art248-4-10.p1")
v("CH52_gamma_bc", "γ_{bc}", "各リスク・クラスに適用される相関係数", "Correlation coefficient applied to each risk class", D6)
v("CH52_S_b", "S_{b}", "バケットbに含まれる全てのリスク・ファクターの加重感応度の合計（－K_{b}を下限、K_{b}を上限とする）", "Sum of the weighted sensitivities of all risk factors in bucket b (floored at −K_{b} and capped at K_{b})", D6)
v("CH52_S_c", "S_{c}", "バケットcに係るS_{b}と同様の方法で計測した値", "Value measured for bucket c in the same manner as S_{b}", D6)

f("p282i2", D3, ["CH52_WS_k_CVA = CH52_RW_k * CH52_s_k_CVA"])
f("p282i3", D3, ["CH52_WS_k_Hdg = CH52_RW_k * CH52_s_k_Hdg"])
inline("p282i0", D2, "CH52_s_k_CVA")
inline("p282i1", D2, "CH52_s_k_Hdg")
inline("p282i4", D3, "CH52_WS_k_CVA")
inline("p282i5", D3, "CH52_s_k_CVA")
inline("p282i6", D3, "CH52_WS_k_Hdg")
inline("p282i7", D3, "CH52_s_k_Hdg")
f("p283i0", D4, ["CH52_WS_k = CH52_WS_k_CVA - CH52_WS_k_Hdg"],
  nj="左辺の添字はPDF画像上でkともbとも読めるが、右辺及び次の算式に合わせてkと読んだ。",
  ne="The subscript on the left-hand side is hard to tell between k and b in the PDF image; it is read as k, consistent with the right-hand side and the following formulas.")
f("p283i1", D5, ["CH52_K_b = sqrt(max(0, sum(idx_kb, CH52_WS_k^2) + sum(idx_kb, sum(idx_lb, CH52_rho_kl * CH52_WS_k * CH52_WS_l))) + CH52_R * sum(idx_kb, CH52_WS_k_Hdg^2))"])
f("p283i2", D6, ["CH52_K_class = CH52_m_CVA * sqrt(sum(idx_b, CH52_K_b^2) + sum(idx_b, sum(idx_cb, CH52_gamma_bc * CH52_S_b * CH52_S_c)))"])
f("p283i3", D6, ["CH52_S_b = max(-CH52_K_b, min(sum(idx_kb, CH52_WS_k), CH52_K_b))"],
  nj="原文は max と min の引数をセミコロンで区切って表記している。", ne="The original separates the arguments of max and min with semicolons; shown here with commas.")
f("p283i4", D6, ["CH52_S_c = max(-CH52_K_c, min(sum(idx_kc, CH52_WS_k), CH52_K_c))"],
  nj="原文は max と min の引数をセミコロンで区切って表記している。", ne="The original separates the arguments of max and min with semicolons; shown here with commas.")
