"""
AI Risk Analyzer - Uses Claude Sonnet 4.5 to analyze citation risks

Provides detailed AI-powered analysis of why a case is at risk, what legal
theories might be impacted, and the connection between citing and cited cases.
"""
import os
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic, APIError

logger = logging.getLogger(__name__)


class AIRiskAnalyzer:
    """Analyzes citation risks using Claude Sonnet 4.5"""

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

    async def analyze_citation_risk(
        self,
        opinion_text: str,
        case_name: str,
        risk_summary: Dict,
        citing_cases: List[Dict],
        max_tokens: int = 2000,
        use_quick_analysis: bool = False
    ) -> Optional[Dict]:
        """
        Analyze why a case is at risk using AI

        Args:
            opinion_text: Full text of the opinion at risk
            case_name: Name of the case
            risk_summary: Citation risk summary (type, severity, confidence, counts)
            citing_cases: List of cases that cite this opinion negatively
            max_tokens: Maximum response length
            use_quick_analysis: If True, uses Haiku for faster analysis; if False, uses Sonnet 4.5

        Returns:
            Dict with analysis results or None if unavailable
        """
        if not self.is_available():
            logger.warning("AI analysis unavailable - ANTHROPIC_API_KEY not set")
            return None

        if not opinion_text or len(opinion_text.strip()) < 100:
            logger.warning("Opinion text too short for analysis")
            return None

        # Truncate opinion text if too long (Claude has 200k token context window)
        # Rough estimate: 1 token ≈ 4 characters
        max_opinion_chars = 150000  # ~37.5k tokens for opinion text
        if len(opinion_text) > max_opinion_chars:
            opinion_text = opinion_text[:max_opinion_chars] + "\n\n[Text truncated for length]"

        try:
            # Select model based on analysis type
            if use_quick_analysis:
                model = "claude-3-5-haiku-20241022"
                model_name = "claude-3.5-haiku"
                # Use shorter prompt and fewer tokens for quick analysis
                if max_tokens > 1000:
                    max_tokens = 1000
            else:
                model = "claude-sonnet-4-5-20250929"
                model_name = "claude-sonnet-4.5"

            # Build the prompt
            prompt = self._build_analysis_prompt(
                opinion_text=opinion_text,
                case_name=case_name,
                risk_summary=risk_summary,
                citing_cases=citing_cases,
                quick_analysis=use_quick_analysis
            )

            # Call Claude API
            logger.info(f"Requesting {model_name} analysis for case: {case_name}")
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text response
            analysis_text = message.content[0].text if message.content else ""

            return {
                "analysis": analysis_text,
                "model": model_name,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return {
                "error": str(e),
                "analysis": None
            }
        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {e}")
            return {
                "error": str(e),
                "analysis": None
            }

    def _build_analysis_prompt(
        self,
        opinion_text: str,
        case_name: str,
        risk_summary: Dict,
        citing_cases: List[Dict],
        quick_analysis: bool = False
    ) -> str:
        """Build the prompt for Claude"""

        # Format risk summary
        risk_type = risk_summary.get('treatment_type', 'UNKNOWN')
        severity = risk_summary.get('severity', 'UNKNOWN')
        confidence = risk_summary.get('confidence', 0)
        negative_count = risk_summary.get('negative_count', 0)

        # Format citing cases
        citing_cases_text = ""
        for case in citing_cases[:5]:  # Limit to top 5 citing cases
            citing_cases_text += f"\n- {case.get('case_name', 'Unknown')} ({case.get('date_filed', 'Unknown date')})"
            if case.get('excerpt'):
                citing_cases_text += f"\n  Excerpt: \"{case['excerpt']}\""

        # Set default if no citing cases
        if not citing_cases_text:
            citing_cases_text = "\nNone provided"

        if quick_analysis:
            # Shorter prompt for Haiku - focus on quick summary
            prompt = f"""You are a legal research assistant. Analyze this case that has been flagged with citation risk.

**Case:** {case_name}
**Risk:** {risk_type} ({severity}, {int(confidence * 100)}% confidence, {negative_count} negative citations)
**Citing Cases:**{citing_cases_text}

**Opinion Text:**
{opinion_text}

---

Provide a brief analysis (2-3 paragraphs):
1. Why is this case at risk? What holdings are challenged?
2. What legal theories or doctrines might be affected?
3. Key practical implications for legal professionals.

Keep it concise and accessible."""
        else:
            # Full comprehensive prompt for Sonnet 4.5
            prompt = f"""You are a legal research assistant analyzing citation risks for case law. You have been provided with a legal opinion that has been flagged as having citation risk.

**Case Being Analyzed:**
{case_name}

**Citation Risk Summary:**
- Risk Type: {risk_type}
- Severity: {severity}
- Confidence: {int(confidence * 100)}%
- Number of negative citations: {negative_count}

**Cases Citing This Opinion Negatively:**{citing_cases_text}

**Full Opinion Text:**
{opinion_text}

---

Please provide a comprehensive analysis addressing the following:

## 1. Risk Overview
Explain in clear, accessible language why this case is at risk. What specific legal issues or holdings have been questioned, criticized, or overturned?

## 2. Impact on Legal Theories
Analyze what case theories, legal doctrines, or precedential value might be impacted if this case is no longer considered good law. Consider:
- What legal principles does this case establish?
- What doctrines or tests does it create or apply?
- How might practitioners need to adjust their arguments?

## 3. Connection to Citing Cases
Explain the relationship between this opinion and the cases that cite it negatively. Why did subsequent courts take issue with this case? Are there specific holdings, reasoning, or factual distinctions that led to the negative treatment?

## 4. Practical Implications
What should legal professionals know when considering whether to cite this case? Is it still useful for certain propositions while risky for others?

Please provide your analysis in a well-structured, professional format suitable for legal professionals."""

        return prompt


# Global instance
_analyzer = None

def get_ai_analyzer() -> AIRiskAnalyzer:
    """Get or create the global AI analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AIRiskAnalyzer()
    return _analyzer
