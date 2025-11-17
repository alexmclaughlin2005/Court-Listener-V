"""
Bulk CSV Import Script for CourtListener Data
Streams large CSV files and imports in batches to avoid memory issues
"""
import csv
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2 import sql

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(settings.DATABASE_URL)

# Field mappings - CSV columns to database columns
DOCKET_FIELDS = [
    'id', 'date_created', 'date_modified', 'source', 'court_id',
    'appeal_from_str', 'assigned_to_str', 'referred_to_str', 'panel_str',
    'date_last_index', 'date_cert_granted', 'date_cert_denied',
    'date_argued', 'date_reargued', 'date_reargument_denied',
    'date_filed', 'date_terminated', 'date_last_filing',
    'case_name_short', 'case_name', 'case_name_full', 'slug', 'docket_number'
]

CLUSTER_FIELDS = [
    'id', 'docket_id', 'date_created', 'date_modified',
    'judges', 'date_filed', 'date_filed_is_approximate', 'slug',
    'case_name_short', 'case_name', 'case_name_full',
    'source', 'procedural_history', 'attorneys', 'nature_of_suit',
    'posture', 'syllabus', 'summary', 'disposition',
    'citation_count', 'precedential_status', 'blocked'
]

CITATION_FIELDS = [
    'id', 'cited_opinion_id', 'citing_opinion_id', 'depth'
]

def parse_value(value: str, field_name: str) -> Optional[str]:
    """Parse CSV value and handle NULL/empty cases"""
    if not value or value == '\\N' or value == 'NULL':
        return None
    # Handle boolean fields
    if field_name in ['date_filed_is_approximate', 'blocked']:
        return 't' if value.lower() in ['true', 't', '1'] else 'f'
    # Handle integer fields
    if field_name in ['id', 'docket_id', 'citation_count', 'source', 'depth',
                      'cited_opinion_id', 'citing_opinion_id']:
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return None
    return value

