# AI Document Intelligence Assistant

A production-grade, multi-tenant **Retrieval-Augmented Generation (RAG)** platform built with **FastAPI**, **PostgreSQL with `pgvector`**, **Google Gemini**, and **Next.js (React)**.

The system allows users to upload unstructured documents (PDFs, text files), automatically parses and chunks them into semantic embeddings, and enables conversational question-answering strictly grounded in document context with verifiable source citations.

---

## 🌐 Live Production Deployment

The application is deployed live in production:

| Component | Provider | Live URL | Status |
| :--- | :--- | :--- | :---: |
| **Frontend Web App** | GitHub Pages | **[https://lidu12.github.io/ai-document-intelligence-assistant/](https://lidu12.github.io/ai-document-intelligence-assistant/)** | 🟢 Live |
| **Backend API** | Render Cloud | **[https://ai-document-intelligence-assistant-1.onrender.com](https://ai-document-intelligence-assistant-1.onrender.com)** | 🟢 Live |
| **Interactive API Docs** | Swagger / OpenAPI | **[https://ai-document-intelligence-assistant-1.onrender.com/docs](https://ai-document-intelligence-assistant-1.onrender.com/docs)** | 🟢 Live |
| **API Health Check** | Render Cloud | **[https://ai-document-intelligence-assistant-1.onrender.com/health](https://ai-document-intelligence-assistant-1.onrender.com/health)** | 🟢 Healthy |

---

## ✨ Features & Architecture

- **Strict Multi-Tenant Isolation**: Vector search and metadata queries are strictly filtered by authenticated `user_id`.
- **PostgreSQL + `pgvector`**: Embeddings and relational metadata live in the same ACID-compliant database.
- **Automated Ingestion Pipeline**: In-memory PDF/TXT extraction with recursive character chunking and sliding-window overlap.
- **Grounded Answers & Citations**: LLM responses reference exact source chunks with document titles, page numbers, and excerpts.
- **Automated CI/CD**: Fully automated deployment workflow via GitHub Actions.
- **Conflict-Free Port Configuration**: Database is mapped to host port **`5433`** by default to prevent conflicts with other local PostgreSQL instances.

```text
┌─────────────────────────────────┐
│     Next.js / React Web UI      │  (Port 3000)
└────────────────┬────────────────┘
                 │ HTTP / REST
                 ▼
┌─────────────────────────────────┐
│      FastAPI Backend Engine     │  (Port 8000)
│  • JWT Auth   • Ingestion   • RAG│
└────────┬───────────────┬────────┘
         │               │
         ▼               ▼
┌──────────────────┐  ┌───────────────────────────────────┐
│ Google Gemini    │  │ PostgreSQL 16 + pgvector          │
│ • Embeddings     │  │ • Relational metadata             │
│ • Generation     │  │ • 768d Vector similarity search   │
└──────────────────┘  └───────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0 (Asyncpg) |
| **Vector DB** | PostgreSQL 16 + `pgvector` |
| **AI / Embeddings** | Google Gemini API (`text-embedding-004`, `gemini-1.5-flash` / `gemini-2.0-flash`) |
| **Document Parsing**| `pypdf` |
| **Frontend UI** | Next.js 14, React 18, TypeScript, Lucide Icons |
| **Authentication** | JWT (PyJWT), salted Bcrypt password hashing |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Quick Setup Guide

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or local Python 3.11+ and Node.js 18+)
- [Google Gemini API Key](https://aistudio.google.com/)

---

### 2. Configure Environment Variables
Create your backend `.env` file from the template:

```powershell
Copy-Item backend/.env.example backend/.env
```

Open `backend/.env` and add your Gemini API key:
```ini
GEMINI_API_KEY="your-gemini-api-key-here"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/doc_intelligence"
SECRET_KEY="your-secure-jwt-secret-key"
```

---

### 3. Choose How to Run

#### Option A: Docker Compose (All-in-One)
Build and start the database, backend, and frontend simultaneously:

```powershell
docker compose up --build
```

#### Option B: Manual Local Setup (Step-by-Step)

**Step 1: Start PostgreSQL with `pgvector` (Docker)**
```powershell
docker run -d --name doc_intelligence_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=doc_intelligence -p 5433:5432 pgvector/pgvector:pg16
```

**Step 2: Start Backend (FastAPI)**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Step 3: Start Frontend (Next.js)**
In a new terminal:
```powershell
cd frontend
npm run dev
```

---

## 🌐 Application Endpoints Reference

### Production (Cloud)
| Service | URL | Notes |
| :--- | :--- | :--- |
| **Frontend Web App** | [https://lidu12.github.io/ai-document-intelligence-assistant/](https://lidu12.github.io/ai-document-intelligence-assistant/) | Hosted on GitHub Pages |
| **Interactive API Docs** | [https://ai-document-intelligence-assistant-1.onrender.com/docs](https://ai-document-intelligence-assistant-1.onrender.com/docs) | Swagger UI on Render |
| **Alternative API Docs** | [https://ai-document-intelligence-assistant-1.onrender.com/redoc](https://ai-document-intelligence-assistant-1.onrender.com/redoc) | ReDoc API documentation |
| **Health Check** | [https://ai-document-intelligence-assistant-1.onrender.com/health](https://ai-document-intelligence-assistant-1.onrender.com/health) | Live DB & vector health status |

### Local Development
| Service | URL | Notes |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Next.js development server |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Local Swagger UI |
| **Alternative API Docs** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Local ReDoc |
| **Health Check** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Local health status |

---

## 🧪 Running Tests

To run the backend test suite:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
