# CourtListener Case Law Browser with Citation Mapping
## Project Plan: Case Search & Citation Network Visualization

---

## Project Overview

Build a powerful case law search and citation analysis tool by importing CourtListener's bulk legal data. The application enables users to:
- **Search case law** across 10M+ opinions from all US courts
- **Explore citation networks** - see what cases a decision cites and what cases cite it
- **Visualize citation graphs** - interactive network diagrams showing citation relationships
- **Analyze citation depth** - understand precedential importance through citation analysis
- **Navigate case law** - jump between cited and citing cases seamlessly

This is essentially building a **legal citation graph database** with a powerful search and visualization interface.

---

## Core Features

### 1. Case Search
- Full-text search across 10M+ opinions
- Filter by court, date range, judge, case type
- Sort by relevance, date, citation count
- View full opinion text with citations highlighted

### 2. Citation Mapping (THE KILLER FEATURE)
- **Outbound Citations**: What cases does this opinion cite?
- **Inbound Citations**: What cases cite this opinion?
- **Citation Network Graph**: Visual network showing citation relationships
- **Citation Depth Analysis**: How influential is this case?
- **Citation Timeline**: When was this case cited over time?
- **Related Cases**: Find similar cases through citation patterns

### 3. Citation Analytics
- Most cited cases overall
- Most cited cases by court/time period
- Citation trends over time
- Precedential authority scoring
- Hub and authority analysis (PageRank-style for cases)

---

## Data Architecture

### Priority Tables (Case Law Focus)

**Tier 1: Foundation (Import First)**
1. **search_court** (~1K rows)
   - Court metadata and hierarchy
   - Required by all other tables

**Tier 2: Core Case Law (Import Second)**
2. **search_docket** (~30M rows, ~20GB)
   - Case metadata: case name, docket number, dates
   - Links to court and parties

3. **search_opinioncluster** (~10M rows, ~5GB)
   - Groups related opinions (lead, concurrence, dissent)
   - Links to docket
   - Citation counts, dates, judges

4. **search_opinion** (~15M rows, ~40GB)
   - Full opinion text
   - Opinion type (lead, concurrence, dissent)
   - Download URLs, word counts

**Tier 3: Citation Network (Import Third - THE BIG ONE)**
5. **search_opinionscited** (~70M rows, ~4GB)
   - The citation map! Maps citing_opinion → cited_opinion
   - Includes citation depth (how many hops)
   - **This is your graph database**

**Tier 4: Supporting Data (Optional, Import Later)**
6. **people_db_person** + **people_db_position** (for judge info)
7. **search_parenthetical** (contextual citations)
8. **search_docketentry** + **search_recapdocument** (PACER documents)

### Database Size Estimates

```
Tier 1 (Courts):           ~1 MB
Tier 2 (Case Law):         ~65 GB
Tier 3 (Citations):        ~4 GB
Tier 4 (Supporting):       ~30 GB
-----------------------------------
Total:                     ~100 GB
```

**Import Time Estimates (with optimization):**
- Tier 1: 1 minute
- Tier 2: 24-36 hours (parallelized)
- Tier 3: 12-18 hours (parallelized) 
- **Total: ~48 hours for full import**

---

## Technical Architecture

### Backend Stack

```
PostgreSQL 15+ (with Graph Extensions)
├── Core Tables (opinions, dockets, clusters)
├── Citation Graph (opinionscited table)
├── Full-Text Search (GIN indexes)
├── Materialized Views (citation statistics)
└── Graph Queries (recursive CTEs)

FastAPI Backend
├── Case Search API
├── Citation API (inbound/outbound)
├── Citation Graph API
├── Analytics API
└── Import Management API

Celery Workers (for background tasks)
├── CSV Download & Import
├── Citation Analysis Jobs
├── Graph Computation (PageRank, etc.)
└── Materialized View Refresh
```

### Frontend Stack

```
React + TypeScript
├── Case Search Interface
├── Opinion Viewer (with highlighted citations)
├── Citation Network Visualizer (D3.js or vis.js)
├── Citation Analytics Dashboard
└── Import Monitor
```

---

## Phase 1: Foundation & Import System (Week 1-2)

### 1.1 Project Setup
- [ ] Railway project with PostgreSQL 15+
- [ ] Backend: FastAPI + SQLAlchemy
- [ ] Worker: Celery + Redis
- [ ] Frontend: React + TypeScript

### 1.2 Database Schema

**Key Models:**

