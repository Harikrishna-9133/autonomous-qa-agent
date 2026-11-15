
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    base_url: HttpUrl
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    base_url: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
