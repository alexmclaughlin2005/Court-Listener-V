#!/usr/bin/env python3
"""
Run database migration to add citation quality analysis tables
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Execute the migration SQL"""
    print("Starting migration: Add citation quality analysis tables")
    print("This will create:")
    print("  - citation_quality_analysis table (stores individual citation assessments)")
    print("  - citation_analysis_tree table (stores complete analysis trees)")

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Read migration SQL
    migration_file = Path(__file__).parent / "add_citation_quality_tables.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Execute migration
    try:
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

            for statement in statements:
                if statement:
                    # Print abbreviated version for long statements
                    display = statement[:200] + "..." if len(statement) > 200 else statement
                    print(f"\nExecuting: {display}")

                    result = conn.execute(text(statement))

                    # If it's a SELECT, print results
                    if statement.upper().startswith('SELECT'):
                        rows = result.fetchall()
                        if rows:
                            print(f"  Found {len(rows)} results:")
                            for row in rows[:10]:  # Limit to first 10 rows
                                print(f"    {row}")
                            if len(rows) > 10:
                                print(f"    ... and {len(rows) - 10} more")

            conn.commit()
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("  1. Create SQLAlchemy models for these tables")
            print("  2. Implement citation_data_fetcher.py service")
            print("  3. Implement citation_quality_analyzer.py service")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("  - Check DATABASE_URL is set correctly")
        print("  - Ensure PostgreSQL is running")
        print("  - Verify search_opinion table exists")
        raise

if __name__ == "__main__":
    run_migration()
