"""
Data Normalization Pipeline

Transforms ingested WO data into clean, analysis-ready tables.
Handles: daypart code normalization, advertiser deduplication,
date standardization, and derived metric calculation.

Usage:
    python pipeline/normalize/run.py
"""

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("normalize")


def normalize(processed_dir: Path):
    """Normalize ingested data into analysis-ready tables."""
    if not processed_dir.exists():
        logger.error(f"Processed directory does not exist: {processed_dir}")
        logger.info("Run the ingestion pipeline first: python pipeline/ingest/run.py")
        return False

    # TODO: Implement normalization
    # 1. Standardize daypart codes to canonical names
    # 2. Normalize advertiser names (dedup variations)
    # 3. Calculate derived fields (AUR = revenue / spots)
    # 4. Build date dimensions (week, month, quarter, YoY keys)
    # 5. Output clean tables

    logger.info("Normalization pipeline — not yet implemented")
    return True


def main():
    processed = PROJECT_ROOT / "data" / "processed"

    logger.info("=" * 60)
    logger.info("WideOrbit Data Normalization Pipeline")
    logger.info(f"Source: {processed}")
    logger.info("=" * 60)

    success = normalize(processed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