```python
# backend/app/models/case_law.py

class Court(Base):
    __tablename__ = "search_court"
    
    id = Column(String(15), primary_key=True)  # e.g., "scotus", "ca9"
    full_name = Column(String(200))
    short_name = Column(String(100))
    jurisdiction = Column(String(3))
    position = Column(Float)  # Hierarchy level
    citation_string = Column(String(100))
    
    # Relationships
    dockets = relationship("Docket", back_populates="court")


class Docket(Base):
    __tablename__ = "search_docket"
    
    id = Column(Integer, primary_key=True)
    court_id = Column(String(15), ForeignKey("search_court.id"))
    docket_number = Column(String(300))
    case_name = Column(Text)
    case_name_short = Column(Text)
    case_name_full = Column(Text)
    date_filed = Column(Date)
    date_terminated = Column(Date)
    date_argued = Column(Date)
    
    # Relationships
    court = relationship("Court", back_populates="dockets")
    clusters = relationship("OpinionCluster", back_populates="docket")
    
    # Indexes for search
    __table_args__ = (
        Index('idx_docket_case_name', 'case_name', postgresql_using='gin',
              postgresql_ops={'case_name': 'gin_trgm_ops'}),
        Index('idx_docket_date_filed', 'date_filed'),
        Index('idx_docket_court', 'court_id'),
    )


class OpinionCluster(Base):
    __tablename__ = "search_opinioncluster"
    
    id = Column(Integer, primary_key=True)
    docket_id = Column(Integer, ForeignKey("search_docket.id"))
    date_filed = Column(Date)
    date_filed_is_approximate = Column(Boolean)
    slug = Column(String(75))
    case_name = Column(Text)
    case_name_short = Column(Text)
    case_name_full = Column(Text)
    
    # Citation info
    scdb_id = Column(String(10))
    citation_count = Column(Integer, default=0)  # How many cases cite this
    precedential_status = Column(String(50))
    
    # Judges
    judges = Column(Text)
    panel_ids = Column(ARRAY(Integer))
    non_participating_judge_ids = Column(ARRAY(Integer))
    
    # Relationships
    docket = relationship("Docket", back_populates="clusters")
    sub_opinions = relationship("Opinion", back_populates="cluster")
    citations_to = relationship(
        "OpinionsCited",
        foreign_keys="OpinionsCited.citing_opinion_id",
        back_populates="citing_opinion"
    )
    citations_from = relationship(
        "OpinionsCited",
        foreign_keys="OpinionsCited.cited_opinion_id",
        back_populates="cited_opinion"
    )


class Opinion(Base):
    __tablename__ = "search_opinion"
    
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey("search_opinioncluster.id"))
    
    # Opinion content
    plain_text = Column(Text)  # Full text
    html = Column(Text)
    html_with_citations = Column(Text)  # Text with citation links
    
    # Metadata
    type = Column(String(20))  # "010lead", "020concurrence", "030dissent"
    sha1 = Column(String(40))
    download_url = Column(String(500))
    local_path = Column(String(500))
    
    # Text analysis
    extracted_by_ocr = Column(Boolean)
    word_count = Column(Integer)
    char_count = Column(Integer)
    
    # Relationships
    cluster = relationship("OpinionCluster", back_populates="sub_opinions")
    
    # Full-text search index
    __table_args__ = (
        Index('idx_opinion_fts', 'plain_text', postgresql_using='gin',
              postgresql_ops={'plain_text': 'gin_trgm_ops'}),
    )


class OpinionsCited(Base):
    """
    THE CITATION GRAPH - 70 million edges!
    
    This is the core of citation mapping.
    Each row represents: Opinion A cites Opinion B
    """
    __tablename__ = "search_opinionscited"
    
    id = Column(Integer, primary_key=True)
    citing_opinion_id = Column(Integer, ForeignKey("search_opinion.id"), nullable=False)
    cited_opinion_id = Column(Integer, ForeignKey("search_opinion.id"), nullable=False)
    depth = Column(Integer, default=1)  # Citation depth/strength
    
    # Relationships
    citing_opinion = relationship(
        "Opinion",
        foreign_keys=[citing_opinion_id],
        backref="cites"
    )
    cited_opinion = relationship(
        "Opinion",
        foreign_keys=[cited_opinion_id],
        backref="cited_by"
    )
    
    # Critical indexes for citation queries
    __table_args__ = (
        Index('idx_opinionscited_citing', 'citing_opinion_id'),
        Index('idx_opinionscited_cited', 'cited_opinion_id'),
        Index('idx_opinionscited_both', 'citing_opinion_id', 'cited_opinion_id'),
        UniqueConstraint('citing_opinion_id', 'cited_opinion_id'),
    )
```

### 1.3 Robust CSV Import System

**Same as previous plan, but optimized for these specific tables:**

