#!/usr/bin/env python3
"""
Run database migration to add evidence column to citation_treatment table
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
    print("Starting migration: Add evidence column to citation_treatment")

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Read migration SQL
    migration_file = Path(__file__).parent / "add_evidence_column.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Execute migration
    try:
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

            for statement in statements:
                if statement:
                    print(f"\nExecuting: {statement[:100]}...")
                    result = conn.execute(text(statement))

                    # If it's a SELECT, print results
                    if statement.upper().startswith('SELECT'):
                        rows = result.fetchall()
                        for row in rows:
                            print(f"  Result: {row}")

            conn.commit()
            print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
