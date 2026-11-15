
from types import SimpleNamespace

from app.database import SessionLocal
from app.models.test_result import TestResult
from app.models.test_case import TestCase
from app.models.bug_report import BugReport
from app.services.ai_bug_investigator import investigate_bug_with_ai


async def investigator_node(state: dict) -> dict:
    """
    LangGraph Investigator Node.

    Investigates failed test results using execution checks
    and original test-case information, then saves bug reports.
    """

    db = SessionLocal()

    try:
        execution_results = state.get("execution_results", [])
        test_run_id = state.get("test_run_id")

        errors = list(state.get("errors", []))
        bug_reports = []

        if not test_run_id:
            raise ValueError("Test Run ID is missing.")

        failed_results = [
            result
            for result in execution_results
            if result.get("status") == "failed"
        ]

        print("Investigator Node started.")
        print(f"Failed tests to investigate: {len(failed_results)}")

        for result in failed_results:

            test_result_id = result.get("test_result_id")

            if not test_result_id:
                raise ValueError(
                    f"Missing database TestResult ID for: "
                    f"{result.get('title', 'Unknown test')}"
                )

            saved_result = db.query(TestResult).filter(
                TestResult.id == test_result_id,
                TestResult.test_run_id == test_run_id
            ).first()


            if not saved_result:
                raise ValueError(
                    f"Test result {test_result_id} was not found "
                    f"in test run {test_run_id}."
                )

            # Prevent duplicate bug reports for this test result.
            existing_bug = db.query(BugReport).filter(
                BugReport.test_result_id == saved_result.id
            ).order_by(BugReport.id.desc()).first()

            if existing_bug:
                print(
                    f"Bug report already exists for test result "
                    f"{saved_result.id}. Reusing report #{existing_bug.id}."
                )

                bug_reports.append({
                    "bug_id": existing_bug.id,
                    "test_result_id": saved_result.id,
                    "test_case_id": saved_result.test_case_id,
                    "test_title": result.get("title"),
                    "title": existing_bug.title,
                    "description": existing_bug.description,
                    "severity": existing_bug.severity,
                    "failure_type": existing_bug.failure_type,
                    "component": existing_bug.component,
                    "root_cause": existing_bug.root_cause,
                    "suggested_fix": existing_bug.suggested_fix,
                    "reproduction_steps": existing_bug.reproduction_steps,
                    "status": existing_bug.status
                })

                continue

            # Retrieve the original test case.


            # Retrieve the original test case.
            test_case = db.query(TestCase).filter(
                TestCase.id == saved_result.test_case_id
            ).first()

            # Preserve the detailed checks from executor state.
            checks = result.get("checks", [])

            # Build a richer investigation input.
            test_result_object = SimpleNamespace(
                error_message=saved_result.error_message,
                actual_result=saved_result.actual_result,
                screenshot_path=saved_result.screenshot_path,
                checks=checks,
                test_title=(
                    test_case.title
                    if test_case
                    else result.get("title", "Unknown test")
                ),
                test_description=(
                    test_case.description
                    if test_case
                    else ""
                ),
                test_steps=(
                    test_case.steps
                    if test_case
                    else ""
                ),
                expected_result=(
                    test_case.expected_result
                    if test_case
                    else ""
                )
            )

            investigation = investigate_bug(test_result_object)

            bug = BugReport(
                test_result_id=saved_result.id,
                title=investigation["title"],
                description=investigation["description"],
                severity=investigation["severity"],
                root_cause=investigation["root_cause"],
                suggested_fix=investigation["suggested_fix"],
                failure_type=investigation["failure_type"],
                component=investigation["component"],
                reproduction_steps=investigation["reproduction_steps"],
                status="open"
            )

            db.add(bug)
            db.flush()

            bug_reports.append({
                "bug_id": bug.id,
                "test_result_id": saved_result.id,
                "test_case_id": saved_result.test_case_id,
                "test_title": result.get("title"),
                "title": bug.title,
                "description": bug.description,
                "severity": bug.severity,
                "failure_type": bug.failure_type,
                "component": bug.component,
                "root_cause": bug.root_cause,
                "suggested_fix": bug.suggested_fix,
                "reproduction_steps": bug.reproduction_steps,
                "status": bug.status
            })

        db.commit()

        print(
            f"Investigator completed: "
            f"{len(bug_reports)} bug reports saved."
        )

        return {
            "bug_reports": bug_reports,
            "current_step": "investigator_completed",
            "workflow_status": "running",
            "errors": errors
        }

    except Exception as error:
        db.rollback()

        print(f"Investigator Node error: {error}")

        return {
            "current_step": "investigator_failed",
            "workflow_status": "failed",
            "errors": state.get("errors", [])
            + [f"Bug investigation failed: {str(error)}"]
        }

    finally:
        db.close()
