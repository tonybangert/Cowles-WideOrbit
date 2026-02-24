"""
WideOrbit WO Traffic — Sample Data Generator

Generates realistic sample data for a 5-station broadcast group:
  - orders.csv   (~500-600 ad buy contracts)
  - spots.csv    (~20,000 individual commercial placements)
  - inventory.csv (~18,200 available ad slots)

Usage:
    python data/sample/generate_sample_data.py
    python data/sample/generate_sample_data.py --output-dir data/sample --seed 42
"""

import argparse
import logging
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("sample_data_gen")


# ── Station Configuration ────────────────────────────────────────────────────

STATIONS = {
    "KHQ-TV":  {"market": "Spokane",  "dma_rank": 72,  "size": 0.35},
    "KULR-TV": {"market": "Billings", "dma_rank": 170, "size": 0.22},
    "KTMF-TV": {"market": "Missoula", "dma_rank": 166, "size": 0.18},
    "KNDO-TV": {"market": "Yakima",   "dma_rank": 125, "size": 0.15},
    "KWYB-TV": {"market": "Butte",    "dma_rank": 190, "size": 0.10},
}

# ── Daypart Configuration ────────────────────────────────────────────────────
# Matches wo_fields.yaml daypart_mapping exactly

DAYPARTS = {
    "EM": {"name": "Early Morning",  "start": time(6, 0),   "end": time(9, 0),    "revenue_share": 0.065, "base_aur_mult": 0.30},
    "DT": {"name": "Daytime",        "start": time(9, 0),   "end": time(16, 0),   "revenue_share": 0.09,  "base_aur_mult": 0.25},
    "EF": {"name": "Early Fringe",   "start": time(16, 0),  "end": time(17, 0),   "revenue_share": 0.04,  "base_aur_mult": 0.35},
    "EN": {"name": "Early News",     "start": time(17, 0),  "end": time(18, 30),  "revenue_share": 0.175, "base_aur_mult": 0.65},
    "PA": {"name": "Prime Access",   "start": time(18, 30), "end": time(20, 0),   "revenue_share": 0.135, "base_aur_mult": 0.55},
    "PR": {"name": "Prime",          "start": time(20, 0),  "end": time(23, 0),   "revenue_share": 0.375, "base_aur_mult": 1.00},
    "LN": {"name": "Late News",      "start": time(23, 0),  "end": time(23, 35),  "revenue_share": 0.09,  "base_aur_mult": 0.50},
    "LF": {"name": "Late Fringe",    "start": time(23, 35), "end": time(2, 0),    "revenue_share": 0.03,  "base_aur_mult": 0.15},
}

# Precompute volume weights: count_weight = revenue_share / aur_mult, then normalize.
# This ensures that count × rate yields the target revenue shares.
_raw_vol = {dp: cfg["revenue_share"] / cfg["base_aur_mult"] for dp, cfg in DAYPARTS.items()}
_vol_total = sum(_raw_vol.values())
DAYPART_VOLUME_WEIGHTS = {dp: v / _vol_total for dp, v in _raw_vol.items()}

# Sell-out rate targets by daypart (fraction of avails booked)
SELLOUT_TARGETS = {
    "EM": 0.60, "DT": 0.55, "EF": 0.58, "EN": 0.75,
    "PA": 0.72, "PR": 0.84, "LN": 0.70, "LF": 0.45,
}

# YoY growth by daypart (2025 vs 2024)
YOY_GROWTH = {
    "EM": 0.04, "DT": 0.03, "EF": 0.04, "EN": 0.06,
    "PA": 0.06, "PR": 0.08, "LN": 0.05, "LF": 0.03,
}

# ── Prime AUR Ranges by Station ──────────────────────────────────────────────

PRIME_AUR_RANGES = {
    "KHQ-TV":  (400, 1200),
    "KULR-TV": (300, 900),
    "KTMF-TV": (250, 800),
    "KNDO-TV": (200, 700),
    "KWYB-TV": (150, 500),
}

# ── Time Range ────────────────────────────────────────────────────────────────

DATE_START = date(2024, 1, 1)
DATE_END = date(2025, 3, 31)
# "Today" cutoff for determining scheduled vs aired status
TODAY_CUTOFF = date(2025, 2, 15)

# ── Spot Length Distribution ──────────────────────────────────────────────────

SPOT_LENGTHS = [30, 15, 60]
SPOT_LENGTH_WEIGHTS = [0.70, 0.20, 0.10]
SPOT_LENGTH_RATE_MULT = {15: 0.60, 30: 1.00, 60: 1.80}