def import_courts(csv_path: str, batch_size: int = 1000):
    """Import courts from CSV"""
    logger.info(f"Importing courts from {csv_path}")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0

            for row in reader:
                # Extract only fields we need
                court_data = (
                    parse_value(row['id'], 'id'),
                    parse_value(row.get('full_name', ''), 'full_name'),
                    parse_value(row.get('short_name', ''), 'short_name'),
                    parse_value(row.get('citation_string', ''), 'citation_string'),
                    parse_value(row.get('in_use', 't'), 'in_use'),
                    parse_value(row.get('has_opinion_scraper', 'f'), 'has_opinion_scraper'),
                    parse_value(row.get('has_oral_argument_scraper', 'f'), 'has_oral_argument_scraper'),
                    parse_value(row.get('position', '0'), 'position'),
                    parse_value(row.get('date_modified', datetime.now().isoformat()), 'date_modified'),
                )
                batch.append(court_data)
                count += 1

                if len(batch) >= batch_size:
                    insert_query = """
                        INSERT INTO search_court
                        (id, full_name, short_name, citation_string, in_use,
                         has_opinion_scraper, has_oral_argument_scraper, position, date_modified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """
                    execute_batch(cursor, insert_query, batch)
                    conn.commit()
                    logger.info(f"Imported {count} courts...")
                    batch = []

            # Insert remaining
            if batch:
                insert_query = """
                    INSERT INTO search_court
                    (id, full_name, short_name, citation_string, in_use,
                     has_opinion_scraper, has_oral_argument_scraper, position, date_modified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
                execute_batch(cursor, insert_query, batch)
                conn.commit()

            logger.info(f"✓ Imported {count} courts total")

    except Exception as e:
        logger.error(f"Error importing courts: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def import_dockets(csv_path: str, batch_size: int = 5000, limit: Optional[int] = None):
    """Import dockets from CSV with streaming"""
    logger.info(f"Importing dockets from {csv_path}")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                # Skip if no court_id (required foreign key)
                if not row.get('court_id'):
                    skipped += 1
                    continue

                docket_data = (
                    parse_value(row['id'], 'id'),
                    parse_value(row.get('date_created'), 'date_created'),
                    parse_value(row.get('date_modified'), 'date_modified'),
                    parse_value(row.get('source', '0'), 'source'),
                    parse_value(row['court_id'], 'court_id'),
                    parse_value(row.get('date_filed'), 'date_filed'),
                    parse_value(row.get('case_name_short'), 'case_name_short'),
                    parse_value(row.get('case_name'), 'case_name'),
                    parse_value(row.get('case_name_full'), 'case_name_full'),
                    parse_value(row.get('slug'), 'slug'),
                    parse_value(row.get('docket_number'), 'docket_number'),
                )
                batch.append(docket_data)
                count += 1

                if len(batch) >= batch_size:
                    insert_query = """
                        INSERT INTO search_docket
                        (id, date_created, date_modified, source, court_id, date_filed,
                         case_name_short, case_name, case_name_full, slug, docket_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """
                    execute_batch(cursor, insert_query, batch, page_size=batch_size)
                    conn.commit()
                    logger.info(f"Imported {count} dockets... (skipped {skipped})")
                    batch = []

            # Insert remaining
            if batch:
                insert_query = """
                    INSERT INTO search_docket
                    (id, date_created, date_modified, source, court_id, date_filed,
                     case_name_short, case_name, case_name_full, slug, docket_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
                execute_batch(cursor, insert_query, batch)
                conn.commit()

            logger.info(f"✓ Imported {count} dockets total (skipped {skipped})")

    except Exception as e:
        logger.error(f"Error importing dockets: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def import_clusters(csv_path: str, batch_size: int = 5000, limit: Optional[int] = None):
    """Import opinion clusters from CSV with streaming"""
    logger.info(f"Importing opinion clusters from {csv_path}")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                # Skip if no docket_id (required foreign key)
                if not row.get('docket_id'):
                    skipped += 1
                    continue

                cluster_data = (
                    parse_value(row['id'], 'id'),
                    parse_value(row['docket_id'], 'docket_id'),
                    parse_value(row.get('date_created'), 'date_created'),
                    parse_value(row.get('date_modified'), 'date_modified'),
                    parse_value(row.get('judges'), 'judges'),
                    parse_value(row.get('date_filed'), 'date_filed'),
                    parse_value(row.get('date_filed_is_approximate', 'f'), 'date_filed_is_approximate'),
                    parse_value(row.get('slug'), 'slug'),
                    parse_value(row.get('case_name_short'), 'case_name_short'),
                    parse_value(row.get('case_name'), 'case_name'),
                    parse_value(row.get('case_name_full'), 'case_name_full'),
                    parse_value(row.get('source', '0'), 'source'),
                    parse_value(row.get('procedural_history'), 'procedural_history'),
                    parse_value(row.get('attorneys'), 'attorneys'),
                    parse_value(row.get('nature_of_suit'), 'nature_of_suit'),
                    parse_value(row.get('posture'), 'posture'),
                    parse_value(row.get('syllabus'), 'syllabus'),
                    parse_value(row.get('summary'), 'summary'),
                    parse_value(row.get('disposition'), 'disposition'),
                    parse_value(row.get('citation_count', '0'), 'citation_count'),
                    parse_value(row.get('precedential_status', 'Unknown'), 'precedential_status'),
                    parse_value(row.get('blocked', 'f'), 'blocked'),
                )
                batch.append(cluster_data)
                count += 1

                if len(batch) >= batch_size:
                    insert_query = """
                        INSERT INTO search_opinioncluster
                        (id, docket_id, date_created, date_modified, judges, date_filed,
                         date_filed_is_approximate, slug, case_name_short, case_name,
                         case_name_full, source, procedural_history, attorneys,
                         nature_of_suit, posture, syllabus, summary, disposition,
                         citation_count, precedential_status, blocked)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """
                    execute_batch(cursor, insert_query, batch, page_size=batch_size)
                    conn.commit()
                    logger.info(f"Imported {count} clusters... (skipped {skipped})")
                    batch = []

            # Insert remaining
            if batch:
                insert_query = """
                    INSERT INTO search_opinioncluster
                    (id, docket_id, date_created, date_modified, judges, date_filed,
                     date_filed_is_approximate, slug, case_name_short, case_name,
                     case_name_full, source, procedural_history, attorneys,
                     nature_of_suit, posture, syllabus, summary, disposition,
                     citation_count, precedential_status, blocked)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
                execute_batch(cursor, insert_query, batch)
                conn.commit()

            logger.info(f"✓ Imported {count} clusters total (skipped {skipped})")

    except Exception as e:
        logger.error(f"Error importing clusters: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def import_citations(csv_path: str, batch_size: int = 10000, limit: Optional[int] = None):
    """Import citations from CSV with streaming"""
    logger.info(f"Importing citations from {csv_path}")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                # Skip if missing required fields
                if not row.get('cited_opinion_id') or not row.get('citing_opinion_id'):
                    skipped += 1
                    continue

                citation_data = (
                    parse_value(row['cited_opinion_id'], 'cited_opinion_id'),
                    parse_value(row['citing_opinion_id'], 'citing_opinion_id'),
                    parse_value(row.get('depth', '1'), 'depth'),
                )
                batch.append(citation_data)
                count += 1

                if len(batch) >= batch_size:
                    insert_query = """
                        INSERT INTO search_opinionscited
                        (cited_opinion_id, citing_opinion_id, depth)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """
                    execute_batch(cursor, insert_query, batch, page_size=batch_size)
                    conn.commit()
                    logger.info(f"Imported {count} citations... (skipped {skipped})")
                    batch = []

            # Insert remaining
            if batch:
                insert_query = """
                    INSERT INTO search_opinionscited
                    (cited_opinion_id, citing_opinion_id, depth)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """
                execute_batch(cursor, insert_query, batch)
                conn.commit()

            logger.info(f"✓ Imported {count} citations total (skipped {skipped})")

    except Exception as e:
        logger.error(f"Error importing citations: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CourtListener CSV data')
    parser.add_argument('--courts', help='Path to courts CSV')
    parser.add_argument('--dockets', help='Path to dockets CSV')
    parser.add_argument('--clusters', help='Path to opinion clusters CSV')
    parser.add_argument('--citations', help='Path to citations CSV')
    parser.add_argument('--limit', type=int, help='Limit number of rows to import (for testing)')
    parser.add_argument('--batch-size', type=int, default=5000, help='Batch size for inserts')

    args = parser.parse_args()

    if args.courts:
        import_courts(args.courts, batch_size=args.batch_size)

    if args.dockets:
        import_dockets(args.dockets, batch_size=args.batch_size, limit=args.limit)

    if args.clusters:
        import_clusters(args.clusters, batch_size=args.batch_size, limit=args.limit)

    if args.citations:
        import_citations(args.citations, batch_size=args.batch_size, limit=args.limit)

if __name__ == '__main__':
    main()