```python
# backend/app/services/case_law_importer.py

class CaseLawImporter:
    """Optimized import for case law tables"""
    
    # Import order (respects foreign keys)
    IMPORT_ORDER = [
        "search_court",           # 1K rows - 1 minute
        "search_docket",          # 30M rows - 12 hours
        "search_opinioncluster",  # 10M rows - 4 hours  
        "search_opinion",         # 15M rows - 8 hours
        "search_opinionscited",   # 70M rows - 18 hours
    ]
    
    async def import_all_case_law(self):
        """Import case law in correct order"""
        
        for table_name in self.IMPORT_ORDER:
            logger.info(f"Starting import of {table_name}")
            
            # Prepare table (drop indexes, disable constraints)
            await self.prepare_table(table_name)
            
            # Import based on size
            if table_name == "search_court":
                # Small table, simple import
                await self.simple_import(table_name)
            else:
                # Large table, parallel import
                await self.parallel_import(table_name, workers=8)
            
            # Finalize table (rebuild indexes, enable constraints)
            await self.finalize_table(table_name)
            
            logger.info(f"Completed import of {table_name}")
```

---

## Phase 2: Citation API Development (Week 3)

### 2.1 Core Citation Endpoints

```python
# backend/app/api/routes/citations.py
from fastapi import APIRouter, Query
from typing import List

router = APIRouter(prefix="/api/citations", tags=["citations"])


@router.get("/outbound/{opinion_id}")
async def get_outbound_citations(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(100, le=1000)
):
    """
    Get cases that this opinion cites (outbound citations)
    
    depth=1: Direct citations only
    depth=2: Citations + citations of citations
    depth=3: Three levels deep
    """
    
    # Query citation graph
    query = """
        WITH RECURSIVE citation_tree AS (
            -- Base case: direct citations
            SELECT 
                cited_opinion_id as opinion_id,
                1 as depth
            FROM search_opinionscited
            WHERE citing_opinion_id = :opinion_id
            
            UNION ALL
            
            -- Recursive case: citations of citations
            SELECT 
                oc.cited_opinion_id,
                ct.depth + 1
            FROM citation_tree ct
            JOIN search_opinionscited oc ON oc.citing_opinion_id = ct.opinion_id
            WHERE ct.depth < :max_depth
        )
        SELECT DISTINCT
            ct.opinion_id,
            ct.depth,
            o.id,
            o.cluster_id,
            oc.case_name,
            oc.date_filed,
            oc.citation_count,
            c.short_name as court
        FROM citation_tree ct
        JOIN search_opinion o ON o.id = ct.opinion_id
        JOIN search_opinioncluster oc ON oc.id = o.cluster_id
        JOIN search_docket d ON d.id = oc.docket_id
        JOIN search_court c ON c.id = d.court_id
        ORDER BY ct.depth, oc.citation_count DESC
        LIMIT :limit
    """
    
    results = await db.execute(
        query,
        {
            "opinion_id": opinion_id,
            "max_depth": depth,
            "limit": limit
        }
    )
    
    return {
        "opinion_id": opinion_id,
        "depth": depth,
        "citations": [
            {
                "opinion_id": row.opinion_id,
                "depth": row.depth,
                "case_name": row.case_name,
                "court": row.court,
                "date_filed": row.date_filed,
                "citation_count": row.citation_count,
            }
            for row in results
        ]
    }


@router.get("/inbound/{opinion_id}")
async def get_inbound_citations(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(100, le=1000),
    sort: str = Query("date", enum=["date", "relevance", "citation_count"])
):
    """
    Get cases that cite this opinion (inbound citations)
    
    This shows how influential/important a case is
    """
    
    query = """
        WITH RECURSIVE citation_tree AS (
            -- Base case: direct citations TO this opinion
            SELECT 
                citing_opinion_id as opinion_id,
                1 as depth
            FROM search_opinionscited
            WHERE cited_opinion_id = :opinion_id
            
            UNION ALL
            
            -- Recursive case: cases that cite the citing cases
            SELECT 
                oc.citing_opinion_id,
                ct.depth + 1
            FROM citation_tree ct
            JOIN search_opinionscited oc ON oc.cited_opinion_id = ct.opinion_id
            WHERE ct.depth < :max_depth
        )
        SELECT DISTINCT
            ct.opinion_id,
            ct.depth,
            o.id,
            o.cluster_id,
            oc.case_name,
            oc.date_filed,
            oc.citation_count,
            c.short_name as court
        FROM citation_tree ct
        JOIN search_opinion o ON o.id = ct.opinion_id
        JOIN search_opinioncluster oc ON oc.id = o.cluster_id
        JOIN search_docket d ON d.id = oc.docket_id
        JOIN search_court c ON c.id = d.court_id
        ORDER BY 
            CASE 
                WHEN :sort = 'date' THEN oc.date_filed 
                ELSE NULL 
            END DESC,
            CASE 
                WHEN :sort = 'citation_count' THEN oc.citation_count 
                ELSE NULL 
            END DESC
        LIMIT :limit
    """
    
    results = await db.execute(
        query,
        {
            "opinion_id": opinion_id,
            "max_depth": depth,
            "limit": limit,
            "sort": sort
        }
    )
    
    return {
        "opinion_id": opinion_id,
        "depth": depth,
        "total_citing_cases": len(results),
        "citations": [...]
    }


@router.get("/network/{opinion_id}")
async def get_citation_network(
    opinion_id: int,
    depth: int = Query(1, ge=1, le=2),
    max_nodes: int = Query(50, le=200)
):
    """
    Get citation network for visualization
    
    Returns nodes (cases) and edges (citations) for graph visualization
    
    Response format:
    {
        "nodes": [
            {
                "id": 12345,
                "case_name": "Roe v. Wade",
                "court": "scotus",
                "date": "1973-01-22",
                "citation_count": 1500,
                "node_type": "center|cited|citing"
            }
        ],
        "edges": [
            {
                "source": 12345,
                "target": 67890,
                "depth": 1,
                "edge_type": "cites|cited_by"
            }
        ]
    }
    """
    
    # Get outbound citations (what this case cites)
    outbound = await get_outbound_citations(opinion_id, depth, max_nodes // 2)
    
    # Get inbound citations (what cites this case)
    inbound = await get_inbound_citations(opinion_id, depth, max_nodes // 2)
    
    # Build graph structure
    nodes = {}
    edges = []
    
    # Center node (the case we're examining)
    center_opinion = await get_opinion_with_cluster(opinion_id)
    nodes[opinion_id] = {
        "id": opinion_id,
        "case_name": center_opinion.cluster.case_name_short,
        "court": center_opinion.cluster.docket.court.short_name,
        "date": center_opinion.cluster.date_filed,
        "citation_count": center_opinion.cluster.citation_count,
        "node_type": "center"
    }
    
    # Add cited opinions (outbound)
    for citation in outbound["citations"]:
        nodes[citation["opinion_id"]] = {
            "id": citation["opinion_id"],
            "case_name": citation["case_name"],
            "court": citation["court"],
            "date": citation["date_filed"],
            "citation_count": citation["citation_count"],
            "node_type": "cited",
            "depth": citation["depth"]
        }
        edges.append({
            "source": opinion_id,
            "target": citation["opinion_id"],
            "depth": citation["depth"],
            "edge_type": "cites"
        })
    
    # Add citing opinions (inbound)
    for citation in inbound["citations"]:
        nodes[citation["opinion_id"]] = {
            "id": citation["opinion_id"],
            "case_name": citation["case_name"],
            "court": citation["court"],
            "date": citation["date_filed"],
            "citation_count": citation["citation_count"],
            "node_type": "citing",
            "depth": citation["depth"]
        }
        edges.append({
            "source": citation["opinion_id"],
            "target": opinion_id,
            "depth": citation["depth"],
            "edge_type": "cited_by"
        })
    
    return {
        "center_opinion_id": opinion_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


@router.get("/analytics/{opinion_id}")
async def get_citation_analytics(opinion_id: int):
    """
    Analyze citation patterns for a case
    
    Returns:
    - Total inbound/outbound citation counts
    - Citation timeline (when was this case cited over time)
    - Most influential citing cases
    - Courts that cite this case most
    - Related cases (cited together frequently)
    """
    
    # Citation counts
    outbound_count = await db.scalar(
        "SELECT COUNT(*) FROM search_opinionscited WHERE citing_opinion_id = :id",
        {"id": opinion_id}
    )
    
    inbound_count = await db.scalar(
        "SELECT COUNT(*) FROM search_opinionscited WHERE cited_opinion_id = :id",
        {"id": opinion_id}
    )
    
    # Citation timeline
    timeline_query = """
        SELECT 
            DATE_TRUNC('year', oc.date_filed) as year,
            COUNT(*) as citation_count
        FROM search_opinionscited sc
        JOIN search_opinion o ON o.id = sc.citing_opinion_id
        JOIN search_opinioncluster oc ON oc.id = o.cluster_id
        WHERE sc.cited_opinion_id = :opinion_id
        GROUP BY year
        ORDER BY year
    """
    timeline = await db.fetch_all(timeline_query, {"opinion_id": opinion_id})
    
    # Top citing courts
    courts_query = """
        SELECT 
            c.short_name,
            c.full_name,
            COUNT(*) as citation_count
        FROM search_opinionscited sc
        JOIN search_opinion o ON o.id = sc.citing_opinion_id
        JOIN search_opinioncluster oc ON oc.id = o.cluster_id
        JOIN search_docket d ON d.id = oc.docket_id
        JOIN search_court c ON c.id = d.court_id
        WHERE sc.cited_opinion_id = :opinion_id
        GROUP BY c.id, c.short_name, c.full_name
        ORDER BY citation_count DESC
        LIMIT 10
    """
    top_courts = await db.fetch_all(courts_query, {"opinion_id": opinion_id})
    
    # Co-cited cases (cases cited together with this one)
    cocited_query = """
        SELECT 
            oc2.id,
            oc2.case_name_short,
            COUNT(*) as cocitation_count
        FROM search_opinionscited sc1
        JOIN search_opinionscited sc2 
            ON sc1.citing_opinion_id = sc2.citing_opinion_id
        JOIN search_opinion o ON o.id = sc2.cited_opinion_id
        JOIN search_opinioncluster oc2 ON oc2.id = o.cluster_id
        WHERE sc1.cited_opinion_id = :opinion_id
            AND sc2.cited_opinion_id != :opinion_id
        GROUP BY oc2.id, oc2.case_name_short
        ORDER BY cocitation_count DESC
        LIMIT 10
    """
    related_cases = await db.fetch_all(cocited_query, {"opinion_id": opinion_id})
    
    return {
        "opinion_id": opinion_id,
        "outbound_citations": outbound_count,
        "inbound_citations": inbound_count,
        "citation_timeline": [
            {"year": row.year.year, "count": row.citation_count}
            for row in timeline
        ],
        "top_citing_courts": [
            {"court": row.short_name, "full_name": row.full_name, "count": row.citation_count}
            for row in top_courts
        ],
        "related_cases": [
            {
                "cluster_id": row.id,
                "case_name": row.case_name_short,
                "cocitation_count": row.cocitation_count
            }
            for row in related_cases
        ]
    }


@router.get("/most-cited")
async def get_most_cited_cases(
    court_id: str = None,
    start_date: date = None,
    end_date: date = None,
    limit: int = Query(100, le=1000)
):
    """
    Get most cited cases overall or filtered by court/date
    """
    
    query = """
        SELECT 
            oc.id,
            oc.case_name,
            oc.case_name_short,
            oc.date_filed,
            oc.citation_count,
            c.short_name as court,
            COUNT(sc.id) as calculated_citation_count
        FROM search_opinioncluster oc
        JOIN search_docket d ON d.id = oc.docket_id
        JOIN search_court c ON c.id = d.court_id
        LEFT JOIN search_opinion o ON o.cluster_id = oc.id
        LEFT JOIN search_opinionscited sc ON sc.cited_opinion_id = o.id
        WHERE 1=1
            {court_filter}
            {date_filter}
        GROUP BY oc.id, oc.case_name, oc.case_name_short, 
                 oc.date_filed, oc.citation_count, c.short_name
        ORDER BY calculated_citation_count DESC
        LIMIT :limit
    """
    
    # Build dynamic filters
    filters = []
    params = {"limit": limit}
    
    if court_id:
        filters.append("AND c.id = :court_id")
        params["court_id"] = court_id
    
    if start_date:
        filters.append("AND oc.date_filed >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        filters.append("AND oc.date_filed <= :end_date")
        params["end_date"] = end_date
    
    query = query.format(
        court_filter=" ".join(f for f in filters if "court" in f),
        date_filter=" ".join(f for f in filters if "date" in f)
    )
    
    results = await db.fetch_all(query, params)
    
    return {
        "most_cited": [
            {
                "cluster_id": row.id,
                "case_name": row.case_name_short,
                "court": row.court,
                "date_filed": row.date_filed,
                "citation_count": row.calculated_citation_count
            }
            for row in results
        ]
    }
```

