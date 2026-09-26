const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const typingIndicator = document.getElementById("typing-indicator");

// Custom Dropdown Elements
const customDropdown = document.getElementById("custom-dropdown");
const dropdownTrigger = document.getElementById("dropdown-trigger");
const dropdownMenu = document.getElementById("dropdown-menu");
const selectedProgrammeText = document.getElementById("selected-programme-text");
const programmeSelect = document.getElementById("programme-select");

const SESSION_KEY = "campus-desk-session-id";

// Initialize Session ID
function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

// Custom Dropdown Interactive Logic
dropdownTrigger.addEventListener("click", (e) => {
  e.stopPropagation();
  const isActive = customDropdown.classList.contains("active");
  customDropdown.classList.toggle("active", !isActive);
  dropdownTrigger.setAttribute("aria-expanded", !isActive);
});

// Select Option from Custom Dropdown
document.querySelectorAll(".dropdown-option").forEach((option) => {
  option.addEventListener("click", () => {
    const val = option.getAttribute("data-value");
    const title = option.querySelector(".option-title").textContent;

    // Update Hidden Select
    programmeSelect.value = val;

    // Update UI Text
    selectedProgrammeText.textContent = title;

    // Active state toggling
    document.querySelectorAll(".dropdown-option").forEach((opt) => opt.classList.remove("selected"));
    option.classList.add("selected");

    // Close Dropdown
    customDropdown.classList.remove("active");
    dropdownTrigger.setAttribute("aria-expanded", "false");
  });
});

// Close Dropdown when clicking outside
document.addEventListener("click", () => {
  if (customDropdown.classList.contains("active")) {
    customDropdown.classList.remove("active");
    dropdownTrigger.setAttribute("aria-expanded", "false");
  }
});

// Quick Fill Function for Desktop Side Hints
function quickFill(text) {
  chatInput.value = text;
  chatInput.focus();
}

function createBotAvatarSVG() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM4 11a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-6z"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/></svg>`;
}

function createUserAvatarSVG() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
}

function addMessage(text, role) {
  const wrapper = document.createElement("div");
  wrapper.className = `msg msg--${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg__avatar";
  avatar.innerHTML = role === "user" ? createUserAvatarSVG() : createBotAvatarSVG();

  const content = document.createElement("div");
  content.className = "msg__content";

  const author = document.createElement("div");
  author.className = "msg__author";
  author.textContent = role === "user" ? "You" : role === "error" ? "System Alert" : "Campus AI Assistant";

  const card = document.createElement("div");
  card.className = "msg__card";
  card.textContent = text;

  content.appendChild(author);
  content.appendChild(card);

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);

  chatLog.appendChild(wrapper);
  
  // Smooth scroll
  chatLog.scrollTo({
    top: chatLog.scrollHeight,
    behavior: 'smooth'
  });
}

function setBusy(isBusy) {
  chatInput.disabled = isBusy;
  sendBtn.disabled = isBusy;
  typingIndicator.hidden = !isBusy;
  if (isBusy) {
    chatLog.scrollTo({
      top: chatLog.scrollHeight,
      behavior: 'smooth'
    });
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
