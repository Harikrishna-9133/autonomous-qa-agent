
import asyncio
from time import perf_counter

from app.database import SessionLocal
from app.models.test_run import TestRun
from app.models.test_case import TestCase
from app.models.test_result import TestResult
from app.services.test_executor import execute_test_case


async def executor_node(state: dict) -> dict:
    """
    LangGraph Executor Node.

    Saves generated test cases and execution results
    in PostgreSQL while using the existing Playwright executor.
    """

    db = SessionLocal()

    try:
        website_url = state.get("website_url")
        project_id = state.get("project_id")
        test_run_id = state.get("test_run_id")
        generated_cases = state.get("generated_test_cases", [])

        if not website_url:
            raise ValueError("Website URL is missing.")

        if not project_id or not test_run_id:
            raise ValueError("Project ID or Test Run ID is missing.")

        if not generated_cases:
            raise ValueError("No generated test cases are available.")

        # 1. Verify that the test run exists and belongs to this project.
        test_run = db.query(TestRun).filter(
            TestRun.id == test_run_id,
            TestRun.project_id == project_id
        ).first()

        if not test_run:
            raise ValueError("Test run not found for this project.")

        if test_run.status != "running":
            raise ValueError("Test run must have running status.")

        print("Executor Node started.")
        print(f"Test Run ID: {test_run_id}")
        print(f"Total generated cases: {len(generated_cases)}")


        # 2. Save or reuse generated test cases in PostgreSQL.

        def normalize_case_value(value):
            return " ".join(str(value or "").split()).strip().lower()

        def make_case_key(title, steps, expected_result):
            return (
                normalize_case_value(title),
                normalize_case_value(steps),
                normalize_case_value(expected_result)
            )

        # Load existing active test cases for this project.
        existing_cases = db.query(TestCase).filter(
            TestCase.project_id == project_id,
            TestCase.status == "active"
        ).all()

        existing_case_map = {}

        for existing in existing_cases:
            key = make_case_key(
                existing.title,
                existing.steps,
                existing.expected_result
            )

            # Keep the first matching existing record.
            existing_case_map.setdefault(key, existing)

        saved_test_cases = []
        reused_count = 0
        created_count = 0

        for index, case in enumerate(generated_cases, start=1):

            steps = case.get("steps", [])

            if isinstance(steps, list):
                steps_text = "\n".join(
                    str(step) for step in steps
                )
            else:
                steps_text = str(steps)

            title = case.get(
                "title",
                f"Generated Test {index}"
            )

            expected_result = case.get(
                "expected_result",
                ""
            )

            key = make_case_key(
                title,
                steps_text,
                expected_result
            )

            # Reuse an existing matching test case.
            test_case = existing_case_map.get(key)

            if test_case:
                reused_count += 1

            else:
                # Create only genuinely new test cases.
                test_case = TestCase(
                    project_id=project_id,
                    title=title,
                    description=case.get("description", ""),
                    steps=steps_text,
                    expected_result=expected_result,
                    priority=case.get("priority", "medium"),
                    status="active"
                )

                db.add(test_case)
                db.flush()

                existing_case_map[key] = test_case
                created_count += 1

            saved_test_cases.append({
                "id": test_case.id,
                "title": test_case.title,
                "description": test_case.description,
                "steps": test_case.steps,
                "expected_result": test_case.expected_result,
                "priority": test_case.priority
            })

        db.commit()

        print(
            f"Test cases reused: {reused_count}; "
            f"new test cases created: {created_count}."
        )

        print(
            f"Total test cases ready for execution: "
            f"{len(saved_test_cases)}."
        )


        print(
            f"Saved {len(saved_test_cases)} test cases in PostgreSQL."
        )

        # 3. Execute each saved test case using Playwright.
        execution_results = []

        for index, test_case in enumerate(saved_test_cases, start=1):

            test_case_id = test_case["id"]
            title = test_case["title"]

            print(
                f"Executing {index}/{len(saved_test_cases)}: {title}"
            )

            start_time = perf_counter()

            try:
                browser_result = await asyncio.to_thread(
                    execute_test_case,
                    website_url,
                    test_run_id,
                    test_case
                )

                result_status = (
                    "passed"
                    if browser_result.get("passed")
                    else "failed"
                )

                actual_result = browser_result.get("actual_result")
                error_message = browser_result.get("error_message")
                screenshot_path = browser_result.get("screenshot_path")
                checks = browser_result.get("checks", [])

            except Exception as error:
                result_status = "failed"
                actual_result = "Browser execution could not be completed."
                error_message = str(error)
                screenshot_path = None
                checks = []

            duration_ms = int(
                (perf_counter() - start_time) * 1000
            )

            # 4. Save the execution result in PostgreSQL.
            saved_result = TestResult(
                test_run_id=test_run_id,
                test_case_id=test_case_id,
                status=result_status,
                actual_result=actual_result,
                error_message=error_message,
                duration_ms=duration_ms,
                screenshot_path=screenshot_path
            )

            db.add(saved_result)
            db.commit()
            db.refresh(saved_result)

            # 5. Keep database IDs in LangGraph state.
            execution_results.append({
                "test_result_id": saved_result.id,
                "test_case_id": test_case_id,
                "execution_index": index,
                "title": title,
                "status": result_status,
                "actual_result": actual_result,
                "error_message": error_message,
                "checks": checks,
                "duration_ms": duration_ms,
                "screenshot_path": screenshot_path
            })

        passed = sum(
            item["status"] == "passed"
            for item in execution_results
        )

        failed = sum(
            item["status"] == "failed"
            for item in execution_results
        )

        print(
            f"Executor completed: {passed} passed, {failed} failed."
        )

        return {
            "generated_test_cases": saved_test_cases,
            "execution_results": execution_results,
            "current_step": "executor_completed",
            "workflow_status": "running",
            "errors": state.get("errors", [])
        }

    except Exception as error:
        db.rollback()

        print(f"Executor Node error: {error}")

        return {
            "current_step": "executor_failed",
            "workflow_status": "failed",
            "errors": state.get("errors", [])
            + [f"Test execution failed: {str(error)}"]
        }

    finally:
        db.close()
