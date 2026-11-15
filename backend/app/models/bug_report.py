
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)

    test_result_id = Column(
        Integer,
        ForeignKey("test_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic bug information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="medium", nullable=False)
    status = Column(String(20), default="open", nullable=False)

    # Investigation information
    root_cause = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    failure_type = Column(
        String(40),
        default="unknown",
        server_default="unknown",
        nullable=False
    )
    component = Column(String(80), nullable=True)
    reproduction_steps = Column(Text, nullable=True)

    # Resolution information
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
