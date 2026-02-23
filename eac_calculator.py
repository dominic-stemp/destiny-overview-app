# ----------------------------------------------------
# EAC CALCULATOR — Destiny Overview App
# ----------------------------------------------------
# Computes Effective Annual Cost table components per
# ASISA disclosure standard.
#
# Fixed charges (TIC, Advice, Admin base, Other flat)
# remain simplified flat % method.
#
# RIY (Reduction in Yield) simulation is used for:
#   - R35 monthly policy fee  → added into Other row
#   - Upfront initial charge  → added into Admin row
#     (RIY method only when monthly_contribution > 0;
#      straight-line used for lump-sum-only)
# ----------------------------------------------------

import math

# ----------------------------------------------------
# TIC MAP (% per annum, VAT-exclusive / as-given)
# ----------------------------------------------------
TIC_MAP: dict[str, float] = {
    "Destiny Market Enhanced Portfolio":          0.89,
    "Destiny Moderate Portfolio":                 0.83,
    "Destiny Conservative Portfolio":             0.74,
    "Destiny Defensive Portfolio":                0.63,
    "Destiny Global Enhanced Portfolio":          0.76,
    "Destiny Sharia Portfolio":                   0.80,
    "Destiny Money Market Portfolio":             0.23,
    "Destiny Passive Market Enhanced Portfolio":  0.28,
    "Destiny Passive Moderate Portfolio":         0.26,
    "Destiny Passive Conservative Portfolio":     0.25,
    "Destiny Passive Defensive Portfolio":        0.23,
}

# R35 fixed monthly policy fee (Rand)
R35_MONTHLY_FEE = 35.0

# Growth assumption for all RIY simulations
GROWTH_RATE_PA = 0.06  # 6% effective per annum


# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def _fmt(rate_pct: float | None, decimals: int = 2) -> str:
    """Format a rate already in % (e.g. 1.23) as '1.23%', or 'N/A'."""
    if rate_pct is None:
        return "N/A"
    return f"{round(rate_pct + 1e-12, decimals):.{decimals}f}%"


def _weighted_tic(allocations: list[tuple[str, float]],
                  tic_map: dict[str, float]) -> float:
    """
    Weighted average TIC (%) from (portfolio_name, weight) pairs.
    Weights are normalised so they need not sum to 100.
    Returns TIC as a percentage (e.g. 0.83, not 0.0083).
    """
    total_weight = sum(w for _, w in allocations)
    if total_weight <= 0:
        return 0.0
    return sum(
        (w / total_weight) * tic_map.get(name, 0.0)
        for name, w in allocations
    )


# ----------------------------------------------------
# CORE SIMULATION ENGINE
# ----------------------------------------------------
def _simulate(
    n_months: int,
    initial_value: float,
    monthly_contribution: float,
    annual_flat_charge_pct: float,
    include_r35: bool,
    growth_pa: float = GROWTH_RATE_PA,
) -> float:
    """
    Month-by-month portfolio simulation.

    Each month (in order):
      1. Apply growth
      2. Add monthly contribution
      3. Deduct proportional flat annual charges (compound monthly equivalent)
      4. Deduct R35 (only if include_r35 and monthly_contribution > 0)

    Parameters
    ----------
    initial_value          : starting portfolio value (may differ from lump_sum
                             if upfront fee is already deducted from it)
    annual_flat_charge_pct : combined flat % p.a. (TIC + advice + admin_base + other_flat)
    growth_pa              : annual growth rate (decimal); default 6%

    Returns final portfolio value (floored at 0).
    """
    monthly_growth = (1 + growth_pa) ** (1 / 12) - 1
    monthly_charge = (1 + annual_flat_charge_pct / 100.0) ** (1 / 12) - 1

    value = initial_value
    for _ in range(n_months):
        value *= (1 + monthly_growth)
        value += monthly_contribution
        value -= value * monthly_charge
        if include_r35 and monthly_contribution > 0:
            value -= R35_MONTHLY_FEE

    return max(value, 0.0)


