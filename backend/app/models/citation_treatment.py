"""
CitationTreatment model - stores analyzed treatment status for opinions
"""
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TreatmentType(str, enum.Enum):
    """Types of citation treatment"""
    OVERRULED = "OVERRULED"
    REVERSED = "REVERSED"
    VACATED = "VACATED"
    ABROGATED = "ABROGATED"
    SUPERSEDED = "SUPERSEDED"
    AFFIRMED = "AFFIRMED"
    FOLLOWED = "FOLLOWED"
    DISTINGUISHED = "DISTINGUISHED"
    QUESTIONED = "QUESTIONED"
    CRITICIZED = "CRITICIZED"
    CITED = "CITED"
    UNKNOWN = "UNKNOWN"


class Severity(str, enum.Enum):
    """Severity of treatment"""
    NEGATIVE = "NEGATIVE"  # Case authority weakened (overruled, reversed, etc.)
    POSITIVE = "POSITIVE"  # Case authority strengthened (affirmed, followed, etc.)
    NEUTRAL = "NEUTRAL"   # Case discussed but authority unchanged (distinguished, cited)
    UNKNOWN = "UNKNOWN"   # Unable to determine


class CitationTreatment(Base):
    """
    CitationTreatment - cached treatment analysis results

    Stores the overall treatment status for an opinion based on
    analysis of all parentheticals mentioning it.

    This table acts as a cache to avoid re-analyzing parentheticals
    on every API request.
    """
    __tablename__ = "citation_treatment"

    id = Column(Integer, primary_key=True)

    # The opinion being analyzed
    opinion_id = Column(Integer, ForeignKey("search_opinion.id"), nullable=False, unique=True)

    # Treatment analysis results
    treatment_type = Column(Enum(TreatmentType), nullable=False, default=TreatmentType.UNKNOWN)
    severity = Column(Enum(Severity), nullable=False, default=Severity.UNKNOWN)

    # Treatment counts
    negative_count = Column(Integer, default=0)  # Number of negative treatments
    positive_count = Column(Integer, default=0)  # Number of positive treatments
    neutral_count = Column(Integer, default=0)   # Number of neutral treatments

    # Confidence score (0.0 to 1.0)
    confidence = Column(Float, default=0.0)

    # Timestamps
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    opinion = relationship("Opinion")

    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_treatment_opinion_id', 'opinion_id'),
        Index('idx_treatment_type', 'treatment_type'),
        Index('idx_treatment_severity', 'severity'),
        Index('idx_treatment_updated', 'last_updated'),
    )
