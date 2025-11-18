#!/usr/bin/env python3
"""
Import a single opinion from CourtListener API by opinion ID
"""
import os
import sys
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup database connection
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:GUYuYYTmYWGmUlcadtojoLWmhKFlHPJE@switchback.proxy.rlwy.net:49807/railway")
COURTLISTENER_API_TOKEN = "13aac3b8baaeb294226e3c82452815d41609b0d1"

def import_opinion(opinion_id: int):
    """Import opinion and all related data from CourtListener"""

    # Create database engine
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Fetch opinion from CourtListener
        print(f"Fetching opinion {opinion_id} from CourtListener...")
        headers = {"Authorization": f"Token {COURTLISTENER_API_TOKEN}"}

        # Get opinion data
        opinion_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
        opinion_response = requests.get(opinion_url, headers=headers)

        if opinion_response.status_code == 404:
            print(f"Opinion {opinion_id} not found on CourtListener")
            return

        opinion_response.raise_for_status()
        opinion_data = opinion_response.json()

        print(f"Opinion found: {opinion_data.get('absolute_url', 'N/A')}")

        # Get cluster data
        cluster_id = opinion_data.get("cluster_id")
        if cluster_id:
            cluster_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"
            cluster_response = requests.get(cluster_url, headers=headers)
            cluster_response.raise_for_status()
            cluster_data = cluster_response.json()

            case_name = cluster_data.get("case_name", "Unknown")
            date_filed = cluster_data.get("date_filed", "Unknown")
            print(f"Case: {case_name}")
            print(f"Date filed: {date_filed}")

            # Get docket data
            docket_id = cluster_data.get("docket_id")
            if docket_id:
                docket_url = f"https://www.courtlistener.com/api/rest/v4/dockets/{docket_id}/"
                docket_response = requests.get(docket_url, headers=headers)
                docket_response.raise_for_status()
                docket_data = docket_response.json()

                # Get court data
                court_id = docket_data.get("court_id")
                if court_id:
                    # Check if court exists
                    court_exists = db.execute(
                        text("SELECT EXISTS(SELECT 1 FROM search_court WHERE id = :court_id)"),
                        {"court_id": court_id}
                    ).scalar()

                    if not court_exists:
                        print(f"Importing court {court_id}...")
                        court_url = f"https://www.courtlistener.com/api/rest/v4/courts/{court_id}/"
                        court_response = requests.get(court_url, headers=headers)
                        court_response.raise_for_status()
                        court_data = court_response.json()

                        # Insert court
                        db.execute(text("""
                            INSERT INTO search_court (
                                id, position, date_modified, in_use, has_opinion_scraper,
                                has_oral_argument_scraper, jurisdiction, citation_string,
                                short_name, full_name, url, start_date, end_date, notes
                            ) VALUES (
                                :id, :position, NOW(), :in_use, :has_opinion_scraper,
                                :has_oral_argument_scraper, :jurisdiction, :citation_string,
                                :short_name, :full_name, :url, :start_date, :end_date, :notes
                            ) ON CONFLICT (id) DO NOTHING
                        """), {
                            "id": court_data.get("id"),
                            "position": court_data.get("position", 0),
                            "in_use": court_data.get("in_use", True),
                            "has_opinion_scraper": court_data.get("has_opinion_scraper", False),
                            "has_oral_argument_scraper": court_data.get("has_oral_argument_scraper", False),
                            "jurisdiction": court_data.get("jurisdiction", "F"),
                            "citation_string": court_data.get("citation_string", ""),
                            "short_name": court_data.get("short_name", ""),
                            "full_name": court_data.get("full_name", ""),
                            "url": court_data.get("url", ""),
                            "start_date": court_data.get("start_date"),
                            "end_date": court_data.get("end_date"),
                            "notes": court_data.get("notes", "")
                        })

                # Check if docket exists
                docket_exists = db.execute(
                    text("SELECT EXISTS(SELECT 1 FROM search_docket WHERE id = :docket_id)"),
                    {"docket_id": docket_id}
                ).scalar()

                if not docket_exists:
                    print(f"Importing docket {docket_id}...")
                    # Insert docket
                    db.execute(text("""
                        INSERT INTO search_docket (
                            id, date_created, date_modified, source, court_id,
                            appeal_from_str, assigned_to_str, referred_to_str,
                            panel_str, date_last_index, date_cert_granted, date_cert_denied,
                            date_argued, date_reargued, date_reargument_denied,
                            date_filed, date_terminated, date_last_filing,
                            case_name_short, case_name, case_name_full, slug,
                            docket_number, docket_number_core, pacer_case_id,
                            cause, nature_of_suit, jury_demand, jurisdiction_type,
                            appellate_fee_status, appellate_case_type_information,
                            mdl_status, filepath_local, filepath_ia, filepath_ia_json,
                            ia_upload_failure_count, ia_needs_upload, ia_date_first_change,
                            view_count, date_blocked, blocked
                        ) VALUES (
                            :id, NOW(), NOW(), :source, :court_id,
                            :appeal_from_str, :assigned_to_str, :referred_to_str,
                            :panel_str, :date_last_index, :date_cert_granted, :date_cert_denied,
                            :date_argued, :date_reargued, :date_reargument_denied,
                            :date_filed, :date_terminated, :date_last_filing,
                            :case_name_short, :case_name, :case_name_full, :slug,
                            :docket_number, :docket_number_core, :pacer_case_id,
                            :cause, :nature_of_suit, :jury_demand, :jurisdiction_type,
                            :appellate_fee_status, :appellate_case_type_information,
                            :mdl_status, :filepath_local, :filepath_ia, :filepath_ia_json,
                            :ia_upload_failure_count, :ia_needs_upload, :ia_date_first_change,
                            :view_count, :date_blocked, :blocked
                        ) ON CONFLICT (id) DO NOTHING
                    """), {
                        "id": docket_id,
                        "source": docket_data.get("source", 0),
                        "court_id": court_id,
                        "appeal_from_str": docket_data.get("appeal_from_str", ""),
                        "assigned_to_str": docket_data.get("assigned_to_str", ""),
                        "referred_to_str": docket_data.get("referred_to_str", ""),
                        "panel_str": docket_data.get("panel_str", ""),
                        "date_last_index": docket_data.get("date_last_index"),
                        "date_cert_granted": docket_data.get("date_cert_granted"),
                        "date_cert_denied": docket_data.get("date_cert_denied"),
                        "date_argued": docket_data.get("date_argued"),
                        "date_reargued": docket_data.get("date_reargued"),
                        "date_reargument_denied": docket_data.get("date_reargument_denied"),
                        "date_filed": docket_data.get("date_filed"),
                        "date_terminated": docket_data.get("date_terminated"),
                        "date_last_filing": docket_data.get("date_last_filing"),
                        "case_name_short": docket_data.get("case_name_short", ""),
                        "case_name": docket_data.get("case_name", ""),
                        "case_name_full": docket_data.get("case_name_full", ""),
                        "slug": docket_data.get("slug", ""),
                        "docket_number": docket_data.get("docket_number", ""),
                        "docket_number_core": docket_data.get("docket_number_core", ""),
                        "pacer_case_id": docket_data.get("pacer_case_id"),
                        "cause": docket_data.get("cause", ""),
                        "nature_of_suit": docket_data.get("nature_of_suit", ""),
                        "jury_demand": docket_data.get("jury_demand", ""),
                        "jurisdiction_type": docket_data.get("jurisdiction_type", ""),
                        "appellate_fee_status": docket_data.get("appellate_fee_status", ""),
                        "appellate_case_type_information": docket_data.get("appellate_case_type_information", ""),
                        "mdl_status": docket_data.get("mdl_status", ""),
                        "filepath_local": docket_data.get("filepath_local", ""),
                        "filepath_ia": docket_data.get("filepath_ia", ""),
                        "filepath_ia_json": docket_data.get("filepath_ia_json", ""),
                        "ia_upload_failure_count": docket_data.get("ia_upload_failure_count"),
                        "ia_needs_upload": docket_data.get("ia_needs_upload", False),
                        "ia_date_first_change": docket_data.get("ia_date_first_change"),
                        "view_count": docket_data.get("view_count", 0),
                        "date_blocked": docket_data.get("date_blocked"),
                        "blocked": docket_data.get("blocked", False)
                    })

            # Check if cluster exists
            cluster_exists = db.execute(
                text("SELECT EXISTS(SELECT 1 FROM search_opinioncluster WHERE id = :cluster_id)"),
                {"cluster_id": cluster_id}
            ).scalar()

            if not cluster_exists:
                print(f"Importing cluster {cluster_id}...")
                # Insert cluster (only fields that exist in our model)
                db.execute(text("""
                    INSERT INTO search_opinioncluster (
                        id, date_created, date_modified, judges,
                        source, citation_count, precedential_status, date_filed,
                        date_filed_is_approximate, slug, case_name_short,
                        case_name, case_name_full, scdb_id, scdb_decision_direction,
                        scdb_votes_majority, scdb_votes_minority,
                        docket_id
                    ) VALUES (
                        :id, NOW(), NOW(), :judges,
                        :source, :citation_count, :precedential_status, :date_filed,
                        :date_filed_is_approximate, :slug, :case_name_short,
                        :case_name, :case_name_full, :scdb_id, :scdb_decision_direction,
                        :scdb_votes_majority, :scdb_votes_minority,
                        :docket_id
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "id": cluster_id,
                    "judges": cluster_data.get("judges", ""),
                    "source": 0,  # TODO: Convert source letter to integer code
                    "citation_count": cluster_data.get("citation_count", 0),
                    "precedential_status": cluster_data.get("precedential_status", ""),
                    "date_filed": cluster_data.get("date_filed"),
                    "date_filed_is_approximate": cluster_data.get("date_filed_is_approximate", False),
                    "slug": cluster_data.get("slug", ""),
                    "case_name_short": cluster_data.get("case_name_short", ""),
                    "case_name": cluster_data.get("case_name", ""),
                    "case_name_full": cluster_data.get("case_name_full", ""),
                    "scdb_id": cluster_data.get("scdb_id") or None,
                    "scdb_decision_direction": cluster_data.get("scdb_decision_direction"),
                    "scdb_votes_majority": cluster_data.get("scdb_votes_majority"),
                    "scdb_votes_minority": cluster_data.get("scdb_votes_minority"),
                    "docket_id": docket_id
                })

        # Check if opinion exists
        opinion_exists = db.execute(
            text("SELECT EXISTS(SELECT 1 FROM search_opinion WHERE id = :opinion_id)"),
            {"opinion_id": opinion_id}
        ).scalar()

        if opinion_exists:
            print(f"Opinion {opinion_id} already exists in database!")
            return

        print(f"Importing opinion {opinion_id}...")
        # Insert opinion (only fields that exist in our model)
        db.execute(text("""
            INSERT INTO search_opinion (
                id, date_created, date_modified, type, sha1, download_url,
                local_path, plain_text, html, html_with_citations,
                extracted_by_ocr, cluster_id
            ) VALUES (
                :id, NOW(), NOW(), :type, :sha1, :download_url,
                :local_path, :plain_text, :html, :html_with_citations,
                :extracted_by_ocr, :cluster_id
            )
        """), {
            "id": opinion_id,
            "type": opinion_data.get("type", "010combined"),
            "sha1": opinion_data.get("sha1", ""),
            "download_url": opinion_data.get("download_url", ""),
            "local_path": opinion_data.get("local_path", ""),
            "plain_text": opinion_data.get("plain_text", ""),
            "html": opinion_data.get("html", ""),
            "html_with_citations": opinion_data.get("html_with_citations", ""),
            "extracted_by_ocr": opinion_data.get("extracted_by_ocr", False),
            "cluster_id": cluster_id
        })

        # Import citations if available (only for opinions that exist)
        opinions_cited = opinion_data.get("opinions_cited", [])
        if opinions_cited:
            print(f"Found {len(opinions_cited)} citations...")
            citations_added = 0
            for cited_url in opinions_cited:
                # Extract cited opinion ID from URL
                cited_id = int(cited_url.rstrip('/').split('/')[-1])

                # Check if cited opinion exists
                cited_exists = db.execute(
                    text("SELECT EXISTS(SELECT 1 FROM search_opinion WHERE id = :cited_id)"),
                    {"cited_id": cited_id}
                ).scalar()

                if cited_exists:
                    # Insert citation relationship
                    db.execute(text("""
                        INSERT INTO search_opinionscited (
                            citing_opinion_id, cited_opinion_id, depth
                        ) VALUES (
                            :citing_id, :cited_id, 1
                        ) ON CONFLICT (citing_opinion_id, cited_opinion_id) DO NOTHING
                    """), {
                        "citing_id": opinion_id,
                        "cited_id": cited_id
                    })
                    citations_added += 1

            print(f"Imported {citations_added}/{len(opinions_cited)} citations (skipped {len(opinions_cited) - citations_added} missing opinions)")

        db.commit()
        print(f"\n✅ Successfully imported opinion {opinion_id}")
        print(f"   Case: {case_name}")
        if opinions_cited:
            print(f"   Citations: {citations_added}/{len(opinions_cited)} imported")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error importing opinion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 import_opinion.py <opinion_id>")
        sys.exit(1)

    opinion_id = int(sys.argv[1])
    import_opinion(opinion_id)
