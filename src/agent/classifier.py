"""Gemini AI Classifier service module."""

import logging
from typing import Optional
from google import genai
from google.genai import types

from src.agent.schemas import ReviewClassification, Sentiment, Category, Urgency
from src.agent.instructions import SYSTEM_INSTRUCTION, build_user_prompt
from src import config

logger = logging.getLogger(__name__)


class ReviewClassifier:
    """Classifier class that communicates with Google Gemini API."""

    def __init__(self, api_key: str = config.GEMINI_API_KEY, model_name: str = config.GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        """Lazy initialization of Gemini client."""
        if self._client is None:
            if not self.api_key or self.api_key in ("your_api_key_here", "your_gemini_api_key_here"):
                raise ValueError("GEMINI_API_KEY environment variable is not configured in .env.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def classify(self, brand: str, product: str, star_rating: int, review_text: str) -> ReviewClassification:
        """Classify a single customer review using Gemini structured JSON outputs.

        Args:
            brand: Brand name.
            product: Product title.
            star_rating: Numeric star rating (1-5).
            review_text: Customer review text.

        Returns:
            ReviewClassification: Validated Pydantic schema object.
        """
        prompt = build_user_prompt(brand, product, star_rating, review_text)

        config_opts = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ReviewClassification,
            temperature=0.1,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config_opts,
        )

        # Parse and return validated Pydantic object
        if hasattr(response, "parsed") and response.parsed is not None:
            return response.parsed  # type: ignore

        # Fallback parsing if needed
        return ReviewClassification.model_validate_json(response.text)
