"""
AI Analysis API - AI-powered citation risk analysis endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models import Opinion, OpinionCluster, CitationTreatment, Parenthetical
from app.services.ai_risk_analyzer import get_ai_analyzer

router = APIRouter()


@router.post("/{opinion_id}")
async def analyze_opinion_risk(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered analysis of citation risk for an opinion

    Provides detailed insights about:
    - Why the case is at risk
    - What legal theories might be impacted
    - The connection between citing and cited cases
    - Practical implications for legal professionals

    Requires ANTHROPIC_API_KEY environment variable to be set.
    """
    analyzer = get_ai_analyzer()

    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI analysis is unavailable. ANTHROPIC_API_KEY not configured."
        )

    # Get the opinion
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Get opinion text
    opinion_text = opinion.plain_text or opinion.html
    if not opinion_text:
        raise HTTPException(
            status_code=400,
            detail="Opinion text not available. Cannot perform AI analysis."
        )

    # Get the cluster for case name
    cluster = None
    case_name = f"Opinion {opinion_id}"
    if opinion.cluster_id:
        cluster = db.query(OpinionCluster).filter(
            OpinionCluster.id == opinion.cluster_id
        ).first()
        if cluster:
            case_name = cluster.case_name

    # Get citation risk summary
    risk_summary = db.query(CitationTreatment).filter(
        CitationTreatment.opinion_id == opinion_id
    ).first()

    if not risk_summary:
        raise HTTPException(
            status_code=404,
            detail="No citation risk analysis found for this opinion. Run treatment analysis first."
        )

    # Only analyze if there's actually a risk (negative severity)
    if risk_summary.severity != 'NEGATIVE':
        return {
            "opinion_id": opinion_id,
            "case_name": case_name,
            "message": "This case does not have negative citation risk. AI analysis is only available for cases with negative citations.",
            "severity": risk_summary.severity,
            "analysis": None
        }

    # Get citing cases with negative treatment (from parentheticals and evidence)
    citing_cases = []

    # Get negative parentheticals
    negative_parentheticals = db.query(Parenthetical).filter(
        Parenthetical.described_opinion_id == opinion_id
    ).limit(10).all()

    # Build citing cases list from evidence if available
    if risk_summary.evidence and isinstance(risk_summary.evidence, dict):
        negative_examples = risk_summary.evidence.get('negative_examples', [])
        for example in negative_examples[:5]:
            citing_opinion_id = example.get('describing_opinion_id')
            if citing_opinion_id:
                citing_opinion = db.query(Opinion).filter(
                    Opinion.id == citing_opinion_id
                ).first()
                if citing_opinion and citing_opinion.cluster_id:
                    citing_cluster = db.query(OpinionCluster).filter(
                        OpinionCluster.id == citing_opinion.cluster_id
                    ).first()
                    if citing_cluster:
                        citing_cases.append({
                            'case_name': citing_cluster.case_name,
                            'date_filed': citing_cluster.date_filed.isoformat() if citing_cluster.date_filed else None,
                            'excerpt': example.get('text', ''),
                            'keywords': example.get('keywords', [])
                        })

    # Build risk summary dict
    risk_summary_dict = {
        'treatment_type': risk_summary.treatment_type,
        'severity': risk_summary.severity,
        'confidence': risk_summary.confidence,
        'negative_count': risk_summary.negative_count,
        'positive_count': risk_summary.positive_count,
        'neutral_count': risk_summary.neutral_count
    }

    # Call AI analyzer
    result = await analyzer.analyze_citation_risk(
        opinion_text=opinion_text,
        case_name=case_name,
        risk_summary=risk_summary_dict,
        citing_cases=citing_cases,
        max_tokens=2000
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="AI analysis failed. Please try again later."
        )

    if result.get('error'):
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis error: {result['error']}"
        )

    return {
        "opinion_id": opinion_id,
        "case_name": case_name,
        "risk_summary": risk_summary_dict,
        "citing_cases_count": len(citing_cases),
        "analysis": result.get('analysis'),
        "model": result.get('model'),
        "usage": result.get('usage')
    }


@router.get("/status")
async def get_ai_status():
    """
    Check if AI analysis is available

    Returns the status of the AI analysis service and whether
    the ANTHROPIC_API_KEY is configured.
    """
    analyzer = get_ai_analyzer()

    return {
        "available": analyzer.is_available(),
        "model": "claude-sonnet-4.5" if analyzer.is_available() else None,
        "message": "AI analysis ready" if analyzer.is_available() else "ANTHROPIC_API_KEY not configured"
    }
