# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------

import streamlit as st
from datetime import date
import pandas as pd
from io import BytesIO

from pdf_generator_ra import generate_ra_pdf
from pdf_generator_pres import generate_pres_pdf
from eac_calculator import compute_eac_table, eac_table_to_rows, TIC_MAP

# ----------------------------------------------------
# CONSTANTS
# ----------------------------------------------------
VAT = 15.0  # hardcoded VAT rate

# ----------------------------------------------------
# UPFRONT FEE BRACKETS
# ----------------------------------------------------
FEE_BRACKETS_OPTION_1 = [
    {"min": 0,          "max": 150000,       "rate": 2.75},
    {"min": 150000.01,  "max": 350000,       "rate": 1.375},
    {"min": 350000.01,  "max": 750000,       "rate": 0.688},
    {"min": 750000.01,  "max": 2000000,      "rate": 0.344},
    {"min": 2000000.01, "max": 5000000,      "rate": 0.25},
    {"min": 5000000.01, "max": float("inf"), "rate": 0.0},
]

UPFRONT_FEE_CAP_EX_VAT = 7500.0  # Option 1 fee capped at R7,500 excl VAT (R8,625 incl VAT)

def calculate_upfront_fee(lump_sum, pres_option, vat_pct, investor_age=0):
    """Tiered (progressive/marginal) upfront fee across band slices, capped at R7,500 excl VAT.
    No upfront fee charged for investors aged 55 or older."""
    if pres_option != 1:
        return 0.0, 0.0, 0.0
    if investor_age >= 55:
        return 0.0, 0.0, 0.0
    remaining = lump_sum
    total_no_vat = 0.0
    for b in FEE_BRACKETS_OPTION_1:
        if remaining <= 0:
            break
        band_size = b["max"] - b["min"] if b["max"] != float("inf") else remaining
        slice_amt = min(remaining, band_size)
        total_no_vat += slice_amt * (b["rate"] / 100)
        remaining -= slice_amt
    # Cap at R7,500 excl VAT
    if total_no_vat > UPFRONT_FEE_CAP_EX_VAT:
        total_no_vat = UPFRONT_FEE_CAP_EX_VAT
    fee_vat = total_no_vat * (1 + vat_pct / 100)
    effective_rate = (total_no_vat / lump_sum * 100) if lump_sum > 0 else 0.0
    return fee_vat, total_no_vat, effective_rate


# ----------------------------------------------------
# INVESTMENT MANAGEMENT FEE (weighted TIC)
# ----------------------------------------------------
def investment_mgmt_from_alloc(df, lump_sum):
    df = df.copy()
    df["w"]          = df["Lump Sum %"] / 100.0
    df["allocation"]  = df["w"] * lump_sum
    df["rand_fee"]    = df["allocation"] * (df["TIC"] / 100.0)
    total_rand_fee    = df["rand_fee"].sum()
    if lump_sum == 0:
        return 0.0
    return (total_rand_fee / lump_sum) * 100.0


# ----------------------------------------------------
# TIC DATA + LIFESTAGE LOGIC
# ----------------------------------------------------
TIC_DATA = {
    "Portfolio": [
        "Destiny Market Enhanced Portfolio",
        "Destiny Moderate Portfolio",
        "Destiny Conservative Portfolio",
        "Destiny Defensive Portfolio",
        "Destiny Global Enhanced Portfolio",
        "Destiny Sharia Portfolio",
        "Destiny Money Market Portfolio",
        "Destiny Passive Market Enhanced Portfolio",
        "Destiny Passive Moderate Portfolio",
        "Destiny Passive Conservative Portfolio",
        "Destiny Passive Defensive Portfolio",
    ],
    "TIC": [0.89, 0.83, 0.74, 0.63, 0.76, 0.80, 0.23, 0.28, 0.26, 0.25, 0.23],
}
TIC_DF = pd.DataFrame(TIC_DATA)


