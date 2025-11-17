"""
Docket model - represents case dockets
"""
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Docket(Base):
    """
    Docket information - from search_docket table
    
    A docket represents a case filing. Multiple opinions can be associated
    with a single docket through OpinionCluster.
    """
    __tablename__ = "search_docket"
    
    id = Column(Integer, primary_key=True)
    date_created = Column(TIMESTAMP(timezone=True))
    date_modified = Column(TIMESTAMP(timezone=True))
    source = Column(Integer)
    
    # Case identification
    docket_number = Column(Text)
    docket_number_core = Column(String(20))
    case_name = Column(Text)
    case_name_short = Column(Text)
    case_name_full = Column(Text)
    slug = Column(String(75))
    
    # Dates
    date_filed = Column(Date)
    date_terminated = Column(Date)
    date_last_filing = Column(Date)
    date_argued = Column(Date)
    date_cert_granted = Column(Date)
    date_cert_denied = Column(Date)
    date_reargued = Column(Date)
    date_reargument_denied = Column(Date)
    date_blocked = Column(Date)
    date_last_index = Column(TIMESTAMP(timezone=True))
    
    # Case details
    cause = Column(Text)
    nature_of_suit = Column(Text)
    jury_demand = Column(Text)
    jurisdiction_type = Column(String(100))
    appellate_fee_status = Column(Text)
    appellate_case_type_information = Column(Text)
    mdl_status = Column(String(100))
    
    # PACER information
    pacer_case_id = Column(String(100))
    filepath_local = Column(String(1000))
    filepath_ia = Column(String(1000))
    filepath_ia_json = Column(String(1000))
    ia_upload_failure_count = Column(Integer)
    ia_needs_upload = Column(Boolean)
    ia_date_first_change = Column(TIMESTAMP(timezone=True))
    
    # Status
    blocked = Column(Boolean)
    view_count = Column(Integer, default=0)
    
    # Foreign keys
    court_id = Column(String(15), ForeignKey("search_court.id"))
    appeal_from_id = Column(String(15))
    assigned_to_id = Column(Integer)  # FK to people_db_person
    referred_to_id = Column(Integer)  # FK to people_db_person
    originating_court_information_id = Column(Integer)  # FK to search_originatingcourtinformation
    idb_data_id = Column(Integer)  # FK to recap_fjcintegrateddatabase
    parent_docket_id = Column(Integer)  # Self-referencing
    
    # String fields (for display when FK not available)
    appeal_from_str = Column(Text)
    assigned_to_str = Column(Text)
    referred_to_str = Column(Text)
    panel_str = Column(Text)
    
    # Federal district court specific fields
    federal_dn_case_type = Column(String(10))
    federal_dn_office_code = Column(String(10))
    federal_dn_judge_initials_assigned = Column(String(10))
    federal_dn_judge_initials_referred = Column(String(10))
    federal_defendant_number = Column(Integer)
    
    # Relationships
    court = relationship("Court", back_populates="dockets")
    clusters = relationship("OpinionCluster", back_populates="docket")
    
    # Indexes for search performance
    __table_args__ = (
        Index('idx_docket_court_id', 'court_id'),
        Index('idx_docket_date_filed', 'date_filed'),
        Index('idx_docket_case_name', 'case_name'),
        Index('idx_docket_docket_number', 'docket_number'),
    )

