#!/usr/bin/env python3
"""
Import parentheticals from CourtListener bulk data CSV

This script:
1. Reads the compressed parentheticals CSV file
2. Filters to only parentheticals where both opinions exist in our database
3. Imports them in batches to the database

Usage:
    python scripts/import_parentheticals.py --input ~/Downloads/parentheticals-2025-10-31.csv.bz2
"""
import os
import sys
import csv
import bz2
import logging
import psycopg2
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Increase CSV field size limit for large texts
csv.field_size_limit(10 * 1024 * 1024)

def get_valid_opinion_ids(database_url):
    """Get set of all opinion IDs in our database"""
    logger.info("Loading valid opinion IDs from database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM search_opinion")
    opinion_ids = set(row[0] for row in cursor.fetchall())

    cursor.close()
    conn.close()

    logger.info(f"Found {len(opinion_ids):,} opinion IDs in database")
    return opinion_ids

def import_parentheticals_batch(conn, batch):
    """Import a batch of parentheticals"""
    if not batch:
        return 0

    cursor = conn.cursor()

    try:
        # Use COPY for fast bulk insert with ON CONFLICT
        # First, try to insert and count how many were new
        execute_values = []
        for row in batch:
            execute_values.append(cursor.mogrify(
                "(%s, %s, %s, %s, %s, %s)",
                (row['id'], row['text'], row['score'],
                 row['described_opinion_id'], row['describing_opinion_id'], row['group_id'])
            ).decode('utf-8'))

        query = f"""
            INSERT INTO search_parenthetical
            (id, text, score, described_opinion_id, describing_opinion_id, group_id)
            VALUES {','.join(execute_values)}
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                score = EXCLUDED.score,
                described_opinion_id = EXCLUDED.described_opinion_id,
                describing_opinion_id = EXCLUDED.describing_opinion_id,
                group_id = EXCLUDED.group_id
        """

        cursor.execute(query)
        conn.commit()
        return len(batch)
    except Exception as e:
        logger.error(f"Error importing batch: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import parentheticals from CourtListener bulk data')
    parser.add_argument('--input', required=True, help='Path to parentheticals CSV file (can be .bz2)')
    parser.add_argument('--database-url', help='Database URL (or use DATABASE_URL env var)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for imports')
    parser.add_argument('--limit', type=int, help='Limit number of rows to import (for testing)')

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)

    # Connect to database
    logger.info("Connecting to database...")
    conn = psycopg2.connect(database_url)

    # Get valid opinion IDs
    valid_opinions = get_valid_opinion_ids(database_url)

    # Open input file (handle both compressed and uncompressed)
    logger.info(f"Reading from {args.input}")
    if args.input.endswith('.bz2'):
        file_handle = bz2.open(args.input, 'rt', encoding='utf-8')
    else:
        file_handle = open(args.input, 'r', encoding='utf-8')

    try:
        reader = csv.DictReader(file_handle)

        batch = []
        total_read = 0
        total_imported = 0
        skipped_missing_opinion = 0

        for row in reader:
            total_read += 1

            try:
                # Check if both opinions exist in our database
                described_id = int(row['described_opinion_id'])
                describing_id = int(row['describing_opinion_id'])

                if described_id not in valid_opinions or describing_id not in valid_opinions:
                    skipped_missing_opinion += 1
                    continue

                # Add to batch
                batch.append({
                    'id': int(row['id']),
                    'text': row['text'],
                    'score': float(row['score']) if row['score'] else None,
                    'described_opinion_id': described_id,
                    'describing_opinion_id': describing_id,
                    'group_id': int(row['group_id']) if row['group_id'] else None
                })
            except (ValueError, KeyError) as e:
                # Skip malformed rows
                logger.warning(f"Skipping malformed row at line {total_read}: {e}")
                continue

            # Import batch when full
            if len(batch) >= args.batch_size:
                imported = import_parentheticals_batch(conn, batch)
                total_imported += imported
                batch = []

                if total_read % 10000 == 0:
                    logger.info(
                        f"Progress: {total_read:,} read | {total_imported:,} imported | "
                        f"{skipped_missing_opinion:,} skipped (missing opinion)"
                    )

            # Check limit
            if args.limit and total_read >= args.limit:
                logger.info(f"Reached limit of {args.limit} rows")
                break

        # Import remaining batch
        if batch:
            imported = import_parentheticals_batch(conn, batch)
            total_imported += imported

        # Final summary
        logger.info("=" * 80)
        logger.info("✅ Import complete!")
        logger.info(f"Total rows read: {total_read:,}")
        logger.info(f"Total imported: {total_imported:,}")
        logger.info(f"Skipped (missing opinion): {skipped_missing_opinion:,}")
        logger.info("=" * 80)

    finally:
        file_handle.close()
        conn.close()

if __name__ == '__main__':
    main()