def get_lifestage_portfolio(option, age):
    if option == "Lifestage":
        if age >= 62:   return "Destiny Defensive Portfolio"
        elif age >= 57: return "Destiny Conservative Portfolio"
        elif age >= 50: return "Destiny Moderate Portfolio"
        else:           return "Destiny Market Enhanced Portfolio"
    if option == "Passive Lifestage":
        if age >= 62:   return "Destiny Passive Defensive Portfolio"
        elif age >= 57: return "Destiny Passive Conservative Portfolio"
        elif age >= 50: return "Destiny Passive Moderate Portfolio"
        else:           return "Destiny Passive Market Enhanced Portfolio"
    return None


# ----------------------------------------------------
# PAGE CONFIG + THEME
# ----------------------------------------------------
st.set_page_config(page_title="Investment Overview", layout="centered")

st.markdown("""
<style>
    .stSelectbox label div,
    .stTextInput label div,
    .stNumberInput label div,
    .stDateInput label div,
    label {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #1A1A1A !important;
        margin-bottom: 6px !important;
    }
    .section-heading {
        font-size: 26px;
        font-weight: 700;
        color: #1A3D6F;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input {
        height: 42px;
        font-size: 16px;
    }
    .result-box {
        background: #F4F6FA;
        border: 1px solid #D6D9E0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# LOGO
# ----------------------------------------------------
import os
logo = "destiny_logo.png" if os.path.exists("destiny_logo.png") else "assets/logo_destiny.png"
st.image(logo, width=360)

# ----------------------------------------------------
# PERSONAL INFORMATION
# ----------------------------------------------------
st.markdown("<div class='section-heading'>Personal Information</div>", unsafe_allow_html=True)

today = date.today()

dob = st.date_input(
    "Investor Date of Birth",
    min_value=date(1900, 1, 1),
    max_value=today,
    format="DD/MM/YYYY",
    key="dob_input",
)

investor_age = (today - dob).days / 365.25
investor_age_display = int(investor_age)  # floor to completed years
st.write(f"**Investor Age:** {investor_age_display} years")

investor_name  = st.text_input("Investor Name",  key="inv_name_input")
investor_email = st.text_input("Investor Email", key="inv_email_input")

# ----------------------------------------------------
# INVESTMENT DETAILS
# ----------------------------------------------------
st.markdown("<div class='section-heading'>Investment Details</div>", unsafe_allow_html=True)

fund = st.selectbox("Product Type", ["Retirement Annuity", "Preservation"], key="fund_select")

# Pres fee option — only shown for Preservation
if fund == "Preservation":
    pres_fee_option_str = st.selectbox(
        "Fee Option",
        [
            "Option 1 – Upfront Fee",
            "Option 2 – Cancellation Fee",
            "Option 3 – Section 14 (No Fees)",
        ],
        key="pres_fee",
    )
    pres_fee_option = int(pres_fee_option_str[7])  # extract digit: "Option 1..." -> 1
else:
    pres_fee_option = 3  # RA: no fee options

def _parse_rand(raw: str) -> int:
    """Strip R, spaces, commas and return int. Returns 0 for empty/invalid."""
    cleaned = raw.replace("R", "").replace(",", "").replace(" ", "").strip()
    try:
        return max(0, int(float(cleaned))) if cleaned else 0
    except ValueError:
        return 0

def _fmt_rand(n: int) -> str:
    return f"R{n:,}" if n else ""

def _rand_input(label: str, key: str, placeholder: str) -> int:
    """Text input that reformats itself to R1,000,000 after each keystroke."""
    raw = st.session_state.get(key, "")
    n   = _parse_rand(raw)
    # If user has typed something and the stored value isn't already formatted,
    # write the formatted version back and rerun so the field shows it.
    if raw and raw != _fmt_rand(n):
        st.session_state[key] = _fmt_rand(n)
        st.rerun()
    st.text_input(label, key=key, placeholder=placeholder)
    return n

estimated_lump_sum = _rand_input(
    "Estimated Lump Sum (R)", key="lump_sum", placeholder="R"
)

if fund == "Retirement Annuity":
    monthly_contribution = _rand_input(
        "Monthly Contribution (R)", key="monthly_contr", placeholder="R"
    )
else:
    monthly_contribution = 0

# RA minimums validation
if fund == "Retirement Annuity":
    if estimated_lump_sum > 0 and estimated_lump_sum < 20000:
        st.error("Minimum lump sum for a Retirement Annuity is R 20,000")
    if monthly_contribution > 0 and monthly_contribution < 500:
        st.error("Minimum monthly contribution for a Retirement Annuity is R 500")

ifa_fee       = st.selectbox("IFA Fee (ex VAT)", ["0%", "0.25%", "0.35%", "0.5%", "0.75%"])
ifa_fee_value = float(ifa_fee.replace("%", ""))

investment_option = st.selectbox(
    "Investment Option", ["Lifestage", "Passive Lifestage", "Own Choice"]
)

is_ra = fund == "Retirement Annuity"

# ----------------------------------------------------
# UPFRONT FEE CALC + DISPLAY (Preservation only)
# ----------------------------------------------------
upfront_fee_vat, upfront_fee_no_vat, upfront_rate_display = calculate_upfront_fee(
    estimated_lump_sum, pres_fee_option, VAT, investor_age
)
net_lump_sum = estimated_lump_sum - upfront_fee_vat

if fund == "Preservation":
    if pres_fee_option == 1:
        st.markdown("<div class='section-heading'>Option 1 – Upfront Fee</div>", unsafe_allow_html=True)
        if investor_age >= 55:
            st.info("No upfront fee applies — investor is aged 55 or older.")
            st.write(f"**Net Amount Invested:** R {int(net_lump_sum):,}")
        else:
            st.write(f"**Upfront Rate:** {upfront_rate_display:.3f}%")
            st.write(f"**Upfront Fee (Incl VAT):** R {upfront_fee_vat:,.2f}")
            st.write(f"**Net Amount Invested:** R {int(net_lump_sum):,}")
    elif pres_fee_option == 2:
        st.markdown("<div class='section-heading'>Option 2 – Cancellation Fee</div>", unsafe_allow_html=True)
        if investor_age >= 55:
            st.info("No cancellation fee applies — investor is aged 55 or older.")
        else:
            st.write(
                "No initial fee is charged. However, if you withdraw funds, "
                "a cancellation fee applies based on your period of membership. "
                "The cancellation fee falls away once the investor reaches age 55 or has been a member for 5 or more years."
            )
            opt2_data = {
                "Period of Membership": ["One year or less", "One to Three years", "Three to Five years", "Five years or more"],
                "Cancellation Fee": ["2.75% plus VAT", "1.75% plus VAT", "0.75% plus VAT", "0%"],
            }
            st.table(pd.DataFrame(opt2_data))
        st.write(f"**Net Amount Invested:** R {estimated_lump_sum:,}")
    elif pres_fee_option == 3:
        st.markdown("<div class='section-heading'>Option 3 – Section 14 (No Fees)</div>", unsafe_allow_html=True)
        st.write("No upfront or cancellation fees apply.")
        st.write(f"**Net Amount Invested:** R {estimated_lump_sum:,}")

# ----------------------------------------------------
# LIFESTAGE / OWN CHOICE PORTFOLIO
# ----------------------------------------------------
ls_name = None
ls_tic  = None
alloc_df = None

if investment_option in ["Lifestage", "Passive Lifestage"]:
    ls_name = get_lifestage_portfolio(investment_option, investor_age)
    ls_tic  = float(TIC_DF.loc[TIC_DF["Portfolio"] == ls_name, "TIC"].iloc[0])

    st.subheader("LifeStage Portfolio Selection")
    st.write(f"**Selected Portfolio:** {ls_name}")
    st.write(f"**TIC:** {ls_tic:.2f}%")

if investment_option == "Own Choice":
    allocations = []
    st.markdown("### Enter Allocations")

    if is_ra:
        colA, colB, colC = st.columns([3, 1.2, 1.7])
        colA.write("**Portfolio**")
        colB.write("**Lump Sum %**")
        colC.write("**Monthly Contribution %**")
    else:
        colA, colB = st.columns([3, 1.2])
        colA.write("**Portfolio**")
        colB.write("**Lump Sum %**")

    for portfolio in TIC_DF["Portfolio"]:
        tic = float(TIC_DF.loc[TIC_DF["Portfolio"] == portfolio, "TIC"].iloc[0])
        if is_ra:
            col1, col2, col3 = st.columns([3, 1.2, 1.7])
            col1.write(f"**{portfolio}**")
            lump_pct = col2.number_input("", min_value=0, max_value=100, step=1, format="%d", key=f"{portfolio}_l")
            cont_pct = col3.number_input(" ", min_value=0, max_value=100, step=1, format="%d", key=f"{portfolio}_c")
        else:
            col1, col2 = st.columns([3, 1.2])
            col1.write(f"**{portfolio}**")
            lump_pct = col2.number_input("", min_value=0, max_value=100, step=1, format="%d", key=f"{portfolio}_l")
            cont_pct = 0
        allocations.append({
            "Portfolio":              portfolio,
            "TIC":                    tic,
            "Lump Sum %":             lump_pct,
            "Monthly Contribution %": cont_pct,
        })

    alloc_df = pd.DataFrame(allocations)
    lump_total = alloc_df["Lump Sum %"].sum()
    if lump_total != 100:
        st.error(f"Lump Sum allocations must add up to 100% (currently {lump_total}%).")
    if is_ra and monthly_contribution > 0:
        cont_total = alloc_df["Monthly Contribution %"].sum()
        if cont_total != 100:
            st.error(f"Monthly Contribution allocations must add up to 100% (currently {cont_total}%).")
    imc = investment_mgmt_from_alloc(alloc_df, estimated_lump_sum)
    st.write(f"**Investment Management Fee (%):** {imc:.4f}%")
    if is_ra:
        st.dataframe(alloc_df.set_index("Portfolio"), hide_index=False)
    else:
        display_df = alloc_df[["Portfolio", "Lump Sum %"]].set_index("Portfolio")
        st.dataframe(display_df, hide_index=False)

# ----------------------------------------------------
# EAC — build via shared calculator
# ----------------------------------------------------
# Build choice_allocations list for compute_eac_table
if investment_option == "Own Choice" and alloc_df is not None:
    choice_allocs = [
        (row["Portfolio"], row["Lump Sum %"])
        for _, row in alloc_df.iterrows()
    ]
else:
    choice_allocs = None

# Determine EAC fee parameters based on fund type and pres option
if is_ra:
    eac_upfront_fee = 0.0
    eac_cancel_fee = 0.0
    include_upfront = False
elif pres_fee_option == 1:
    eac_upfront_fee = upfront_fee_vat
    eac_cancel_fee = 0.0
    include_upfront = True
elif pres_fee_option == 2:
    eac_upfront_fee = 0.0
    eac_cancel_fee = 0.0 if investor_age >= 55 else estimated_lump_sum * 0.0275 * (1 + VAT / 100)
    include_upfront = False
else:  # Option 3
    eac_upfront_fee = 0.0
    eac_cancel_fee = 0.0
    include_upfront = False

_eac_common = dict(
    fund_type          = "RA" if is_ra else "Preservation",
    age                = investor_age,
    investment_option  = investment_option,
    selected_portfolio = ls_name,
    choice_allocations = choice_allocs,
    ifa_fee_ex_vat     = ifa_fee_value,
    vat_rate           = VAT,
    admin_base_ex_vat  = 0.75,
    tic_map            = TIC_MAP,
    lump_sum           = estimated_lump_sum,
    monthly_contribution = monthly_contribution,
)

try:
    eac = compute_eac_table(
        **_eac_common,
        include_upfront_in_eac    = include_upfront,
        upfront_fee_incl_vat      = eac_upfront_fee,
        cancellation_fee_incl_vat = eac_cancel_fee,
    )
    eac_no_cancel = None
except Exception as _eac_err:
    st.error(f"EAC calculation error ({type(_eac_err).__name__}): {_eac_err}")
    st.stop()

# Convert to PDF-compatible row dicts
fund_key = "RA" if is_ra else "Preservation"
eac_rows = eac_table_to_rows(eac, fund_key)
eac_rows_no_cancel = None

# ----------------------------------------------------
# EAC TABLE PREVIEW (on-screen)
# ----------------------------------------------------
st.markdown("<div class='section-heading'>Effective Annual Cost (EAC)</div>", unsafe_allow_html=True)

def _rows_to_df(row_list, hide_zero_other=True, has_split_5yr=False):
    """Convert eac_table_to_rows output to a display DataFrame."""
    if has_split_5yr:
        cols_order = ["y1", "y3", "y5pre", "y5"]
        col_labels  = ["1 year", "3 years", "< 5 years", "5 years"]
    else:
        cols_order = ["y1", "y3", "y5"]
        col_labels  = ["1 year", "3 years", "5 years"]
    def fmt(v):
        return f"{v:.2f}%" if v is not None else "N/A"
    display = []
    for r in row_list:
        if hide_zero_other and r["label"] == "Other":
            if all((r.get(k) is None or r.get(k) == 0.0) for k in cols_order):
                continue
        row_dict = {"": r["label"]}
        for key, label in zip(cols_order, col_labels):
            row_dict[label] = fmt(r.get(key))
        display.append(row_dict)
    return pd.DataFrame(display)

st.dataframe(_rows_to_df(eac_rows, hide_zero_other=True, has_split_5yr=not is_ra), hide_index=True, use_container_width=True)

# ----------------------------------------------------
# GENERATE PDF BUTTON
# ----------------------------------------------------
st.markdown("---")

if st.button("Generate Investment Report (PDF)"):

    safe_name = investor_name.replace(" ", "_") if investor_name else "report"

    ra_lump_err    = is_ra and estimated_lump_sum > 0 and estimated_lump_sum < 20000
    ra_monthly_err = is_ra and monthly_contribution > 0 and monthly_contribution < 500

    if ra_lump_err or ra_monthly_err:
        st.error("Please correct the minimum value errors above before generating the PDF.")

    elif is_ra:
        field_values = {
            "InvestorName":        investor_name,
            "DateOfBirth":         dob.strftime("%d/%m/%Y"),
            "InvestorAge":         f"{investor_age_display} years",
            "InvestorEmail":       investor_email,
            "QuotationDate":       today.strftime("%d %B %Y"),
            "InitialLumpSum":      f"R {estimated_lump_sum:,}",
            "MonthlyContribution": f"R {monthly_contribution:,}",
            "InvestmentOption":    investment_option,
            "LifestagePortfolio":  ls_name or "",
            "LifestageTIC":        f"{ls_tic:.2f}%" if ls_tic else "",
            "LifestageTICValue":   ls_tic or 0.0,
            "LumpSumRaw":          estimated_lump_sum,
            "EACRows":             eac_rows,
        }
        pdf_bytes = generate_ra_pdf(field_values, alloc_df=alloc_df)

        if pdf_bytes:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"destiny_overview_{safe_name}.pdf",
                mime="application/pdf",
            )

    else:
        pres_fee_no_vat = upfront_fee_no_vat
        pres_vat_amt    = upfront_fee_vat - upfront_fee_no_vat

        field_values = {
            "InvestorName":       investor_name,
            "DateOfBirth":        dob.strftime("%d/%m/%Y"),
            "InvestorAge":        f"{investor_age_display} years",
            "InvestorEmail":      investor_email,
            "QuotationDate":      today.strftime("%d %B %Y"),
            "InitialLumpSum":     f"R {estimated_lump_sum:,}",
            "InitialFeeNoVAT":    f"R {pres_fee_no_vat:,.2f}",
            "InitialFeeVATAmt":   f"R {pres_vat_amt:,.2f}",
            "NetLumpSum":         f"R {int(net_lump_sum):,}",
            "InvestmentOption":   investment_option,
            "LifestagePortfolio": ls_name or "",
            "LifestageTIC":       f"{ls_tic:.2f}%" if ls_tic else "",
            "LifestageTICValue":  ls_tic or 0.0,
            "LumpSumRaw":         estimated_lump_sum,
            "PresOption":         pres_fee_option,
            "InvestorAgeRaw":     investor_age,
            "EACRows":            eac_rows,
        }
        pdf_bytes = generate_pres_pdf(field_values, alloc_df=alloc_df)

        if pdf_bytes:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"destiny_overview_{safe_name}.pdf",
                mime="application/pdf",
            )
