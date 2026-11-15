
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseResponse


router = APIRouter(
    prefix="/api/test-cases",
    tags=["Test Cases"]
)


@router.post(
    "/",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED
)
def create_test_case(
    data: TestCaseCreate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == data.project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    test_case = TestCase(**data.model_dump())

    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    return test_case


@router.get("/", response_model=list[TestCaseResponse])
def get_test_cases(db: Session = Depends(get_db)):
    return db.query(TestCase).order_by(TestCase.id.desc()).all()


@router.get("/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(
    test_case_id: int,
    db: Session = Depends(get_db)
):
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id
    ).first()

    if not test_case:
        raise HTTPException(
            status_code=404,
            detail="Test case not found"
        )

    return test_case


@router.delete("/{test_case_id}")
def delete_test_case(
    test_case_id: int,
    db: Session = Depends(get_db)
):
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id
    ).first()

    if not test_case:
        raise HTTPException(
            status_code=404,
            detail="Test case not found"
        )

    db.delete(test_case)
    db.commit()

    return {
        "message": "Test case deleted successfully",
        "test_case_id": test_case_id
    }


@router.put("/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_case_id: int,
    data: TestCaseCreate,
    db: Session = Depends(get_db)
):
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id
    ).first()

    if not test_case:
        raise HTTPException(
            status_code=404,
            detail="Test case not found"
        )

    project = db.query(Project).filter(
        Project.id == data.project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    update_data = data.model_dump()

    for field, value in update_data.items():
        setattr(test_case, field, value)

    db.commit()
    db.refresh(test_case)

    return test_case
