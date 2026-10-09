#!/usr/bin/env python3
"""
Chapter 3 formulas: transcriptions of the 47 image formulas extract_chapter_v2.py left as
{{F:<id>}} tokens (41 in the text, 6 inside table cells), plus the variables they use and
their provisional notation. Merged into feeds/fsa-basel-cap-jp/formulas.json and
notation.json (Chapter 2's entries are kept). Every formula here was read off the PDF image
(source: "transcribed"); two carry notes where the image is doubtful or departs from the
Basel text — both are also on the verification list (pipeline/EXTERNAL_INFO_REQUESTS.md).

Usage: python3 pipeline/translations/ch3_formulas.py
"""
import json
import re
from pathlib import Path

FEED = Path(__file__).resolve().parent.parent.parent / "feeds" / "fsa-basel-cap-jp"
C = "fsa-basel-cap-jp.ch3."
A47, A49, A68, A76, A83, A84 = (C + a for a in ("art47.", "art49.", "art68.", "art76.", "art83.", "art84."))

V = {}  # id -> (symbol, name_ja, name_en, desc_ja, desc_en, defined_at)
def v(i, sym, nj, ne, at, dj="", de=""):
    V[i] = (sym, nj, ne, dj, de, at)

# --- SA-CCR (Article 47)
v("RC", "RC", "再構築コスト", "Replacement cost", A47 + "p1")
v("PFE", "PFE", "将来の潜在的なエクスポージャー額", "Potential future exposure", A47 + "p1")
v("V", "V", "ネッティング・セットに含まれる取引の時価の合計額", "Sum of the market values of the transactions in the netting set", A47 + "p2")
v("C", "C", "ヘアカット調整後のネット担保額", "Net collateral amount after haircuts", A47 + "p2")
v("SA_H", "H", "ボラティリティ調整率", "Haircut", A47 + "p3", "第三項各号の算式で算出する。", "Calculated by the formulas in the items of paragraph (3).")
v("SA_HM", "H_{M}", "最低保有期間の下で毎営業日の時価評価等を行う場合のボラティリティ調整率", "Haircut under the minimum holding period with daily revaluation or remargining", A76 + "p2")
v("SA_H10", "H_{10}", "標準的ボラティリティ調整率", "Standard supervisory haircut", A47 + "p3", "第六節第三款第二目（第七十条）に規定するもの。", "As provided in Section 6, Subsection 3, Division 2 (Article 70).")
v("SA_NR", "N_{R}", "ネッティング・セットに含まれる取引の残存期間のうち最も長い営業日数", "Longest residual maturity (in business days) of the transactions in the netting set", A47 + "p3", "十営業日未満のときは十営業日。", "Ten business days if less than ten.")
v("SA_TM", "T_{M}", "最低保有期間", "Minimum holding period", A47 + "p3", "第七十六条第二項第一号に定めるもの。", "As specified in Article 76(2)(i).")
v("MPOR", "MPOR", "リスクのマージン期間", "Margin period of risk", A47 + "p3", "第四項・第五項で定める営業日数。", "Business days set by paragraphs (4) and (5).")
v("multiplier", "multiplier", "乗数", "Multiplier", A47 + "p6")
v("AddOn_agg", "AddOn^{aggregate}", "アドオンの合計額", "Aggregate add-on", A47 + "p6", "金利・為替・信用・株式・コモディティのアドオンの合計。", "Sum of the interest rate, FX, credit, equity and commodity add-ons.")
v("AddOn_IR", "AddOn^{(IR)}", "金利デリバティブに係るアドオン", "Add-on for interest rate derivatives", A47 + "p6")
v("AddOn_IR_j", "AddOn_{j}^{(IR)}", "通貨j建ての金利デリバティブのヘッジセットに係るアドオンの額の合計額", "Add-on for the hedging sets of interest rate derivatives in currency j", A47 + "p11")
v("D_j1", "D_{j1}^{(IR)}", "通貨j建てでE_iが一年未満の金利デリバティブの実効想定元本額の合計額", "Effective notional of currency-j interest rate derivatives with E_i under 1 year", A47 + "p11")
v("D_j2", "D_{j2}^{(IR)}", "通貨j建てでE_iが一年以上五年以下の金利デリバティブの実効想定元本額の合計額", "Effective notional of currency-j interest rate derivatives with E_i of 1–5 years", A47 + "p11")
v("D_j3", "D_{j3}^{(IR)}", "通貨j建てでE_iが五年超の金利デリバティブの実効想定元本額の合計額", "Effective notional of currency-j interest rate derivatives with E_i over 5 years", A47 + "p11")
v("SD_i", "SD_{i}", "デュレーション調整値", "Supervisory duration (duration adjustment value)", A47 + "p11", "十営業日を年換算した値が下限。", "Floored at ten business days expressed in years.")
v("S_i", "S_{i}", "計算期間の最も早い日までの営業日数（年換算）", "Business days to the earliest date of the calculation period, in years", A47 + "p11")
v("E_i", "E_{i}", "計算期間の最も遅い日までの営業日数（年換算）", "Business days to the latest date of the calculation period, in years", A47 + "p11")
v("P_i", "P_{i}", "オプションiが参照する金利等の水準", "Level of the rate, etc. referenced by option i", A47 + "p11")
v("K_i", "K_{i}", "オプションiの行使価格", "Strike price of option i", A47 + "p11")
v("sigma_i", "σ_{i}", "監督上のボラティリティ", "Supervisory volatility", A47 + "p11", "金利〇・五、為替〇・一五、信用一・〇／〇・八、株式一・二〇／〇・七五、コモディティ一・五／〇・七。", "IR 0.5, FX 0.15, credit 1.0/0.8, equity 1.20/0.75, commodity 1.5/0.7.")
v("T_i", "T_{i}", "最も遅い権利行使日までの営業日数（年換算）", "Business days to the latest exercise date, in years", A47 + "p11")
v("M_i", "M_{i}", "金利デリバティブiの残存期間（営業日数）", "Residual maturity of derivative i (business days)", A47 + "p11", "十営業日未満のときは十営業日。", "Ten business days if less than ten.")
v("MPOR_i", "MPOR_{i}", "取引iを含むネッティング・セットのリスクのマージン期間", "Margin period of risk of the netting set containing transaction i", A47 + "p11")
v("AddOn_FX", "AddOn^{(FX)}", "外国為替デリバティブに係るアドオン", "Add-on for FX derivatives", A47 + "p6")
v("AddOn_FX_j", "AddOn_{HS_{j}}^{(FX)}", "ヘッジセットjに係るアドオンの額", "Add-on for hedging set j", A47 + "p12")
v("AddOn_Credit", "AddOn^{(Credit)}", "信用デリバティブに係るアドオン", "Add-on for credit derivatives", A47 + "p6")
v("AddOn_Ent_k", "AddOn(Entity_{k})", "Entity_kを参照する信用デリバティブに係るアドオンの額の合計額", "Add-on for credit derivatives referencing Entity_k", A47 + "p13")
v("rho_cr_k", "ρ_{k}^{(Credit)}", "Entity_kに係る相関係数", "Correlation parameter for Entity_k", A47 + "p13", "事業法人等〇・五、インデックス〇・八。", "Single name 0.5, index 0.8.")
v("A_i", "A_{i}", "当該階層より劣後する全階層の額の合計÷原資産の額", "Attachment point: subordinate tranches ÷ underlying pool", A47 + "p13")
v("D_i", "D_{i}", "当該階層及び劣後する全階層の額の合計÷原資産の額", "Detachment point: this and subordinate tranches ÷ underlying pool", A47 + "p13")
v("AddOn_Equity", "AddOn^{(Equity)}", "エクイティ・デリバティブに係るアドオン", "Add-on for equity derivatives", A47 + "p6")
v("AddOn_Eq_k", "AddOn(Equity_{k})", "Equity_kを参照するエクイティ・デリバティブに係るアドオンの額の合計額", "Add-on for equity derivatives referencing Equity_k", A47 + "p14")
v("rho_eq_k", "ρ_{k}^{(Equity)}", "Equity_kに係る相関係数", "Correlation parameter for Equity_k", A47 + "p14", "個別株〇・五、株価指数〇・八。", "Single name 0.5, index 0.8.")
v("AddOn_Com", "AddOn^{(Com)}", "コモディティ・デリバティブに係るアドオン", "Add-on for commodity derivatives", A47 + "p6")
v("AddOn_Com_j", "AddOn_{HS_{j}}^{(Com)}", "ヘッジセットjに係るアドオンの額", "Add-on for commodity hedging set j", A47 + "p15")
v("AddOn_Type_k", "AddOn(Type_{k}^{j})", "ヘッジセットjでコモディティkを参照するコモディティ・デリバティブに係るアドオンの額の合計額", "Add-on for commodity derivatives referencing commodity k in hedging set j", A47 + "p15")
v("rho_com_j", "ρ_{j}^{(Com)}", "ヘッジセットjに係る相関係数", "Correlation parameter for hedging set j", A47 + "p15", "〇・四。", "0.4.")
v("NS_MA", "NS∈MA", "マージン・アグリーメントMAの対象となるネッティング・セット", "Netting sets covered by margin agreement MA", A47 + "p17")
v("V_NS", "V_{NS}", "NSに含まれる取引の時価の合計額", "Sum of market values of the transactions in NS", A47 + "p17")
v("C_MA", "C_{MA}", "MAの下におけるヘアカット調整後のネット担保額", "Net collateral after haircuts under MA", A47 + "p17")
v("PFE_NS_unm", "PFE_{NS}^{unmargined}", "マージン・アグリーメントがないものとして算出したNSのPFE", "PFE of NS calculated as if unmargined", A47 + "p18")
# --- Expected exposure method (Article 49)
v("EPE_eff", "EPE_{eff}", "実効EPE", "Effective EPE", A49 + "p2")
v("EE_eff_k", "EE_{eff,t_{k}}", "実効EE_tk", "Effective EE at time t_k", A49 + "p2", "max(実効EE_tk−1, EE_tk)。", "max(effective EE at t_{k−1}, EE at t_k).")
v("EE_k", "EE_{t_{k}}", "時点t_kにおける期待エクスポージャー", "Expected exposure at time t_k", A49 + "p2")
v("EPE", "EPE", "EPE（αの推計に用いる値）", "EPE (used in estimating α)", A49 + "p4")
v("dt_k", "Δt_{k}", "t_k − t_k−1", "t_k − t_{k−1}", A49 + "p2")
v("n", "n", "t_nが一年となるような数", "The n such that t_n is one year", A49 + "p2")
v("idx_k1", "k=1", "和の添字（k＝1からnまで）", "Summation index (k = 1 to n)", A49 + "p2")
# --- Comprehensive approach (Articles 68, 76)
v("CRM_H", "H", "適用するボラティリティ調整率", "Haircut to be applied", A68 + "p1")
v("a_i", "a_{i}", "各担保の額が担保総額に占める割合", "Share of each collateral item in the total", A68 + "p1")
v("H_i", "H_{i}", "各担保に対応するボラティリティ調整率", "Haircut for each collateral item", A68 + "p1")
v("CRM_HM", "H_{M}", "最低保有期間の下で毎営業日の時価評価等を行う場合のボラティリティ調整率", "Haircut under the minimum holding period with daily revaluation or remargining", A76 + "p2")
v("CRM_H10", "H_{10}", "調整対象となる第七十条のボラティリティ調整率", "The Article 70 haircut being adjusted", A76 + "p2")
v("CRM_TM", "T_{M}", "最低保有期間", "Minimum holding period", A76 + "p2")
v("CRM_NR", "N_{R}", "担保額調整又は時価評価の間隔（営業日数）", "Remargining or revaluation interval (business days)", A76 + "p3")
# --- Haircut floors (Articles 83, 84)
v("f_A", "f_{A}", "貸出証券等のボラティリティ調整率の標準的下限", "Haircut floor for securities lent or posted", A83 + "p1")
v("f_B", "f_{B}", "借入証券等のボラティリティ調整率の標準的下限", "Haircut floor for securities borrowed or received", A83 + "p1")
v("C_t", "C_{t}", "ネットで借入れとなる証券又は現金の取引額", "Amount of a security or cash borrowed on a net basis", A84 + "p1")
v("E_s", "E_{s}", "ネットで貸付けとなる証券又は現金の取引額", "Amount of a security or cash lent on a net basis", A84 + "p1")
v("f_s", "f_{s}", "ネットで貸付けとなる証券等の標準的下限", "Haircut floor for a security lent on a net basis", A84 + "p1")
v("f_t", "f_{t}", "ネットで借入れとなる証券等の標準的下限", "Haircut floor for a security borrowed on a net basis", A84 + "p1")

