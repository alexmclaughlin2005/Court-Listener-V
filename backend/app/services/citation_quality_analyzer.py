"""
Citation Quality Analyzer - AI-powered citation quality assessment

Uses Claude Haiku 3.5 to analyze whether a cited case is safe to rely upon as precedent.
Considers opinion text, treatment status, and citation context.
"""
import os
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic, APIError
from sqlalchemy.orm import Session

from app.models import (
    Opinion,
    CitationQualityAnalysis,
    CitationTreatment,
    QualityAssessment
)
from app.services.citation_data_fetcher import get_opinion_text

logger = logging.getLogger(__name__)

# Model configuration
HAIKU_MODEL = "claude-haiku-4-5-20251001"  # Latest Haiku 4.5
MAX_TOKENS = 1000  # Keep responses concise for faster analysis
MAX_OPINION_LENGTH = 150000  # ~37.5k tokens


class CitationQualityAnalyzer:
    """
    Analyzes citation quality using Claude Haiku 3.5

    Determines if a cited case is safe to rely upon by analyzing:
    - Full opinion text
    - Treatment status (overruled, questioned, etc.)
    - Citation patterns and context
    """

    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - AI analysis will be unavailable")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)

    def is_available(self) -> bool:
        """Check if AI analysis is available"""
        return self.client is not None

    def analyze_citation_quality(
        self,
        opinion: Opinion,
        db: Session
    ) -> Optional[Dict]:
        """
        Analyze citation quality using AI

        Args:
            opinion: Opinion object to analyze
            db: Database session

        Returns:
            Dict with analysis results matching schema:
            {
                "quality_assessment": "GOOD|QUESTIONABLE|OVERRULED|SUPERSEDED|UNCERTAIN",
                "confidence": 0.0-1.0,
                "is_overruled": bool,
                "is_questioned": bool,
                "is_criticized": bool,
                "risk_score": 0-100,
                "summary": "explanation text"
            }

        Returns None if analysis unavailable or fails
        """
        if not self.is_available():
            logger.warning("AI analysis unavailable - ANTHROPIC_API_KEY not set")
            return None

        # Get opinion text
        opinion_text = get_opinion_text(opinion, db, max_length=MAX_OPINION_LENGTH)
        if not opinion_text or len(opinion_text.strip()) < 100:
            logger.warning(f"Opinion {opinion.id} text too short or unavailable for analysis")
            return None

        # Get treatment data if available
        treatment = db.query(CitationTreatment).filter(
            CitationTreatment.opinion_id == opinion.id
        ).first()

        # Build context from treatment
        treatment_context = self._build_treatment_context(treatment)

        # Get case metadata
        case_metadata = self._get_case_metadata(opinion, db)

        try:
            # Build prompt
            prompt = self._build_quality_prompt(
                opinion_text=opinion_text,
                case_metadata=case_metadata,
                treatment_context=treatment_context
            )

            logger.info(f"Analyzing opinion {opinion.id} with Claude Haiku 4.5")

            # Call Claude API
            message = self.client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = message.content[0].text
            analysis = self._parse_ai_response(response_text)

            if analysis:
                logger.info(f"Analysis complete for opinion {opinion.id}: {analysis['quality_assessment']} (confidence: {analysis['confidence']})")
                return analysis
            else:
                logger.error(f"Failed to parse AI response for opinion {opinion.id}")
                return None

        except APIError as e:
            logger.error(f"Anthropic API error analyzing opinion {opinion.id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing opinion {opinion.id}: {e}")
            return None

    def _build_treatment_context(self, treatment: Optional[CitationTreatment]) -> Dict:
        """Build treatment context dict from CitationTreatment model"""
        if not treatment:
            return {
                "treatment_type": "UNKNOWN",
                "severity": "UNKNOWN",
                "negative_count": 0,
                "positive_count": 0,
                "neutral_count": 0,
                "confidence": 0.0,
                "evidence": None
            }

        return {
            "treatment_type": treatment.treatment_type.value,
            "severity": treatment.severity.value,
            "negative_count": treatment.negative_count or 0,
            "positive_count": treatment.positive_count or 0,
            "neutral_count": treatment.neutral_count or 0,
            "confidence": treatment.confidence or 0.0,
            "evidence": treatment.evidence
        }

    def _get_case_metadata(self, opinion: Opinion, db: Session) -> Dict:
        """Get case metadata for context"""
        metadata = {
            "opinion_id": opinion.id,
            "case_name": "Unknown",
            "court_name": "Unknown",
            "date_filed": None,
            "citation_count": 0
        }

        # Try to get cluster info
        if opinion.cluster_id:
            from app.models import OpinionCluster, Docket, Court

            cluster = db.query(OpinionCluster).filter(
                OpinionCluster.id == opinion.cluster_id
            ).first()

            if cluster:
                metadata["case_name"] = cluster.case_name or cluster.case_name_short or "Unknown"
                metadata["date_filed"] = cluster.date_filed.isoformat() if cluster.date_filed else None
                metadata["citation_count"] = cluster.citation_count or 0

                # Get court info
                if cluster.docket_id:
                    docket = db.query(Docket).filter(Docket.id == cluster.docket_id).first()
                    if docket and docket.court_id:
                        court = db.query(Court).filter(Court.id == docket.court_id).first()
                        if court:
                            metadata["court_name"] = court.short_name or "Unknown"

        return metadata

    def _build_quality_prompt(
        self,
        opinion_text: str,
        case_metadata: Dict,
        treatment_context: Dict
    ) -> str:
        """Build AI prompt for quality analysis"""
        # Format treatment evidence if available
        evidence_text = ""
        if treatment_context["evidence"]:
            evidence = treatment_context["evidence"]
            if isinstance(evidence, dict) and "examples" in evidence:
                examples = evidence["examples"][:3]  # Limit to 3 examples
                if examples:
                    evidence_text = "\nTreatment Examples:\n"
                    for ex in examples:
                        evidence_text += f"- {ex.get('text', '')}\n"

        prompt = f"""You are a legal research assistant analyzing case precedent. Evaluate this opinion based ONLY on its own content and metadata.

=== CASE METADATA ===
Case: {case_metadata['case_name']}
Court: {case_metadata['court_name']}
Date Filed: {case_metadata['date_filed'] or 'Unknown'}
Times Cited by Other Cases: {case_metadata['citation_count']}

=== FULL OPINION TEXT ===
{opinion_text}
=== END OPINION TEXT ===

=== YOUR TASK ===
Analyze this opinion's intrinsic precedential value by examining the opinion text itself:

1. **Was THIS Opinion Reversed or Overruled?**: CRITICAL - Check if THIS opinion states it has been reversed/overruled by a higher court:
   - Search for: "this opinion", "our decision", "our holding" + "reversed", "overruled", "vacated"
   - If THIS opinion was reversed/overruled → OVERRULED assessment
   - If THIS opinion is doing the reversing → Continue analysis (it may still be GOOD)

2. **Procedural Outcome of THIS Case**: What did this court decide?
   - "AFFIRMED" = This court agreed with lower court → GOOD (clear endorsement)
   - "REVERSED" = This court overturned lower court → GOOD (this court's reasoning is binding)
   - "REVERSED AND REMANDED" = Overturned and sent back → GOOD (clear legal holdings on why reversal occurred)
   - "DISMISSED" = Case thrown out on procedural grounds → QUESTIONABLE (may lack substantive holdings)
   - "VACATED" = Prior decision nullified → QUESTIONABLE (limited precedential value)

   IMPORTANT: If this opinion REVERSED a lower court, that means THIS opinion's reasoning is the binding precedent, not the lower court's decision.

3. **This Opinion's Effect on Prior Law**: Did this opinion overrule OTHER prior precedent?
   - Search for: "overruled", "overrule", "no longer good law", "superseded by statute", "abrogated"
   - If this opinion OVERRULED older cases → GOOD (this is the current law replacing old law)

4. **Holding vs. Dicta**:
   - Holding = rule necessary to decide the case (binding precedent)
   - Dicta = commentary not necessary to decision (persuasive only)
   - Is the main legal principle part of the actual holding?

5. **Quality of Reasoning**:
   - Is the legal analysis thorough and well-reasoned?
   - Does it cite relevant precedent and statutes?
   - Is the reasoning clear or convoluted?

6. **Court Authority**:
   - Higher courts = stronger precedent
   - En banc decisions > panel decisions
   - Consider: {case_metadata['court_name']}

7. **Age & Citation Count**:
   - Age: {case_metadata['date_filed'] or 'Unknown'}
   - Cited {case_metadata['citation_count']} times
   - Older cases with low citation counts may have limited relevance

CRITICAL RULES:
- DO NOT confuse the outcome: If THIS opinion says "REVERSED AND REMANDED", that means THIS COURT is creating binding precedent by overturning the lower court
- A "REVERSED" decision means THIS opinion's reasoning is the law, not the lower court's
- Only mark OVERRULED if THIS opinion states that IT (this opinion) has been reversed/overruled by a higher court
- If this opinion REVERSED or OVERRULED OTHER prior cases → GOOD (this is current law)
- If this opinion was AFFIRMED → GOOD (clear precedent)
- Only mark QUESTIONABLE if the reasoning is weak, dicta-heavy, dismissed on procedural grounds, or vacated
- Mark UNCERTAIN only if you cannot determine precedential value from the text

Return ONLY valid JSON (no explanatory text):

{{
  "quality_assessment": "GOOD" | "QUESTIONABLE" | "OVERRULED" | "SUPERSEDED" | "UNCERTAIN",
  "confidence": 0.0-1.0,
  "is_overruled": boolean,
  "is_questioned": boolean,
  "is_criticized": boolean,
  "risk_score": 0-100,
  "summary": "2-3 sentences explaining your assessment based on specific findings in the opinion text"
}}

**Assessment Categories:**
- **GOOD**: Clear holding, sound reasoning, proper procedural posture, currently binding precedent
- **QUESTIONABLE**: Weak reasoning, primarily dicta, or problematic procedural posture (dismissed/vacated)
- **OVERRULED**: This opinion explicitly states it has been overruled or superseded (rare - only if stated in text)
- **SUPERSEDED**: Opinion states it's superseded by statute/amendment (look for explicit language)
- **UNCERTAIN**: Cannot determine precedential value from opinion text and metadata alone

**Risk Score Guidelines:**
- 0-20: Strong binding precedent (affirmed holding, clear reasoning, authoritative court)
- 21-40: Solid precedent with minor concerns (older case, lower court, but good reasoning)
- 41-60: Moderate concerns (mixed dicta/holding, unclear reasoning, or procedural issues)
- 61-80: Significant issues (primarily dicta, weak reasoning, or dismissed/vacated)
- 81-100: Should not be cited as precedent (overruled, superseded, or no precedential value)"""

        return prompt

    def _parse_ai_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse AI response into structured format

        Args:
            response_text: Raw AI response text

        Returns:
            Parsed analysis dict or None if parsing fails
        """
        try:
            # Try to extract JSON from response
            # Sometimes Claude adds explanatory text before/after JSON
            response_text = response_text.strip()

            # Find JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx == -1 or end_idx == -1:
                logger.error("No JSON object found in AI response")
                return None

            json_str = response_text[start_idx:end_idx + 1]
            analysis = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "quality_assessment",
                "confidence",
                "is_overruled",
                "is_questioned",
                "is_criticized",
                "risk_score",
                "summary"
            ]

            for field in required_fields:
                if field not in analysis:
                    logger.error(f"Missing required field in AI response: {field}")
                    return None

            # Validate types and ranges
            if not isinstance(analysis["confidence"], (int, float)) or not (0 <= analysis["confidence"] <= 1):
                logger.error(f"Invalid confidence value: {analysis['confidence']}")
                return None

            if not isinstance(analysis["risk_score"], (int, float)) or not (0 <= analysis["risk_score"] <= 100):
                logger.error(f"Invalid risk_score value: {analysis['risk_score']}")
                return None

            # Validate quality_assessment enum
            valid_assessments = ["GOOD", "QUESTIONABLE", "OVERRULED", "SUPERSEDED", "UNCERTAIN"]
            if analysis["quality_assessment"] not in valid_assessments:
                logger.error(f"Invalid quality_assessment: {analysis['quality_assessment']}")
                return None

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing AI response: {e}")
            return None

    def get_cached_analysis(self, opinion_id: int, db: Session) -> Optional[CitationQualityAnalysis]:
        """
        Get cached analysis for an opinion

        Args:
            opinion_id: Opinion ID
            db: Database session

        Returns:
            CitationQualityAnalysis object or None if not cached
        """
        return db.query(CitationQualityAnalysis).filter(
            CitationQualityAnalysis.cited_opinion_id == opinion_id,
            CitationQualityAnalysis.analysis_version == 1  # Current version
        ).first()

    def save_analysis(
        self,
        opinion_id: int,
        analysis: Dict,
        db: Session
    ) -> Optional[CitationQualityAnalysis]:
        """
        Save analysis results to database

        Args:
            opinion_id: Opinion ID
            analysis: Analysis dict from analyze_citation_quality()
            db: Database session

        Returns:
            Saved CitationQualityAnalysis object or None on error
        """
        try:
            # Check if analysis already exists
            existing = self.get_cached_analysis(opinion_id, db)

            if existing:
                # Update existing
                existing.quality_assessment = analysis["quality_assessment"]
                existing.confidence = analysis["confidence"]
                existing.is_overruled = analysis["is_overruled"]
                existing.is_questioned = analysis["is_questioned"]
                existing.is_criticized = analysis["is_criticized"]
                existing.risk_score = analysis["risk_score"]
                existing.ai_summary = analysis["summary"]
                existing.ai_model = HAIKU_MODEL
                existing.analysis_version = 1

                db.commit()
                db.refresh(existing)

                logger.info(f"Updated cached analysis for opinion {opinion_id}")
                return existing
            else:
                # Create new
                quality_analysis = CitationQualityAnalysis(
                    cited_opinion_id=opinion_id,
                    quality_assessment=analysis["quality_assessment"],
                    confidence=analysis["confidence"],
                    is_overruled=analysis["is_overruled"],
                    is_questioned=analysis["is_questioned"],
                    is_criticized=analysis["is_criticized"],
                    risk_score=analysis["risk_score"],
                    ai_summary=analysis["summary"],
                    ai_model=HAIKU_MODEL,
                    analysis_version=1
                )

                db.add(quality_analysis)
                db.commit()
                db.refresh(quality_analysis)

                logger.info(f"Saved new analysis for opinion {opinion_id}")
                return quality_analysis

        except Exception as e:
            logger.error(f"Failed to save analysis for opinion {opinion_id}: {e}")
            db.rollback()
            return None
