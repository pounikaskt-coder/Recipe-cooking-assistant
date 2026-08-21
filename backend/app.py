"""
app.py
------
Recipe / Cooking Assistant Chatbot - Backend (Flask + Gemini + Firestore)

Run pandra maadhiri:
    python app.py

Idhu http://127.0.0.1:5000 la run aagum.t8.6
Frontend (frontend/index.html) idhoda /api/chat endpoint-a REST API
mூலமாக call pannum.
"""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

import firebase_config

# ---------- Setup ----------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY illa! backend/.env file create pannunga "
        "(.env.example-a copy pannunga) and unga API key podunga."
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.6-flash")

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# System prompt: chatbot-a recipe/cooking topic mattum pesa restrict pannuthu
SYSTEM_PROMPT = """You are "NextGen-C Cooking Assistant", a friendly AI
chatbot whose ONLY purpose is to help users with cooking and recipes.

Rules:
- Only answer questions about recipes, ingredients, cooking steps,
  substitutions, cooking times, nutrition of dishes, and kitchen tips.
- If the user asks something unrelated to food/cooking, politely say
  you can only help with recipes and cooking, and steer them back.
- Give clear, step-by-step recipe instructions with ingredients list
  and steps when a recipe is asked.
- Keep answers friendly and easy to follow, like a helpful home cook.
"""

# In-memory chat history per session (simple demo storage; Firestore
# handles persistent storage if USE_FIRESTORE=true)
chat_sessions = {}


def get_chat(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = model.start_chat(
            history=[
                {"role": "user", "parts": [SYSTEM_PROMPT]},
                {
                    "role": "model",
                    "parts": [
                        "Understood! I'm ready to help with recipes and "
                        "cooking questions only."
                    ],
                },
            ]
        )
    return chat_sessions[session_id]


# ---------- Routes ----------

@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not user_message:
        return jsonify({"error": "message empty"}), 400

    # Optional: pull relevant recipe knowledge from Firestore
    recipe_context = firebase_config.get_recipe_context(user_message)

    prompt = user_message
    if recipe_context:
        prompt = (
            f"Here is some extra reference from our recipe database:\n"
            f"{recipe_context}\n\nUser question: {user_message}"
        )

    try:
        convo = get_chat(session_id)
        response = convo.send_message(prompt)
        reply_text = response.text
    except Exception as e:
        print(f"[Gemini] error: {e}")
        return jsonify({"error": "AI service failed, try again."}), 500

    # Optional: save to Firestore
    firebase_config.save_chat_message(session_id, "user", user_message)
    firebase_config.save_chat_message(session_id, "assistant", reply_text)

    return jsonify({"reply": reply_text, "session_id": session_id})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)