
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TestCaseCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    steps: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    priority: Literal["low", "medium", "high"] = "medium"


class TestCaseResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    steps: str
    expected_result: str
    priority: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
