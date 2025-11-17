"""
OpinionCluster model - groups related opinions (lead, concurrence, dissent)
"""
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, TIMESTAMP, ForeignKey, ARRAY, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class OpinionCluster(Base):
    """
    OpinionCluster - groups related opinions from a single case
    
    A cluster typically contains:
    - One lead opinion
    - Zero or more concurrences
    - Zero or more dissents
    
    All opinions in a cluster share the same docket.
    """
    __tablename__ = "search_opinioncluster"
    
    id = Column(Integer, primary_key=True)
    date_created = Column(TIMESTAMP(timezone=True))
    date_modified = Column(TIMESTAMP(timezone=True))
    
    # Case identification
    slug = Column(String(75))
    case_name = Column(Text)
    case_name_short = Column(Text)
    case_name_full = Column(Text)
    
    # Dates
    date_filed = Column(Date)
    date_filed_is_approximate = Column(Boolean)
    
    # Citation information
    citation_count = Column(Integer, default=0)  # How many cases cite this cluster
    precedential_status = Column(String(50))
    
    # SCDB (Supreme Court Database) fields
    scdb_id = Column(String(10))
    scdb_decision_direction = Column(String(10))
    scdb_votes_majority = Column(Integer)
    scdb_votes_minority = Column(Integer)
    
    # Judges
    judges = Column(Text)  # Comma-separated judge names
    panel_ids = Column(ARRAY(Integer))  # Array of people_db_person IDs
    non_participating_judge_ids = Column(ARRAY(Integer))
    
    # Source
    source = Column(Integer)
    
    # Foreign keys
    docket_id = Column(Integer, ForeignKey("search_docket.id"), nullable=False)
    
    # Relationships
    docket = relationship("Docket", back_populates="clusters")
    sub_opinions = relationship("Opinion", back_populates="cluster")
    
    # Indexes
    __table_args__ = (
        Index('idx_cluster_docket_id', 'docket_id'),
        Index('idx_cluster_date_filed', 'date_filed'),
        Index('idx_cluster_citation_count', 'citation_count'),
    )

