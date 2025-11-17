"""
Import citations from CourtListener API

Uses the CourtListener REST API to fetch citation data for opinions
and populate the local database.

Usage:
    export DATABASE_URL="postgresql://..."
    python3 scripts/import_citations_api.py --limit 100 --batch-size 10
"""
import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_batch
import requests
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CourtListener API configuration
CL_API_BASE = "https://www.courtlistener.com/api/rest/v3"
CL_API_TOKEN = os.environ.get('COURTLISTENER_API_TOKEN', '')


def get_api_headers():
    """Get headers for CourtListener API requests"""
    headers = {
        'User-Agent': 'CourtListener Case Law API (educational project)'
    }
    if CL_API_TOKEN:
        headers['Authorization'] = f'Token {CL_API_TOKEN}'
    return headers


def get_local_opinion_ids(conn, limit: int = None) -> List[int]:
    """
    Get list of opinion IDs from local database that need citation data
    """
    cursor = conn.cursor()

    # Get opinions that don't have any citations yet
    query = """
        SELECT DISTINCT o.id
        FROM search_opinion o
        WHERE NOT EXISTS (
            SELECT 1 FROM search_opinionscited oc
            WHERE oc.citing_opinion_id = o.id
        )
        ORDER BY o.id
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    opinion_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    logger.info(f"Found {len(opinion_ids)} opinions without citation data")
    return opinion_ids


def fetch_opinion_citations(opinion_id: int) -> Dict[str, Any]:
    """
    Fetch citation data for an opinion from CourtListener API
    """
    try:
        # Fetch the opinion details which includes citations
        url = f"{CL_API_BASE}/opinions/{opinion_id}/"
        response = requests.get(url, headers=get_api_headers(), timeout=10)

        if response.status_code == 404:
            logger.debug(f"Opinion {opinion_id} not found in API")
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"API error for opinion {opinion_id}: {e}")
        return None


def extract_citations(opinion_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract citation information from opinion API response
    """
    if not opinion_data:
        return []

    citations = []
    opinion_id = opinion_data.get('id')

    # Extract citations from opinions_cited field
    opinions_cited = opinion_data.get('opinions_cited', [])

    for cited_url in opinions_cited:
        # Extract opinion ID from URL (e.g., "https://www.courtlistener.com/api/rest/v3/opinions/123456/")
        try:
            cited_id = int(cited_url.rstrip('/').split('/')[-1])
            citations.append({
                'citing_opinion_id': opinion_id,
                'cited_opinion_id': cited_id,
                'depth': 1  # Direct citation
            })
        except (ValueError, IndexError):
            logger.warning(f"Could not parse cited opinion URL: {cited_url}")
            continue

    return citations


def import_citations_batch(conn, citations: List[Dict[str, Any]]) -> int:
    """
    Import a batch of citations into the database
    """
    if not citations:
        return 0

    cursor = conn.cursor()

    # Filter citations to only include those where both opinions exist in our database
    cursor.execute("""
        SELECT id FROM search_opinion
        WHERE id = ANY(%s)
    """, ([c['cited_opinion_id'] for c in citations],))

    valid_cited_ids = set(row[0] for row in cursor.fetchall())

    valid_citations = [
        c for c in citations
        if c['cited_opinion_id'] in valid_cited_ids
    ]

    if not valid_citations:
        cursor.close()
        return 0

    # Insert citations
    insert_query = """
        INSERT INTO search_opinionscited (citing_opinion_id, cited_opinion_id, depth)
        VALUES (%(citing_opinion_id)s, %(cited_opinion_id)s, %(depth)s)
        ON CONFLICT (citing_opinion_id, cited_opinion_id) DO NOTHING
    """

    try:
        execute_batch(cursor, insert_query, valid_citations, page_size=1000)
        conn.commit()
        inserted = len(valid_citations)
        cursor.close()
        return inserted
    except Exception as e:
        conn.rollback()
        cursor.close()
        logger.error(f"Error inserting citations: {e}")
        return 0


