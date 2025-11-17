#!/usr/bin/env python3
"""
Optimized Bulk Treatment Analyzer - Directly processes parentheticals from database

This script processes parentheticals directly from the database without API calls,
making it much faster for bulk analysis of millions of parentheticals.

Usage:
    export DATABASE_URL="postgresql://..."
    python3 scripts/analyze_treatments_bulk_optimized.py --batch-size 10000 --limit 100000
"""
import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_batch
import re
from typing import List, Dict, Tuple
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Treatment classification (copied from treatment_classifier.py for standalone use)

class TreatmentType(str, Enum):
    OVERRULED = "overruled"
    REVERSED = "reversed"
    VACATED = "vacated"
    ABROGATED = "abrogated"
    SUPERSEDED = "superseded"
    QUESTIONED = "questioned"
    CRITICIZED = "criticized"
    AFFIRMED = "affirmed"
    FOLLOWED = "followed"
    DISTINGUISHED = "distinguished"
    CITED = "cited"
    UNKNOWN = "unknown"

class Severity(str, Enum):
    NEGATIVE = "negative"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

NEGATIVE_KEYWORDS = {
    'overruled': 10, 'overruling': 10, 'overrule': 10,
    'abrogated': 10, 'abrogating': 10,
    'reversed': 9, 'reversing': 9,
    'vacated': 9, 'vacating': 9,
    'superseded': 9,
    'disapproved': 8, 'disapproving': 8,
    'rejected': 7, 'rejecting': 7,
    'questioned': 6, 'questioning': 6,
    'doubted': 6,
    'criticized': 5, 'criticizing': 5,
    'limited': 4, 'limiting': 4,
    'narrowed': 4, 'narrowing': 4,
}

POSITIVE_KEYWORDS = {
    'affirmed': 8, 'affirming': 8,
    'followed': 7, 'following': 7,
    'adopted': 7, 'adopting': 7,
    'approved': 6, 'approving': 6,
    'applied': 5, 'applying': 5,
    'cited with approval': 8,
    'endorsed': 6, 'endorsing': 6,
    'agreed': 5, 'agreeing': 5,
}

NEUTRAL_KEYWORDS = {
    'distinguished': 5, 'distinguishing': 5,
    'explained': 3, 'explaining': 3,
    'discussed': 2, 'discussing': 2,
    'cited': 1, 'citing': 1,
    'mentioned': 1, 'mentioning': 1,
    'referenced': 1, 'referencing': 1,
}

def find_keyword_scores(text: str) -> Tuple[int, int, int]:
    """
    Find keyword scores in text
    Returns: (negative_score, positive_score, neutral_score)
    """
    text_lower = text.lower()

    negative_score = sum(score for keyword, score in NEGATIVE_KEYWORDS.items()
                        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))

    positive_score = sum(score for keyword, score in POSITIVE_KEYWORDS.items()
                        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))

    neutral_score = sum(score for keyword, score in NEUTRAL_KEYWORDS.items()
                       if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))

    return negative_score, positive_score, neutral_score

def classify_treatment(negative_score: int, positive_score: int, neutral_score: int,
                       negative_count: int, positive_count: int) -> Tuple[str, str, float]:
    """
    Classify treatment based on aggregated scores
    Returns: (treatment_type, severity, confidence) - uppercase enum values
    """
    # Determine severity
    if negative_score > 0 or negative_count > 0:
        severity = "NEGATIVE"

        # Determine specific treatment type based on strongest negative signal
        if negative_score >= 10:
            treatment_type = "OVERRULED"
        elif negative_score >= 9:
            treatment_type = "REVERSED"
        elif negative_score >= 6:
            treatment_type = "QUESTIONED"
        else:
            treatment_type = "CRITICIZED"

        confidence = min(1.0, 0.6 + (negative_count * 0.1))

    elif positive_score > neutral_score:
        severity = "POSITIVE"

        if positive_score >= 8:
            treatment_type = "AFFIRMED"
        else:
            treatment_type = "FOLLOWED"

        confidence = min(1.0, 0.4 + (positive_count * 0.05))

    else:
        severity = "NEUTRAL"
        treatment_type = "CITED"
        confidence = 0.3

    return treatment_type, severity, confidence

