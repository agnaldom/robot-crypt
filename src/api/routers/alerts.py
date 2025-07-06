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
from src.ai.smart_alerts import SmartAlertsEngine, create_smart_alerts_engine, AlertCategory, AlertPriority

router = APIRouter()


# Dependency to get Smart Alerts Engine
async def get_smart_alerts_engine() -> SmartAlertsEngine:
    """Get Smart Alerts Engine instance."""
    return await create_smart_alerts_engine()


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


# Smart Alerts Endpoints
@router.get("/smart/categories")
async def get_smart_alert_categories(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get available smart alert categories.
    """
    return {
        "categories": [
            {
                "category": "TECHNICAL",
                "name": "Technical Analysis",
                "description": "AI-powered technical analysis alerts"
            },
            {
                "category": "NEWS",
                "name": "News Sentiment",
                "description": "News sentiment analysis and market impact alerts"
            },
            {
                "category": "RISK",
                "name": "Risk Management",
                "description": "Risk assessment and portfolio protection alerts"
            },
            {
                "category": "ANOMALY",
                "name": "Anomaly Detection",
                "description": "Unusual market behavior and pattern alerts"
            },
            {
                "category": "PORTFOLIO",
                "name": "Portfolio Optimization",
                "description": "Portfolio rebalancing and optimization alerts"
            }
        ],
        "priorities": [
            {
                "priority": "LOW",
                "name": "Low Priority",
                "description": "Information alerts for awareness"
            },
            {
                "priority": "MEDIUM",
                "name": "Medium Priority",
                "description": "Important alerts requiring attention"
            },
            {
                "priority": "HIGH",
                "name": "High Priority",
                "description": "Critical alerts requiring immediate action"
            },
            {
                "priority": "CRITICAL",
                "name": "Critical Priority",
                "description": "Emergency alerts for immediate response"
            }
        ]
    }


@router.post("/smart/generate")
async def generate_smart_alert(
    category: AlertCategory,
    priority: AlertPriority,
    asset_symbol: str,
    smart_alerts_engine: SmartAlertsEngine = Depends(get_smart_alerts_engine),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate a smart alert using AI analysis.
    """
    try:
        alert = await smart_alerts_engine.generate_smart_alert(
            category=category,
            priority=priority,
            asset_symbol=asset_symbol,
            user_id=current_user.id
        )
        
        return {
            "status": "success",
            "alert": {
                "id": alert.id,
                "category": alert.category,
                "priority": alert.priority,
                "title": alert.title,
                "message": alert.message,
                "asset_symbol": alert.asset_symbol,
                "confidence": alert.confidence,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate smart alert: {str(e)}"
        )


@router.post("/smart/analyze")
async def analyze_and_generate_alerts(
    asset_symbol: str,
    analysis_type: str = Query("comprehensive", description="Type of analysis: comprehensive, technical, news, risk"),
    smart_alerts_engine: SmartAlertsEngine = Depends(get_smart_alerts_engine),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Analyze market conditions and generate relevant smart alerts.
    """
    try:
        alerts = await smart_alerts_engine.analyze_and_generate_alerts(
            asset_symbol=asset_symbol,
            user_id=current_user.id,
            analysis_type=analysis_type
        )
        
        return {
            "status": "success",
            "analysis_type": analysis_type,
            "asset_symbol": asset_symbol,
            "alerts_generated": len(alerts),
            "alerts": [
                {
                    "id": alert.id,
                    "category": alert.category,
                    "priority": alert.priority,
                    "title": alert.title,
                    "message": alert.message,
                    "confidence": alert.confidence,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze and generate alerts: {str(e)}"
        )


@router.post("/smart/{alert_id}/send")
async def send_smart_alert_notification(
    alert_id: str,
    notification_channel: str = Query("all", description="Notification channel: telegram, local, or all"),
    smart_alerts_engine: SmartAlertsEngine = Depends(get_smart_alerts_engine),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Send a smart alert notification through specified channels.
    """
    try:
        success = await smart_alerts_engine.send_smart_alert_notification(
            alert_id=alert_id,
            user_id=current_user.id,
            channel=notification_channel
        )
        
        if success:
            return {
                "status": "success",
                "alert_id": alert_id,
                "notification_channel": notification_channel,
                "message": "Smart alert notification sent successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Smart alert not found or notification failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send smart alert notification: {str(e)}"
        )


@router.get("/smart/portfolio-insights")
async def get_portfolio_insights(
    include_recommendations: bool = Query(True, description="Include AI recommendations"),
    smart_alerts_engine: SmartAlertsEngine = Depends(get_smart_alerts_engine),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get AI-powered portfolio insights and recommendations.
    """
    try:
        insights = await smart_alerts_engine.get_portfolio_insights(
            user_id=current_user.id,
            include_recommendations=include_recommendations
        )
        
        return {
            "status": "success",
            "user_id": current_user.id,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio insights: {str(e)}"
        )


@router.get("/smart/market-sentiment")
async def get_market_sentiment_analysis(
    asset_symbol: Optional[str] = Query(None, description="Specific asset symbol for sentiment analysis"),
    smart_alerts_engine: SmartAlertsEngine = Depends(get_smart_alerts_engine),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get AI-powered market sentiment analysis.
    """
    try:
        sentiment_analysis = await smart_alerts_engine.get_market_sentiment_analysis(
            asset_symbol=asset_symbol
        )
        
        return {
            "status": "success",
            "asset_symbol": asset_symbol,
            "sentiment_analysis": sentiment_analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get market sentiment analysis: {str(e)}"
        )

