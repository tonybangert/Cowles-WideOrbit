"""
Data Ingestion Pipeline — WideOrbit WO Traffic

Reads raw WO exports from data/raw/ and writes to data/processed/.
Handles: CSV parsing, type casting, null handling, deduplication.

Usage:
    python pipeline/ingest/run.py
    python pipeline/ingest/run.py --source data/sample/  # Ingest sample data
"""

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("ingest")


def ingest(source_dir: Path, output_dir: Path):
    """Ingest WO data exports from source to processed output."""
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return False

    csv_files = list(source_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in {source_dir}")
        return False

    logger.info(f"Found {len(csv_files)} files to ingest:")
    for f in csv_files:
        logger.info(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    output_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Implement ingestion logic
    # 1. Read each CSV with pandas/polars
    # 2. Validate against expected schema (data/schemas/)
    # 3. Cast types, handle nulls
    # 4. Deduplicate records
    # 5. Write to data/processed/

    logger.info("Ingestion pipeline — not yet implemented")
    logger.info("Next step: Get sample data or WO export schema to build parser")
    return True


def main():
    parser = argparse.ArgumentParser(description="WideOrbit Data Ingestion Pipeline")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source directory (defaults to data/raw/)",
    )
    args = parser.parse_args()

    source = Path(args.source) if args.source else PROJECT_ROOT / "data" / "raw"
    output = PROJECT_ROOT / "data" / "processed"

    logger.info("=" * 60)
    logger.info("WideOrbit Data Ingestion Pipeline")
    logger.info(f"Source: {source}")
    logger.info(f"Output: {output}")
    logger.info("=" * 60)

    success = ingest(source, output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
