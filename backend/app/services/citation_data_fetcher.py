"""
Citation Data Fetcher - Fetch missing case data from CourtListener API

This service ensures opinion data exists in our database before analysis.
If data is missing, it fetches from CourtListener API v4.
"""
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import Opinion, OpinionCluster, Docket, Court, OpinionsCited

# Configure logging
logger = logging.getLogger(__name__)

# CourtListener API configuration
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_API_TOKEN = os.getenv("COURTLISTENER_API_TOKEN", "")
RATE_LIMIT_PER_HOUR = 5000  # CourtListener API limit
REQUEST_DELAY = 0.72  # seconds (to stay under 5000/hour = 1.39 requests/sec)

# Cache for 404s (don't repeatedly try to fetch missing opinions)
_404_cache: Dict[int, datetime] = {}
_404_CACHE_TTL = timedelta(hours=24)


class CourtListenerAPIError(Exception):
    """Base exception for CourtListener API errors"""
    pass


class RateLimitError(CourtListenerAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class OpinionNotFoundError(CourtListenerAPIError):
    """Raised when opinion is not found in CourtListener"""
    pass


def _get_session() -> requests.Session:
    """
    Create a requests session with retry logic

    Returns:
        Configured requests Session
    """
    session = requests.Session()

    # Configure retries
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,  # Wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set headers
    if COURTLISTENER_API_TOKEN:
        session.headers.update({
            "Authorization": f"Token {COURTLISTENER_API_TOKEN}",
            "Accept": "application/json"
        })

    return session


def _check_404_cache(opinion_id: int) -> bool:
    """
    Check if opinion was recently not found (404)

    Args:
        opinion_id: Opinion ID to check

    Returns:
        True if in 404 cache and not expired
    """
    if opinion_id in _404_cache:
        cached_time = _404_cache[opinion_id]
        if datetime.now() - cached_time < _404_CACHE_TTL:
            return True
        else:
            # Expired, remove from cache
            del _404_cache[opinion_id]
    return False


def _add_to_404_cache(opinion_id: int):
    """Add opinion to 404 cache"""
    _404_cache[opinion_id] = datetime.now()


def fetch_opinion_from_api(opinion_id: int) -> Optional[Dict]:
    """
    Fetch opinion data from CourtListener API

    Args:
        opinion_id: CourtListener opinion ID

    Returns:
        Opinion data dict or None if not found

    Raises:
        RateLimitError: If rate limit exceeded
        CourtListenerAPIError: For other API errors
    """
    # Check 404 cache first
    if _check_404_cache(opinion_id):
        logger.debug(f"Opinion {opinion_id} in 404 cache, skipping API call")
        return None

    session = _get_session()
    url = f"{COURTLISTENER_API_BASE}/opinions/{opinion_id}/"

    try:
        logger.info(f"Fetching opinion {opinion_id} from CourtListener API")

        # Rate limiting delay
        time.sleep(REQUEST_DELAY)

        response = session.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Opinion {opinion_id} not found in CourtListener (404)")
            _add_to_404_cache(opinion_id)
            raise OpinionNotFoundError(f"Opinion {opinion_id} not found")
        elif response.status_code == 429:
            logger.error("CourtListener API rate limit exceeded")
            raise RateLimitError("API rate limit exceeded")
        else:
            logger.error(f"CourtListener API error: {response.status_code} - {response.text}")
            raise CourtListenerAPIError(f"API returned {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching opinion {opinion_id}")
        raise CourtListenerAPIError("API request timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching opinion {opinion_id}: {e}")
        raise CourtListenerAPIError(f"Request failed: {e}")


def fetch_cluster_from_api(cluster_id: int) -> Optional[Dict]:
    """
    Fetch opinion cluster data from CourtListener API

    Args:
        cluster_id: CourtListener cluster ID

    Returns:
        Cluster data dict or None if not found

    Raises:
        RateLimitError: If rate limit exceeded
        CourtListenerAPIError: For other API errors
    """
    session = _get_session()
    url = f"{COURTLISTENER_API_BASE}/clusters/{cluster_id}/"

    try:
        logger.info(f"Fetching cluster {cluster_id} from CourtListener API")

        # Rate limiting delay
        time.sleep(REQUEST_DELAY)

        response = session.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Cluster {cluster_id} not found in CourtListener (404)")
            return None
        elif response.status_code == 429:
            logger.error("CourtListener API rate limit exceeded")
            raise RateLimitError("API rate limit exceeded")
        else:
            logger.error(f"CourtListener API error: {response.status_code}")
            raise CourtListenerAPIError(f"API returned {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching cluster {cluster_id}: {e}")
        raise CourtListenerAPIError(f"Request failed: {e}")


def ensure_opinion_exists(opinion_id: int, db: Session) -> Optional[Opinion]:
    """
    Ensure opinion exists in database, fetch from API if missing

    Args:
        opinion_id: Opinion ID
        db: Database session

    Returns:
        Opinion object or None if not found anywhere

    Raises:
        RateLimitError: If API rate limit exceeded
        CourtListenerAPIError: For other API errors
    """
    # Check if opinion already exists in DB
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()

    if opinion:
        logger.debug(f"Opinion {opinion_id} found in database")
        return opinion

    # Opinion not in DB, fetch from API
    logger.info(f"Opinion {opinion_id} not in database, fetching from API")

    try:
        opinion_data = fetch_opinion_from_api(opinion_id)
        if not opinion_data:
            return None

        # Create opinion record (simplified - just basic fields for now)
        # In production, you'd want to fetch and create related cluster/docket/court too
        opinion = Opinion(
            id=opinion_data.get("id"),
            cluster_id=opinion_data.get("cluster"),
            type=opinion_data.get("type", "010lead"),
            author_str=opinion_data.get("author_str"),
            per_curiam=opinion_data.get("per_curiam", False),
            plain_text=opinion_data.get("plain_text"),
            html=opinion_data.get("html"),
            html_with_citations=opinion_data.get("html_with_citations"),
        )

        db.add(opinion)
        db.commit()
        db.refresh(opinion)

        logger.info(f"Opinion {opinion_id} successfully fetched and saved")
        return opinion

    except OpinionNotFoundError:
        logger.warning(f"Opinion {opinion_id} does not exist in CourtListener")
        return None


def ensure_opinion_text(opinion: Opinion, db: Session) -> Optional[str]:
    """
    Ensure opinion has full text, fetch from API if missing

    Priority: plain_text > html > fetch from API

    Args:
        opinion: Opinion object
        db: Database session

    Returns:
        Opinion text (plain text or HTML) or None if unavailable

    Raises:
        RateLimitError: If API rate limit exceeded
        CourtListenerAPIError: For other API errors
    """
    # Check existing text fields
    if opinion.plain_text:
        logger.debug(f"Opinion {opinion.id} has plain_text ({len(opinion.plain_text)} chars)")
        return opinion.plain_text

    if opinion.html:
        logger.debug(f"Opinion {opinion.id} has html ({len(opinion.html)} chars)")
        return opinion.html

    # No text in DB, fetch from API
    logger.info(f"Opinion {opinion.id} missing text, fetching from API")

    try:
        opinion_data = fetch_opinion_from_api(opinion.id)
        if not opinion_data:
            return None

        # Update opinion with text
        plain_text = opinion_data.get("plain_text")
        html = opinion_data.get("html")

        if plain_text:
            opinion.plain_text = plain_text
        if html:
            opinion.html = html

        db.commit()
        db.refresh(opinion)

        # Return best available text
        text = plain_text or html
        if text:
            logger.info(f"Opinion {opinion.id} text fetched ({len(text)} chars)")
        return text

    except OpinionNotFoundError:
        logger.warning(f"Opinion {opinion.id} text not available in CourtListener")
        return None


def get_opinion_text(opinion: Opinion, db: Session, max_length: int = 150000) -> Optional[str]:
    """
    Get opinion text with optional truncation

    Args:
        opinion: Opinion object
        db: Database session
        max_length: Maximum text length (default 150k chars ~37.5k tokens)

    Returns:
        Opinion text (truncated if necessary) or None
    """
    text = ensure_opinion_text(opinion, db)

    if not text:
        return None

    # Truncate if needed
    if len(text) > max_length:
        logger.warning(f"Opinion {opinion.id} text truncated from {len(text)} to {max_length} chars")
        text = text[:max_length] + "\n\n[... Text truncated for API limits ...]"

    return text


def batch_ensure_opinions(opinion_ids: List[int], db: Session) -> Tuple[List[Opinion], List[int]]:
    """
    Ensure multiple opinions exist, fetch missing ones from API

    Args:
        opinion_ids: List of opinion IDs
        db: Database session

    Returns:
        Tuple of (found opinions, missing opinion IDs)

    Note:
        This performs batch DB lookup, but API fetches are sequential
        due to rate limiting requirements
    """
    # Batch query existing opinions
    existing_opinions = db.query(Opinion).filter(Opinion.id.in_(opinion_ids)).all()
    existing_ids = {op.id for op in existing_opinions}

    missing_ids = [id for id in opinion_ids if id not in existing_ids]

    if not missing_ids:
        logger.debug(f"All {len(opinion_ids)} opinions found in database")
        return existing_opinions, []

    logger.info(f"Found {len(existing_opinions)}/{len(opinion_ids)} opinions in DB, fetching {len(missing_ids)} from API")

    # Fetch missing opinions one by one (rate limiting)
    fetched_opinions = []
    still_missing = []

    for opinion_id in missing_ids:
        try:
            opinion = ensure_opinion_exists(opinion_id, db)
            if opinion:
                fetched_opinions.append(opinion)
            else:
                still_missing.append(opinion_id)
        except (RateLimitError, CourtListenerAPIError) as e:
            logger.error(f"Failed to fetch opinion {opinion_id}: {e}")
            still_missing.append(opinion_id)

    all_opinions = existing_opinions + fetched_opinions
    return all_opinions, still_missing


def get_opinion_citations(opinion_id: int, db: Session) -> List[int]:
    """
    Get list of opinion IDs that this opinion cites

    Args:
        opinion_id: Opinion ID
        db: Database session

    Returns:
        List of cited opinion IDs
    """
    citations = db.query(OpinionsCited.cited_opinion_id).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).all()

    return [c.cited_opinion_id for c in citations]
