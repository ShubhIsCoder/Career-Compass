const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const quickPrompts = document.getElementById("quick-prompts");

let sessionId = null;
let token = localStorage.getItem("cc_token");

function addMessage(role, text, options = {}) {
  const div = document.createElement("div");
  div.className = `msg ${role}${options.typing ? " typing" : ""}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

async function ensureAuth() {
  if (token) return;
  const email = prompt("Enter email for CareerCompass login/register:");
  const password = prompt("Enter password (min 8 chars):");
  if (!email || !password) {
    throw new Error("Authentication required");
  }

  const attempts = [
    { endpoint: "/api/auth/login", payload: { email, password } },
    { endpoint: "/api/auth/register", payload: { email, password, tier: "free" } },
  ];

  for (const attempt of attempts) {
    const response = await fetch(attempt.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(attempt.payload),
    });

    if (response.ok) {
      const data = await response.json();
      token = data.access_token;
      localStorage.setItem("cc_token", token);
      return;
    }
  }

  throw new Error("Unable to authenticate");
}

function setPrompt(text) {
  messageInput.value = text;
  messageInput.focus();
}

quickPrompts?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;
  const prompt = target.dataset.prompt;
  if (!prompt) return;
  setPrompt(prompt);
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  messageInput.value = "";

  const typingBubble = addMessage("bot", "Thinking…", { typing: true });

  try {
    await ensureAuth();

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    sessionId = data.session_id;
    typingBubble.remove();
    addMessage("bot", data.reply);
  } catch (error) {
    typingBubble.remove();
    const errorMessage = error instanceof Error ? error.message : "Unexpected error";
    addMessage("bot", `Error: ${errorMessage}`);
  }
});

addMessage(
  "bot",
  "Hey — I’m CareerCompass. I support persistent sessions, login, and tier-based usage. Share your background + target role."
);
