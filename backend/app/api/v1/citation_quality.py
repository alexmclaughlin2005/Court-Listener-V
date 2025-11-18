"""
Citation Quality API - endpoints for recursive citation quality analysis
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models import Opinion, CitationQualityAnalysis, CitationAnalysisTree
from app.services.recursive_citation_analyzer import RecursiveCitationAnalyzer
from app.services.citation_quality_analyzer import CitationQualityAnalyzer

router = APIRouter()


@router.post("/analyze/{opinion_id}")
async def analyze_citation_tree(
    opinion_id: int,
    depth: int = Query(4, ge=1, le=5, description="Analysis depth (1-5 levels)"),
    force_refresh: bool = Query(False, description="Force re-analysis, ignore cache"),
    db: Session = Depends(get_db)
):
    """
    Analyze citation quality tree for an opinion

    Performs recursive citation analysis up to specified depth:
    - Fetches all cited opinions (breadth-first traversal)
    - Analyzes each citation with AI (Claude Haiku 3.5)
    - Calculates overall risk assessment
    - Saves complete tree to database

    Args:
        opinion_id: Root opinion to analyze
        depth: Analysis depth (1-5 levels, default 4)
        force_refresh: If True, re-analyze even if cached (default False)

    Returns:
        Complete analysis tree with risk assessment

    Requires:
        - ANTHROPIC_API_KEY environment variable
        - COURTLISTENER_API_TOKEN for missing opinions
    """
    # Verify opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Check if AI is available
    analyzer = CitationQualityAnalyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI analysis unavailable - ANTHROPIC_API_KEY not configured"
        )

    # Create recursive analyzer
    recursive_analyzer = RecursiveCitationAnalyzer()

    try:
        # Run analysis
        result = recursive_analyzer.analyze_citation_tree(
            root_opinion_id=opinion_id,
            max_depth=depth,
            db=db,
            force_refresh=force_refresh
        )

        return {
            "success": True,
            "opinion_id": opinion_id,
            "result": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/tree/{opinion_id}")
async def get_citation_tree(
    opinion_id: int,
    depth: Optional[int] = Query(None, ge=1, le=5, description="Filter by depth"),
    db: Session = Depends(get_db)
):
    """
    Get cached citation analysis tree

    Returns the most recent completed analysis tree for an opinion.

    Args:
        opinion_id: Opinion ID
        depth: Optional depth filter (returns tree at specific depth)

    Returns:
        Cached analysis tree or 404 if not found
    """
    # Build query
    query = db.query(CitationAnalysisTree).filter(
        CitationAnalysisTree.root_opinion_id == opinion_id,
        CitationAnalysisTree.status == 'completed'
    )

    if depth:
        query = query.filter(CitationAnalysisTree.max_depth == depth)

    # Get most recent tree
    tree = query.order_by(
        CitationAnalysisTree.analysis_completed_at.desc()
    ).first()

    if not tree:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for opinion {opinion_id}"
        )

    return tree.to_dict(include_tree_data=True)


@router.get("/analysis/{opinion_id}")
async def get_citation_analysis(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Get individual citation quality analysis

    Returns the cached AI analysis for a single opinion.

    Args:
        opinion_id: Opinion ID

    Returns:
        Citation quality analysis or 404 if not cached
    """
    analysis = db.query(CitationQualityAnalysis).filter(
        CitationQualityAnalysis.cited_opinion_id == opinion_id,
        CitationQualityAnalysis.analysis_version == 1
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for opinion {opinion_id}"
        )

    return analysis.to_dict()


@router.get("/stats")
async def get_quality_stats(db: Session = Depends(get_db)):
    """
    Get citation quality analysis statistics

    Returns aggregate stats about cached analyses.
    """
    from sqlalchemy import func

    # Total analyses
    total = db.query(func.count(CitationQualityAnalysis.id)).scalar()

    # By quality assessment
    quality_counts = db.query(
        CitationQualityAnalysis.quality_assessment,
        func.count(CitationQualityAnalysis.id)
    ).group_by(
        CitationQualityAnalysis.quality_assessment
    ).all()

    # Average risk score
    avg_risk = db.query(
        func.avg(CitationQualityAnalysis.risk_score)
    ).scalar()

    # Total trees analyzed
    total_trees = db.query(
        func.count(CitationAnalysisTree.id)
    ).filter(
        CitationAnalysisTree.status == 'completed'
    ).scalar()

    # Average execution time
    avg_time = db.query(
        func.avg(CitationAnalysisTree.execution_time_seconds)
    ).filter(
        CitationAnalysisTree.status == 'completed'
    ).scalar()

    # Cache hit rate
    total_cache_hits = db.query(
        func.sum(CitationAnalysisTree.cache_hits)
    ).filter(
        CitationAnalysisTree.status == 'completed'
    ).scalar() or 0

    total_cache_misses = db.query(
        func.sum(CitationAnalysisTree.cache_misses)
    ).filter(
        CitationAnalysisTree.status == 'completed'
    ).scalar() or 0

    total_cache_attempts = total_cache_hits + total_cache_misses
    cache_hit_rate = (total_cache_hits / total_cache_attempts) if total_cache_attempts > 0 else 0

    return {
        "total_analyses": total or 0,
        "by_quality": {
            quality: count for quality, count in quality_counts
        },
        "average_risk_score": round(float(avg_risk), 2) if avg_risk else 0.0,
        "total_trees_analyzed": total_trees or 0,
        "average_execution_time_seconds": round(float(avg_time), 2) if avg_time else 0.0,
        "cache_hit_rate": round(cache_hit_rate, 3)
    }


@router.get("/high-risk")
async def get_high_risk_opinions(
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: Session = Depends(get_db)
):
    """
    Get opinions with high citation risk

    Returns opinions sorted by risk score (descending).

    Args:
        limit: Maximum number of results (default 20, max 100)
    """
    analyses = db.query(CitationQualityAnalysis).filter(
        CitationQualityAnalysis.risk_score >= 60  # High risk threshold
    ).order_by(
        CitationQualityAnalysis.risk_score.desc()
    ).limit(limit).all()

    return {
        "count": len(analyses),
        "high_risk_opinions": [a.to_dict() for a in analyses]
    }


@router.delete("/tree/{opinion_id}")
async def delete_citation_tree(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete cached citation analysis tree(s)

    Removes all cached trees for an opinion. Use this to force
    fresh analysis on next request.

    Args:
        opinion_id: Opinion ID
    """
    trees = db.query(CitationAnalysisTree).filter(
        CitationAnalysisTree.root_opinion_id == opinion_id
    ).all()

    if not trees:
        raise HTTPException(
            status_code=404,
            detail=f"No trees found for opinion {opinion_id}"
        )

    count = len(trees)
    for tree in trees:
        db.delete(tree)

    db.commit()

    return {
        "success": True,
        "deleted_count": count,
        "message": f"Deleted {count} tree(s) for opinion {opinion_id}"
    }


@router.get("/status")
async def get_status():
    """
    Check citation quality analysis service status

    Returns availability of AI analysis and API integrations.
    """
    import os

    quality_analyzer = CitationQualityAnalyzer()

    return {
        "ai_available": quality_analyzer.is_available(),
        "ai_model": "claude-haiku-4-5-20251001" if quality_analyzer.is_available() else None,
        "courtlistener_api_configured": bool(os.getenv("COURTLISTENER_API_TOKEN")),
        "service_status": "operational" if quality_analyzer.is_available() else "degraded",
        "message": "Citation quality analysis ready" if quality_analyzer.is_available() else "ANTHROPIC_API_KEY not configured"
    }
