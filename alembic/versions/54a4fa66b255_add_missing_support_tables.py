"""add_missing_support_tables

Revision ID: 54a4fa66b255
Revises: 5dd05cdf0956
Create Date: 2025-07-08 00:41:03.852602

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54a4fa66b255'
down_revision = '5dd05cdf0956'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing support tables that the application needs
    
    # Notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('telegram_sent', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_notifications_id', 'id')
    )
    
    # Transaction history table
    op.create_table('transaction_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('operation_type', sa.String(length=10), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('profit_loss', sa.Float(), nullable=True),
        sa.Column('profit_loss_percentage', sa.Float(), nullable=True),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('strategy_used', sa.String(length=50), nullable=False),
        sa.Column('strategy_type', sa.String(length=20), nullable=True),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('fees', sa.Float(), nullable=True),
        sa.Column('balance_before', sa.Float(), nullable=True),
        sa.Column('balance_after', sa.Float(), nullable=True),
        sa.Column('trade_notes', sa.Text(), nullable=True),
        sa.Column('risk_percentage', sa.Float(), nullable=True),
        sa.Column('market_condition', sa.String(length=50), nullable=True),
        sa.Column('indicators_at_entry', sa.JSON(), nullable=True),
        sa.Column('indicators_at_exit', sa.JSON(), nullable=True),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Daily performance table
    op.create_table('daily_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('starting_balance', sa.Float(), nullable=False),
        sa.Column('ending_balance', sa.Float(), nullable=False),
        sa.Column('total_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('winning_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('losing_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('profit_loss', sa.Float(), server_default='0', nullable=False),
        sa.Column('profit_loss_percentage', sa.Float(), server_default='0', nullable=False),
        sa.Column('largest_win', sa.Float(), nullable=True),
        sa.Column('largest_loss', sa.Float(), nullable=True),
        sa.Column('avg_win', sa.Float(), nullable=True),
        sa.Column('avg_loss', sa.Float(), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('avg_profit_per_trade', sa.Float(), nullable=True),
        sa.Column('avg_loss_per_trade', sa.Float(), nullable=True),
        sa.Column('drawdown', sa.Float(), nullable=True),
        sa.Column('metrics_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    
    # Performance metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('winning_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('losing_trades', sa.Integer(), server_default='0', nullable=False),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('final_capital', sa.Float(), nullable=False),
        sa.Column('profit_loss', sa.Float(), nullable=False),
        sa.Column('profit_loss_percentage', sa.Float(), nullable=False),
        sa.Column('avg_profit_per_trade', sa.Float(), nullable=True),
        sa.Column('avg_loss_per_trade', sa.Float(), nullable=True),
        sa.Column('profit_factor', sa.Float(), nullable=True),
        sa.Column('max_consecutive_wins', sa.Integer(), nullable=True),
        sa.Column('max_consecutive_losses', sa.Integer(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('max_drawdown_percentage', sa.Float(), nullable=True),
        sa.Column('recovery_factor', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('sortino_ratio', sa.Float(), nullable=True),
        sa.Column('calmar_ratio', sa.Float(), nullable=True),
        sa.Column('avg_trade_duration', sa.Float(), nullable=True),
        sa.Column('best_symbol', sa.String(length=20), nullable=True),
        sa.Column('worst_symbol', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_type', 'start_date', 'end_date')
    )
    
    # App state table
    op.create_table('app_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('state_data', sa.JSON(), nullable=False),
        sa.Column('strategy_type', sa.String(length=50), nullable=True),
        sa.Column('active_pairs', sa.JSON(), nullable=True),
        sa.Column('open_positions', sa.JSON(), nullable=True),
        sa.Column('config_settings', sa.JSON(), nullable=True),
        sa.Column('last_check_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Capital history table
    op.create_table('capital_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('change_amount', sa.Float(), nullable=True),
        sa.Column('change_percentage', sa.Float(), nullable=True),
        sa.Column('trade_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop the support tables in reverse order
    op.drop_table('capital_history')
    op.drop_table('app_state')
    op.drop_table('performance_metrics')
    op.drop_table('daily_performance')
    op.drop_table('transaction_history')
    op.drop_table('notifications')
