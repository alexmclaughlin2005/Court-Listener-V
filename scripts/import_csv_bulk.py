"""
Local CSV Import - Run with DATABASE_URL environment variable
Usage:
  export DATABASE_URL="postgresql://..."
  python3 scripts/import_csv_bulk.py --courts people_db_court-2025-10-31.csv --limit 10000
"""
import csv
import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_batch

# Increase CSV field size limit for large text fields (opinions, syllabi, etc.)
csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_value(value, field_name=None):
    """Parse CSV value"""
    if not value or value == '\\N' or value == 'NULL':
        return None
    if field_name in ['date_filed_is_approximate', 'blocked', 'in_use',
                      'has_opinion_scraper', 'has_oral_argument_scraper', 'extracted_by_ocr']:
        return 't' if value.lower() in ['true', 't', '1', 'yes'] else 'f'
    # Note: court_id is a string (e.g., 'scotus', 'ca9'), but other IDs are integers
    if field_name in ['docket_id', 'citation_count', 'source', 'depth',
                      'cited_opinion_id', 'citing_opinion_id', 'position',
                      'described_opinion_id', 'describing_opinion_id', 'group_id']:
        try:
            return str(int(float(value)))
        except:
            return None
    # For numeric IDs that could be int or string (cluster id, docket id from CSV)
    if field_name == 'id':
        try:
            # Try to parse as integer first
            return str(int(float(value)))
        except:
            # If that fails, it's a string ID (like court IDs)
            return value if value else None
    return value

