"""
Citation API endpoints - citation network queries
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.core.database import get_db
from app.models import Opinion, OpinionsCited, OpinionCluster, Docket, Court, CitationTreatment
from collections import defaultdict

router = APIRouter()


def get_opinion_details(opinion_id: int, db: Session, include_treatment: bool = True) -> Dict[str, Any]:
    """Helper function to get opinion details with cluster and court info"""
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        return None

    cluster = db.query(OpinionCluster).filter(OpinionCluster.id == opinion.cluster_id).first()
    if not cluster:
        return None

    docket = db.query(Docket).filter(Docket.id == cluster.docket_id).first()
    court = db.query(Court).filter(Court.id == docket.court_id).first() if docket else None

    details = {
        "opinion_id": opinion.id,
        "cluster_id": cluster.id,
        "case_name": cluster.case_name,
        "case_name_short": cluster.case_name_short,
        "date_filed": cluster.date_filed.isoformat() if cluster.date_filed else None,
        "citation_count": cluster.citation_count or 0,
        "court_id": court.id if court else None,
        "court_name": court.short_name if court else None
    }

    # Add treatment data if requested
    if include_treatment:
        treatment = db.query(CitationTreatment).filter(
            CitationTreatment.opinion_id == opinion_id
        ).first()

        if treatment:
            details["treatment"] = {
                "type": treatment.treatment_type.value,
                "severity": treatment.severity.value,
                "confidence": treatment.confidence
            }
        else:
            details["treatment"] = None

    return details


@router.get("/outbound/{opinion_id}")
async def get_outbound_citations(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=3, description="Citation depth"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get cases that this opinion cites (outbound citations)

    depth=1: Direct citations only
    depth=2: Citations + citations of citations
    depth=3: Three levels deep
    """
    # Verify opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Collect all citations recursively
    all_citations = []
    visited = {opinion_id}
    current_level = {opinion_id}

    for level in range(depth):
        if not current_level:
            break

        # Get citations for current level
        citations = db.query(
            OpinionsCited.cited_opinion_id,
            OpinionsCited.depth.label("citation_depth")
        ).filter(
            OpinionsCited.citing_opinion_id.in_(current_level)
        ).all()

        next_level = set()
        for citation in citations:
            cited_id = citation.cited_opinion_id
            if cited_id not in visited:
                details = get_opinion_details(cited_id, db)
                if details:
                    details["depth"] = level + 1
                    details["citation_depth"] = citation.citation_depth
                    all_citations.append(details)
                    visited.add(cited_id)
                    next_level.add(cited_id)

        current_level = next_level

    # Apply limit
    all_citations = all_citations[:limit]

    return {
        "opinion_id": opinion_id,
        "depth": depth,
        "total_citations": len(all_citations),
        "citations": all_citations
    }


@router.get("/inbound/{opinion_id}")
async def get_inbound_citations(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(100, le=1000),
    sort: str = Query("date", enum=["date", "relevance", "citation_count"]),
    db: Session = Depends(get_db)
):
    """
    Get cases that cite this opinion (inbound citations)

    This shows how influential/important a case is
    """
    # Verify opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Collect all citing opinions recursively
    all_citations = []
    visited = {opinion_id}
    current_level = {opinion_id}

    for level in range(depth):
        if not current_level:
            break

        # Get opinions that cite current level
        citations = db.query(
            OpinionsCited.citing_opinion_id,
            OpinionsCited.depth.label("citation_depth")
        ).filter(
            OpinionsCited.cited_opinion_id.in_(current_level)
        ).all()

        next_level = set()
        for citation in citations:
            citing_id = citation.citing_opinion_id
            if citing_id not in visited:
                details = get_opinion_details(citing_id, db)
                if details:
                    details["depth"] = level + 1
                    details["citation_depth"] = citation.citation_depth
                    all_citations.append(details)
                    visited.add(citing_id)
                    next_level.add(citing_id)

        current_level = next_level

    # Sort results
    if sort == "date":
        all_citations.sort(key=lambda x: x.get("date_filed") or "", reverse=True)
    elif sort == "citation_count":
        all_citations.sort(key=lambda x: x.get("citation_count") or 0, reverse=True)

    # Apply limit
    all_citations = all_citations[:limit]

    return {
        "opinion_id": opinion_id,
        "depth": depth,
        "total_citing_cases": len(all_citations),
        "citations": all_citations
    }


