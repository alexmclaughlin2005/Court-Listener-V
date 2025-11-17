"""
Case Search API endpoints
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from app.core.database import get_db
from app.models import OpinionCluster, Opinion, Docket, Court

router = APIRouter()


@router.get("/cases")
async def search_cases(
    q: str = Query(..., min_length=3, description="Search query"),
    court: Optional[str] = Query(None, description="Court ID filter"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    sort: str = Query("relevance", enum=["relevance", "date", "citations"]),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Full-text search across case law

    Searches case names, opinion text, and docket numbers.
    Currently uses basic SQL LIKE matching (can be upgraded to full-text search later).
    """
    # Build base query joining all necessary tables
    query = db.query(
        OpinionCluster.id,
        OpinionCluster.case_name,
        OpinionCluster.case_name_short,
        OpinionCluster.date_filed,
        OpinionCluster.citation_count,
        OpinionCluster.precedential_status,
        OpinionCluster.slug,
        Court.short_name.label("court_name"),
        Court.id.label("court_id")
    ).join(
        Docket, OpinionCluster.docket_id == Docket.id
    ).join(
        Court, Docket.court_id == Court.id
    )

    # Add search filters
    search_term = f"%{q}%"
    query = query.filter(
        or_(
            OpinionCluster.case_name.ilike(search_term),
            OpinionCluster.case_name_short.ilike(search_term),
            Docket.docket_number.ilike(search_term)
        )
    )

    # Add court filter
    if court:
        query = query.filter(Court.id == court)

    # Add date filters
    if date_from:
        query = query.filter(OpinionCluster.date_filed >= date_from)
    if date_to:
        query = query.filter(OpinionCluster.date_filed <= date_to)

    # Apply sorting
    if sort == "date":
        query = query.order_by(desc(OpinionCluster.date_filed))
    elif sort == "citations":
        query = query.order_by(desc(OpinionCluster.citation_count))
    else:  # relevance - for now just use date
        query = query.order_by(desc(OpinionCluster.date_filed))

    # Get total count
    total = query.count()

    # Apply pagination
    results = query.offset(offset).limit(limit).all()

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "id": result.id,
            "case_name": result.case_name,
            "case_name_short": result.case_name_short,
            "date_filed": result.date_filed.isoformat() if result.date_filed else None,
            "citation_count": result.citation_count or 0,
            "precedential_status": result.precedential_status,
            "slug": result.slug,
            "court": {
                "id": result.court_id,
                "name": result.court_name
            }
        })

    return {
        "query": q,
        "results": formatted_results,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    """Get a single case by cluster ID with full details"""
    # Get opinion cluster with related data
    cluster = db.query(OpinionCluster).filter(OpinionCluster.id == case_id).first()

    if not cluster:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get docket and court info
    docket = db.query(Docket).filter(Docket.id == cluster.docket_id).first()
    court = db.query(Court).filter(Court.id == docket.court_id).first() if docket else None

    # Get opinions
    opinions = db.query(Opinion).filter(Opinion.cluster_id == case_id).all()

    # Format opinions
    formatted_opinions = []
    for opinion in opinions:
        formatted_opinions.append({
            "id": opinion.id,
            "type": opinion.type,
            "plain_text": opinion.plain_text[:500] + "..." if opinion.plain_text and len(opinion.plain_text) > 500 else opinion.plain_text,
            "html": opinion.html,
            "extracted_by_ocr": opinion.extracted_by_ocr
        })

    return {
        "id": cluster.id,
        "case_name": cluster.case_name,
        "case_name_short": cluster.case_name_short,
        "case_name_full": cluster.case_name_full,
        "slug": cluster.slug,
        "date_filed": cluster.date_filed.isoformat() if cluster.date_filed else None,
        "date_filed_is_approximate": cluster.date_filed_is_approximate,
        "citation_count": cluster.citation_count or 0,
        "precedential_status": cluster.precedential_status,
        "judges": cluster.judges,
        "docket": {
            "id": docket.id if docket else None,
            "docket_number": docket.docket_number if docket else None,
            "date_filed": docket.date_filed.isoformat() if docket and docket.date_filed else None
        } if docket else None,
        "court": {
            "id": court.id if court else None,
            "short_name": court.short_name if court else None,
            "full_name": court.full_name if court else None
        } if court else None,
        "opinions": formatted_opinions
    }

