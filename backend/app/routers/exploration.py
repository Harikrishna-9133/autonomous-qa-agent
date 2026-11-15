
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.services.website_explorer import explore_website


router = APIRouter(
    prefix="/api/exploration",
    tags=["Autonomous Website Exploration"]
)


@router.post("/projects/{project_id}")
def explore_project(
    project_id: int,
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
        result = explore_website(project.base_url)

        return {
            "message": "Website exploration completed",
            "project_id": project.id,
            "project_name": project.name,
            "exploration": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Website exploration failed: {str(error)}"
        )
