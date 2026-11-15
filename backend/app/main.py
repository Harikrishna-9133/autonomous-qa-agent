from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from app.database import Base, engine, test_database_connection
from app.models import Project
from app.routers.project import router as project_router
from app.routers.test_case import router as test_case_router
from app.routers.test_run import router as test_run_router
from app.routers.ai_planner import router as ai_planner_router
from app.routers.bug_report import router as bug_report_router
from app.routers.qa_report import router as qa_report_router
from app.routers import qa_report
from app.routers.exploration import router as exploration_router
from app.routers.agent import router as agent_router
from app.routers.evidence import router as evidence_router

app = FastAPI(
    title="Autonomous AI Testing Agent",
    description="An AI-powered software testing and QA platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(project_router)
app.include_router(test_case_router)
app.include_router(test_run_router)
app.include_router(ai_planner_router)
app.include_router(bug_report_router)
app.include_router(qa_report_router)
app.include_router(qa_report.router)
app.include_router(exploration_router)
app.include_router(agent_router)
app.include_router(evidence_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to Autonomous AI Testing Agent",
        "status": "Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Autonomous QA Agent"
    }


@app.get("/db-health")
def database_health():
    try:
        test_database_connection()
        return {
            "status": "connected",
            "database": "qa_agent_db"
        }
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )


@app.get("/tables")
def get_tables():
    return {
        "tables": list(Base.metadata.tables.keys())
    }
