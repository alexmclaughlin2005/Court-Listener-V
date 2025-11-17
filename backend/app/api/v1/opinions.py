"""
Opinion endpoints - fetch opinion text from CourtListener API on-demand
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Opinion
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# CourtListener API configuration (v4 is the latest)
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_API_TOKEN = os.getenv("COURTLISTENER_API_TOKEN", "")

class OpinionTextResponse(BaseModel):
    opinion_id: int
    plain_text: Optional[str] = None
    html: Optional[str] = None
    html_with_citations: Optional[str] = None
    source: str  # "database" or "courtlistener_api"
    cached: bool

@router.get("/{opinion_id}/text", response_model=OpinionTextResponse)
async def get_opinion_text(opinion_id: int, db: Session = Depends(get_db)):
    """
    Get opinion text - from database if available, otherwise fetch from CourtListener API
    """
    # Check if opinion exists in database
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()

    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found in database")

    # If we already have text in database, return it
    if opinion.plain_text or opinion.html:
        return OpinionTextResponse(
            opinion_id=opinion_id,
            plain_text=opinion.plain_text,
            html=opinion.html,
            html_with_citations=opinion.html_with_citations,
            source="database",
            cached=True
        )

    # Otherwise, fetch from CourtListener API
    logger.info(f"Fetching opinion {opinion_id} text from CourtListener API")

    if not COURTLISTENER_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="CourtListener API token not configured. Set COURTLISTENER_API_TOKEN environment variable."
        )

    try:
        headers = {
            "Authorization": f"Token {COURTLISTENER_API_TOKEN}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{COURTLISTENER_API_BASE}/opinions/{opinion_id}/",
                headers=headers,
                follow_redirects=True
            )
            response.raise_for_status()

            data = response.json()

            plain_text = data.get('plain_text')
            html = data.get('html')
            html_with_citations = data.get('html_with_citations')

            # Optionally cache the text in database for future requests
            if plain_text or html:
                opinion.plain_text = plain_text
                opinion.html = html
                opinion.html_with_citations = html_with_citations
                db.commit()
                logger.info(f"Cached opinion {opinion_id} text in database")

            return OpinionTextResponse(
                opinion_id=opinion_id,
                plain_text=plain_text,
                html=html,
                html_with_citations=html_with_citations,
                source="courtlistener_api",
                cached=False
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Opinion {opinion_id} not found on CourtListener"
            )
        logger.error(f"CourtListener API error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error fetching from CourtListener: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching opinion text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching opinion text: {str(e)}"
        )

@router.post("/{opinion_id}/fetch-and-cache")
async def fetch_and_cache_opinion(opinion_id: int, db: Session = Depends(get_db)):
    """
    Manually trigger fetching and caching of opinion text from CourtListener
    """
    result = await get_opinion_text(opinion_id, db)
    return {
        "status": "success",
        "opinion_id": opinion_id,
        "cached": True,
        "has_text": bool(result.plain_text or result.html)
    }

@router.get("/{opinion_id}/status")
def check_opinion_text_status(opinion_id: int, db: Session = Depends(get_db)):
    """
    Check if opinion text is available in database or needs to be fetched
    """
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()

    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    return {
        "opinion_id": opinion_id,
        "has_plain_text": bool(opinion.plain_text),
        "has_html": bool(opinion.html),
        "text_length": len(opinion.plain_text) if opinion.plain_text else 0,
        "needs_fetch": not (opinion.plain_text or opinion.html)
    }
