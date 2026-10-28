"""Unit tests for agent schema validation, prompt structure, and edge cases."""

import pytest
from pydantic import ValidationError

from src.agent.schemas import (
    ReviewClassification,
    Sentiment,
    Category,
    Urgency,
    TriageRow,
)
from src.agent.instructions import SYSTEM_INSTRUCTION, build_user_prompt


def test_review_classification_pydantic_validation():
    data = {
        "sentiment": "Negative",
        "category": "Safety Concern",
        "urgency": "Critical",
        "english_summary": "The electric kettle started smoking and burned user fingers.",
        "suggested_action": "Issue immediate safety recall and contact user.",
    }

    result = ReviewClassification.model_validate(data)
    assert result.sentiment == Sentiment.NEGATIVE
    assert result.category == Category.SAFETY_CONCERN
    assert result.urgency == Urgency.CRITICAL


def test_invalid_sentiment_raises_validation_error():
    """Edge Case: Ensure Pydantic rejects non-standard sentiment values."""
    data = {
        "sentiment": "Extremely Happy",  # Invalid Enum
        "category": "Praise",
        "urgency": "Low",
        "english_summary": "Great product.",
        "suggested_action": "None.",
    }
    with pytest.raises(ValidationError):
        ReviewClassification.model_validate(data)


def test_invalid_urgency_raises_validation_error():
    """Edge Case: Ensure Pydantic rejects invalid urgency levels like 'Medium'."""
    data = {
        "sentiment": "Neutral",
        "category": "Other",
        "urgency": "Medium",  # Invalid Enum (Must be Critical, High, or Low)
        "english_summary": "Okay product.",
        "suggested_action": "None.",
    }
    with pytest.raises(ValidationError):
        ReviewClassification.model_validate(data)


def test_prompt_injection_guardrails_present():
    """Edge Case: Verify system instructions contain explicit prompt-injection defenses."""
    assert "untrusted" in SYSTEM_INSTRUCTION.lower()
    assert "ignore requests" in SYSTEM_INSTRUCTION.lower()


def test_star_rating_conflict_handling():
    """Edge Case: 5-Star rating with Critical safety hazard text."""
    data = {
        "sentiment": "Negative",
        "category": "Safety Concern",
        "urgency": "Critical",
        "english_summary": "Trekking poles snapped causing a fall despite 5-star rating.",
        "suggested_action": "Investigate hazard immediately.",
    }
    result = ReviewClassification.model_validate(data)
    assert result.urgency == Urgency.CRITICAL


def test_triage_row_empty_classification_fields():
    """Edge Case: Unclassified or Needs Manual Review rows leave classification columns empty."""
    row = TriageRow(
        review_id="R-1006",
        brand="Northvane",
        product="Headlamp",
        star_rating=1,
        status="Needs Manual Review",
        processed_at="2026-10-28T00:00:00",
    )
    csv_dict = row.to_csv_dict()
    assert csv_dict["Sentiment"] == ""
    assert csv_dict["Category"] == ""
    assert csv_dict["Urgency"] == ""
    assert csv_dict["Status"] == "Needs Manual Review"


def test_user_prompt_construction():
    prompt = build_user_prompt(
        brand="Northvane",
        product="Headlamp",
        star_rating=5,
        review_text="Great battery life.",
    )
    assert "Northvane" in prompt
    assert "Headlamp" in prompt
    assert "Great battery life." in prompt
