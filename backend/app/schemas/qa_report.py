from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QAProjectInfo(BaseModel):
    project_id: int
    project_name: str
    website_url: str


class QATestExecutionInfo(BaseModel):
    test_run_id: int
    run_status: str
    started_at: datetime
    completed_at: Optional[datetime] = None


class QAExecutionSummary(BaseModel):
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_percentage: float


class QABugSeveritySummary(BaseModel):
    critical: int
    high: int
    medium: int
    low: int


class QABugStatusSummary(BaseModel):
    open: int
    in_progress: int
    resolved: int


class QABugSummary(BaseModel):
    total_bugs: int
    severity: QABugSeveritySummary
    status: QABugStatusSummary


class QATestDetail(BaseModel):
    test_result_id: int
    test_case_id: int
    test_title: str
    status: str
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    screenshot_path: Optional[str] = None



class QABugDetail(BaseModel):
    bug_id: int
    test_result_id: int
    title: str
    description: Optional[str] = None
    severity: str

    # Advanced investigation details
    failure_type: Optional[str] = None
    component: Optional[str] = None
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    reproduction_steps: Optional[str] = None

    # Bug lifecycle details
    status: str
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None



class QAReportResponse(BaseModel):
    project: QAProjectInfo
    test_execution: QATestExecutionInfo
    execution_summary: QAExecutionSummary
    bug_summary: QABugSummary
    test_details: list[QATestDetail]
    bug_details: list[QABugDetail]
    recommendations: list[str]