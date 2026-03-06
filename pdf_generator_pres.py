# ----------------------------------------------------
# PRESERVATION PDF GENERATOR — ReportLab
# ----------------------------------------------------

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
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
DARK_BLUE  = colors.HexColor("#1A3D6F")
GOLD       = colors.HexColor("#C8A951")
LIGHT_GREY = colors.HexColor("#F4F6FA")
MID_GREY   = colors.HexColor("#D6D9E0")
BLACK      = colors.HexColor("#1A1A1A")
WHITE      = colors.white


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
        textColor=DARK_BLUE, leading=16, spaceBefore=6, spaceAfter=2,
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
        leading=14, spaceAfter=6, leftIndent=0, firstLineIndent=0,
        alignment=TA_JUSTIFY,
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
    data = [
        [Paragraph("Period of Membership", styles["table_header"]),
         Paragraph("Cancellation Fee",     styles["table_header"])],
        [Paragraph("One year or less",     styles["table_cell"]),
         Paragraph("2.75% plus VAT",       styles["table_cell_center"])],
        [Paragraph("One to Three years",   styles["table_cell"]),
         Paragraph("1.75% plus VAT",       styles["table_cell_center"])],
        [Paragraph("Three to Five years",  styles["table_cell"]),
         Paragraph("0.75% plus VAT",       styles["table_cell_center"])],
        [Paragraph("Five years or more",   styles["table_cell"]),
         Paragraph("0%",                   styles["table_cell_center"])],
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


# ----------------------------------------------------
# MAIN GENERATOR
# ----------------------------------------------------
def generate_pres_pdf(field_values: dict, alloc_df=None) -> bytes:

    buffer = BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Destiny Preservation Fund Investment Overview",
    )

    S = make_styles()
    story = []
    CONTENT_W = PAGE_W - 2 * MARGIN

    inv_option  = field_values.get("InvestmentOption", "")
    ls_portfolio = field_values.get("LifestagePortfolio", "")
    ls_tic_val  = field_values.get("LifestageTICValue", 0.0)
    lump_sum_raw = field_values.get("LumpSumRaw", 0.0)
    pres_option  = field_values.get("PresOption", 1)

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
        story.append(Spacer(1, 3*mm))

    # --------------------------------------------------
    # PAGE 1 — TITLE + INTRO BULLETS
    # --------------------------------------------------
    story.append(Paragraph("Destiny Preservation Funds", S["title_main"]))
    story.append(Paragraph("Investment Overview", S["title_sub"]))
    story.append(hr(thickness=1.5, color=GOLD, space_before=2, space_after=8))

    story.append(Paragraph(
        "<b>Important information about the Destiny Preservation Funds:</b>",
        S["body_left"]
    ))
    story.append(Spacer(1, 2*mm))

    for b in [
        "You can use the Destiny Preservation Funds (the Funds) to preserve your existing retirement savings from a Pension or Provident Fund.",
        "You may also use the Destiny Preservation Funds to preserve retirement savings from another Preservation Fund.",
        "You may be allowed to make a once-off partial or full withdrawal before retirement. This is subject to the restrictions of the transferring fund and legislation/regulations.",
        "You cannot retire from the Fund before age 55 unless you are permanently disabled.",
        "When you retire from the Destiny Preservation Pension Fund, a maximum of one-third of your investment can be taken as cash. The remainder must be used to purchase an annuity such as the Destiny Living Annuity. The amount taken in cash is taxable.",
        "If you have not agreed to invest according to the LifeStage Model as recommended by the Board of Trustees then you are responsible for ensuring that the Portfolio you select meets your investment needs and risk profile.",
        "The return on your investment is not guaranteed. As the market value of your investment may change, you carry the risk of losing.",
        "Once your investment has been processed, there is no cooling-off period and your investment cannot be cancelled. However, you may transfer your investment to another preservation fund or employer fund registered under the provisions of the Pension Funds Act (1956).",
    ]:
        story.append(Paragraph(f"\u2022\u2002{b}", S["bullet"]))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 2 — PERSONAL + INVESTMENT DETAILS + FEE OPTION
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
    story.append(detail_table([
        ("Initial lump sum contribution",        field_values.get("InitialLumpSum", "")),
        ("Lump sum invested after initial fees",  field_values.get("NetLumpSum", "")),
    ], S, col_widths=(110*mm, CONTENT_W - 110*mm)))
    story.append(Spacer(1, 5*mm))

    # Fee option section
    story.append(Paragraph("Fee Option Selected", S["section_heading"]))
    story.append(hr())

    if pres_option == 1:
        story.append(Paragraph("Option 1 \u2013 Upfront Fee", S["option_heading"]))
        story.append(Paragraph(
            "An upfront fee applies on the initial lump sum investment, as per the fee schedule, "
            "capped at R7,500 (inclusive of VAT).",
            S["body"]
        ))
    elif pres_option == 2:
        story.append(Paragraph("Option 2 \u2013 Cancellation Fee", S["option_heading"]))
        story.append(Paragraph(
            "No upfront fee is charged. However, if you withdraw funds, a cancellation fee applies "
            "based on your period of membership as per the table below.",
            S["body"]
        ))
        story.append(Spacer(1, 3*mm))
        story.append(option2_penalty_table(S, CONTENT_W))
    elif pres_option == 3:
        story.append(Paragraph("Option 3 \u2013 Section 14 (No Fees)", S["option_heading"]))
        story.append(Paragraph(
            "No upfront fee and no cancellation fee apply to this investment.",
            S["body"]
        ))

    story.append(Spacer(1, 6*mm))

    # --------------------------------------------------
    # LIFESTAGE + PORTFOLIO SELECTION
    # Build entire block then wrap in KeepTogether so it
    # either fits on this page or moves to the next page.
    # --------------------------------------------------
    ls_block = []

    ls_block.append(Paragraph("Destiny LifeStage Model", S["section_heading"]))
    ls_block.append(hr())
    ls_block.append(Paragraph(
        "The Destiny Retirement Funds\u2019 default investment portfolio is the Destiny LifeStage Model. "
        "Unless you advise us as per your portfolio selection, you will automatically be invested in the Life Stage Model. "
        "The Model invests your assets according to your age and assumes a retirement age of 65. "
        "Based on the information as per this overview, your Investment Portfolio at inception will be the:",
        S["body"]
    ))
    ls_block.append(Spacer(1, 3*mm))

    # LifeStage table — only the applicable row
    if inv_option == "Lifestage":
        ls_rows = [[Paragraph("LifeStage Model:", S["table_label"]),
                    Paragraph(ls_portfolio, S["table_cell"])]]
    elif inv_option == "Passive Lifestage":
        ls_rows = [[Paragraph("Passive LifeStage Model:", S["table_label"]),
                    Paragraph(ls_portfolio, S["table_cell"])]]
    else:
        ls_rows = None

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
        ls_block.append(ls_table)
        ls_block.append(Spacer(1, 3*mm))

    # Portfolio selection — Own Choice only
    if inv_option == "Own Choice":
        ls_block.append(Paragraph("Personal Portfolio Selection", S["section_heading"]))
        ls_block.append(hr())

        if alloc_df is not None:
            active = alloc_df[(alloc_df["Lump Sum %"] > 0) | (alloc_df["Monthly Contribution %"] > 0)]
        else:
            active = None

        if active is not None and len(active) > 0:
            ch_data = [[
                Paragraph("Portfolio",  S["table_header"]),
                Paragraph("Lump Sum %", S["table_header"]),
                Paragraph("Monthly %",  S["table_header"]),
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
            ls_block.append(ch_table)
        else:
            ls_block.append(Paragraph("No portfolio allocations entered.", S["body_left"]))

        # Investor declaration (Own Choice only)
        ls_block.append(Spacer(1, 3*mm))
        ls_block.append(Paragraph(
            "I have elected to Opt Out of the Destiny LifeStage Model and I have selected the portfolios "
            "as per the above table.",
            S["body_left"]
        ))
        ls_block.append(Spacer(1, 4*mm))
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
        ls_block.append(sig_table)
        ls_block.append(Spacer(1, 3*mm))

    story.append(KeepTogether(ls_block))
    story.append(PageBreak())

    # --------------------------------------------------
    # EAC TABLE (4 cols) + FEE DESCRIPTIONS (all on one page)
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
        Paragraph("",             S["table_header"]),
        Paragraph("Next 1 year",  S["table_header"]),
        Paragraph("Next 3 years", S["table_header"]),
        Paragraph("Next 5 years", S["table_header"]),
        Paragraph("Age 55",       S["table_header"]),
    ]
    eac_data = [eac_header]

    def fmt(v):
        return f"{v:.2f}%" if v is not None else "N/A"

    for row in eac_rows:
        # Hide Other row if all values are zero
        if row["label"] == "Other":
            vals = [row.get(k) for k in ("y1", "y3", "y5", "y55")]
            if all((v is None or v == 0.0) for v in vals):
                continue
        is_total = row.get("is_total", False)
        cs = S["table_label_center"] if is_total else S["table_cell_center"]
        eac_data.append([
            Paragraph(row["label"],        cs),
            Paragraph(fmt(row.get("y1")),  cs),
            Paragraph(fmt(row.get("y3")),  cs),
            Paragraph(fmt(row.get("y5")),  cs),
            Paragraph(fmt(row.get("y55")), cs),
        ])

    total_row_idx = len(eac_data) - 1
    col_w = CONTENT_W / 5
    eac_table = Table(
        eac_data,
        colWidths=[col_w * 1.8, col_w * 0.8, col_w * 0.8, col_w * 0.8, col_w * 0.8]
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
    story.append(Spacer(1, 3*mm))

    # Other charges description changes based on pres_option
    if pres_option == 2:
        other_charges_text = [
            "This fee is paid to GIB Financial Services for portfolio construction\u2026",
            "A cancellation fee may apply if you withdraw your investment before the applicable period. "
            "The cancellation fee shown in the Advice row of the EAC table above reflects the worst-case "
            "reduction in yield based on the maximum cancellation fee of 2.75% (plus VAT).",
        ]
    else:
        other_charges_text = [
            "This fee is paid to GIB Financial Services for portfolio construction\u2026",
        ]

    for heading, body_texts in [
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
        ("4.\u2002Other Charges", other_charges_text),
    ]:
        items = [Paragraph(heading, S["numbered_heading"])]
        items += [Paragraph(t, S["body"]) for t in body_texts]
        story.append(KeepTogether(items))

    story.append(PageBreak())

    # --------------------------------------------------
    # PAGE 5 — IMPORTANT NOTES + DECLARATION + CONTACT
    # --------------------------------------------------
    story.append(Paragraph("Important Notes", S["section_heading"]))
    story.append(hr())

    for note in [
        "The Funds are approved preservation funds administered by GIB Financial Services (Pty) Limited "
        "(\u201cthe Administrator\u201d), an approved fund administrator and an authorised financial services "
        "provider. The Administrator holds professional indemnity and fidelity insurance cover.",

        "Your interest in the Funds will be managed through an investment account. You will be invested according "
        "to the LifeStage Model unless you elect to Opt Out and select one or more investment portfolio as made "
        "available by the Fund.",

        "The investment portfolios provide no guarantees. As the value of the investment account may go down as "
        "well as up, you bear the risk of the investment performance.",

        "\u2013 The business cut off for receiving an instruction is the last day of the month. The instruction "
        "will only be processed once the funds reflect in the Destiny bank account and supporting documents and "
        "proof of deposit have been received. Should an instruction be received after the last day of the month "
        "then it will only be processed on the following month or earlier at the administrator\u2019s discretion.",

        "\u2013 The unit price that will apply is the price at which the Investment Administrator completes the "
        "purchase of units.",

        "\u2013 You have 14 days after receipt of the investment confirmation from the Administrator, to report "
        "any errors to the administrator. The administrator reserves the right to determine whether it has acted "
        "incorrectly on the investor\u2019s instruction.",

        "\u2013 A switch instruction between investment portfolios will take effect within 7 working days after "
        "receipt thereof.",

        "\u2013 A withdrawal notification in the prescribed format will take a maximum of ten business days to "
        "process.",

        "In the event of your death before retirement, the trustees of the Fund have the discretion, in terms of "
        "Section 37C of the Pension Funds Act 24 of 1956, to apportion the benefit that may become payable "
        "between beneficiaries nominated by you and your dependants. Subject to legislation, the beneficiaries "
        "and dependants may have the option of receiving their benefit in cash and/or as a pension. These "
        "benefits may qualify for tax concessions up to certain limits.",

        "You may transfer your investment in the Fund to another Preservation Fund. These transfers are subject "
        "to the requirements of the Destiny Preservation Funds, the fund you transfer to and legislation at the "
        "time.",
    ]:
        story.append(Paragraph(note, S["body"]))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'For comprehensive information please refer to the Conditions of Membership available at '
        '<link href="http://www.gib.co.za"><u>www.gib.co.za</u></link> or via the call centre on 0860 00FUND (3863).',
        S["body_left"]
    ))

    # Investor Declaration
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Investor Declaration", S["section_heading"]))
    story.append(hr())
    story.append(Paragraph(
        "I confirm that I have read and understand the information provided in this investment overview.",
        S["body_left"]
    ))
    story.append(Spacer(1, 4*mm))
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
    story.append(Spacer(1, 4*mm))

    # Contact boxes
    half = (CONTENT_W - 6*mm) / 2
    contact_table = Table([[
        [
            Paragraph("Destiny Preservation Funds",           S["contact_heading"]),
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
