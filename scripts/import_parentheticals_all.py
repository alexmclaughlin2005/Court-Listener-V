#!/usr/bin/env python3
"""
Import ALL parentheticals from CourtListener bulk data CSV

This script imports all parentheticals WITHOUT checking if opinions exist.
It temporarily disables foreign key constraints during import.

Usage:
    python scripts/import_parentheticals_all.py --input ~/Downloads/parentheticals-2025-10-31.csv.bz2
"""
import os
import sys
import bz2
import logging
import psycopg2
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_csv_line(line):
    """
    Custom CSV parser that handles the specific format of CourtListener's CSV:
    - Fields are quoted with double quotes
    - Internal quotes are escaped with backslash or doubled
    - Last field (group_id) may be empty

    Expected format: "id","text","score","described_opinion_id","describing_opinion_id","group_id"
    """
    # Strip newline
    line = line.rstrip('\n\r')

    # Pattern to match quoted fields: "field content"
    # We'll extract fields one by one from right to left (since group_id is last and may be empty)

    # Try to extract from the end backwards
    # Last field: group_id (may be empty: "" or "123")
    match = re.search(r',"([^"]*)"$', line)
    if not match:
        return None
    group_id = match.group(1)
    line = line[:match.start()] + ','  # Remove last field, keep comma

    # describing_opinion_id (should be numeric)
    match = re.search(r',"(\d+)",$', line)
    if not match:
        return None
    describing_opinion_id = match.group(1)
    line = line[:match.start()] + ','

    # described_opinion_id (should be numeric)
    match = re.search(r',"(\d+)",$', line)
    if not match:
        return None
    described_opinion_id = match.group(1)
    line = line[:match.start()] + ','

    # score (may be numeric or empty)
    match = re.search(r',"([^"]*)",$', line)
    if not match:
        return None
    score = match.group(1)
    line = line[:match.start()] + ','

    # Now we have: "id","text",
    # Extract id from start
    match = re.match(r'^"(\d+)",', line)
    if not match:
        return None
    id_val = match.group(1)
    line = line[match.end():]  # Remove id, keep rest

    # What's left should be the text field: "text",
    # Remove leading and trailing quotes and comma
    if not line.startswith('"') or not line.endswith('",'):
        return None
    text = line[1:-2]  # Remove surrounding " and trailing ",

    # Unescape quotes in text (handle both \" and "")
    text = text.replace('\\"', '"').replace('""', '"')

    return {
        'id': id_val,
        'text': text,
        'score': score,
        'described_opinion_id': described_opinion_id,
        'describing_opinion_id': describing_opinion_id,
        'group_id': group_id
    }

def disable_foreign_key_constraints(conn):
    """Temporarily disable foreign key constraints on parenthetical table"""
    cursor = conn.cursor()
    try:
        logger.info("Disabling foreign key constraints...")
        cursor.execute("""
            ALTER TABLE search_parenthetical
            DROP CONSTRAINT IF EXISTS search_parenthetical_described_opinion_id_fkey
        """)
        cursor.execute("""
            ALTER TABLE search_parenthetical
            DROP CONSTRAINT IF EXISTS search_parenthetical_describing_opinion_id_fkey
        """)
        conn.commit()
        logger.info("Foreign key constraints disabled")
    finally:
        cursor.close()

def enable_foreign_key_constraints(conn):
    """Re-enable foreign key constraints on parenthetical table (NOT VALIDATED)"""
    cursor = conn.cursor()
    try:
        logger.info("Re-enabling foreign key constraints (NOT VALIDATED)...")
        cursor.execute("""
            ALTER TABLE search_parenthetical
            ADD CONSTRAINT search_parenthetical_described_opinion_id_fkey
            FOREIGN KEY (described_opinion_id)
            REFERENCES search_opinion(id)
            NOT VALID
        """)
        cursor.execute("""
            ALTER TABLE search_parenthetical
            ADD CONSTRAINT search_parenthetical_describing_opinion_id_fkey
            FOREIGN KEY (describing_opinion_id)
            REFERENCES search_opinion(id)
            NOT VALID
        """)
        conn.commit()
        logger.info("Foreign key constraints re-enabled (NOT VALIDATED)")
        logger.info("Note: Constraints will be validated for new inserts only")
    finally:
        cursor.close()

def import_parentheticals_batch(conn, batch):
    """Import a batch of parentheticals"""
    if not batch:
        return 0

    cursor = conn.cursor()
    try:
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

    parser = argparse.ArgumentParser(description='Import ALL parentheticals (disables FK constraints)')
    parser.add_argument('--input', required=True, help='Path to parentheticals CSV file (can be .bz2)')
    parser.add_argument('--database-url', help='Database URL (or use DATABASE_URL env var)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for imports')
    parser.add_argument('--limit', type=int, help='Limit number of rows to import (for testing)')
    parser.add_argument('--skip-constraints', action='store_true',
                       help='Skip disabling/enabling constraints (if already done)')

    args = parser.parse_args()

    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)

    conn = psycopg2.connect(database_url)

    # Disable foreign key constraints
    if not args.skip_constraints:
        disable_foreign_key_constraints(conn)

    logger.info(f"Reading from {args.input}")
    if args.input.endswith('.bz2'):
        file_handle = bz2.open(args.input, 'rt', encoding='utf-8')
    else:
        file_handle = open(args.input, 'r', encoding='utf-8')

    try:
        batch = []
        total_read = 0
        total_imported = 0
        skipped_parse_error = 0

        # Skip header
        next(file_handle)

        for line in file_handle:
            total_read += 1

            # Parse line
            row = parse_csv_line(line)
            if not row:
                skipped_parse_error += 1
                if total_read % 10000 == 0:
                    logger.warning(f"Parse error at line {total_read}")
                continue

            try:
                # Add to batch (NO validation of opinion IDs)
                batch.append({
                    'id': int(row['id']),
                    'text': row['text'],
                    'score': float(row['score']) if row['score'] else None,
                    'described_opinion_id': int(row['described_opinion_id']),
                    'describing_opinion_id': int(row['describing_opinion_id']),
                    'group_id': int(row['group_id']) if row['group_id'] else None
                })
            except (ValueError, KeyError) as e:
                skipped_parse_error += 1
                continue

            # Import batch when full
            if len(batch) >= args.batch_size:
                imported = import_parentheticals_batch(conn, batch)
                total_imported += imported
                batch = []

                if total_read % 10000 == 0:
                    logger.info(
                        f"Progress: {total_read:,} read | {total_imported:,} imported | "
                        f"{skipped_parse_error:,} parse errors"
                    )

            if args.limit and total_read >= args.limit:
                break

        # Import remaining batch
        if batch:
            imported = import_parentheticals_batch(conn, batch)
            total_imported += imported

        logger.info("=" * 80)
        logger.info("✅ Import complete!")
        logger.info(f"Total rows read: {total_read:,}")
        logger.info(f"Total imported: {total_imported:,}")
        logger.info(f"Skipped (parse errors): {skipped_parse_error:,}")
        logger.info("=" * 80)

    finally:
        file_handle.close()

        # Re-enable foreign key constraints (NOT VALIDATED for existing data)
        if not args.skip_constraints:
            enable_foreign_key_constraints(conn)

        conn.close()

if __name__ == '__main__':
    main()
