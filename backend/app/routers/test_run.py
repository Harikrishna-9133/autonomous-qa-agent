from app.services.test_executor import execute_test_case as run_browser_test_case
from app.services.browser_service import validate_url
from time import perf_counter
from app.services.browser_service import run_homepage_test
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.schemas.test_run import (
    TestRunCreate,
    TestRunResponse,
    TestResultCreate,
    TestResultResponse
)

router = APIRouter(
    prefix="/api/test-runs",
    tags=["Test Execution"]
)


@router.post(
    "/",
    response_model=TestRunResponse,
    status_code=status.HTTP_201_CREATED
)
def create_test_run(
    data: TestRunCreate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == data.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    test_run = TestRun(
        project_id=data.project_id,
        status="running"
    )

    db.add(test_run)
    db.commit()
    db.refresh(test_run)

    return test_run


@router.get("/", response_model=list[TestRunResponse])
def get_test_runs(db: Session = Depends(get_db)):
    return db.query(TestRun).order_by(TestRun.id.desc()).all()


@router.get("/{run_id}", response_model=TestRunResponse)
def get_test_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    return run


@router.post(
    "/{run_id}/results",
    response_model=TestResultResponse,
    status_code=status.HTTP_201_CREATED
)
def create_test_result(
    run_id: int,
    data: TestResultCreate,
    db: Session = Depends(get_db)
):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Results can only be added to a running test run"
        )

    test_case = db.query(TestCase).filter(
        TestCase.id == data.test_case_id,
        TestCase.project_id == run.project_id
    ).first()

    if not test_case:
        raise HTTPException(
            status_code=404,
            detail="Test case not found in this project"
        )

    result = TestResult(
        test_run_id=run_id,
        **data.model_dump()
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result


@router.get("/{run_id}/results", response_model=list[TestResultResponse])
def get_test_results(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    return db.query(TestResult).filter(
        TestResult.test_run_id == run_id
    ).order_by(TestResult.id).all()


@router.post("/{run_id}/complete", response_model=TestRunResponse)
def complete_test_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Only running test runs can be completed"
        )

    results = db.query(TestResult).filter(
        TestResult.test_run_id == run_id
    ).all()

    if not results:
        raise HTTPException(
            status_code=400,
            detail="Add at least one test result before completing the run"
        )

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)

    return run


@router.get("/{run_id}/summary")
def get_test_run_summary(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    results = db.query(TestResult).filter(
        TestResult.test_run_id == run_id
    ).all()

    passed = sum(result.status == "passed" for result in results)
    failed = sum(result.status == "failed" for result in results)
    skipped = sum(result.status == "skipped" for result in results)

    return {
        "test_run_id": run_id,
        "project_id": run.project_id,
        "status": run.status,
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped
    }


@router.post("/{run_id}/execute/{test_case_id}")
def execute_test_case(
    run_id: int,
    test_case_id: int,
    db: Session = Depends(get_db)
):
    run = db.query(TestRun).filter(
        TestRun.id == run_id
    ).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Test run must be running"
        )

    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.project_id == run.project_id
    ).first()

    if not test_case:
        raise HTTPException(
            status_code=404,
            detail="Test case not found in this project"
        )

    project = db.query(Project).filter(
        Project.id == run.project_id
    ).first()


    try:
        test_case_data = {
            "id": test_case.id,
            "title": test_case.title,
            "description": test_case.description,
            "steps": test_case.steps,
            "expected_result": test_case.expected_result
        }

        browser_result = run_browser_test_case(
            project.base_url,
            run_id,
            test_case_data
        )


        result_status = (
            "passed" if browser_result["passed"] else "failed"
        )

        result = TestResult(
            test_run_id=run_id,
            test_case_id=test_case_id,
            status=result_status,
            actual_result=browser_result["actual_result"],
            error_message=browser_result["error_message"],
            screenshot_path=browser_result["screenshot_path"]
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "message": "Automated browser test completed",
            "test_run_id": run_id,
            "test_case_id": test_case_id,
            "browser_result": browser_result,
            "saved_result": {
                "id": result.id,
                "status": result.status
            }
        }

    except Exception as error:
        db.rollback()

        result = TestResult(
            test_run_id=run_id,
            test_case_id=test_case_id,
            status="failed",
            actual_result="Browser test could not complete",
            error_message=str(error)
        )

        db.add(result)
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Automated test failed: {error}"
        )


