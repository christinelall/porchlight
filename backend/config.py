from __future__ import annotations

import os

APP_NAME = "Porchlight"
USE_STRANDS = os.getenv("PORCHLIGHT_USE_STRANDS", "0") == "1"

# Porchlight is built on Strands Agents. The model provider is intentionally swappable.
# If a Gemini API key is present and no provider is explicitly selected, use Gemini.
# This keeps the hackathon demo unblocked when a development AWS account cannot invoke Bedrock.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_PROVIDER = os.getenv("PORCHLIGHT_MODEL_PROVIDER") or ("gemini" if GEMINI_API_KEY else "bedrock")

if MODEL_PROVIDER == "gemini":
    MODEL_ID = os.getenv("PORCHLIGHT_MODEL_ID", "gemini-3.6-flash")
elif MODEL_PROVIDER == "bedrock":
    MODEL_ID = os.getenv("PORCHLIGHT_MODEL_ID", "global.amazon.nova-2-lite-v1:0")
else:
    MODEL_ID = os.getenv("PORCHLIGHT_MODEL_ID", "")

AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