T = "transcribed"
F = []  # (anchor, node, display, lines, label_ja, label_en, note_ja, note_en)
def f(anchor, node, lines, display="block", lj="", le="", nj="", ne=""):
    F.append({"id": f"f-ch3-{anchor}", "anchor": anchor, "node_id": node, "display": display, "lines": lines,
              "label_ja": lj, "label_en": le, "source": T, "note_ja": nj, "note_en": ne})
def inline(anchor, node, var):
    f(anchor, node, [var], display="inline")

f("p98i0", A47 + "p3", ["SA_H = SA_HM * sqrt((min(SA_NR, 250) + SA_TM - 1) / SA_TM)"], lj="一　マージン・アグリーメントを締結していない場合", le="(i) Without a margin agreement")
f("p98i1", A47 + "p3", ["SA_HM = SA_H10 * sqrt(SA_TM / 10)"])
f("p98i2", A47 + "p3", ["SA_H = SA_H10 * sqrt(MPOR / 10)"], lj="二　マージン・アグリーメントを締結している場合", le="(ii) With a margin agreement")
f("p99i0", A47 + "p6", ["multiplier = min(1, 0.05 + (1 - 0.05) * exp((V - C) / (2 * (1 - 0.05) * AddOn_agg)))"])
f("p101i0", A47 + "p11", ["AddOn_IR = sum(j, AddOn_IR_j)"])
inline("p101i1", A47 + "p11", "AddOn_IR_j")
inline("p101i2", A47 + "p11", "AddOn_IR_j")
f("p101i3", A47 + "p11", ["(D_j1^2 + D_j2^2 + D_j3^2 + 1.4 * D_j1 * D_j2 + 1.4 * D_j2 * D_j3 + 0.6 * D_j1 * D_j3)^(1 / 2)"])
inline("p101i4", A47 + "p11", "D_j1")
inline("p101i5", A47 + "p11", "D_j2")
inline("p101i6", A47 + "p11", "D_j3")
f("p101i7", A47 + "p11", ["abs(D_j1) + abs(D_j2) + abs(D_j3)"])
f("p101i8", A47 + "p11", ["SD_i = (exp(-0.05 * S_i) - exp(-0.05 * E_i)) / 0.05"])
_d = "(ln(P_i / K_i) + 0.5 * sigma_i^2 * T_i) / (sigma_i * sqrt(T_i))"
f("p102i0", A47 + "p11", [f"Phi({_d})"], display="inline")
f("p102i1", A47 + "p11", [f"-Phi({_d})"], display="inline")
f("p102i2", A47 + "p11", [f"-Phi(-{_d})"], display="inline")
f("p102i3", A47 + "p11", [f"Phi(-{_d})"], display="inline")
f("p103i0", A47 + "p11", ["sqrt(min(M_i, 250) / 250)"])
f("p103i1", A47 + "p11", ["3 / 2 * sqrt(MPOR_i / 250)"])
f("p103i2", A47 + "p12", ["AddOn_FX = sum(j, AddOn_FX_j)"])
inline("p103i3", A47 + "p12", "AddOn_FX_j")
inline("p103i4", A47 + "p12", "AddOn_FX_j")
f("p104i0", A47 + "p13", ["AddOn_Credit = ((sum(k, rho_cr_k * AddOn_Ent_k))^2 + sum(k, (1 - rho_cr_k^2) * AddOn_Ent_k^2))^(1 / 2)"])
inline("p104i1", A47 + "p13", "rho_cr_k")
inline("p105i0", A47 + "p13", "rho_cr_k")
f("p106i0", A47 + "p13", ["15 / ((1 + 14 * A_i) * (1 + 14 * D_i))"], display="inline")
f("p106i1", A47 + "p13", ["-15 / ((1 + 14 * A_i) * (1 + 14 * D_i))"], display="inline")
f("p106i2", A47 + "p14", ["AddOn_Equity = ((sum(k, rho_eq_k * AddOn_Eq_k))^2 + sum(k, (1 - rho_eq_k^2) * AddOn_Eq_k^2))^(1 / 2)"],
  nj="原文PDFの画像では外側の指数の分母が判読困難（「3」にも見える）。バーゼル基準（CRE52）及び第十三項の信用デリバティブの算式に合わせ1/2と転記した。要確認。",
  ne="In the PDF image the denominator of the outer exponent is hard to read (it could be taken for a 3). Transcribed as 1/2, consistent with Basel (CRE52) and the credit formula in paragraph (13). To be verified.")
