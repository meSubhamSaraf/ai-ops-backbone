MESSAGE_CLASSIFIER_PROMPT = """
Classify the following Slack message.

Return STRICT JSON:

{{
    "type": "task/question/other",
    "confidence": 0.0
}}

Rules:

task:
A request or commitment where someone needs to perform an action.
Examples:
- I'll check this
- Let me verify
- Please investigate
- We will fix this

question:
A message asking for information or clarification.

other:
General discussion, acknowledgements, updates, or statements.

If unsure return:

{{
    "type": "other",
    "confidence": 0.0
}}

Message:
{message}
"""