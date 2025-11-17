#!/usr/bin/env python3
"""
Test script for enhanced treatment classification with negation and context detection
"""
import sys
sys.path.insert(0, 'backend')

from app.services.treatment_classifier import classify_parenthetical, find_treatment_signals

# Test cases demonstrating the improvements
test_cases = [
    # Negation patterns
    {
        'text': 'declined to follow the Smith holding on qualified immunity',
        'expected': 'NEGATIVE',
        'description': 'Negation: "declined to follow" should be negative, not positive'
    },
    {
        'text': 'followed the reasoning in Jones v. State',
        'expected': 'POSITIVE',
        'description': 'Regular positive: "followed" without negation'
    },
    {
        'text': 'refused to adopt the test articulated in Martinez',
        'expected': 'NEGATIVE',
        'description': 'Negation: "refused to adopt" should be negative'
    },
    {
        'text': 'no longer followed after the Supreme Court decision',
        'expected': 'NEGATIVE',
        'description': 'Strong negation: "no longer followed" is very negative'
    },

    # Context modifiers
    {
        'text': 'expressly overruled the prior precedent',
        'expected': 'NEGATIVE',
        'description': 'Intensifier: "expressly overruled" should have higher score'
    },
    {
        'text': 'arguably questioned the validity of the earlier holding',
        'expected': 'NEGATIVE',
        'description': 'Weakener: "arguably questioned" should have lower score'
    },
    {
        'text': 'clearly affirmed the district court decision',
        'expected': 'POSITIVE',
        'description': 'Intensifier: "clearly affirmed" should have higher score'
    },
    {
        'text': 'possibly followed the same approach',
        'expected': 'POSITIVE',
        'description': 'Weakener: "possibly followed" should have lower score'
    },

    # Complex cases
    {
        'text': 'distinguished and rejected the Smith analysis',
        'expected': 'NEGATIVE',
        'description': 'Complex negation pattern with "distinguished and rejected"'
    },
    {
        'text': 'unequivocally reversed the lower court holding',
        'expected': 'NEGATIVE',
        'description': 'Strong intensifier: "unequivocally reversed"'
    },
]

def test_classification():
    print("=" * 80)
    print("Testing Enhanced Treatment Classification")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Text: \"{test['text']}\"")

        # Classify
        result = classify_parenthetical(test['text'])

        # Show signals detected
        print(f"  Signals detected:")
        for signal in result.signals:
            print(f"    - {signal.keyword} (score: {signal.score}, severity: {signal.severity.value})")

        print(f"  Result: {result.treatment_type.value} ({result.severity.value})")
        print(f"  Confidence: {result.confidence:.2f}")

        # Check if matches expected
        if result.severity.value == test['expected']:
            print(f"  ✅ PASS")
            passed += 1
        else:
            print(f"  ❌ FAIL - Expected {test['expected']}, got {result.severity.value}")
            failed += 1

        print()

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return passed, failed

def compare_before_after():
    """Show specific examples of how negation detection improves accuracy"""
    print("\n" + "=" * 80)
    print("Before vs After: Negation Detection")
    print("=" * 80)
    print()

    examples = [
        "declined to follow Smith",
        "followed Smith",
        "refused to adopt the test",
        "adopted the test",
    ]

    for text in examples:
        result = classify_parenthetical(text)
        print(f"Text: \"{text}\"")
        print(f"  Classification: {result.severity.value}")
        print(f"  Keywords: {[s.keyword for s in result.signals]}")
        print()

def compare_context_modifiers():
    """Show how context modifiers affect scores"""
    print("\n" + "=" * 80)
    print("Context Modifier Effects")
    print("=" * 80)
    print()

    pairs = [
        ("overruled the precedent", "expressly overruled the precedent"),
        ("followed the rule", "clearly followed the rule"),
        ("questioned the holding", "arguably questioned the holding"),
    ]

    for plain, modified in pairs:
        result1 = classify_parenthetical(plain)
        result2 = classify_parenthetical(modified)

        score1 = sum(s.score for s in result1.signals)
        score2 = sum(s.score for s in result2.signals)

        print(f"Plain:    \"{plain}\" = {score1} points")
        print(f"Modified: \"{modified}\" = {score2} points")
        print(f"  Difference: {score2 - score1:+d} points ({(score2/score1-1)*100:+.1f}%)")
        print()

if __name__ == '__main__':
    # Run tests
    passed, failed = test_classification()

    # Show comparisons
    compare_before_after()
    compare_context_modifiers()

    # Exit with status
    sys.exit(0 if failed == 0 else 1)