# ── Seasonal Multipliers ─────────────────────────────────────────────────────

def seasonal_rate_multiplier(d: date) -> float:
    """Q4 +15%, Q1 -10%, Q2/Q3 baseline."""
    month = d.month
    if month in (10, 11, 12):
        return 1.15
    elif month in (1, 2, 3):
        return 0.90
    elif month in (7, 8):
        return 0.95
    return 1.00


def seasonal_volume_multiplier(d: date) -> float:
    """Q4 +20% volume, Q1 -15% volume."""
    month = d.month
    if month in (10, 11, 12):
        return 1.20
    elif month in (1, 2, 3):
        return 0.85
    elif month in (7, 8):
        return 0.90
    return 1.00


# ── Advertiser Configuration ─────────────────────────────────────────────────

def generate_advertisers(rng: np.random.Generator) -> List[Dict]:
    """Create 50 advertisers: mix of national brands and local businesses."""
    national = [
        {"name": "Pacific Auto Group", "type": "national", "weight": 10.0},
        {"name": "Columbia Health Systems", "type": "national", "weight": 7.0},
        {"name": "Cascade Insurance", "type": "national", "weight": 6.5},
        {"name": "Northwest Wireless", "type": "national", "weight": 6.0},
        {"name": "Evergreen Financial", "type": "national", "weight": 5.5},
        {"name": "Summit Home Improvement", "type": "national", "weight": 5.0},
        {"name": "Olympic Furniture", "type": "national", "weight": 4.5},
        {"name": "Rainier Automotive", "type": "national", "weight": 4.0},
        {"name": "Puget Sound Energy", "type": "national", "weight": 3.5},
        {"name": "Glacier Pharmaceuticals", "type": "national", "weight": 3.0},
        {"name": "Timberline Foods", "type": "national", "weight": 2.8},
        {"name": "Horizon Telecom", "type": "national", "weight": 2.5},
        {"name": "Baker Mountain Sports", "type": "national", "weight": 2.2},
        {"name": "Clearwater Legal Group", "type": "national", "weight": 2.0},
        {"name": "Alpine Dental Network", "type": "national", "weight": 1.8},
    ]
    local = [
        {"name": "Mike's Plumbing & HVAC", "type": "local", "weight": 1.5},
        {"name": "Valley Ford", "type": "local", "weight": 1.5},
        {"name": "Cascade Eye Clinic", "type": "local", "weight": 1.3},
        {"name": "Spokane Spine Center", "type": "local", "weight": 1.2},
        {"name": "Heritage Roofing", "type": "local", "weight": 1.1},
        {"name": "Lakeside Chevrolet", "type": "local", "weight": 1.0},
        {"name": "Pioneer Title & Escrow", "type": "local", "weight": 1.0},
        {"name": "Mountain West Credit Union", "type": "local", "weight": 0.9},
        {"name": "Cedar Park Veterinary", "type": "local", "weight": 0.9},
        {"name": "Inland Empire Paving", "type": "local", "weight": 0.8},
        {"name": "Riverfront Dental", "type": "local", "weight": 0.8},
        {"name": "Northwest Garage Doors", "type": "local", "weight": 0.7},
        {"name": "Cascade Heating & Air", "type": "local", "weight": 0.7},
        {"name": "Valley Medical Center", "type": "local", "weight": 0.6},
        {"name": "Hilltop Family Law", "type": "local", "weight": 0.6},
        {"name": "Grandview Tire & Auto", "type": "local", "weight": 0.5},
        {"name": "Sunset Realty Group", "type": "local", "weight": 0.5},
        {"name": "Columbia Basin Ag Supply", "type": "local", "weight": 0.5},
        {"name": "Maple Street Jewelers", "type": "local", "weight": 0.4},
        {"name": "Yakima Valley Winery", "type": "local", "weight": 0.4},
        {"name": "Sunnyside RV & Marine", "type": "local", "weight": 0.4},
        {"name": "Peak Performance Fitness", "type": "local", "weight": 0.3},
        {"name": "Wenatchee Appliance", "type": "local", "weight": 0.3},
        {"name": "Tri-Cities Honda", "type": "local", "weight": 0.3},
        {"name": "Blue Sky Landscaping", "type": "local", "weight": 0.3},
        {"name": "River Park Square Mall", "type": "local", "weight": 0.3},
        {"name": "Palouse Country Realty", "type": "local", "weight": 0.2},
        {"name": "Desert Sun Tanning", "type": "local", "weight": 0.2},
        {"name": "Walla Walla Steakhouse", "type": "local", "weight": 0.2},
        {"name": "Cascade Bail Bonds", "type": "local", "weight": 0.2},
        {"name": "Kennewick Mattress Outlet", "type": "local", "weight": 0.2},
        {"name": "Coeur d'Alene Resort", "type": "local", "weight": 0.2},
        {"name": "Ellensburg Feed & Seed", "type": "local", "weight": 0.15},
        {"name": "Moses Lake Storage", "type": "local", "weight": 0.15},
        {"name": "Pullman Pizza Palace", "type": "local", "weight": 0.10},
    ]
    advertisers = national + local
    total_w = sum(a["weight"] for a in advertisers)
    for a in advertisers:
        a["share"] = a["weight"] / total_w
    return advertisers


