"""
OpinionsCited model - the citation graph edges
"""
from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class OpinionsCited(Base):
    """
    OpinionsCited - THE CITATION GRAPH (70+ million edges!)
    
    This is the core of citation mapping.
    Each row represents: Opinion A cites Opinion B
    
    Structure:
    - citing_opinion_id: The opinion that makes the citation
    - cited_opinion_id: The opinion being cited
    - depth: Citation depth (1 = direct citation)
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
        backref="cites"  # opinions that this opinion cites
    )
    cited_opinion = relationship(
        "Opinion",
        foreign_keys=[cited_opinion_id],
        backref="cited_by"  # opinions that cite this opinion
    )
    
    # Critical indexes for citation queries
    __table_args__ = (
        Index('idx_opinionscited_citing', 'citing_opinion_id'),
        Index('idx_opinionscited_cited', 'cited_opinion_id'),
        Index('idx_opinionscited_both', 'citing_opinion_id', 'cited_opinion_id'),
        UniqueConstraint('citing_opinion_id', 'cited_opinion_id', name='uq_citing_cited'),
    )

