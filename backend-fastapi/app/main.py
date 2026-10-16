import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import analysis, chatbot, health


configured_cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if "*" in configured_cors_origins:
    raise ValueError("CORS_ORIGINS must list explicit origins; wildcard origins are not allowed.")

CORS_ORIGINS = configured_cors_origins or [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Models are lazy-loaded on first use. LegalBERT stays unloaded unless ENABLE_LEGALBERT=true.
    yield


app = FastAPI(title="ContractAI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(chatbot.router)
