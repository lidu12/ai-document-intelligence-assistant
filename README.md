# AI Document Intelligence Assistant (Production-Grade RAG System)

A multi-tenant, enterprise-ready Document Intelligence platform built with **FastAPI**, **PostgreSQL with `pgvector`**, **Google Gemini**, and **Next.js/React**.

This application allows users to upload unstructured documents (PDFs, text files), process them into structured semantic chunks, generate vector embeddings, and interact with them using a grounded **Retrieval-Augmented Generation (RAG)** pipeline that provides verifiable citations and eliminates hallucinations.

---

## 🌟 Key Highlights & Engineering Features

- **Strict Multi-Tenant Isolation**: Vector similarity queries are filtered at the database level using `user_id`. Users can never access or retrieve another user's document vectors.
- **pgvector Vector Database**: Embeddings and relational metadata live in the same PostgreSQL instance, guaranteeing ACID transactions and preventing dual-write synchronization issues.
- **Custom Ingestion Pipeline**: In-memory streaming PDF and TXT parsers paired with recursive character-level chunking with configurable overlap to preserve semantic context.
- **Grounded RAG with Citations**: Responses are strictly anchored in retrieved chunks. The model outputs source attribution tags (Document Name, Page Number, Chunk Excerpt).
- **Anti-Hallucination Guardrails**: Distance threshold filtering rejects irrelevant context. If the answer does not exist in the uploaded documents, the system explicitly reports insufficient information.
- **Production Architecture**: Asynchronous FastAPI endpoints, Pydantic v2 data validation, SQLAlchemy 2.0 async ORM, JWT authentication with bcrypt password hashing, and Docker Compose containerization.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                            │
│                  Modern Responsive Web UI (React / Next.js)             │
│          • Authentication  • Document Manager  • Citation Inspector     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / REST / JSON
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               API LAYER                                 │
│                     FastAPI Application Gateway                         │
│   • CORS & Security Headers   • Request Validation (Pydantic v2)        │
│   • Global Error Handling     • Dependency Injection                    │
└───────┬────────────────────────────┬────────────────────────────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌──────────────────┐       ┌──────────────────┐       ┌───────────────────┐
│   AUTH SERVICE   │       │ DOCUMENT SERVICE │       │    RAG SERVICE    │
│ • Password Hash  │       │ • File Parsing   │       │ • Query Embedding │
│ • JWT Generation │       │ • Text Cleaning  │       │ • Vector Search   │
│ • User Context   │       │ • Chunk Splitting│       │ • Context Builder │
└────────┬─────────┘       └─────────┬────────┘       │ • Gemini LLM Call │
         │                           │                └─────────┬─────────┘
         │                           │                          │
         │                           ▼                          │
         │                 ┌──────────────────┐                 │
         │                 │EMBEDDING SERVICE │                 │
         │                 │• Gemini Vector API│                │
         │                 └─────────┬────────┘                 │
         │                           │                          │
         ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE LAYER                             │
