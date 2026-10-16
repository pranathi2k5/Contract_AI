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
- 🤖 **Legal Chatbot** — Gemini API by default, grounded in the uploaded contract and retrieved legal sections; Ollama remains available for development

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile App | Flutter (Dart) |
| API Backend | Spring Boot 3.x (Java 17+) |
| AI/ML Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 |
| Vector Store | ChromaDB |
| NLP Models | LegalBERT, SBERT |
| RAG | ChromaDB + shared SBERT embeddings |
| Chatbot LLM | Gemini API (configurable); optional Ollama development provider |
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

## FastAPI LLM and India Code corpus

The chatbot uses the `gemini` provider by default. Configure `GEMINI_API_KEY` as a
server-side environment variable; do not put it in `app.js` or other browser files.
`GEMINI_MODEL` and `LLM_TIMEOUT_SECONDS` can be set to tune the model and request
timeout. To use a developer's local Ollama instance instead, set
`LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and `OLLAMA_MODEL`. Missing keys, timeouts,
and provider errors return HTTP 503 rather than a generated fallback.

The India Code corpus is built only from configured HTTPS sources on
`indiacode.nic.in`. Set `INDIA_CODE_SOURCES_JSON` to a JSON array of source records,
each containing `act_name` and the official document `url`; add `version` and
`effective_date` when verified in that source. Then, from `backend-fastapi`, run:

```bash
python -m app.services.rag_service --ingest
```

Ingestion is repeatable, stores sections with source/version metadata, and uses the
same `SBERT_MODEL` for both stored and query embeddings. ChromaDB's local persistent
directory is selected by `CHROMA_PERSIST_DIRECTORY`; on Render, attach a persistent
disk and point this setting at its mount path (for example `/var/data/chroma_db`),
then run the ingestion command from the Render shell after setting the sources.
If using the Docker Compose Chroma service, `CHROMA_HOST` and `CHROMA_PORT` select it;
the existing `chromadata` volume persists that collection. An empty or unavailable
corpus is reported as such; there is no bundled legal-mapping fallback.

Analysis returns the selected perspective score for compatibility and adds
`role_risk_scores` with independent Sender and Receiver scores and clause-level
contributions. Applicable-law records contain the retrieved statutory text and
official source citation. Similarity is informational and does not determine
applicability; all output is legal information, not legal advice.
