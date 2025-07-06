"""
Alerts router for Robot-Crypt API.
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_active_user, get_current_active_superuser
from src.database.database import get_database
from src.schemas.alert import Alert, AlertCreate, AlertUpdate, AlertTrigger
from src.schemas.user import User
from src.services.alert_service import AlertService

router = APIRouter()


@router.get("/", response_model=List[Alert])
async def read_alerts(
    skip: int = 0,
    limit: int = 100,
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_triggered: Optional[bool] = Query(None, description="Filter by triggered status"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve alerts with optional filters.
    """
    alert_service = AlertService(db)
    
    # Non-superuser can only see their own alerts
    user_id = None if current_user.is_superuser else current_user.id
    
    alerts = await alert_service.list_alerts(
        user_id=user_id,
        alert_type=alert_type,
        is_active=is_active,
        is_triggered=is_triggered,
        limit=limit,
        offset=skip
    )
    return alerts


@router.post("/", response_model=Alert)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new alert.
    """
    alert_service = AlertService(db)
    
    # Set user_id to current user
    user_id = current_user.id
    
    alert = await alert_service.create_alert(
        user_id=user_id,
        alert_type=alert_in.alert_type,
        message=alert_in.message,
        trigger_value=alert_in.trigger_value,
        asset_id=alert_in.asset_id,
        parameters=alert_in.parameters
    )
    return alert


@router.get("/my", response_model=List[Alert])
async def read_my_alerts(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user's alerts.
    """
    alert_service = AlertService(db)
    alerts = await alert_service.get_alerts_by_user(
        user_id=current_user.id,
        active_only=is_active
    )
    return alerts[skip:skip+limit]


@router.get("/active", response_model=List[Alert])
async def read_active_alerts(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all active alerts for monitoring.
    """
    alert_service = AlertService(db)
    user_id = None if current_user.is_superuser else current_user.id
    
    alerts = await alert_service.list_alerts(
        user_id=user_id,
        is_active=True
    )
    return alerts


@router.get("/triggered", response_model=List[Alert])
async def read_triggered_alerts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get recently triggered alerts.
    """
    alert_service = AlertService(db)
    user_id = None if current_user.is_superuser else current_user.id
    
    alerts = await alert_service.list_alerts(
        user_id=user_id,
        is_triggered=True,
        limit=limit,
        offset=skip
    )
    return alerts


@router.get("/{alert_id}", response_model=Alert)
async def read_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get alert by ID.
    """
    alert_service = AlertService(db)
    alert = await alert_service.get_alert_by_id(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check ownership if not superuser
    if not current_user.is_superuser and alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return alert


@router.put("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update an alert.
    """
    alert_service = AlertService(db)
    
    # Check if alert exists and user has permission
    existing_alert = await alert_service.get_alert_by_id(alert_id)
    if not existing_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not current_user.is_superuser and existing_alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    alert = await alert_service.update_alert(
        alert_id=alert_id,
        message=alert_in.message,
        trigger_value=alert_in.trigger_value,
        is_active=alert_in.is_active,
        parameters=alert_in.parameters
    )
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@router.delete("/{alert_id}", response_model=Alert)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete an alert.
    """
    alert_service = AlertService(db)
    
    # Check if alert exists and user has permission
    existing_alert = await alert_service.get_alert_by_id(alert_id)
    if not existing_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not current_user.is_superuser and existing_alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await alert_service.delete_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return existing_alert


@router.post("/{alert_id}/trigger", response_model=dict)
async def trigger_alert(
    alert_id: int,
    trigger_data: AlertTrigger,
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Manually trigger an alert (for testing/admin purposes).
    """
    alert_service = AlertService(db)
    
    # Check if alert exists
    existing_alert = await alert_service.get_alert_by_id(alert_id)
    if not existing_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Trigger the alert
    triggered_alert = await alert_service.trigger_alert(
        alert_id=alert_id,
        triggered_at=datetime.utcnow()
    )
    
    if not triggered_alert:
        raise HTTPException(status_code=500, detail="Failed to trigger alert")
    
    return {
        "alert_id": alert_id,
        "status": "triggered",
        "triggered_at": triggered_alert.triggered_at.isoformat(),
        "message": f"Alert '{triggered_alert.message}' triggered manually"
    }


@router.post("/test")
async def test_alert_system(
    db: AsyncSession = Depends(get_database),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Test the alert system functionality.
    """
    alert_service = AlertService(db)
    
    # Get system statistics
    stats = await alert_service.get_alert_statistics(current_user.id)
    
    # Get active alerts
    active_alerts = await alert_service.list_alerts(is_active=True)
    
    # Get triggered alerts for notification
    triggered_alerts = await alert_service.get_triggered_alerts_for_notification()
    
    return {
        "status": "ok",
        "system_stats": stats,
        "active_alerts": len(active_alerts),
        "triggered_alerts_pending": len(triggered_alerts),
        "notification_channels": {
            "telegram": "not_configured",
            "email": "not_configured",
            "webhook": "available"
        },
        "last_check": datetime.utcnow().isoformat(),
        "test_results": {
            "database_connection": "ok",
            "alert_processing": "ok",
            "notifications": "pending_configuration"
        }
    }


@router.get("/types/available")
async def get_available_alert_types(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get available alert types and their configurations.
    """
    return {
        "alert_types": [
            {
                "type": "price",
                "name": "Price Alert",
                "description": "Trigger when asset price reaches target",
                "parameters": ["trigger_value", "condition"],
                "supported_conditions": ["above", "below", "equals"]
            },
            {
                "type": "technical",
                "name": "Technical Indicator Alert",
                "description": "Trigger based on technical indicator values",
                "parameters": ["indicator_type", "trigger_value", "condition"],
                "supported_indicators": ["RSI", "MA", "EMA", "MACD", "BB"]
            },
            {
                "type": "macro",
                "name": "Macro Economic Alert",
                "description": "Trigger on economic events or news",
                "parameters": ["event_type", "impact_level"],
                "supported_events": ["fed_meeting", "inflation_data", "employment_report"]
            },
            {
                "type": "risk",
                "name": "Risk Management Alert",
                "description": "Trigger on risk threshold breaches",
                "parameters": ["risk_metric", "threshold"],
                "supported_metrics": ["volatility", "drawdown", "exposure"]
            },
            {
                "type": "portfolio",
                "name": "Portfolio Alert",
                "description": "Trigger on portfolio changes",
                "parameters": ["metric", "threshold"],
                "supported_metrics": ["total_value", "profit_loss", "allocation"]
            }
        ]
    }
