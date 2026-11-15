
from app.services.local_test_planner import generate_test_plan


async def planner_node(state: dict) -> dict:
    """
    LangGraph Test Planner Node.

    Uses the existing local test planner to generate
    test cases from discovered website features.
    """

    try:
        project_name = state.get("project_name", "QA Project")
        website_url = state.get("website_url")

        description = state.get(
            "project_description",
            "Automatically explored website."
        )

        features = state.get("discovered_features", [])

        interactive_elements = (
            state.get("exploration_data", {})
            .get("pages", [])
        )

        interactive_elements = [
            element
    for page in interactive_elements
    for element in page.get("interactive_elements", [])
]

        number_of_tests = state.get("number_of_tests", 8)

        if not website_url:
            raise ValueError("Website URL is missing.")

        if not features and not interactive_elements:
            raise ValueError(
        "No website features or interactive elements were discovered."
    )

        print("Test Planner started.")
        print(f"Discovered features: {features}")
        print(f"Interactive elements received: {len(interactive_elements)}")

        # Generate test scenarios using existing planner.
        plan = generate_test_plan(
    project_name=project_name,
    website_url=website_url,
    description=description,
    features=features,
    number_of_tests=number_of_tests,
    interactive_elements=interactive_elements
)

        generated_cases = plan.get("test_cases", [])

        if not generated_cases:
            raise ValueError(
                "The planner did not generate any test cases."
            )

        print(
            f"Test Planner completed: {len(generated_cases)} cases generated."
        )

        return {
            "generated_test_cases": generated_cases,
            "current_step": "planner_completed",
            "workflow_status": "running",
            "errors": state.get("errors", [])
        }

    except Exception as error:
        print(f"Planner error: {error}")

        return {
            "current_step": "planner",
            "workflow_status": "failed",
            "errors": state.get("errors", [])
            + [f"Test planning failed: {str(error)}"]
        }
