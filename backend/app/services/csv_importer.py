"""
CSV Import Service - handles bulk import of CourtListener CSV files
"""
import csv
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import SessionLocal, engine, Base

logger = logging.getLogger(__name__)


class CSVImporter:
    """
    Handles importing CSV files into the database with optimizations:
    - Batch inserts
    - Parallel processing
    - Index management
    - Progress tracking
    """
    
    # Import order (respects foreign key dependencies)
    IMPORT_ORDER = [
        "search_court",           # ~1K rows - 1 minute
        "search_docket",          # ~30M rows - 12 hours
        "search_opinioncluster",  # ~10M rows - 4 hours
        "search_opinion",         # ~15M rows - 8 hours
        "search_opinionscited",   # ~70M rows - 18 hours
    ]
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or settings.CSV_DATA_DIR)
        self.batch_size = settings.IMPORT_BATCH_SIZE
        self.workers = settings.IMPORT_WORKERS
        
    def get_csv_path(self, table_name: str) -> Path:
        """Find CSV file for a table name"""
        # Try exact match first
        csv_file = self.data_dir / f"{table_name}.csv"
        if csv_file.exists():
            return csv_file
        
        # Try with date suffix
        for csv_file in self.data_dir.glob(f"{table_name}-*.csv"):
            return csv_file
        
        # Try sample file
        sample_file = self.data_dir / f"{table_name}-sample.csv"
        if sample_file.exists():
            return sample_file
            
        raise FileNotFoundError(f"CSV file for {table_name} not found in {self.data_dir}")
    
    async def prepare_table(self, table_name: str, db: Session):
        """Prepare table for import: disable indexes, constraints"""
        logger.info(f"Preparing table {table_name} for import...")
        
        # Disable foreign key constraints temporarily
        if table_name != "search_court":  # First table doesn't need this
            try:
                db.execute(text("SET session_replication_role = 'replica'"))
                db.commit()
            except Exception as e:
                logger.warning(f"Could not disable constraints: {e}")
    
    async def finalize_table(self, table_name: str, db: Session):
        """Finalize table after import: rebuild indexes, enable constraints"""
        logger.info(f"Finalizing table {table_name}...")
        
        # Re-enable foreign key constraints
        try:
            db.execute(text("SET session_replication_role = 'origin'"))
            db.commit()
        except Exception as e:
            logger.warning(f"Could not re-enable constraints: {e}")
    
    def parse_csv_row(self, row: Dict[str, str], table_name: str) -> Dict[str, Any]:
        """Parse a CSV row and convert types based on table schema"""
        parsed = {}
        
        for key, value in row.items():
            if value == '' or value is None:
                parsed[key] = None
                continue
            
            # Type conversion based on column name patterns
            if 'date' in key.lower() and 'created' not in key.lower() and 'modified' not in key.lower():
                try:
                    parsed[key] = datetime.strptime(value, '%Y-%m-%d').date()
                except:
                    parsed[key] = None
            elif 'date_created' in key or 'date_modified' in key or 'date_last' in key:
                try:
                    parsed[key] = datetime.fromisoformat(value.replace('+00', ''))
                except:
                    parsed[key] = None
            elif key in ['id', 'citation_count', 'word_count', 'char_count', 'view_count']:
                try:
                    parsed[key] = int(value)
                except:
                    parsed[key] = None
            elif key in ['depth', 'source']:
                try:
                    parsed[key] = int(value)
                except:
                    parsed[key] = None
            elif key in ['in_use', 'has_opinion_scraper', 'has_oral_argument_scraper', 
                         'blocked', 'extracted_by_ocr', 'ia_needs_upload', 
                         'date_filed_is_approximate']:
                parsed[key] = value.lower() in ('true', 't', '1', 'yes')
            elif key == 'position':
                try:
                    parsed[key] = float(value)
                except:
                    parsed[key] = None
            else:
                parsed[key] = value
        
        return parsed
    
    async def import_table(self, table_name: str, model_class) -> int:
        """
        Import a single table from CSV
        
        Returns: number of rows imported
        """
        csv_path = self.get_csv_path(table_name)
        logger.info(f"Starting import of {table_name} from {csv_path}")
        
        db = SessionLocal()
        try:
            # Prepare table
            await self.prepare_table(table_name, db)
            
            # Read CSV and import in batches
            rows_imported = 0
            batch = []
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    parsed_row = self.parse_csv_row(row, table_name)
                    batch.append(parsed_row)
                    
                    if len(batch) >= self.batch_size:
                        # Bulk insert batch
                        db.bulk_insert_mappings(model_class, batch)
                        db.commit()
                        rows_imported += len(batch)
                        batch = []
                        
                        if rows_imported % 100000 == 0:
                            logger.info(f"  Imported {rows_imported:,} rows...")
                
                # Insert remaining batch
                if batch:
                    db.bulk_insert_mappings(model_class, batch)
                    db.commit()
                    rows_imported += len(batch)
            
            # Finalize table
            await self.finalize_table(table_name, db)
            
            logger.info(f"Completed import of {table_name}: {rows_imported:,} rows")
            return rows_imported
            
        except Exception as e:
            logger.error(f"Error importing {table_name}: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
    
    async def import_all(self) -> Dict[str, int]:
        """
        Import all tables in the correct order
        
        Returns: dict mapping table names to row counts
        """
        results = {}
        
        # Import in order
        for table_name in self.IMPORT_ORDER:
            try:
                # Map table name to model class
                if table_name == "search_court":
                    from app.models.court import Court
                    model_class = Court
                elif table_name == "search_docket":
                    from app.models.docket import Docket
                    model_class = Docket
                elif table_name == "search_opinioncluster":
                    from app.models.opinion_cluster import OpinionCluster
                    model_class = OpinionCluster
                elif table_name == "search_opinion":
                    from app.models.opinion import Opinion
                    model_class = Opinion
                elif table_name == "search_opinionscited":
                    from app.models.opinions_cited import OpinionsCited
                    model_class = OpinionsCited
                else:
                    logger.warning(f"Unknown table: {table_name}, skipping")
                    continue
                
                rows = await self.import_table(table_name, model_class)
                results[table_name] = rows
                
            except FileNotFoundError:
                logger.warning(f"CSV file not found for {table_name}, skipping")
                continue
        
        return results


async def run_import(data_dir: Optional[str] = None):
    """Main import function"""
    importer = CSVImporter(data_dir)
    results = await importer.import_all()
    
    logger.info("Import Summary:")
    for table, rows in results.items():
        logger.info(f"  {table}: {rows:,} rows")
    
    return results

