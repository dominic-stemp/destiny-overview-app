# ----------------------------------------------------
# EAC CALCULATOR — Destiny Overview App
# ----------------------------------------------------
import math

# ----------------------------------------------------
# TIC MAP
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

GROWTH_RATE_PA = 0.06


# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def _fmt(rate_pct: float | None, decimals: int = 2) -> str:
    if rate_pct is None:
        return "N/A"
    return f"{round(rate_pct + 1e-12, decimals):.{decimals}f}%"


def _weighted_tic(allocations, tic_map):
    total_weight = sum(w for _, w in allocations)
    if total_weight <= 0:
        return 0.0
    return sum((w / total_weight) * tic_map.get(name, 0.0) for name, w in allocations)


# ----------------------------------------------------
# SIMULATION
# ----------------------------------------------------
def _simulate(n_months, initial_value, monthly_contribution, annual_flat_charge_pct, growth_pa=GROWTH_RATE_PA):
    monthly_growth = (1 + growth_pa) ** (1 / 12) - 1
    monthly_charge = (1 + annual_flat_charge_pct / 100.0) ** (1 / 12) - 1
    value = initial_value
    for _ in range(n_months):
        value *= (1 + monthly_growth)
        value += monthly_contribution
        value -= value * monthly_charge
    return max(value, 0.0)


def _binary_search_rate(target, n_months, initial_value, monthly_contribution, annual_flat_charge_pct):
    def _val_at(g):
        return _simulate(n_months, initial_value, monthly_contribution, annual_flat_charge_pct, g)
    lo, hi = 0.0, GROWTH_RATE_PA
    for _ in range(60):
        mid = (lo + hi) / 2
        if _val_at(mid) > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _compute_riy(n_years, lump_sum, fee_incl_vat, monthly_contribution, annual_flat_charge_pct):
    """RIY of a one-time fee (upfront or cancellation). Returns % (e.g. 1.50)."""
    if fee_incl_vat <= 0:
        return 0.0
    n_months = n_years * 12
    net_initial = max(lump_sum - fee_incl_vat, 0.0)
    final_with = _simulate(n_months, net_initial, monthly_contribution, annual_flat_charge_pct)
    final_without = _simulate(n_months, lump_sum, monthly_contribution, annual_flat_charge_pct)
    if final_without <= 0 or final_with >= final_without:
        return 0.0
    r_eff = _binary_search_rate(final_with, n_months, lump_sum, monthly_contribution, annual_flat_charge_pct)
    return round(max((GROWTH_RATE_PA - r_eff) * 100, 0.0), 4)