def generate_agencies() -> Dict[str, Optional[str]]:
    """Map advertisers to agencies. ~70% through agencies, 30% direct."""
    agencies = [
        "Copacino Fujikado",
        "PB& Seattle",
        "DNA Agency",
        "Spokane Media Group",
        "Inland Media Buyers",
        "Cascade Media Partners",
        "Northwest Ad Works",
        "Pacific Rim Media",
    ]
    return agencies


def generate_programs() -> Dict[str, List[str]]:
    """Realistic program names per daypart."""
    return {
        "EM": ["Morning Report", "NW Morning News", "Sunrise Edition", "AM Northwest"],
        "DT": ["NW Living", "The Talk", "Let's Make a Deal", "The Price Is Right",
                "The Young and the Restless", "Local Hour"],
        "EF": ["Inside Edition", "Judge Judy", "Hot Bench", "People's Court"],
        "EN": ["Evening News at 5", "Evening News at 5:30", "Evening News at 6"],
        "PA": ["Wheel of Fortune", "Jeopardy!", "Entertainment Tonight", "Access Hollywood"],
        "PR": ["Survivor", "Chicago Fire", "Law & Order", "FBI", "NCIS",
                "The Voice", "60 Minutes", "Sunday Night Football"],
        "LN": ["Late News at 11", "News Tonight"],
        "LF": ["The Tonight Show", "Late Show", "Nightline", "Jimmy Kimmel Live"],
    }


# ── Rate Calculation ─────────────────────────────────────────────────────────

def calculate_spot_rate(
    station: str,
    daypart: str,
    length: int,
    air_date: date,
    rng: np.random.Generator,
) -> float:
    """Calculate a realistic spot rate based on station, daypart, length, date."""
    prime_low, prime_high = PRIME_AUR_RANGES[station]
    prime_mid = (prime_low + prime_high) / 2
    daypart_mult = DAYPARTS[daypart]["base_aur_mult"]
    base_rate = prime_mid * daypart_mult
    length_mult = SPOT_LENGTH_RATE_MULT[length]
    season_mult = seasonal_rate_multiplier(air_date)

    # YoY: 2025 dates get growth bump
    yoy_mult = 1.0
    if air_date.year >= 2025:
        yoy_mult = 1.0 + YOY_GROWTH[daypart]

    rate = base_rate * length_mult * season_mult * yoy_mult
    # Add noise: ±15%
    noise = rng.normal(1.0, 0.08)
    noise = max(0.85, min(1.15, noise))
    rate *= noise
    return round(rate, 2)


# ── Order Generation ─────────────────────────────────────────────────────────

