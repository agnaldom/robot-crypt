"""
Reports router for Robot-Crypt API.
"""

from typing import Any, List, Optional
from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user, get_current_active_superuser
from src.database.database import get_database
from src.schemas.report import (
    Report, ReportCreate, ReportUpdate, ReportGeneration,
    ReportTemplate, ReportSummary
)
from src.schemas.user import User
from src.services.report_service import ReportService

router = APIRouter()


@router.get("/", response_model=List[Report])
async def read_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    format: Optional[str] = Query(None, description="Filter by format"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve reports with optional filters.
    """
    report_service = ReportService(db)
    
    # Non-superuser can only see their own reports
    user_id = None if current_user.is_superuser else current_user.id
    
    reports = await report_service.list_reports(
        user_id=user_id,
        report_type=report_type,
        format=format,
        limit=limit,
        offset=skip
    )
    return reports


@router.post("/", response_model=Report)
async def create_report(
    report_in: ReportCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new report.
    """
    report_service = ReportService(db)
    
    # Set user_id to current user
    user_id = current_user.id
    
    report = await report_service.create_report(
        user_id=user_id,
        title=report_in.title,
        report_type=report_in.type,
        format=report_in.format,
        content=report_in.content,
        parameters=report_in.parameters
    )
    return report


@router.post("/generate", response_model=dict)
async def generate_report(
    report_request: ReportGeneration,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a new report with specified parameters.
    """
    report_service = ReportService(db)
    
    # Generate report based on type
    if report_request.report_type == "performance":
        report = await report_service.generate_performance_report(
            user_id=current_user.id,
            title=report_request.title or "Performance Report",
            parameters=report_request.parameters
        )
    elif report_request.report_type == "trade_history":
        start_date = None
        end_date = None
        if report_request.parameters:
            start_date_str = report_request.parameters.get("start_date")
            end_date_str = report_request.parameters.get("end_date")
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        report = await report_service.generate_trade_history_report(
            user_id=current_user.id,
            title=report_request.title or "Trade History Report",
            start_date=start_date,
            end_date=end_date,
            parameters=report_request.parameters
        )
    elif report_request.report_type == "risk_analysis":
        report = await report_service.generate_risk_analysis_report(
            user_id=current_user.id,
            title=report_request.title or "Risk Analysis Report",
            parameters=report_request.parameters
        )
    else:
        # Generic report creation
        report = await report_service.create_report(
            user_id=current_user.id,
            title=report_request.title or f"{report_request.report_type.title()} Report",
            report_type=report_request.report_type,
            format=report_request.format,
            parameters=report_request.parameters
        )
    
    # Save report to file if requested format is not JSON
    file_path = None
    if report_request.format != "json":
        file_path = await report_service.save_report_to_file(report.id, report_request.format)
    
    return {
        "report_id": report.id,
        "status": "generated",
        "type": report.type,
        "format": report.format,
        "title": report.title,
        "generated_at": report.created_at.isoformat(),
        "file_path": file_path,
        "download_url": f"/reports/{report.id}/download",
        "content_length": len(report.content) if report.content else 0
    }


@router.get("/my", response_model=List[Report])
async def read_my_reports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user's reports.
    """
    report_service = ReportService(db)
    reports = await report_service.get_reports_by_user(
        user_id=current_user.id,
        limit=limit
    )
    return reports[skip:skip+limit]


@router.get("/templates", response_model=List[ReportTemplate])
async def get_report_templates(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get available report templates.
    """
    return [
        ReportTemplate(
            name="Performance Summary",
            type="performance",
            description="Comprehensive trading performance analysis",
            default_parameters={
                "period": "monthly",
                "include_charts": True,
                "include_metrics": True
            },
            available_formats=["pdf", "csv", "json"]
        ),
        ReportTemplate(
            name="Trade History",
            type="trade_history", 
            description="Detailed history of all trading activities",
            default_parameters={
                "date_range": "last_30_days",
                "include_fees": True,
                "group_by": "asset"
            },
            available_formats=["csv", "pdf", "json"]
        ),
        ReportTemplate(
            name="Risk Analysis",
            type="risk_analysis",
            description="Risk metrics and exposure analysis",
            default_parameters={
                "include_var": True,
                "include_drawdown": True,
                "confidence_level": 0.95
            },
            available_formats=["pdf", "json"]
        ),
        ReportTemplate(
            name="Portfolio Overview",
            type="portfolio",
            description="Current portfolio allocation and performance",
            default_parameters={
                "include_allocation": True,
                "include_performance": True,
                "benchmark": "BTC"
            },
            available_formats=["pdf", "csv"]
        )
    ]


@router.get("/summary", response_model=ReportSummary)
async def get_reports_summary(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get reports summary and statistics.
    """
    report_service = ReportService(db)
    
    # Get actual statistics
    stats = await report_service.get_report_statistics(current_user.id)
    
    # Get recent reports
    recent_reports = await report_service.get_reports_by_user(
        user_id=current_user.id,
        limit=5
    )
    
    return ReportSummary(
        total_reports=stats["total_reports"],
        reports_by_type=stats["report_types"],
        reports_by_format=stats["formats"],
        recent_reports=[
            {
                "id": report.id,
                "title": report.title,
                "type": report.type,
                "created_at": report.created_at.isoformat()
            }
            for report in recent_reports
        ],
        storage_used=sum(len(r.content or "") for r in recent_reports) / 1024 / 1024  # MB
    )


@router.get("/{report_id}", response_model=Report)
async def read_report(
    report_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get report by ID.
    """
    report_service = ReportService(db)
    report = await report_service.get_report_by_id(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check ownership if not superuser
    if not current_user.is_superuser and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return report


@router.put("/{report_id}", response_model=Report)
async def update_report(
    report_id: int,
    report_in: ReportUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a report.
    """
    report_service = ReportService(db)
    
    # Check if report exists and user has permission
    existing_report = await report_service.get_report_by_id(report_id)
    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.is_superuser and existing_report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    report = await report_service.update_report(
        report_id=report_id,
        title=report_in.title,
        content=report_in.content,
        parameters=report_in.parameters
    )
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.delete("/{report_id}", response_model=Report)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a report.
    """
    report_service = ReportService(db)
    
    # Check if report exists and user has permission
    existing_report = await report_service.get_report_by_id(report_id)
    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.is_superuser and existing_report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await report_service.delete_report(report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return existing_report


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Download a report file.
    """
    report_service = ReportService(db)
    
    # Check if report exists and user has permission
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.is_superuser and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Try to get report content
    content = await report_service.get_report_content(report_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="Report content not found")
    
    # If file exists on disk, return FileResponse
    if report.file_path and os.path.exists(report.file_path):
        return FileResponse(
            path=report.file_path,
            filename=f"{report.title}.{report.format}",
            media_type='application/octet-stream'
        )
    
    # Otherwise, return content as response
    from fastapi.responses import Response
    
    if report.format == "json":
        media_type = "application/json"
    elif report.format == "csv":
        media_type = "text/csv"
    elif report.format == "pdf":
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={report.title}.{report.format}"}
    )


@router.post("/bulk-generate", response_model=dict)
async def bulk_generate_reports(
    report_requests: List[ReportGeneration],
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Generate multiple reports in bulk (admin only).
    """
    report_service = ReportService(db)
    
    generated_reports = []
    failed_reports = []
    
    for i, request in enumerate(report_requests):
        try:
            # Generate each report
            if request.report_type == "performance":
                report = await report_service.generate_performance_report(
                    user_id=current_user.id,
                    title=request.title or f"Bulk Performance Report {i+1}",
                    parameters=request.parameters
                )
            elif request.report_type == "trade_history":
                report = await report_service.generate_trade_history_report(
                    user_id=current_user.id,
                    title=request.title or f"Bulk Trade History Report {i+1}",
                    parameters=request.parameters
                )
            elif request.report_type == "risk_analysis":
                report = await report_service.generate_risk_analysis_report(
                    user_id=current_user.id,
                    title=request.title or f"Bulk Risk Analysis Report {i+1}",
                    parameters=request.parameters
                )
            else:
                report = await report_service.create_report(
                    user_id=current_user.id,
                    title=request.title or f"Bulk {request.report_type.title()} Report {i+1}",
                    report_type=request.report_type,
                    format=request.format,
                    parameters=request.parameters
                )
            
            generated_reports.append({
                "report_id": report.id,
                "title": report.title,
                "type": report.type,
                "status": "generated"
            })
            
        except Exception as e:
            failed_reports.append({
                "index": i,
                "title": request.title or f"Report {i+1}",
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "status": "completed",
        "total_requested": len(report_requests),
        "successful": len(generated_reports),
        "failed": len(failed_reports),
        "generated_reports": generated_reports,
        "failed_reports": failed_reports,
        "completed_at": datetime.now().isoformat()
    }


@router.get("/types/available")
async def get_available_report_types(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get available report types and their configurations.
    """
    return {
        "report_types": [
            {
                "type": "performance",
                "name": "Performance Report",
                "description": "Trading performance analysis with metrics and charts",
                "required_parameters": ["period"],
                "optional_parameters": ["assets", "include_charts", "benchmark"],
                "supported_formats": ["pdf", "csv", "json"],
                "estimated_generation_time": "30-60 seconds"
            },
            {
                "type": "trade_history",
                "name": "Trade History Report",
                "description": "Detailed record of all trading activities",
                "required_parameters": ["date_from", "date_to"],
                "optional_parameters": ["assets", "trade_type", "status"],
                "supported_formats": ["csv", "pdf", "json"],
                "estimated_generation_time": "15-30 seconds"
            },
            {
                "type": "risk_analysis",
                "name": "Risk Analysis Report",
                "description": "Comprehensive risk assessment and metrics",
                "required_parameters": ["period"],
                "optional_parameters": ["confidence_level", "include_var", "include_stress_test"],
                "supported_formats": ["pdf", "json"],
                "estimated_generation_time": "45-90 seconds"
            },
            {
                "type": "portfolio",
                "name": "Portfolio Report",
                "description": "Current portfolio status and allocation analysis",
                "required_parameters": [],
                "optional_parameters": ["benchmark", "include_allocation", "include_history"],
                "supported_formats": ["pdf", "csv"],
                "estimated_generation_time": "20-40 seconds"
            },
            {
                "type": "regulatory",
                "name": "Regulatory Report",
                "description": "Tax and regulatory compliance report",
                "required_parameters": ["tax_year"],
                "optional_parameters": ["jurisdiction", "include_fees"],
                "supported_formats": ["pdf", "csv"],
                "estimated_generation_time": "60-120 seconds"
            }
        ]
    }
