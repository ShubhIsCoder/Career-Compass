const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const quickPrompts = document.getElementById("quick-prompts");

const history = [];

function addMessage(role, text, options = {}) {
  const div = document.createElement("div");
  div.className = `msg ${role}${options.typing ? " typing" : ""}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
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
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    typingBubble.remove();
    addMessage("bot", data.reply);
    history.push({ user: message, assistant: data.reply });
  } catch (error) {
    typingBubble.remove();
    const errorMessage = error instanceof Error ? error.message : "Unexpected error";
    addMessage("bot", `Error: ${errorMessage}`);
  }
});

addMessage(
  "bot",
  "Hey — I’m CareerCompass. Share your current background + your target role, and I’ll generate a practical action plan."
);
