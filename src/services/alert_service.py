from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.alert import Alert
from src.models.asset import Asset
from src.models.user import User


class AlertService:
    def __init__(self, db_session: Session):
        self.db = db_session

    # Basic CRUD operations
    async def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    async def get_alerts_by_user(
        self, 
        user_id: int,
        active_only: bool = True,
        triggered_only: bool = False,
        alert_type: Optional[str] = None
    ) -> List[Alert]:
        """Get alerts for a specific user with optional filters"""
        query = self.db.query(Alert).filter(Alert.user_id == user_id)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        if triggered_only:
            query = query.filter(Alert.is_triggered == True)
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        return query.order_by(Alert.created_at.desc()).all()

    async def get_alerts_by_asset(
        self, 
        asset_id: int,
        active_only: bool = True
    ) -> List[Alert]:
        """Get all alerts for a specific asset"""
        query = self.db.query(Alert).filter(Alert.asset_id == asset_id)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        return query.order_by(Alert.created_at.desc()).all()

    async def list_alerts(
        self,
        user_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_triggered: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Alert]:
        """List alerts with various filters"""
        query = self.db.query(Alert)
        
        if user_id:
            query = query.filter(Alert.user_id == user_id)
        
        if asset_id:
            query = query.filter(Alert.asset_id == asset_id)
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        if is_active is not None:
            query = query.filter(Alert.is_active == is_active)
        
        if is_triggered is not None:
            query = query.filter(Alert.is_triggered == is_triggered)
        
        return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

    async def create_alert(
        self,
        user_id: int,
        alert_type: str,
        message: str,
        trigger_value: Optional[float] = None,
        asset_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert"""
        alert = Alert(
            user_id=user_id,
            asset_id=asset_id,
            alert_type=alert_type,
            message=message,
            trigger_value=trigger_value,
            is_active=True,
            is_triggered=False,
            parameters=parameters or {}
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    async def update_alert(
        self,
        alert_id: int,
        message: Optional[str] = None,
        trigger_value: Optional[float] = None,
        is_active: Optional[bool] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Update an existing alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        if message is not None:
            alert.message = message
        
        if trigger_value is not None:
            alert.trigger_value = trigger_value
        
        if is_active is not None:
            alert.is_active = is_active
        
        if parameters is not None:
            alert.parameters = parameters
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    async def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return False
        
        self.db.delete(alert)
        self.db.commit()
        
        return True

    # Alert-specific operations
    async def trigger_alert(self, alert_id: int, triggered_at: Optional[datetime] = None) -> Optional[Alert]:
        """Mark an alert as triggered"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.is_triggered = True
        alert.triggered_at = triggered_at or datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    async def deactivate_alert(self, alert_id: int) -> Optional[Alert]:
        """Deactivate an alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.is_active = False
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    async def reactivate_alert(self, alert_id: int) -> Optional[Alert]:
        """Reactivate an alert and reset triggered status"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.is_active = True
        alert.is_triggered = False
        alert.triggered_at = None
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    # Alert processing methods
    async def check_price_alerts(self, asset_id: int, current_price: float) -> List[Alert]:
        """Check and trigger price alerts for an asset"""
        # Get active price alerts for this asset
        alerts = self.db.query(Alert).filter(
            and_(
                Alert.asset_id == asset_id,
                Alert.alert_type == "price",
                Alert.is_active == True,
                Alert.is_triggered == False
            )
        ).all()
        
        triggered_alerts = []
        
        for alert in alerts:
            should_trigger = False
            
            # Check different price alert conditions based on parameters
            if alert.parameters:
                condition = alert.parameters.get("condition", "above")
                
                if condition == "above" and current_price >= alert.trigger_value:
                    should_trigger = True
                elif condition == "below" and current_price <= alert.trigger_value:
                    should_trigger = True
                elif condition == "change_percent":
                    # Check percentage change (requires previous price in parameters)
                    prev_price = alert.parameters.get("reference_price")
                    if prev_price:
                        change_percent = ((current_price - prev_price) / prev_price) * 100
                        if abs(change_percent) >= alert.trigger_value:
                            should_trigger = True
            else:
                # Default condition: trigger if price is above trigger value
                if current_price >= alert.trigger_value:
                    should_trigger = True
            
            if should_trigger:
                triggered_alert = await self.trigger_alert(alert.id)
                if triggered_alert:
                    triggered_alerts.append(triggered_alert)
        
        return triggered_alerts

    async def check_technical_alerts(self, asset_id: int, technical_data: Dict[str, Any]) -> List[Alert]:
        """Check and trigger technical analysis alerts"""
        alerts = self.db.query(Alert).filter(
            and_(
                Alert.asset_id == asset_id,
                Alert.alert_type == "technical",
                Alert.is_active == True,
                Alert.is_triggered == False
            )
        ).all()
        
        triggered_alerts = []
        
        for alert in alerts:
            should_trigger = False
            
            if alert.parameters:
                indicator = alert.parameters.get("indicator")
                condition = alert.parameters.get("condition", "above")
                
                if indicator and indicator in technical_data:
                    indicator_value = technical_data[indicator]
                    
                    if condition == "above" and indicator_value >= alert.trigger_value:
                        should_trigger = True
                    elif condition == "below" and indicator_value <= alert.trigger_value:
                        should_trigger = True
                    elif condition == "crosses_above" and indicator_value > alert.trigger_value:
                        # This would require previous value comparison
                        should_trigger = True
                    elif condition == "crosses_below" and indicator_value < alert.trigger_value:
                        # This would require previous value comparison
                        should_trigger = True
            
            if should_trigger:
                triggered_alert = await self.trigger_alert(alert.id)
                if triggered_alert:
                    triggered_alerts.append(triggered_alert)
        
        return triggered_alerts

    async def check_risk_alerts(self, user_id: int, portfolio_metrics: Dict[str, Any]) -> List[Alert]:
        """Check and trigger risk-based alerts"""
        alerts = self.db.query(Alert).filter(
            and_(
                Alert.user_id == user_id,
                Alert.alert_type == "risk",
                Alert.is_active == True,
                Alert.is_triggered == False
            )
        ).all()
        
        triggered_alerts = []
        
        for alert in alerts:
            should_trigger = False
            
            if alert.parameters:
                risk_metric = alert.parameters.get("risk_metric")
                condition = alert.parameters.get("condition", "above")
                
                if risk_metric and risk_metric in portfolio_metrics:
                    metric_value = portfolio_metrics[risk_metric]
                    
                    if condition == "above" and metric_value >= alert.trigger_value:
                        should_trigger = True
                    elif condition == "below" and metric_value <= alert.trigger_value:
                        should_trigger = True
            
            if should_trigger:
                triggered_alert = await self.trigger_alert(alert.id)
                if triggered_alert:
                    triggered_alerts.append(triggered_alert)
        
        return triggered_alerts

    async def get_triggered_alerts_for_notification(self, user_id: Optional[int] = None) -> List[Alert]:
        """Get recently triggered alerts that need notification"""
        query = self.db.query(Alert).filter(
            and_(
                Alert.is_triggered == True,
                Alert.triggered_at.isnot(None)
            )
        )
        
        if user_id:
            query = query.filter(Alert.user_id == user_id)
        
        # Get alerts triggered in the last hour (or adjust as needed)
        return query.order_by(Alert.triggered_at.desc()).limit(50).all()

    async def bulk_deactivate_alerts(self, user_id: int, asset_id: Optional[int] = None) -> int:
        """Bulk deactivate alerts for a user or specific asset"""
        query = self.db.query(Alert).filter(
            and_(
                Alert.user_id == user_id,
                Alert.is_active == True
            )
        )
        
        if asset_id:
            query = query.filter(Alert.asset_id == asset_id)
        
        updated_count = query.update({Alert.is_active: False})
        self.db.commit()
        
        return updated_count

    async def get_alert_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get alert statistics for a user"""
        total_alerts = self.db.query(Alert).filter(Alert.user_id == user_id).count()
        active_alerts = self.db.query(Alert).filter(
            and_(Alert.user_id == user_id, Alert.is_active == True)
        ).count()
        triggered_alerts = self.db.query(Alert).filter(
            and_(Alert.user_id == user_id, Alert.is_triggered == True)
        ).count()
        
        # Count by alert type
        alert_types = self.db.query(Alert.alert_type).filter(Alert.user_id == user_id).distinct().all()
        type_counts = {}
        for (alert_type,) in alert_types:
            count = self.db.query(Alert).filter(
                and_(Alert.user_id == user_id, Alert.alert_type == alert_type)
            ).count()
            type_counts[alert_type] = count
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "triggered_alerts": triggered_alerts,
            "alert_types": type_counts
        }
