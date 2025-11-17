#!/usr/bin/env python3
"""
Fetch and cache opinion text from CourtListener API for all opinions in database.

This script:
1. Gets all opinion IDs from your database that don't have text
2. Fetches text from CourtListener API (respecting rate limits)
3. Caches the text in your database

Usage:
    python scripts/fetch_all_opinions.py --limit 1000 --batch-size 100
"""
import os
import sys
import time
import logging
import httpx
import psycopg2
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CourtListener API configuration
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
RATE_LIMIT_DELAY = 0.72  # 5000 requests/hour = 1.39 requests/second = 0.72s between requests

def fetch_opinion_text(opinion_id: int, api_token: str) -> Optional[dict]:
    """Fetch opinion text from CourtListener API"""
    headers = {
        "Authorization": f"Token {api_token}"
    }

    try:
        response = httpx.get(
            f"{COURTLISTENER_API_BASE}/opinions/{opinion_id}/",
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Opinion {opinion_id} not found on CourtListener (404)")
            return None
        elif e.response.status_code == 429:
            logger.error(f"Rate limit exceeded (429). Increase delay between requests.")
            return None
        else:
            logger.error(f"HTTP error {e.response.status_code} for opinion {opinion_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching opinion {opinion_id}: {e}")
        return None

def update_opinion_in_db(conn, opinion_id: int, data: dict):
    """Update opinion text and metadata in database"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE search_opinion
            SET plain_text = %s,
                html = %s,
                html_with_citations = %s,
                download_url = %s,
                sha1 = %s,
                extracted_by_ocr = %s,
                date_modified = NOW()
            WHERE id = %s
        """, (
            data.get('plain_text'),
            data.get('html'),
            data.get('html_with_citations'),
            data.get('download_url'),
            data.get('sha1'),
            data.get('extracted_by_ocr'),
            opinion_id
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating opinion {opinion_id} in database: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def get_opinions_without_text(conn, limit: Optional[int] = None):
    """Get opinion IDs that don't have text"""
    cursor = conn.cursor()

    query = """
        SELECT id
        FROM search_opinion
        WHERE (plain_text IS NULL OR plain_text = '')
          AND (html IS NULL OR html = '')
        ORDER BY id
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    opinion_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    return opinion_ids

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fetch opinion text from CourtListener API')
    parser.add_argument('--limit', type=int, help='Limit number of opinions to fetch')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of opinions to fetch before reporting progress')
    parser.add_argument('--start-from', type=int, help='Start from specific opinion ID')
    parser.add_argument('--database-url', help='Database URL (or use DATABASE_URL env var)')
    parser.add_argument('--api-token', help='CourtListener API token (or use COURTLISTENER_API_TOKEN env var)')

    args = parser.parse_args()

    # Get configuration
    database_url = args.database_url or os.getenv('DATABASE_URL')
    api_token = args.api_token or os.getenv('COURTLISTENER_API_TOKEN')

    if not database_url:
        logger.error("DATABASE_URL not provided. Use --database-url or set DATABASE_URL environment variable")
        sys.exit(1)

    if not api_token:
        logger.error("CourtListener API token not provided. Use --api-token or set COURTLISTENER_API_TOKEN environment variable")
        sys.exit(1)

    # Connect to database
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(database_url)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Get opinions without text
    logger.info("Finding opinions without text...")
    opinion_ids = get_opinions_without_text(conn, limit=args.limit)

    if args.start_from:
        opinion_ids = [oid for oid in opinion_ids if oid >= args.start_from]

    total_opinions = len(opinion_ids)
    logger.info(f"Found {total_opinions} opinions without text")

    if total_opinions == 0:
        logger.info("All opinions already have text!")
        conn.close()
        return

    # Estimate time
    estimated_seconds = total_opinions * RATE_LIMIT_DELAY
    estimated_hours = estimated_seconds / 3600
    logger.info(f"Estimated time: {estimated_hours:.1f} hours (respecting 5000 req/hour rate limit)")

    # Fetch and cache opinions
    logger.info("Starting to fetch opinions from CourtListener API...")
    logger.info(f"Rate limit: {RATE_LIMIT_DELAY:.2f}s between requests")

    fetched = 0
    cached = 0
    not_found = 0
    errors = 0
    start_time = time.time()

    for i, opinion_id in enumerate(opinion_ids, 1):
        # Fetch from API
        data = fetch_opinion_text(opinion_id, api_token)
        fetched += 1

        if data is None:
            not_found += 1
        elif data.get('plain_text') or data.get('html'):
            # Update database with full data
            if update_opinion_in_db(conn, opinion_id, data):
                cached += 1
            else:
                errors += 1
        else:
            not_found += 1

        # Progress reporting
        if i % args.batch_size == 0 or i == total_opinions:
            elapsed = time.time() - start_time
            rate = fetched / elapsed if elapsed > 0 else 0
            remaining = total_opinions - i
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_hours = eta_seconds / 3600

            logger.info(
                f"Progress: {i}/{total_opinions} ({i/total_opinions*100:.1f}%) | "
                f"Cached: {cached} | Not found: {not_found} | Errors: {errors} | "
                f"Rate: {rate:.2f}/s | ETA: {eta_hours:.1f}h"
            )

        # Rate limiting
        if i < total_opinions:  # Don't delay after last request
            time.sleep(RATE_LIMIT_DELAY)

    # Final summary
    elapsed = time.time() - start_time
    logger.info("=" * 80)
    logger.info("✅ Fetch complete!")
    logger.info(f"Total opinions processed: {fetched}")
    logger.info(f"Successfully cached: {cached}")
    logger.info(f"Not found on CourtListener: {not_found}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Total time: {elapsed/3600:.2f} hours")
    logger.info(f"Average rate: {fetched/elapsed:.2f} requests/second")
    logger.info("=" * 80)

    conn.close()

if __name__ == '__main__':
    main()
