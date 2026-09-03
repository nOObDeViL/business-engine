import os
import json
from datetime import datetime

STATE_FILE = "state.json"
DASHBOARD_FILE = "index.html"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"capital": 0.0, "revenue": 0.0, "businesses": [], "logs": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def log_action(state, msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {msg}"
    state["logs"].append(entry)
    state["logs"] = state["logs"][-25:]
    print(entry)

def get_builtin_product_spec():
    return {
        "slug": "comic-16x9-slicer",
        "name": "Webtoon & Manga 16:9 Panel Slicer",
        "tagline": "Slices vertical webtoons into 16:9 video recap assets directly in your browser.",
        "price_usd": 2.99
    }

def generate_spec_with_ai(api_key: str, state: dict) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    
    target_model = "gemini-3.6-flash"
    try:
        available = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])]
        for pref in ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
            matched = [m for m in available if pref in m]
            if matched:
                target_model = matched[0]
                break
    except Exception as e:
        log_action(state, f"Model auto-discovery: {e}")

    log_action(state, f"Requesting blueprint from {target_model}")
    prompt = """Generate an MVP spec for a 100% client-side web utility (HTML5/Canvas, zero compute costs) for creators.
Return ONLY valid JSON (no backticks, no markdown):
{"slug": "unique-url-slug", "name": "Tool Name", "tagline": "1-sentence benefit", "price_usd": 2.50}"""
    
    response = client.models.generate_content(
        model=target_model,
        contents=prompt
    )
    cleaned = response.text.strip().replace("```json", "").replace("
