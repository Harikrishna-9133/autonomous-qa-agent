# Autonomous AI Testing & QA Agent

An AI-powered website testing and quality assurance platform that explores websites, generates test scenarios, executes browser-based tests, investigates failures, and generates QA reports.

## 1. Project Overview

The Autonomous AI Testing & QA Agent automates important software testing activities using browser automation, AI-assisted analysis, and workflow orchestration.

The platform helps users:
- Register and manage website projects.
- Explore website pages and identify features.
- Generate test scenarios.
- Execute browser tests using Playwright.
- Investigate failed test results.
- Capture testing evidence.
- Generate and manage QA reports.

## 2. Technology Stack

### Frontend
- React
- Vite
- JavaScript
- Axios
- Recharts
- Lucide React

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg
- Playwright

### AI and Orchestration
- LangGraph
- LangChain Core
- OpenAI API integration with rule-based fallback

### Deployment
- Docker
- Docker Compose
- Nginx
- WSL 2

## 3. System Architecture

The application follows a frontend-backend architecture.

1. React frontend provides the user interface.
2. FastAPI handles API requests and application workflows.
3. LangGraph coordinates the testing workflow.
4. Playwright performs browser automation.
5. PostgreSQL stores projects, test cases, execution results, and bug reports.
6. The reporting module generates QA reports.

## 4. Main Modules

- Website Project Management
- Website Explorer Agent
- Test Planner
- Test Executor
- Bug Investigator
- QA Report Generator
- Autonomous Workflow Orchestration

## 5. Docker Deployment

### Prerequisites
- Docker Desktop
- Docker Compose
- Existing PostgreSQL database
- Windows with WSL 2 support

### Start the application

From the project root:

```powershell
docker compose up -d
```

### Check containers

```powershell
docker compose ps
```

### View backend logs

```powershell
docker compose logs --tail=50 backend
```

### Restart containers

```powershell
docker compose restart
```

### Stop containers

```powershell
docker compose down
```

Do not use `docker compose down -v` when preserving database or volume data is important.

## 6. Application URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Backend Health | http://localhost:8000/health |
| Database Health | http://localhost:8000/db-health |

## 7. Demonstrated Testing Results

A Docker-based QA execution was completed against the portfolio website.

- Run ID: 38
- Total tests: 8
- Passed: 8
- Failed: 0
- Skipped: 0
- Pass rate: 100%

The QA report was generated and displayed successfully.

The Bug Reports interface also displayed existing database records after the Docker restart test.

## 8. Security Considerations

- Keep API keys and database credentials in environment variables.
- Never commit `.env` files.
- Restrict website testing to authorized targets.
- Validate URLs and browser requests.
- Apply browser isolation, network restrictions, and resource limits before production use.
- Protect screenshots and test evidence from unauthorized access.

## 9. Current Limitations

- Some test planning and bug investigation paths use rule-based fallbacks.
- Test execution still uses keyword-driven interpretation in some workflows.
- Full autonomous natural-language test execution needs further development.
- Additional network isolation, authentication, and production deployment hardening are required.

## 10. Future Enhancements

- More advanced AI-driven test planning.
- Natural-language test execution.
- Improved root-cause analysis.
- Retrieval-Augmented Generation for historical testing knowledge.
- Enhanced browser isolation.
- CI/CD integration.
- Advanced test analytics and reporting.

## 11. Project Goal

The goal is to build an intelligent and extensible QA platform that reduces repetitive manual testing work and helps teams identify, investigate, and report website defects efficiently.