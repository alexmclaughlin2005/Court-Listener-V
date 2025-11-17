"""
Treatment API - Citation treatment detection endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models import Opinion, Parenthetical, CitationTreatment, OpinionCluster
from app.models.citation_treatment import TreatmentType, Severity
from app.services.treatment_classifier import analyze_opinion_treatment, TreatmentSummary

router = APIRouter()


@router.get("/{opinion_id}")
async def get_treatment(
    opinion_id: int,
    db: Session = Depends(get_db),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get treatment analysis for an opinion

    Returns:
        - Overall treatment status (OVERRULED, AFFIRMED, etc.)
        - Severity (NEGATIVE, POSITIVE, NEUTRAL)
        - Confidence score
        - Count breakdown by treatment type
        - Significant treatment examples
    """
    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Check cache first
    if use_cache:
        cached = db.query(CitationTreatment).filter(
            CitationTreatment.opinion_id == opinion_id
        ).first()

        if cached:
            # Handle enum values - they might be stored as strings or enum objects
            treatment_type_val = cached.treatment_type.value if hasattr(cached.treatment_type, 'value') else str(cached.treatment_type)
            severity_val = cached.severity.value if hasattr(cached.severity, 'value') else str(cached.severity)

            # Safely get evidence field (may not exist in old cached records)
            try:
                evidence = cached.evidence if hasattr(cached, 'evidence') and cached.evidence else None
            except Exception:
                evidence = None

            return {
                "opinion_id": opinion_id,
                "treatment_type": treatment_type_val,
                "severity": severity_val,
                "confidence": cached.confidence,
                "summary": {
                    "negative": cached.negative_count,
                    "positive": cached.positive_count,
                    "neutral": cached.neutral_count
                },
                "evidence": evidence,
                "last_updated": cached.last_updated.isoformat() if cached.last_updated else None,
                "from_cache": True
            }

    # Get parentheticals describing this opinion
    parentheticals = db.query(Parenthetical).filter(
        Parenthetical.described_opinion_id == opinion_id
    ).all()

    if not parentheticals:
        return {
            "opinion_id": opinion_id,
            "treatment_type": "UNKNOWN",
            "severity": "UNKNOWN",
            "confidence": 0.0,
            "summary": {
                "negative": 0,
                "positive": 0,
                "neutral": 0
            },
            "message": "No parentheticals found for this opinion",
            "from_cache": False
        }

    # Analyze treatment
    parenthetical_data = [
        (p.text, p.described_opinion_id, p.describing_opinion_id)
        for p in parentheticals
    ]

    analysis = analyze_opinion_treatment(opinion_id, parenthetical_data)

    # Cache the results
    cached = db.query(CitationTreatment).filter(
        CitationTreatment.opinion_id == opinion_id
    ).first()

    if cached:
        # Update existing
        cached.treatment_type = analysis.treatment_type
        cached.severity = analysis.severity
        cached.negative_count = analysis.negative_count
        cached.positive_count = analysis.positive_count
        cached.neutral_count = analysis.neutral_count
        cached.confidence = analysis.confidence
        cached.evidence = analysis.evidence
        cached.last_updated = datetime.utcnow()
    else:
        # Create new cache entry
        cached = CitationTreatment(
            opinion_id=opinion_id,
            treatment_type=analysis.treatment_type,
            severity=analysis.severity,
            negative_count=analysis.negative_count,
            positive_count=analysis.positive_count,
            neutral_count=analysis.neutral_count,
            confidence=analysis.confidence,
            evidence=analysis.evidence
        )
        db.add(cached)

    db.commit()

    return {
        "opinion_id": opinion_id,
        "treatment_type": analysis.treatment_type.value,
        "severity": analysis.severity.value,
        "confidence": analysis.confidence,
        "summary": {
            "negative": analysis.negative_count,
            "positive": analysis.positive_count,
            "neutral": analysis.neutral_count,
            "total": analysis.total_parentheticals
        },
        "evidence": analysis.evidence,
        "significant_treatments": analysis.significant_treatments,
        "from_cache": False
    }


@router.get("/{opinion_id}/history")
async def get_treatment_history(
    opinion_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200, description="Maximum number of results")
):
    """
    Get chronological treatment history for an opinion

    Returns all parentheticals describing this opinion with their
    classifications, ordered by the date of the describing opinion.
    """
    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Get parentheticals with describing opinion details
    parentheticals = db.query(
        Parenthetical,
        Opinion,
        OpinionCluster
    ).join(
        Opinion, Parenthetical.describing_opinion_id == Opinion.id
    ).join(
        OpinionCluster, Opinion.cluster_id == OpinionCluster.id
    ).filter(
        Parenthetical.described_opinion_id == opinion_id
    ).order_by(
        OpinionCluster.date_filed.desc()
    ).limit(limit).all()

    # Classify each parenthetical
    from app.services.treatment_classifier import classify_parenthetical

    history = []
    for paren, describing_opinion, cluster in parentheticals:
        result = classify_parenthetical(paren.text)

        history.append({
            "parenthetical_id": paren.id,
            "treatment_type": result.treatment_type.value,
            "severity": result.severity.value,
            "confidence": result.confidence,
            "text": paren.text,
            "describing_opinion_id": describing_opinion.id,
            "describing_case_name": cluster.case_name,
            "date_filed": cluster.date_filed.isoformat() if cluster.date_filed else None,
            "keywords": [s.keyword for s in result.signals[:3]]  # Top 3 keywords
        })

    return {
        "opinion_id": opinion_id,
        "total_treatments": len(history),
        "history": history
    }


@router.post("/analyze/{opinion_id}")
async def analyze_treatment(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Force fresh analysis of treatment (bypasses cache)

    Use this to trigger re-analysis when new parentheticals are added.
    """
    return await get_treatment(opinion_id, db, use_cache=False)


@router.post("/batch")
async def batch_analyze(
    opinion_ids: List[int],
    db: Session = Depends(get_db),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Batch analyze multiple opinions

    Returns treatment summaries for all requested opinions.
    """
    if len(opinion_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 opinions per batch request"
        )

    results = []
    for opinion_id in opinion_ids:
        try:
            result = await get_treatment(opinion_id, db, use_cache=use_cache)
            results.append(result)
        except HTTPException:
            # Skip opinions that don't exist
            results.append({
                "opinion_id": opinion_id,
                "error": "Opinion not found"
            })

    return {
        "total": len(results),
        "results": results
    }


@router.get("/stats/summary")
async def get_treatment_stats(
    db: Session = Depends(get_db)
):
    """
    Get overall statistics about treatments in the database
    """
    # Count treatments by type
    total_cached = db.query(CitationTreatment).count()

    # Count by severity
    negative_count = db.query(CitationTreatment).filter(
        CitationTreatment.severity == Severity.NEGATIVE
    ).count()

    positive_count = db.query(CitationTreatment).filter(
        CitationTreatment.severity == Severity.POSITIVE
    ).count()

    neutral_count = db.query(CitationTreatment).filter(
        CitationTreatment.severity == Severity.NEUTRAL
    ).count()

    # Total parentheticals
    total_parentheticals = db.query(Parenthetical).count()

    return {
        "total_analyzed": total_cached,
        "total_parentheticals": total_parentheticals,
        "by_severity": {
            "negative": negative_count,
            "positive": positive_count,
            "neutral": neutral_count
        }
    }