### 2.2 Case Search API

```python
# backend/app/api/routes/search.py

@router.get("/search")
async def search_cases(
    q: str = Query(..., min_length=3),
    court: str = None,
    date_from: date = None,
    date_to: date = None,
    sort: str = Query("relevance", enum=["relevance", "date", "citations"]),
    cursor: str = None,
    limit: int = Query(50, le=100)
):
    """
    Full-text search across case law
    
    Searches:
    - Case names
    - Opinion text
    - Docket numbers
    
    Returns results with pagination cursor
    """
    
    # PostgreSQL full-text search
    query = """
        SELECT 
            oc.id,
            oc.case_name,
            oc.case_name_short,
            oc.date_filed,
            oc.citation_count,
            c.short_name as court,
            d.docket_number,
            o.id as opinion_id,
            -- Relevance score
            ts_rank(
                to_tsvector('english', o.plain_text),
                plainto_tsquery('english', :search_query)
            ) as relevance,
            -- Snippet for preview
            ts_headline(
                'english',
                o.plain_text,
                plainto_tsquery('english', :search_query),
                'MaxWords=50, MinWords=25'
            ) as snippet
        FROM search_opinioncluster oc
        JOIN search_opinion o ON o.cluster_id = oc.id
        JOIN search_docket d ON d.id = oc.docket_id
        JOIN search_court c ON c.id = d.court_id
        WHERE 
            to_tsvector('english', o.plain_text) @@ 
            plainto_tsquery('english', :search_query)
            {court_filter}
            {date_filter}
            {cursor_filter}
        ORDER BY 
            {sort_clause}
        LIMIT :limit
    """
    
    # Build query dynamically
    # ... (similar to above)
    
    results = await db.fetch_all(query, params)
    
    return {
        "query": q,
        "results": [...],
        "pagination": {
            "next_cursor": next_cursor,
            "limit": limit
        }
    }
```