def get_opinions_to_analyze(conn, limit: int = None, offset: int = 0, force_reanalyze: bool = False) -> List[int]:
    """
    Get opinion IDs that need treatment analysis
    Only includes opinions that actually exist in our database

    Args:
        force_reanalyze: If True, re-analyze opinions that don't have evidence
    """
    cursor = conn.cursor()

    if force_reanalyze:
        # Get opinions that need evidence added (either no treatment or no evidence)
        query = """
            SELECT DISTINCT p.described_opinion_id
            FROM search_parenthetical p
            INNER JOIN search_opinion o ON o.id = p.described_opinion_id
            LEFT JOIN citation_treatment ct ON ct.opinion_id = p.described_opinion_id
            WHERE ct.opinion_id IS NULL OR ct.evidence IS NULL
            ORDER BY p.described_opinion_id
        """
    else:
        # Get opinions with parentheticals that don't have cached treatment
        query = """
            SELECT DISTINCT p.described_opinion_id
            FROM search_parenthetical p
            INNER JOIN search_opinion o ON o.id = p.described_opinion_id
            LEFT JOIN citation_treatment ct ON ct.opinion_id = p.described_opinion_id
            WHERE ct.opinion_id IS NULL
            ORDER BY p.described_opinion_id
        """

    if limit:
        query += f" LIMIT {limit}"

    if offset:
        query += f" OFFSET {offset}"

    cursor.execute(query)
    opinion_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    return opinion_ids

def find_keywords_in_text(text: str) -> Dict[str, List[str]]:
    """
    Find specific keywords in text and return by category
    Returns: {'negative': [...], 'positive': [...], 'neutral': [...]}
    """
    text_lower = text.lower()
    found = {'negative': [], 'positive': [], 'neutral': []}

    for keyword in NEGATIVE_KEYWORDS.keys():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            found['negative'].append(keyword)

    for keyword in POSITIVE_KEYWORDS.keys():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            found['positive'].append(keyword)

    for keyword in NEUTRAL_KEYWORDS.keys():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            found['neutral'].append(keyword)

    return found

def analyze_opinion_batch(conn, opinion_ids: List[int]) -> List[Dict]:
    """
    Analyze a batch of opinions and return treatment results with evidence
    """
    cursor = conn.cursor()

    # Fetch all parentheticals for these opinions with describing opinion ID
    cursor.execute("""
        SELECT described_opinion_id, text, describing_opinion_id, score
        FROM search_parenthetical
        WHERE described_opinion_id = ANY(%s)
    """, (opinion_ids,))

    # Group parentheticals by opinion
    opinion_parentheticals = {}
    for opinion_id, text, describing_id, score in cursor.fetchall():
        if opinion_id not in opinion_parentheticals:
            opinion_parentheticals[opinion_id] = []
        opinion_parentheticals[opinion_id].append({
            'text': text,
            'describing_opinion_id': describing_id,
            'score': score
        })

    cursor.close()

    # Analyze each opinion
    results = []
    for opinion_id in opinion_ids:
        parentheticals = opinion_parentheticals.get(opinion_id, [])

        if not parentheticals:
            continue

        # Aggregate scores and collect evidence
        total_negative = 0
        total_positive = 0
        total_neutral = 0
        negative_count = 0
        positive_count = 0
        neutral_count = 0

        # Track significant examples for evidence
        negative_examples = []
        positive_examples = []

        for p in parentheticals:
            text = p['text']
            neg, pos, neu = find_keyword_scores(text)
            total_negative += neg
            total_positive += pos
            total_neutral += neu

            # Find specific keywords for evidence
            keywords = find_keywords_in_text(text)

            if neg > 0:
                negative_count += 1
                negative_examples.append({
                    'text': text[:300],  # Truncate to 300 chars
                    'keywords': keywords['negative'],
                    'score': neg,
                    'describing_opinion_id': p['describing_opinion_id']
                })
            elif pos > 0:
                positive_count += 1
                positive_examples.append({
                    'text': text[:300],
                    'keywords': keywords['positive'],
                    'score': pos,
                    'describing_opinion_id': p['describing_opinion_id']
                })
            else:
                neutral_count += 1

        # Classify overall treatment
        treatment_type, severity, confidence = classify_treatment(
            total_negative, total_positive, total_neutral,
            negative_count, positive_count
        )

        # Sort examples by score and take top 5
        negative_examples.sort(key=lambda x: x['score'], reverse=True)
        positive_examples.sort(key=lambda x: x['score'], reverse=True)

        # Build evidence object
        evidence = {
            'summary': f"{treatment_type} based on {negative_count} negative, {positive_count} positive, {neutral_count} neutral parentheticals",
            'negative_examples': negative_examples[:5],  # Top 5 negative
            'positive_examples': positive_examples[:5],  # Top 5 positive
            'total_negative_score': total_negative,
            'total_positive_score': total_positive
        }

        results.append({
            'opinion_id': opinion_id,
            'treatment_type': treatment_type,
            'severity': severity,
            'confidence': confidence,
            'negative_count': negative_count,
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'total_parentheticals': len(parentheticals),
            'evidence': evidence
        })

    return results

