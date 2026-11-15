from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.test_result import TestResult
from app.models.bug_report import BugReport
from app.schemas.bug_report import (
    BugReportCreate,
    BugReportResponse,
    BugReportLifecycleUpdate
)
from app.services.bug_investigator import investigate_bug


router = APIRouter(
    prefix="/api/bug-reports",
    tags=["Bug Investigator"]
)


# Generate a bug report from a failed test result
@router.post(
    "/investigate/{test_result_id}",
    response_model=BugReportResponse
)
def investigate_test_failure(
    test_result_id: int,
    db: Session = Depends(get_db)
):

    test_result = db.query(TestResult).filter(
        TestResult.id == test_result_id
    ).first()

    if not test_result:
        raise HTTPException(
            status_code=404,
            detail="Test result not found"
        )


    if test_result.status.lower() != "failed":
        raise HTTPException(
            status_code=400,
            detail="Only failed test results can be investigated"
        )

    # Return the existing report instead of creating a duplicate.
    existing_bug = db.query(BugReport).filter(
        BugReport.test_result_id == test_result.id
    ).order_by(BugReport.id.desc()).first()

    if existing_bug:
        return existing_bug

    analysis = investigate_bug(test_result)


    bug_report = BugReport(
        test_result_id=test_result.id,
        title=analysis["title"],
        description=analysis["description"],
        severity=analysis["severity"],
        root_cause=analysis["root_cause"],
        suggested_fix=analysis["suggested_fix"],
        status="open"
    )

    db.add(bug_report)
    db.commit()
    db.refresh(bug_report)

    return bug_report


# Retrieve all bug reports

