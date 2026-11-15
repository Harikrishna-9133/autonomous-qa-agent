import asyncio
import json
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.bug_report import BugReport
from app.agents.investigator_node import investigator_node
from app.agents.reporter_node import reporter_node


PROJECT_ID = 3
TEST_CASE_ID = 68

db = SessionLocal()

try:
    # Verify the existing project and test case.
    project = db.query(Project).filter(
        Project.id == PROJECT_ID
    ).first()

    test_case = db.query(TestCase).filter(
        TestCase.id == TEST_CASE_ID,
        TestCase.project_id == PROJECT_ID
    ).first()

    if not project or not test_case:
        raise ValueError("Project or test case not found.")

    # Create a new test run.
    test_run = TestRun(
        project_id=PROJECT_ID,
        status="running",
        started_at=datetime.now(timezone.utc)
    )

    db.add(test_run)
    db.commit()
    db.refresh(test_run)

    # Insert one clearly labelled synthetic failure.
    test_result = TestResult(
        test_run_id=test_run.id,
        test_case_id=test_case.id,
        status="failed",
        actual_result="Synthetic controlled browser timeout.",
        error_message=(
            "TimeoutError: Synthetic controlled timeout "
            "while waiting for a page element."
        ),
        duration_ms=100,
        screenshot_path=None
    )

    db.add(test_result)
    db.commit()
    db.refresh(test_result)

    run_id = test_run.id
    result_id = test_result.id

    print("\nCONTROLLED TEST CREATED")
    print("Project ID:", PROJECT_ID)
    print("Test Run ID:", run_id)
    print("Test Result ID:", result_id)

finally:
    db.close()


# Execute the actual Investigator Node.
state = {
    "project_id": PROJECT_ID,
    "test_run_id": run_id,
    "execution_results": [{
        "test_result_id": result_id,
        "test_case_id": TEST_CASE_ID,
        "title": "Synthetic Browser Timeout Test",
        "status": "failed",
        "actual_result": "Synthetic controlled browser timeout.",
        "error_message": (
            "TimeoutError: Synthetic controlled timeout "
            "while waiting for a page element."
        )
    }],
    "errors": []
}

investigation_output = asyncio.run(
    investigator_node(state)
)

print("\nINVESTIGATOR OUTPUT")
print(json.dumps(investigation_output, indent=2, default=str))

if investigation_output.get("workflow_status") == "failed":
    raise RuntimeError("Investigator Node failed. Check the output above.")

if len(investigation_output.get("bug_reports", [])) != 1:
    raise RuntimeError("Expected exactly one investigated bug.")

# Execute the actual Reporter Node.
report_state = {
    **state,
    **investigation_output
}

reporter_output = asyncio.run(
    reporter_node(report_state)
)

print("\nREPORTER OUTPUT")
print(json.dumps(reporter_output, indent=2, default=str))

if reporter_output.get("workflow_status") == "failed":
    raise RuntimeError("Reporter Node failed. Check the output above.")

# Verify the saved database records.
db = SessionLocal()

try:
    saved_bug = db.query(BugReport).filter(
        BugReport.test_result_id == result_id
    ).first()

    if not saved_bug:
        raise RuntimeError("Bug report was not saved.")

    print("\nDATABASE VERIFICATION")
    print("Bug ID:", saved_bug.id)
    print("Failure type:", saved_bug.failure_type)
    print("Component:", saved_bug.component)
    print("Root cause:", saved_bug.root_cause)
    print("Suggested fix:", saved_bug.suggested_fix)
    print("Reproduction steps:", saved_bug.reproduction_steps)
    print("Status:", saved_bug.status)

    print("\nQA REPORT VERIFICATION")
    print(json.dumps(
        reporter_output.get("qa_report"),
        indent=2,
        default=str
    ))

    print("\nEND-TO-END INVESTIGATOR TEST PASSED")

finally:
    db.close()
