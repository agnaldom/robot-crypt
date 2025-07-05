"""
Report schemas for Robot-Crypt API.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    """Base report schema."""
    user_id: int = Field(..., description="User ID")
    title: str = Field(..., description="Report title")
    type: str = Field(..., description="Report type (performance, trade_history, risk_analysis)")
    format: str = Field(..., description="Report format (pdf, csv, json)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Report parameters")


class ReportCreate(ReportBase):
    """Schema for creating a report."""
    pass


class ReportUpdate(BaseModel):
    """Schema for updating a report."""
    title: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Report(ReportBase):
    """Schema for report returned in API responses."""
    id: int
    content: Optional[str]
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportGeneration(BaseModel):
    """Schema for report generation request."""
    report_type: str = Field(..., description="Type of report to generate")
    format: str = Field(default="pdf", description="Output format (pdf, csv, json)")
    title: Optional[str] = Field(None, description="Custom report title")
    date_from: Optional[datetime] = Field(None, description="Start date for data")
    date_to: Optional[datetime] = Field(None, description="End date for data")
    assets: Optional[list] = Field(None, description="Specific assets to include")
    include_charts: bool = Field(True, description="Include charts in report")
    include_summary: bool = Field(True, description="Include summary section")
    custom_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom parameters")


class ReportTemplate(BaseModel):
    """Schema for report template."""
    name: str = Field(..., description="Template name")
    type: str = Field(..., description="Report type")
    description: Optional[str] = Field(None, description="Template description")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    available_formats: list = Field(default=["pdf", "csv"], description="Available output formats")


class ReportSummary(BaseModel):
    """Schema for report summary data."""
    total_reports: int = Field(..., description="Total number of reports")
    reports_by_type: Dict[str, int] = Field(..., description="Reports count by type")
    reports_by_format: Dict[str, int] = Field(..., description="Reports count by format")
    recent_reports: list = Field(..., description="Recent reports list")
    storage_used: Optional[float] = Field(None, description="Storage used in MB")
