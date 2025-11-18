"""
Resumable CSV Import with Progress Tracking
This script can resume imports from where they left off by tracking progress in the database.

NOTE: Opinions are NOT included here - use the API batch import instead to fetch opinion text.

Usage:
  export DATABASE_URL="postgresql://..."

  # Import in chunks of 100k records
  python3 scripts/import_csv_resumable.py --dockets dockets-2025-10-31.csv --chunk-size 100000

  # Resume from where it left off (automatically detects progress)
  python3 scripts/import_csv_resumable.py --dockets dockets-2025-10-31.csv --chunk-size 100000

  # Import all tables in sequence (except opinions)
  python3 scripts/import_csv_resumable.py --all --chunk-size 100000

  # Check progress status
  python3 scripts/import_csv_resumable.py --status
"""
import csv
import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

# Increase CSV field size limit for large text fields
csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_progress_table(conn):
    """Create table to track import progress"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_progress (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                csv_file VARCHAR(500) NOT NULL,
                rows_imported INTEGER DEFAULT 0,
                rows_skipped INTEGER DEFAULT 0,
                last_row_processed INTEGER DEFAULT 0,
                total_rows INTEGER,
                status VARCHAR(50) DEFAULT 'in_progress',
                started_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                error_message TEXT,
                UNIQUE(table_name, csv_file)
            )
        """)
        conn.commit()
        logger.info("✓ Progress tracking table ready")
    except Exception as e:
        logger.warning(f"Progress table might already exist: {e}")
        conn.rollback()
    finally:
        cursor.close()

def get_progress(conn, table_name, csv_file):
    """Get current import progress for a table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT rows_imported, rows_skipped, last_row_processed, status
            FROM import_progress
            WHERE table_name = %s AND csv_file = %s
        """, (table_name, csv_file))
        result = cursor.fetchone()
        if result:
            return {
                'rows_imported': result[0],
                'rows_skipped': result[1],
                'last_row_processed': result[2],
                'status': result[3]
            }
        return None
    finally:
        cursor.close()

def update_progress(conn, table_name, csv_file, rows_imported, rows_skipped, last_row, status='in_progress', error=None):
    """Update import progress"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO import_progress
            (table_name, csv_file, rows_imported, rows_skipped, last_row_processed, status, error_message, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (table_name, csv_file)
            DO UPDATE SET
                rows_imported = EXCLUDED.rows_imported,
                rows_skipped = EXCLUDED.rows_skipped,
                last_row_processed = EXCLUDED.last_row_processed,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                updated_at = NOW(),
                completed_at = CASE WHEN EXCLUDED.status = 'completed' THEN NOW() ELSE import_progress.completed_at END
        """, (table_name, csv_file, rows_imported, rows_skipped, last_row, status, error))
        conn.commit()
    finally:
        cursor.close()

def parse_value(value, field_name=None):
    """Parse CSV value"""
    if not value or value == '\\N' or value == 'NULL':
        return None
    if field_name in ['date_filed_is_approximate', 'blocked', 'in_use',
                      'has_opinion_scraper', 'has_oral_argument_scraper', 'extracted_by_ocr']:
        return 't' if value.lower() in ['true', 't', '1', 'yes'] else 'f'
    if field_name in ['docket_id', 'citation_count', 'source', 'depth',
                      'cited_opinion_id', 'citing_opinion_id', 'position',
                      'described_opinion_id', 'describing_opinion_id', 'group_id']:
        try:
            return str(int(float(value)))
        except:
            return None
    if field_name == 'id':
        try:
            return str(int(float(value)))
        except:
            return value if value else None
    return value

