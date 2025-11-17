"""
Bulk Treatment Analyzer - Analyze and cache treatment for all opinions with parentheticals

This script fetches all opinions that have parentheticals and analyzes their treatment,
caching the results in the citation_treatment table for fast API responses.

Usage:
    export DATABASE_URL="postgresql://..."
    python3 scripts/analyze_treatments_bulk.py --limit 100
"""
import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_batch
import requests
from typing import List, Dict, Any
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API configuration
API_URL = os.environ.get('API_URL', 'https://court-listener-v-production.up.railway.app')

def get_opinions_with_parentheticals(conn, limit: int = None) -> List[int]:
    """
    Get list of opinion IDs that have parentheticals (and thus need treatment analysis)
    """
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT described_opinion_id
        FROM search_parenthetical
        ORDER BY described_opinion_id
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    opinion_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    logger.info(f"Found {len(opinion_ids)} opinions with parentheticals")
    return opinion_ids


def analyze_opinion_via_api(opinion_id: int) -> Dict[str, Any]:
    """
    Analyze opinion treatment via API endpoint
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/treatment/{opinion_id}?use_cache=false",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API error for opinion {opinion_id}: {e}")
        return None


def bulk_analyze_treatments(conn, opinion_ids: List[int], batch_size: int = 10):
    """
    Analyze treatments for multiple opinions in batches
    """
    total = len(opinion_ids)
    analyzed = 0
    cached = 0
    errors = 0

    logger.info(f"Starting bulk analysis of {total} opinions...")

    for i in range(0, total, batch_size):
        batch = opinion_ids[i:i + batch_size]

        for opinion_id in batch:
            try:
                result = analyze_opinion_via_api(opinion_id)

                if result:
                    if result.get('from_cache'):
                        cached += 1
                    else:
                        analyzed += 1
                        logger.info(
                            f"✓ Opinion {opinion_id}: {result['treatment_type']} "
                            f"({result['severity']}, {result['confidence']:.0%} confidence)"
                        )
                else:
                    errors += 1

                # Small delay to avoid overwhelming the API
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error analyzing opinion {opinion_id}: {e}")
                errors += 1

        # Progress update
        progress = min(i + batch_size, total)
        logger.info(f"Progress: {progress}/{total} ({progress/total*100:.1f}%) - Analyzed: {analyzed}, Cached: {cached}, Errors: {errors}")

    return {
        'total': total,
        'analyzed': analyzed,
        'cached': cached,
        'errors': errors
    }


def get_treatment_stats(conn):
    """
    Get statistics about treatments in the database
    """
    cursor = conn.cursor()

    # Total treatments
    cursor.execute("SELECT COUNT(*) FROM citation_treatment")
    total_cached = cursor.fetchone()[0]

    # By severity
    cursor.execute("""
        SELECT severity, COUNT(*)
        FROM citation_treatment
        GROUP BY severity
    """)
    by_severity = dict(cursor.fetchall())

    # By treatment type
    cursor.execute("""
        SELECT treatment_type, COUNT(*)
        FROM citation_treatment
        GROUP BY treatment_type
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    top_treatments = cursor.fetchall()

    cursor.close()

    return {
        'total_cached': total_cached,
        'by_severity': by_severity,
        'top_treatments': top_treatments
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Bulk analyze treatments for opinions')
    parser.add_argument('--limit', type=int, help='Limit number of opinions to analyze')
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
        logger.info("\n📊 Current Treatment Statistics:")
        stats = get_treatment_stats(conn)
        logger.info(f"  Total cached treatments: {stats['total_cached']}")
        logger.info(f"  By severity: {stats['by_severity']}")
        logger.info(f"  Top treatments:")
        for treatment_type, count in stats['top_treatments']:
            logger.info(f"    - {treatment_type}: {count}")

        if args.stats_only:
            return

        # Get opinions to analyze
        opinion_ids = get_opinions_with_parentheticals(conn, limit=args.limit)

        if not opinion_ids:
            logger.info("No opinions with parentheticals found")
            return

        # Analyze treatments
        logger.info(f"\n🔍 Starting analysis (batch size: {args.batch_size})...")
        results = bulk_analyze_treatments(conn, opinion_ids, batch_size=args.batch_size)

        # Final report
        logger.info("\n" + "="*60)
        logger.info("📈 FINAL REPORT")
        logger.info("="*60)
        logger.info(f"Total opinions processed: {results['total']}")
        logger.info(f"Newly analyzed: {results['analyzed']}")
        logger.info(f"Already cached: {results['cached']}")
        logger.info(f"Errors: {results['errors']}")
        logger.info(f"Success rate: {(results['analyzed'] + results['cached']) / results['total'] * 100:.1f}%")

        # Show updated statistics
        logger.info("\n📊 Updated Treatment Statistics:")
        stats = get_treatment_stats(conn)
        logger.info(f"  Total cached treatments: {stats['total_cached']}")
        logger.info(f"  By severity:")
        for severity, count in stats['by_severity'].items():
            logger.info(f"    - {severity}: {count}")
        logger.info(f"  Top treatments:")
        for treatment_type, count in stats['top_treatments']:
            logger.info(f"    - {treatment_type}: {count}")

        logger.info("\n🎉 Bulk analysis complete!")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
