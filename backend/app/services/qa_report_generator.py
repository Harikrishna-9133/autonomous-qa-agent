
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.models.test_case import TestCase
from app.models.bug_report import BugReport


def generate_qa_report(
    db: Session,
    project_id: int,
    run_id: int
):
    # 1. Get project details
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise ValueError("Project not found")

    # 2. Get test run
    test_run = db.query(TestRun).filter(
        TestRun.id == run_id,
        TestRun.project_id == project_id
    ).first()

    if not test_run:
        raise ValueError("Test run not found for this project")

    # 3. Get test results
    results = db.query(TestResult).filter(
        TestResult.test_run_id == run_id
    ).all()

    total_tests = len(results)

    passed = sum(
        result.status == "passed" for result in results
    )

    failed = sum(
        result.status == "failed" for result in results
    )

    skipped = sum(
        result.status == "skipped" for result in results
    )

    pass_percentage = (
        round((passed / total_tests) * 100, 2)
        if total_tests > 0 else 0
    )

    # 4. Get bug reports linked to this test run
    bugs = (
        db.query(BugReport)
        .join(
            TestResult,
            BugReport.test_result_id == TestResult.id
        )
        .filter(TestResult.test_run_id == run_id)
        .order_by(BugReport.id.desc())
        .all()
    )

    # 5. Calculate bug severity
    severity_summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    status_summary = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0
    }

    for bug in bugs:
        severity = bug.severity.lower()
        status = bug.status.lower()

        if severity in severity_summary:
            severity_summary[severity] += 1

        if status in status_summary:
            status_summary[status] += 1

    # 6. Get individual test details
    test_details = []

    for result in results:
        test_case = db.query(TestCase).filter(
            TestCase.id == result.test_case_id
        ).first()

        test_details.append({
            "test_result_id": result.id,
            "test_case_id": result.test_case_id,
            "test_title": (
                test_case.title if test_case else "Unknown Test"
            ),
            "status": result.status,
            "actual_result": result.actual_result,
            "error_message": result.error_message,
            "duration_ms": result.duration_ms,
            "screenshot_path": result.screenshot_path
        })

    # 7. Prepare complete bug investigation details
    bug_details = []

    for bug in bugs:
        bug_details.append({
            "bug_id": bug.id,
            "test_result_id": bug.test_result_id,
            "title": bug.title,
            "description": bug.description,
            "severity": bug.severity,

            # Advanced investigation details
            "failure_type": bug.failure_type,
            "component": bug.component,
            "root_cause": bug.root_cause,
            "suggested_fix": bug.suggested_fix,
            "reproduction_steps": bug.reproduction_steps,

            # Bug lifecycle details
            "status": bug.status,
            "resolution_notes": bug.resolution_notes,
            "resolved_at": bug.resolved_at
        })

    # 8. Generate recommendations
    recommendations = []

    if failed > 0:
        recommendations.append(
            "Investigate failed test cases and fix the identified issues."
        )

    if severity_summary["critical"] > 0:
        recommendations.append(
            "Address critical-severity bugs immediately."
        )

    if severity_summary["high"] > 0:
        recommendations.append(
            "Prioritize high-severity bugs."
        )

    if status_summary["open"] > 0:
        recommendations.append(
            "Review and assign all open bug reports."
        )

    if total_tests > 0 and failed == 0:
        recommendations.append(
            "All recorded tests passed. Continue regular regression testing."
        )

    if not recommendations:
        recommendations.append(
            "No immediate recommendations based on the recorded results."
        )

    # 9. Return complete QA report
    return {
        "project": {
            "project_id": project.id,
            "project_name": project.name,
            "website_url": project.base_url
        },

        "test_execution": {
            "test_run_id": test_run.id,
            "run_status": test_run.status,
            "started_at": test_run.started_at,
            "completed_at": test_run.completed_at
        },

        "execution_summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_percentage": pass_percentage
        },

        "bug_summary": {
            "total_bugs": len(bugs),
            "severity": severity_summary,
            "status": status_summary
        },

        "test_details": test_details,

        "bug_details": bug_details,

        "recommendations": recommendations
    }