def import_courts(conn, csv_path, batch_size=1000, chunk_size=None):
    """Import courts with progress tracking"""
    table_name = 'search_court'
    logger.info(f"📋 Importing courts from {csv_path}")

    progress = get_progress(conn, table_name, csv_path)
    start_row = progress['last_row_processed'] if progress and progress['status'] != 'completed' else 0

    if progress and progress['status'] == 'completed':
        logger.info(f"✅ Courts already imported ({progress['rows_imported']} rows)")
        return

    if start_row > 0:
        logger.info(f"↻ Resuming from row {start_row}")

    cursor = conn.cursor()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            current_row = 0
            count = progress['rows_imported'] if progress else 0
            skipped = progress['rows_skipped'] if progress else 0

            for row in reader:
                current_row += 1
                if current_row <= start_row:
                    continue
                if chunk_size and count >= chunk_size:
                    break

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
                    update_progress(conn, table_name, csv_path, count, skipped, current_row)
                    logger.info(f"✓ {count:,} courts | skipped {skipped:,}")
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

            update_progress(conn, table_name, csv_path, count, skipped, current_row, 'completed')
            logger.info(f"✅ Imported {count:,} courts (skipped {skipped:,})")

    except Exception as e:
        logger.error(f"❌ Error importing courts: {e}")
        update_progress(conn, table_name, csv_path, count, skipped, current_row, 'error', str(e))
        raise
    finally:
        cursor.close()

def import_dockets(conn, csv_path, batch_size=5000, chunk_size=None):
    """Import dockets with progress tracking and resume capability"""
    table_name = 'search_docket'
    logger.info(f"📋 Importing dockets from {csv_path}")

    progress = get_progress(conn, table_name, csv_path)
    start_row = progress['last_row_processed'] if progress and progress['status'] != 'completed' else 0

    if progress and progress['status'] == 'completed':
        logger.info(f"✅ Dockets already imported ({progress['rows_imported']} rows)")
        return

    if start_row > 0:
        logger.info(f"↻ Resuming from row {start_row:,}")

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM search_court")
    valid_courts = set(row[0] for row in cursor.fetchall())
    logger.info(f"Found {len(valid_courts)} valid courts")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            current_row = 0
            count = progress['rows_imported'] if progress else 0
            skipped = progress['rows_skipped'] if progress else 0
            initial_count = count

            for row in reader:
                current_row += 1
                if current_row <= start_row:
                    continue
                if chunk_size and (count - initial_count) >= chunk_size:
                    logger.info(f"✓ Reached chunk limit of {chunk_size:,}")
                    break

                court_id = row.get('court_id')
                if not court_id or court_id not in valid_courts:
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
                    update_progress(conn, table_name, csv_path, count, skipped, current_row)
                    logger.info(f"✓ {count:,} dockets | skipped {skipped:,} | row {current_row:,}")
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

            status = 'in_progress' if chunk_size and (count - initial_count) >= chunk_size else 'completed'
            update_progress(conn, table_name, csv_path, count, skipped, current_row, status)
            logger.info(f"✅ Imported {count:,} dockets (skipped {skipped:,})")

    except Exception as e:
        logger.error(f"❌ Error importing dockets: {e}")
        update_progress(conn, table_name, csv_path, count, skipped, current_row, 'error', str(e))
        raise
    finally:
        cursor.close()

def import_clusters(conn, csv_path, batch_size=5000, chunk_size=None):
    """Import opinion clusters with progress tracking"""
    table_name = 'search_opinioncluster'
    logger.info(f"📋 Importing opinion clusters from {csv_path}")

    progress = get_progress(conn, table_name, csv_path)
    start_row = progress['last_row_processed'] if progress and progress['status'] != 'completed' else 0

    if progress and progress['status'] == 'completed':
        logger.info(f"✅ Clusters already imported ({progress['rows_imported']} rows)")
        return

    if start_row > 0:
        logger.info(f"↻ Resuming from row {start_row:,}")

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM search_docket")
    valid_dockets = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_dockets):,} valid dockets")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            current_row = 0
            count = progress['rows_imported'] if progress else 0
            skipped = progress['rows_skipped'] if progress else 0
            initial_count = count

            for row in reader:
                current_row += 1
                if current_row <= start_row:
                    continue
                if chunk_size and (count - initial_count) >= chunk_size:
                    logger.info(f"✓ Reached chunk limit of {chunk_size:,}")
                    break

                docket_id = parse_value(row.get('docket_id'), 'docket_id')
                if not docket_id or docket_id not in valid_dockets:
                    skipped += 1
                    continue

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
                except Exception:
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
                        update_progress(conn, table_name, csv_path, count, skipped, current_row)
                        logger.info(f"✓ {count:,} clusters | skipped {skipped:,} | row {current_row:,}")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch failed: {str(batch_error)[:100]}")
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
                    logger.warning(f"⚠️  Final batch failed: {str(batch_error)[:100]}")
                    skipped += len(batch)
                    conn.rollback()

            status = 'in_progress' if chunk_size and (count - initial_count) >= chunk_size else 'completed'
            update_progress(conn, table_name, csv_path, count, skipped, current_row, status)
            logger.info(f"✅ Imported {count:,} clusters (skipped {skipped:,})")

    except Exception as e:
        logger.error(f"❌ Error importing clusters: {e}")
        update_progress(conn, table_name, csv_path, count, skipped, current_row, 'error', str(e))
        raise
    finally:
        cursor.close()

