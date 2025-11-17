"""
Parenthetical model - represents parenthetical text describing how cases cite each other
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Parenthetical(Base):
    """
    Parenthetical - text describing the treatment of a cited case

    Example: "holding that contracts require consideration"
    or "overruling Smith v. Jones on procedural grounds"

    These parentheticals are analyzed to detect citation treatment
    (e.g., whether a case has been overruled, affirmed, etc.)
    """
    __tablename__ = "search_parenthetical"

    id = Column(Integer, primary_key=True)

    # Parenthetical content
    text = Column(Text, nullable=False)  # The actual parenthetical text
    score = Column(Float)  # Relevance/importance score from CourtListener

    # Opinion relationships
    # described_opinion = the case being described (the cited case)
    # describing_opinion = the case doing the describing (the citing case)
    described_opinion_id = Column(Integer, ForeignKey("search_opinion.id"), nullable=False)
    describing_opinion_id = Column(Integer, ForeignKey("search_opinion.id"), nullable=False)

    # Group ID for clustering related parentheticals
    group_id = Column(Integer)

    # Relationships
    described_opinion = relationship("Opinion", foreign_keys=[described_opinion_id])
    describing_opinion = relationship("Opinion", foreign_keys=[describing_opinion_id])

    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_parenthetical_described', 'described_opinion_id'),
        Index('idx_parenthetical_describing', 'describing_opinion_id'),
        Index('idx_parenthetical_group', 'group_id'),
    )