def _binary_search_rate(
    target: float,
    n_months: int,
    initial_value: float,
    monthly_contribution: float,
    annual_flat_charge_pct: float,
) -> float:
    """
    Binary-search for the effective annual growth rate r (in decimal) such
    that _simulate(..., growth_pa=r, include_r35=False) == target.

    Searches within [0, GROWTH_RATE_PA].
    Returns the solved r (decimal).
    """
    def _val_at(growth_pa: float) -> float:
        return _simulate(
            n_months=n_months,
            initial_value=initial_value,
            monthly_contribution=monthly_contribution,
            annual_flat_charge_pct=annual_flat_charge_pct,
            include_r35=False,
            growth_pa=growth_pa,
        )

    lo, hi = 0.0, GROWTH_RATE_PA
    for _ in range(60):   # 60 iterations → ~1e-15 precision
        mid = (lo + hi) / 2
        if _val_at(mid) > target:
            hi = mid
        else:
            lo = mid

    return (lo + hi) / 2


# ----------------------------------------------------
# R35 RIY
# ----------------------------------------------------
def _compute_r35_riy(
    n_years: int,
    lump_sum: float,
    monthly_contribution: float,
    annual_flat_charge_pct: float,
) -> float:
    """
    RIY impact of the R35 monthly fee over n_years.
    Returns 0.0 if no monthly contribution.
    Returns result as a percentage (e.g. 0.25 means 0.25%).
    """
    if monthly_contribution <= 0:
        return 0.0

    n_months = n_years * 12

    final_with    = _simulate(n_months, lump_sum, monthly_contribution,
                              annual_flat_charge_pct, include_r35=True)
    final_without = _simulate(n_months, lump_sum, monthly_contribution,
                              annual_flat_charge_pct, include_r35=False)

    if final_without <= 0 or final_with >= final_without:
        return 0.0

    # Solve for r such that without-R35 simulation at rate r = final_with
    r_eff = _binary_search_rate(
        target=final_with,
        n_months=n_months,
        initial_value=lump_sum,
        monthly_contribution=monthly_contribution,
        annual_flat_charge_pct=annual_flat_charge_pct,
    )
    riy = GROWTH_RATE_PA - r_eff
    return round(max(riy * 100, 0.0), 4)


# ----------------------------------------------------
# UPFRONT CHARGE RIY
# ----------------------------------------------------
def _compute_upfront_riy(
    n_years: int,
    lump_sum: float,
    upfront_fee_incl_vat: float,
    monthly_contribution: float,
    annual_flat_charge_pct: float,
) -> float:
    """
    RIY impact of the initial upfront % charge over n_years.
    Used only when monthly_contribution > 0 (ASISA requirement).

    Step 1: Simulate WITH upfront deducted from starting value.
            initial_value = lump_sum - upfront_fee_incl_vat
    Step 2: Simulate WITHOUT upfront (full lump_sum invested).
    Step 3: Binary-search for r such that without-upfront sim at rate r
            equals final_with_upfront.
    RIY_upfront = 0.06 - r

    Returns result as a percentage (e.g. 1.50 means 1.50%).
    Returns 0.0 if upfront_fee_incl_vat <= 0.
    """
    if upfront_fee_incl_vat <= 0:
        return 0.0

    n_months = n_years * 12
    net_initial = lump_sum - upfront_fee_incl_vat

    # Step 1 — with upfront already deducted from starting capital
    final_with_upfront = _simulate(
        n_months=n_months,
        initial_value=max(net_initial, 0.0),
        monthly_contribution=monthly_contribution,
        annual_flat_charge_pct=annual_flat_charge_pct,
        include_r35=(monthly_contribution > 0),
    )

    # Step 2 — without upfront (full lump sum)
    final_without_upfront = _simulate(
        n_months=n_months,
        initial_value=lump_sum,
        monthly_contribution=monthly_contribution,
        annual_flat_charge_pct=annual_flat_charge_pct,
        include_r35=(monthly_contribution > 0),
    )

    if final_without_upfront <= 0 or final_with_upfront >= final_without_upfront:
        return 0.0

    # Step 3 — binary-search for r on the without-upfront simulation
    r_eff = _binary_search_rate(
        target=final_with_upfront,
        n_months=n_months,
        initial_value=lump_sum,
        monthly_contribution=monthly_contribution,
        annual_flat_charge_pct=annual_flat_charge_pct,
    )
    riy = GROWTH_RATE_PA - r_eff
    return round(max(riy * 100, 0.0), 4)