inline("p107i0", A47 + "p14", "rho_eq_k")
inline("p107i1", A47 + "p14", "rho_eq_k")
f("p108i0", A47 + "p15", ["AddOn_Com = sum(j, AddOn_Com_j)"])
f("p108i1", A47 + "p15", ["AddOn_Com_j = ((rho_com_j * sum(k, AddOn_Type_k))^2 + (1 - rho_com_j^2) * sum(k, AddOn_Type_k^2))^(1 / 2)"])
inline("p108i2", A47 + "p15", "AddOn_Com_j")
inline("p108i3", A47 + "p15", "AddOn_Type_k")
inline("p108i4", A47 + "p15", "rho_com_j")
inline("p108i5", A47 + "p15", "AddOn_Type_k")
f("p110i0", A47 + "p17", ["RC = max(sum(NS_MA, max(V_NS, 0)) - max(C_MA, 0), 0) + max(sum(NS_MA, min(V_NS, 0)) - min(C_MA, 0), 0)"])
f("p111i0", A47 + "p18", ["PFE = sum(NS_MA, PFE_NS_unm)"])
inline("p111i1", A47 + "p18", "PFE_NS_unm")
f("p111i2", A49 + "p2", ["EPE_eff = sum(idx_k1, n, EE_eff_k * dt_k)"])
f("p113i0", A49 + "p4", ["EPE = sum(idx_k1, n, EE_k * dt_k)"])
f("p129i0", A68 + "p1", ["CRM_H = sum(i, a_i * H_i)"])
f("p133i0", A76 + "p2", ["CRM_HM = CRM_H10 * sqrt(CRM_TM / 10)"])
f("p133i1", A76 + "p3", ["CRM_H = CRM_HM * sqrt((CRM_NR - (CRM_TM - 1)) / CRM_TM)"],
  nj="原文PDFの画像のとおり「N_R − (T_M − 1)」と転記した。バーゼル基準（CRE22.59）及び第四十七条第三項第一号の算式では「N_R + (T_M − 1)」であり、誤植の可能性がある。要確認。",
  ne="Transcribed as printed in the PDF image: \"N_R − (T_M − 1)\". Basel (CRE22.59) and the formula in Article 47(3)(i) have \"N_R + (T_M − 1)\", so this may be a misprint. To be verified.")
