from fastapi import FastAPI, Request
import psycopg2
import os
from dotenv import load_dotenv
import json
import google.generativeai as genai
from dateutil import parser

load_dotenv()

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@app.get("/")
def health():
    return {"status": "AI Ops Backend Running"}


@app.get("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"database_time": result}
    except Exception as e:
        return {"error": str(e)}


# ------------------------------
# Core AI Processing Logic
# ------------------------------
def process_message_logic(message_id, client_name, conn, cur):

    cur.execute(
        "SELECT content FROM raw_messages WHERE id = %s;",
        (message_id,)
    )
    row = cur.fetchone()

    if not row:
        return {"error": "Message not found"}

    message_text = row[0]

    prompt = f"""
    Extract action items from this Slack message.

    Return STRICT JSON only:
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

    If no action items exist:
    {{
        "action_items": []
    }}

    Slack message:
    {message_text}
    """

    response = model.generate_content(prompt)
    ai_output = response.text.strip()

    # Clean markdown fences
    if ai_output.startswith("```"):
        ai_output = ai_output.split("```")[1]
        ai_output = ai_output.replace("json", "").strip()

    try:
        parsed = json.loads(ai_output)
    except Exception:
        return {"error": "Invalid JSON from Gemini"}

    action_items = parsed.get("action_items") or []
    if not isinstance(action_items, list):
        action_items = []

    for item in action_items:

        raw_due = item.get("due_date")
        parsed_due = None

        if raw_due:
            try:
                parsed_due = parser.parse(raw_due, fuzzy=True).date()
            except Exception:
                parsed_due = None

        cur.execute(
            """
            INSERT INTO action_items 
            (client, description, owner, due_date, priority, source_message_id)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                client_name,
                item.get("description"),
                item.get("owner"),
                parsed_due,
                item.get("priority"),
                message_id
            )
        )

    cur.execute(
        "UPDATE raw_messages SET processed = true WHERE id = %s;",
        (message_id,)
    )

    return {
        "status": "processed",
        "action_items_created": len(action_items)
    }


# ------------------------------
# Slack Webhook
# ------------------------------
@app.post("/slack/events")
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

            # 1️⃣ Insert raw message (idempotent)
            cur.execute(
                """
                INSERT INTO raw_messages (source, external_id, content, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING
                RETURNING id;
                """,
                (
                    "slack",
                    event.get("event_ts"),
                    event.get("text"),
                    json.dumps(payload),
                )
            )

            row = cur.fetchone()

            if not row:
                conn.commit()
                return {"status": "duplicate_ignored"}

            new_id = row[0]

            # 2️⃣ Fetch client using channel id
            cur.execute(
                """
                SELECT client_name
                FROM client_channels
                WHERE platform = 'slack'
                AND external_id = %s;
                """,
                (event.get("channel"),)
            )

            client_row = cur.fetchone()
            client_name = client_row[0] if client_row else None

            # 3️⃣ Process with deterministic client
            result = process_message_logic(new_id, client_name, conn, cur)

            conn.commit()

        except Exception as e:
            print("Slack processing error:", e)

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return {"status": "ok"}

# ------------------------------
# Manual Processing Endpoint
# ------------------------------
@app.post("/process-message/{message_id}")
def process_message_endpoint(message_id: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # fetch client from raw message metadata
        cur.execute(
            """
            SELECT metadata
            FROM raw_messages
            WHERE id = %s;
            """,
            (message_id,)
        )
        row = cur.fetchone()

        client_name = None

        if row:
            metadata = row[0]
            channel_id = metadata.get("event", {}).get("channel")

            if channel_id:
                cur.execute(
                    """
                    SELECT client_name
                    FROM client_channels
                    WHERE platform = 'slack'
                    AND external_id = %s;
                    """,
                    (channel_id,)
                )
                client_row = cur.fetchone()
                client_name = client_row[0] if client_row else None

        result = process_message_logic(message_id, client_name, conn, cur)

        conn.commit()
        return result

    finally:
        cur.close()
        conn.close()

# ------------------------------
# Gemini Test Endpoint
# ------------------------------
@app.get("/test-gemini")
def test_gemini():
    try:
        models = [m.name for m in genai.list_models()]
        return {
            "status": "Gemini connection successful",
            "available_models": models
        }
    except Exception as e:
        return {"error": str(e)}