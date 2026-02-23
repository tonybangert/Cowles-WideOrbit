"""
Cowles Project — Broadcast Revenue Intelligence API
Agentic layer on top of WideOrbit WO Traffic data for revenue intelligence,
operational insights, and proactive alerting.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
import logging
from pathlib import Path

# Add project root to path for shared module imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cowles_project")

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Cowles Project — Broadcast Revenue Intelligence",
    description="Agentic intelligence layer for WideOrbit WO Traffic data",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev", "local"] else None,
    redoc_url=None,
)

# =============================================================================
# RATE LIMITING
# =============================================================================

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# CORS
# =============================================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

PRODUCTION_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")
if PRODUCTION_ORIGINS:
    ALLOWED_ORIGINS.extend([o.strip() for o in PRODUCTION_ORIGINS.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

# =============================================================================
# AI CLIENT INITIALIZATION
# =============================================================================

try:
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger.info("Anthropic client initialized")
except Exception as e:
    anthropic_client = None
    logger.warning(f"Anthropic not available: {e}. Running in MOCK mode.")

# =============================================================================
# DATA PATHS
# =============================================================================

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
SCHEMAS_DIR = DATA_DIR / "schemas"

# =============================================================================
# DATA LOADER + DATA ROUTES
# =============================================================================

from services.data_loader import DataLoader
data_loader = DataLoader(SAMPLE_DIR)

from routes.data import router as data_router, init_loader
init_loader(data_loader)
app.include_router(data_router)

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    context: Optional[str] = None  # "revenue", "inventory", "pacing", etc.

class ChatResponse(BaseModel):
    response: str

class HealthResponse(BaseModel):
    status: str
    service: str
    mode: str
    version: str
    data_status: Optional[Dict[str, Any]] = None

class PipelineStatusResponse(BaseModel):
    raw_files: int
    processed_files: int
    sample_files: int
    last_ingest: Optional[str] = None

# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@app.get("/", response_model=HealthResponse, tags=["health"])
async def root():
    return HealthResponse(
        status="online",
        service="Cowles Project — Broadcast Revenue Intelligence",
        mode="AI" if anthropic_client else "MOCK",
        version="0.1.0",
    )

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    data_status = {
        "raw_dir_exists": RAW_DIR.exists(),
        "sample_dir_exists": SAMPLE_DIR.exists(),
        "processed_dir_exists": PROCESSED_DIR.exists(),
        "sample_files": len(list(SAMPLE_DIR.glob("*.csv"))) if SAMPLE_DIR.exists() else 0,
    }
    return HealthResponse(
        status="healthy",
        service="Cowles Project — Broadcast Revenue Intelligence",
        mode="AI" if anthropic_client else "MOCK",
        version="0.1.0",
        data_status=data_status,
    )

# =============================================================================
# PIPELINE STATUS
# =============================================================================

@app.get("/api/pipeline/status", response_model=PipelineStatusResponse, tags=["pipeline"])
async def pipeline_status():
    """Check the status of the data pipeline."""
    return PipelineStatusResponse(
        raw_files=len(list(RAW_DIR.glob("*.csv"))) if RAW_DIR.exists() else 0,
        processed_files=len(list(PROCESSED_DIR.glob("*.csv"))) if PROCESSED_DIR.exists() else 0,
        sample_files=len(list(SAMPLE_DIR.glob("*.csv"))) if SAMPLE_DIR.exists() else 0,
    )

# =============================================================================
# CHAT ENDPOINT — Revenue Intelligence
# =============================================================================

SYSTEM_PROMPT = """You are a broadcast revenue intelligence analyst for a television station group.
You analyze WideOrbit WO Traffic data to provide insights on:
- Revenue trends by daypart (early morning, daytime, early fringe, early news, prime access, prime, late news, late fringe)
- Average Unit Rate (AUR) analysis and pricing recommendations
- Advertiser concentration and revenue risk assessment
- Sell-out rates and inventory pacing vs. prior year
- Makegood exposure and preemption impact

You are advisory only — all recommendations require human approval before action.
You speak in the language of broadcast TV sales: dayparts, AUR, sell-out rates, pacing, makegoods.
Be specific with numbers when data is available. Flag data gaps honestly.
Never fabricate data points — if you don't have the data, say so."""

@app.post("/chat", response_model=ChatResponse, tags=["chat"])
@limiter.limit("60/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """Revenue intelligence chat endpoint."""
    try:
        if anthropic_client:
            messages = []
            for msg in (chat_request.history or []):
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": chat_request.message})

            response = anthropic_client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
            )

            response_text = response.content[0].text
            logger.info(f"Chat processed: {len(chat_request.message)} chars in, {len(response_text)} chars out")
        else:
            response_text = (
                f"[MOCK] Received: '{chat_request.message}'\n\n"
                "The AI service is not configured. Set ANTHROPIC_API_KEY to enable.\n"
                "Running in mock mode — no WideOrbit data analysis available."
            )

        return ChatResponse(response=response_text)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
