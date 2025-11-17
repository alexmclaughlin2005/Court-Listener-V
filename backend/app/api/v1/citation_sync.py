"""
Citation Sync API - On-demand citation fetching from CourtListener
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Opinion, OpinionsCited, OpinionCluster, Docket, Court
from datetime import datetime
import os
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# CourtListener API configuration (v4 is the latest)
CL_API_BASE = "https://www.courtlistener.com/api/rest/v4"
CL_API_TOKEN = os.environ.get('COURTLISTENER_API_TOKEN', '')


def get_api_headers():
    """Get headers for CourtListener API requests"""
    headers = {
        'User-Agent': 'CourtListener Case Law API (educational project)'
    }
    if CL_API_TOKEN:
        headers['Authorization'] = f'Token {CL_API_TOKEN}'
    return headers


async def fetch_and_import_opinion(opinion_id: int, db: Session, client: httpx.AsyncClient) -> bool:
    """
    Fetch opinion, cluster, and docket from CourtListener API and import into database

    Returns True if successfully imported, False otherwise
    """
    try:
        # Fetch opinion from API
        opinion_response = await client.get(
            f"{CL_API_BASE}/opinions/{opinion_id}/",
            headers=get_api_headers(),
            timeout=30.0
        )

        if opinion_response.status_code == 404:
            logger.warning(f"Opinion {opinion_id} not found in API")
            return False

        opinion_response.raise_for_status()
        opinion_data = opinion_response.json()

        # Extract cluster ID from opinion
        cluster_url = opinion_data.get('cluster')
        if not cluster_url:
            logger.warning(f"No cluster URL for opinion {opinion_id}")
            return False

        cluster_id = int(cluster_url.rstrip('/').split('/')[-1])

        # Check if cluster already exists
        existing_cluster = db.query(OpinionCluster).filter(OpinionCluster.id == cluster_id).first()

        if not existing_cluster:
            # Fetch cluster from API
            cluster_response = await client.get(
                f"{CL_API_BASE}/clusters/{cluster_id}/",
                headers=get_api_headers(),
                timeout=30.0
            )

            if cluster_response.status_code == 404:
                logger.warning(f"Cluster {cluster_id} not found in API")
                return False

            cluster_response.raise_for_status()
            cluster_data = cluster_response.json()

            # Extract docket ID
            docket_url = cluster_data.get('docket')
            if not docket_url:
                logger.warning(f"No docket URL for cluster {cluster_id}")
                return False

            docket_id = int(docket_url.rstrip('/').split('/')[-1])

            # Check if docket exists
            existing_docket = db.query(Docket).filter(Docket.id == docket_id).first()

            if not existing_docket:
                # Fetch docket from API
                docket_response = await client.get(
                    f"{CL_API_BASE}/dockets/{docket_id}/",
                    headers=get_api_headers(),
                    timeout=30.0
                )

                if docket_response.status_code == 404:
                    logger.warning(f"Docket {docket_id} not found in API")
                    return False

                docket_response.raise_for_status()
                docket_data = docket_response.json()

                # Extract court ID
                court_url = docket_data.get('court')
                court_id = None
                if court_url:
                    court_id = court_url.rstrip('/').split('/')[-1]

                    # Ensure court exists (or create stub)
                    existing_court = db.query(Court).filter(Court.id == court_id).first()
                    if not existing_court:
                        # Create minimal court record
                        new_court = Court(
                            id=court_id,
                            short_name=court_id,
                            full_name=f"Court {court_id}",
                            position=0
                        )
                        db.add(new_court)
                        db.flush()

                # Create docket
                new_docket = Docket(
                    id=docket_id,
                    docket_number=docket_data.get('docket_number'),
                    case_name=docket_data.get('case_name'),
                    case_name_short=docket_data.get('case_name_short'),
                    court_id=court_id,
                    date_filed=datetime.fromisoformat(docket_data['date_filed']).date() if docket_data.get('date_filed') else None,
                    date_created=datetime.now(),
                    date_modified=datetime.now()
                )
                db.add(new_docket)
                db.flush()

            # Create cluster
            new_cluster = OpinionCluster(
                id=cluster_id,
                docket_id=docket_id,
                case_name=cluster_data.get('case_name'),
                case_name_short=cluster_data.get('case_name_short'),
                case_name_full=cluster_data.get('case_name_full'),
                slug=cluster_data.get('slug'),
                date_filed=datetime.fromisoformat(cluster_data['date_filed']).date() if cluster_data.get('date_filed') else None,
                date_filed_is_approximate=cluster_data.get('date_filed_is_approximate', False),
                citation_count=cluster_data.get('citation_count', 0),
                precedential_status=cluster_data.get('precedential_status'),
                judges=cluster_data.get('judges'),
                date_created=datetime.now(),
                date_modified=datetime.now()
            )
            db.add(new_cluster)
            db.flush()
        else:
            cluster_id = existing_cluster.id

        # Check if opinion already exists
        existing_opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
        if existing_opinion:
            logger.info(f"Opinion {opinion_id} already exists")
            return True

        # Create opinion
        new_opinion = Opinion(
            id=opinion_id,
            cluster_id=cluster_id,
            type=opinion_data.get('type'),
            plain_text=opinion_data.get('plain_text'),
            html=opinion_data.get('html'),
            html_with_citations=opinion_data.get('html_with_citations'),
            extracted_by_ocr=opinion_data.get('extracted_by_ocr', False),
            sha1=opinion_data.get('sha1'),
            download_url=opinion_data.get('download_url'),
            date_created=datetime.now(),
            date_modified=datetime.now()
        )
        db.add(new_opinion)
        db.flush()

        logger.info(f"Successfully imported opinion {opinion_id}")
        return True

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching opinion {opinion_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error importing opinion {opinion_id}: {e}")
        return False


@router.post("/sync/{opinion_id}")
async def sync_opinion_citations(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch and import citations for a specific opinion from CourtListener API

    This endpoint:
    1. Checks if citations already exist
    2. Fetches from CourtListener API if needed
    3. Imports valid citations (where cited opinions exist locally)
    4. Returns status and counts
    """

    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

    # Check existing citations
    existing_count = db.query(OpinionsCited).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).count()

    # If we already have citations, return early
    if existing_count > 0:
        return {
            "opinion_id": opinion_id,
            "status": "already_synced",
            "existing_citations": existing_count,
            "new_citations": 0,
            "message": "Citations already exist for this opinion"
        }

    # Fetch from CourtListener API
    try:
        url = f"{CL_API_BASE}/opinions/{opinion_id}/"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=get_api_headers(), timeout=30.0)

            if response.status_code == 404:
                return {
                    "opinion_id": opinion_id,
                    "status": "not_found_in_api",
                    "existing_citations": 0,
                    "new_citations": 0,
                    "message": "Opinion not found in CourtListener API"
                }

            response.raise_for_status()
            opinion_data = response.json()

    except httpx.HTTPError as e:
        logger.error(f"API error for opinion {opinion_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch from CourtListener API: {str(e)}"
        )

    # Extract citations
    opinions_cited = opinion_data.get('opinions_cited', [])

    if not opinions_cited:
        return {
            "opinion_id": opinion_id,
            "status": "no_citations",
            "existing_citations": 0,
            "new_citations": 0,
            "message": "No citations found in API response"
        }

    # Parse cited opinion IDs
    cited_ids = []
    for cited_url in opinions_cited:
        try:
            cited_id = int(cited_url.rstrip('/').split('/')[-1])
            cited_ids.append(cited_id)
        except (ValueError, IndexError):
            logger.warning(f"Could not parse cited opinion URL: {cited_url}")
            continue

    if not cited_ids:
        return {
            "opinion_id": opinion_id,
            "status": "no_valid_citations",
            "existing_citations": 0,
            "new_citations": 0,
            "message": "No valid citation IDs could be parsed"
        }

    # Check which cited opinions exist in our database
    valid_cited_ids = set(
        row[0] for row in db.query(Opinion.id).filter(Opinion.id.in_(cited_ids)).all()
    )

    # Find missing opinions
    missing_ids = set(cited_ids) - valid_cited_ids

    # If we have missing opinions, try to fetch them from the API
    if missing_ids:
        logger.info(f"Fetching {len(missing_ids)} missing opinions from API for opinion {opinion_id}")
        fetched_count = 0
        failed_count = 0

        async with httpx.AsyncClient() as client:
            for missing_id in missing_ids:
                success = await fetch_and_import_opinion(missing_id, db, client)
                if success:
                    fetched_count += 1
                    valid_cited_ids.add(missing_id)  # Add to valid set
                else:
                    failed_count += 1

        logger.info(f"Fetched {fetched_count} opinions, {failed_count} failed")

    if not valid_cited_ids:
        return {
            "opinion_id": opinion_id,
            "status": "no_local_matches",
            "existing_citations": 0,
            "new_citations": 0,
            "api_citations_found": len(cited_ids),
            "message": "Citations found in API but cited opinions could not be imported"
        }

    # Import citations
    new_citations = []
    for cited_id in valid_cited_ids:
        citation = OpinionsCited(
            citing_opinion_id=opinion_id,
            cited_opinion_id=cited_id,
            depth=1
        )
        new_citations.append(citation)

    try:
        db.bulk_save_objects(new_citations)
        db.commit()

        # Calculate how many opinions were fetched
        fetched_opinions = len(missing_ids & valid_cited_ids) if missing_ids else 0

        message = f"Successfully imported {len(new_citations)} citations"
        if fetched_opinions > 0:
            message += f" (fetched {fetched_opinions} missing opinions from API)"

        return {
            "opinion_id": opinion_id,
            "status": "success",
            "existing_citations": 0,
            "new_citations": len(new_citations),
            "api_citations_found": len(cited_ids),
            "local_matches": len(valid_cited_ids),
            "fetched_opinions": fetched_opinions,
            "message": message
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Database error importing citations for opinion {opinion_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import citations: {str(e)}"
        )


@router.get("/check/{opinion_id}")
async def check_citation_status(
    opinion_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if an opinion has citations in the database

    Returns:
    - has_citations: boolean
    - citation_count: number of citations
    - needs_sync: whether we should try fetching from API
    """

    # Check if opinion exists
    opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
    if not opinion:
        raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

    # Count citations
    citation_count = db.query(OpinionsCited).filter(
        OpinionsCited.citing_opinion_id == opinion_id
    ).count()

    return {
        "opinion_id": opinion_id,
        "has_citations": citation_count > 0,
        "citation_count": citation_count,
        "needs_sync": citation_count == 0
    }
