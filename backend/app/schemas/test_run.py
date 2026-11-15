
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TestRunCreate(BaseModel):
    project_id: int


class TestRunResponse(BaseModel):
    id: int
    project_id: int
    status: str
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TestResultCreate(BaseModel):
    test_case_id: int
    status: Literal["passed", "failed", "skipped"]
    actual_result: str | None = None
    error_message: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    screenshot_path: str | None = None


class TestResultResponse(BaseModel):
    id: int
    test_run_id: int
    test_case_id: int
    status: str
    actual_result: str | None
    error_message: str | None
    duration_ms: int | None
    screenshot_path: str | None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