f("p139i0", A83 + "p1", ["(1 + f_B) / (1 + f_A) - 1"])
f("p140i0", A84 + "p1", ["(sum(t, C_t) - sum(s, E_s)) / sum(s, E_s)"])
f("p140i1", A84 + "p1", ["((sum(s, E_s / (1 + f_s)) / sum(s, E_s)) / (sum(t, C_t / (1 + f_t)) / sum(t, C_t))) - 1"])


def main():
    fpath, npath = FEED / "formulas.json", FEED / "notation.json"
    formulas = json.loads(fpath.read_text(encoding="utf-8"))
    notation = json.loads(npath.read_text(encoding="utf-8"))
    for vid, (sym, nj, ne, dj, de, at) in V.items():
        formulas["variables"][vid] = {"name_ja": nj, "name_en": ne, "desc_ja": dj, "desc_en": de, "defined_at": at}
        notation["symbols"][vid] = sym
    keep = [x for x in formulas["formulas"] if not x["id"].startswith("f-ch3-")]
    formulas["formulas"] = keep + F
    fpath.write_text(json.dumps(formulas, ensure_ascii=False, indent=2), encoding="utf-8")
    npath.write_text(json.dumps(notation, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(F)} Chapter 3 formulas, {len(V)} variables")


if __name__ == "__main__":
    main()
