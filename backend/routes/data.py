"""
Data API routes — six endpoints serving aggregated WideOrbit analytics.

All revenue calculations filter on status in ('aired', 'makegood').
CY = 2025, PY = 2024.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from services.data_loader import DataLoader, DAYPART_NAMES, DAYPART_ORDER

router = APIRouter(prefix="/api/data", tags=["data"])

_loader: DataLoader | None = None


def init_loader(loader: DataLoader) -> None:
    """Called once from main.py to inject the shared DataLoader."""
    global _loader
    _loader = loader


def _get_loader() -> DataLoader:
    assert _loader is not None, "DataLoader not initialized — call init_loader() first"
    return _loader


# ── helpers ──────────────────────────────────────────────────────────────────

CY_YEAR = 2025
PY_YEAR = 2024
REVENUE_STATUSES = ["aired", "makegood"]


# ── GET /stations ────────────────────────────────────────────────────────────

@router.get("/stations")
async def get_stations():
    loader = _get_loader()
    return {"stations": loader.get_stations()}


# ── GET /revenue-by-daypart ──────────────────────────────────────────────────

@router.get("/revenue-by-daypart")
async def revenue_by_daypart(station: str | None = Query(default=None)):
    loader = _get_loader()
    spots = loader.spots

    rev = spots[spots["status"].isin(REVENUE_STATUSES)].copy()
    if station:
        rev = rev[rev["station"] == station]

    rev["year"] = rev["air_date"].dt.year
    cy = rev[rev["year"] == CY_YEAR]
    py = rev[rev["year"] == PY_YEAR]

    cy_by_dp = cy.groupby("daypart")["rate"].sum()
    py_by_dp = py.groupby("daypart")["rate"].sum()

    total_cy = float(cy["rate"].sum())
    total_py = float(py["rate"].sum())

    dayparts = []
    for dp in DAYPART_ORDER:
        cy_r = float(cy_by_dp.get(dp, 0))
        py_r = float(py_by_dp.get(dp, 0))
        yoy = ((cy_r - py_r) / py_r * 100) if py_r > 0 else 0.0
        share = (cy_r / total_cy * 100) if total_cy > 0 else 0.0
        dayparts.append({
            "daypart": dp,
            "daypart_name": DAYPART_NAMES[dp],
            "cy_revenue": round(cy_r, 2),
            "py_revenue": round(py_r, 2),
            "yoy_pct": round(yoy, 1),
            "share_pct": round(share, 1),
        })

    total_yoy = ((total_cy - total_py) / total_py * 100) if total_py > 0 else 0.0

    return {
        "dayparts": dayparts,
        "total_cy": round(total_cy, 2),
        "total_py": round(total_py, 2),
        "total_yoy_pct": round(total_yoy, 1),
    }


# ── GET /aur-trends ─────────────────────────────────────────────────────────

@router.get("/aur-trends")
async def aur_trends(
    station: str | None = Query(default=None),
    granularity: str = Query(default="monthly"),
):
    loader = _get_loader()
    spots = loader.spots

    rev = spots[spots["status"].isin(REVENUE_STATUSES)].copy()
    if station:
        rev = rev[rev["station"] == station]

    if granularity == "quarterly":
        rev["period"] = rev["air_date"].dt.to_period("Q").astype(str)
    else:
        rev["period"] = rev["air_date"].dt.to_period("M").astype(str)

    grouped = rev.groupby(["period", "daypart"])["rate"].mean()
    periods = sorted(rev["period"].unique().tolist())

    series: dict[str, list[float | None]] = {}
    for dp in DAYPART_ORDER:
        values: list[float | None] = []
        for p in periods:
            try:
                values.append(round(float(grouped.loc[(p, dp)]), 2))
            except KeyError:
                values.append(None)
        series[dp] = values

    return {"periods": periods, "series": series}


# ── GET /top-advertisers ─────────────────────────────────────────────────────

@router.get("/top-advertisers")
async def top_advertisers(
    station: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
):
    loader = _get_loader()
    spots = loader.spots
    orders = loader.orders

    rev = spots[spots["status"].isin(REVENUE_STATUSES)].copy()
    if station:
        rev = rev[rev["station"] == station]

    merged = rev.merge(
        orders[["order_id", "advertiser_name"]],
        on="order_id",
        how="left",
    )

    by_adv = merged.groupby("advertiser_name")["rate"].sum().sort_values(ascending=False)
    total_rev = float(by_adv.sum())

    top = by_adv.head(limit)
    advertisers = []
    for name, revenue in top.items():
        share = (float(revenue) / total_rev * 100) if total_rev > 0 else 0.0
        advertisers.append({
            "name": str(name),
            "revenue": round(float(revenue), 2),
            "share_pct": round(share, 1),
            "concentration_flag": share > 15,
        })

    # HHI = sum of squared market shares (as percentages)
    all_shares = (by_adv / total_rev * 100) if total_rev > 0 else by_adv * 0
    hhi = float((all_shares ** 2).sum())

    top5_share = (
        round(float(by_adv.head(5).sum()) / total_rev * 100, 1)
        if total_rev > 0 else 0.0
    )

    return {
        "advertisers": advertisers,
        "hhi": round(hhi),
        "top5_share": top5_share,
    }


# ── GET /sellout-rates ───────────────────────────────────────────────────────

@router.get("/sellout-rates")
async def sellout_rates(station: str | None = Query(default=None)):
    loader = _get_loader()
    inv = loader.inventory.copy()
    if station:
        inv = inv[inv["station"] == station]

    inv["year"] = inv["date"].dt.year
    cy = inv[inv["year"] == CY_YEAR]
    py = inv[inv["year"] == PY_YEAR]

    cy_by_dp = cy.groupby("daypart").agg(booked=("booked", "sum"), avails=("total_avails", "sum"))
    py_by_dp = py.groupby("daypart").agg(booked=("booked", "sum"), avails=("total_avails", "sum"))

    dayparts = []
    for dp in DAYPART_ORDER:
        cy_avails = float(cy_by_dp.loc[dp, "avails"]) if dp in cy_by_dp.index else 0
        cy_booked = float(cy_by_dp.loc[dp, "booked"]) if dp in cy_by_dp.index else 0
        py_avails = float(py_by_dp.loc[dp, "avails"]) if dp in py_by_dp.index else 0
        py_booked = float(py_by_dp.loc[dp, "booked"]) if dp in py_by_dp.index else 0

        cy_rate = (cy_booked / cy_avails * 100) if cy_avails > 0 else 0.0
        py_rate = (py_booked / py_avails * 100) if py_avails > 0 else 0.0

        dayparts.append({
            "daypart": dp,
            "daypart_name": DAYPART_NAMES[dp],
            "cy_rate": round(cy_rate, 1),
            "py_rate": round(py_rate, 1),
            "pricing_flag": cy_rate > 85,
        })

    return {"dayparts": dayparts}


# ── GET /makegood-summary ────────────────────────────────────────────────────

@router.get("/makegood-summary")
async def makegood_summary(station: str | None = Query(default=None)):
    loader = _get_loader()
    spots = loader.spots.copy()
    if station:
        spots = spots[spots["station"] == station]

    countable = ["aired", "makegood", "preempted"]

    # ── by station ───────────────────────────────────────────────────────
    station_rows = []
    for st in sorted(spots["station"].unique()):
        st_spots = spots[spots["station"] == st]
        relevant = st_spots[st_spots["status"].isin(countable)]
        total = len(relevant)
        preempted = int((relevant["status"] == "preempted").sum())
        makegood = int((relevant["status"] == "makegood").sum())

        preemption_rate = (preempted / total * 100) if total > 0 else 0.0
        makegood_rate = (makegood / total * 100) if total > 0 else 0.0
        combined_rate = preemption_rate + makegood_rate

        revenue_impact = float(
            st_spots[st_spots["status"] == "preempted"]["rate"].sum()
        )

        station_rows.append({
            "station": st,
            "preempted": preempted,
            "makegood": makegood,
            "total_spots": total,
            "preemption_rate": round(preemption_rate, 1),
            "makegood_rate": round(makegood_rate, 1),
            "combined_rate": round(combined_rate, 1),
            "revenue_impact": round(revenue_impact, 2),
            "flag": combined_rate > 5,
        })

    # ── by daypart ───────────────────────────────────────────────────────
    daypart_rows = []
    for dp in DAYPART_ORDER:
        dp_spots = spots[spots["daypart"] == dp]
        relevant = dp_spots[dp_spots["status"].isin(countable)]
        total = len(relevant)
        preempted = int((relevant["status"] == "preempted").sum())
        makegood = int((relevant["status"] == "makegood").sum())

        combined_rate = ((preempted + makegood) / total * 100) if total > 0 else 0.0
        revenue_impact = float(
            dp_spots[dp_spots["status"] == "preempted"]["rate"].sum()
        )

        daypart_rows.append({
            "daypart": dp,
            "daypart_name": DAYPART_NAMES[dp],
            "preempted": preempted,
            "makegood": makegood,
            "total_spots": total,
            "combined_rate": round(combined_rate, 1),
            "revenue_impact": round(revenue_impact, 2),
            "flag": combined_rate > 5,
        })

    return {"stations": station_rows, "by_daypart": daypart_rows}