def import_courts(conn, csv_path, batch_size=1000):
    logger.info(f"Importing courts from {csv_path}")
    cursor = conn.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                # Skip rows with no ID
                court_id = parse_value(row.get('id'), 'id')
                if not court_id:
                    skipped += 1
                    continue

                court_data = (
                    court_id,
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
                    logger.info(f"✓ Imported {count} courts (skipped {skipped})")
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

        logger.info(f"✅ Imported {count} courts total (skipped {skipped} invalid rows)")

    except Exception as e:
        logger.error(f"❌ Error importing courts: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def import_dockets(conn, csv_path, batch_size=5000, limit=None):
    logger.info(f"Importing dockets from {csv_path}")
    cursor = conn.cursor()

    # Get valid court IDs
    logger.info("Loading valid court IDs from database...")
    cursor.execute("SELECT id FROM search_court")
    valid_courts = set(row[0] for row in cursor.fetchall())
    logger.info(f"Found {len(valid_courts)} valid courts")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                court_id = row.get('court_id')
                if not court_id:
                    skipped += 1
                    continue

                # Skip dockets with invalid court_id references
                if court_id not in valid_courts:
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

        logger.info(f"✅ Imported {count} dockets total (skipped {skipped})")

    except Exception as e:
        logger.error(f"❌ Error importing dockets: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def import_clusters(conn, csv_path, batch_size=5000, limit=None):
    logger.info(f"Importing opinion clusters from {csv_path}")
    cursor = conn.cursor()

    # Get valid docket IDs
    logger.info("Loading valid docket IDs from database...")
    cursor.execute("SELECT id FROM search_docket")
    valid_dockets = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_dockets)} valid dockets")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                docket_id = parse_value(row.get('docket_id'), 'docket_id')
                if not docket_id:
                    skipped += 1
                    continue

                # Skip clusters with invalid docket_id references
                if docket_id not in valid_dockets:
                    skipped += 1
                    continue

                # Only include columns that exist in the database schema
                try:
                    cluster_data = (
                        parse_value(row['id'], 'id'),
                        parse_value(row['docket_id'], 'docket_id'),
                        parse_value(row.get('date_created'), 'date_created'),
                        parse_value(row.get('date_modified'), 'date_modified'),
                        parse_value(row.get('slug'), 'slug'),
                        parse_value(row.get('case_name'), 'case_name'),
                        parse_value(row.get('case_name_short'), 'case_name_short'),
                        parse_value(row.get('case_name_full'), 'case_name_full'),
                        parse_value(row.get('date_filed'), 'date_filed'),
                        parse_value(row.get('date_filed_is_approximate', 'f'), 'date_filed_is_approximate'),
                        parse_value(row.get('citation_count', '0'), 'citation_count'),
                        parse_value(row.get('precedential_status', 'Published'), 'precedential_status'),
                        parse_value(row.get('scdb_id'), 'scdb_id'),
                        parse_value(row.get('scdb_decision_direction'), 'scdb_decision_direction'),
                        parse_value(row.get('scdb_votes_majority'), 'scdb_votes_majority'),
                        parse_value(row.get('scdb_votes_minority'), 'scdb_votes_minority'),
                        parse_value(row.get('judges'), 'judges'),
                        parse_value(row.get('source', '0'), 'source'),
                    )
                    batch.append(cluster_data)
                    count += 1
                except Exception as e:
                    # Skip malformed rows
                    skipped += 1
                    continue

                if len(batch) >= batch_size:
                    try:
                        execute_batch(cursor, """
                            INSERT INTO search_opinioncluster
                            (id, docket_id, date_created, date_modified, slug, case_name,
                             case_name_short, case_name_full, date_filed, date_filed_is_approximate,
                             citation_count, precedential_status, scdb_id, scdb_decision_direction,
                             scdb_votes_majority, scdb_votes_minority, judges, source)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, batch, page_size=batch_size)
                        conn.commit()
                        logger.info(f"✓ Imported {count} clusters (skipped {skipped})")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch insert failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                        skipped += len(batch)
                        conn.rollback()
                    batch = []

            if batch:
                try:
                    execute_batch(cursor, """
                        INSERT INTO search_opinioncluster
                        (id, docket_id, date_created, date_modified, slug, case_name,
                         case_name_short, case_name_full, date_filed, date_filed_is_approximate,
                         citation_count, precedential_status, scdb_id, scdb_decision_direction,
                         scdb_votes_majority, scdb_votes_minority, judges, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, batch)
                    conn.commit()
                except Exception as batch_error:
                    logger.warning(f"⚠️  Final batch failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                    skipped += len(batch)
                    conn.rollback()

        logger.info(f"✅ Imported {count} clusters total (skipped {skipped})")

    except Exception as e:
        logger.error(f"❌ Error importing clusters: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def import_opinions(conn, csv_path, batch_size=5000, limit=None):
    logger.info(f"Importing opinions from {csv_path}")
    cursor = conn.cursor()

    # Get valid cluster IDs
    logger.info("Loading valid cluster IDs from database...")
    cursor.execute("SELECT id FROM search_opinioncluster")
    valid_clusters = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_clusters)} valid clusters")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                # Skip opinions without cluster_id
                cluster_id = parse_value(row.get('cluster_id'), 'cluster_id')
                if not cluster_id:
                    skipped += 1
                    continue

                # Skip opinions with invalid cluster_id references
                if cluster_id not in valid_clusters:
                    skipped += 1
                    continue

                try:
                    opinion_data = (
                        parse_value(row['id'], 'id'),
                        parse_value(row.get('date_created'), 'date_created'),
                        parse_value(row.get('date_modified'), 'date_modified'),
                        cluster_id,
                        parse_value(row.get('plain_text'), 'plain_text'),
                        parse_value(row.get('html'), 'html'),
                        parse_value(row.get('html_with_citations'), 'html_with_citations'),
                        parse_value(row.get('type'), 'type'),
                        parse_value(row.get('sha1'), 'sha1'),
                        parse_value(row.get('download_url'), 'download_url'),
                        parse_value(row.get('local_path'), 'local_path'),
                        parse_value(row.get('extracted_by_ocr', 'f'), 'extracted_by_ocr'),
                        parse_value(row.get('word_count'), 'word_count'),
                        parse_value(row.get('char_count'), 'char_count'),
                    )
                    batch.append(opinion_data)
                    count += 1
                except Exception as e:
                    skipped += 1
                    continue

                if len(batch) >= batch_size:
                    try:
                        execute_batch(cursor, """
                            INSERT INTO search_opinion
                            (id, date_created, date_modified, cluster_id, plain_text, html,
                             html_with_citations, type, sha1, download_url, local_path,
                             extracted_by_ocr, word_count, char_count)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, batch, page_size=batch_size)
                        conn.commit()
                        logger.info(f"✓ Imported {count} opinions (skipped {skipped})")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch insert failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                        skipped += len(batch)
                        conn.rollback()
                    batch = []

            if batch:
                try:
                    execute_batch(cursor, """
                        INSERT INTO search_opinion
                        (id, date_created, date_modified, cluster_id, plain_text, html,
                         html_with_citations, type, sha1, download_url, local_path,
                         extracted_by_ocr, word_count, char_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, batch)
                    conn.commit()
                except Exception as batch_error:
                    logger.warning(f"⚠️  Final batch failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                    skipped += len(batch)
                    conn.rollback()

        logger.info(f"✅ Imported {count} opinions total (skipped {skipped})")

    except Exception as e:
        logger.error(f"❌ Error importing opinions: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def import_citations(conn, csv_path, batch_size=10000, limit=None):
    logger.info(f"Importing citations from {csv_path}")
    cursor = conn.cursor()

    # Get valid opinion IDs
    logger.info("Loading valid opinion IDs from database...")
    cursor.execute("SELECT id FROM search_opinion")
    valid_opinions = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_opinions)} valid opinions")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                # Skip citations with missing IDs
                citing_id = parse_value(row.get('citing_opinion_id'), 'citing_opinion_id')
                cited_id = parse_value(row.get('cited_opinion_id'), 'cited_opinion_id')

                if not citing_id or not cited_id:
                    skipped += 1
                    continue

                # Skip citations with invalid opinion_id references
                if citing_id not in valid_opinions or cited_id not in valid_opinions:
                    skipped += 1
                    continue

                try:
                    citation_data = (
                        parse_value(row['id'], 'id'),
                        citing_id,
                        cited_id,
                        parse_value(row.get('depth', '1'), 'depth'),
                    )
                    batch.append(citation_data)
                    count += 1
                except Exception as e:
                    skipped += 1
                    continue

                if len(batch) >= batch_size:
                    try:
                        execute_batch(cursor, """
                            INSERT INTO search_opinionscited
                            (id, citing_opinion_id, cited_opinion_id, depth)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (citing_opinion_id, cited_opinion_id) DO NOTHING
                        """, batch, page_size=batch_size)
                        conn.commit()
                        logger.info(f"✓ Imported {count} citations (skipped {skipped})")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch insert failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                        skipped += len(batch)
                        conn.rollback()
                    batch = []

            if batch:
                try:
                    execute_batch(cursor, """
                        INSERT INTO search_opinionscited
                        (id, citing_opinion_id, cited_opinion_id, depth)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (citing_opinion_id, cited_opinion_id) DO NOTHING
                    """, batch)
                    conn.commit()
                except Exception as batch_error:
                    logger.warning(f"⚠️  Final batch failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                    skipped += len(batch)
                    conn.rollback()

        logger.info(f"✅ Imported {count} citations total (skipped {skipped})")

    except Exception as e:
        logger.error(f"❌ Error importing citations: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def import_parentheticals(conn, csv_path, batch_size=10000, limit=None):
    logger.info(f"Importing parentheticals from {csv_path}")
    cursor = conn.cursor()

    # Get valid opinion IDs
    logger.info("Loading valid opinion IDs from database...")
    cursor.execute("SELECT id FROM search_opinion")
    valid_opinions = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_opinions)} valid opinions")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            count = 0
            skipped = 0

            for row in reader:
                if limit and count >= limit:
                    break

                try:
                    # Validate opinion IDs exist
                    described_id = parse_value(row.get('described_opinion_id'), 'described_opinion_id')
                    describing_id = parse_value(row.get('describing_opinion_id'), 'describing_opinion_id')

                    if not described_id or not describing_id:
                        skipped += 1
                        continue

                    # Skip if opinion IDs don't exist
                    if described_id not in valid_opinions or describing_id not in valid_opinions:
                        skipped += 1
                        continue

                    # Get text (required field)
                    text = parse_value(row.get('text'))
                    if not text:
                        skipped += 1
                        continue

                    parenthetical_data = (
                        parse_value(row.get('id'), 'id'),
                        text,
                        parse_value(row.get('score')),
                        described_id,
                        describing_id,
                        parse_value(row.get('group_id')),
                    )
                    batch.append(parenthetical_data)
                    count += 1
                except Exception as e:
                    skipped += 1
                    continue

                if len(batch) >= batch_size:
                    try:
                        execute_batch(cursor, """
                            INSERT INTO search_parenthetical
                            (id, text, score, described_opinion_id, describing_opinion_id, group_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, batch, page_size=batch_size)
                        conn.commit()
                        logger.info(f"✓ Imported {count} parentheticals (skipped {skipped})")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch insert failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                        skipped += len(batch)
                        conn.rollback()
                    batch = []

            if batch:
                try:
                    execute_batch(cursor, """
                        INSERT INTO search_parenthetical
                        (id, text, score, described_opinion_id, describing_opinion_id, group_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, batch)
                    conn.commit()
                except Exception as batch_error:
                    logger.warning(f"⚠️  Final batch failed, skipping {len(batch)} rows: {str(batch_error)[:100]}")
                    skipped += len(batch)
                    conn.rollback()

        logger.info(f"✅ Imported {count} parentheticals total (skipped {skipped})")

    except Exception as e:
        logger.error(f"❌ Error importing parentheticals: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import CourtListener CSV data')
    parser.add_argument('--courts', help='Path to courts CSV')
    parser.add_argument('--dockets', help='Path to dockets CSV')
    parser.add_argument('--clusters', help='Path to opinion clusters CSV')
    parser.add_argument('--opinions', help='Path to opinions CSV')
    parser.add_argument('--citations', help='Path to citations CSV')
    parser.add_argument('--parentheticals', help='Path to parentheticals CSV')
    parser.add_argument('--limit', type=int, help='Limit rows (for testing)')
    parser.add_argument('--batch-size', type=int, default=5000, help='Batch size')

    args = parser.parse_args()

    # Get DATABASE_URL from environment or use Railway default
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        # Try Railway internal URL
        db_url = os.environ.get('DATABASE_PRIVATE_URL')

    if not db_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Set it with: export DATABASE_URL='postgresql://...'")
        sys.exit(1)

    logger.info(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        logger.info("✅ Connected successfully")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        sys.exit(1)

    try:
        if args.courts:
            import_courts(conn, args.courts, batch_size=args.batch_size)

        if args.dockets:
            import_dockets(conn, args.dockets, batch_size=args.batch_size, limit=args.limit)

        if args.clusters:
            import_clusters(conn, args.clusters, batch_size=args.batch_size, limit=args.limit)

        if args.opinions:
            import_opinions(conn, args.opinions, batch_size=args.batch_size, limit=args.limit)

        if args.citations:
            import_citations(conn, args.citations, batch_size=args.batch_size, limit=args.limit)

        if args.parentheticals:
            import_parentheticals(conn, args.parentheticals, batch_size=args.batch_size, limit=args.limit)

        logger.info("🎉 Import complete!")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
