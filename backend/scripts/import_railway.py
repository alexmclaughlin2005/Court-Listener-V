"""
Import script to run on Railway with bulk CSV data
Usage: railway run python backend/scripts/import_railway.py --courts courts.csv --limit 10000
"""
import csv
import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_value(value, field_name=None):
    """Parse CSV value"""
    if not value or value == '\\N' or value == 'NULL':
        return None
    if field_name in ['date_filed_is_approximate', 'blocked']:
        return 't' if value.lower() in ['true', 't', '1'] else 'f'
    if field_name in ['id', 'docket_id', 'citation_count', 'source', 'depth',
                      'cited_opinion_id', 'citing_opinion_id']:
        try:
            return str(int(value))
        except:
            return None
    return value

def import_courts(conn, csv_path, batch_size=1000):
    logger.info(f"Importing courts from {csv_path}")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0

        for row in reader:
            court_data = (
                parse_value(row['id'], 'id'),
                parse_value(row.get('full_name', ''), 'full_name'),
                parse_value(row.get('short_name', ''), 'short_name'),
                parse_value(row.get('citation_string', ''), 'citation_string'),
                parse_value(row.get('in_use', 't'), 'in_use'),
                parse_value(row.get('has_opinion_scraper', 'f'), 'has_opinion_scraper'),
                parse_value(row.get('has_oral_argument_scraper', 'f'), 'has_oral_argument_scraper'),
                parse_value(row.get('position', '0'), 'position'),
            )
            batch.append(court_data)
            count += 1

            if len(batch) >= batch_size:
                execute_batch(cursor, """
                    INSERT INTO search_court
                    (id, full_name, short_name, citation_string, in_use,
                     has_opinion_scraper, has_oral_argument_scraper, position)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, batch)
                conn.commit()
                logger.info(f"✓ Imported {count} courts")
                batch = []

        if batch:
            execute_batch(cursor, """
                INSERT INTO search_court
                (id, full_name, short_name, citation_string, in_use,
                 has_opinion_scraper, has_oral_argument_scraper, position)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            conn.commit()

    logger.info(f"✓ Imported {count} courts total")
    cursor.close()

def import_dockets(conn, csv_path, batch_size=5000, limit=None):
    logger.info(f"Importing dockets from {csv_path}")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        skipped = 0

        for row in reader:
            if limit and count >= limit:
                break

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
                execute_batch(cursor, """
                    INSERT INTO search_docket
                    (id, date_created, date_modified, source, court_id, date_filed,
                     case_name_short, case_name, case_name_full, slug, docket_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, batch, page_size=batch_size)
                conn.commit()
                logger.info(f"✓ Imported {count} dockets (skipped {skipped})")
                batch = []

        if batch:
            execute_batch(cursor, """
                INSERT INTO search_docket
                (id, date_created, date_modified, source, court_id, date_filed,
                 case_name_short, case_name, case_name_full, slug, docket_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            conn.commit()

    logger.info(f"✓ Imported {count} dockets total (skipped {skipped})")
    cursor.close()

def import_clusters(conn, csv_path, batch_size=5000, limit=None):
    logger.info(f"Importing opinion clusters from {csv_path}")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        skipped = 0

        for row in reader:
            if limit and count >= limit:
                break

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
                execute_batch(cursor, """
                    INSERT INTO search_opinioncluster
                    (id, docket_id, date_created, date_modified, judges, date_filed,
                     date_filed_is_approximate, slug, case_name_short, case_name,
                     case_name_full, source, procedural_history, attorneys,
                     nature_of_suit, posture, syllabus, summary, disposition,
                     citation_count, precedential_status, blocked)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, batch, page_size=batch_size)
                conn.commit()
                logger.info(f"✓ Imported {count} clusters (skipped {skipped})")
                batch = []

        if batch:
            execute_batch(cursor, """
                INSERT INTO search_opinioncluster
                (id, docket_id, date_created, date_modified, judges, date_filed,
                 date_filed_is_approximate, slug, case_name_short, case_name,
                 case_name_full, source, procedural_history, attorneys,
                 nature_of_suit, posture, syllabus, summary, disposition,
                 citation_count, precedential_status, blocked)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            conn.commit()

    logger.info(f"✓ Imported {count} clusters total (skipped {skipped})")
    cursor.close()

def import_citations(conn, csv_path, batch_size=10000, limit=None):
    logger.info(f"Importing citations from {csv_path}")
    cursor = conn.cursor()

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0
        skipped = 0

        for row in reader:
            if limit and count >= limit:
                break

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
                execute_batch(cursor, """
                    INSERT INTO search_opinionscited
                    (cited_opinion_id, citing_opinion_id, depth)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, batch, page_size=batch_size)
                conn.commit()
                logger.info(f"✓ Imported {count} citations (skipped {skipped})")
                batch = []

        if batch:
            execute_batch(cursor, """
                INSERT INTO search_opinionscited
                (cited_opinion_id, citing_opinion_id, depth)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, batch)
            conn.commit()

    logger.info(f"✓ Imported {count} citations total (skipped {skipped})")
    cursor.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CourtListener CSV data')
    parser.add_argument('--courts', help='Path to courts CSV')
    parser.add_argument('--dockets', help='Path to dockets CSV')
    parser.add_argument('--clusters', help='Path to opinion clusters CSV')
    parser.add_argument('--citations', help='Path to citations CSV')
    parser.add_argument('--limit', type=int, help='Limit rows (for testing)')
    parser.add_argument('--batch-size', type=int, default=5000, help='Batch size')

    args = parser.parse_args()

    # Get DATABASE_URL from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info(f"Connecting to database...")
    conn = psycopg2.connect(db_url)

    try:
        if args.courts:
            import_courts(conn, args.courts, batch_size=args.batch_size)

        if args.dockets:
            import_dockets(conn, args.dockets, batch_size=args.batch_size, limit=args.limit)

        if args.clusters:
            import_clusters(conn, args.clusters, batch_size=args.batch_size, limit=args.limit)

        if args.citations:
            import_citations(conn, args.citations, batch_size=args.batch_size, limit=args.limit)

        logger.info("✅ Import complete!")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
