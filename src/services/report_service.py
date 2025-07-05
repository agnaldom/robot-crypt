from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
import os
from pathlib import Path

from src.models.report import Report
from src.models.user import User


class ReportService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.reports_directory = Path("reports")
        self.reports_directory.mkdir(exist_ok=True)

    # Basic CRUD operations
    async def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """Get report by ID"""
        return self.db.query(Report).filter(Report.id == report_id).first()

    async def get_reports_by_user(
        self, 
        user_id: int,
        report_type: Optional[str] = None,
        format: Optional[str] = None,
        limit: int = 50
    ) -> List[Report]:
        """Get reports for a specific user with optional filters"""
        query = self.db.query(Report).filter(Report.user_id == user_id)
        
        if report_type:
            query = query.filter(Report.type == report_type)
        
        if format:
            query = query.filter(Report.format == format)
        
        return query.order_by(Report.created_at.desc()).limit(limit).all()

    async def list_reports(
        self,
        user_id: Optional[int] = None,
        report_type: Optional[str] = None,
        format: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Report]:
        """List reports with various filters"""
        query = self.db.query(Report)
        
        if user_id:
            query = query.filter(Report.user_id == user_id)
        
        if report_type:
            query = query.filter(Report.type == report_type)
        
        if format:
            query = query.filter(Report.format == format)
        
        return query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()

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
        self.db.commit()
        self.db.refresh(report)
        
        return report

    async def update_report(
        self,
        report_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Report]:
        """Update an existing report"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            return None
        
        if title is not None:
            report.title = title
        
        if content is not None:
            report.content = content
        
        if parameters is not None:
            report.parameters = parameters
        
        self.db.commit()
        self.db.refresh(report)
        
        return report

    async def delete_report(self, report_id: int) -> bool:
        """Delete a report"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            return False
        
        # Delete file if it exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError:
                pass  # File might be already deleted or inaccessible
        
        self.db.delete(report)
        self.db.commit()
        
        return True

    # Report generation methods
    async def generate_performance_report(
        self,
        user_id: int,
        title: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Report:
        """Generate a performance report for a user"""
        # This would typically involve complex calculations
        # For now, we'll create a basic structure
        
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
        
        # You would populate this with actual portfolio data
        # from portfolio service, trading records, etc.
        
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
        
        # You would populate this with actual trading data
        # from trading service, transaction records, etc.
        
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
        
        # You would populate this with actual risk calculations
        # from portfolio service, market data, etc.
        
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
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
        if not report or not report.content:
            return None
        
        # Determine file format
        file_format = format or report.format
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.id}_{timestamp}.{file_format}"
        file_path = self.reports_directory / filename
        
        try:
            if file_format == "json":
                with open(file_path, 'w') as f:
                    f.write(report.content)
            elif file_format == "csv":
                # Convert JSON content to CSV if needed
                data = json.loads(report.content)
                # This would require more complex CSV conversion logic
                with open(file_path, 'w') as f:
                    f.write(self._convert_to_csv(data))
            elif file_format == "pdf":
                # This would require PDF generation logic
                # For now, save as text
                with open(file_path, 'w') as f:
                    f.write(report.content)
            
            # Update report with file path
            report.file_path = str(file_path)
            self.db.commit()
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error saving report to file: {e}")
            return None

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert JSON data to CSV format (basic implementation)"""
        # This is a simplified CSV conversion
        # In practice, you'd want more sophisticated conversion logic
        import csv
        import io
        
        output = io.StringIO()
        
        if "data" in data and isinstance(data["data"], dict):
            # Extract tabular data from the report
            for key, value in data["data"].items():
                if isinstance(value, list) and value:
                    # Write section header
                    output.write(f"\n{key.upper()}\n")
                    
                    # Write CSV data
                    if isinstance(value[0], dict):
                        fieldnames = value[0].keys()
                        writer = csv.DictWriter(output, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(value)
                    else:
                        # Simple list
                        for item in value:
                            output.write(f"{item}\n")
                    
                    output.write("\n")
        
        return output.getvalue()

    async def get_report_content(self, report_id: int) -> Optional[str]:
        """Get report content, either from database or file"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
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
        total_reports = self.db.query(Report).filter(Report.user_id == user_id).count()
        
        # Count by report type
        report_types = self.db.query(Report.type).filter(Report.user_id == user_id).distinct().all()
        type_counts = {}
        for (report_type,) in report_types:
            count = self.db.query(Report).filter(
                and_(Report.user_id == user_id, Report.type == report_type)
            ).count()
            type_counts[report_type] = count
        
        # Count by format
        formats = self.db.query(Report.format).filter(Report.user_id == user_id).distinct().all()
        format_counts = {}
        for (format,) in formats:
            count = self.db.query(Report).filter(
                and_(Report.user_id == user_id, Report.format == format)
            ).count()
            format_counts[format] = count
        
        return {
            "total_reports": total_reports,
            "report_types": type_counts,
            "formats": format_counts
        }

    async def cleanup_old_reports(self, days_old: int = 30) -> int:
        """Delete reports older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_reports = self.db.query(Report).filter(
            Report.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for report in old_reports:
            if await self.delete_report(report.id):
                deleted_count += 1
        
        return deleted_count

    async def bulk_export_reports(
        self,
        user_id: int,
        format: str = "json",
        report_type: Optional[str] = None
    ) -> Optional[str]:
        """Export multiple reports to a single file"""
        reports = await self.get_reports_by_user(
            user_id=user_id,
            report_type=report_type,
            limit=1000
        )
        
        if not reports:
            return None
        
        # Create export data
        export_data = {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "report_type": report_type,
            "total_reports": len(reports),
            "reports": []
        }
        
        for report in reports:
            report_data = {
                "id": report.id,
                "title": report.title,
                "type": report.type,
                "format": report.format,
                "created_at": report.created_at.isoformat(),
                "parameters": report.parameters,
                "content": report.content
            }
            export_data["reports"].append(report_data)
        
        # Save to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_export_{user_id}_{timestamp}.{format}"
        file_path = self.reports_directory / filename
        
        try:
            if format == "json":
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            elif format == "csv":
                with open(file_path, 'w') as f:
                    f.write(self._convert_to_csv(export_data))
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error exporting reports: {e}")
            return None
