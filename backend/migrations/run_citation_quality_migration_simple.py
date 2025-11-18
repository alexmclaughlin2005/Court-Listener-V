#!/usr/bin/env python3
"""
Run database migration to add citation quality analysis tables
Simplified version that uses DATABASE_URL from environment
"""
import os
import sys
from pathlib import Path
import psycopg2

def run_migration():
    """Execute the migration SQL"""
    print("Starting migration: Add citation quality analysis tables")
    print("This will create:")
    print("  - citation_quality_analysis table (stores individual citation assessments)")
    print("  - citation_analysis_tree table (stores complete analysis trees)")

    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("\n❌ DATABASE_URL environment variable not set")
        print("\nPlease set it with:")
        print('  export DATABASE_URL="postgresql://user:password@host:port/database"')
        sys.exit(1)

    print(f"\nConnecting to database...")

    # Read migration SQL
    migration_file = Path(__file__).parent / "add_citation_quality_tables.sql"
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Execute migration
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()

        # Execute entire SQL at once (let PostgreSQL handle statement ordering)
        print(f"\nExecuting migration SQL...")
        cursor.execute(migration_sql)

        # Fetch any SELECT results
        try:
            rows = cursor.fetchall()
            if rows:
                print(f"\n  Verification Results:")
                for row in rows[:20]:  # Show up to 20 rows
                    print(f"    {row}")
                if len(rows) > 20:
                    print(f"    ... and {len(rows) - 20} more")
        except psycopg2.ProgrammingError:
            # No results to fetch (normal for CREATE/ALTER statements)
            pass

        conn.commit()
        cursor.close()
        conn.close()

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
        if 'conn' in locals():
            conn.rollback()
        raise

if __name__ == "__main__":
    run_migration()
