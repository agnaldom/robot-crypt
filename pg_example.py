#!/usr/bin/env python3
"""
Arquivo de exemplo para demonstrar como usar o PostgresManager para
armazenar dados de transações, métricas de performance e estatísticas de trading.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from postgres_manager import PostgresManager

def setup_logging():
    """Configura o sistema de logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("robot-crypt")

def main():
    """Função principal de exemplo"""
    logger = setup_logging()
    logger.info("Iniciando exemplo de uso do PostgresManager")
    
    # Verifica se as variáveis de ambiente necessárias estão configuradas
    if not os.environ.get("POSTGRES_URL") and not os.environ.get("POSTGRES_HOST"):
        logger.error("Variáveis de ambiente para conexão PostgreSQL não configuradas")
        logger.info("Configure POSTGRES_URL ou POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        
        # Usar valores de exemplo para demonstração
        logger.info("Usando valores locais para demonstração")
        os.environ["POSTGRES_HOST"] = "localhost"
        os.environ["POSTGRES_PORT"] = "5432"
        os.environ["POSTGRES_DB"] = "robot_crypt"
        os.environ["POSTGRES_USER"] = "postgres"
        os.environ["POSTGRES_PASSWORD"] = "postgres"
    
    # Inicializa o PostgresManager
    try:
        pg = PostgresManager()
        logger.info("PostgresManager inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar PostgresManager: {str(e)}")
        return
    
    # Exemplo 1: Registrar uma transação de compra
    logger.info("Exemplo 1: Registrando transação de compra")
    buy_data = {
        "symbol": "BTC/USDT",
        "operation_type": "buy",
        "entry_price": 42000.50,
        "quantity": 0.01,
        "entry_time": datetime.now(),
        "strategy_used": "ScalpingStrategy",
        "strategy_type": "Scalping",
        "stop_loss": 41000.00,
        "take_profit": 43000.00,
        "risk_percentage": 1.5,
        "balance_before": 10000.00,
        "indicators_at_entry": {
            "rsi": 42.5,
            "macd": {"histogram": 0.25, "signal": 0.1, "macd": 0.35},
            "ema": {"fast": 42100, "slow": 41900}
        }
    }
    
    buy_tx_id = pg.record_transaction(buy_data)
    
    if buy_tx_id:
        logger.info(f"Transação de compra registrada com ID: {buy_tx_id}")
        
        # Registrar atualização de capital
        capital_id = pg.save_capital_update(
            balance=buy_data["balance_before"] - (buy_data["entry_price"] * buy_data["quantity"]),
            change_amount=-(buy_data["entry_price"] * buy_data["quantity"]),
            change_percentage=-(buy_data["entry_price"] * buy_data["quantity"] / buy_data["balance_before"]) * 100,
            trade_id=buy_tx_id,
            event_type="buy",
            notes=f"Compra de {buy_data['quantity']} BTC a {buy_data['entry_price']} USDT"
        )
        
        logger.info(f"Atualização de capital registrada com ID: {capital_id}")
    else:
        logger.error("Falha ao registrar transação de compra")
    
    # Exemplo 2: Registrar uma transação de venda com lucro
    logger.info("Exemplo 2: Registrando transação de venda com lucro")
    
    # Simulando que passou algum tempo e o preço subiu
    exit_time = datetime.now() + timedelta(hours=2)
    exit_price = 42500.75
    
    # Calculando lucro/prejuízo
    entry_price = buy_data["entry_price"]
    quantity = buy_data["quantity"]
    profit_amount = (exit_price - entry_price) * quantity
    profit_percentage = (exit_price / entry_price - 1) * 100
    balance_before = buy_data["balance_before"] - (entry_price * quantity)
    balance_after = balance_before + (exit_price * quantity)
    
    sell_data = {
        "symbol": "BTC/USDT",
        "operation_type": "sell",
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "profit_loss": profit_amount,
        "profit_loss_percentage": profit_percentage,
        "entry_time": buy_data["entry_time"],
        "exit_time": exit_time,
        "strategy_used": "ScalpingStrategy",
        "strategy_type": "Scalping",
        "balance_before": balance_before,
        "balance_after": balance_after,
        "indicators_at_exit": {
            "rsi": 68.2,
            "macd": {"histogram": 0.45, "signal": 0.2, "macd": 0.65},
            "ema": {"fast": 42600, "slow": 42200}
        }
    }
    
    sell_tx_id = pg.record_transaction(sell_data)
    
    if sell_tx_id:
        logger.info(f"Transação de venda registrada com ID: {sell_tx_id}")
        
        # Registrar atualização de capital
        capital_id = pg.save_capital_update(
            balance=balance_after,
            change_amount=profit_amount,
            change_percentage=profit_percentage,
            trade_id=sell_tx_id,
            event_type="sell",
            notes=f"Venda de {quantity} BTC a {exit_price} USDT com lucro de {profit_percentage:.2f}%"
        )
        
        logger.info(f"Atualização de capital registrada com ID: {capital_id}")
    else:
        logger.error("Falha ao registrar transação de venda")
    
    # Exemplo 3: Recuperar histórico de transações
    logger.info("Exemplo 3: Recuperando histórico de transações")
    transactions = pg.get_transaction_history(symbol="BTC/USDT", limit=10)
    
    if transactions:
        logger.info(f"Recuperadas {len(transactions)} transações")
        for tx in transactions:
            op_type = tx['operation_type'].upper()
            if op_type == 'BUY':
                logger.info(f"[{tx['entry_time']}] COMPRA de {tx['symbol']} - Preço: {tx['entry_price']}, Qtd: {tx['quantity']}")
            else:
                logger.info(f"[{tx['exit_time']}] VENDA de {tx['symbol']} - Preço: {tx['exit_price']}, Lucro: {tx['profit_loss_percentage']:.2f}%")
    else:
        logger.warning("Nenhuma transação encontrada")
    
    # Exemplo 4: Calcular métricas de performance para o período atual
    logger.info("Exemplo 4: Calculando métricas de performance")
    
    # Definir período: último dia
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    metrics = pg.calculate_performance_metrics('daily', start_date, end_date)
    
    if metrics:
        logger.info("Métricas de performance calculadas:")
        logger.info(f"Período: {metrics['start_date']} a {metrics['end_date']}")
        logger.info(f"Total de trades: {metrics['total_trades']}")
        logger.info(f"Win rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Lucro/Prejuízo: {metrics['profit_loss']:.2f} ({metrics['profit_loss_percentage']:.2f}%)")
        logger.info(f"Lucro médio por trade: {metrics['avg_profit_per_trade']:.2f}")
        logger.info(f"Prejuízo médio por trade: {metrics['avg_loss_per_trade']:.2f}")
    else:
        logger.warning("Não foi possível calcular métricas (dados insuficientes ou erro)")
    
    # Exemplo 5: Obter histórico de capital
    logger.info("Exemplo 5: Obtendo histórico de capital")
    capital_history = pg.get_capital_history(limit=5)
    
    if capital_history:
        logger.info(f"Histórico de capital ({len(capital_history)} registros):")
        for entry in capital_history:
            change_str = f"{entry['change_percentage']:+.2f}%" if entry['change_percentage'] else "N/A"
            logger.info(f"[{entry['timestamp']}] Saldo: {entry['balance']:.2f} USDT ({change_str})")
    else:
        logger.warning("Nenhum registro de capital encontrado")
    
    # Exemplo 6: Registrar indicadores técnicos
    logger.info("Exemplo 6: Registrando indicadores técnicos")
    
    rsi_values = {"values": [45.2, 47.8, 52.3, 55.1, 53.2], "last": 53.2}
    rsi_id = pg.save_technical_indicator(
        symbol="BTC/USDT",
        indicator_type="RSI",
        values=rsi_values,
        interval="1h"
    )
    
    if rsi_id:
        logger.info(f"Indicador RSI registrado")
    
    # Exemplo 7: Registrar sinal de trading
    logger.info("Exemplo 7: Registrando sinal de trading")
    
    signal_id = pg.save_trading_signal(
        symbol="BTC/USDT",
        signal_type="buy",
        strength=0.75,
        price=42100.50,
        source="technical",
        reasoning="RSI saindo da zona de sobrevenda com MACD bullish",
        indicators_data={"rsi": 53.2, "macd": {"histogram": 0.25, "signal": 0.1, "macd": 0.35}}
    )
    
    if signal_id:
        logger.info(f"Sinal de compra registrado com ID: {signal_id}")
        # Marcar o sinal como executado
        pg.update_signal_executed(signal_id)
        logger.info(f"Sinal ID {signal_id} marcado como executado")
    
    logger.info("Exemplo de uso do PostgresManager concluído com sucesso")
    
    # Encerra a conexão
    pg.disconnect()

if __name__ == "__main__":
    main()
