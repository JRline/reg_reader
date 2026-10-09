from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "ch6c"
C = "fsa-basel-cap-jp.ch6."
A4 = C + "art261-4.p1"
A33 = C + "art263-3."
A34 = C + "art263-4."
A35 = C + "art263-5."
A64 = C + "art264."
A642 = C + "art264-2."
A65 = C + "art265."
A652 = C + "art265-2."

# --- Article 261-4: vega risk sensitivity
v("C6C_SK", "s_{k}", "オプション・リスクのベガ・リスクの感応度", "Vega risk sensitivity of option risk", A4)
v("C6C_SIG", "σ_{i}", "オプション性を含む商品iのインプライド・ボラティリティ", "Implied volatility of instrument i, which includes optionality", A4)
v("C6C_DSIG", "Δσ_{i}", "インプライド・ボラティリティの微小な変化幅", "Small change width applied to the implied volatility", A4)
v("C6C_V1", "V_{i}(σ_{i}+Δσ_{i})", "商品iのインプライド・ボラティリティをΔσ_{i}変化させた値を変数とする商品iの市場価値", "Market value of instrument i with its implied volatility changed by Δσ_{i}", A4)
v("C6C_V0", "V_{i}(σ_{i})", "商品iのインプライド・ボラティリティを変数とする関数であり、商品iの市場価値を表すもの", "Market value of instrument i as a function of its implied volatility", A4)
f("p360i1", A4, ["C6C_SK = (C6C_V1 - C6C_V0) / C6C_DSIG * C6C_SIG"],
  nj="原文の算式の右側には「(=vega×σ_{i})」という注記が括弧書きで付されているが、ここでは表示していない。V_{i}(σ_{i}+Δσ_{i})、V_{i}(σ_{i})は関数記法のため別の変数として表記している。",
  ne="The printed formula is followed by the parenthetical remark \"(= vega × σ_{i})\", which is not drawn here. V_{i}(σ_{i}+Δσ_{i}) and V_{i}(σ_{i}) are function values and are represented as two variables.")

# --- Article 263-3: correlation between risk factors (non-securitization credit spread) and buckets
v("C6C_RHO", "ρ_{kl}", "リスク・ファクター間の相関係数", "Correlation coefficient between risk factors k and l", A33 + "p3")
v("C6C_RHO_NAME", "ρ_{kl}^{(name)}", "感応度kと感応度lの銘柄に係る相関係数", "Correlation coefficient relating to the names of sensitivities k and l", A33 + "p4")
v("C6C_RHO_TENOR", "ρ_{kl}^{(tenor)}", "感応度kと感応度lのテナーに係る相関係数", "Correlation coefficient relating to the tenors of sensitivities k and l", A33 + "p4")
v("C6C_RHO_BASIS", "ρ_{kl}^{(basis)}", "感応度kと感応度lのカーブに係る相関係数", "Correlation coefficient relating to the curves (basis) of sensitivities k and l", A33 + "p4")
v("C6C_KB", "K_{b (other bucket)}", "バケットbのリスク加重後の感応度の合算値(当該バケットが「その他」のバケットである場合)", "Aggregate of the risk-weighted sensitivities of bucket b (where the bucket is the \"other\" bucket)", A33 + "p6")
v("C6C_WS_k", "WS_{k}", "リスク・ファクターkのリスク加重後の感応度", "Risk-weighted sensitivity of risk factor k", A33 + "p6")
v("C6C_GAMMA", "γ_{bc}", "バケット間の相関係数", "Correlation coefficient between buckets b and c", A33 + "p7")
v("C6C_GAMMA_RATING", "γ_{bc}^{(rating)}", "信用度に係るバケット間の相関係数", "Correlation coefficient between buckets relating to credit quality (rating)", A33 + "p8")
v("C6C_GAMMA_SECTOR", "γ_{bc}^{(sector)}", "セクターに係るバケット間の相関係数", "Correlation coefficient between buckets relating to sector", A33 + "p8")

