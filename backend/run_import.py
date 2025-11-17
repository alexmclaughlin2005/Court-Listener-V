"""
Script to run CSV import manually
"""
import asyncio
import sys
from pathlib import Path
from app.services.csv_importer import run_import

if __name__ == "__main__":
    # Get data directory from command line or use default
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "../data"
    
    print(f"Starting import from: {data_dir}")
    print("This may take several hours for large datasets...")
    
    try:
        results = asyncio.run(run_import(data_dir))
        
        print("\n" + "="*50)
        print("Import Summary:")
        print("="*50)
        for table, rows in results.items():
            print(f"  {table}: {rows:,} rows")
        print("="*50)
        
    except Exception as e:
        print(f"Import failed: {e}", file=sys.stderr)
        sys.exit(1)