def bulk_import_citations(conn, opinion_ids: List[int], batch_size: int = 10):
    """
    Import citations for multiple opinions in batches
    """
    total = len(opinion_ids)
    imported = 0
    skipped = 0
    errors = 0

    logger.info(f"Starting citation import for {total} opinions...")

    all_citations = []

    for i, opinion_id in enumerate(opinion_ids):
        try:
            # Fetch opinion data from API
            opinion_data = fetch_opinion_citations(opinion_id)

            if opinion_data:
                # Extract citations
                citations = extract_citations(opinion_data)
                all_citations.extend(citations)

                if citations:
                    logger.info(f"✓ Opinion {opinion_id}: Found {len(citations)} citations")
                else:
                    skipped += 1
            else:
                skipped += 1

            # Import in batches
            if len(all_citations) >= batch_size * 10:
                count = import_citations_batch(conn, all_citations)
                imported += count
                logger.info(f"Imported {count} citations (total: {imported})")
                all_citations = []

            # Rate limiting - CourtListener API has rate limits
            time.sleep(0.1)  # 10 requests per second

            # Progress update
            if (i + 1) % batch_size == 0:
                progress = i + 1
                logger.info(f"Progress: {progress}/{total} ({progress/total*100:.1f}%) - Imported: {imported}, Skipped: {skipped}, Errors: {errors}")

        except Exception as e:
            logger.error(f"Error processing opinion {opinion_id}: {e}")
            errors += 1

    # Import remaining citations
    if all_citations:
        count = import_citations_batch(conn, all_citations)
        imported += count
        logger.info(f"Imported final batch: {count} citations")

    return {
        'total': total,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }


def get_citation_stats(conn):
    """
    Get statistics about citations in the database
    """
    cursor = conn.cursor()

    # Total citations
    cursor.execute("SELECT COUNT(*) FROM search_opinionscited")
    total_citations = cursor.fetchone()[0]

    # Opinions with citations
    cursor.execute("""
        SELECT COUNT(DISTINCT citing_opinion_id)
        FROM search_opinionscited
    """)
    opinions_with_citations = cursor.fetchone()[0]

    # Most cited opinions
    cursor.execute("""
        SELECT cited_opinion_id, COUNT(*) as citation_count
        FROM search_opinionscited
        GROUP BY cited_opinion_id
        ORDER BY citation_count DESC
        LIMIT 10
    """)
    top_cited = cursor.fetchall()

    cursor.close()

    return {
        'total_citations': total_citations,
        'opinions_with_citations': opinions_with_citations,
        'top_cited': top_cited
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import citations from CourtListener API')
    parser.add_argument('--limit', type=int, help='Limit number of opinions to process')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    parser.add_argument('--stats-only', action='store_true', help='Only show statistics')

    args = parser.parse_args()

    # Get DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
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
        # Show current statistics
        logger.info("\n📊 Current Citation Statistics:")
        stats = get_citation_stats(conn)
        logger.info(f"  Total citations: {stats['total_citations']}")
        logger.info(f"  Opinions with citations: {stats['opinions_with_citations']}")
        logger.info(f"  Top 10 most cited opinions:")
        for cited_id, count in stats['top_cited']:
            logger.info(f"    - Opinion {cited_id}: {count} citations")

        if args.stats_only:
            return

        # Get opinions to process
        opinion_ids = get_local_opinion_ids(conn, limit=args.limit)

        if not opinion_ids:
            logger.info("No opinions need citation data")
            return

        # Import citations
        logger.info(f"\n🔍 Starting citation import (batch size: {args.batch_size})...")
        results = bulk_import_citations(conn, opinion_ids, batch_size=args.batch_size)

        # Final report
        logger.info("\n" + "="*60)
        logger.info("📈 FINAL REPORT")
        logger.info("="*60)
        logger.info(f"Total opinions processed: {results['total']}")
        logger.info(f"Citations imported: {results['imported']}")
        logger.info(f"Opinions skipped (no citations): {results['skipped']}")
        logger.info(f"Errors: {results['errors']}")
        if results['total'] > 0:
            logger.info(f"Success rate: {(results['total'] - results['errors']) / results['total'] * 100:.1f}%")

        # Show updated statistics
        logger.info("\n📊 Updated Citation Statistics:")
        stats = get_citation_stats(conn)
        logger.info(f"  Total citations: {stats['total_citations']}")
        logger.info(f"  Opinions with citations: {stats['opinions_with_citations']}")

        logger.info("\n🎉 Citation import complete!")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
