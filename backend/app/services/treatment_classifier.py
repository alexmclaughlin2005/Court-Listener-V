"""
Treatment Classifier - Detects citation treatment using keyword analysis

Analyzes parenthetical text to determine if a case has been:
- Negatively treated (overruled, reversed, questioned, etc.)
- Positively treated (affirmed, followed, applied, etc.)
- Neutrally treated (distinguished, cited, discussed, etc.)
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.models.citation_treatment import TreatmentType, Severity


# Keyword dictionaries with weighted scores
# Higher scores = stronger signal

NEGATIVE_KEYWORDS = {
    'overruled': 10,      # Strongest negative treatment
    'overruling': 10,
    'overrule': 10,
    'abrogated': 10,
    'abrogating': 10,
    'reversed': 9,
    'reversing': 9,
    'vacated': 9,
    'vacating': 9,
    'superseded': 9,
    'disapproved': 8,
    'disapproving': 8,
    'rejected': 7,
    'rejecting': 7,
    'questioned': 6,
    'questioning': 6,
    'doubted': 6,
    'criticized': 5,
    'criticizing': 5,
    'limited': 4,
    'limiting': 4,
    'narrowed': 4,
    'narrowing': 4,
}

POSITIVE_KEYWORDS = {
    'affirmed': 8,        # Strong positive treatment
    'affirming': 8,
    'followed': 7,
    'following': 7,
    'adopted': 7,
    'adopting': 7,
    'approved': 6,
    'approving': 6,
    'applied': 5,
    'applying': 5,
    'cited with approval': 8,
    'endorsed': 6,
    'endorsing': 6,
    'agreed': 5,
    'agreeing': 5,
}

NEUTRAL_KEYWORDS = {
    'distinguished': 5,   # Neutral but meaningful
    'distinguishing': 5,
    'explained': 3,
    'explaining': 3,
    'discussed': 2,
    'discussing': 2,
    'cited': 1,
    'citing': 1,
    'mentioned': 1,
    'mentioning': 1,
    'referenced': 1,
    'referencing': 1,
}

# Negation patterns that reverse positive keywords into negative
# Format: (pattern, keyword_to_negate, negative_score)
NEGATION_PATTERNS = [
    # Strong negations
    (r'declined\s+to\s+follow', 'followed', 8),
    (r'refused\s+to\s+follow', 'followed', 8),
    (r'declined\s+to\s+adopt', 'adopted', 8),
    (r'refused\s+to\s+adopt', 'adopted', 8),
    (r'declined\s+to\s+apply', 'applied', 7),
    (r'refused\s+to\s+apply', 'applied', 7),
    (r'not\s+followed', 'followed', 6),
    (r'no\s+longer\s+followed', 'followed', 9),
    (r'expressly\s+rejected', 'rejected', 9),

    # Conditional negations
    (r'declined\s+to\s+extend', 'extended', 5),
    (r'refused\s+to\s+extend', 'extended', 5),

    # Implicit negations through distinguishing
    (r'distinguished\s+and\s+rejected', 'rejected', 7),
    (r'distinguished\s+.*?\s+declined', 'declined', 6),
]

# Context modifiers - words that appear near keywords and modify meaning
CONTEXT_MODIFIERS = {
    # Intensifiers (increase score)
    'expressly': 1.3,
    'explicitly': 1.3,
    'clearly': 1.2,
    'unequivocally': 1.4,
    'categorically': 1.4,
    'firmly': 1.2,
    'strongly': 1.2,
    'completely': 1.3,

    # Weakeners (decrease score)
    'implicitly': 0.8,
    'arguably': 0.7,
    'possibly': 0.6,
    'potentially': 0.7,
    'might': 0.6,
    'could': 0.7,
    'seems': 0.7,
    'appears': 0.8,
}

# Context window size (characters before/after keyword)
CONTEXT_WINDOW = 50


@dataclass
class TreatmentSignal:
    """A detected treatment signal in parenthetical text"""
    keyword: str
    score: int
    severity: Severity
    position: int  # Character position in text


@dataclass
class TreatmentResult:
    """Result of analyzing a single parenthetical"""
    treatment_type: TreatmentType
    severity: Severity
    confidence: float  # 0.0 to 1.0
    signals: List[TreatmentSignal]
    text: str


@dataclass
class TreatmentSummary:
    """Aggregated treatment analysis for an opinion"""
    opinion_id: int
    treatment_type: TreatmentType
    severity: Severity
    confidence: float
    negative_count: int
    positive_count: int
    neutral_count: int
    total_parentheticals: int
    significant_treatments: List[Dict]  # List of notable treatment instances
    evidence: Optional[Dict] = None  # Evidence showing why this treatment was assigned


def normalize_text(text: str) -> str:
    """Normalize text for matching"""
    return text.lower().strip()


def get_context_modifier(text: str, position: int) -> float:
    """
    Check for context modifiers near a keyword position
    Returns a multiplier to apply to the score (1.0 = no modification)
    """
    # Extract context window around the keyword
    start = max(0, position - CONTEXT_WINDOW)
    end = min(len(text), position + CONTEXT_WINDOW)
    context = text[start:end].lower()

    # Check for modifiers in context
    modifier = 1.0
    for word, mult in CONTEXT_MODIFIERS.items():
        if word in context:
            # Apply strongest modifier if multiple found
            modifier = max(modifier, mult) if mult > 1.0 else min(modifier, mult)

    return modifier


def find_treatment_signals(text: str) -> List[TreatmentSignal]:
    """
    Find all treatment keywords in text and return signals with context awareness

    Enhancements:
    - Detects negation patterns ("declined to follow" vs "followed")
    - Applies context modifiers ("expressly overruled" stronger than "overruled")
    - Prevents false positives from reversed meanings
    """
    signals = []
    normalized = normalize_text(text)
    negated_positions = set()  # Track positions that are part of negation patterns

    # FIRST: Check for negation patterns (these override normal keywords)
    for pattern, negated_keyword, neg_score in NEGATION_PATTERNS:
        for match in re.finditer(pattern, normalized):
            # Mark all positions in this match as negated
            for pos in range(match.start(), match.end()):
                negated_positions.add(pos)

            # Add as negative signal with context modifier
            modifier = get_context_modifier(normalized, match.start())
            adjusted_score = int(neg_score * modifier)

            signals.append(TreatmentSignal(
                keyword=match.group(0),  # Full negation phrase
                score=adjusted_score,
                severity=Severity.NEGATIVE,
                position=match.start()
            ))

    # SECOND: Check regular keywords, but skip if part of a negation pattern
    for keyword, score in NEGATIVE_KEYWORDS.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for match in re.finditer(pattern, normalized):
            # Skip if this position is part of a negation pattern
            if match.start() in negated_positions:
                continue

            modifier = get_context_modifier(normalized, match.start())
            adjusted_score = int(score * modifier)

            signals.append(TreatmentSignal(
                keyword=keyword,
                score=adjusted_score,
                severity=Severity.NEGATIVE,
                position=match.start()
            ))

    for keyword, score in POSITIVE_KEYWORDS.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for match in re.finditer(pattern, normalized):
            # Skip if this position is part of a negation pattern
            if match.start() in negated_positions:
                continue

            modifier = get_context_modifier(normalized, match.start())
            adjusted_score = int(score * modifier)

            signals.append(TreatmentSignal(
                keyword=keyword,
                score=adjusted_score,
                severity=Severity.POSITIVE,
                position=match.start()
            ))

    for keyword, score in NEUTRAL_KEYWORDS.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for match in re.finditer(pattern, normalized):
            # Skip if this position is part of a negation pattern
            if match.start() in negated_positions:
                continue

            modifier = get_context_modifier(normalized, match.start())
            adjusted_score = int(score * modifier)

            signals.append(TreatmentSignal(
                keyword=keyword,
                score=adjusted_score,
                severity=Severity.NEUTRAL,
                position=match.start()
            ))

    return signals


def classify_parenthetical(text: str) -> TreatmentResult:
    """
    Classify a single parenthetical text for treatment type

    Returns:
        TreatmentResult with detected treatment type, severity, and confidence
    """
    signals = find_treatment_signals(text)

    if not signals:
        return TreatmentResult(
            treatment_type=TreatmentType.CITED,
            severity=Severity.NEUTRAL,
            confidence=0.3,  # Low confidence when no keywords found
            signals=[],
            text=text
        )

    # Calculate scores by severity
    negative_score = sum(s.score for s in signals if s.severity == Severity.NEGATIVE)
    positive_score = sum(s.score for s in signals if s.severity == Severity.POSITIVE)
    neutral_score = sum(s.score for s in signals if s.severity == Severity.NEUTRAL)

    total_score = negative_score + positive_score + neutral_score

    # Determine primary severity
    if negative_score > positive_score and negative_score > neutral_score:
        severity = Severity.NEGATIVE
        max_score = negative_score
    elif positive_score > negative_score and positive_score > neutral_score:
        severity = Severity.POSITIVE
        max_score = positive_score
    else:
        severity = Severity.NEUTRAL
        max_score = neutral_score

    # Determine specific treatment type based on strongest signal
    strongest_signal = max(signals, key=lambda s: s.score)
    treatment_type = _map_keyword_to_treatment_type(strongest_signal.keyword, severity)

    # Calculate confidence (0.0 to 1.0)
    # Higher confidence when:
    # - Multiple signals of same severity
    # - High-scoring keywords present
    # - Clear dominance of one severity
    confidence = min(1.0, (max_score / 10.0) * (1.0 + len([s for s in signals if s.severity == severity]) * 0.1))

    return TreatmentResult(
        treatment_type=treatment_type,
        severity=severity,
        confidence=confidence,
        signals=signals,
        text=text
    )


def _map_keyword_to_treatment_type(keyword: str, severity: Severity) -> TreatmentType:
    """Map a keyword to its specific treatment type"""
    keyword = keyword.lower()

    # Negative treatments
    if 'overrul' in keyword:
        return TreatmentType.OVERRULED
    elif 'revers' in keyword:
        return TreatmentType.REVERSED
    elif 'vacat' in keyword:
        return TreatmentType.VACATED
    elif 'abrogat' in keyword:
        return TreatmentType.ABROGATED
    elif 'supersed' in keyword:
        return TreatmentType.SUPERSEDED
    elif 'question' in keyword or 'doubt' in keyword:
        return TreatmentType.QUESTIONED
    elif 'criticiz' in keyword or 'disapprov' in keyword or 'reject' in keyword:
        return TreatmentType.CRITICIZED

    # Positive treatments
    elif 'affirm' in keyword:
        return TreatmentType.AFFIRMED
    elif 'follow' in keyword or 'adopt' in keyword or 'approv' in keyword or 'endors' in keyword:
        return TreatmentType.FOLLOWED

    # Neutral treatments
    elif 'distinguish' in keyword:
        return TreatmentType.DISTINGUISHED

    # Default based on severity
    elif severity == Severity.NEGATIVE:
        return TreatmentType.CRITICIZED
    elif severity == Severity.POSITIVE:
        return TreatmentType.FOLLOWED
    else:
        return TreatmentType.CITED


def analyze_opinion_treatment(
    opinion_id: int,
    parentheticals: List[Tuple[str, int, int]]  # [(text, described_id, describing_id), ...]
) -> TreatmentSummary:
    """
    Analyze all parentheticals mentioning an opinion to determine overall treatment

    Args:
        opinion_id: The opinion being analyzed
        parentheticals: List of (text, described_opinion_id, describing_opinion_id) tuples

    Returns:
        TreatmentSummary with aggregated analysis
    """
    if not parentheticals:
        return TreatmentSummary(
            opinion_id=opinion_id,
            treatment_type=TreatmentType.UNKNOWN,
            severity=Severity.UNKNOWN,
            confidence=0.0,
            negative_count=0,
            positive_count=0,
            neutral_count=0,
            total_parentheticals=0,
            significant_treatments=[]
        )

    # Classify each parenthetical
    results: List[Tuple[TreatmentResult, int, int]] = []  # (result, described_id, describing_id)
    for text, described_id, describing_id in parentheticals:
        result = classify_parenthetical(text)
        results.append((result, described_id, describing_id))

    # Count by severity
    negative_count = sum(1 for r, _, _ in results if r.severity == Severity.NEGATIVE)
    positive_count = sum(1 for r, _, _ in results if r.severity == Severity.POSITIVE)
    neutral_count = sum(1 for r, _, _ in results if r.severity == Severity.NEUTRAL)

    # Determine overall treatment
    # Negative treatments have higher weight in final determination
    if negative_count > 0:
        # Any negative treatment is significant
        severity = Severity.NEGATIVE
        # Find most severe negative treatment
        negative_results = [(r, d, g) for r, d, g in results if r.severity == Severity.NEGATIVE]
        strongest = max(negative_results, key=lambda x: x[0].confidence * max((s.score for s in x[0].signals), default=0))
        treatment_type = strongest[0].treatment_type
        confidence = min(1.0, 0.6 + (negative_count * 0.1))  # Higher confidence with more negative signals
    elif positive_count > neutral_count:
        severity = Severity.POSITIVE
        positive_results = [(r, d, g) for r, d, g in results if r.severity == Severity.POSITIVE]
        strongest = max(positive_results, key=lambda x: x[0].confidence)
        treatment_type = strongest[0].treatment_type
        confidence = min(1.0, 0.4 + (positive_count * 0.05))
    else:
        severity = Severity.NEUTRAL
        treatment_type = TreatmentType.CITED
        confidence = 0.3

    # Collect significant treatments (negative and high-confidence positive)
    significant = []
    negative_examples = []
    positive_examples = []
    total_negative_score = 0
    total_positive_score = 0

    for result, described_id, describing_id in results:
        # Calculate total scores
        for signal in result.signals:
            if signal.severity == Severity.NEGATIVE:
                total_negative_score += signal.score
            elif signal.severity == Severity.POSITIVE:
                total_positive_score += signal.score

        # Collect examples for evidence
        if result.severity == Severity.NEGATIVE:
            negative_examples.append({
                'text': result.text[:300],  # Truncate to 300 chars
                'keywords': [s.keyword for s in result.signals if s.severity == Severity.NEGATIVE],
                'score': sum(s.score for s in result.signals if s.severity == Severity.NEGATIVE),
                'describing_opinion_id': describing_id
            })
        elif result.severity == Severity.POSITIVE:
            positive_examples.append({
                'text': result.text[:300],
                'keywords': [s.keyword for s in result.signals if s.severity == Severity.POSITIVE],
                'score': sum(s.score for s in result.signals if s.severity == Severity.POSITIVE),
                'describing_opinion_id': describing_id
            })

        # Collect significant treatments for compatibility
        if result.severity == Severity.NEGATIVE or (result.severity == Severity.POSITIVE and result.confidence > 0.7):
            significant.append({
                'type': result.treatment_type.value,
                'severity': result.severity.value,
                'confidence': result.confidence,
                'described_opinion_id': described_id,
                'describing_opinion_id': describing_id,
                'excerpt': result.text[:200] + '...' if len(result.text) > 200 else result.text,
                'keywords': [s.keyword for s in result.signals[:3]]  # Top 3 keywords
            })

    # Sort examples by score and take top 5
    negative_examples.sort(key=lambda x: x['score'], reverse=True)
    positive_examples.sort(key=lambda x: x['score'], reverse=True)

    # Build evidence object
    evidence = {
        'summary': f"{treatment_type.value} based on {negative_count} negative, {positive_count} positive, {neutral_count} neutral parentheticals",
        'negative_examples': negative_examples[:5],  # Top 5 negative
        'positive_examples': positive_examples[:5],  # Top 5 positive
        'total_negative_score': total_negative_score,
        'total_positive_score': total_positive_score
    }

    # Sort significant treatments by confidence
    significant.sort(key=lambda x: x['confidence'], reverse=True)

    return TreatmentSummary(
        opinion_id=opinion_id,
        treatment_type=treatment_type,
        severity=severity,
        confidence=confidence,
        negative_count=negative_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        total_parentheticals=len(parentheticals),
        significant_treatments=significant[:10],  # Top 10 most significant
        evidence=evidence
    )
