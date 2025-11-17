"""
Initialize database - create all tables
"""
from app.core.database import engine, Base
from app.models import Court, Docket, OpinionCluster, Opinion, OpinionsCited

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

