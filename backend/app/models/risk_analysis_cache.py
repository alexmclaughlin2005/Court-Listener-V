"""
Risk Analysis Cache model - stores pre-computed citation risk analysis
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class RiskAnalysisCache(Base):
    """
    Cache table for storing risk analysis results

    This avoids re-running expensive deep citation analysis
    for opinions that have already been analyzed.
    """
    __tablename__ = "risk_analysis_cache"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Opinion being analyzed
    opinion_id = Column(Integer, ForeignKey("opinions.id"), nullable=False, index=True)

    # Analysis parameters
    analysis_depth = Column(Integer, nullable=False, default=4)

    # Risk assessment results
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)  # LOW, MEDIUM, HIGH
    total_cases_analyzed = Column(Integer, nullable=False)
    negative_treatment_count = Column(Integer, nullable=False)

    # Full analysis data (JSON)
    analysis_data = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RiskAnalysisCache(opinion_id={self.opinion_id}, risk_level={self.risk_level}, score={self.risk_score})>"