│                    PostgreSQL 16 + pgvector Extension                    │
│   • users              • documents            • document_chunks (vector)│
│   • conversations      • messages                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11+) | Asynchronous, high-throughput REST API with automatic OpenAPI documentation. |
| **Data Validation** | Pydantic v2 | High-performance request parsing, validation, and schema definitions. |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` | Relational data persistence and high-dimensional vector similarity search. |
| **Database ORM** | SQLAlchemy 2.0 (Async) | Type-safe asynchronous database queries using `asyncpg`. |
| **Authentication** | PyJWT & Passlib (Bcrypt) | Stateless JWT tokens and salted password hashing. |
| **Embedding Model** | Google Gemini `text-embedding-004` | 768-dimensional semantic text embeddings. |
| **Generative LLM** | Google Gemini `gemini-1.5-flash` / `gemini-2.0-flash` | Low-latency, cost-effective reasoning with strict prompt adherence. |
| **Document Parsing** | `pypdf` | Fast, pure-Python PDF page extraction without heavy native C dependencies. |
| **Frontend** | React / Next.js | Modern, responsive web interface for document management and citation chat. |
| **Containerization** | Docker & Docker Compose | Multi-container orchestration for backend, database, and frontend. |

---

## 🔄 How the Pipelines Work

### 1. Document Ingestion Pipeline
1. **Upload**: The user uploads a file (`.pdf` or `.txt`) via `POST /api/v1/documents/upload`.
2. **Validation**: The system validates file format, MIME type, and size limits (max 10MB).
3. **Extraction**: Raw text is parsed page by page and cleaned of control characters.
4. **Chunking**: Text is split into sliding-window chunks (e.g., 500 tokens with 50-token overlap) to preserve semantic continuity across boundaries.
5. **Embedding**: Chunks are batched and sent to Google Gemini `text-embedding-004` to generate 768-dimensional vectors.
6. **Storage**: Document metadata and vector chunks are saved in PostgreSQL in a single atomic transaction.

### 2. Retrieval-Augmented Generation (RAG) Pipeline
1. **Query**: The user submits a question via `POST /api/v1/chat`.
2. **Embedding**: The question is converted into a 768-dimensional query vector.
3. **Scoped Vector Search**: pgvector executes a cosine distance search (`<=>`) on `document_chunks`, filtered strictly by `documents.user_id = current_user.id`.
4. **Context Construction**: Top-$K$ relevant chunks exceeding the similarity threshold are assembled into an augmented prompt with unique source IDs (`[Source 1]`, `[Source 2]`).
5. **LLM Generation**: Google Gemini generates an answer grounded solely in the retrieved context, citing specific sources.
6. **Response**: The API returns the answer along with structured citation metadata (document title, page number, chunk excerpt).

---

## 📂 Project Structure

```text
ai-document-intelligence-assistant/
├── README.md                           # Master project documentation
├── .gitignore                          # Git ignore rules
├── docker-compose.yml                  # Docker Compose orchestration
│
├── backend/
│   ├── Dockerfile                      # Backend container definition
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment variables template
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                     # FastAPI entry point & lifespan
│       │
│       ├── core/                       # Core system configurations
│       │   ├── __init__.py
│       │   ├── config.py               # Pydantic Settings management
│       │   ├── database.py             # Async database session & engine
│       │   ├── security.py             # Password hashing & JWT logic
│       │   └── exceptions.py           # Global exception definitions
│       │
│       ├── models/                     # SQLAlchemy ORM database models
│       │   ├── __init__.py
│       │   ├── base.py                 # Base declarative model & mixins
│       │   ├── user.py                 # User table model
│       │   ├── document.py             # Document & DocumentChunk (pgvector)
│       │   └── chat.py                 # Conversation & Message tables
│       │
│       ├── schemas/                    # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── auth.py                 # Auth request/response schemas
│       │   ├── document.py             # Document & chunk schemas
│       │   └── chat.py                 # Query, response, & citation schemas
│       │
│       ├── services/                   # Business logic layer
│       │   ├── __init__.py
│       │   ├── auth_service.py         # Authentication & registration logic
│       │   ├── document_parser.py      # PDF and TXT text extraction
│       │   ├── chunking_service.py     # Recursive sliding-window chunking
│       │   ├── embedding_service.py    # Gemini vector embeddings client
│       │   ├── vector_service.py       # pgvector similarity queries
│       │   ├── document_service.py     # Ingestion orchestration
│       │   ├── ai_service.py           # Gemini LLM generation client
│       │   └── rag_service.py          # Grounded RAG orchestrator
│       │
│       └── api/                        # HTTP endpoints & dependencies
│           ├── __init__.py
│           ├── deps.py                 # Dependency injection (Auth, DB)
│           ├── router.py               # Combined API router
│           └── routes/
│               ├── __init__.py
│               ├── auth.py             # /api/v1/auth endpoints
│               ├── documents.py        # /api/v1/documents endpoints
│               └── chat.py             # /api/v1/chat endpoints
│
├── frontend/                           # React / Next.js web application
│
└── tests/                              # Automated test suite
    ├── conftest.py                     # Pytest fixtures & test DB setup
    ├── test_auth.py                    # Authentication tests
    ├── test_documents.py               # Parsing & chunking tests
    └── test_rag.py                     # Vector search & RAG pipeline tests
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- **Python**: 3.11 or higher
- **PostgreSQL**: 16 with `pgvector` extension installed (or run via Docker)
- **Node.js**: 18+ (for frontend)
- **Google Gemini API Key**: [Get a Gemini API key from Google AI Studio](https://aistudio.google.com/)

### 2. Environment Configuration
Copy the template file and fill in your secrets:
```bash
cp backend/.env.example backend/.env
```

Key environment variables:
```ini
PROJECT_NAME="AI Document Intelligence Assistant"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/doc_intelligence"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Running with Docker Compose (Recommended)
```bash
docker compose up --build
```
- **Backend API Docs**: `http://localhost:8000/docs`
- **Frontend Web UI**: `http://localhost:3000`

---

## 🔒 Security & Privacy Practices

1. **Zero Multi-Tenant Data Leakage**: Vector search queries join `documents` and explicitly match `user_id`. Chunks belonging to other users are excluded at query execution time.
2. **No Hard-Coded Secrets**: All credentials (API keys, database URLs, JWT secrets) are loaded strictly via environment variables validated by Pydantic.
3. **Cryptographic Password Protection**: User passwords are saved using industry-standard salted `bcrypt` hashes.
4. **Input Sanitization**: File uploads are strictly validated against maximum byte sizes and accepted MIME types.

---

## 📄 License
This project is licensed under the MIT License.
