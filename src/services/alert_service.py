from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from src.models.alert import Alert
from src.models.asset import Asset
from src.models.user import User


class AlertService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # Basic CRUD operations
    async def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def get_alerts_by_user(
        self, 
        user_id: int,
        active_only: bool = True,
        triggered_only: bool = False,
        alert_type: Optional[str] = None
    ) -> List[Alert]:
        """Get alerts for a specific user with optional filters"""
        conditions = [Alert.user_id == user_id]
        
        if active_only:
            conditions.append(Alert.is_active == True)
        
        if triggered_only:
            conditions.append(Alert.is_triggered == True)
        
        if alert_type:
            conditions.append(Alert.alert_type == alert_type)
        
        query = select(Alert).where(and_(*conditions)).order_by(Alert.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

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
        conditions = []
        
        if user_id:
            conditions.append(Alert.user_id == user_id)
        
        if asset_id:
            conditions.append(Alert.asset_id == asset_id)
        
        if alert_type:
            conditions.append(Alert.alert_type == alert_type)
        
        if is_active is not None:
            conditions.append(Alert.is_active == is_active)
        
        if is_triggered is not None:
            conditions.append(Alert.is_triggered == is_triggered)
        
        query = select(Alert)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

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
        await self.db.commit()
        await self.db.refresh(alert)
        
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
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        
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
        
        await self.db.commit()
        await self.db.refresh(alert)
        
        return alert

    async def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        
        if not alert:
            return False
        
        await self.db.delete(alert)
        await self.db.commit()
        
        return True

    async def trigger_alert(self, alert_id: int, triggered_at: Optional[datetime] = None) -> Optional[Alert]:
        """Mark an alert as triggered"""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        alert.is_triggered = True
        alert.triggered_at = triggered_at or datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(alert)
        
        return alert

    async def get_triggered_alerts_for_notification(self, user_id: Optional[int] = None) -> List[Alert]:
        """Get recently triggered alerts that need notification"""
        conditions = [
            Alert.is_triggered == True,
            Alert.triggered_at.isnot(None)
        ]
        
        if user_id:
            conditions.append(Alert.user_id == user_id)
        
        query = select(Alert).where(and_(*conditions)).order_by(Alert.triggered_at.desc()).limit(50)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_alert_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get alert statistics for a user"""
        # Total alerts
        total_result = await self.db.execute(
            select(Alert).where(Alert.user_id == user_id)
        )
        total_alerts = len(total_result.scalars().all())
        
        # Active alerts
        active_result = await self.db.execute(
            select(Alert).where(and_(Alert.user_id == user_id, Alert.is_active == True))
        )
        active_alerts = len(active_result.scalars().all())
        
        # Triggered alerts
        triggered_result = await self.db.execute(
            select(Alert).where(and_(Alert.user_id == user_id, Alert.is_triggered == True))
        )
        triggered_alerts = len(triggered_result.scalars().all())
        
        # Count by alert type
        types_result = await self.db.execute(
            select(Alert.alert_type).where(Alert.user_id == user_id).distinct()
        )
        alert_types = types_result.scalars().all()
        
        type_counts = {}
        for alert_type in alert_types:
            type_result = await self.db.execute(
                select(Alert).where(and_(Alert.user_id == user_id, Alert.alert_type == alert_type))
            )
            type_counts[alert_type] = len(type_result.scalars().all())
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "triggered_alerts": triggered_alerts,
            "alert_types": type_counts
        }
