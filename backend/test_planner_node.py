
import asyncio
from app.agents.planner_node import planner_node

state = {
    "project_name": "Hari Krishna Portfolio",
    "website_url": "https://harikrishnaportfolio-nine.vercel.app/",
    "project_description": "Personal portfolio website",
    "discovered_features": [
        "homepage",
        "about",
        "experience",
        "projects",
        "skills",
        "notes",
        "contact",
        "navigation"
    ],
    "number_of_tests": 8,
    "errors": []
}

async def main():
    result = await planner_node(state)

    print("\n========== PLANNER NODE RESULT ==========")
    print("Current Step:", result.get("current_step"))
    print("Workflow Status:", result.get("workflow_status"))

    cases = result.get("generated_test_cases", [])

    print("\nTotal Generated Test Cases:", len(cases))

    for index, case in enumerate(cases, start=1):
        print(f"\nTest Case {index}")
        print("Title:", case.get("title"))
        print("Priority:", case.get("priority"))
        print("Steps:", case.get("steps"))
        print("Expected:", case.get("expected_result"))

    if result.get("errors"):
        print("\nErrors:", result["errors"])

asyncio.run(main())
