# ----------------------------------------------------
# RA PDF GENERATOR — ReportLab
# ----------------------------------------------------

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether
)
from io import BytesIO
import os

# ----------------------------------------------------
# COLOURS
# ----------------------------------------------------
DARK_BLUE   = colors.HexColor("#1A3D6F")
GOLD        = colors.HexColor("#C8A951")
LIGHT_GREY  = colors.HexColor("#F4F6FA")
MID_GREY    = colors.HexColor("#D6D9E0")
BLACK       = colors.HexColor("#1A1A1A")
WHITE       = colors.white
HIGHLIGHT   = colors.HexColor("#FFF3CD")   # amber highlight for active bracket

# ----------------------------------------------------
# STYLES
# ----------------------------------------------------
def make_styles():
    styles = {}

    styles["title_main"] = ParagraphStyle(
        "title_main", fontName="Helvetica-Bold", fontSize=20,
        textColor=DARK_BLUE, leading=26, spaceAfter=2,
    )
    styles["title_sub"] = ParagraphStyle(
        "title_sub", fontName="Helvetica", fontSize=13,
        textColor=colors.HexColor("#555555"), leading=18, spaceAfter=10,
    )
    styles["section_heading"] = ParagraphStyle(
        "section_heading", fontName="Helvetica-Bold", fontSize=12,
        textColor=DARK_BLUE, leading=16, spaceBefore=10, spaceAfter=4,
    )
    styles["numbered_heading"] = ParagraphStyle(
        "numbered_heading", fontName="Helvetica-Bold", fontSize=10,
        textColor=BLACK, leading=14, spaceBefore=6, spaceAfter=2,
    )
    styles["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9, textColor=BLACK,
        leading=13, spaceAfter=4, alignment=TA_JUSTIFY,
    )
    styles["body_left"] = ParagraphStyle(
        "body_left", fontName="Helvetica", fontSize=9, textColor=BLACK,
        leading=13, spaceAfter=4, alignment=TA_LEFT,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet", fontName="Helvetica", fontSize=9, textColor=BLACK,
        leading=13, spaceAfter=4, leftIndent=12, alignment=TA_JUSTIFY,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header", fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, leading=12, alignment=TA_CENTER,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell", fontName="Helvetica", fontSize=9,
        textColor=BLACK, leading=12, alignment=TA_LEFT,
    )
    styles["table_cell_center"] = ParagraphStyle(
        "table_cell_center", fontName="Helvetica", fontSize=9,
        textColor=BLACK, leading=12, alignment=TA_CENTER,
    )
    styles["table_label"] = ParagraphStyle(
        "table_label", fontName="Helvetica-Bold", fontSize=9,
        textColor=BLACK, leading=12, alignment=TA_LEFT,
    )
    styles["table_label_center"] = ParagraphStyle(
        "table_label_center", fontName="Helvetica-Bold", fontSize=9,
        textColor=BLACK, leading=12, alignment=TA_CENTER,
    )
    styles["option_heading"] = ParagraphStyle(
        "option_heading", fontName="Helvetica-Bold", fontSize=10,
        textColor=DARK_BLUE, leading=14, spaceBefore=8, spaceAfter=3,
    )
    styles["contact_heading"] = ParagraphStyle(
        "contact_heading", fontName="Helvetica-Bold", fontSize=9,
        textColor=BLACK, leading=13, spaceAfter=4,
    )
    styles["contact_body"] = ParagraphStyle(
        "contact_body", fontName="Helvetica", fontSize=8,
        textColor=BLACK, leading=12,
    )
    styles["signature_label"] = ParagraphStyle(
        "signature_label", fontName="Helvetica", fontSize=9,
        textColor=BLACK, leading=13,
    )

    return styles


# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def hr(thickness=0.5, color=MID_GREY, space_before=2, space_after=5):
    return HRFlowable(
        width="100%", thickness=thickness, color=color,
        spaceAfter=space_after, spaceBefore=space_before,
    )


