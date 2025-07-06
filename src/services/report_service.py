from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import json
import os
from pathlib import Path

from src.models.report import Report
from src.models.user import User


class ReportService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.reports_directory = Path("reports")
        self.reports_directory.mkdir(exist_ok=True)

    # Basic CRUD operations
    async def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """Get report by ID"""
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()

    async def get_reports_by_user(
        self, 
        user_id: int,
        report_type: Optional[str] = None,
        format: Optional[str] = None,
        limit: int = 50
    ) -> List[Report]:
        """Get reports for a specific user with optional filters"""
        conditions = [Report.user_id == user_id]
        
        if report_type:
            conditions.append(Report.type == report_type)
        
        if format:
            conditions.append(Report.format == format)
        
        query = select(Report).where(and_(*conditions)).order_by(Report.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_reports(
        self,
        user_id: Optional[int] = None,
        report_type: Optional[str] = None,
        format: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Report]:
        """List reports with various filters"""
        conditions = []
        
        if user_id:
            conditions.append(Report.user_id == user_id)
        
        if report_type:
            conditions.append(Report.type == report_type)
        
        if format:
            conditions.append(Report.format == format)
        
        query = select(Report)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Report.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_report(
        self,
        user_id: int,
        title: str,
        report_type: str,
        format: str = "json",
        content: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Create a new report"""
        report = Report(
            user_id=user_id,
            title=title,
            type=report_type,
            format=format,
            content=content,
            parameters=parameters or {}
        )
        
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        
        return report

    async def update_report(
        self,
        report_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Report]:
        """Update an existing report"""
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        if title is not None:
            report.title = title
        
        if content is not None:
            report.content = content
        
        if parameters is not None:
            report.parameters = parameters
        
        await self.db.commit()
        await self.db.refresh(report)
        
        return report

    async def delete_report(self, report_id: int) -> bool:
        """Delete a report"""
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        
        if not report:
            return False
        
        # Delete file if it exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError:
                pass  # File might be already deleted or inaccessible
        
        await self.db.delete(report)
        await self.db.commit()
        
        return True

    # Report generation methods
    async def generate_performance_report(
        self,
        user_id: int,
        title: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Generate a performance report for a user"""
        report_data = {
            "user_id": user_id,
            "report_type": "performance",
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": parameters or {},
            "data": {
                "portfolio_value": 0.0,
                "total_return": 0.0,
                "daily_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "positions": [],
                "transactions": []
            }
        }
        
        content = json.dumps(report_data, indent=2)
        
        report = await self.create_report(
            user_id=user_id,
            title=title,
            report_type="performance",
            format="json",
            content=content,
            parameters=parameters
        )
        
        return report

    async def generate_trade_history_report(
        self,
        user_id: int,
        title: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Generate a trade history report"""
        
        # Build parameters for date filtering
        report_params = parameters or {}
        if start_date:
            report_params["start_date"] = start_date.isoformat()
        if end_date:
            report_params["end_date"] = end_date.isoformat()
        
        report_data = {
            "user_id": user_id,
            "report_type": "trade_history",
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": report_params,
            "data": {
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "summary": {
                    "total_trades": 0,
                    "profitable_trades": 0,
                    "losing_trades": 0,
                    "total_volume": 0.0,
                    "total_profit_loss": 0.0,
                    "win_rate": 0.0
                },
                "trades": []
            }
        }
        
        content = json.dumps(report_data, indent=2)
        
        report = await self.create_report(
            user_id=user_id,
            title=title,
            report_type="trade_history",
            format="json",
            content=content,
            parameters=report_params
        )
        
        return report

    async def generate_risk_analysis_report(
        self,
        user_id: int,
        title: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Generate a risk analysis report"""
        
        report_data = {
            "user_id": user_id,
            "report_type": "risk_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": parameters or {},
            "data": {
                "risk_metrics": {
                    "value_at_risk": 0.0,
                    "conditional_var": 0.0,
                    "beta": 0.0,
                    "correlation_matrix": {},
                    "concentration_risk": 0.0,
                    "liquidity_risk": 0.0
                },
                "portfolio_composition": {
                    "asset_allocation": {},
                    "sector_allocation": {},
                    "geographic_allocation": {}
                },
                "stress_test_results": {
                    "scenarios": [],
                    "results": []
                }
            }
        }
        
        content = json.dumps(report_data, indent=2)
        
        report = await self.create_report(
            user_id=user_id,
            title=title,
            report_type="risk_analysis",
            format="json",
            content=content,
            parameters=parameters
        )
        
        return report

    async def save_report_to_file(self, report_id: int, format: str = None) -> Optional[str]:
        """Save report content to file and update file_path"""
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        
        if not report or not report.content:
            return None
        
        # Determine file format
        file_format = format or report.format
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.id}_{timestamp}.{file_format}"
        file_path = self.reports_directory / filename
        
        try:
            with open(file_path, 'w') as f:
                f.write(report.content)
            
            # Update report with file path
            report.file_path = str(file_path)
            await self.db.commit()
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error saving report to file: {e}")
            return None

    async def get_report_content(self, report_id: int) -> Optional[str]:
        """Get report content, either from database or file"""
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        # Try to get content from database first
        if report.content:
            return report.content
        
        # If not in database, try to read from file
        if report.file_path and os.path.exists(report.file_path):
            try:
                with open(report.file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading report file: {e}")
                return None
        
        return None

    async def get_report_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get report statistics for a user"""
        # Total reports
        total_result = await self.db.execute(
            select(Report).where(Report.user_id == user_id)
        )
        total_reports = len(total_result.scalars().all())
        
        # Count by report type
        types_result = await self.db.execute(
            select(Report.type).where(Report.user_id == user_id).distinct()
        )
        report_types = types_result.scalars().all()
        
        type_counts = {}
        for report_type in report_types:
            type_result = await self.db.execute(
                select(Report).where(and_(Report.user_id == user_id, Report.type == report_type))
            )
            type_counts[report_type] = len(type_result.scalars().all())
        
        # Count by format
        formats_result = await self.db.execute(
            select(Report.format).where(Report.user_id == user_id).distinct()
        )
        formats = formats_result.scalars().all()
        
        format_counts = {}
        for format in formats:
            format_result = await self.db.execute(
                select(Report).where(and_(Report.user_id == user_id, Report.format == format))
            )
            format_counts[format] = len(format_result.scalars().all())
        
        return {
            "total_reports": total_reports,
            "report_types": type_counts,
            "formats": format_counts
        }
