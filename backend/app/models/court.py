"""
Court model - represents courts in the system
"""
from sqlalchemy import Column, String, Boolean, Float, Date, Text, SmallInteger, TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base


class Court(Base):
    """
    Court information - from search_court table
    
    Note: Based on the ERD, this table has many fields.
    We'll start with the essential ones and can add more as needed.
    """
    __tablename__ = "search_court"
    
    id = Column(String(15), primary_key=True)  # e.g., "scotus", "ca9", "njd"
    date_modified = Column(TIMESTAMP(timezone=True))
    in_use = Column(Boolean)
    has_opinion_scraper = Column(Boolean)
    has_oral_argument_scraper = Column(Boolean)
    position = Column(Float)  # Hierarchy level
    citation_string = Column(String(100))
    short_name = Column(String(100))
    full_name = Column(String(200))
    url = Column(String(500))
    start_date = Column(Date)
    end_date = Column(Date)
    jurisdiction = Column(String(3))
    notes = Column(Text)
    pacer_court_id = Column(SmallInteger)
    fic_court_id = Column(String(3))
    pacer_has_rss_feed = Column(Boolean)
    date_last_pacer_contact = Column(TIMESTAMP(timezone=True))
    pacer_rss_entry_types = Column(Text)
    
    # Relationships
    dockets = relationship("Docket", back_populates="court")