---

## Phase 3: Citation Visualization (Week 4)

### 3.1 Citation Network Graph Component

```tsx
// frontend/src/components/CitationNetworkGraph.tsx
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useQuery } from '@tanstack/react-query';

interface Node {
  id: number;
  case_name: string;
  court: string;
  date: string;
  citation_count: number;
  node_type: 'center' | 'cited' | 'citing';
  depth?: number;
}

interface Edge {
  source: number;
  target: number;
  depth: number;
  edge_type: 'cites' | 'cited_by';
}

interface CitationNetworkProps {
  opinionId: number;
  depth?: number;
  maxNodes?: number;
}

export function CitationNetworkGraph({ 
  opinionId, 
  depth = 1,
  maxNodes = 50 
}: CitationNetworkProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  
  const { data, isLoading } = useQuery({
    queryKey: ['citation-network', opinionId, depth],
    queryFn: () => fetchCitationNetwork(opinionId, depth, maxNodes),
  });

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const width = 1200;
    const height = 800;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes as any)
      .force('link', d3.forceLink(data.edges)
        .id((d: any) => d.id)
        .distance(d => (d.depth === 1 ? 150 : 250))
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Color scale based on node type
    const colorScale = d3.scaleOrdinal<string>()
      .domain(['center', 'cited', 'citing'])
      .range(['#ef4444', '#3b82f6', '#10b981']);

    // Draw edges
    const links = svg.append('g')
      .selectAll('line')
      .data(data.edges)
      .join('line')
      .attr('stroke', d => d.edge_type === 'cites' ? '#94a3b8' : '#cbd5e1')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');

    // Define arrow markers
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#94a3b8');

    // Draw nodes
    const nodes = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .join('circle')
      .attr('r', d => {
        if (d.node_type === 'center') return 20;
        return 10 + Math.min(d.citation_count / 50, 15);
      })
      .attr('fill', d => colorScale(d.node_type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(drag(simulation) as any);

    // Add labels
    const labels = svg.append('g')
      .selectAll('text')
      .data(data.nodes)
      .join('text')
      .text(d => d.case_name.length > 30 
        ? d.case_name.substring(0, 30) + '...' 
        : d.case_name
      )
      .attr('font-size', d => d.node_type === 'center' ? 14 : 10)
      .attr('font-weight', d => d.node_type === 'center' ? 'bold' : 'normal')
      .attr('dx', 25)
      .attr('dy', 5);

    // Add tooltips
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'citation-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'white')
      .style('border', '1px solid #ccc')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('box-shadow', '0 2px 4px rgba(0,0,0,0.1)');

    nodes
      .on('mouseover', (event, d) => {
        tooltip
          .style('visibility', 'visible')
          .html(`
            <strong>${d.case_name}</strong><br/>
            Court: ${d.court}<br/>
            Date: ${d.date}<br/>
            Citations: ${d.citation_count}<br/>
            Type: ${d.node_type}
          `);
      })
      .on('mousemove', (event) => {
        tooltip
          .style('top', (event.pageY - 10) + 'px')
          .style('left', (event.pageX + 10) + 'px');
      })
      .on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      })
      .on('click', (event, d) => {
        // Navigate to case detail page
        window.location.href = `/case/${d.id}`;
      });

    // Update positions on each tick
    simulation.on('tick', () => {
      links
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodes
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Drag behavior
    function drag(simulation: d3.Simulation<any, any>) {
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event: any) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
    }

    // Cleanup
    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [data]);

  if (isLoading) {
    return <div>Loading citation network...</div>;
  }

  return (
    <div className="citation-network-container">
      <div className="controls mb-4 flex gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Depth</label>
          <select 
            value={depth} 
            onChange={(e) => setDepth(Number(e.target.value))}
            className="border rounded px-3 py-2"
          >
            <option value={1}>1 level</option>
            <option value={2}>2 levels</option>
            <option value={3}>3 levels</option>
          </select>
        </div>
        <div className="legend flex gap-4 items-center">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span>Center Case</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span>Cited By</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span>Cites</span>
          </div>
        </div>
      </div>
      <svg ref={svgRef} className="border rounded-lg shadow-lg"></svg>
      <div className="stats mt-4 grid grid-cols-3 gap-4">
        <div className="stat-card">
          <div className="text-2xl font-bold">{data?.nodes.length || 0}</div>
          <div className="text-sm text-gray-600">Cases</div>
        </div>
        <div className="stat-card">
          <div className="text-2xl font-bold">{data?.edges.length || 0}</div>
          <div className="text-sm text-gray-600">Citations</div>
        </div>
        <div className="stat-card">
          <div className="text-2xl font-bold">
            {data?.nodes.filter(n => n.node_type === 'citing').length || 0}
          </div>
          <div className="text-sm text-gray-600">Citing Cases</div>
        </div>
      </div>
    </div>
  );
}
```

