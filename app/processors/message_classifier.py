import json

from app.prompts.message_classifier.message_classifierv1 import MESSAGE_CLASSIFIER_PROMPT
from app.services.gemini_service import generate


def classify_message(message_text: str):

    prompt = MESSAGE_CLASSIFIER_PROMPT.format(message=message_text)

    response = generate(prompt)

    if response.startswith("```"):
        response = response.split("```")[1]
        response = response.replace("json", "").strip()

    try:
        result = json.loads(response)
        return result
    except Exception:
        return {
            "type": "other",
            "confidence": 0
        }