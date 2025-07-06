from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Portfolio Snapshot Schemas
class PortfolioAssetBase(BaseModel):
    asset_id: int
    symbol: str
    quantity: float
    avg_buy_price: float
    current_price: float
    invested_value: float
    current_value: float
    profit_loss: float
    profit_loss_percentage: float
    allocation_percentage: float
    is_active: bool = True


class PortfolioAssetCreate(PortfolioAssetBase):
    pass


class PortfolioAssetUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_buy_price: Optional[float] = None
    current_price: Optional[float] = None
    invested_value: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    allocation_percentage: Optional[float] = None
    is_active: Optional[bool] = None


class PortfolioAssetInDB(PortfolioAssetBase):
    id: int
    snapshot_id: int
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# Portfolio Snapshot Schemas
class PortfolioSnapshotBase(BaseModel):
    user_id: int
    total_invested_value: float
    current_market_value: float
    total_profit_loss: float
    profit_loss_percentage: float
    risk_level: Optional[str] = None
    value_at_risk: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    btc_comparison: Optional[float] = None
    eth_comparison: Optional[float] = None
    metrics: Dict[str, Any] = {}


class PortfolioSnapshotCreate(PortfolioSnapshotBase):
    assets: List[PortfolioAssetCreate] = []


class PortfolioSnapshotUpdate(BaseModel):
    total_invested_value: Optional[float] = None
    current_market_value: Optional[float] = None
    total_profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    risk_level: Optional[str] = None
    value_at_risk: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    btc_comparison: Optional[float] = None
    eth_comparison: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class PortfolioSnapshotInDB(PortfolioSnapshotBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PortfolioSnapshotWithAssets(PortfolioSnapshotInDB):
    assets: List[PortfolioAssetInDB] = []


# Portfolio Transaction Schemas
class PortfolioTransactionBase(BaseModel):
    user_id: int
    asset_id: int
    transaction_type: str
    quantity: float
    price: float
    total_value: float
    fee: float = 0.0
    realized_profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    external_id: Optional[str] = None
    external_source: Optional[str] = None
    executed_at: datetime
    
    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v):
        if v not in ["buy", "sell"]:
            raise ValueError("Transaction type must be 'buy' or 'sell'")
        return v


class PortfolioTransactionCreate(PortfolioTransactionBase):
    pass


class PortfolioTransactionUpdate(BaseModel):
    quantity: Optional[float] = None
    price: Optional[float] = None
    total_value: Optional[float] = None
    fee: Optional[float] = None
    realized_profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    external_id: Optional[str] = None
    external_source: Optional[str] = None
    executed_at: Optional[datetime] = None


class PortfolioTransactionInDB(PortfolioTransactionBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Portfolio Metric Schemas
class PortfolioMetricBase(BaseModel):
    user_id: int
    period_type: str
    period_start: datetime
    period_end: datetime
    starting_value: float
    ending_value: float
    absolute_return: float
    percentage_return: float
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    value_at_risk: Optional[float] = None
    btc_return: Optional[float] = None
    eth_return: Optional[float] = None
    market_return: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    win_rate: Optional[float] = None
    additional_metrics: Dict[str, Any] = {}
    
    @field_validator("period_type")
    @classmethod
    def validate_period_type(cls, v):
        valid_types = ["daily", "weekly", "monthly", "yearly", "all_time"]
        if v not in valid_types:
            raise ValueError(f"Period type must be one of {valid_types}")
        return v


class PortfolioMetricCreate(PortfolioMetricBase):
    pass


class PortfolioMetricUpdate(BaseModel):
    period_type: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    starting_value: Optional[float] = None
    ending_value: Optional[float] = None
    absolute_return: Optional[float] = None
    percentage_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    value_at_risk: Optional[float] = None
    btc_return: Optional[float] = None
    eth_return: Optional[float] = None
    market_return: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    win_rate: Optional[float] = None
    additional_metrics: Optional[Dict[str, Any]] = None


class PortfolioMetricInDB(PortfolioMetricBase):
    id: int
    calculated_at: datetime
    
    model_config = ConfigDict(
        from_attributes = True
    )

# Portfolio Alert Schemas
class PortfolioAlertBase(BaseModel):
    user_id: int
    asset_id: Optional[int] = None
    alert_type: str
    alert_level: str
    condition_type: str
    threshold_value: float
    current_value: Optional[float] = None
    title: str
    message: str
    is_active: bool = True
    is_triggered: bool = False
    notify_email: bool = True
    notify_push: bool = True
    notify_in_app: bool = True
    recurrence: Optional[str] = None
    cool_down_minutes: int = 0
    additional_config: Dict[str, Any] = {}
    
    @validator("alert_type")
    def validate_alert_type(cls, v):
        valid_types = ["price", "value", "percentage", "risk"]
        if v not in valid_types:
            raise ValueError(f"Alert type must be one of {valid_types}")
        return v
    
    @validator("alert_level")
    def validate_alert_level(cls, v):
        valid_levels = ["info", "warning", "danger"]
        if v not in valid_levels:
            raise ValueError(f"Alert level must be one of {valid_levels}")
        return v
    
    @validator("condition_type")
    def validate_condition_type(cls, v):
        valid_conditions = ["above", "below", "equals"]
        if v not in valid_conditions:
            raise ValueError(f"Condition type must be one of {valid_conditions}")
        return v


class PortfolioAlertCreate(PortfolioAlertBase):
    pass


class PortfolioAlertUpdate(BaseModel):
    asset_id: Optional[int] = None
    alert_type: Optional[str] = None
    alert_level: Optional[str] = None
    condition_type: Optional[str] = None
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    title: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None
    is_triggered: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None
    notify_in_app: Optional[bool] = None
    recurrence: Optional[str] = None
    cool_down_minutes: Optional[int] = None
    additional_config: Optional[Dict[str, Any]] = None


class PortfolioAlertInDB(PortfolioAlertBase):
    id: int
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes = True
    )

