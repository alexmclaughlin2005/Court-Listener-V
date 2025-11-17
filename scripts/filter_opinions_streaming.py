#!/usr/bin/env python3
"""
Filter opinions CSV directly from compressed file without full extraction.

This saves disk space by streaming the decompression and filtering in one pass.

Usage:
    python scripts/filter_opinions_streaming.py \
        --input opinions-2025-10-31.csv.bz2 \
        --output opinions-filtered.csv \
        --database-url "postgresql://..."
"""
import csv
import psycopg2
import os
import sys
import logging
import bz2
from pathlib import Path

# Increase CSV field size limit for large opinion texts
csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit

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

def filter_opinions_streaming(input_path, output_path, valid_clusters):
    """Filter opinions CSV directly from compressed file"""
    logger.info(f"Reading compressed file: {input_path}")
    logger.info(f"Writing filtered opinions to: {output_path}")

    input_size = Path(input_path).stat().st_size / (1024**3)
    logger.info(f"Compressed file size: {input_size:.2f} GB")
    logger.info("Streaming decompression and filtering...")

    kept_count = 0
    skipped_count = 0
    total_count = 0

    # Open compressed file and decompress on-the-fly
    with bz2.open(input_path, 'rt', encoding='utf-8', errors='replace') as infile:
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
                    output_size = Path(output_path).stat().st_size / (1024**3) if os.path.exists(output_path) else 0
                    logger.info(
                        f"Processed {total_count:,} rows | "
                        f"Kept: {kept_count:,} ({kept_count/total_count*100:.1f}%) | "
                        f"Skipped: {skipped_count:,} | "
                        f"Output size: {output_size:.2f} GB"
                    )

    output_size = Path(output_path).stat().st_size / (1024**3)

    logger.info("=" * 60)
    logger.info(f"✅ Filtering complete!")
    logger.info(f"Total rows processed: {total_count:,}")
    logger.info(f"Opinions kept: {kept_count:,}")
    logger.info(f"Opinions skipped: {skipped_count:,}")
    logger.info(f"Keep rate: {kept_count/total_count*100:.2f}%")
    logger.info(f"Compressed input size: {input_size:.2f} GB")
    logger.info(f"Filtered output size: {output_size:.2f} GB")
    logger.info("=" * 60)

    return kept_count

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Filter opinions CSV from compressed file')
    parser.add_argument('--input', required=True, help='Input compressed CSV file (.bz2)')
    parser.add_argument('--output', required=True, help='Output filtered CSV file')
    parser.add_argument('--database-url', required=True, help='Database URL')

    args = parser.parse_args()

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
        valid_clusters = get_valid_cluster_ids(args.database_url)

        if len(valid_clusters) == 0:
            logger.error("No clusters found in database!")
            sys.exit(1)

        # Filter opinions with streaming decompression
        kept_count = filter_opinions_streaming(args.input, args.output, valid_clusters)

        if kept_count == 0:
            logger.warning("⚠️  No matching opinions found!")
            logger.warning("This might indicate a mismatch between cluster IDs in the database and CSV")
        else:
            logger.info(f"\n✅ Next step: Import filtered opinions")
            logger.info(f"python scripts/import_csv_bulk.py --opinions {args.output} --batch-size 5000")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
