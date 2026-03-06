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

UPFRONT_FEE_CAP = 7500.0  # Option 1 fee capped at R7,500 incl VAT

def calculate_upfront_fee(lump_sum, pres_option, vat_pct):
    """Tiered (progressive/marginal) upfront fee across band slices, capped at R7,500."""
    if pres_option != 1:
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
    fee_vat = total_no_vat * (1 + vat_pct / 100)
    # Cap at R7,500 incl VAT
    if fee_vat > UPFRONT_FEE_CAP:
        fee_vat = UPFRONT_FEE_CAP
        total_no_vat = fee_vat / (1 + vat_pct / 100)
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

estimated_lump_sum = st.number_input(
    "Estimated Lump Sum (R)", min_value=0.0, step=1000.0, format="%.2f", key="lump_sum"
)
monthly_contribution = st.number_input(
    "Monthly Contribution (R)", min_value=0.0, step=100.0, format="%.2f", key="monthly_contr"
)

# RA minimums validation
if fund == "Retirement Annuity":
    if estimated_lump_sum > 0 and estimated_lump_sum < 20000:
        st.error("Minimum lump sum for a Retirement Annuity is R 20,000.00")
    if monthly_contribution > 0 and monthly_contribution < 500:
        st.error("Minimum monthly contribution for a Retirement Annuity is R 500.00")

ifa_fee       = st.selectbox("IFA Fee (ex VAT)", ["0%", "0.25%", "0.35%", "0.5%", "0.75%"])
ifa_fee_value = float(ifa_fee.replace("%", ""))

investment_option = st.selectbox(
    "Investment Option", ["Lifestage", "Passive Lifestage", "Own Choice"]
)

# ----------------------------------------------------
# UPFRONT FEE CALC + DISPLAY (Preservation only)
# ----------------------------------------------------
upfront_fee_vat, upfront_fee_no_vat, upfront_rate_display = calculate_upfront_fee(
    estimated_lump_sum, pres_fee_option, VAT
)
net_lump_sum = estimated_lump_sum - upfront_fee_vat

if fund == "Preservation":
    if pres_fee_option == 1:
        st.markdown("<div class='section-heading'>Option 1 – Upfront Fee</div>", unsafe_allow_html=True)
        st.write(f"**Upfront Rate:** {upfront_rate_display:.3f}%")
        st.write(f"**Upfront Fee (Incl VAT):** R {upfront_fee_vat:,.2f}")
        st.write(f"**Net Amount Invested:** R {net_lump_sum:,.2f}")
    elif pres_fee_option == 2:
        st.markdown("<div class='section-heading'>Option 2 – Cancellation Fee</div>", unsafe_allow_html=True)
        st.write(
            "No initial fee is charged. However, if you withdraw funds, "
            "a cancellation fee applies based on your period of membership:"
        )
        opt2_data = {
            "Period of Membership": ["One year or less", "One to Three years", "Three to Five years", "Five years or more"],
            "Cancellation Fee": ["2.75% plus VAT", "1.75% plus VAT", "0.75% plus VAT", "0%"],
        }
        st.table(pd.DataFrame(opt2_data))
        st.write(f"**Net Amount Invested:** R {estimated_lump_sum:,.2f}")
    elif pres_fee_option == 3:
        st.markdown("<div class='section-heading'>Option 3 – Section 14 (No Fees)</div>", unsafe_allow_html=True)
        st.write("No upfront or cancellation fees apply.")
        st.write(f"**Net Amount Invested:** R {estimated_lump_sum:,.2f}")

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

    colA, colB, colC = st.columns([3, 1.2, 1.7])
    colA.write("**Portfolio**")
    colB.write("**Lump Sum %**")
    colC.write("**Monthly Contribution %**")

    for portfolio in TIC_DF["Portfolio"]:
        col1, col2, col3 = st.columns([3, 1.2, 1.7])
        col1.write(f"**{portfolio}**")
        lump_pct = col2.number_input("", min_value=0.0, max_value=100.0, key=f"{portfolio}_l")
        cont_pct = col3.number_input(" ", min_value=0.0, max_value=100.0, key=f"{portfolio}_c")
        tic      = float(TIC_DF.loc[TIC_DF["Portfolio"] == portfolio, "TIC"].iloc[0])
        allocations.append({
            "Portfolio":              portfolio,
            "TIC":                    tic,
            "Lump Sum %":             lump_pct,
            "Monthly Contribution %": cont_pct,
        })

    alloc_df = pd.DataFrame(allocations)
    imc = investment_mgmt_from_alloc(alloc_df, estimated_lump_sum)
    st.write(f"**Investment Management Fee (%):** {imc:.4f}%")
    st.dataframe(alloc_df.set_index("Portfolio"), hide_index=False)

