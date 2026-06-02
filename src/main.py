from fastapi import Form  
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from rag import add_document, hybrid_search, generate_answer, process_pdf
from models import Query
import shutil
import chromadb
from datetime import datetime

load_dotenv()

app = FastAPI(title="Enterprise Knowledge Assistant")

UPLOAD_DIR = "../uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

bearer = HTTPBearer()

# Simple in-memory users (No hashing issues)
users_db = {
    "admin@company.com": {"password": "admin123", "role": "admin"},
    "hr@company.com": {"password": "hr123", "role": "hr"},
    "finance@company.com": {"password": "finance123", "role": "finance"}
}

analytics = {"queries": [], "most_asked": {}}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"email": payload.get("sub"), "role": payload.get("role")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.post("/login")
async def login(
    email: str = Form(...), 
    password: str = Form(...)
):
    user = users_db.get(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": email, "role": user["role"]})
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "role": user["role"]
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, detail="Only PDF files allowed")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    text = process_pdf(file_path)
    add_document(text, file.filename)
    
    return {"message": f"Successfully uploaded {file.filename}"}

@app.get("/documents")
async def get_documents(user=Depends(get_current_user)):
    """Return list of uploaded documents"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            if filename.lower().endswith('.pdf'):
                files.append({
                    "filename": filename,
                    "uploaded_at": datetime.now().isoformat()
                })
        return files
    except:
        return []

@app.delete("/documents/{filename}")
async def delete_document(filename: str, user=Depends(get_current_user)):
    """Delete document from filesystem and ChromaDB"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from ChromaDB
    try:
        chroma_client = chromadb.PersistentClient(path="../chroma_db")
        collection = chroma_client.get_collection("company_docs")
        collection.delete(where={"filename": filename})
    except:
        pass
    
    return {"message": f"Deleted {filename}"}

@app.post("/ask")
async def ask_question(query: Query, user=Depends(get_current_user)):
    context = hybrid_search(query.question)
    answer = generate_answer(query.question, context)
    
    analytics["queries"].append(query.question)
    analytics["most_asked"][query.question] = analytics["most_asked"].get(query.question, 0) + 1
    
    return {
        "answer": answer,
        "sources": [c["metadata"] for c in context]
    }

@app.get("/analytics")
async def get_analytics(user=Depends(get_current_user)):
    sorted_faqs = sorted(analytics["most_asked"].items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "total_queries": len(analytics["queries"]),
        "most_asked": sorted_faqs,
        "recent_queries": analytics["queries"][-10:]
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)