f("p368i0", A33 + "p3", ["C6C_RHO = C6C_RHO_NAME * C6C_RHO_TENOR * C6C_RHO_BASIS"])
inline("p368i1", A33 + "p4", "C6C_RHO_NAME")
inline("p368i2", A33 + "p4", "C6C_RHO_TENOR")
inline("p368i3", A33 + "p4", "C6C_RHO_BASIS")
inline("p368i4", A33 + "p4", "C6C_RHO_NAME")
inline("p368i5", A33 + "p4", "C6C_RHO_TENOR")
inline("p369i0", A33 + "p4", "C6C_RHO_BASIS")
inline("p369i1", A33 + "p5", "C6C_RHO_NAME")
inline("p369i2", A33 + "p5", "C6C_RHO_TENOR")
inline("p369i3", A33 + "p5", "C6C_RHO_BASIS")
inline("p369i4", A33 + "p5", "C6C_RHO_NAME")
inline("p369i5", A33 + "p5", "C6C_RHO_TENOR")
inline("p369i6", A33 + "p5", "C6C_RHO_BASIS")
f("p369i7", A33 + "p6", ["C6C_KB = sum(k, abs(C6C_WS_k))"])
f("p369i8", A33 + "p7", ["C6C_GAMMA = C6C_GAMMA_RATING * C6C_GAMMA_SECTOR"])
inline("p369i9", A33 + "p8", "C6C_GAMMA_RATING")
inline("p369i10", A33 + "p8", "C6C_GAMMA_SECTOR")
inline("p369i11", A33 + "p8", "C6C_GAMMA_RATING")
inline("p369i12", A33 + "p8", "C6C_GAMMA_SECTOR")

# --- Article 263-4: securitization products (CTP)
f("p372i0", A34 + "p3", ["C6C_RHO = C6C_RHO_NAME * C6C_RHO_TENOR * C6C_RHO_BASIS"])
inline("p372i1", A34 + "p4", "C6C_RHO_NAME")
inline("p372i2", A34 + "p4", "C6C_RHO_TENOR")
inline("p372i3", A34 + "p4", "C6C_RHO_BASIS")
inline("p372i4", A34 + "p4", "C6C_RHO_NAME")
inline("p372i5", A34 + "p4", "C6C_RHO_TENOR")
inline("p372i6", A34 + "p4", "C6C_RHO_BASIS")
f("p372i7", A34 + "p5", ["C6C_GAMMA = C6C_GAMMA_RATING * C6C_GAMMA_SECTOR"])
inline("p372i8", A34 + "p6", "C6C_GAMMA_RATING")
inline("p372i9", A34 + "p6", "C6C_GAMMA_SECTOR")
inline("p372i10", A34 + "p6", "C6C_GAMMA_RATING")
inline("p373i0", A34 + "p6", "C6C_GAMMA_SECTOR")

# --- Article 263-5: securitization products (non-CTP)
v("C6C_RHO_TRANCHE", "ρ_{kl}^{(tranche)}", "感応度kと感応度lの銘柄(トランシェ)に係る相関係数", "Correlation coefficient relating to the names (tranches) of sensitivities k and l", A35 + "p4")
f("p375i0", A35 + "p3", ["C6C_RHO = C6C_RHO_TRANCHE * C6C_RHO_TENOR * C6C_RHO_BASIS"])
inline("p375i1", A35 + "p4", "C6C_RHO_TRANCHE")
inline("p375i2", A35 + "p4", "C6C_RHO_TENOR")
inline("p375i3", A35 + "p4", "C6C_RHO_BASIS")
inline("p375i4", A35 + "p4", "C6C_RHO_TRANCHE")
inline("p375i5", A35 + "p4", "C6C_RHO_TENOR")
inline("p375i6", A35 + "p4", "C6C_RHO_BASIS")
f("p375i7", A35 + "p5", ["C6C_KB = sum(k, abs(C6C_WS_k))"])

# --- Article 264: equity risk
f("p378i0", A64 + "p4", ["C6C_KB = sum(k, abs(C6C_WS_k))"])

# --- Article 264-2: commodity risk
v("C6C_RHO_CTY", "ρ_{kl}^{(cty)}", "感応度kと感応度lのコモディティに係る相関係数", "Correlation coefficient relating to the commodities of sensitivities k and l", A642 + "p4")
f("p380i0", A642 + "p3", ["C6C_RHO = C6C_RHO_CTY * C6C_RHO_TENOR * C6C_RHO_BASIS"])
inline("p380i1", A642 + "p4", "C6C_RHO_CTY")
inline("p380i2", A642 + "p4", "C6C_RHO_TENOR")
inline("p380i3", A642 + "p4", "C6C_RHO_BASIS")
inline("p380i4", A642 + "p4", "C6C_RHO_CTY")
inline("p381i0", A642 + "p4", "C6C_RHO_TENOR")
inline("p381i1", A642 + "p4", "C6C_RHO_BASIS")

