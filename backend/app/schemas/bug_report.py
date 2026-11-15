
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BugReportCreate(BaseModel):
    test_result_id: int
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    severity: str = "medium"
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    failure_type: str = "unknown"
    component: Optional[str] = None
    reproduction_steps: Optional[str] = None
    resolution_notes: Optional[str] = None
    status: str = "open"


class BugReportLifecycleUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class BugReportResponse(BaseModel):
    id: int
    test_result_id: int
    title: str
    description: Optional[str]
    severity: str
    root_cause: Optional[str]
    suggested_fix: Optional[str]
    failure_type: str
    component: Optional[str]
    reproduction_steps: Optional[str]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    updated_at: datetime
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
