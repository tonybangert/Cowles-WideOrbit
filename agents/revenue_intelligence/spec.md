# Revenue Intelligence Agent — Specification

## Purpose
Analyze WideOrbit WO Traffic data to surface revenue trends, pricing insights,
advertiser risk, and inventory pacing for broadcast television station groups.

## Inputs
- Processed WO data tables: orders, spots, inventory, makegoods
- Time range (default: trailing 90 days + same period prior year)
- Station filter (optional — single station or group-wide)
- Daypart filter (optional)

## Outputs
The agent produces a structured analysis with these sections:

### 1. Revenue by Daypart Trending
- Revenue by daypart for current period vs. prior year
- Week-over-week and month-over-month trends
- Daypart share of total revenue

### 2. AUR (Average Unit Rate) Analysis
- AUR by daypart, current vs. prior year
- AUR trend direction (rising, flat, declining)
- Pricing recommendations when sell-out rates are high

### 3. Advertiser Concentration
- Top 10 advertisers by revenue share
- Revenue concentration risk (HHI or top-5 share)
- New vs. returning advertiser ratio

### 4. Inventory Pacing
- Sell-out rate by daypart (booked / available)
- Pacing vs. same period last year
- Projected sell-out at current pace

### 5. Makegood Exposure
- Makegood spots as % of total spots
- Revenue impact of preemptions
- Stations/dayparts with highest makegood rates

## Decision Logic
- If sell-out > 85% in a daypart → flag as pricing opportunity
- If single advertiser > 15% of revenue → flag concentration risk
- If AUR declining while sell-out is flat → flag potential rate erosion
- If makegood rate > 5% → flag operational issue

## Output Format
- Structured JSON for dashboard rendering
- Narrative summary for chat/report consumption
- Both outputs from same analysis pass

## Guardrails
- Advisory only — never recommend specific dollar amounts for rate changes
- Flag when data is insufficient for reliable conclusions
- Always compare to prior year when data is available
- Never extrapolate beyond 30 days without explicit disclaimer
