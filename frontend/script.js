let token = null;
let currentUser = null;
let currentChatId = null;
let chats = {}; // { chatId: { title, messages } }

console.log("✅ Script v4.0 with Documents + History + Suggestions");

// ====================== LOGIN ======================
async function login() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    if (!email || !password) return alert("Enter email and password");

    try {
        const res = await fetch('http://localhost:8000/login', {
            method: 'POST',
            body: new URLSearchParams({email, password})
        });
        const data = await res.json();
        if (data.access_token) {
            token = data.access_token;
            currentUser = { email, role: data.role };
            document.getElementById('login-modal').classList.add('hidden');
            document.getElementById('user-info').innerHTML = `👤 ${email} (${data.role})`;
            loadUploadedDocuments();
            newChat(); // Start fresh
        } else alert("Invalid credentials");
    } catch (e) {
        alert("Backend not reachable");
    }
}

function logout() {
    token = null;
    currentUser = null;
    document.getElementById('login-modal').classList.remove('hidden');
}

// ====================== UPLOAD ======================
function triggerFileUpload() {
    if (!token) return alert("Please login first!");
    document.getElementById('file-upload').click();
}

async function uploadFile(event) {
    const file = event.target.files[0];
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        alert("Please select a valid PDF");
        event.target.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (res.ok) {
            alert(`✅ Successfully uploaded: ${file.name}`);
            event.target.value = '';
            loadUploadedDocuments();
        } else if (res.status === 401) {
            logout();
        } else {
            alert("Upload failed");
        }
    } catch (err) {
        console.error(err);
        alert("Upload error");
    }
}

// ====================== DOCUMENTS ======================
async function loadUploadedDocuments() {
    try {
        const res = await fetch('http://localhost:8000/documents', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const docs = await res.json();
        
        const container = document.getElementById('uploaded-docs');
        container.innerHTML = docs.map(doc => `
            <div class="flex items-center justify-between bg-gray-800 p-3 rounded-2xl text-sm group">
                <span class="truncate flex-1">${doc.filename}</span>
                <button onclick="deleteDocument('${doc.filename}')" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-500">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
        
        document.getElementById('doc-count').textContent = `${docs.length} docs`;
    } catch (e) {
        console.error(e);
    }
}

async function deleteDocument(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
        await fetch(`http://localhost:8000/documents/${filename}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        loadUploadedDocuments();
        alert("Document deleted");
    } catch (e) {
        alert("Delete failed");
    }
}

// ====================== CHAT HISTORY ======================
function saveCurrentChat() {
    if (!currentChatId || !chats[currentChatId]) return;
    // Save logic can be enhanced with backend later
}

function newChat() {
    saveCurrentChat();
    currentChatId = 'chat_' + Date.now();
    chats[currentChatId] = { title: "New Conversation", messages: [] };
    
    document.getElementById('chat-container').innerHTML = '';
    document.getElementById('chat-title').textContent = "New Conversation";
    document.getElementById('suggestions').classList.remove('hidden');
    loadChatHistory();
    showSuggestions();
}

function loadChatHistory() {
    const container = document.getElementById('chat-history');
    container.innerHTML = Object.values(chats).map(chat => `
        <div onclick="loadChat('${Object.keys(chats).find(k => chats[k] === chat)}')" 
             class="px-4 py-2 hover:bg-gray-800 rounded-2xl cursor-pointer text-sm truncate">
            ${chat.title}
        </div>
    `).join('');
}

function loadChat(chatId) {
    currentChatId = chatId;
    const chat = chats[chatId];
    document.getElementById('chat-container').innerHTML = chat.messages.map(m => `
        <div class="${m.sender === 'user' ? 'flex justify-end' : 'flex justify-start'} mb-4">
            <div class="${m.sender === 'user' ? 'bg-blue-600' : 'bg-gray-800'} max-w-[80%] rounded-3xl px-5 py-4">
                <p>${m.content}</p>
            </div>
        </div>
    `).join('');
    document.getElementById('chat-title').textContent = chat.title;
}

// ====================== SUGGESTIONS ======================
function showSuggestions() {
    const suggestions = [
        "What is the leave policy?",
        "Summarize the company handbook",
        "What are the benefits?",
        "Tell me about performance review process"
    ];
    
    const container = document.getElementById('suggestion-buttons');
    container.innerHTML = suggestions.map(q => `
        <button onclick="useSuggestion('${q}')" 
                class="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-2xl text-sm">
            ${q}
        </button>
    `).join('');
}

function useSuggestion(question) {
    document.getElementById('query-input').value = question;
    sendQuery();
}

// ====================== SEND QUERY ======================
async function sendQuery() {
    const input = document.getElementById('query-input');
    const question = input.value.trim();
    if (!question || !token || !currentChatId) return;

    const chat = chats[currentChatId];
    chat.messages.push({ sender: 'user', content: question });
    addMessage('user', question);
    input.value = '';

    try {
        const res = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        
        if (res.ok) {
            chat.messages.push({ sender: 'bot', content: data.answer });
            addMessage('bot', data.answer, data.sources || []);
        }
    } catch (e) {
        console.error(e);
        addMessage('bot', "Sorry, something went wrong.");
    }
}

function addMessage(sender, content, sources = []) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = sender === 'user' ? 'flex justify-end mb-4' : 'flex justify-start mb-4';
    
    let html = `<div class="${sender === 'user' ? 'bg-blue-600' : 'bg-gray-800'} max-w-[80%] rounded-3xl px-5 py-4"><p>${content}</p>`;
    if (sender === 'bot' && sources.length) {
        html += `<div class="mt-3 text-xs text-gray-400">Sources:</div>`;
        sources.forEach(s => html += `<div class="text-xs text-emerald-400">• ${s.filename || s}</div>`);
    }
    html += `</div>`;
    div.innerHTML = html;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ====================== ANALYTICS ======================
async function showAnalytics() {
    // ... (keep your existing analytics function)
    if (!token) return alert("Please login first!");
    try {
        const res = await fetch('http://localhost:8000/analytics', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        // render logic...
        document.getElementById('analytics-modal').classList.remove('hidden');
    } catch (e) {
        alert("Could not load analytics");
    }
}

function hideAnalytics() {
    document.getElementById('analytics-modal').classList.add('hidden');
}

// ====================== INIT ======================
window.onload = () => {
    document.getElementById('login-modal').classList.remove('hidden');
    const input = document.getElementById('query-input');
    if (input) {
        input.addEventListener('keypress', e => {
            if (e.key === 'Enter') sendQuery();
        });
    }
};