def import_citations(conn, csv_path, batch_size=10000, chunk_size=None):
    """Import citations with progress tracking"""
    table_name = 'search_opinionscited'
    logger.info(f"📋 Importing citations from {csv_path}")

    progress = get_progress(conn, table_name, csv_path)
    start_row = progress['last_row_processed'] if progress and progress['status'] != 'completed' else 0

    if progress and progress['status'] == 'completed':
        logger.info(f"✅ Citations already imported ({progress['rows_imported']} rows)")
        return

    if start_row > 0:
        logger.info(f"↻ Resuming from row {start_row:,}")

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM search_opinion")
    valid_opinions = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_opinions):,} valid opinions")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            current_row = 0
            count = progress['rows_imported'] if progress else 0
            skipped = progress['rows_skipped'] if progress else 0
            initial_count = count

            for row in reader:
                current_row += 1
                if current_row <= start_row:
                    continue
                if chunk_size and (count - initial_count) >= chunk_size:
                    break

                citing_id = parse_value(row.get('citing_opinion_id'), 'citing_opinion_id')
                cited_id = parse_value(row.get('cited_opinion_id'), 'cited_opinion_id')

                if not citing_id or not cited_id or citing_id not in valid_opinions or cited_id not in valid_opinions:
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
                except Exception:
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
                        update_progress(conn, table_name, csv_path, count, skipped, current_row)
                        logger.info(f"✓ {count:,} citations | skipped {skipped:,} | row {current_row:,}")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch failed: {str(batch_error)[:100]}")
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
                except Exception:
                    skipped += len(batch)
                    conn.rollback()

            status = 'in_progress' if chunk_size and (count - initial_count) >= chunk_size else 'completed'
            update_progress(conn, table_name, csv_path, count, skipped, current_row, status)
            logger.info(f"✅ Imported {count:,} citations (skipped {skipped:,})")

    except Exception as e:
        logger.error(f"❌ Error importing citations: {e}")
        update_progress(conn, table_name, csv_path, count, skipped, current_row, 'error', str(e))
        raise
    finally:
        cursor.close()

def import_parentheticals(conn, csv_path, batch_size=10000, chunk_size=None):
    """Import parentheticals with progress tracking"""
    table_name = 'search_parenthetical'
    logger.info(f"📋 Importing parentheticals from {csv_path}")

    progress = get_progress(conn, table_name, csv_path)
    start_row = progress['last_row_processed'] if progress and progress['status'] != 'completed' else 0

    if progress and progress['status'] == 'completed':
        logger.info(f"✅ Parentheticals already imported ({progress['rows_imported']} rows)")
        return

    if start_row > 0:
        logger.info(f"↻ Resuming from row {start_row:,}")

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM search_opinion")
    valid_opinions = set(str(row[0]) for row in cursor.fetchall())
    logger.info(f"Found {len(valid_opinions):,} valid opinions")

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            current_row = 0
            count = progress['rows_imported'] if progress else 0
            skipped = progress['rows_skipped'] if progress else 0
            initial_count = count

            for row in reader:
                current_row += 1
                if current_row <= start_row:
                    continue
                if chunk_size and (count - initial_count) >= chunk_size:
                    break

                try:
                    described_id = parse_value(row.get('described_opinion_id'), 'described_opinion_id')
                    describing_id = parse_value(row.get('describing_opinion_id'), 'describing_opinion_id')

                    if not described_id or not describing_id or described_id not in valid_opinions or describing_id not in valid_opinions:
                        skipped += 1
                        continue

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
                except Exception:
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
                        update_progress(conn, table_name, csv_path, count, skipped, current_row)
                        logger.info(f"✓ {count:,} parentheticals | skipped {skipped:,} | row {current_row:,}")
                    except Exception as batch_error:
                        logger.warning(f"⚠️  Batch failed: {str(batch_error)[:100]}")
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
                except Exception:
                    skipped += len(batch)
                    conn.rollback()

            status = 'in_progress' if chunk_size and (count - initial_count) >= chunk_size else 'completed'
            update_progress(conn, table_name, csv_path, count, skipped, current_row, status)
            logger.info(f"✅ Imported {count:,} parentheticals (skipped {skipped:,})")

    except Exception as e:
        logger.error(f"❌ Error importing parentheticals: {e}")
        update_progress(conn, table_name, csv_path, count, skipped, current_row, 'error', str(e))
        raise
    finally:
        cursor.close()

