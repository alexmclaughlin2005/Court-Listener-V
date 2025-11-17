"""
Opinion model - represents individual opinions (lead, concurrence, dissent)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Opinion(Base):
    """
    Opinion - individual opinion text from a case
    
    Each opinion belongs to an OpinionCluster and represents
    either a lead opinion, concurrence, or dissent.
    """
    __tablename__ = "search_opinion"
    
    id = Column(Integer, primary_key=True)
    date_created = Column(TIMESTAMP(timezone=True))
    date_modified = Column(TIMESTAMP(timezone=True))
    
    # Foreign key
    cluster_id = Column(Integer, ForeignKey("search_opinioncluster.id"), nullable=False)
    
    # Opinion content
    plain_text = Column(Text)  # Full text content
    html = Column(Text)  # HTML formatted text
    html_with_citations = Column(Text)  # HTML with citation links
    
    # Opinion type
    type = Column(String(20))  # "010lead", "020concurrence", "030dissent", etc.
    
    # File information
    sha1 = Column(String(40))
    download_url = Column(String(500))
    local_path = Column(String(500))
    
    # Text analysis
    extracted_by_ocr = Column(Boolean)
    word_count = Column(Integer)
    char_count = Column(Integer)
    
    # Relationships
    cluster = relationship("OpinionCluster", back_populates="sub_opinions")
    
    # Full-text search indexes
    __table_args__ = (
        Index('idx_opinion_cluster_id', 'cluster_id'),
        Index('idx_opinion_type', 'type'),
    )