# ----------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------
def compute_eac_table(
    fund_type: str,
    age: float,
    investment_option: str,
    selected_portfolio: str | None,
    choice_allocations: list | None,
    ifa_fee_ex_vat: float,
    vat_rate: float = 15.0,
    admin_base_ex_vat: float = 0.75,
    tic_map: dict | None = None,
    include_upfront_in_eac: bool = False,
    upfront_fee_incl_vat: float = 0.0,        # Option 1: goes into Admin row
    cancellation_fee_incl_vat: float = 0.0,   # Option 2: goes into Other row
    lump_sum: float = 0.0,
    monthly_contribution: float = 0.0,
) -> dict:
    if tic_map is None:
        tic_map = TIC_MAP

    vat_mult = 1 + vat_rate / 100.0

    # 1. IMC
    if investment_option == "Own Choice" and choice_allocations:
        imc_pct = _weighted_tic(choice_allocations, tic_map)
    else:
        imc_pct = tic_map.get(selected_portfolio or "", 0.0)

    # 2. Advice (incl VAT) — flat ongoing fee only
    advice_pct = ifa_fee_ex_vat * vat_mult

    # 3. Admin = 0.75% ex VAT, incl VAT (full amount, no split)
    admin_pct = admin_base_ex_vat * vat_mult  # e.g. 0.75 * 1.15 = 0.8625%

    # 4. Upfront charge % of lump sum (for admin row RIY)
    upfront_charge_pct = 0.0
    if include_upfront_in_eac and lump_sum > 0 and upfront_fee_incl_vat > 0:
        upfront_charge_pct = (upfront_fee_incl_vat / lump_sum) * 100.0

    use_riy_upfront = (monthly_contribution > 0) and (upfront_charge_pct > 0)

    # 5. Cancellation fee for Other row
    use_riy_cancel = (monthly_contribution > 0) and (cancellation_fee_incl_vat > 0)
    cancel_straight_pct = 0.0
    if lump_sum > 0 and cancellation_fee_incl_vat > 0:
        cancel_straight_pct = (cancellation_fee_incl_vat / lump_sum) * 100.0

    # 6. Disclosure periods
    if fund_type == "RA":
        numeric_periods = [("1 year", 1), ("3 years", 3), ("5 years", 5)]
    else:
        # Preservation: split 5yr into "< 5 years" (fee applies) and "5 years" (fee waived)
        numeric_periods = [("1 year", 1), ("3 years", 3), ("< 5 years", 5), ("5 years", 5)]

    all_columns = [label for label, _ in numeric_periods]

    # 7. Combined flat % for simulations
    combined_flat_pct = imc_pct + advice_pct + admin_pct

    # 8. Build per-column values
    imc_vals, advice_vals, admin_vals, other_vals = [], [], [], []

    for label, n in numeric_periods:
        if n is None:
            imc_vals.append(None); advice_vals.append(None)
            admin_vals.append(None); other_vals.append(None)
            continue

        imc_vals.append(round(imc_pct + 1e-12, 2))

        # Advice = base + upfront RIY (upfront fee goes into advice row)
        if use_riy_upfront:
            upfront_riy = _compute_riy(n, lump_sum, upfront_fee_incl_vat, monthly_contribution, combined_flat_pct)
            advice_vals.append(round(advice_pct + upfront_riy + 1e-12, 4))
        else:
            upfront_comp = (upfront_charge_pct / n) if (include_upfront_in_eac and upfront_charge_pct > 0) else 0.0
            advice_vals.append(round(advice_pct + upfront_comp + 1e-12, 4))

        # Admin = base only
        admin_vals.append(round(admin_pct + 1e-12, 4))

        # Other = cancellation fee, but only if cancellation still applies at this period.
        # "< 5 years" column: fee applies (day before waiver). "5 years" column: fee waived.
        # Also waived once investor reaches age 55 or period >= 5 years.
        if label == "< 5 years":
            # Day-before-5-year: cancellation still applies unless age 55 already reached
            cancel_applies = (age + n < 55)
        else:
            cancel_applies = (n < 5) and (age + n < 55)

        if not cancel_applies:
            other_vals.append(0.0)
        elif use_riy_cancel:
            cancel_riy = _compute_riy(n, lump_sum, cancellation_fee_incl_vat, monthly_contribution, combined_flat_pct)
            other_vals.append(round(cancel_riy + 1e-12, 4))
        elif cancel_straight_pct > 0:
            other_vals.append(round((cancel_straight_pct / n) + 1e-12, 4))
        else:
            other_vals.append(0.0)

    # Total
    total_vals = []
    for i in range(len(all_columns)):
        parts = [imc_vals[i], advice_vals[i], admin_vals[i], other_vals[i]]
        if any(p is None for p in parts):
            total_vals.append(None)
        else:
            total_vals.append(round(sum(parts) + 1e-12, 2))

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
            "imc": imc_vals, "advice": advice_vals,
            "admin": admin_vals, "other": other_vals, "total": total_vals,
        },
        "_upfront_in_eac": include_upfront_in_eac,
    }


# ----------------------------------------------------
# CONVERT to PDF row format
# ----------------------------------------------------
def eac_table_to_rows(eac: dict, fund_type: str) -> list[dict]:
    raw  = eac["_raw"]
    cols = eac["columns"]
    col_key_map = {
        "Next 1 year": "y1", "Next 3 years": "y3", "Next 5 years": "y5",
        "Next 10 years": "y10", "Age 55": "y55", "10 years": "y10",
        "1 year": "y1", "3 years": "y3", "5 years": "y5",
        "< 5 years": "y5pre",
    }
    component_order = ["imc", "advice", "admin", "other", "total"]
    label_map = {
        "imc": "Investment Management", "advice": "Advice", "admin": "Admin",
        "other": "Other", "total": "Effective Annual Cost",
    }
    result = []
    for comp in component_order:
        row = {"label": label_map[comp], "is_total": comp == "total"}
        for i, col_label in enumerate(cols):
            key = col_key_map.get(col_label)
            if key:
                row[key] = raw[comp][i]
        result.append(row)
    return result
