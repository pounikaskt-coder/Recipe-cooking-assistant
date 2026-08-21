// script.js
// Frontend logic: sends user message to Flask backend (/api/chat)
// and displays the reply. Simple session_id so backend can keep
// per-user conversation history.

const API_URL = "http://127.0.0.1:5000/api/chat";

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

// session_id-a browser-oda localStorage la vachikonga, so idhu page
// reload aana kooda same conversation continue aagum.
let sessionId = localStorage.getItem("rasoi_session_id");
if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem("rasoi_session_id", sessionId);
}

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `msg ${sender}`;
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return msg;
}

async function sendMessage(message) {
  addMessage(message, "user");
  chatInput.value = "";
  sendBtn.disabled = true;

  const thinkingMsg = addMessage("thinking…", "bot thinking");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!res.ok) throw new Error("Server error");

    const data = await res.json();
    thinkingMsg.remove();
    addMessage(data.reply, "bot");
  } catch (err) {
    thinkingMsg.remove();
    addMessage(
      "Oops, couldn't reach the kitchen 🍳 — check that the backend " +
        "server is running (python app.py) and try again.",
      "bot"
    );
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  sendMessage(text);
});