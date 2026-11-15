
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.ai_planner import AIPlannerRequest
from app.services.local_test_planner import generate_test_plan
from app.services.website_explorer import explore_website


router = APIRouter(
    prefix="/api/ai-planner",
    tags=["AI Test Planner"]
)


def save_test_cases(db, project, plan):
    """Save generated test cases into the database."""

    saved_test_cases = []

    for item in plan["test_cases"]:

        steps_text = "\n".join(
            f"{index}. {step}"
            for index, step in enumerate(
                item["steps"],
                start=1
            )
        )

        test_case = TestCase(
            project_id=project.id,
            title=item["title"],
            description=item["description"],
            steps=steps_text,
            expected_result=item["expected_result"],
            priority=item["priority"],
            status="active"
        )

        db.add(test_case)
        db.flush()

        saved_test_cases.append({
            "id": test_case.id,
            "project_id": test_case.project_id,
            "title": test_case.title,
            "description": test_case.description,
            "steps": test_case.steps,
            "expected_result": test_case.expected_result,
            "priority": test_case.priority,
            "status": test_case.status
        })

    db.commit()

    return saved_test_cases


def get_discovered_features(exploration):
    """
    Convert discovered website sections into planner features.
    """

    section_mapping = {
        "home": "homepage",
        "about": "about",
        "experience": "experience",
        "projects": "projects",
        "skills": "skills",
        "blog": "notes",
        "notes": "notes",
        "contact": "contact"
    }

    discovered_features = []

    # A successfully explored website has a homepage.
    if exploration.get("pages"):
        discovered_features.append("homepage")

    section_links = exploration.get(
        "section_links",
        []
    )

    if section_links:
        discovered_features.append("navigation")

    # Convert section IDs into planner features.
    for section in section_links:

        section_id = section.get(
            "section_id",
            ""
        ).lower().strip()

        mapped_feature = section_mapping.get(
            section_id
        )

        if mapped_feature:
            discovered_features.append(mapped_feature)

    # Remove duplicate features while preserving order.
    unique_features = list(
        dict.fromkeys(discovered_features)
    )

    return unique_features


# -------------------------------------------------
# EXISTING ENDPOINT
# Manual feature-based test generation
# -------------------------------------------------

@router.post("/projects/{project_id}/generate")
def generate_project_test_cases(
    project_id: int,
    request: AIPlannerRequest,
    db: Session = Depends(get_db)
):

    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    try:

        plan = generate_test_plan(
            project_name=project.name,
            website_url=project.base_url,
            description=project.description or "",
            features=request.features,
            number_of_tests=request.number_of_tests
        )

        saved_test_cases = save_test_cases(
            db,
            project,
            plan
        )

        return {
            "message": "Test cases generated and saved successfully",
            "project_id": project.id,
            "project_name": project.name,
            "total_generated": len(saved_test_cases),
            "test_cases": saved_test_cases
        }

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Test generation failed: {str(error)}"
        )


# -------------------------------------------------
# NEW ENDPOINT
# Exploration-based test generation
# -------------------------------------------------

@router.post("/projects/{project_id}/generate-from-exploration")
def generate_tests_from_exploration(
    project_id: int,
    request: AIPlannerRequest,
    db: Session = Depends(get_db)
):

    # 1. Find the registered project.
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    try:

        # 2. Explore the registered website.
        exploration = explore_website(
            project.base_url
        )

        # 3. Extract features from discovered sections.
        discovered_features = get_discovered_features(
            exploration
        )

        # 4. Combine discovered features with user features.
        requested_features = request.features or []

        combined_features = list(
            dict.fromkeys(
                discovered_features + requested_features
            )
        )

        if not combined_features:
            raise ValueError(
                "No website features were discovered for test generation"
            )

        # 5. Generate test scenarios using the existing planner.
        plan = generate_test_plan(
            project_name=project.name,
            website_url=project.base_url,
            description=project.description or "",
            features=combined_features,
            number_of_tests=request.number_of_tests
        )

        # 6. Save generated scenarios in PostgreSQL.
        saved_test_cases = save_test_cases(
            db,
            project,
            plan
        )

        # 7. Return generated tests and exploration information.
        return {
            "message": "Exploration-based test cases generated successfully",
            "project_id": project.id,
            "project_name": project.name,
            "discovered_features": discovered_features,
            "features_used": combined_features,
            "exploration_summary": exploration.get(
                "summary",
                {}
            ),
            "total_generated": len(saved_test_cases),
            "test_cases": saved_test_cases
        }

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Exploration-based test generation failed: {str(error)}"
        )
