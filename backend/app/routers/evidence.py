
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/api/evidence",
    tags=["Test Evidence"]
)

# Screenshots are stored in the project's screenshots folder.
SCREENSHOT_DIR = (
    Path(__file__).resolve().parents[3] / "screenshots"
).resolve()


@router.get("/screenshots/{filename}")
def get_screenshot(filename: str):

    # Accept only filenames created by the test executor.
    if not re.fullmatch(
    r"run_\d+(?:_test_\d+)?_[a-f0-9]+\.png",
    filename
):
        raise HTTPException(
            status_code=400,
            detail="Invalid screenshot filename"
        )

    screenshot_path = (
        SCREENSHOT_DIR / filename
    ).resolve()

    # Prevent access outside the screenshots directory.
    if screenshot_path.parent != SCREENSHOT_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid screenshot location"
        )

    if not screenshot_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Screenshot not found"
        )

    return FileResponse(
        path=screenshot_path,
        media_type="image/png",
        filename=filename
    )