def generate_orders(
    advertisers: List[Dict],
    agencies: List[str],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate ~500-600 orders across 5 stations and 50 advertisers.

    Uses recurring campaign patterns spread evenly across the time range.
    Includes warm-up orders starting in Q4 2023 whose flights extend into
    Q1 2024, so both Q1 periods have comparable spillover volume.
    """
    orders = []
    order_counter = 1000

    # Extended range for warm-up orders (flights starting Oct-Dec 2023
    # that spill into Jan-Mar 2024, giving Q1 2024 comparable spillover)
    WARMUP_START = date(2023, 10, 1)
    total_days = (DATE_END - DATE_START).days
    warmup_days = (DATE_START - WARMUP_START).days  # 92 days of warm-up

    for adv in advertisers:
        share = adv["share"]
        if share >= 0.06:
            n_orders = rng.integers(26, 40)
        elif share >= 0.03:
            n_orders = rng.integers(14, 24)
        elif share >= 0.015:
            n_orders = rng.integers(8, 16)
        elif share >= 0.008:
            n_orders = rng.integers(4, 10)
        else:
            n_orders = rng.integers(2, 5)

        # Assign agency (~70% through agencies)
        if adv["type"] == "national" or rng.random() < 0.55:
            agency = rng.choice(agencies)
        else:
            agency = None

        # Determine which stations this advertiser buys
        station_list = list(STATIONS.keys())
        if adv["type"] == "national":
            n_stations = rng.integers(3, 6)
            adv_stations = list(rng.choice(station_list, size=n_stations, replace=False))
        else:
            n_stations = rng.integers(1, 3)
            local_weights = np.array([0.10, 0.25, 0.25, 0.20, 0.20])
            adv_stations = list(rng.choice(
                station_list, size=n_stations, replace=False, p=local_weights
            ))

        # Add warm-up orders (Q4 2023 → spill into Q1 2024)
        # ~20% of orders are warm-up, proportional to advertiser size
        n_warmup = max(1, int(n_orders * 0.18))
        full_range_days = warmup_days + total_days  # Oct 2023 through Mar 2025

        for i in range(n_orders + n_warmup):
            order_counter += 1
            # Weight station selection by sqrt of market size (tempered to avoid
            # over-concentrating on KIRO which is 4-8x larger than others)
            stn_sizes = np.array([STATIONS[s]["size"] ** 0.5 for s in adv_stations])
            stn_probs = stn_sizes / stn_sizes.sum()
            station = rng.choice(adv_stations, p=stn_probs)

            flight_weeks = int(rng.choice([1, 2, 4, 4, 8, 8, 13, 13, 13]))
            flight_days = flight_weeks * 7

            if i < n_warmup:
                # Warm-up order: starts in Q4 2023
                start_offset = int(rng.integers(0, warmup_days))
                start_date = WARMUP_START + timedelta(days=start_offset)
            else:
                # Regular order: spread evenly across main range
                idx = i - n_warmup
                base_offset = int((idx / n_orders) * total_days)
                jitter = int(rng.integers(-14, 15))
                start_offset = max(0, min(total_days - flight_days, base_offset + jitter))
                start_date = DATE_START + timedelta(days=start_offset)

            end_date = start_date + timedelta(days=flight_days - 1)
            if end_date > DATE_END:
                end_date = DATE_END
            # Skip warm-up orders that don't reach into the main date range
            if end_date < DATE_START:
                continue

            lead_days = int(rng.integers(1, 31))
            order_date = start_date - timedelta(days=lead_days)
            if order_date < date(2023, 9, 1):
                order_date = date(2023, 9, 1)

            orders.append({
                "order_id": f"WO-{order_counter:05d}",
                "advertiser_name": adv["name"],
                "agency_name": agency,
                "order_date": order_date.isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "order_total": 0.0,  # backfilled later
                "station": station,
            })

    df = pd.DataFrame(orders)
    logger.info(f"Generated {len(df)} orders across {df['station'].nunique()} stations")
    return df


# ── Spot Generation ──────────────────────────────────────────────────────────

def generate_spots(
    orders_df: pd.DataFrame,
    advertisers: List[Dict],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate ~20,000 spots referencing valid orders."""
    programs = generate_programs()
    spots = []
    spot_counter = 100000

    # Build advertiser weight lookup
    adv_weights = {a["name"]: a["share"] for a in advertisers}

    # Station with notably worse preemption (for spec testing)
    high_preempt_station = "KHQ-TV"

    for _, order in orders_df.iterrows():
        start = date.fromisoformat(order["start_date"])
        end = date.fromisoformat(order["end_date"])
        station = order["station"]
        adv_name = order["advertiser_name"]
        # Clip to main date range (warm-up orders may start before DATE_START)
        effective_start = max(start, DATE_START)
        effective_end = min(end, DATE_END)
        flight_days = (effective_end - effective_start).days + 1
        if flight_days <= 0:
            continue

        adv_share = adv_weights.get(adv_name, 0.005)

        # Spots per order: proportional to flight length and advertiser weight.
        if adv_share >= 0.06:
            spots_per_week = rng.integers(6, 14)
        elif adv_share >= 0.03:
            spots_per_week = rng.integers(5, 11)
        elif adv_share >= 0.015:
            spots_per_week = rng.integers(3, 8)
        elif adv_share >= 0.008:
            spots_per_week = rng.integers(2, 6)
        else:
            spots_per_week = rng.integers(1, 4)

        n_spots = max(1, int(spots_per_week * flight_days / 7))

        # Volume seasonal adjustment
        mid_date = start + timedelta(days=flight_days // 2)
        vol_mult = seasonal_volume_multiplier(mid_date)
        n_spots = max(1, int(n_spots * vol_mult))

        # Distribute across dayparts weighted by volume (not revenue share)
        daypart_codes = list(DAYPARTS.keys())
        daypart_weights = np.array([DAYPART_VOLUME_WEIGHTS[dp] for dp in daypart_codes])

        daypart_assignments = rng.choice(daypart_codes, size=n_spots, p=daypart_weights)

        for i in range(n_spots):
            spot_counter += 1
            dp = daypart_assignments[i]
            dp_info = DAYPARTS[dp]

            # Random air_date within flight (clipped to main range)
            day_offset = int(rng.integers(0, flight_days))
            air_date = effective_start + timedelta(days=day_offset)

            # Random air_time within daypart window
            air_time = _random_time_in_daypart(dp_info["start"], dp_info["end"], rng)

            # Spot length
            length = int(rng.choice(SPOT_LENGTHS, p=SPOT_LENGTH_WEIGHTS))

            # Rate
            rate = calculate_spot_rate(station, dp, length, air_date, rng)

            # Status
            status = _determine_status(
                air_date, dp, station, high_preempt_station, rng
            )

            # Program
            program = rng.choice(programs[dp])

            spots.append({
                "spot_id": f"SP-{spot_counter:06d}",
                "order_id": order["order_id"],
                "air_date": air_date.isoformat(),
                "air_time": air_time.strftime("%H:%M:%S"),
                "daypart": dp,
                "program": program,
                "length": length,
                "rate": rate,
                "status": status,
                "station": station,
            })

    df = pd.DataFrame(spots)
    logger.info(f"Generated {len(df)} spots across {df['station'].nunique()} stations")
    return df


def _random_time_in_daypart(start: time, end: time, rng: np.random.Generator) -> time:
    """Generate a random time within a daypart window."""
    start_mins = start.hour * 60 + start.minute
    end_mins = end.hour * 60 + end.minute

    # Handle Late Fringe wrapping past midnight
    if end_mins <= start_mins:
        end_mins += 24 * 60

    rand_mins = int(rng.integers(start_mins, end_mins))
    rand_mins = rand_mins % (24 * 60)
    return time(rand_mins // 60, rand_mins % 60)


def _determine_status(
    air_date: date,
    daypart: str,
    station: str,
    high_preempt_station: str,
    rng: np.random.Generator,
) -> str:
    """Determine spot status: aired, scheduled, preempted, makegood."""
    if air_date > TODAY_CUTOFF:
        return "scheduled"

    # Base preemption rate: ~2.5%, higher in news dayparts at high_preempt_station
    preempt_chance = 0.020
    mg_chance = 0.015
    if daypart in ("EN", "LN"):
        preempt_chance = 0.035  # Breaking news preemptions
    if station == high_preempt_station:
        preempt_chance *= 1.8  # KIRO notably worse
        mg_chance *= 1.5

    roll = rng.random()
    if roll < preempt_chance:
        return "preempted"
    elif roll < preempt_chance + mg_chance:
        return "makegood"
    else:
        return "aired"


# ── Order Total Backfill ─────────────────────────────────────────────────────

def update_order_totals(orders_df: pd.DataFrame, spots_df: pd.DataFrame) -> pd.DataFrame:
    """Set order_total = sum of spot rates for each order."""
    totals = spots_df.groupby("order_id")["rate"].sum().reset_index()
    totals.columns = ["order_id", "calculated_total"]
    merged = orders_df.merge(totals, on="order_id", how="left")
    merged["order_total"] = merged["calculated_total"].fillna(0).round(2)
    merged.drop(columns=["calculated_total"], inplace=True)
    logger.info(f"Updated order totals. Total revenue: ${merged['order_total'].sum():,.2f}")
    return merged


# ── Inventory Generation ─────────────────────────────────────────────────────

def generate_inventory(
    spots_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate inventory: one row per station x daypart x date.

    Derives total_avails from the average booked rate per station/daypart
    and target sell-out rates, so aggregate sell-out metrics match targets.
    """
    all_dates = pd.date_range(DATE_START, DATE_END, freq="D")
    n_days = len(all_dates)
    rows = []

    # Count booked spots per station/daypart/date
    booked_counts = (
        spots_df.groupby(["station", "daypart", "air_date"])
        .size()
        .reset_index(name="booked_count")
    )
    booked_lookup = {}
    for _, row in booked_counts.iterrows():
        key = (row["station"], row["daypart"], row["air_date"])
        booked_lookup[key] = row["booked_count"]

    # Two-pass allocation: guarantee exact total avails per station/daypart
    # to hit target sell-out rates, then distribute across days.
    station_dp_totals = (
        spots_df.groupby(["station", "daypart"]).size().reset_index(name="total_spots")
    )
    total_booked_map = {}
    for _, row in station_dp_totals.iterrows():
        total_booked_map[(row["station"], row["daypart"])] = row["total_spots"]

    for station in STATIONS:
        for dp_code in DAYPARTS:
            key_base = (station, dp_code)
            total_booked = total_booked_map.get(key_base, 0)
            target_so = SELLOUT_TARGETS[dp_code]
            total_target_avails = int(round(total_booked / target_so)) if total_booked > 0 else n_days

            # Pass 1: collect booked per day, set floor at booked
            day_data = []
            for d in all_dates:
                d_date = d.date()
                key = (station, dp_code, d_date.isoformat())
                booked = booked_lookup.get(key, 0)
                day_data.append({"date": d_date, "booked": booked, "avails": booked})

            # Pass 2: distribute remaining avails (total_target - sum_booked)
            # across all days, weighted toward days with lower bookings
            sum_floor = sum(dd["booked"] for dd in day_data)
            remaining_to_add = max(0, total_target_avails - sum_floor)

            if remaining_to_add > 0:
                # Generate random weights and distribute
                raw_weights = rng.random(n_days) + 0.1
                raw_weights /= raw_weights.sum()
                extra_per_day = (raw_weights * remaining_to_add).astype(int)
                # Distribute rounding remainder
                shortfall = remaining_to_add - extra_per_day.sum()
                if shortfall > 0:
                    bump_indices = rng.choice(n_days, size=int(shortfall), replace=False)
                    for idx in bump_indices:
                        extra_per_day[idx] += 1
                for i, dd in enumerate(day_data):
                    dd["avails"] += int(extra_per_day[i])

            for dd in day_data:
                remaining = dd["avails"] - dd["booked"]
                rows.append({
                    "date": dd["date"].isoformat(),
                    "daypart": dp_code,
                    "station": station,
                    "total_avails": dd["avails"],
                    "booked": dd["booked"],
                    "remaining": remaining,
                })

    df = pd.DataFrame(rows)
    logger.info(
        f"Generated {len(df)} inventory rows "
        f"({df['station'].nunique()} stations x {df['daypart'].nunique()} dayparts x "
        f"{df['date'].nunique()} dates)"
    )
    return df


# ── Validation ────────────────────────────────────────────────────────────────

def validate_all(
    orders_df: pd.DataFrame,
    spots_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
) -> bool:
    """Run referential integrity and distribution checks."""
    errors = []

    # 1. Every spot references a valid order
    valid_orders = set(orders_df["order_id"])
    invalid_refs = spots_df[~spots_df["order_id"].isin(valid_orders)]
    if len(invalid_refs) > 0:
        errors.append(f"  {len(invalid_refs)} spots reference invalid order_ids")

    # 2. spot.air_date within order's [start_date, end_date]
    merged = spots_df.merge(
        orders_df[["order_id", "start_date", "end_date", "station"]],
        on="order_id",
        suffixes=("", "_order"),
    )
    out_of_range = merged[
        (merged["air_date"] < merged["start_date"]) |
        (merged["air_date"] > merged["end_date"])
    ]
    if len(out_of_range) > 0:
        errors.append(f"  {len(out_of_range)} spots have air_date outside order flight range")

    # 3. spot.station matches order.station
    station_mismatch = merged[merged["station"] != merged["station_order"]]
    if len(station_mismatch) > 0:
        errors.append(f"  {len(station_mismatch)} spots have station mismatch with order")

    # 4. No null order_ids in spots
    null_orders = spots_df["order_id"].isna().sum()
    if null_orders > 0:
        errors.append(f"  {null_orders} spots have null order_id")

    # 5. No negative inventory remaining
    neg_inv = inventory_df[inventory_df["remaining"] < 0]
    if len(neg_inv) > 0:
        errors.append(f"  {len(neg_inv)} inventory rows have negative remaining")

    # 6. inventory.remaining = total_avails - booked
    inv_check = inventory_df[
        inventory_df["remaining"] != inventory_df["total_avails"] - inventory_df["booked"]
    ]
    if len(inv_check) > 0:
        errors.append(f"  {len(inv_check)} inventory rows: remaining != total_avails - booked")

    # 7. Future spots should be "scheduled"
    future_non_sched = spots_df[
        (spots_df["air_date"] > TODAY_CUTOFF.isoformat()) &
        (spots_df["status"] != "scheduled")
    ]
    if len(future_non_sched) > 0:
        errors.append(f"  {len(future_non_sched)} future spots not marked as 'scheduled'")

    if errors:
        logger.error("VALIDATION FAILED:")
        for e in errors:
            logger.error(e)
        return False

    logger.info("All validation checks passed")
    return True


# ── Summary Statistics ────────────────────────────────────────────────────────

def print_summary(
    orders_df: pd.DataFrame,
    spots_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
):
    """Print summary statistics vs distribution targets."""
    print("\n" + "=" * 70)
    print("  SAMPLE DATA GENERATION -- SUMMARY")
    print("=" * 70)

    # Row counts
    print(f"\n  Orders:    {len(orders_df):>8,}")
    print(f"  Spots:     {len(spots_df):>8,}")
    print(f"  Inventory: {len(inventory_df):>8,}")

    total_revenue = spots_df["rate"].sum()
    print(f"\n  Total Revenue: ${total_revenue:>14,.2f}")

    # Revenue by station
    print(f"\n  {'-' * 50}")
    print(f"  REVENUE BY STATION")
    print(f"  {'-' * 50}")
    station_rev = spots_df.groupby("station")["rate"].sum().sort_values(ascending=False)
    for station, rev in station_rev.items():
        pct = rev / total_revenue * 100
        print(f"    {station:<10} ${rev:>12,.2f}  ({pct:5.1f}%)")

    # Revenue by daypart
    print(f"\n  {'-' * 50}")
    print(f"  REVENUE BY DAYPART (vs Target)")
    print(f"  {'-' * 50}")
    dp_rev = spots_df.groupby("daypart")["rate"].sum().sort_values(ascending=False)
    for dp, rev in dp_rev.items():
        pct = rev / total_revenue * 100
        target = DAYPARTS[dp]["revenue_share"] * 100
        delta = pct - target
        print(f"    {dp} ({DAYPARTS[dp]['name']:<16}) {pct:5.1f}%  (target: {target:5.1f}%, delta: {delta:+.1f}%)")

    # Spot length distribution
    print(f"\n  {'-' * 50}")
    print(f"  SPOT LENGTH DISTRIBUTION (vs Target)")
    print(f"  {'-' * 50}")
    length_counts = spots_df["length"].value_counts(normalize=True).sort_index()
    targets = {15: 0.20, 30: 0.70, 60: 0.10}
    for length, pct in length_counts.items():
        target = targets.get(length, 0)
        print(f"    {length}s:  {pct*100:5.1f}%  (target: {target*100:.0f}%)")

    # Status distribution
    print(f"\n  {'-' * 50}")
    print(f"  SPOT STATUS DISTRIBUTION")
    print(f"  {'-' * 50}")
    status_counts = spots_df["status"].value_counts(normalize=True)
    for status, pct in status_counts.items():
        print(f"    {status:<12} {pct*100:5.1f}%")

    # Advertiser concentration
    print(f"\n  {'-' * 50}")
    print(f"  ADVERTISER CONCENTRATION")
    print(f"  {'-' * 50}")
    adv_rev = spots_df.groupby(
        spots_df["order_id"].map(
            dict(zip(orders_df["order_id"], orders_df["advertiser_name"]))
        )
    )["rate"].sum().sort_values(ascending=False)
    top5_rev = adv_rev.head(5).sum()
    top1_pct = adv_rev.iloc[0] / total_revenue * 100
    top5_pct = top5_rev / total_revenue * 100
    print(f"    Top advertiser:  {adv_rev.index[0]}")
    print(f"      Revenue share: {top1_pct:.1f}%  (target: ~13%, threshold: 15%)")
    print(f"    Top 5 combined:  {top5_pct:.1f}%  (target: ~45%)")
    print(f"    Total advertisers: {adv_rev.nunique()}")

    # Sell-out rates by daypart
    print(f"\n  {'-' * 50}")
    print(f"  SELL-OUT RATES BY DAYPART (vs Target)")
    print(f"  {'-' * 50}")
    inv_agg = inventory_df.groupby("daypart").agg(
        total=("total_avails", "sum"),
        booked=("booked", "sum"),
    )
    inv_agg["sellout"] = inv_agg["booked"] / inv_agg["total"]
    for dp in ["PR", "EN", "PA", "LN", "EM", "EF", "DT", "LF"]:
        if dp in inv_agg.index:
            so = inv_agg.loc[dp, "sellout"] * 100
            target = SELLOUT_TARGETS[dp] * 100
            flag = " !! PRICING FLAG" if so >= 85 else ""
            print(f"    {dp} ({DAYPARTS[dp]['name']:<16}) {so:5.1f}%  (target: {target:.0f}%){flag}")

    # Makegood rates by station
    print(f"\n  {'-' * 50}")
    print(f"  MAKEGOOD + PREEMPTION RATES BY STATION")
    print(f"  {'-' * 50}")
    past_spots = spots_df[spots_df["air_date"] <= TODAY_CUTOFF.isoformat()]
    for station in STATIONS:
        st_spots = past_spots[past_spots["station"] == station]
        if len(st_spots) == 0:
            continue
        preempt_pct = (st_spots["status"] == "preempted").mean() * 100
        mg_pct = (st_spots["status"] == "makegood").mean() * 100
        combined = preempt_pct + mg_pct
        flag = " !! ABOVE 5% THRESHOLD" if combined > 5 else ""
        print(f"    {station:<10} preempted: {preempt_pct:4.1f}%  makegood: {mg_pct:4.1f}%  combined: {combined:4.1f}%{flag}")

    # YoY comparison (Q1 2024 vs Q1 2025)
    print(f"\n  {'-' * 50}")
    print(f"  YoY Q1 COMPARISON (Jan-Mar 2024 vs 2025)")
    print(f"  {'-' * 50}")
    q1_2024 = spots_df[
        (spots_df["air_date"] >= "2024-01-01") & (spots_df["air_date"] <= "2024-03-31")
    ]
    q1_2025 = spots_df[
        (spots_df["air_date"] >= "2025-01-01") & (spots_df["air_date"] <= "2025-03-31")
    ]
    rev_2024 = q1_2024["rate"].sum()
    rev_2025 = q1_2025["rate"].sum()
    if rev_2024 > 0:
        yoy_change = (rev_2025 - rev_2024) / rev_2024 * 100
        print(f"    Q1 2024 revenue: ${rev_2024:>12,.2f}")
        print(f"    Q1 2025 revenue: ${rev_2025:>12,.2f}")
        print(f"    YoY change:      {yoy_change:>+11.1f}%")
    aur_2024 = q1_2024["rate"].mean()
    aur_2025 = q1_2025["rate"].mean()
    if aur_2024 > 0:
        aur_change = (aur_2025 - aur_2024) / aur_2024 * 100
        print(f"    Q1 2024 AUR:     ${aur_2024:>12,.2f}")
        print(f"    Q1 2025 AUR:     ${aur_2025:>12,.2f}")
        print(f"    AUR change:      {aur_change:>+11.1f}%")

    print("\n" + "=" * 70)
    print("  GENERATION COMPLETE")
    print("=" * 70 + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate WideOrbit WO Traffic sample data for a 5-station broadcast group"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Output directory for CSV files (default: same as script)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("WideOrbit Sample Data Generator")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Seed: {args.seed}")
    logger.info(f"Date range: {DATE_START} to {DATE_END}")
    logger.info("=" * 60)

    # Step 1: Setup
    advertisers = generate_advertisers(rng)
    agencies = generate_agencies()
    logger.info(f"Configured {len(advertisers)} advertisers, {len(agencies)} agencies")

    # Step 2: Generate orders
    logger.info("Generating orders...")
    orders_df = generate_orders(advertisers, agencies, rng)

    # Step 3: Generate spots
    logger.info("Generating spots...")
    spots_df = generate_spots(orders_df, advertisers, rng)

    # Step 4: Backfill order totals
    logger.info("Updating order totals from spot sums...")
    orders_df = update_order_totals(orders_df, spots_df)

    # Step 5: Generate inventory
    logger.info("Generating inventory...")
    inventory_df = generate_inventory(spots_df, rng)

    # Step 6: Validate
    logger.info("Validating data integrity...")
    valid = validate_all(orders_df, spots_df, inventory_df)

    # Step 7: Write CSVs
    orders_path = output_dir / "orders.csv"
    spots_path = output_dir / "spots.csv"
    inventory_path = output_dir / "inventory.csv"

    orders_df.to_csv(orders_path, index=False)
    spots_df.to_csv(spots_path, index=False)
    inventory_df.to_csv(inventory_path, index=False)

    logger.info(f"Wrote {orders_path} ({len(orders_df)} rows)")
    logger.info(f"Wrote {spots_path} ({len(spots_df)} rows)")
    logger.info(f"Wrote {inventory_path} ({len(inventory_df)} rows)")

    # Step 8: Print summary
    print_summary(orders_df, spots_df, inventory_df)

    if not valid:
        logger.error("Data validation failed — check errors above")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