@router.get("/", response_model=list[BugReportResponse])
def get_bug_reports(
    severity: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(BugReport)

    if severity:
        query = query.filter(
            BugReport.severity == severity.lower()
        )

    if status:
        query = query.filter(
            BugReport.status == status.lower()
        )

    return query.order_by(
        BugReport.id.desc()
    ).all()



# Retrieve bug failure analytics
@router.get("/analytics")
def get_bug_analytics(
    db: Session = Depends(get_db)
):
    bugs = db.query(BugReport).all()

    total = len(bugs)

    # Count bugs by lifecycle status.
    status_counts = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
    }

    # Count bugs by severity.
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    failure_categories = {}
    component_breakdown = {}
    recurring_patterns = {}

    for bug in bugs:
        status = (bug.status or "unknown").strip().lower()
        severity = (bug.severity or "unknown").strip().lower()

        status_counts[status] = status_counts.get(status, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        failure_type = (
            (bug.failure_type or "unknown").strip().lower()
            or "unknown"
        )

        component = (
            (bug.component or "unclassified").strip().lower()
            or "unclassified"
        )

        failure_categories[failure_type] = (
            failure_categories.get(failure_type, 0) + 1
        )

        component_breakdown[component] = (
            component_breakdown.get(component, 0) + 1
        )

        # Identify repeated combinations of failure type,
        # component and bug title.
        title = (bug.title or "Untitled").strip().lower()

        pattern_key = (failure_type, component, title)

        if pattern_key not in recurring_patterns:
            recurring_patterns[pattern_key] = {
                "failure_type": failure_type,
                "component": component,
                "title": title,
                "count": 0,
                "bug_ids": [],
            }

        recurring_patterns[pattern_key]["count"] += 1
        recurring_patterns[pattern_key]["bug_ids"].append(bug.id)

    repeated_failures = [
        pattern
        for pattern in recurring_patterns.values()
        if pattern["count"] > 1
    ]

    repeated_failures.sort(
        key=lambda item: item["count"],
        reverse=True
    )

    return {
        "total_bugs": total,
        "status_breakdown": status_counts,
        "severity_breakdown": severity_counts,
        "failure_categories": [
            {"failure_type": key, "count": value}
            for key, value in sorted(
                failure_categories.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ],
        "component_breakdown": [
            {"component": key, "count": value}
            for key, value in sorted(
                component_breakdown.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ],
        "recurring_failures": repeated_failures,
    }

# Retrieve bug failure analytics
@router.get("/analytics")
def get_bug_analytics(db: Session = Depends(get_db)):

    bugs = db.query(BugReport).all()

    total = len(bugs)

    status_counts = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0
    }

    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    failure_categories = {}
    component_breakdown = {}
    recurring_patterns = {}

    for bug in bugs:

        status = (bug.status or "unknown").strip().lower()
        severity = (bug.severity or "unknown").strip().lower()

        status_counts[status] = status_counts.get(status, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        failure_type = (
            (bug.failure_type or "unknown").strip().lower()
            or "unknown"
        )

        component = (
            (bug.component or "unclassified").strip().lower()
            or "unclassified"
        )

        failure_categories[failure_type] = (
            failure_categories.get(failure_type, 0) + 1
        )

        component_breakdown[component] = (
            component_breakdown.get(component, 0) + 1
        )

        title = (bug.title or "Untitled").strip().lower()

        pattern_key = (failure_type, component, title)

        if pattern_key not in recurring_patterns:
            recurring_patterns[pattern_key] = {
                "failure_type": failure_type,
                "component": component,
                "title": title,
                "count": 0,
                "bug_ids": []
            }

        recurring_patterns[pattern_key]["count"] += 1
        recurring_patterns[pattern_key]["bug_ids"].append(bug.id)

    repeated_failures = [
        pattern
        for pattern in recurring_patterns.values()
        if pattern["count"] > 1
    ]

    repeated_failures.sort(
        key=lambda item: item["count"],
        reverse=True
    )

    return {
        "total_bugs": total,
        "status_breakdown": status_counts,
        "severity_breakdown": severity_counts,

        "failure_categories": [
            {"failure_type": key, "count": value}
            for key, value in sorted(
                failure_categories.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ],

        "component_breakdown": [
            {"component": key, "count": value}
            for key, value in sorted(
                component_breakdown.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ],

        "recurring_failures": repeated_failures
    }


# Retrieve one bug report
@router.get("/{bug_id}", response_model=BugReportResponse)
def get_bug_report(
    bug_id: int,
    db: Session = Depends(get_db)
):

    bug = db.query(BugReport).filter(
        BugReport.id == bug_id
    ).first()

    if not bug:
        raise HTTPException(
            status_code=404,
            detail="Bug report not found"
        )

    return bug


# Update bug report status
@router.patch("/{bug_id}/status")
def update_bug_status(
    bug_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    allowed_statuses = [
        "open",
        "in_progress",
        "resolved"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    bug = db.query(BugReport).filter(
        BugReport.id == bug_id
    ).first()

    if not bug:
        raise HTTPException(
            status_code=404,
            detail="Bug report not found"
        )

    bug.status = status

    db.commit()
    db.refresh(bug)

    return {
        "message": "Bug status updated successfully",
        "bug_id": bug.id,
        "status": bug.status
    }

@router.patch("/{bug_id}/lifecycle", response_model=BugReportResponse)
def update_bug_lifecycle(
    bug_id: int,
    update_data: BugReportLifecycleUpdate,
    db: Session = Depends(get_db)
):
    bug = db.query(BugReport).filter(
        BugReport.id == bug_id
    ).first()

    if not bug:
        raise HTTPException(
            status_code=404,
            detail="Bug report not found"
        )

    allowed_statuses = ["open", "in_progress", "resolved"]

    if update_data.status is not None:
        if update_data.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Allowed: open, in_progress, resolved"
            )

        bug.status = update_data.status

        if update_data.status == "resolved":
            if bug.resolved_at is None:
                bug.resolved_at = datetime.now(timezone.utc)
        else:
            bug.resolved_at = None

    if update_data.resolution_notes is not None:
        bug.resolution_notes = update_data.resolution_notes

    bug.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(bug)

    return bug
