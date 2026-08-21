"""
firebase_config.py
-------------------
Optional Firestore integration.

Firestore inga rendu velaikku use pandrom:
1. recipes collection -> chatbot-oda "knowledge" (Gemini-ku theriyatha
   unga own recipes/notes vachikkalam)
2. chat_history collection -> ovvoru session-oda messages store pannum

Idhu venaam nu iruntha, .env file la USE_FIRESTORE=false nu vachikonga.
App Firestore illama normal ah run aagum (Gemini mattum use pannum).
"""

import os
import json

USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true"

db = None

if USE_FIRESTORE:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = os.getenv("FIREBASE_CRED_PATH", "firebase-credentials.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()


def get_recipe_context(user_message: str, limit: int = 3) -> str:
    """
    recipes collection la irundhu, user kettadhukku relevant ah irukura
    documents-a eduthu, oru text block ah return pannum. Idha Gemini-ku
    'context' ah anுப்பலாம் (simple keyword match - production la vector
    search / embeddings use pannalaam).
    """
    if not USE_FIRESTORE or db is None:
        return ""

    try:
        docs = db.collection("recipes").stream()
        matches = []
        message_lower = user_message.lower()

        for doc in docs:
            data = doc.to_dict()
            title = data.get("title", "")
            content = data.get("content", "")
            if title.lower() in message_lower or any(
                word in message_lower for word in title.lower().split()
            ):
                matches.append(f"Recipe: {title}\n{content}")
            if len(matches) >= limit:
                break

        return "\n\n".join(matches)
    except Exception as e:
        print(f"[Firestore] recipe fetch error: {e}")
        return ""


def save_chat_message(session_id: str, role: str, message: str):
    """chat_history collection la ovvoru message-um save pannum."""
    if not USE_FIRESTORE or db is None:
        return

    try:
        db.collection("chat_history").add(
            {
                "session_id": session_id,
                "role": role,
                "message": message,
            }
        )
    except Exception as e:
        print(f"[Firestore] save error: {e}")


def seed_sample_recipes():
    """
    Optional: run once to add sample recipes to Firestore, so you can
    test the knowledge-base feature. Call this manually if needed.
    """
    if not USE_FIRESTORE or db is None:
        print("Firestore off. .env la USE_FIRESTORE=true pannunga first.")
        return

    sample = [
        {
            "title": "Tomato Rice",
            "content": "Ingredients: rice, tomato, onion, chilli powder, "
            "mustard seeds, curry leaves. Steps: onion-a saute pannunga, "
            "tomato serunga, spices podunga, cooked rice-oda kalakkunga.",
        },
        {
            "title": "Curd Rice",
            "content": "Ingredients: cooked rice, curd, milk, mustard "
            "seeds, curry leaves, ginger. Steps: rice-a mash pannunga, "
            "curd + milk serthu kalakkunga, tempering podunga.",
        },
    ]
    for item in sample:
        db.collection("recipes").add(item)
    print("Sample recipes added to Firestore.")