
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)

    test_run_id = Column(
        Integer,
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    test_case_id = Column(
        Integer,
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status = Column(String(20), nullable=False)

    actual_result = Column(Text, nullable=True)

    error_message = Column(Text, nullable=True)

    duration_ms = Column(Integer, nullable=True)

    screenshot_path = Column(String(500), nullable=True)

    executed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