# ----------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------
def compute_eac_table(
    fund_type: str,                              # "RA" or "Preservation"
    age: float,                                  # investor age (float from DOB calc)
    investment_option: str,                      # "Lifestage" | "Passive Lifestage" | "Choice"
    selected_portfolio: str | None,              # for Lifestage / Passive Lifestage
    choice_allocations: list[tuple[str, float]] | None,  # [(name, weight_pct_0_to_100), ...]
    ifa_fee_ex_vat: float,                       # e.g. 0.75 (percent, NOT decimal)
    vat_rate: float = 15.0,                      # e.g. 15.0 (percent, NOT decimal)
    admin_base_ex_vat: float = 0.75,             # percent p.a. (0.75%)
    tic_map: dict[str, float] | None = None,
    include_upfront_in_eac: bool = True,
    upfront_fee_incl_vat: float = 0.0,
    lump_sum: float = 0.0,
    monthly_contribution: float = 0.0,           # R per month; 0 → lump-sum-only rules
) -> dict:
    """
    Returns:
    {
      "columns": ["Next 1 year", "Next 3 years", ...],
      "rows": [
        {"name": "Investment Management", "values": [...], "is_total": False},
        ...
        {"name": "Effective Annual Cost", "values": [...], "is_total": True},
      ],
      "_raw": {imc, advice, admin, other, total},  # float or None per column
      "_r35_riy":     [...],   # R35 RIY per column (debug)
      "_upfront_riy": [...],   # upfront RIY per column (debug; None = straight-line used)
    }
    """

    if tic_map is None:
        tic_map = TIC_MAP

    vat_mult = 1 + vat_rate / 100.0

    # --------------------------------------------------
    # 1. IMC
    # --------------------------------------------------
    if investment_option == "Choice" and choice_allocations:
        imc_pct = _weighted_tic(choice_allocations, tic_map)
    else:
        imc_pct = tic_map.get(selected_portfolio or "", 0.0)

    # --------------------------------------------------
    # 2. Advice (incl. VAT)
    # --------------------------------------------------
    advice_pct = ifa_fee_ex_vat * vat_mult

    # --------------------------------------------------
    # 3. Admin base + Other flat (0.75% ex VAT, 60/40)
    # --------------------------------------------------
    admin_total_inc_vat = admin_base_ex_vat * vat_mult
    admin_base_pct = admin_total_inc_vat * 0.60
    other_flat_pct  = admin_total_inc_vat * 0.40

    # --------------------------------------------------
    # 4. Upfront charge as % of lump sum
    # --------------------------------------------------
    upfront_charge_pct = 0.0
    if include_upfront_in_eac and lump_sum > 0 and upfront_fee_incl_vat > 0:
        upfront_charge_pct = (upfront_fee_incl_vat / lump_sum) * 100.0

    use_riy_for_upfront = (monthly_contribution > 0) and (upfront_charge_pct > 0)

    # --------------------------------------------------
    # 5. Disclosure periods
    # --------------------------------------------------
    if fund_type == "RA":
        numeric_periods = [("Next 1 year", 1), ("Next 3 years", 3),
                           ("Next 5 years", 5), ("Next 10 years", 10)]
    else:
        numeric_periods = [("Next 1 year", 1), ("Next 3 years", 3),
                           ("Next 5 years", 5)]

    years_to_55     = 55.0 - age
    age55_applicable = years_to_55 > 0
    n55             = max(1, math.ceil(years_to_55)) if age55_applicable else None
    all_columns     = [label for label, _ in numeric_periods] + ["Age 55"]

    # --------------------------------------------------
    # 6. Combined flat % used inside simulations
    #    (all components that are NOT RIY-treated)
    # --------------------------------------------------
    combined_flat_pct = imc_pct + advice_pct + admin_base_pct + other_flat_pct

    # --------------------------------------------------
    # 7. RIY calculations — one value per disclosure period
    # --------------------------------------------------
    all_periods_n = [n for _, n in numeric_periods] + ([n55] if age55_applicable else [None])

    r35_riy_vals:     list[float | None] = []
    upfront_riy_vals: list[float | None] = []

    for n in all_periods_n:
        if n is None:
            r35_riy_vals.append(None)
            upfront_riy_vals.append(None)
            continue

        r35_riy_vals.append(
            _compute_r35_riy(
                n_years=n,
                lump_sum=lump_sum,
                monthly_contribution=monthly_contribution,
                annual_flat_charge_pct=combined_flat_pct,
            )
        )

        if use_riy_for_upfront:
            upfront_riy_vals.append(
                _compute_upfront_riy(
                    n_years=n,
                    lump_sum=lump_sum,
                    upfront_fee_incl_vat=upfront_fee_incl_vat,
                    monthly_contribution=monthly_contribution,
                    annual_flat_charge_pct=combined_flat_pct,
                )
            )
        else:
            upfront_riy_vals.append(None)  # straight-line handled below

    # --------------------------------------------------
    # 8. Build per-column component values
    # --------------------------------------------------
    imc_vals:    list[float | None] = []
    advice_vals: list[float | None] = []
    admin_vals:  list[float | None] = []
    other_vals:  list[float | None] = []

    period_ns = [n for _, n in numeric_periods] + ([n55] if age55_applicable else [None])

    for i, n in enumerate(period_ns):
        if n is None:
            imc_vals.append(None)
            advice_vals.append(None)
            admin_vals.append(None)
            other_vals.append(None)
            continue

        imc_vals.append(round(imc_pct + 1e-12, 2))
        advice_vals.append(round(advice_pct + 1e-12, 2))

        # Admin = base + upfront treatment (RIY or straight-line)
        if use_riy_for_upfront:
            upfront_component = upfront_riy_vals[i] or 0.0
        else:
            # Lump-sum-only: straight-line amortisation
            upfront_component = (upfront_charge_pct / n) if (include_upfront_in_eac and upfront_charge_pct > 0) else 0.0

        admin_vals.append(round(admin_base_pct + upfront_component + 1e-12, 4))

        # Other = flat + R35 RIY
        r35_v = r35_riy_vals[i] or 0.0
        other_vals.append(round(other_flat_pct + r35_v + 1e-12, 4))

    # Total
    total_vals: list[float | None] = []
    for i in range(len(all_columns)):
        parts = [imc_vals[i], advice_vals[i], admin_vals[i], other_vals[i]]
        if any(p is None for p in parts):
            total_vals.append(None)
        else:
            total_vals.append(round(sum(parts) + 1e-12, 2))

    # --------------------------------------------------
    # 9. Format to strings
    # --------------------------------------------------
    def fmt_list(vals):
        return [_fmt(v) for v in vals]

    rows = [
        {"name": "Investment Management", "values": fmt_list(imc_vals),    "is_total": False},
        {"name": "Advice",                "values": fmt_list(advice_vals), "is_total": False},
        {"name": "Admin",                 "values": fmt_list(admin_vals),  "is_total": False},
        {"name": "Other",                 "values": fmt_list(other_vals),  "is_total": False},
        {"name": "Effective Annual Cost", "values": fmt_list(total_vals),  "is_total": True},
    ]

    return {
        "columns": all_columns,
        "rows": rows,
        "_raw": {
            "imc":    imc_vals,
            "advice": advice_vals,
            "admin":  admin_vals,
            "other":  other_vals,
            "total":  total_vals,
        },
        "_upfront_in_eac":   include_upfront_in_eac,
        "_r35_riy":          r35_riy_vals,
        "_upfront_riy":      upfront_riy_vals,   # None entries = straight-line was used
        "_use_riy_upfront":  use_riy_for_upfront,
    }


