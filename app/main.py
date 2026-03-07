from fastapi import FastAPI
from app.ingestion.slack_handler import router as slack_router
from app.database import get_connection
import google.generativeai as genai


app = FastAPI()

app.include_router(slack_router)


@app.get("/")
def health():
    return {"status": "AI Ops Backend Running"}


@app.get("/test-db")
def test_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT NOW();")
    result = cur.fetchone()

    cur.close()
    conn.close()

    return {"database_time": result}


@app.get("/test-gemini")
def test_gemini():

    models = [m.name for m in genai.list_models()]

    return {
        "status": "Gemini connection successful",
        "available_models": models
    }