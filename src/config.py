"""Configuration management for Pax Distribution Review Triage."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV_PATH = BASE_DIR / "input" / "reviews_sample.csv"
OUTPUT_CSV_PATH = BASE_DIR / "outputs" / "Triage Results.csv"

# Gemini AI API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Resend Email Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
ALERT_EMAIL_RECIPIENT = os.getenv("ALERT_EMAIL_RECIPIENT", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")