def detail_table(rows, styles, col_widths=(90*mm, 80*mm)):
    data = [
        [Paragraph(label, styles["table_label"]),
         Paragraph(str(value), styles["table_cell"])]
        for label, value in rows
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  LIGHT_GREY),
        ("BACKGROUND",    (1, 0), (1, -1),  WHITE),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def option2_penalty_table(styles, CONTENT_W):
    """Shared Option 2 waived fee penalty table."""
    data = [
        [Paragraph("Period of Membership", styles["table_header"]),
         Paragraph("Withdrawal Fee", styles["table_header"])],
        [Paragraph("One year or less",    styles["table_cell"]),
         Paragraph("2.75% plus VAT",      styles["table_cell_center"])],
        [Paragraph("One to Three years",  styles["table_cell"]),
         Paragraph("1.75% plus VAT",      styles["table_cell_center"])],
        [Paragraph("Three to Five years", styles["table_cell"]),
         Paragraph("0.75% plus VAT",      styles["table_cell_center"])],
        [Paragraph("Five years or more",  styles["table_cell"]),
         Paragraph("0%",                  styles["table_cell_center"])],
    ]
    t = Table(data, colWidths=[100*mm, CONTENT_W - 100*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def option1_bracket_table(styles, CONTENT_W, lump_sum):
    """Static reference table showing full band amounts and fees. Total = sum of all bands."""
    FEE_BRACKETS = [
        {"min": 0,          "max": "150,000",        "rate": 2.75,  "band": 150000.00,     "fee": 4125.00},
        {"min": 150000.01,  "max": "350,000",        "rate": 1.375, "band": 199999.99,     "fee": 2750.00},
        {"min": 350000.01,  "max": "750,000",        "rate": 0.688, "band": 399999.99,     "fee": 2752.00},
        {"min": 750000.01,  "max": "2,000,000",      "rate": 0.344, "band": 1249999.99,    "fee": 4300.00},
        {"min": 2000000.01, "max": "5,000,000",      "rate": 0.25,  "band": 3999999.99,   "fee": 10000.00},
        {"min": 5000000.01, "max": "50,000,000",     "rate": 0.0,   "band": 44999999.99,  "fee": 0.0},
    ]

    header = [
        Paragraph("Min (R)",        styles["table_header"]),
        Paragraph("Max (R)",        styles["table_header"]),
        Paragraph("Rate",           styles["table_header"]),
        Paragraph("Band Amount (R)", styles["table_header"]),
        Paragraph("Fee (R)",        styles["table_header"]),
    ]
    data = [header]
    total_fee = sum(b["fee"] for b in FEE_BRACKETS)

    for b in FEE_BRACKETS:
        min_str = "\u2013" if b["min"] == 0 else f"{b['min']:,.2f}"
        fee_str = f"{b['fee']:,.2f}" if b["fee"] > 0 else "\u2013"
        cs = styles["table_cell_center"]
        data.append([
            Paragraph(min_str,          cs),
            Paragraph(b["max"],         cs),
            Paragraph(f"{b['rate']}%",  cs),
            Paragraph(f"{b['band']:,.2f}", cs),
            Paragraph(fee_str,          cs),
        ])

    data.append([
        Paragraph("Total",             styles["table_label"]),
        Paragraph("",                  styles["table_label_center"]),
        Paragraph("",                  styles["table_label_center"]),
        Paragraph("",                  styles["table_label_center"]),
        Paragraph(f"{total_fee:,.2f}", styles["table_label_center"]),
    ])
    total_row_idx = len(data) - 1

    col_w = CONTENT_W / 5
    t = Table(data, colWidths=[col_w * 0.9, col_w * 0.9, col_w * 0.65, col_w * 1.1, col_w * 1.45])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),               DARK_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, total_row_idx-1), [WHITE, LIGHT_GREY]),
        ("BACKGROUND",    (0, total_row_idx), (-1, total_row_idx), LIGHT_GREY),
        ("FONTNAME",      (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 1), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    return t


def fund_allocation_table(styles, CONTENT_W, lump_sum, inv_option, ls_name, ls_tic, alloc_df,
                          upfront_fee_vat=0.0, advice_fee_incl_vat=0.0):
    """
    Portfolio | Lump Sum Investment (R) | Initial Fee (R) | Ongoing Fee % | Fund TIC %
    Initial Fee = once-off upfront fee incl VAT (Option 1 only; shown on first/total row).
    Ongoing Fee % = annual advice fee incl VAT only.
    """
    header = [
        Paragraph("Portfolio",               styles["table_header"]),
        Paragraph("Lump Sum\nInvestment (R)", styles["table_header"]),
        Paragraph("Initial Fee (R)",          styles["table_header"]),
        Paragraph("Ongoing Fee %",            styles["table_header"]),
        Paragraph("Fund TIC %",              styles["table_header"]),
    ]
    data = [header]

    initial_fee_str = f"{upfront_fee_vat:,.2f}" if upfront_fee_vat > 0 else "\u2013"
    advice_str      = f"{advice_fee_incl_vat:.2f}%" if advice_fee_incl_vat > 0 else "\u2013"

    if inv_option == "Choice" and alloc_df is not None:
        active = alloc_df[(alloc_df["Lump Sum %"] > 0) | (alloc_df["Monthly Contribution %"] > 0)]
        total_weighted_tic = 0.0
        total_alloc = 0.0
        first = True
        for _, row in active.iterrows():
            alloc_r = lump_sum * (row["Lump Sum %"] / 100)
            total_alloc += alloc_r
            total_weighted_tic += alloc_r * (row["TIC"] / 100)
            # Initial fee and advice only on first row
            data.append([
                Paragraph(row["Portfolio"],                        styles["table_cell"]),
                Paragraph(f"{alloc_r:,.2f}",                      styles["table_cell_center"]),
                Paragraph(initial_fee_str if first else "",        styles["table_cell_center"]),
                Paragraph(advice_str      if first else "",        styles["table_cell_center"]),
                Paragraph(f"{row['TIC']:.2f}%",                   styles["table_cell_center"]),
            ])
            first = False
        weighted_tic = (total_weighted_tic / lump_sum * 100) if lump_sum > 0 else 0
        data.append([
            Paragraph("Weighted Fee",         styles["table_label"]),
            Paragraph(f"{total_alloc:,.2f}",  styles["table_label_center"]),
            Paragraph("",                     styles["table_label_center"]),
            Paragraph("",                     styles["table_label_center"]),
            Paragraph(f"{weighted_tic:.2f}%", styles["table_label_center"]),
        ])
    else:
        tic = ls_tic if ls_tic else 0.0
        data.append([
            Paragraph(ls_name or "",       styles["table_cell"]),
            Paragraph(f"{lump_sum:,.2f}",  styles["table_cell_center"]),
            Paragraph(initial_fee_str,     styles["table_cell_center"]),
            Paragraph(advice_str,          styles["table_cell_center"]),
            Paragraph(f"{tic:.2f}%",       styles["table_cell_center"]),
        ])
        data.append([
            Paragraph("Weighted Fee",      styles["table_label"]),
            Paragraph(f"{lump_sum:,.2f}",  styles["table_label_center"]),
            Paragraph("",                  styles["table_label_center"]),
            Paragraph("",                  styles["table_label_center"]),
            Paragraph(f"{tic:.2f}%",       styles["table_label_center"]),
        ])

    total_row_idx = len(data) - 1
    col_w = CONTENT_W / 5
    t = Table(data, colWidths=[col_w * 1.6, col_w * 1.0, col_w * 0.85, col_w * 0.85, col_w * 0.7])
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),              DARK_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, total_row_idx-1), [WHITE, LIGHT_GREY]),
        ("BACKGROUND",    (0, total_row_idx), (-1, total_row_idx), LIGHT_GREY),
        ("FONTNAME",      (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


# ----------------------------------------------------
# MAIN GENERATOR
# ----------------------------------------------------
def generate_ra_pdf(field_values: dict, alloc_df=None) -> bytes:

    buffer  = BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN  = 20 * mm

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Destiny RA Investment Overview",
    )

    S = make_styles()
    story = []
    CONTENT_W = PAGE_W - 2 * MARGIN

    inv_option        = field_values.get("InvestmentOption", "")
    ls_portfolio      = field_values.get("LifestagePortfolio", "")
    ls_tic_val        = field_values.get("LifestageTICValue", 0.0)
    lump_sum_raw      = field_values.get("LumpSumRaw", 0.0)
    pres_option       = field_values.get("PresOption", 1)
    upfront_fee_vat   = field_values.get("UpfrontFeeVATRaw", 0.0)
    advice_fee_incl_vat = field_values.get("AdviceFeeInclVAT", 0.0)

    # --------------------------------------------------
    # LOGO
    # --------------------------------------------------
    logo_path = "destiny_logo.png"
    if not os.path.exists(logo_path):
        logo_path = "assets/logo_destiny.png"

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=18*mm, kind="proportional")
        ht = Table([[logo, ""]], colWidths=[80*mm, CONTENT_W - 80*mm])
        ht.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
        story.append(ht)
        story.append(Spacer(1, 5*mm))

    # --------------------------------------------------
    # PAGE 1 — TITLE + INTRO BULLETS
    # --------------------------------------------------
    story.append(Paragraph("Destiny Retirement Annuity Fund", S["title_main"]))
    story.append(Paragraph("Investment Overview", S["title_sub"]))
    story.append(hr(thickness=1.5, color=GOLD, space_before=2, space_after=6))

    for b in [
        "You can use the Destiny Retirement Annuity Fund (the Fund) to save for retirement in a tax-efficient manner.",
        "All lump sum and regular investments in the Destiny Retirement Annuity are split between the retirement component and the savings component. We invest one-third of the investment amount in your savings component and two-thirds in your retirement component.",
        "You may only access your retirement component money when you retire. You cannot retire before the age of 55 unless you are permanently disabled, or you emigrate or if your investment value across all your investments in the Fund is less than R15,000.",
        "If you are transferring a compulsory investment to the Retirement Annuity it could include a vested component with vested benefits and/or non-vested benefits, a retirement component, and a savings component. The transferring fund will indicate the components that are included. The investment and fee account selection of this proposal will apply to all components.",
        "When you retire a maximum of one-third of the market value of your investment can be taken as cash. The remainder must be used to purchase an income-providing vehicle such as the Destiny Living Annuity.",
        "If you have not agreed to invest according to the LifeStage Model as recommended by the Board of Trustees then you are responsible for ensuring that the Portfolio you select meets your investment needs and risk profile.",
        "The investment portfolios provide no guarantees. As the value of the investment account may go down as well as up, you bear the risk of the investment performance.",
        "Once your investment has been processed, there is no cooling-off period and your investment cannot be cancelled. However, you may transfer your investment to another retirement annuity fund registered under the provisions of the Pension Funds Act (1956).",
    ]:
        story.append(Paragraph(f"\u2022\u2002{b}", S["bullet"]))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 2 — PERSONAL + INVESTMENT DETAILS
    # --------------------------------------------------
    story.append(Paragraph("Personal Details", S["section_heading"]))
    story.append(hr())
    story.append(detail_table([
        ("Investor Name",     field_values.get("InvestorName", "")),
        ("Date of Birth",     field_values.get("DateOfBirth", "")),
        ("Current Age",       field_values.get("InvestorAge", "")),
        ("E-mail",            field_values.get("InvestorEmail", "")),
        ("Date of Quotation", field_values.get("QuotationDate", "")),
    ], S, col_widths=(80*mm, CONTENT_W - 80*mm)))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("Investment Details", S["section_heading"]))
    story.append(hr())
    monthly = field_values.get("MonthlyContribution", "R 0.00")
    story.append(detail_table([
        ("Initial lump sum contribution",                       field_values.get("InitialLumpSum", "")),
        ("Initial Fee including VAT",                           field_values.get("InitialFeeVAT", "")),
        ("Lump sum invested after initial fees",                field_values.get("NetLumpSum", "")),
        ("Recurring contribution",                              monthly),
        ("Recurring contribution invested after initial fees",  monthly),
    ], S, col_widths=(110*mm, CONTENT_W - 110*mm)))
    story.append(Spacer(1, 5*mm))

    # Option 1 bracket table — only show when Option 1 is selected
    if pres_option == 1:
        story.append(Paragraph("Option 1 \u2013 Upfront Fee Schedule", S["section_heading"]))
        story.append(hr())
        story.append(option1_bracket_table(S, CONTENT_W, lump_sum_raw))

    # Option 2 — only show when Option 2 is selected
    if pres_option == 2:
        story.append(Paragraph("Option 2 \u2013 Waived Initial Fee", S["section_heading"]))
        story.append(hr())
        story.append(Paragraph(
            "No initial fee is charged. However, if you withdraw funds before age 55, for any reason, "
            "then the following fee will be charged on the withdrawal amount, before any tax is calculated "
            "and based on the following period of membership.",
            S["body"]
        ))
        story.append(Spacer(1, 3*mm))
        story.append(option2_penalty_table(S, CONTENT_W))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 3 — LIFESTAGE MODEL + PORTFOLIO SELECTION
    # --------------------------------------------------
    story.append(Paragraph("Destiny LifeStage Model", S["section_heading"]))
    story.append(hr())
    story.append(Paragraph(
        "The Destiny Retirement Annuity\u2019s default investment portfolio is the Destiny LifeStage Model. "
        "Unless you advise us per Section 4 hereunder, you will automatically be invested in the Life Stage Model. "
        "The Model invests your assets according to your age and assumes a retirement age of 65. "
        "Based on the information per this overview, your Investment Portfolio at inception will be the:",
        S["body"]
    ))
    story.append(Spacer(1, 3*mm))

    # LifeStage table — only show the applicable row
    if inv_option == "Lifestage":
        ls_rows = [[Paragraph("LifeStage Model:", S["table_label"]),
                    Paragraph(ls_portfolio, S["table_cell"])]]
    elif inv_option == "Passive Lifestage":
        ls_rows = [[Paragraph("Passive LifeStage Model:", S["table_label"]),
                    Paragraph(ls_portfolio, S["table_cell"])]]
    else:
        ls_rows = None   # Choice — no lifestage table

    if ls_rows:
        ls_table = Table(ls_rows, colWidths=[80*mm, CONTENT_W - 80*mm])
        ls_table.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
            ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
            ("BACKGROUND",    (0, 0), (0, -1),  LIGHT_GREY),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ]))
        story.append(ls_table)
        story.append(Spacer(1, 6*mm))

    # Portfolio selection — only for Choice
    if inv_option == "Choice":
        story.append(Paragraph("Personal Portfolio Selection", S["section_heading"]))
        story.append(hr())

        if alloc_df is not None:
            active = alloc_df[(alloc_df["Lump Sum %"] > 0) | (alloc_df["Monthly Contribution %"] > 0)]
        else:
            active = None

        if active is not None and len(active) > 0:
            ch_data = [[
                Paragraph("Portfolio",   S["table_header"]),
                Paragraph("Lump Sum %",  S["table_header"]),
                Paragraph("Monthly %",   S["table_header"]),
            ]]
            for _, row in active.iterrows():
                ch_data.append([
                    Paragraph(row["Portfolio"],                        S["table_cell"]),
                    Paragraph(f"{row['Lump Sum %']:.1f}%",            S["table_cell_center"]),
                    Paragraph(f"{row['Monthly Contribution %']:.1f}%", S["table_cell_center"]),
                ])
            ch_table = Table(ch_data, colWidths=[CONTENT_W - 60*mm, 30*mm, 30*mm])
            ch_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
                ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
                ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ]))
            story.append(ch_table)
        else:
            story.append(Paragraph("No portfolio allocations entered.", S["body_left"]))

        # Investor declaration (Choice only)
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph(
            "I have elected to Opt Out of the Destiny LifeStage Model and I have selected the portfolios "
            "as per the above table.",
            S["body_left"]
        ))
        story.append(Spacer(1, 8*mm))
        sig_data = [[
            Paragraph("Signature of investor", S["signature_label"]),
            Paragraph("", S["signature_label"]),
        ]]
        sig_table = Table(sig_data, colWidths=[40*mm, CONTENT_W - 40*mm])
        sig_table.setStyle(TableStyle([
            ("LINEBELOW",     (1, 0), (1, 0), 0.5, BLACK),
            ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(sig_table)
        story.append(Spacer(1, 5*mm))

    # Fund allocation table (all options)
    story.append(Paragraph("Fund Allocation Detail", S["section_heading"]))
    story.append(hr())
    story.append(fund_allocation_table(S, CONTENT_W, lump_sum_raw, inv_option, ls_portfolio, ls_tic_val, alloc_df,
                                        upfront_fee_vat=upfront_fee_vat, advice_fee_incl_vat=advice_fee_incl_vat))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 4 — EAC TABLE + FEE DESCRIPTIONS
    # --------------------------------------------------
    story.append(Paragraph("Effective Annual Cost (EAC)", S["section_heading"]))
    story.append(hr())
    story.append(Paragraph(
        "The effective annual cost (EAC) is a measure that has been introduced to allow you to compare the charges "
        "you incur and their effect on investment returns when you invest in different financial products. It is "
        "expressed as an annualised percentage. The EAC is made up of four components which are added together, "
        "as shown in the table below. The effect of some of the charges may vary, depending on your investment "
        "period. The EAC calculation assumes that an investor ends his or her investment in the financial product "
        "at the end of the relevant periods shown in the table.",
        S["body"]
    ))
    story.append(Spacer(1, 3*mm))

    eac_rows = field_values.get("EACRows", [])

    eac_header = [
        Paragraph("", S["table_header"]),
        Paragraph("Next 1 year",   S["table_header"]),
        Paragraph("Next 3 years",  S["table_header"]),
        Paragraph("Next 5 years",  S["table_header"]),
        Paragraph("Next 10 years", S["table_header"]),
        Paragraph("Age 55",        S["table_header"]),
    ]
    eac_data = [eac_header]

    def fmt(v):
        return f"{v:.2f}%" if v is not None else "N/A"

    for row in eac_rows:
        is_total = row.get("is_total", False)
        # All cells centered; label bold if total
        lbl_s = S["table_label_center"] if is_total else S["table_cell_center"]
        val_s = S["table_label_center"] if is_total else S["table_cell_center"]
        eac_data.append([
            Paragraph(row["label"],         lbl_s),
            Paragraph(fmt(row.get("y1")),   val_s),
            Paragraph(fmt(row.get("y3")),   val_s),
            Paragraph(fmt(row.get("y5")),   val_s),
            Paragraph(fmt(row.get("y10")),  val_s),
            Paragraph(fmt(row.get("y55")),  val_s),
        ])

    total_row_idx = len(eac_data) - 1
    col_w = CONTENT_W / 6
    eac_table = Table(
        eac_data,
        colWidths=[col_w * 1.8, col_w * 0.84, col_w * 0.84, col_w * 0.84, col_w * 0.84, col_w * 0.84]
    )
    eac_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("ROWBACKGROUNDS",(0, 1), (-1, total_row_idx - 1), [WHITE, LIGHT_GREY]),
        ("BACKGROUND",    (0, total_row_idx), (-1, total_row_idx), LIGHT_GREY),
        ("FONTNAME",      (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    story.append(eac_table)
    story.append(Spacer(1, 6*mm))

    for heading, body_text in [
        ("1.\u2002Investment Management Charges", [
            "The next table shows the investment fund manager initial and ongoing fees, the investment fund total "
            "investment charges (TIC) and the investment fund manager rebate for the investment funds that you chose. "
            "An estimate of the total fee that you will pay for investment management is the fund TIC less any rebate, "
            "plus the effect of any initial fee. This is the calculation we use for the figure we show in the EAC table.",

            "The investment managers charge an ongoing fee for managing the assets of a particular investment fund on "
            "your behalf. The fee is based on the market value of the underlying investment in each of the investment "
            "funds. It is included in the price of the fund and will not reflect as a separate fee on the investment. "
            "There are management and operating costs in the investment fund that could have an impact on an "
            "investment\u2019s growth. The TIC is a recognised method to measure this. It includes the investment "
            "manager\u2019s ongoing fee as well as any other expenses incurred inside the fund over the last year, "
            "such as performance fees and the costs of buying and selling assets underlying the investment component. "
            "The TIC is a backward-looking measure, which means that it could change from year to year. If the TIC is "
            "not available, we use the total expense ratio (TER), which is the TIC excluding transaction costs. Where "
            "neither the TIC nor the TER is available, we use the investment manager\u2019s ongoing fee.",

            "For some investment funds, we perform specialised administrative functions on behalf of the investment "
            "managers. In certain agreed circumstances, the investment manager refunds part of the investment fund "
            "manager ongoing fee to us \u2013 this is called a rebate. We pass all rebates on all investment funds "
            "back to you. The quoted rebates are at the discretion of the fund manager who can change or withdraw it "
            "at any time.",
        ]),
        ("2.\u2002Advice Charges", [
            "Your financial adviser will receive a yearly ongoing fee, illustrated above, of the market value of your "
            "investment. We will calculate the amount of the ongoing fee and pay it to your financial adviser every "
            "month. These fees are negotiated between you and your financial adviser.",
        ]),
        ("3.\u2002Administration Charges", [
            "We charge an ongoing administration fee for the initial setup and ongoing administration of your "
            "investment. The ongoing administration fee is illustrated in the above table. We show the combined "
            "effect of all administration fees in the administration charge component in the EAC table.",
        ]),
        ("4.\u2002Other Charges", [
            "This fee is paid to GIB Financial Services for portfolio construction\u2026",
        ]),
    ]:
        items = [Paragraph(heading, S["numbered_heading"])]
        items += [Paragraph(t, S["body"]) for t in body_text]
        story.append(KeepTogether(items))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 5 — IMPORTANT NOTES + CONTACT
    # --------------------------------------------------
    story.append(Paragraph("Important Notes", S["section_heading"]))
    story.append(hr())

    for note in [
        "The Destiny Retirement Annuity Fund (\u201cthe Fund\u201d) is an approved retirement annuity fund. The Fund "
        "is administered by GIB Financial Services (Pty) Limited (\u201cthe Administrator\u201d), an approved fund "
        "administrator and an authorised financial services provider. The Administrator holds professional indemnity "
        "and fidelity insurance cover.",

        "Your interest in the Fund will be managed through an investment account. You will be invested according to "
        "the LifeStage Model unless you elect to Opt Out and select one or more investment portfolio as made "
        "available by the Fund.",

        "The investment portfolios provide no guarantees. As the value of the investment account may go down as well "
        "as up, you bear the risk of the investment performance.",

        "\u2013 The business cut off for receiving an instruction is the last day of the month. The instruction will "
        "only be processed once the funds reflect in Destiny\u2019s bank account and supporting documents and proof "
        "of deposit are received. Should an instruction be received after the last day of the month then it will "
        "only be processed on the following month or earlier at the administrator\u2019s discretion.",

        "\u2013 The unit price that will apply is the price at which the Investment Administrator completes the "
        "purchase of units.",

        "\u2013 You have 14 days after receipt of the investment confirmation from the Administrator, to report any "
        "errors to the administrator. The administrator reserves the right to determine whether it has acted "
        "incorrectly on the investor\u2019s instruction.",

        "\u2013 A switch instruction between investment portfolios will take effect within 7 working days after "
        "receipt thereof.",

        "\u2013 A withdrawal notification in the prescribed format will take a maximum of ten business days to "
        "process.",

        "In the event of your death before retirement, the trustees of the Fund have the discretion, in terms of "
        "Section 37C of the Pension Funds Act 24 of 1956 to apportion the benefit that may become payable between "
        "beneficiaries nominated by you and your dependants. Subject to legislation, the beneficiaries and "
        "dependants may have the option of receiving their benefit in cash and/or as a pension. These benefits may "
        "qualify for tax concessions up to certain limits.",

        "You may transfer your investment in the Destiny Retirement Annuity Fund to another retirement annuity fund. "
        "These transfers are subject to the requirements of the Destiny Retirement Annuity Fund, the fund you "
        "transfer to and legislation at the time.",
    ]:
        story.append(Paragraph(note, S["body"]))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'For comprehensive information please refer to the Conditions of Membership available at '
        '<link href="http://www.gib.co.za"><u>www.gib.co.za</u></link> or via the call centre on 0860 00FUND (3863).',
        S["body_left"]
    ))
    # Investor Declaration
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Investor Declaration", S["section_heading"]))
    story.append(hr())
    story.append(Paragraph(
        "I confirm that I have read and understand the information provided in this investment overview.",
        S["body_left"]
    ))
    story.append(Spacer(1, 8*mm))
    sig_data = [[
        Paragraph("Signed at", S["signature_label"]),
        Paragraph("",          S["signature_label"]),
        Paragraph("Date",      S["signature_label"]),
        Paragraph("",          S["signature_label"]),
    ]]
    sig_table = Table(sig_data, colWidths=[20*mm, 80*mm, 15*mm, 55*mm])
    sig_table.setStyle(TableStyle([
        ("LINEBELOW",     (1, 0), (1, 0), 0.5, BLACK),
        ("LINEBELOW",     (3, 0), (3, 0), 0.5, BLACK),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8*mm))

    half = (CONTENT_W - 6*mm) / 2
    contact_table = Table([[
        [
            Paragraph("Contact Details",                      S["contact_heading"]),
            Paragraph("Destiny Retirement Annuity Fund",      S["contact_body"]),
            Paragraph("FSCA registration Number 12/8/38116/R",S["contact_body"]),
            Paragraph("P O Box 3211, Houghton, 2041",         S["contact_body"]),
            Paragraph("Telephone: 0860 00FUND (3863)",        S["contact_body"]),
            Paragraph("rfs@gib.co.za",                        S["contact_body"]),
            Paragraph("www.gib.co.za",                        S["contact_body"]),
        ],
        [
            Paragraph("Administrator",                        S["contact_heading"]),
            Paragraph("GIB Financial Services (Pty) Ltd",     S["contact_body"]),
            Paragraph("Section 13B approval number 24/267",   S["contact_body"]),
            Paragraph("Financial Service Provider number 9305",S["contact_body"]),
            Paragraph("P O Box 3211, Houghton, 2041",         S["contact_body"]),
            Paragraph("Telephone: (011) 483 1212",            S["contact_body"]),
            Paragraph('<link href="mailto:rfs@gib.co.za"><font color="#0563C1"><u>rfs@gib.co.za</u></font></link>', S["contact_body"]),
            Paragraph("www.gib.co.za",                        S["contact_body"]),
        ],
    ]], colWidths=[half, half])
    contact_table.setStyle(TableStyle([
        ("BOX",           (0, 0), (0, 0), 0.5, MID_GREY),
        ("BOX",           (1, 0), (1, 0), 0.5, MID_GREY),
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEAFTER",     (0, 0), (0, 0),   0.5, MID_GREY),
    ]))
    story.append(contact_table)

    doc.build(story)
    return buffer.getvalue()
