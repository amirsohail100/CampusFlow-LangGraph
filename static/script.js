const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const typingIndicator = document.getElementById("typing-indicator");
const programmeSelect = document.getElementById("programme-select");

const SESSION_KEY = "campus-desk-session-id";

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function addMessage(text, role) {
  const wrapper = document.createElement("div");
  wrapper.className = `msg msg--${role}`;

  const card = document.createElement("div");
  card.className = "msg__card";
  card.textContent = text;

  wrapper.appendChild(card);
  chatLog.appendChild(wrapper);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setBusy(isBusy) {
  chatInput.disabled = isBusy;
  sendBtn.disabled = isBusy;
  typingIndicator.hidden = !isBusy;
  if (isBusy) {
    chatLog.scrollTop = chatLog.scrollHeight;
  }
}

async function sendMessage(message) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: getSessionId(),
      programme: programmeSelect.value,
      message,
    }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "The assistant could not be reached.");
  }

  return response.json();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  chatInput.value = "";
  setBusy(true);

  try {
    const data = await sendMessage(message);
    addMessage(data.reply, "bot");
  } catch (err) {
    addMessage(err.message || "Something went wrong. Please try again.", "error");
  } finally {
    setBusy(false);
    chatInput.focus();
  }
});

window.addEventListener("DOMContentLoaded", () => {
  chatInput.focus();
});
