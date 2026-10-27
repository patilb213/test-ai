
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import login_user, signup_user
from .database import check_database
from .schemas import LoginRequest, SignupRequest

from .projects import router as projects_router
from .tests import router as tests_router
from .runs import router as runs_router
from .recorder import router as recorder_router
from .dashboard import router as dashboard_router
from .healing_routes import router as healing_router


# ============================================================
# TEST AI APPLICATION
# ============================================================

app = FastAPI(
    title="Test AI API",
    description=(
        "AI-assisted smart test recording, execution, "
        "verification and self-healing platform"
    ),
    version="1.0.0",
)


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = BACKEND_DIR / "evidence"

EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

configured_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

allowed_origins = [
    origin.strip().rstrip("/")
    for origin in configured_origins.split(",")
    if origin.strip()
]


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(projects_router)
app.include_router(tests_router)
app.include_router(runs_router)
app.include_router(recorder_router)
app.include_router(dashboard_router)
app.include_router(healing_router)


# ============================================================
# EVIDENCE
# ============================================================

# Local-development compatibility only.
# Production evidence requires authenticated access,
# per-user authorization and durable private storage.

if os.getenv("ENABLE_PUBLIC_EVIDENCE", "false").lower() == "true":
    app.mount(
        "/evidence",
        StaticFiles(directory=str(EVIDENCE_DIR)),
        name="evidence",
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Test AI Backend is running",
        "service": "Test AI API",
        "version": "1.0.0",
        "features": [
            "Project Management",
            "Scriptless Test Recording",
            "Reusable Test Cases",
            "Automated Test Execution",
            "Expected Result Verification",
            "Self-Healing Locators",
            "Evidence Screenshots",
            "Test Run History",
            "Dashboard Analytics",
        ],
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    database_status = check_database()

    if not database_status:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {
        "status": "healthy",
        "service": "Test AI API",
        "database": True,
    }


# ============================================================
# SIGNUP
# ============================================================

@app.post("/api/auth/signup")
def signup(data: SignupRequest):
    try:
        user = signup_user(
            data.name,
            data.email,
            data.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid registration details or email already registered",
        )

    return {
        "message": "Signup successful",
        "user": user,
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(data: LoginRequest):
    result = login_user(
        data.email,
        data.password,
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return result
