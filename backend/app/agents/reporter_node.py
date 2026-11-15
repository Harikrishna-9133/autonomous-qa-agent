
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.test_run import TestRun
from app.services.qa_report_generator import generate_qa_report


async def reporter_node(state: dict) -> dict:
    """
    Final LangGraph Node.

    Updates test-run status and generates
    the final QA report from PostgreSQL.
    """

    db = SessionLocal()

    try:
        project_id = state.get("project_id")
        run_id = state.get("test_run_id")

        if not project_id or not run_id:
            raise ValueError("Project ID or Test Run ID is missing.")

        # 1. Retrieve the test run.
        test_run = db.query(TestRun).filter(
            TestRun.id == run_id,
            TestRun.project_id == project_id
        ).first()

        if not test_run:
            raise ValueError("Test run not found.")

        # 2. Determine the final run status.
        execution_results = state.get("execution_results", [])

        has_failed_tests = any(
            result.get("status") == "failed"
            for result in execution_results
        )

        has_workflow_errors = bool(state.get("errors", []))

        test_run.status = (
            "failed"
            if has_failed_tests or has_workflow_errors
            else "completed"
        )

        test_run.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(test_run)

        # 3. Generate the final QA report.
        qa_report = generate_qa_report(
            db=db,
            project_id=project_id,
            run_id=run_id
        )

        print("QA Report generated successfully.")

        return {
            "qa_report": qa_report,
            "current_step": "reporter_completed",
            "workflow_status": (
                "failed"
                if has_failed_tests or has_workflow_errors
                else "completed"
            ),
            "errors": state.get("errors", [])
        }

    except Exception as error:
        db.rollback()

        print(f"Reporter Node error: {error}")

        return {
            "current_step": "reporter_failed",
            "workflow_status": "failed",
            "errors": state.get("errors", [])
            + [f"QA report generation failed: {str(error)}"]
        }

    finally:
        db.close()
