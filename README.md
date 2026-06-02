# KnowBase - Enterprise Knowledge Assistant

A powerful **RAG-based internal knowledge base** that allows employees to chat with company documents (PDFs) using hybrid search and Groq LLM.

![KnowBase Interface](screenshot.png)

---

## ✨ Features

- **PDF Upload & Processing** with automatic chunking
- **Hybrid Search** (Vector + BM25)
- **AI Chat** powered by Groq (Llama-3.3-70B) with source citations
- **JWT Authentication** with role-based access
- **Uploaded Documents Management** (View + Delete)
- **Multiple Chat History**
- **Smart Query Suggestions**
- **Analytics Dashboard**

---

## 📸 Screenshot

![KnowBase UI](screenshot.png)

_Clean, modern dark-themed interface with sidebar navigation, document management, and interactive chat._

---

## 🛠 Tech Stack

- **Backend**: FastAPI, ChromaDB, Rank-BM25, Groq
- **Frontend**: HTML + Tailwind CSS + Vanilla JS
- **Embeddings**: `all-MiniLM-L6-v2`

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd Enterprise-Knowledge_Assistant
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Add Groq API Key
Create .env in root:
envGROQ_API_KEY=your_groq_api_key_here
3. Run

Backend: cd src && python main.py
Frontend: Open frontend/index.html with Live Server


🔑 Default Login

hr@company.com / hr123
finance@company.com / finance123
admin@company.com / admin123


📁 Project Structure
text├── src/                  # FastAPI backend
├── frontend/             # HTML + JS UI
├── uploaded_docs/        # Uploaded PDFs
├── chroma_db/            # Vector database
├── screenshot.png        # Project screenshot
└── README.md
```
