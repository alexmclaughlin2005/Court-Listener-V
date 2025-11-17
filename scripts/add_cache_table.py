"""
Script to add risk_analysis_cache table to database
"""
import sys
import os

# Add backend directory to path to import app modules
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_dir)

from app.core.database import engine
from app.models.risk_analysis_cache import RiskAnalysisCache

def create_cache_table():
    """Create the risk_analysis_cache table"""
    print("Creating risk_analysis_cache table...")

    try:
        # Create table if it doesn't exist
        RiskAnalysisCache.__table__.create(engine, checkfirst=True)
        print("✅ Successfully created risk_analysis_cache table")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

    return True

if __name__ == "__main__":
    success = create_cache_table()
    sys.exit(0 if success else 1)
