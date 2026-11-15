
import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()


# Structure of one AI-generated test case
class GeneratedTestCase(BaseModel):
    title: str
    description: str
    steps: list[str]
    expected_result: str
    priority: Literal["low", "medium", "high"]


# Structure of the complete test plan
class TestPlan(BaseModel):
    test_cases: list[GeneratedTestCase]


def generate_test_plan(
    project_name: str,
    website_url: str,
    description: str,
    features: list[str],
    number_of_tests: int = 5
) -> dict:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from the .env file")

    if not 1 <= number_of_tests <= 15:
        raise ValueError("number_of_tests must be between 1 and 15")

    client = OpenAI(api_key=api_key)

    system_prompt = """
    You are an expert software quality assurance test planner.

    Generate practical website test cases based on the project details
    and features provided by the user.

    Rules:
    1. Generate the requested number of test cases.
    2. Include clear and actionable testing steps.
    3. Include measurable expected results.
    4. Assign priority as low, medium, or high.
    5. Cover different relevant testing scenarios.
    6. Do not invent website functionality that was not described.
    7. Test only normal, authorized website functionality.
    """

    user_prompt = f"""
    Generate {number_of_tests} test cases for this website.

    Project name: {project_name}
    Website URL: {website_url}
    Description: {description}
    Website features: {", ".join(features)}

    Return useful test cases for an automated QA platform.
    """

    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        text_format=TestPlan
    )

    if response.output_parsed is None:
        raise ValueError("AI did not return a valid test plan")

    return response.output_parsed.model_dump()