# ----------------------------------------------------
# CONVERT to PDF-generator row format
# ----------------------------------------------------
def eac_table_to_rows(eac: dict, fund_type: str) -> list[dict]:
    """
    Converts compute_eac_table output to the list-of-dicts format
    expected by the PDF generators:
      [{"label": ..., "y1": ..., "y3": ..., "y5": ..., "y10": ..., "y55": ..., "is_total": ...}, ...]
    Numeric columns contain floats (or None for N/A).
    """
    raw  = eac["_raw"]
    cols = eac["columns"]

    col_key_map = {
        "Next 1 year":   "y1",
        "Next 3 years":  "y3",
        "Next 5 years":  "y5",
        "Next 10 years": "y10",
        "Age 55":        "y55",
    }
    component_order = ["imc", "advice", "admin", "other", "total"]
    label_map = {
        "imc":    "Investment Management",
        "advice": "Advice",
        "admin":  "Admin",
        "other":  "Other",
        "total":  "Effective Annual Cost",
    }
    is_total_map = {"total": True}

    result = []
    for comp in component_order:
        row = {"label": label_map[comp], "is_total": is_total_map.get(comp, False)}
        for i, col_label in enumerate(cols):
            key = col_key_map.get(col_label)
            if key:
                row[key] = raw[comp][i]  # float or None
        result.append(row)

    return result
