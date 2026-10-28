"""Pydantic schemas and Enums for review classification and triage results."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class Category(str, Enum):
    PRODUCT_DEFECT = "Product Defect"
    SAFETY_CONCERN = "Safety Concern"
    SHIPPING_PACKAGING = "Shipping/Packaging"
    WRONG_ITEM = "Wrong Item"
    LISTING_ACCURACY = "Listing Accuracy"
    PRAISE = "Praise"
    OTHER = "Other"


class Urgency(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    LOW = "Low"


class ReviewClassification(BaseModel):
    """Structured AI response schema returned by Gemini."""

    sentiment: Sentiment = Field(
        description="Sentiment of the review: Positive, Neutral, or Negative."
    )
    category: Category = Field(
        description="Primary topic/category of the review."
    )
    urgency: Urgency = Field(
        description="Assessed urgency level based on safety risks and defect severity."
    )
    english_summary: str = Field(
        description="One-sentence summary in English, regardless of review input language."
    )
    suggested_action: str = Field(
        description="One short, practical next step for the Pax Distribution team."
    )


class TriageRow(BaseModel):
    """Model representing a single row in the final Triage Results.csv."""

    review_id: str
    brand: str
    product: str
    star_rating: int
    sentiment: Optional[str] = ""
    category: Optional[str] = ""
    urgency: Optional[str] = ""
    english_summary: Optional[str] = ""
    suggested_action: Optional[str] = ""
    status: str
    processed_at: str

    def to_csv_dict(self) -> dict:
        """Return dict matching the exact 11 mandatory CSV column header names."""
        return {
            "Review ID": self.review_id,
            "Brand": self.brand,
            "Product": self.product,
            "Star Rating": self.star_rating,
            "Sentiment": self.sentiment or "",
            "Category": self.category or "",
            "Urgency": self.urgency or "",
            "English Summary": self.english_summary or "",
            "Suggested Action": self.suggested_action or "",
            "Status": self.status,
            "Processed At": self.processed_at,
        }
