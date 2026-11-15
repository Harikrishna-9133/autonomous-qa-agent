from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.qa_report import QAReportResponse
from app.services.qa_report_generator import generate_qa_report


router = APIRouter(
    prefix="/api/qa-reports",
    tags=["QA Reports"]
)


@router.get(
    "/projects/{project_id}/runs/{run_id}",
    response_model=QAReportResponse
)
def get_qa_report(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db)
):
    try:
        report = generate_qa_report(
            db=db,
            project_id=project_id,
            run_id=run_id
        )
        return report

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )