"""
Bulk CSV Import API Endpoint
Trigger via: curl -X POST "https://your-api.railway.app/api/v1/bulk/import?limit=10000"
"""
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import csv
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy import text
from app.core.database import SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)

# Track import status
import_status = {
    "running": False,
    "progress": {},
    "error": None
}

def parse_value(value, field_name=None):
    """Parse CSV value"""
    if not value or value == '\\N' or value == 'NULL':
        return None
    if field_name in ['date_filed_is_approximate', 'blocked', 'in_use',
                      'has_opinion_scraper', 'has_oral_argument_scraper']:
        return 't' if value.lower() in ['true', 't', '1', 'yes'] else 'f'
    if field_name in ['id', 'docket_id', 'citation_count', 'source', 'depth',
                      'cited_opinion_id', 'citing_opinion_id', 'position']:
        try:
            return str(int(float(value)))
        except:
            return None
    return value

def do_import(
    courts_file: Optional[str],
    dockets_file: Optional[str],
    clusters_file: Optional[str],
    limit: Optional[int],
    batch_size: int
):
    """Background task to perform import"""
    global import_status
    import_status["running"] = True
    import_status["error"] = None
    import_status["progress"] = {}

    db = SessionLocal()
    project_root = Path(__file__).parent.parent.parent.parent.parent

    try:
        # Import courts
        if courts_file:
            logger.info(f"Importing courts from {courts_file}")
            csv_path = project_root / courts_file

            if not csv_path.exists():
                import_status["error"] = f"File not found: {courts_file}"
                return

            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch = []
                count = 0

                for row in reader:
                    if limit and count >= limit:
                        break

                    try:
                        db.execute(text("""
                            INSERT INTO search_court
                            (id, full_name, short_name, citation_string, in_use,
                             has_opinion_scraper, has_oral_argument_scraper, position)
                            VALUES (:id, :full_name, :short_name, :citation_string, :in_use,
                                    :has_opinion_scraper, :has_oral_argument_scraper, :position)
                            ON CONFLICT (id) DO NOTHING
                        """), {
                            'id': parse_value(row['id'], 'id'),
                            'full_name': parse_value(row.get('full_name', ''), 'full_name'),
                            'short_name': parse_value(row.get('short_name', ''), 'short_name'),
                            'citation_string': parse_value(row.get('citation_string', ''), 'citation_string'),
                            'in_use': parse_value(row.get('in_use', 't'), 'in_use'),
                            'has_opinion_scraper': parse_value(row.get('has_opinion_scraper', 'f'), 'has_opinion_scraper'),
                            'has_oral_argument_scraper': parse_value(row.get('has_oral_argument_scraper', 'f'), 'has_oral_argument_scraper'),
                            'position': parse_value(row.get('position', '0'), 'position'),
                        })
                        count += 1

                        if count % batch_size == 0:
                            db.commit()
                            import_status["progress"]["courts"] = count
                            logger.info(f"Imported {count} courts")

                    except Exception as e:
                        logger.error(f"Error importing court row: {e}")
                        continue

                db.commit()
                import_status["progress"]["courts"] = count
                logger.info(f"✅ Imported {count} courts total")

        # Import dockets
        if dockets_file:
            logger.info(f"Importing dockets from {dockets_file}")
            csv_path = project_root / dockets_file

            if not csv_path.exists():
                import_status["error"] = f"File not found: {dockets_file}"
                return

            with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                count = 0
                skipped = 0

                for row in reader:
                    if limit and count >= limit:
                        break

                    if not row.get('court_id'):
                        skipped += 1
                        continue

                    try:
                        db.execute(text("""
                            INSERT INTO search_docket
                            (id, date_created, date_modified, source, court_id, date_filed,
                             case_name_short, case_name, case_name_full, slug, docket_number)
                            VALUES (:id, :date_created, :date_modified, :source, :court_id, :date_filed,
                                    :case_name_short, :case_name, :case_name_full, :slug, :docket_number)
                            ON CONFLICT (id) DO NOTHING
                        """), {
                            'id': parse_value(row['id'], 'id'),
                            'date_created': parse_value(row.get('date_created'), 'date_created'),
                            'date_modified': parse_value(row.get('date_modified'), 'date_modified'),
                            'source': parse_value(row.get('source', '0'), 'source'),
                            'court_id': parse_value(row['court_id'], 'court_id'),
                            'date_filed': parse_value(row.get('date_filed'), 'date_filed'),
                            'case_name_short': parse_value(row.get('case_name_short'), 'case_name_short'),
                            'case_name': parse_value(row.get('case_name'), 'case_name'),
                            'case_name_full': parse_value(row.get('case_name_full'), 'case_name_full'),
                            'slug': parse_value(row.get('slug'), 'slug'),
                            'docket_number': parse_value(row.get('docket_number'), 'docket_number'),
                        })
                        count += 1

                        if count % batch_size == 0:
                            db.commit()
                            import_status["progress"]["dockets"] = count
                            import_status["progress"]["dockets_skipped"] = skipped
                            logger.info(f"Imported {count} dockets (skipped {skipped})")

                    except Exception as e:
                        logger.error(f"Error importing docket row: {e}")
                        skipped += 1
                        continue

                db.commit()
                import_status["progress"]["dockets"] = count
                import_status["progress"]["dockets_skipped"] = skipped
                logger.info(f"✅ Imported {count} dockets total (skipped {skipped})")

        # Import clusters
        if clusters_file:
            logger.info(f"Importing clusters from {clusters_file}")
            csv_path = project_root / clusters_file

            if not csv_path.exists():
                import_status["error"] = f"File not found: {clusters_file}"
                return

            with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                count = 0
                skipped = 0

                for row in reader:
                    if limit and count >= limit:
                        break

                    if not row.get('docket_id'):
                        skipped += 1
                        continue

                    try:
                        db.execute(text("""
                            INSERT INTO search_opinioncluster
                            (id, docket_id, date_created, date_modified, judges, date_filed,
                             date_filed_is_approximate, slug, case_name_short, case_name,
                             case_name_full, source, procedural_history, attorneys,
                             nature_of_suit, posture, syllabus, summary, disposition,
                             citation_count, precedential_status, blocked)
                            VALUES (:id, :docket_id, :date_created, :date_modified, :judges, :date_filed,
                                    :date_filed_is_approximate, :slug, :case_name_short, :case_name,
                                    :case_name_full, :source, :procedural_history, :attorneys,
                                    :nature_of_suit, :posture, :syllabus, :summary, :disposition,
                                    :citation_count, :precedential_status, :blocked)
                            ON CONFLICT (id) DO NOTHING
                        """), {
                            'id': parse_value(row['id'], 'id'),
                            'docket_id': parse_value(row['docket_id'], 'docket_id'),
                            'date_created': parse_value(row.get('date_created'), 'date_created'),
                            'date_modified': parse_value(row.get('date_modified'), 'date_modified'),
                            'judges': parse_value(row.get('judges'), 'judges'),
                            'date_filed': parse_value(row.get('date_filed'), 'date_filed'),
                            'date_filed_is_approximate': parse_value(row.get('date_filed_is_approximate', 'f'), 'date_filed_is_approximate'),
                            'slug': parse_value(row.get('slug'), 'slug'),
                            'case_name_short': parse_value(row.get('case_name_short'), 'case_name_short'),
                            'case_name': parse_value(row.get('case_name'), 'case_name'),
                            'case_name_full': parse_value(row.get('case_name_full'), 'case_name_full'),
                            'source': parse_value(row.get('source', '0'), 'source'),
                            'procedural_history': parse_value(row.get('procedural_history'), 'procedural_history'),
                            'attorneys': parse_value(row.get('attorneys'), 'attorneys'),
                            'nature_of_suit': parse_value(row.get('nature_of_suit'), 'nature_of_suit'),
                            'posture': parse_value(row.get('posture'), 'posture'),
                            'syllabus': parse_value(row.get('syllabus'), 'syllabus'),
                            'summary': parse_value(row.get('summary'), 'summary'),
                            'disposition': parse_value(row.get('disposition'), 'disposition'),
                            'citation_count': parse_value(row.get('citation_count', '0'), 'citation_count'),
                            'precedential_status': parse_value(row.get('precedential_status', 'Unknown'), 'precedential_status'),
                            'blocked': parse_value(row.get('blocked', 'f'), 'blocked'),
                        })
                        count += 1

                        if count % batch_size == 0:
                            db.commit()
                            import_status["progress"]["clusters"] = count
                            import_status["progress"]["clusters_skipped"] = skipped
                            logger.info(f"Imported {count} clusters (skipped {skipped})")

                    except Exception as e:
                        logger.error(f"Error importing cluster row: {e}")
                        skipped += 1
                        continue

                db.commit()
                import_status["progress"]["clusters"] = count
                import_status["progress"]["clusters_skipped"] = skipped
                logger.info(f"✅ Imported {count} clusters total (skipped {skipped})")

        logger.info("🎉 Import complete!")

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import_status["error"] = str(e)
    finally:
        import_status["running"] = False
        db.close()


@router.post("/import")
async def start_bulk_import(
    background_tasks: BackgroundTasks,
    courts: str = Query(None, description="Courts CSV filename"),
    dockets: str = Query(None, description="Dockets CSV filename"),
    clusters: str = Query(None, description="Clusters CSV filename"),
    limit: int = Query(None, description="Limit rows per file"),
    batch_size: int = Query(1000, description="Batch size")
):
    """
    Start bulk CSV import in background

    Examples:
        # Import 10K test records:
        POST /api/v1/bulk/import?courts=people_db_court-2025-10-31.csv&dockets=search_docket-sample.csv&limit=10000

        # Import all courts:
        POST /api/v1/bulk/import?courts=people_db_court-2025-10-31.csv
    """
    global import_status

    if import_status["running"]:
        return JSONResponse(
            status_code=409,
            content={"error": "Import already running", "progress": import_status["progress"]}
        )

    if not any([courts, dockets, clusters]):
        raise HTTPException(
            status_code=400,
            detail="Must specify at least one file: courts, dockets, or clusters"
        )

    background_tasks.add_task(
        do_import,
        courts_file=courts,
        dockets_file=dockets,
        clusters_file=clusters,
        limit=limit,
        batch_size=batch_size
    )

    return {
        "status": "started",
        "message": "Import started in background",
        "files": {
            "courts": courts,
            "dockets": dockets,
            "clusters": clusters
        },
        "limit": limit,
        "note": "Check /api/v1/bulk/status for progress"
    }


@router.get("/status")
async def get_import_status():
    """Get current import progress"""
    return {
        "running": import_status["running"],
        "progress": import_status["progress"],
        "error": import_status["error"]
    }
