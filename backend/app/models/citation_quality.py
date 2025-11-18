"""
Citation Quality models - stores AI-powered citation quality analysis
"""
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, Index, Boolean, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class QualityAssessment(str, enum.Enum):
    """Quality assessment categories for cited cases"""
    GOOD = "GOOD"                # Safe to cite, no negative treatment
    QUESTIONABLE = "QUESTIONABLE"  # Has some criticism or questioning
    OVERRULED = "OVERRULED"       # Explicitly overruled
    SUPERSEDED = "SUPERSEDED"     # Replaced by statute or newer precedent
    UNCERTAIN = "UNCERTAIN"       # Insufficient information to assess


class AnalysisStatus(str, enum.Enum):
    """Status of analysis tree processing"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CitationQualityAnalysis(Base):
    """
    CitationQualityAnalysis - individual citation quality assessments

    Stores AI-powered quality analysis for each cited opinion.
    Results are reusable across multiple analysis trees.

    This table acts as a cache to avoid re-analyzing the same
    citation across different analysis trees.
    """
    __tablename__ = "citation_quality_analysis"

    id = Column(Integer, primary_key=True)

    # The cited opinion being analyzed
    cited_opinion_id = Column(
        Integer,
        ForeignKey("search_opinion.id", ondelete="CASCADE"),
        nullable=False
    )

    # AI Analysis Results
    quality_assessment = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    ai_summary = Column(Text, nullable=True)  # Brief explanation from AI
    ai_model = Column(String(100), nullable=True)  # Model used (e.g., "claude-3-5-haiku-20241022")

    # Risk Indicators (boolean flags for quick filtering)
    is_overruled = Column(Boolean, default=False)
    is_questioned = Column(Boolean, default=False)
    is_criticized = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)  # 0-100 risk score

    # Metadata
    analysis_version = Column(Integer, default=1)  # For future re-analysis tracking
    analyzed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    cited_opinion = relationship("Opinion", foreign_keys=[cited_opinion_id])

    # Constraints and Indexes
    __table_args__ = (
        # Prevent duplicate analyses for same opinion/version
        UniqueConstraint('cited_opinion_id', 'analysis_version', name='unique_citation_quality'),
        Index('idx_citation_quality_opinion', 'cited_opinion_id'),
        Index('idx_citation_quality_assessment', 'quality_assessment'),
        Index('idx_citation_quality_risk', 'risk_score'),
        Index('idx_citation_quality_analyzed_at', 'analyzed_at'),
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "cited_opinion_id": self.cited_opinion_id,
            "quality_assessment": self.quality_assessment,
            "confidence": self.confidence,
            "ai_summary": self.ai_summary,
            "ai_model": self.ai_model,
            "is_overruled": self.is_overruled,
            "is_questioned": self.is_questioned,
            "is_criticized": self.is_criticized,
            "risk_score": self.risk_score,
            "analysis_version": self.analysis_version,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class CitationAnalysisTree(Base):
    """
    CitationAnalysisTree - complete citation analysis trees

    Stores the full citation tree analysis for a root opinion,
    including all levels analyzed and aggregated risk assessment.

    Supports incremental updates: if a tree exists with current_depth=2
    and max_depth=4 is requested, we can continue from level 3.

    Tree structure stored in JSONB for flexibility.
    """
    __tablename__ = "citation_analysis_tree"

    id = Column(Integer, primary_key=True)

    # Root opinion for this analysis tree
    root_opinion_id = Column(
        Integer,
        ForeignKey("search_opinion.id", ondelete="CASCADE"),
        nullable=False
    )

    # Analysis Configuration
    max_depth = Column(Integer, nullable=False)  # Depth requested (1-4)
    current_depth = Column(Integer, nullable=False)  # Deepest level completed so far

    # Aggregated Results (for quick stats without parsing JSONB)
    total_citations_analyzed = Column(Integer, default=0)
    good_count = Column(Integer, default=0)
    questionable_count = Column(Integer, default=0)
    overruled_count = Column(Integer, default=0)
    superseded_count = Column(Integer, default=0)
    uncertain_count = Column(Integer, default=0)

    # Risk Assessment
    overall_risk_score = Column(Float, default=0.0)  # 0-100
    overall_risk_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    risk_factors = Column(JSONB, nullable=True)  # Array of risk factor descriptions

    # Tree Structure (JSONB for flexibility)
    tree_data = Column(JSONB, nullable=False)  # Full citation tree with relationships
    high_risk_citations = Column(JSONB, nullable=True)  # Subset of most problematic citations

    # Metadata
    analysis_started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    analysis_completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    execution_time_seconds = Column(Float, nullable=True)

    # Performance metrics
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)

    # Status tracking
    status = Column(String(20), default='in_progress')  # in_progress, completed, failed
    error_message = Column(Text, nullable=True)

    # Relationships
    root_opinion = relationship("Opinion", foreign_keys=[root_opinion_id])

    # Constraints and Indexes
    __table_args__ = (
        # Allow multiple analyses per opinion (different depths, re-runs)
        # Only enforce uniqueness when analysis is complete
        UniqueConstraint('root_opinion_id', 'max_depth', 'analysis_completed_at', name='unique_tree_analysis'),
        Index('idx_tree_root_opinion', 'root_opinion_id'),
        Index('idx_tree_status', 'status'),
        Index('idx_tree_risk_level', 'overall_risk_level'),
        Index('idx_tree_completed', 'analysis_completed_at'),
        # GIN indexes for JSONB columns (for efficient JSON queries)
        Index('idx_tree_data', 'tree_data', postgresql_using='gin'),
        Index('idx_tree_high_risk', 'high_risk_citations', postgresql_using='gin'),
    )

    def to_dict(self, include_tree_data=False):
        """
        Convert to dictionary for API responses

        Args:
            include_tree_data: If True, include full tree_data (can be large)
        """
        result = {
            "id": self.id,
            "root_opinion_id": self.root_opinion_id,
            "max_depth": self.max_depth,
            "current_depth": self.current_depth,
            "total_citations_analyzed": self.total_citations_analyzed,
            "analysis_summary": {
                "good_count": self.good_count,
                "questionable_count": self.questionable_count,
                "overruled_count": self.overruled_count,
                "superseded_count": self.superseded_count,
                "uncertain_count": self.uncertain_count,
            },
            "overall_risk_assessment": {
                "score": self.overall_risk_score,
                "level": self.overall_risk_level,
                "factors": self.risk_factors,
            },
            "high_risk_citations": self.high_risk_citations,
            "status": self.status,
            "error_message": self.error_message,
            "analysis_started_at": self.analysis_started_at.isoformat() if self.analysis_started_at else None,
            "analysis_completed_at": self.analysis_completed_at.isoformat() if self.analysis_completed_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "execution_time_seconds": self.execution_time_seconds,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

        if include_tree_data:
            result["citation_tree"] = self.tree_data

        return result

    def is_complete(self) -> bool:
        """Check if analysis is complete"""
        return self.status == 'completed' and self.current_depth >= self.max_depth

    def can_extend_to_depth(self, new_depth: int) -> bool:
        """Check if this tree can be extended to a new depth"""
        return (
            self.status == 'completed' and
            new_depth > self.max_depth and
            self.current_depth >= self.max_depth
        )