# ----------------------------------------------------
# EAC — build via shared calculator
# ----------------------------------------------------
is_ra = fund == "Retirement Annuity"

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
    # Cancellation fee worst-case (2.75% + VAT) shown in Other row as RIY
    eac_upfront_fee = 0.0
    eac_cancel_fee = estimated_lump_sum * 0.0275 * (1 + VAT / 100)
    include_upfront = False
else:  # Option 3
    eac_upfront_fee = 0.0
    eac_cancel_fee = 0.0
    include_upfront = False

eac = compute_eac_table(
    fund_type                 = "RA" if is_ra else "Preservation",
    age                       = investor_age,
    investment_option         = investment_option,
    selected_portfolio        = ls_name,
    choice_allocations        = choice_allocs,
    ifa_fee_ex_vat            = ifa_fee_value,
    vat_rate                  = VAT,
    admin_base_ex_vat         = 0.75,
    tic_map                   = TIC_MAP,
    include_upfront_in_eac    = include_upfront,
    upfront_fee_incl_vat      = eac_upfront_fee,
    cancellation_fee_incl_vat = eac_cancel_fee,
    lump_sum                  = estimated_lump_sum,
    monthly_contribution      = monthly_contribution,
)

# Convert to PDF-compatible row dicts
eac_rows = eac_table_to_rows(eac, "RA" if is_ra else "Preservation")

# ----------------------------------------------------
# EAC TABLE PREVIEW (on-screen)
# ----------------------------------------------------
st.markdown("<div class='section-heading'>Effective Annual Cost (EAC)</div>", unsafe_allow_html=True)

eac_display_rows = []
for r in eac["rows"]:
    # Hide Other row if all values are zero/N/A
    if r["name"] == "Other":
        if all(v in ("0.00%", "N/A") for v in r["values"]):
            continue
    row_dict = {"": r["name"]}
    for col, val in zip(eac["columns"], r["values"]):
        row_dict[col] = val
    eac_display_rows.append(row_dict)

st.dataframe(
    pd.DataFrame(eac_display_rows),
    hide_index=True,
    use_container_width=True,
)

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
            "DateOfBirth":         dob.strftime("%d %B %Y"),
            "InvestorAge":         f"{investor_age_display} years",
            "InvestorEmail":       investor_email,
            "QuotationDate":       today.strftime("%d %B %Y"),
            "InitialLumpSum":      f"R {estimated_lump_sum:,.2f}",
            "MonthlyContribution": f"R {monthly_contribution:,.2f}",
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
            "DateOfBirth":        dob.strftime("%d %B %Y"),
            "InvestorAge":        f"{investor_age_display} years",
            "InvestorEmail":      investor_email,
            "QuotationDate":      today.strftime("%d %B %Y"),
            "InitialLumpSum":     f"R {estimated_lump_sum:,.2f}",
            "InitialFeeNoVAT":    f"R {pres_fee_no_vat:,.2f}",
            "InitialFeeVATAmt":   f"R {pres_vat_amt:,.2f}",
            "NetLumpSum":         f"R {net_lump_sum:,.2f}",
            "InvestmentOption":   investment_option,
            "LifestagePortfolio": ls_name or "",
            "LifestageTIC":       f"{ls_tic:.2f}%" if ls_tic else "",
            "LifestageTICValue":  ls_tic or 0.0,
            "LumpSumRaw":         estimated_lump_sum,
            "PresOption":         pres_fee_option,
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
