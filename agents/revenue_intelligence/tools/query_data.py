"""
Revenue Intelligence — Data Query Tools

These tools are used by the revenue intelligence agent to query
processed WideOrbit data. They will be registered as Claude tool_use
definitions when the agent runs.
"""

from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def get_revenue_by_daypart(
    station: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Query revenue totals grouped by daypart."""
    # TODO: Implement with pandas/polars against processed data
    return {"status": "stub", "tool": "get_revenue_by_daypart"}


def get_aur_trends(
    daypart: Optional[str] = None,
    station: Optional[str] = None,
    granularity: str = "weekly",
):
    """Query Average Unit Rate trends over time."""
    # TODO: Implement with pandas/polars against processed data
    return {"status": "stub", "tool": "get_aur_trends"}


def get_top_advertisers(
    limit: int = 10,
    station: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Query top advertisers by revenue."""
    # TODO: Implement with pandas/polars against processed data
    return {"status": "stub", "tool": "get_top_advertisers"}


def get_sellout_rates(
    station: Optional[str] = None,
    daypart: Optional[str] = None,
):
    """Query inventory sell-out rates by daypart."""
    # TODO: Implement with pandas/polars against processed data
    return {"status": "stub", "tool": "get_sellout_rates"}


def get_makegood_summary(
    station: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Query makegood/preemption summary."""
    # TODO: Implement with pandas/polars against processed data
    return {"status": "stub", "tool": "get_makegood_summary"}


# Claude tool_use definitions for the revenue intelligence agent
TOOL_DEFINITIONS = [
    {
        "name": "get_revenue_by_daypart",
        "description": "Query revenue totals grouped by broadcast daypart. Returns revenue, spot count, and AUR for each daypart.",
        "input_schema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": "Station call letters (e.g., 'KTVX'). Omit for all stations."},
                "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
            },
        },
    },
    {
        "name": "get_aur_trends",
        "description": "Query Average Unit Rate (AUR) trends over time for a specific daypart or all dayparts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "daypart": {"type": "string", "description": "Daypart name (e.g., 'prime', 'early_news'). Omit for all."},
                "station": {"type": "string", "description": "Station call letters. Omit for all stations."},
                "granularity": {"type": "string", "enum": ["daily", "weekly", "monthly"], "description": "Time granularity for trend data"},
            },
        },
    },
    {
        "name": "get_top_advertisers",
        "description": "Query top advertisers ranked by revenue. Shows revenue share and concentration metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of top advertisers to return (default: 10)"},
                "station": {"type": "string", "description": "Station call letters. Omit for all stations."},
                "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
            },
        },
    },
    {
        "name": "get_sellout_rates",
        "description": "Query inventory sell-out rates (booked / available) by daypart. Includes pacing vs. prior year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": "Station call letters. Omit for all stations."},
                "daypart": {"type": "string", "description": "Daypart name. Omit for all dayparts."},
            },
        },
    },
    {
        "name": "get_makegood_summary",
        "description": "Query makegood and preemption summary. Shows makegood rate, revenue impact, and problem areas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": "Station call letters. Omit for all stations."},
                "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
            },
        },
    },
]