# Portfolio Projection Schemas
class PortfolioProjectionBase(BaseModel):
    user_id: int
    scenario_type: str
    time_horizon: int
    time_unit: str
    initial_value: float
    expected_return_rate: float
    volatility: float
    recurring_investment: Optional[float] = None
    recurring_frequency: Optional[str] = None
    withdrawal_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
    projected_value: float
    best_case_value: Optional[float] = None
    worst_case_value: Optional[float] = None
    projection_data: Dict[str, Any]
    title: str
    description: Optional[str] = None
    
    @validator("scenario_type")
    def validate_scenario_type(cls, v):
        valid_types = ["optimistic", "pessimistic", "realistic", "custom"]
        if v not in valid_types:
            raise ValueError(f"Scenario type must be one of {valid_types}")
        return v
    
    @validator("time_unit")
    def validate_time_unit(cls, v):
        valid_units = ["days", "months", "years"]
        if v not in valid_units:
            raise ValueError(f"Time unit must be one of {valid_units}")
        return v


class PortfolioProjectionCreate(PortfolioProjectionBase):
    pass


class PortfolioProjectionUpdate(BaseModel):
    scenario_type: Optional[str] = None
    time_horizon: Optional[int] = None
    time_unit: Optional[str] = None
    initial_value: Optional[float] = None
    expected_return_rate: Optional[float] = None
    volatility: Optional[float] = None
    recurring_investment: Optional[float] = None
    recurring_frequency: Optional[str] = None
    withdrawal_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
    projected_value: Optional[float] = None
    best_case_value: Optional[float] = None
    worst_case_value: Optional[float] = None
    projection_data: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    description: Optional[str] = None


class PortfolioProjectionInDB(PortfolioProjectionBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes = True
    )

# Portfolio Report Schemas
class PortfolioReportBase(BaseModel):
    user_id: int
    title: str
    report_type: str
    format: str
    period_type: str
    period_start: datetime
    period_end: datetime
    file_path: Optional[str] = None
    content: Optional[str] = None
    parameters: Dict[str, Any] = {}
    is_scheduled: bool = False
    schedule_frequency: Optional[str] = None
    
    @validator("report_type")
    def validate_report_type(cls, v):
        valid_types = ["summary", "performance", "transactions", "tax", "custom"]
        if v not in valid_types:
            raise ValueError(f"Report type must be one of {valid_types}")
        return v
    
    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["pdf", "csv", "json"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v
    
    @validator("period_type")
    def validate_period_type(cls, v):
        valid_types = ["daily", "weekly", "monthly", "quarterly", "yearly", "custom"]
        if v not in valid_types:
            raise ValueError(f"Period type must be one of {valid_types}")
        return v


class PortfolioReportCreate(PortfolioReportBase):
    pass


class PortfolioReportUpdate(BaseModel):
    title: Optional[str] = None
    report_type: Optional[str] = None
    format: Optional[str] = None
    period_type: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_scheduled: Optional[bool] = None
    schedule_frequency: Optional[str] = None


class PortfolioReportInDB(PortfolioReportBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes = True
    )