### 3.2 Case Detail Page with Citations

```tsx
// frontend/src/pages/CaseDetailPage.tsx

export function CaseDetailPage() {
  const { caseId } = useParams();
  
  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => fetchCase(caseId),
  });

  const { data: outbound } = useQuery({
    queryKey: ['citations-outbound', caseData?.opinion_id],
    queryFn: () => fetchOutboundCitations(caseData?.opinion_id),
    enabled: !!caseData?.opinion_id,
  });

  const { data: inbound } = useQuery({
    queryKey: ['citations-inbound', caseData?.opinion_id],
    queryFn: () => fetchInboundCitations(caseData?.opinion_id),
    enabled: !!caseData?.opinion_id,
  });

  const { data: analytics } = useQuery({
    queryKey: ['citation-analytics', caseData?.opinion_id],
    queryFn: () => fetchCitationAnalytics(caseData?.opinion_id),
    enabled: !!caseData?.opinion_id,
  });

  return (
    <div className="case-detail-page">
      {/* Header */}
      <div className="case-header bg-white p-6 rounded-lg shadow mb-6">
        <h1 className="text-3xl font-bold mb-2">{caseData?.case_name}</h1>
        <div className="flex gap-6 text-sm text-gray-600">
          <span>{caseData?.court}</span>
          <span>{caseData?.date_filed}</span>
          <span>Docket: {caseData?.docket_number}</span>
          <span>{caseData?.citation_count} citations</span>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="opinion">
        <TabsList>
          <TabsTrigger value="opinion">Opinion</TabsTrigger>
          <TabsTrigger value="citations">
            Citations ({(outbound?.citations.length || 0) + (inbound?.citations.length || 0)})
          </TabsTrigger>
          <TabsTrigger value="network">Citation Network</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Opinion Text Tab */}
        <TabsContent value="opinion">
          <Card>
            <CardContent className="prose max-w-none p-6">
              <div 
                dangerouslySetInnerHTML={{ __html: caseData?.html_with_citations }}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Citations Tab */}
        <TabsContent value="citations">
          <div className="grid grid-cols-2 gap-6">
            {/* Outbound Citations */}
            <Card>
              <CardHeader>
                <CardTitle>
                  Cases Cited ({outbound?.citations.length || 0})
                </CardTitle>
                <CardDescription>
                  Cases that this opinion cites as authority
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {outbound?.citations.map((citation: any) => (
                    <div 
                      key={citation.opinion_id}
                      className="p-3 border rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/case/${citation.cluster_id}`)}
                    >
                      <div className="font-medium">{citation.case_name}</div>
                      <div className="text-sm text-gray-600">
                        {citation.court} • {citation.date_filed}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Inbound Citations */}
            <Card>
              <CardHeader>
                <CardTitle>
                  Citing Cases ({inbound?.citations.length || 0})
                </CardTitle>
                <CardDescription>
                  Cases that cite this opinion
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {inbound?.citations.map((citation: any) => (
                    <div 
                      key={citation.opinion_id}
                      className="p-3 border rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/case/${citation.cluster_id}`)}
                    >
                      <div className="font-medium">{citation.case_name}</div>
                      <div className="text-sm text-gray-600">
                        {citation.court} • {citation.date_filed}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Citation Network Tab */}
        <TabsContent value="network">
          <Card>
            <CardContent className="p-6">
              <CitationNetworkGraph 
                opinionId={caseData?.opinion_id}
                depth={2}
                maxNodes={50}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <div className="grid grid-cols-2 gap-6">
            {/* Citation Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Citation Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={analytics?.citation_timeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#3b82f6" 
                      fill="#93c5fd" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Top Citing Courts */}
            <Card>
              <CardHeader>
                <CardTitle>Top Citing Courts</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics?.top_citing_courts}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="court" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Related Cases */}
            <Card className="col-span-2">
              <CardHeader>
                <CardTitle>Related Cases</CardTitle>
                <CardDescription>
                  Cases frequently cited together with this case
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics?.related_cases.map((related: any) => (
                    <div 
                      key={related.cluster_id}
                      className="flex justify-between items-center p-3 border rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/case/${related.cluster_id}`)}
                    >
                      <span className="font-medium">{related.case_name}</span>
                      <span className="text-sm text-gray-600">
                        Co-cited {related.cocitation_count} times
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

## Phase 4: Advanced Features (Week 5-6)

### 4.1 Citation Authority Scoring (PageRank)

Compute "importance" scores for cases based on citation patterns:

```python
# backend/app/services/citation_analytics.py
import networkx as nx
from typing import Dict

class CitationAnalytics:
    """Compute advanced citation metrics"""
    
    async def compute_pagerank(self) -> Dict[int, float]:
        """
        Compute PageRank-style authority scores for all cases
        
        Cases with more inbound citations from important cases
        get higher scores.
        """
        
        # Build citation graph
        G = nx.DiGraph()
        
        # Add all opinions as nodes
        opinions = await db.fetch_all(
            "SELECT id FROM search_opinion"
        )
        G.add_nodes_from([o.id for o in opinions])
        
        # Add citations as edges
        citations = await db.fetch_all(
            "SELECT citing_opinion_id, cited_opinion_id FROM search_opinionscited"
        )
        G.add_edges_from([
            (c.citing_opinion_id, c.cited_opinion_id) 
            for c in citations
        ])
        
        # Compute PageRank
        pagerank = nx.pagerank(G, alpha=0.85)
        
        # Store in database
        await self._store_authority_scores(pagerank)
        
        return pagerank
    
    async def compute_hub_authority_scores(self):
        """
        HITS algorithm: identify hubs (cite many important cases)
        and authorities (cited by many hubs)
        """
        
        # Similar to PageRank but computes two scores
        # ...
```

### 4.2 Citation Search & Filtering

```tsx
// frontend/src/pages/CitationExplorer.tsx

export function CitationExplorerPage() {
  return (
    <div className="citation-explorer">
      <h1>Citation Explorer</h1>
      
      {/* Filters */}
      <div className="filters grid grid-cols-4 gap-4 mb-6">
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Court" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="scotus">Supreme Court</SelectItem>
            <SelectItem value="ca1">First Circuit</SelectItem>
            {/* ... */}
          </SelectContent>
        </Select>

        <Input type="date" placeholder="From Date" />
        <Input type="date" placeholder="To Date" />
        
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Sort By" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="citations">Most Cited</SelectItem>
            <SelectItem value="date">Most Recent</SelectItem>
            <SelectItem value="authority">Authority Score</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Results */}
      <DataTable
        columns={caseColumns}
        data={cases}
        onRowClick={(case) => navigate(`/case/${case.id}`)}
      />
    </div>
  );
}
```

---

## Revised Timeline

### Week 1-2: Foundation & Import (CRITICAL)
- ✅ Project setup on Railway
- ✅ Database schema for case law
- ✅ Robust CSV parser
- ✅ Parallel import system
- ✅ Import Tier 1-2 (Courts + Case Law: ~55M rows, 36 hours)

### Week 3: Citation Map Import & API
- ✅ Import Tier 3 (Citations: 70M rows, 18 hours)
- ✅ Citation API endpoints (outbound, inbound, network)
- ✅ Test citation queries on real data

### Week 4: Visualization
- ✅ D3.js citation network graph
- ✅ Interactive force-directed layout
- ✅ Case detail page with citations

### Week 5-6: Advanced Features
- ✅ Citation analytics (timeline, courts, co-citations)
- ✅ PageRank authority scores
- ✅ Search with filters
- ✅ Citation explorer dashboard

### Week 7: Testing & Optimization
- ✅ Performance tuning for 70M row queries
- ✅ Load testing
- ✅ UI polish

### Week 8: Production Launch
- ✅ Deploy to Railway
- ✅ Complete data import
- ✅ Documentation
- ✅ Launch! 🚀

---

## Success Metrics

### Must-Have
1. ✅ Import completes in <48 hours
2. ✅ Can search 10M opinions in <1 second
3. ✅ Citation graph loads in <2 seconds
4. ✅ Network visualization handles 100+ nodes smoothly
5. ✅ Can navigate citation relationships seamlessly

### Performance Targets
- **Case Search**: <500ms response time
- **Citation Queries**: <1s for up to 3 depth levels
- **Graph Visualization**: <2s to render 50-node network
- **Most Cited**: <2s to compute top 100

---

## Next Steps

Ready to build this? Let's start with:

1. **Railway Setup**: Deploy PostgreSQL and create the schema
2. **Import System**: Build the robust CSV parser and parallel importer
3. **Citation API**: Implement the core citation endpoints
4. **Visualization**: Build the D3.js citation network graph

Which component would you like me to help you build first?

Let me know and I'll create the actual code files to get you started!