def save_treatments(conn, results: List[Dict]) -> int:
    """
    Save treatment results to database with evidence
    """
    if not results:
        return 0

    cursor = conn.cursor()

    try:
        import json

        # Use UPSERT to handle duplicates
        values = [
            (
                r['opinion_id'],
                r['treatment_type'],
                r['severity'],
                r['confidence'],
                r['negative_count'],
                r['positive_count'],
                r['neutral_count'],
                json.dumps(r['evidence'])  # Convert evidence dict to JSON
            )
            for r in results
        ]

        execute_batch(cursor, """
            INSERT INTO citation_treatment
            (opinion_id, treatment_type, severity, confidence,
             negative_count, positive_count, neutral_count,
             evidence, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (opinion_id)
            DO UPDATE SET
                treatment_type = EXCLUDED.treatment_type,
                severity = EXCLUDED.severity,
                confidence = EXCLUDED.confidence,
                negative_count = EXCLUDED.negative_count,
                positive_count = EXCLUDED.positive_count,
                neutral_count = EXCLUDED.neutral_count,
                evidence = EXCLUDED.evidence,
                last_updated = NOW()
        """, values)

        conn.commit()
        return len(results)

    except Exception as e:
        logger.error(f"Error saving treatments: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()

def get_stats(conn):
    """Get current statistics"""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM citation_treatment")
    total_cached = cursor.fetchone()[0]

    cursor.execute("""
        SELECT severity, COUNT(*)
        FROM citation_treatment
        GROUP BY severity
    """)
    by_severity = dict(cursor.fetchall())

    cursor.execute("""
        SELECT COUNT(DISTINCT described_opinion_id)
        FROM search_parenthetical
    """)
    total_with_parentheticals = cursor.fetchone()[0]

    cursor.close()

    return {
        'total_cached': total_cached,
        'by_severity': by_severity,
        'total_with_parentheticals': total_with_parentheticals,
        'remaining': total_with_parentheticals - total_cached
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Optimized bulk treatment analysis')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of opinions to process at once')
    parser.add_argument('--limit', type=int,
                       help='Total number of opinions to analyze')
    parser.add_argument('--offset', type=int, default=0,
                       help='Skip first N opinions')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show statistics')
    parser.add_argument('--force-reanalyze', action='store_true',
                       help='Re-analyze opinions that lack evidence')

    args = parser.parse_args()

    # Connect to database
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info("Connecting to database...")
    conn = psycopg2.connect(db_url)

    try:
        # Show stats
        stats = get_stats(conn)
        logger.info("=" * 80)
        logger.info("Current Statistics:")
        logger.info(f"  Total opinions with parentheticals: {stats['total_with_parentheticals']:,}")
        logger.info(f"  Already analyzed: {stats['total_cached']:,}")
        logger.info(f"  Remaining to analyze: {stats['remaining']:,}")
        logger.info(f"  By severity: {stats['by_severity']}")
        logger.info("=" * 80)

        if args.stats_only:
            return

        # Get opinions to analyze
        mode = "with missing evidence" if args.force_reanalyze else "without treatment"
        logger.info(f"Finding opinions to analyze {mode} (limit={args.limit}, offset={args.offset})...")
        opinion_ids = get_opinions_to_analyze(conn, limit=args.limit, offset=args.offset, force_reanalyze=args.force_reanalyze)

        if not opinion_ids:
            logger.info("No opinions need analysis!")
            return

        total_to_analyze = len(opinion_ids)
        logger.info(f"Found {total_to_analyze:,} opinions to analyze")

        # Process in batches
        analyzed_count = 0
        batch_size = args.batch_size

        logger.info(f"Starting analysis (batch size: {batch_size})...")

        for i in range(0, total_to_analyze, batch_size):
            batch = opinion_ids[i:i + batch_size]

            # Analyze batch
            results = analyze_opinion_batch(conn, batch)

            # Save results
            saved = save_treatments(conn, results)
            analyzed_count += saved

            # Progress report
            progress = min(i + batch_size, total_to_analyze)
            logger.info(
                f"Progress: {progress:,}/{total_to_analyze:,} ({progress/total_to_analyze*100:.1f}%) | "
                f"Analyzed: {analyzed_count:,}"
            )

        # Final stats
        final_stats = get_stats(conn)
        logger.info("=" * 80)
        logger.info("Final Statistics:")
        logger.info(f"  Newly analyzed: {analyzed_count:,}")
        logger.info(f"  Total cached: {final_stats['total_cached']:,}")
        logger.info(f"  Remaining: {final_stats['remaining']:,}")
        logger.info(f"  By severity: {final_stats['by_severity']}")
        logger.info("=" * 80)
        logger.info("Analysis complete!")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