def show_progress_status(conn):
    """Display current import progress for all tables"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT table_name, csv_file, rows_imported, rows_skipped,
                   last_row_processed, status, updated_at
            FROM import_progress
            ORDER BY updated_at DESC
        """)
        results = cursor.fetchall()

        if not results:
            logger.info("No import progress found")
            return

        logger.info("\n" + "="*80)
        logger.info("IMPORT PROGRESS STATUS")
        logger.info("="*80)
        for row in results:
            table, csv_file, imported, skipped, last_row, status, updated = row
            logger.info(f"\n{table}:")
            logger.info(f"  File: {csv_file}")
            logger.info(f"  Status: {status}")
            logger.info(f"  Imported: {imported:,} rows")
            logger.info(f"  Skipped: {skipped:,} rows")
            logger.info(f"  Last row: {last_row:,}")
            logger.info(f"  Updated: {updated}")
        logger.info("="*80 + "\n")
    finally:
        cursor.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Resumable CSV Import with Progress Tracking')
    parser.add_argument('--courts', help='Path to courts CSV')
    parser.add_argument('--dockets', help='Path to dockets CSV')
    parser.add_argument('--clusters', help='Path to opinion clusters CSV')
    parser.add_argument('--citations', help='Path to citations CSV')
    parser.add_argument('--parentheticals', help='Path to parentheticals CSV')
    parser.add_argument('--all', action='store_true', help='Import all tables in sequence (except opinions)')
    parser.add_argument('--chunk-size', type=int, help='Number of rows to import in this run (enables resumable imports)')
    parser.add_argument('--batch-size', type=int, default=5000, help='Batch size for inserts')
    parser.add_argument('--status', action='store_true', help='Show import progress status')

    args = parser.parse_args()

    db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PRIVATE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        logger.info("✅ Connected successfully")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        sys.exit(1)

    try:
        create_progress_table(conn)

        if args.status:
            show_progress_status(conn)
            return

        if args.all:
            logger.info("🚀 Starting import sequence (opinions will be fetched via API separately)...")
            if os.path.exists('courts-2025-10-31.csv'):
                import_courts(conn, 'courts-2025-10-31.csv', args.batch_size, args.chunk_size)
            if os.path.exists('dockets-2025-10-31.csv'):
                import_dockets(conn, 'dockets-2025-10-31.csv', args.batch_size, args.chunk_size)
            if os.path.exists('opinion-clusters-2025-10-31.csv'):
                import_clusters(conn, 'opinion-clusters-2025-10-31.csv', args.batch_size, args.chunk_size)
            logger.info("⏭️  Skipping opinions - use API batch import instead")
            if os.path.exists('citations-2025-10-31.csv'):
                import_citations(conn, 'citations-2025-10-31.csv', args.batch_size, args.chunk_size)
            if os.path.exists('search_parenthetical-2025-10-31.csv'):
                import_parentheticals(conn, 'search_parenthetical-2025-10-31.csv', args.batch_size, args.chunk_size)
        else:
            if args.courts:
                import_courts(conn, args.courts, args.batch_size, args.chunk_size)
            if args.dockets:
                import_dockets(conn, args.dockets, args.batch_size, args.chunk_size)
            if args.clusters:
                import_clusters(conn, args.clusters, args.batch_size, args.chunk_size)
            if args.citations:
                import_citations(conn, args.citations, args.batch_size, args.chunk_size)
            if args.parentheticals:
                import_parentheticals(conn, args.parentheticals, args.batch_size, args.chunk_size)

        show_progress_status(conn)
        logger.info("🎉 Import complete!")
        logger.info("💡 Use scripts/fetch_opinions_api.py to fetch opinion text via API")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
