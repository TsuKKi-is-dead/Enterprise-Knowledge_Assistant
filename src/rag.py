import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from rank_bm25 import BM25Okapi
import numpy as np
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="../chroma_db")
collection = chroma_client.get_or_create_collection("company_docs")

documents = []
metadata = []

def process_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def add_document(text: str, filename: str):
    global documents, metadata
    if not text.strip():
        print(f"⚠️ No text extracted from {filename}")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_text(text)
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        embedding = embedding_model.encode(chunk).tolist()
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"filename": filename, "chunk_id": i}],
            ids=[f"{filename}_{i}"]
        )
        documents.append(chunk)
        metadata.append({"filename": filename})
    
    print(f"✅ Added {len(chunks)} chunks from {filename} | Total documents: {len(documents)}")

def hybrid_search(query: str, top_k: int = 6):
    global documents
    
    if len(documents) == 0:
        return []

    # Vector Search
    query_emb = embedding_model.encode(query).tolist()
    vector_results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["metadatas", "documents"]
    )

    results = []
    seen = set()

    # Add vector results first
    if vector_results.get('documents'):
        for doc, meta in zip(vector_results['documents'][0], vector_results['metadatas'][0]):
            if doc not in seen:
                results.append({"text": doc, "metadata": meta})
                seen.add(doc)

    return results[:top_k]

def generate_answer(query: str, context: list):
    if not context:
        return "Please upload some PDF documents first so I can help you with company knowledge."
    
    context_str = "\n\n".join([
        f"Source: {c['metadata'].get('filename', 'Document')}\nContent: {c['text']}" 
        for c in context
    ])
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful enterprise knowledge assistant. Answer based only on the provided context."},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
        ],
        temperature=0.1,
        max_tokens=1024
    )
    return response.choices[0].message.content