@router.post("/{run_id}/execute-portfolio-suite")
def execute_portfolio_suite(
    run_id: int,
    db: Session = Depends(get_db)
):
    run = db.query(TestRun).filter(
        TestRun.id == run_id
    ).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Test run must be running"
        )

    project = db.query(Project).filter(
        Project.id == run.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    test_cases = {
        2: "Homepage loading",
        3: "Portfolio navigation",
        4: "Portfolio introduction"
    }


    try:
        test_case_data = {
            "id": test_case.id,
            "title": test_case.title,
            "description": test_case.description,
            "steps": test_case.steps,
            "expected_result": test_case.expected_result
        }

        browser_result = run_browser_test_case(
            project.base_url,
            run_id,
            test_case_data
        )


        saved_results = []

        for check in browser_result["checks"]:
            test_case_id = next(
                (
                    case_id for case_id, name in test_cases.items()
                    if name == check["name"]
                ),
                None
            )

            if test_case_id is None:
                continue

            test_case = db.query(TestCase).filter(
                TestCase.id == test_case_id,
                TestCase.project_id == run.project_id
            ).first()

            if not test_case:
                raise ValueError(
                    f"Test case {test_case_id} not found in this project"
                )

            result = TestResult(
                test_run_id=run_id,
                test_case_id=test_case_id,
                status="passed" if check["passed"] else "failed",
                actual_result=str(check["details"]),
                error_message=None if check["passed"] else str(check["details"]),
                screenshot_path=browser_result["screenshot_path"]
            )

            db.add(result)
            saved_results.append({
                "test_case_id": test_case_id,
                "name": check["name"],
                "status": result.status,
                "details": check["details"]
            })

        run.status = (
            "completed" if browser_result["passed"] else "failed"
        )
        run.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "message": "Portfolio test suite executed",
            "test_run_id": run_id,
            "browser_result": browser_result,
            "saved_results": saved_results
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio test suite failed: {error}"
        )


@router.post("/{run_id}/execute-generated-suite")
def execute_generated_suite(
    run_id: int,
    db: Session = Depends(get_db)
):
    run = db.query(TestRun).filter(
        TestRun.id == run_id
    ).first()

    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status != "running":
        raise HTTPException(
            status_code=400,
            detail="Test run must be running"
        )

    project = db.query(Project).filter(
        Project.id == run.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        validate_url(project.base_url)

        test_cases = db.query(TestCase).filter(
            TestCase.project_id == run.project_id,
            TestCase.status == "active"
        ).order_by(TestCase.id.asc()).all()

        if not test_cases:
            raise HTTPException(
                status_code=400,
                detail="No active test cases found"
            )

        saved_results = []

        for test_case in test_cases:
            start_time = perf_counter()

            test_case_data = {
                "id": test_case.id,
                "title": test_case.title,
                "description": test_case.description,
                "steps": test_case.steps,
                "expected_result": test_case.expected_result
            }

            try:
                browser_result = run_browser_test_case(
                    project.base_url,
                    run_id,
                    test_case_data
                )

                result_status = (
                    "passed" if browser_result["passed"] else "failed"
                )

                actual_result = browser_result["actual_result"]
                error_message = browser_result["error_message"]
                screenshot_path = browser_result["screenshot_path"]

            except Exception as error:
                result_status = "failed"
                actual_result = "Browser execution could not complete"
                error_message = str(error)
                screenshot_path = None

            duration_ms = int(
                (perf_counter() - start_time) * 1000
            )

            result = TestResult(
                test_run_id=run_id,
                test_case_id=test_case.id,
                status=result_status,
                actual_result=actual_result,
                error_message=error_message,
                duration_ms=duration_ms,
                screenshot_path=screenshot_path
            )

            db.add(result)

            saved_results.append({
                "test_case_id": test_case.id,
                "title": test_case.title,
                "status": result_status,
                "duration_ms": duration_ms,
                "actual_result": actual_result,
                "screenshot_path": screenshot_path
            })

        total_failed = sum(
            item["status"] == "failed"
            for item in saved_results
        )

        run.status = "failed" if total_failed else "completed"
        run.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "message": "Generated test suite executed successfully",
            "test_run_id": run_id,
            "project_id": run.project_id,
            "total_tests": len(saved_results),
            "passed": len(saved_results) - total_failed,
            "failed": total_failed,
            "status": run.status,
            "results": saved_results
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Generated test suite failed: {str(error)}"
        )
