#!/usr/bin/env python3
"""
Filter opinions CSV to only include opinions for clusters in the database.

This significantly reduces the dataset size from ~50GB to ~1-2GB by only
keeping opinions that match your existing clusters.

Usage:
    python scripts/filter_opinions_by_clusters.py \
        --input opinions-2025-10-31.csv \
        --output opinions-filtered.csv
"""
import csv
import psycopg2
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_valid_cluster_ids(database_url):
    """Get all cluster IDs from the database"""
    logger.info("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    logger.info("Loading cluster IDs from database...")
    cursor.execute("SELECT id FROM search_opinioncluster")
    cluster_ids = set(str(row[0]) for row in cursor.fetchall())

    cursor.close()
    conn.close()

    logger.info(f"Found {len(cluster_ids)} clusters in database")
    return cluster_ids

def filter_opinions(input_path, output_path, valid_clusters):
    """Filter opinions CSV to only include valid cluster_id matches"""
    logger.info(f"Reading opinions from: {input_path}")
    logger.info(f"Writing filtered opinions to: {output_path}")

    input_size = Path(input_path).stat().st_size / (1024**3)
    logger.info(f"Input file size: {input_size:.2f} GB")

    kept_count = 0
    skipped_count = 0
    total_count = 0

    with open(input_path, 'r', encoding='utf-8', errors='replace') as infile:
        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                total_count += 1

                # Check if cluster_id exists in our database
                cluster_id = row.get('cluster_id', '')
                if cluster_id and cluster_id in valid_clusters:
                    writer.writerow(row)
                    kept_count += 1
                else:
                    skipped_count += 1

                # Progress update every 100K rows
                if total_count % 100000 == 0:
                    output_size = Path(output_path).stat().st_size / (1024**3)
                    logger.info(
                        f"Processed {total_count:,} rows | "
                        f"Kept: {kept_count:,} | "
                        f"Skipped: {skipped_count:,} | "
                        f"Output size: {output_size:.2f} GB"
                    )

    output_size = Path(output_path).stat().st_size / (1024**3)
    reduction = ((input_size - output_size) / input_size * 100) if input_size > 0 else 0

    logger.info("=" * 60)
    logger.info(f"✅ Filtering complete!")
    logger.info(f"Total rows processed: {total_count:,}")
    logger.info(f"Opinions kept: {kept_count:,}")
    logger.info(f"Opinions skipped: {skipped_count:,}")
    logger.info(f"Input size: {input_size:.2f} GB")
    logger.info(f"Output size: {output_size:.2f} GB")
    logger.info(f"Size reduction: {reduction:.1f}%")
    logger.info("=" * 60)

    return kept_count

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Filter opinions CSV by cluster IDs')
    parser.add_argument('--input', required=True, help='Input opinions CSV file')
    parser.add_argument('--output', required=True, help='Output filtered CSV file')
    parser.add_argument('--database-url', help='Database URL (or use DATABASE_URL env var)')

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not provided")
        logger.error("Use --database-url or set DATABASE_URL environment variable")
        sys.exit(1)

    # Check input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Check output file doesn't already exist
    if os.path.exists(args.output):
        response = input(f"Output file {args.output} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted")
            sys.exit(0)
        os.remove(args.output)

    try:
        # Get valid cluster IDs from database
        valid_clusters = get_valid_cluster_ids(database_url)

        if len(valid_clusters) == 0:
            logger.error("No clusters found in database!")
            sys.exit(1)

        # Filter opinions
        kept_count = filter_opinions(args.input, args.output, valid_clusters)

        if kept_count == 0:
            logger.warning("⚠️  No matching opinions found!")
            logger.warning("This might indicate a mismatch between cluster IDs in the database and CSV")
        else:
            logger.info(f"\n✅ Next step: Import filtered opinions")
            logger.info(f"railway run python scripts/import_csv_bulk.py --opinions {args.output} --batch-size 5000")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    main()
