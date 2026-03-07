ACTION_ITEM_PROMPT = """
Extract action items from this Slack message.

Return STRICT JSON:

{{
    "action_items": [
        {{
            "description": "...",
            "owner": "...",
            "due_date": "...",
            "priority": "low/medium/high"
        }}
    ]
}}

If no action items exist return:

{{
    "action_items": []
}}

Message:
{message}
"""