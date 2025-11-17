"""
Sample data generator for testing the Court Listener application
Generates realistic but minimal sample data for all tables
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import random
from sqlalchemy.orm import Session
from app.models import Court, Docket, OpinionCluster, Opinion, OpinionsCited
import logging

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generate sample legal case data for testing"""

    # Sample court data (real court IDs from CourtListener)
    SAMPLE_COURTS = [
        {
            "id": "scotus",
            "full_name": "Supreme Court of the United States",
            "short_name": "Supreme Court",
            "citation_string": "S. Ct.",
            "in_use": True,
            "has_opinion_scraper": True,
            "has_oral_argument_scraper": False,
            "position": 1.0,
            "jurisdiction": "F"
        },
        {
            "id": "ca1",
            "full_name": "United States Court of Appeals for the First Circuit",
            "short_name": "First Circuit",
            "citation_string": "1st Cir.",
            "in_use": True,
            "has_opinion_scraper": True,
            "has_oral_argument_scraper": True,
            "position": 2.1,
            "jurisdiction": "F"
        },
        {
            "id": "ca9",
            "full_name": "United States Court of Appeals for the Ninth Circuit",
            "short_name": "Ninth Circuit",
            "citation_string": "9th Cir.",
            "in_use": True,
            "has_opinion_scraper": True,
            "has_oral_argument_scraper": True,
            "position": 2.9,
            "jurisdiction": "F"
        },
        {
            "id": "ca2",
            "full_name": "United States Court of Appeals for the Second Circuit",
            "short_name": "Second Circuit",
            "citation_string": "2d Cir.",
            "in_use": True,
            "has_opinion_scraper": True,
            "has_oral_argument_scraper": False,
            "position": 2.2,
            "jurisdiction": "F"
        },
        {
            "id": "cadc",
            "full_name": "United States Court of Appeals for the District of Columbia Circuit",
            "short_name": "D.C. Circuit",
            "citation_string": "D.C. Cir.",
            "in_use": True,
            "has_opinion_scraper": True,
            "has_oral_argument_scraper": True,
            "position": 2.12,
            "jurisdiction": "FD"
        }
    ]

    # Sample case names and legal topics
    CASE_TEMPLATES = [
        "Smith v. Jones",
        "United States v. Johnson",
        "Brown v. Board of Education",
        "Doe v. State of California",
        "People v. Williams",
        "SEC v. Corporation Inc.",
        "Johnson v. Department of Justice",
        "Miller v. County of Los Angeles",
        "Anderson v. City of New York",
        "Wilson v. State",
    ]

    LEGAL_TOPICS = [
        "civil rights", "criminal procedure", "constitutional law",
        "contract law", "tort law", "administrative law",
        "securities fraud", "employment discrimination", "habeas corpus",
        "first amendment", "fourth amendment", "due process"
    ]

    def __init__(self, db: Session):
        self.db = db
        self.created_courts = []
        self.created_dockets = []
        self.created_clusters = []
        self.created_opinions = []

    def generate_courts(self, count: int = 5) -> List[Court]:
        """Generate sample court records"""
        logger.info(f"Generating {count} sample courts...")
        courts = []

        for court_data in self.SAMPLE_COURTS[:count]:
            court = Court(**court_data)
            courts.append(court)

        self.db.bulk_save_objects(courts)
        self.db.commit()

        # Refresh to get database IDs
        for court in courts:
            self.db.refresh(court)

        self.created_courts = courts
        logger.info(f"Created {len(courts)} courts")
        return courts

    def generate_dockets(self, count: int = 20) -> List[Docket]:
        """Generate sample docket records"""
        logger.info(f"Generating {count} sample dockets...")
        dockets = []

        base_date = datetime.now() - timedelta(days=365*5)  # 5 years ago

        for i in range(count):
            court = random.choice(self.created_courts)
            date_filed = base_date + timedelta(days=random.randint(0, 365*5))

            docket = Docket(
                source=0,  # Default source
                court_id=court.id,
                docket_number=f"{random.randint(1, 99):02d}-{random.randint(1000, 9999)}",
                case_name=random.choice(self.CASE_TEMPLATES),
                case_name_short=random.choice(self.CASE_TEMPLATES).split(" v. ")[0],
                date_filed=date_filed.date(),
                date_created=date_filed,
                date_modified=datetime.now(),
            )
            dockets.append(docket)

        self.db.bulk_save_objects(dockets)
        self.db.commit()

        for docket in dockets:
            self.db.refresh(docket)

        self.created_dockets = dockets
        logger.info(f"Created {len(dockets)} dockets")
        return dockets

    def generate_opinion_clusters(self, count: int = 20) -> List[OpinionCluster]:
        """Generate sample opinion cluster records"""
        logger.info(f"Generating {count} sample opinion clusters...")
        clusters = []

        for docket in self.created_dockets[:count]:
            date_filed = docket.date_filed or date.today()

            cluster = OpinionCluster(
                docket_id=docket.id,
                judges=self._generate_judges(),
                date_filed=date_filed,
                date_filed_is_approximate=False,
                slug=f"{docket.case_name_short.lower().replace(' ', '-')}-{random.randint(1000, 9999)}",
                case_name=docket.case_name,
                case_name_short=docket.case_name_short,
                source="C",  # Court website
                precedential_status="Published",
                citation_count=random.randint(0, 50),
                date_created=docket.date_created,
                date_modified=datetime.now(),
            )
            clusters.append(cluster)

        self.db.bulk_save_objects(clusters)
        self.db.commit()

        for cluster in clusters:
            self.db.refresh(cluster)

        self.created_clusters = clusters
        logger.info(f"Created {len(clusters)} opinion clusters")
        return clusters

    def generate_opinions(self, count: int = 25) -> List[Opinion]:
        """Generate sample opinion records"""
        logger.info(f"Generating {count} sample opinions...")
        opinions = []

        opinion_types = ["010combined", "020lead", "030concurrence", "040dissent"]

        for i, cluster in enumerate(self.created_clusters):
            # Each cluster gets 1-2 opinions
            num_opinions = random.randint(1, 2)

            for j in range(num_opinions):
                opinion = Opinion(
                    cluster_id=cluster.id,
                    type=opinion_types[j] if j < len(opinion_types) else opinion_types[0],
                    author_str=self._generate_judge_name(),
                    plain_text=self._generate_opinion_text(cluster.case_name),
                    html=f"<p>{self._generate_opinion_text(cluster.case_name)}</p>",
                    extracted_by_ocr=False,
                    date_created=cluster.date_created,
                    date_modified=datetime.now(),
                )
                opinions.append(opinion)

                if len(opinions) >= count:
                    break

            if len(opinions) >= count:
                break

        self.db.bulk_save_objects(opinions)
        self.db.commit()

        for opinion in opinions:
            self.db.refresh(opinion)

        self.created_opinions = opinions
        logger.info(f"Created {len(opinions)} opinions")
        return opinions

    def generate_citations(self, count: int = 30) -> List[OpinionsCited]:
        """Generate sample citation relationships"""
        logger.info(f"Generating {count} sample citations...")
        citations = []

        # Create citations between opinions (citation network)
        for i in range(min(count, len(self.created_opinions) * 2)):
            citing_opinion = random.choice(self.created_opinions)
            cited_opinion = random.choice(self.created_opinions)

            # Don't cite yourself
            if citing_opinion.id == cited_opinion.id:
                continue

            # Check if citation already exists
            existing = any(
                c.citing_opinion_id == citing_opinion.id and
                c.cited_opinion_id == cited_opinion.id
                for c in citations
            )

            if existing:
                continue

            citation = OpinionsCited(
                citing_opinion_id=citing_opinion.id,
                cited_opinion_id=cited_opinion.id,
                depth=random.randint(1, 5)
            )
            citations.append(citation)

        self.db.bulk_save_objects(citations)
        self.db.commit()

        logger.info(f"Created {len(citations)} citations")
        return citations

    def _generate_judges(self) -> str:
        """Generate random judge names"""
        judges = [
            "Roberts, C.J.", "Thomas, J.", "Alito, J.",
            "Sotomayor, J.", "Kagan, J.", "Gorsuch, J.",
            "Barrett, J.", "Jackson, J."
        ]
        return ", ".join(random.sample(judges, k=random.randint(1, 3)))

    def _generate_judge_name(self) -> str:
        """Generate a single judge name"""
        judges = [
            "Roberts", "Thomas", "Alito", "Sotomayor",
            "Kagan", "Gorsuch", "Barrett", "Jackson"
        ]
        return random.choice(judges)

    def _generate_opinion_text(self, case_name: str) -> str:
        """Generate sample opinion text"""
        topic = random.choice(self.LEGAL_TOPICS)

        return f"""In the matter of {case_name}, this Court addresses important questions of {topic}.

The petitioner argues that the lower court erred in its interpretation of precedent.
After careful consideration of the arguments presented and review of relevant case law,
we find that the decision below must be affirmed.

The constitutional principles at stake require a careful balancing of interests.
The framers intended to protect fundamental rights while maintaining the proper
functioning of government institutions.

For these reasons, we hold that the judgment of the court below is AFFIRMED.
"""

    def generate_all_sample_data(
        self,
        courts: int = 5,
        dockets: int = 20,
        clusters: int = 20,
        opinions: int = 25,
        citations: int = 30
    ) -> Dict[str, int]:
        """
        Generate a complete sample dataset

        Returns dict with counts of created records
        """
        logger.info("Starting sample data generation...")

        results = {}

        # Generate in order (respecting foreign keys)
        results['courts'] = len(self.generate_courts(courts))
        results['dockets'] = len(self.generate_dockets(dockets))
        results['opinion_clusters'] = len(self.generate_opinion_clusters(clusters))
        results['opinions'] = len(self.generate_opinions(opinions))
        results['citations'] = len(self.generate_citations(citations))

        logger.info(f"Sample data generation complete: {results}")
        return results


def generate_sample_data(
    db: Session,
    courts: int = 5,
    dockets: int = 20,
    clusters: int = 20,
    opinions: int = 25,
    citations: int = 30
) -> Dict[str, int]:
    """
    Convenience function to generate sample data

    Args:
        db: Database session
        courts: Number of courts to create (max 5)
        dockets: Number of dockets to create
        clusters: Number of opinion clusters to create
        opinions: Number of opinions to create
        citations: Number of citation relationships to create

    Returns:
        Dict mapping table names to row counts
    """
    generator = SampleDataGenerator(db)
    return generator.generate_all_sample_data(
        courts=min(courts, 5),  # Max 5 sample courts available
        dockets=dockets,
        clusters=clusters,
        opinions=opinions,
        citations=citations
    )
