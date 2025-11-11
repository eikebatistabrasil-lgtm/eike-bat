const messagesDiv = document.getElementById('messages');
const form = document.getElementById('chatForm');
const usernameInput = document.getElementById('username');
const messageInput = document.getElementById('message');

let messages = JSON.parse(localStorage.getItem('chatMessages') || '[]');

function renderMessages() {
  messagesDiv.innerHTML = '';
  messages.forEach(msg => {
    const div = document.createElement('div');
    div.className = 'message';
    div.innerHTML = `<strong>${msg.username}:</strong> ${msg.text}`;
    messagesDiv.appendChild(div);
  });
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

form.addEventListener('submit', e => {
  e.preventDefault();
  const username = usernameInput.value.trim() || "Anônimo";
  const text = messageInput.value.trim();
  if (!text) return;

  const newMsg = { username, text, time: Date.now() };
  messages.push(newMsg);
  localStorage.setItem('chatMessages', JSON.stringify(messages));
  messageInput.value = '';
  renderMessages();
});

renderMessages();
