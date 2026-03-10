import json
from fastapi import APIRouter, Request

from app.database import get_connection

from app.repositories.raw_message_repo import insert_raw_message
from app.repositories.client_repo import get_client_from_channel

from app.processors.action_item_processor import process_action_items

from app.repositories.platform_user_repo import (
    get_platform_user,
    insert_platform_user
)

from app.services.slack_service import fetch_slack_user

from app.processors.message_classifier import classify_message

from app.processors.question_processor import process_question


router = APIRouter()


@router.post("/slack/events")
async def slack_events(request: Request):

    payload = await request.json()

    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    if payload.get("type") == "event_callback":

        event = payload.get("event")


        if event.get("subtype") == "bot_message":
            return {"status": "ignored"}

        conn = None
        cur = None

        try:

            conn = get_connection()
            cur = conn.cursor()

            sender_id = event.get("user")
            sender_name = None

            if sender_id:
            
                sender_name = get_platform_user(cur, "slack", sender_id)

                if not sender_name:
                
                    user_data = fetch_slack_user(sender_id)

                    if user_data:
                    
                        insert_platform_user(
                            cur,
                            "slack",
                            sender_id,
                            user_data["real_name"],
                            user_data["display_name"],
                            user_data["email"]
                        )


            row = insert_raw_message(
                cur,
                "slack",
                event.get("event_ts"),
                event.get("text"),
                json.dumps(payload)
            )

            if not row:
                conn.commit()
                return {"status": "duplicate_ignored"}

            message_id = row[0]

            client_name = get_client_from_channel(
                cur,
                event.get("channel")
            )

            message_text = event.get("text")

            classification = classify_message(message_text)

            message_type = classification.get("type")

            if message_type == "task":
            
                process_action_items(
                    message_id,
                    client_name,
                    message_text,
                    sender_name,
                    conn,
                    cur
                )
                
            elif message_type == "question":
                product = "connect_api" #temporary , need to add in DB of client channel and get it from there
                process_question(
                    message_id,
                    client_name,
                    product,
                    message_text,
                    cur
                )

            cur.execute(
                "UPDATE raw_messages SET processed=true WHERE id=%s",
                (message_id,)
            )

            conn.commit()

        finally:

            if cur:
                cur.close()

            if conn:
                conn.close()

    return {"status": "ok"}