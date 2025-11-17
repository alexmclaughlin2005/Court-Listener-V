"""
Citation Sync API - On-demand citation fetching from CourtListener
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Opinion, OpinionsCited
import os
import requests
import logging

router = APIRouter()
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


@router.post("/sync/{opinion_id}")
async def sync_opinion_citations(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch and import citations for a specific opinion from CourtListener API

    This endpoint:
    1. Checks if citations already exist
    2. Fetches from CourtListener API if needed
    3. Imports valid citations (where cited opinions exist locally)
    4. Returns status and counts
    """

    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

    # Check existing citations
    existing_count = db.query(OpinionsCited).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).count()

    # If we already have citations, return early
    if existing_count > 0:
        return {
            "opinion_id": opinion_id,
            "status": "already_synced",
            "existing_citations": existing_count,
            "new_citations": 0,
            "message": "Citations already exist for this opinion"
        }

    # Fetch from CourtListener API
    try:
        url = f"{CL_API_BASE}/opinions/{opinion_id}/"
        response = requests.get(url, headers=get_api_headers(), timeout=10)

        if response.status_code == 404:
            return {
                "opinion_id": opinion_id,
                "status": "not_found_in_api",
                "existing_citations": 0,
                "new_citations": 0,
                "message": "Opinion not found in CourtListener API"
            }

        response.raise_for_status()
        opinion_data = response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"API error for opinion {opinion_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch from CourtListener API: {str(e)}"
        )

    # Extract citations
    opinions_cited = opinion_data.get('opinions_cited', [])

    if not opinions_cited:
        return {
            "opinion_id": opinion_id,
            "status": "no_citations",
            "existing_citations": 0,
            "new_citations": 0,
            "message": "No citations found in API response"
        }

    # Parse cited opinion IDs
    cited_ids = []
    for cited_url in opinions_cited:
        try:
            cited_id = int(cited_url.rstrip('/').split('/')[-1])
            cited_ids.append(cited_id)
        except (ValueError, IndexError):
            logger.warning(f"Could not parse cited opinion URL: {cited_url}")
            continue

    if not cited_ids:
        return {
            "opinion_id": opinion_id,
            "status": "no_valid_citations",
            "existing_citations": 0,
            "new_citations": 0,
            "message": "No valid citation IDs could be parsed"
        }

    # Check which cited opinions exist in our database
    valid_cited_ids = set(
        row[0] for row in db.query(Opinion.id).filter(Opinion.id.in_(cited_ids)).all()
    )

    if not valid_cited_ids:
        return {
            "opinion_id": opinion_id,
            "status": "no_local_matches",
            "existing_citations": 0,
            "new_citations": 0,
            "api_citations_found": len(cited_ids),
            "message": "Citations found in API but cited opinions don't exist in local database"
        }

    # Import citations
    new_citations = []
    for cited_id in valid_cited_ids:
        citation = OpinionsCited(
            citing_opinion_id=opinion_id,
            cited_opinion_id=cited_id,
            depth=1
        )
        new_citations.append(citation)

    try:
        db.bulk_save_objects(new_citations)
        db.commit()

        return {
            "opinion_id": opinion_id,
            "status": "success",
            "existing_citations": 0,
            "new_citations": len(new_citations),
            "api_citations_found": len(cited_ids),
            "local_matches": len(valid_cited_ids),
            "message": f"Successfully imported {len(new_citations)} citations"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Database error importing citations for opinion {opinion_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import citations: {str(e)}"
        )


@router.get("/check/{opinion_id}")
async def check_citation_status(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if an opinion has citations in the database

    Returns:
    - has_citations: boolean
    - citation_count: number of citations
    - needs_sync: whether we should try fetching from API
    """

    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

    # Count citations
    citation_count = db.query(OpinionsCited).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).count()

    return {
        "opinion_id": opinion_id,
        "has_citations": citation_count > 0,
        "citation_count": citation_count,
        "needs_sync": citation_count == 0
    }
