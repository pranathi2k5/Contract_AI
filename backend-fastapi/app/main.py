from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import analysis, chatbot, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Models could be pre-loaded here
    yield
    # Cleanup here if needed

app = FastAPI(title="ContractAI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(chatbot.router)