@router.get("/network/{opinion_id}")
async def get_citation_network(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=2),
    max_nodes: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """
    Get citation network for visualization

    Returns nodes (cases) and edges (citations) for graph visualization
    """
    # Verify opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Get center node details
    center_details = get_opinion_details(opinion_id, db)
    if not center_details:
        raise HTTPException(status_code=404, detail="Opinion details not found")

    nodes = {opinion_id: center_details}
    edges = []

    # Get outbound citations (this opinion cites...)
    outbound = db.query(
        OpinionsCited.cited_opinion_id,
        OpinionsCited.depth
    ).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).limit(max_nodes // 2).all()

    for citation in outbound:
        cited_id = citation.cited_opinion_id
        if cited_id not in nodes:
            details = get_opinion_details(cited_id, db)
            if details:
                details["node_type"] = "cited"
                nodes[cited_id] = details

        edges.append({
            "source": opinion_id,
            "target": cited_id,
            "type": "outbound",
            "depth": citation.depth
        })

    # Get inbound citations (opinions that cite this one)
    inbound = db.query(
        OpinionsCited.citing_opinion_id,
        OpinionsCited.depth
    ).filter(
        OpinionsCited.cited_opinion_id == opinion_id
    ).limit(max_nodes // 2).all()

    for citation in inbound:
        citing_id = citation.citing_opinion_id
        if citing_id not in nodes:
            details = get_opinion_details(citing_id, db)
            if details:
                details["node_type"] = "citing"
                nodes[citing_id] = details

        edges.append({
            "source": citing_id,
            "target": opinion_id,
            "type": "inbound",
            "depth": citation.depth
        })

    # Mark center node
    nodes[opinion_id]["node_type"] = "center"

    return {
        "center_opinion_id": opinion_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


@router.get("/analytics/{opinion_id}")
async def get_citation_analytics(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze citation patterns for a case

    Returns citation counts, timeline, top citing courts, related cases
    """
    # Verify opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail="Opinion not found")

    # Get outbound citation count
    outbound_count = db.query(func.count(OpinionsCited.cited_opinion_id)).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).scalar()

    # Get inbound citation count
    inbound_count = db.query(func.count(OpinionsCited.citing_opinion_id)).filter(
        OpinionsCited.cited_opinion_id == opinion_id
    ).scalar()

    # Get citing opinions with details
    citing_opinions = db.query(
        OpinionsCited.citing_opinion_id,
        Opinion.cluster_id
    ).join(
        Opinion, OpinionsCited.citing_opinion_id == Opinion.id
    ).filter(
        OpinionsCited.cited_opinion_id == opinion_id
    ).limit(100).all()

    # Group by court and date for analytics
    court_counts = defaultdict(int)
    date_counts = defaultdict(int)

    for citing in citing_opinions:
        cluster = db.query(OpinionCluster).filter(
            OpinionCluster.id == citing.cluster_id
        ).first()

        if cluster:
            docket = db.query(Docket).filter(Docket.id == cluster.docket_id).first()
            if docket:
                court = db.query(Court).filter(Court.id == docket.court_id).first()
                if court:
                    court_counts[court.short_name] += 1

                if cluster.date_filed:
                    year = cluster.date_filed.year
                    date_counts[year] += 1

    # Format top citing courts
    top_citing_courts = [
        {"court": court, "count": count}
        for court, count in sorted(court_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Format citation timeline
    citation_timeline = [
        {"year": year, "count": count}
        for year, count in sorted(date_counts.items())
    ]

    # Get related cases (cases cited by the same opinions)
    related_query = db.query(
        OpinionsCited.cited_opinion_id,
        func.count(OpinionsCited.citing_opinion_id).label("common_citations")
    ).filter(
        OpinionsCited.citing_opinion_id.in_([c.citing_opinion_id for c in citing_opinions]),
        OpinionsCited.cited_opinion_id != opinion_id
    ).group_by(
        OpinionsCited.cited_opinion_id
    ).order_by(
        desc("common_citations")
    ).limit(10).all()

    related_cases = []
    for related in related_query:
        details = get_opinion_details(related.cited_opinion_id, db)
        if details:
            details["common_citations"] = related.common_citations
            related_cases.append(details)

    return {
        "opinion_id": opinion_id,
        "outbound_citations": outbound_count or 0,
        "inbound_citations": inbound_count or 0,
        "citation_timeline": citation_timeline,
        "top_citing_courts": top_citing_courts,
        "related_cases": related_cases
    }


@router.get("/most-cited")
async def get_most_cited_cases(
    court_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get most cited cases overall or filtered by court/date"""
    # Base query: get opinion clusters with citation counts
    query = db.query(
        OpinionCluster.id,
        OpinionCluster.case_name,
        OpinionCluster.case_name_short,
        OpinionCluster.date_filed,
        OpinionCluster.citation_count,
        Court.short_name.label("court_name"),
        Court.id.label("court_id")
    ).join(
        Docket, OpinionCluster.docket_id == Docket.id
    ).join(
        Court, Docket.court_id == Court.id
    )

    # Apply filters
    if court_id:
        query = query.filter(Court.id == court_id)

    if start_date:
        query = query.filter(OpinionCluster.date_filed >= start_date)

    if end_date:
        query = query.filter(OpinionCluster.date_filed <= end_date)

    # Sort by citation count and limit
    results = query.order_by(
        desc(OpinionCluster.citation_count)
    ).limit(limit).all()

    # Format results
    most_cited = []
    for result in results:
        most_cited.append({
            "cluster_id": result.id,
            "case_name": result.case_name,
            "case_name_short": result.case_name_short,
            "date_filed": result.date_filed.isoformat() if result.date_filed else None,
            "citation_count": result.citation_count or 0,
            "court": {
                "id": result.court_id,
                "name": result.court_name
            }
        })

    return {
        "most_cited": most_cited,
        "total": len(most_cited),
        "filters": {
            "court_id": court_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }
