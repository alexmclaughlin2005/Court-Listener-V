"""
Recursive Citation Analyzer - Breadth-first citation tree analysis

Orchestrates recursive citation quality analysis:
1. Fetch citations level by level (breadth-first)
2. Ensure opinion data exists (fetch from API if needed)
3. Run AI quality analysis (use cache if available)
4. Build complete citation tree with relationships
5. Calculate overall risk assessment
6. Re-evaluate parent citations if deep issues found
7. Save tree to database for incremental updates
"""
import logging
import time
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models import (
    Opinion,
    OpinionsCited,
    CitationQualityAnalysis,
    CitationAnalysisTree,
)
from app.services.citation_data_fetcher import (
    ensure_opinion_exists,
    get_opinion_text,
    get_opinion_citations,
)
from app.services.citation_quality_analyzer import CitationQualityAnalyzer

logger = logging.getLogger(__name__)

# Configuration
MAX_CITATIONS_PER_LEVEL = 100  # Limit citations per level to prevent explosion
HIGH_RISK_THRESHOLD = 60  # Risk scores >= 60 are considered high risk
RE_EVALUATION_THRESHOLD = 70  # Trigger parent re-evaluation if child >= 70


class RecursiveCitationAnalyzer:
    """
    Analyzes citation trees using breadth-first traversal

    Features:
    - Breadth-first traversal (all of level 1, then level 2, etc.)
    - Incremental updates (skip previously analyzed levels)
    - AI analysis with caching
    - Post-analysis re-evaluation of parents
    - Full tree storage in JSONB
    """

    def __init__(self):
        self.quality_analyzer = CitationQualityAnalyzer()

    def analyze_citation_tree(
        self,
        root_opinion_id: int,
        max_depth: int,
        db: Session,
        force_refresh: bool = False
    ) -> Dict:
        """
        Analyze citation tree up to specified depth

        Args:
            root_opinion_id: Root opinion to analyze
            max_depth: Maximum depth (1-4 levels)
            db: Database session
            force_refresh: If True, ignore cache and re-analyze

        Returns:
            Dict with complete analysis results
        """
        start_time = time.time()

        logger.info(f"Starting citation tree analysis for opinion {root_opinion_id}, depth={max_depth}")

        # Validate depth
        if not (1 <= max_depth <= 5):
            raise ValueError("max_depth must be between 1 and 5")

        # Check for existing tree (incremental update support)
        existing_tree = self._get_existing_tree(root_opinion_id, max_depth, db)

        if existing_tree and not force_refresh:
            if existing_tree.is_complete():
                logger.info(f"Found complete cached tree for opinion {root_opinion_id} at depth {max_depth}")
                return existing_tree.to_dict(include_tree_data=True)

            # Existing tree can be extended
            start_depth = existing_tree.current_depth + 1
            logger.info(f"Continuing analysis from depth {start_depth}")
        else:
            start_depth = 1
            # Create new tree record
            existing_tree = self._create_tree_record(root_opinion_id, max_depth, db)

        # Data structures for analysis
        all_citations = {}  # opinion_id -> citation data
        visited = {root_opinion_id}  # Prevent cycles
        current_level_ids = {root_opinion_id}
        cache_hits = 0
        cache_misses = 0

        # Level-by-level analysis (breadth-first)
        for depth in range(start_depth, max_depth + 1):
            logger.info(f"Analyzing level {depth} ({len(current_level_ids)} opinions)")

            if not current_level_ids:
                logger.info(f"No more citations at depth {depth}, stopping early")
                break

            # Get citations for current level
            level_citations, next_level_ids = self._analyze_level(
                current_level_ids=current_level_ids,
                depth=depth,
                visited=visited,
                db=db
            )

            # Track cache performance
            for citation in level_citations:
                if citation.get("from_cache"):
                    cache_hits += 1
                else:
                    cache_misses += 1

            # Add to all citations
            for citation in level_citations:
                all_citations[citation["opinion_id"]] = citation

            # Update visited set
            visited.update(next_level_ids)

            # Prepare for next level
            current_level_ids = next_level_ids

            # Limit per level
            if len(current_level_ids) > MAX_CITATIONS_PER_LEVEL:
                logger.warning(f"Level {depth + 1} has {len(current_level_ids)} citations, limiting to {MAX_CITATIONS_PER_LEVEL}")
                current_level_ids = set(list(current_level_ids)[:MAX_CITATIONS_PER_LEVEL])

        # Post-analysis re-evaluation
        logger.info("Running re-evaluation pass for parent citations")
        self._re_evaluate_parents(all_citations, max_depth)

        # Calculate overall risk assessment
        risk_assessment = self._calculate_overall_risk(all_citations)

        # Build citation tree structure
        tree_data = self._build_tree_structure(root_opinion_id, all_citations)

        # Extract high-risk citations
        high_risk_citations = self._extract_high_risk_citations(all_citations)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Update tree record
        self._update_tree_record(
            tree=existing_tree,
            current_depth=max_depth,
            all_citations=all_citations,
            risk_assessment=risk_assessment,
            tree_data=tree_data,
            high_risk_citations=high_risk_citations,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            execution_time=execution_time,
            db=db
        )

        logger.info(f"Analysis complete in {execution_time:.2f}s: {len(all_citations)} citations, {cache_hits} cache hits, {cache_misses} cache misses")

        return existing_tree.to_dict(include_tree_data=True)

    def _get_existing_tree(
        self,
        root_opinion_id: int,
        max_depth: int,
        db: Session
    ) -> Optional[CitationAnalysisTree]:
        """Get existing tree for incremental updates"""
        return db.query(CitationAnalysisTree).filter(
            CitationAnalysisTree.root_opinion_id == root_opinion_id,
            CitationAnalysisTree.max_depth == max_depth,
            CitationAnalysisTree.status.in_(['in_progress', 'completed'])
        ).order_by(
            CitationAnalysisTree.analysis_started_at.desc()
        ).first()

    def _create_tree_record(
        self,
        root_opinion_id: int,
        max_depth: int,
        db: Session
    ) -> CitationAnalysisTree:
        """Create new tree record"""
        tree = CitationAnalysisTree(
            root_opinion_id=root_opinion_id,
            max_depth=max_depth,
            current_depth=0,
            status='in_progress',
            tree_data={}
        )
        db.add(tree)
        db.commit()
        db.refresh(tree)
        return tree

    def _analyze_level(
        self,
        current_level_ids: Set[int],
        depth: int,
        visited: Set[int],
        db: Session
    ) -> Tuple[List[Dict], Set[int]]:
        """
        Analyze a single level of citations

        Returns:
            Tuple of (level_citations, next_level_ids)
        """
        level_citations = []
        next_level_ids = set()

        for opinion_id in current_level_ids:
            # Get citations for this opinion
            cited_ids = get_opinion_citations(opinion_id, db)

            for cited_id in cited_ids:
                if cited_id in visited:
                    continue  # Skip already visited (prevent cycles)

                # Ensure opinion exists
                opinion = ensure_opinion_exists(cited_id, db)
                if not opinion:
                    logger.warning(f"Opinion {cited_id} not found, skipping")
                    continue

                # Check for cached analysis
                cached_analysis = self.quality_analyzer.get_cached_analysis(cited_id, db)

                if cached_analysis:
                    # Use cached result
                    citation_data = {
                        "opinion_id": cited_id,
                        "depth": depth,
                        "quality_assessment": cached_analysis.quality_assessment,
                        "confidence": cached_analysis.confidence,
                        "risk_score": cached_analysis.risk_score,
                        "is_overruled": cached_analysis.is_overruled,
                        "is_questioned": cached_analysis.is_questioned,
                        "is_criticized": cached_analysis.is_criticized,
                        "summary": cached_analysis.ai_summary,
                        "from_cache": True,
                        "children": []  # Will be populated later
                    }
                    logger.debug(f"Using cached analysis for opinion {cited_id}")
                else:
                    # Run new analysis
                    if not self.quality_analyzer.is_available():
                        logger.warning(f"AI analysis unavailable for opinion {cited_id}, skipping")
                        continue

                    analysis = self.quality_analyzer.analyze_citation_quality(opinion, db)
                    if not analysis:
                        logger.warning(f"Analysis failed for opinion {cited_id}, skipping")
                        continue

                    # Save to cache
                    self.quality_analyzer.save_analysis(cited_id, analysis, db)

                    citation_data = {
                        "opinion_id": cited_id,
                        "depth": depth,
                        "quality_assessment": analysis["quality_assessment"],
                        "confidence": analysis["confidence"],
                        "risk_score": analysis["risk_score"],
                        "is_overruled": analysis["is_overruled"],
                        "is_questioned": analysis["is_questioned"],
                        "is_criticized": analysis["is_criticized"],
                        "summary": analysis["summary"],
                        "from_cache": False,
                        "children": []
                    }
                    logger.info(f"Completed analysis for opinion {cited_id}: {analysis['quality_assessment']} (risk: {analysis['risk_score']})")

                level_citations.append(citation_data)
                next_level_ids.add(cited_id)

        return level_citations, next_level_ids

    def _re_evaluate_parents(self, all_citations: Dict[int, Dict], max_depth: int):
        """
        Re-evaluate parent citations if children have high risk

        If a Level 3-4 citation has very high risk (>= 70), we should
        increase the risk of its parents (Levels 1-2) since they rely on it.
        """
        # Find high-risk deep citations (levels 3-4)
        high_risk_deep = [
            cit for cit in all_citations.values()
            if cit["depth"] >= 3 and cit["risk_score"] >= RE_EVALUATION_THRESHOLD
        ]

        if not high_risk_deep:
            logger.debug("No high-risk deep citations found, skipping re-evaluation")
            return

        logger.info(f"Found {len(high_risk_deep)} high-risk citations at depth >= 3, re-evaluating parents")

        # For now, just add a risk factor note to parents
        # In a more sophisticated implementation, we could:
        # 1. Track parent-child relationships in tree_data
        # 2. Increase parent risk scores proportionally
        # 3. Update parent summaries to mention problematic children

        # Simple approach: Mark any Level 1-2 citations as higher risk
        for citation in all_citations.values():
            if citation["depth"] <= 2:
                # Check if any children are high risk
                # (This is simplified - in production, track actual relationships)
                citation["has_high_risk_children"] = len(high_risk_deep) > 0

    def _calculate_overall_risk(self, all_citations: Dict[int, Dict]) -> Dict:
        """Calculate overall risk assessment for the tree"""
        if not all_citations:
            return {
                "score": 0.0,
                "level": "LOW",
                "confidence": 1.0,
                "factors": []
            }

        # Count by quality
        counts = defaultdict(int)
        for citation in all_citations.values():
            counts[citation["quality_assessment"]] += 1

        total = len(all_citations)
        negative_count = counts.get("OVERRULED", 0) + counts.get("SUPERSEDED", 0)
        questionable_count = counts.get("QUESTIONABLE", 0)

        # Calculate risk score
        negative_pct = (negative_count / total) * 100
        questionable_pct = (questionable_count / total) * 100

        # Depth-weighted risk (closer citations matter more)
        depth_weighted_risk = sum(
            (1.0 / max(cit["depth"], 1)) * cit["risk_score"]
            for cit in all_citations.values()
        ) / total

        # Combined risk score
        risk_score = min(
            (negative_pct * 0.5) + (questionable_pct * 0.3) + (depth_weighted_risk * 0.2),
            100
        )

        # Determine risk level
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Build risk factors
        factors = []
        if negative_count > 0:
            factors.append(f"{negative_count} overruled/superseded cases ({negative_pct:.1f}%)")
        if questionable_count > 0:
            factors.append(f"{questionable_count} questionable cases ({questionable_pct:.1f}%)")

        # Check for depth 1 issues (most critical)
        depth1_issues = [c for c in all_citations.values() if c["depth"] == 1 and c["risk_score"] >= HIGH_RISK_THRESHOLD]
        if depth1_issues:
            factors.append(f"{len(depth1_issues)} high-risk citations at depth 1")

        return {
            "score": round(risk_score, 2),
            "level": risk_level,
            "confidence": 0.85,  # Could be calculated based on analysis confidence
            "factors": factors
        }

    def _build_tree_structure(self, root_opinion_id: int, all_citations: Dict[int, Dict]) -> Dict:
        """Build hierarchical tree structure"""
        # For now, store as flat list organized by depth
        # In production, could build actual parent-child relationships
        tree = {
            "root_opinion_id": root_opinion_id,
            "citations_by_depth": {}
        }

        for citation in all_citations.values():
            depth = citation["depth"]
            if depth not in tree["citations_by_depth"]:
                tree["citations_by_depth"][depth] = []

            tree["citations_by_depth"][depth].append({
                "opinion_id": citation["opinion_id"],
                "quality_assessment": citation["quality_assessment"],
                "risk_score": citation["risk_score"],
                "summary": citation["summary"]
            })

        return tree

    def _extract_high_risk_citations(self, all_citations: Dict[int, Dict]) -> List[Dict]:
        """Extract high-risk citations for quick access"""
        high_risk = [
            {
                "opinion_id": cit["opinion_id"],
                "depth": cit["depth"],
                "quality_assessment": cit["quality_assessment"],
                "risk_score": cit["risk_score"],
                "summary": cit["summary"]
            }
            for cit in all_citations.values()
            if cit["risk_score"] >= HIGH_RISK_THRESHOLD
        ]

        # Sort by risk score (descending)
        high_risk.sort(key=lambda x: x["risk_score"], reverse=True)

        return high_risk[:20]  # Limit to top 20

    def _update_tree_record(
        self,
        tree: CitationAnalysisTree,
        current_depth: int,
        all_citations: Dict,
        risk_assessment: Dict,
        tree_data: Dict,
        high_risk_citations: List[Dict],
        cache_hits: int,
        cache_misses: int,
        execution_time: float,
        db: Session
    ):
        """Update tree record with analysis results"""
        # Count by quality
        counts = defaultdict(int)
        for citation in all_citations.values():
            counts[citation["quality_assessment"]] += 1

        # Update tree
        tree.current_depth = current_depth
        tree.total_citations_analyzed = len(all_citations)
        tree.good_count = counts.get("GOOD", 0)
        tree.questionable_count = counts.get("QUESTIONABLE", 0)
        tree.overruled_count = counts.get("OVERRULED", 0)
        tree.superseded_count = counts.get("SUPERSEDED", 0)
        tree.uncertain_count = counts.get("UNCERTAIN", 0)
        tree.overall_risk_score = risk_assessment["score"]
        tree.overall_risk_level = risk_assessment["level"]
        tree.risk_factors = risk_assessment["factors"]
        tree.tree_data = tree_data
        tree.high_risk_citations = high_risk_citations
        tree.cache_hits = cache_hits
        tree.cache_misses = cache_misses
        tree.execution_time_seconds = execution_time
        tree.status = 'completed'
        tree.analysis_completed_at = datetime.now()

        db.commit()
        db.refresh(tree)