# --- Article 265: vega risk
v("C6C_RHO_OPT", "ρ_{kl}^{(option maturity)}", "オプションの権利行使日までの年数に係る相関係数", "Correlation coefficient relating to the time to option exercise", A65 + "p4")
v("C6C_RHO_UND", "ρ_{kl}^{(underlying maturity)}", "原資産となる金利派生商品の契約期間に係る相関係数", "Correlation coefficient relating to the contract period of the underlying interest rate derivative", A65 + "p4")
v("C6C_RHO_DELTA", "ρ_{kl}^{(DELTA)}", "ベガ・リスク・ファクターに対応するデルタ・リスク・ファクター間の相関係数", "Correlation coefficient between the delta risk factors corresponding to the vega risk factors", A65 + "p4")
v("C6C_ALPHA", "α", "一パーセント", "Parameter α, equal to 1%", A65 + "p4")
v("C6C_T_k", "T_{k}", "オプション商品kのオプション権利行使日までの年数", "Number of years until the option exercise date of option product k", A65 + "p4")
v("C6C_T_l", "T_{l}", "オプション商品lのオプション権利行使日までの年数", "Number of years until the option exercise date of option product l", A65 + "p4")
v("C6C_TU_k", "T_{k}^{U}", "オプション商品kの原資産となる金利派生商品の契約期間の年数", "Number of years of the contract period of the interest rate derivative underlying option product k", A65 + "p4")
v("C6C_TU_l", "T_{l}^{U}", "オプション商品lの原資産となる金利派生商品の契約期間の年数", "Number of years of the contract period of the interest rate derivative underlying option product l", A65 + "p4")
f("p383i0", A65 + "p3", ["C6C_RHO = min(C6C_RHO_OPT * C6C_RHO_UND, 1)"],
  nj="原文では min[…；1] と角括弧及びセミコロンで表記されている。",
  ne="Printed as min[ … ; 1] with square brackets and a semicolon; written here as min(a, 1).")
f("p383i1", A65 + "p3", ["C6C_RHO = min(C6C_RHO_DELTA * C6C_RHO_OPT, 1)"],
  nj="原文では min[…；1] と角括弧及びセミコロンで表記されている。",
  ne="Printed as min[ … ; 1] with square brackets and a semicolon; written here as min(a, 1).")
inline("p384i0", A65 + "p4", "C6C_RHO_OPT")
inline("p384i1", A65 + "p4", "C6C_RHO_UND")
inline("p384i2", A65 + "p4", "C6C_RHO_DELTA")
inline("p384i3", A65 + "p4", "C6C_RHO_OPT")
f("p384i4", A65 + "p4", ["C6C_RHO_OPT = exp(-C6C_ALPHA * (abs(C6C_T_k - C6C_T_l) / min(C6C_T_k, C6C_T_l)))"],
  nj="原文では分母が min{T_{k}；T_{l}} と波括弧及びセミコロンで表記されている。",
  ne="The denominator is printed as min{T_{k} ; T_{l}} with braces and a semicolon; written here as min(T_{k}, T_{l}).")
inline("p384i5", A65 + "p4", "C6C_RHO_UND")
f("p384i6", A65 + "p4", ["C6C_RHO_UND = exp(-C6C_ALPHA * (abs(C6C_TU_k - C6C_TU_l) / min(C6C_TU_k, C6C_TU_l)))"],
  nj="原文では分母が min{T_{k}^{U}；T_{l}^{U}} と波括弧及びセミコロンで表記されている。",
  ne="The denominator is printed as min{T_{k}^{U} ; T_{l}^{U}} with braces and a semicolon; written here as min(T_{k}^{U}, T_{l}^{U}).")
inline("p384i7", A65 + "p4", "C6C_TU_k")
inline("p384i8", A65 + "p4", "C6C_TU_l")
inline("p384i9", A65 + "p4", "C6C_RHO_DELTA")
f("p384i10", A65 + "p5", ["C6C_KB = sum(k, abs(C6C_WS_k))"])

# --- Article 265-2: curvature risk
v("C6C_CVRP_k", "CVR_{k}^{+}", "リスク・ファクターkの上方シフト時のカーベチャー・リスクのリスク加重後の感応度", "Curvature risk-weighted sensitivity of risk factor k under the upward shift", A652 + "p4")
v("C6C_CVRM_k", "CVR_{k}^{-}", "リスク・ファクターkの下方シフト時のカーベチャー・リスクのリスク加重後の感応度", "Curvature risk-weighted sensitivity of risk factor k under the downward shift", A652 + "p4")
inline("p387i0", A652 + "p3", "C6C_RHO_NAME")
inline("p387i1", A652 + "p3", "C6C_RHO_NAME")
inline("p387i2", A652 + "p3", "C6C_RHO_NAME")
inline("p387i3", A652 + "p3", "C6C_RHO_TRANCHE")
inline("p387i4", A652 + "p3", "C6C_RHO_CTY")
f("p387i5", A652 + "p4", ["C6C_KB = max(sum(k, max(C6C_CVRP_k, 0)), sum(k, max(C6C_CVRM_k, 0)))"])
