"""
AI Risk Analyzer - Uses Claude AI to analyze citation risks

Two-tier analysis system:
- Quick Analysis: Claude Haiku 4.5 (fastest, near-frontier intelligence)
- Deep Analysis: Claude Sonnet 4.5 (comprehensive, maximum intelligence)

Provides AI-powered analysis including:
- Opinion text quality assessment
- Overturn status determination (OVERTURNED vs QUESTIONED)
- Legal impact analysis
- Practical guidance for practitioners
"""
import os
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic, APIError

logger = logging.getLogger(__name__)


class AIRiskAnalyzer:
    """
    Analyzes citation risks using Claude AI models

    Features:
    - Two-tier analysis: Quick (Haiku 4.5) or Deep (Sonnet 4.5)
    - Opinion text quality assessment
    - Overturn status determination
    - Practical guidance for legal practitioners
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
                model = "claude-haiku-4-5-20251001"  # Latest Haiku 4.5 (Oct 2024)
                model_name = "claude-haiku-4.5"
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

            # Call Claude API (standard request/response)
            logger.info(f"Requesting {model_name} analysis for case: {case_name}")

            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text from response
            analysis_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    analysis_text += block.text

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
            # Shorter prompt for Haiku - focus on quick summary with quality assessment
            prompt = f"""You are a legal research assistant analyzing a case flagged with citation risk.

**Case:** {case_name}
**Risk Classification:** {risk_type} ({severity}, {int(confidence * 100)}% confidence, {negative_count} negative citations)
**Citing Cases:**{citing_cases_text}

**Opinion Text:**
{opinion_text}

---

Provide a structured analysis in 3-4 paragraphs:

**1. Opinion Quality Assessment**
First, assess whether this is a high-quality opinion text or if it appears to be OCR/poor quality. Look for:
- Coherent legal reasoning and structure
- Proper formatting and citations
- Clear holdings and analysis
If the text quality is poor (garbled, OCR errors, incomplete), note this prominently as it affects the reliability of this analysis.

**2. Overturn Status**
Determine if this opinion has been **fully overturned** or just criticized/questioned. State clearly:
- "OVERTURNED" if reversed, vacated, or abrogated by a higher court
- "QUESTIONED" if criticized, distinguished, or called into doubt
- "PARTIAL" if only certain holdings are affected
Base this on the risk type ({risk_type}) and citing cases evidence.

**3. Why At Risk & Legal Impact**
Explain which specific holdings are challenged and what legal theories/doctrines are affected.

**4. Practical Guidance**
Should practitioners avoid citing this case entirely, or is it still valid for certain propositions?

Be direct and conclusive. If text quality prevents confident analysis, say so upfront."""
        else:
            # Full comprehensive prompt for Sonnet 4.5 with quality and overturn assessment
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

Please provide a comprehensive analysis addressing the following sections:

## 1. Opinion Text Quality Assessment
**First and foremost**, evaluate the quality and reliability of the opinion text itself:
- Is this a clean, well-formatted opinion with coherent legal reasoning?
- Are there signs of OCR errors, garbled text, or missing sections?
- Can you identify clear holdings and legal analysis?
- Does the text quality allow for confident analysis?

If the text quality is poor or unreliable, state this prominently at the start. Poor OCR quality or incomplete text significantly undermines the value of any subsequent analysis.

## 2. Overturn Status Determination
Make a clear determination about the current status of this case:

**OVERTURNED** - The case has been reversed, vacated, or abrogated by a higher court. The precedent is no longer binding or authoritative.

**QUESTIONED** - The case has been criticized, distinguished, or called into doubt but not formally overturned. Some precedential value remains but with caveats.

**PARTIALLY AFFECTED** - Only certain holdings or aspects of the case have been undermined. Other parts remain good law.

State your determination clearly and explain the basis (e.g., the risk type "{risk_type}" and evidence from citing cases).

## 3. Risk Overview and Affected Holdings
Explain in detail:
- Which specific legal issues, holdings, or reasoning have been challenged?
- What was the original precedent established by this case?
- How have subsequent courts treated or distinguished this precedent?

## 4. Impact on Legal Theories and Doctrines
Analyze the broader implications:
- What legal principles, doctrines, or tests are affected?
- How might the loss or weakening of this precedent impact legal practice?
- Are there alternative authorities practitioners should consider?
- What areas of law are most affected?

## 5. Connection to Citing Cases
Explain the relationship between this opinion and the cases citing it negatively:
- Why did subsequent courts take issue with this case?
- Are there factual distinctions or changes in legal landscape?
- Is the criticism focused on specific holdings or broader reasoning?
- Do citing cases offer alternative approaches?

## 6. Practical Implications for Practitioners
Provide clear, actionable guidance:
- Should this case be avoided entirely or can it still be cited for certain propositions?
- What are the risks of relying on this precedent?
- Are there stronger alternative authorities?
- In what contexts (if any) is this case still useful?
- Should lawyers distinguish or defend this case when opponents cite it?

**Important**: If the opinion text quality is poor, emphasize that practitioners should verify this analysis against an official reporter version before making citation decisions.

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
