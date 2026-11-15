
from pydantic import BaseModel, Field


class AIPlannerRequest(BaseModel):
    features: list[str] = Field(
        min_length=1,
        description="Website features to generate test cases for"
    )

    number_of_tests: int = Field(
        default=5,
        ge=1,
        le=15
    )
