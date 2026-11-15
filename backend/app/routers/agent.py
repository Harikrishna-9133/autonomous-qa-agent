
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.test_run import TestRun
from app.agents.qa_graph import qa_agent_graph


router = APIRouter(
    prefix="/api/agent",
    tags=["Autonomous QA Agent"]
)


@router.post("/run/{project_id}")
async def run_autonomous_qa(
    project_id: int,
    db: Session = Depends(get_db)
):
    # 1. Retrieve the project.
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found."
        )

    # 2. Create a new test run.
    test_run = TestRun(
        project_id=project.id,
        status="running"
    )

    db.add(test_run)
    db.commit()
    db.refresh(test_run)

    # 3. Prepare the initial LangGraph state.
    initial_state = {
        "project_id": project.id,
        "project_name": project.name,
        "website_url": project.base_url,
        "project_description": project.description or "",
        "number_of_tests": 8,
        "test_run_id": test_run.id,
        "errors": [],
        "workflow_status": "running"
    }

    try:
        # 4. Execute the complete LangGraph workflow.
        final_state = await qa_agent_graph.ainvoke(initial_state)
                # Verify that the final QA reporting stage completed.
        if final_state.get("current_step") != "reporter_completed":
            raise RuntimeError(
                "Autonomous QA workflow did not complete successfully. "
                f"Current step: {final_state.get('current_step')}. "
                f"Errors: {final_state.get('errors', [])}"
            )

        return {
            "message": "Autonomous QA workflow finished.",
            "project_id": project.id,
            "project_name": project.name,
            "test_run_id": test_run.id,
            "workflow_status": final_state.get(
                "workflow_status", "unknown"
            ),
            "current_step": final_state.get("current_step"),
            "discovered_features": final_state.get(
                "discovered_features", []
            ),
            "total_generated_tests": len(
                final_state.get("generated_test_cases", [])
            ),
            "execution_results": final_state.get(
                "execution_results", []
            ),
            "bug_reports": final_state.get("bug_reports", []),
            "qa_report": final_state.get("qa_report"),
            "errors": final_state.get("errors", [])
        }

    except Exception as error:
        # 5. Mark the run as failed if the workflow crashes.
        db.rollback()

        failed_run = db.query(TestRun).filter(
            TestRun.id == test_run.id
        ).first()

        if failed_run:
            failed_run.status = "failed"
            failed_run.completed_at = datetime.now(timezone.utc)
            db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Autonomous QA workflow failed: {str(error)}"
        )
