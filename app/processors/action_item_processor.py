import json
from dateutil import parser

from app.services.gemini_service import generate
from app.prompts.tasks.v1 import ACTION_ITEM_PROMPT
from app.repositories.action_item_repo import insert_action_item


def extract_action_items(message_text):

    prompt = ACTION_ITEM_PROMPT.format(message=message_text)

    ai_output = generate(prompt)

    if ai_output.startswith("```"):
        ai_output = ai_output.split("```")[1]
        ai_output = ai_output.replace("json", "").strip()

    parsed = json.loads(ai_output)

    return parsed.get("action_items", [])

def process_action_items(message_id, client_name, message_text, sender_name, conn, cur):

    action_items = extract_action_items(message_text)

    for item in action_items:

        owner = item.get("owner")

        if owner:
            owner = owner.lower()

        if owner in ["sender", "speaker", "me", "i", None]:
            owner = sender_name

        raw_due = item.get("due_date")
        parsed_due = None

        if raw_due:
            try:
                parsed_due = parser.parse(raw_due, fuzzy=True).date()
            except Exception:
                parsed_due = None

        insert_action_item(
            cur,
            client_name,
            item.get("description"),
            owner,
            parsed_due,
            item.get("priority"),
            message_id
        )

    return len(action_items)