
from typing import Any, TypedDict


class QAAgentState(TypedDict, total=False):
    """
    Shared state passed between all nodes
    in the Autonomous QA Agent workflow.
    """

    # Project information
    project_id: int
    project_name: str
    website_url: str
    project_description: str
    number_of_tests: int

    # Website exploration
    exploration_data: dict[str, Any]
    discovered_features: list[str]

    # Test planning
    generated_test_cases: list[dict[str, Any]]

    # Test execution
    test_run_id: int
    execution_results: list[dict[str, Any]]

    # Bug investigation
    bug_reports: list[dict[str, Any]]

    # Final QA report
    qa_report: dict[str, Any]

    # Workflow tracking
    current_step: str
    workflow_status: str
    errors: list[str]
