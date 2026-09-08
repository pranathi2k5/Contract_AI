# ContractAI 🔍⚖️

**AI-Powered Legal Contract Analysis & Decision Support System**

An intelligent system for uploading, analyzing, and understanding legal contracts using LegalBERT, SBERT, and RAG, with a Flutter mobile app, dual Spring Boot + FastAPI backend, and PostgreSQL database.

---

## Features

- 🔐 **JWT Authentication** — Secure email/password login and registration
- 👥 **Role Toggle** — Switch between Sender/Receiver per contract
- 📄 **Multi-format Upload** — PDF, DOCX, and Image (OCR via Tesseract)
- 📊 **Risk Dashboard** — Overall risk score gauge + category distribution charts
- ⚠️ **Risk Clause Analysis** — LegalBERT + SBERT powered risk scoring
- 🔍 **Missing Clause Detection** — SBERT cosine similarity against standard templates
- ⚖️ **Indian Law Mapping** — Clause-level mapping to applicable Indian Acts & Sections
- 📋 **PDF Report** — Downloadable comprehensive analysis report
- 🤖 **Legal Chatbot** — RAG-powered context-aware legal assistant (Ollama local model)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile App | Flutter (Dart) |
| API Backend | Spring Boot 3.x (Java 17+) |
| AI/ML Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 |
| Vector Store | ChromaDB |
| NLP Models | LegalBERT, SBERT |
| RAG | LangChain + ChromaDB |
| Chatbot LLM | Ollama (local) |
| OCR | Tesseract |
| Containerization | Docker Compose |

## Quick Start

```bash
# 1. Clone and navigate
cd ContractAI

# 2. Start infrastructure
docker-compose up -d postgres chromadb

# 3. Start Spring Boot backend
cd backend-springboot
mvn spring-boot:run

# 4. Start FastAPI backend
cd backend-fastapi
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. Start Flutter app
cd contract_ai_app
flutter pub get
flutter run
```

### Existing Database Migration

For an existing PostgreSQL volume, run the schema alignment once before starting Spring Boot:

```bash
psql "$DATABASE_URL" -f database/migrations/001_align_numeric_score_columns.sql
```

Fresh Docker PostgreSQL volumes apply this migration automatically after `database/init.sql`. Keep `spring.jpa.hibernate.ddl-auto=validate` enabled so deployment stops when the schema and entities diverge.

## Contract Types Supported

- Employment Agreements
- Non-Disclosure Agreements (NDA)
- Sales Agreements
- Service Agreements
- Rental/Lease Agreements

## Architecture

```
Flutter App → Spring Boot (Auth + CRUD) → FastAPI (AI/ML)
                    ↓                          ↓
               PostgreSQL                  ChromaDB
```
