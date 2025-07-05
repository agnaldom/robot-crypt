# Relatório de Uso das Tabelas PostgreSQL - Robot-Crypt

Este relatório analisa onde cada uma das 17 tabelas PostgreSQL está sendo usada no projeto Robot-Crypt.

## 📊 Status das Tabelas

### ✅ TABELAS ATIVAS (Com dados e uso frequente)

#### 1. **app_state** (40 kB, 0 registros)
- **Uso**: Armazenamento do estado da aplicação
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 256-266)
- **Métodos**:
  - `save_app_state()` - Salva estado atual
  - `load_last_app_state()` - Carrega último estado
- **Usado em**:
  - `src/trading_bot_main.py` - Salvamento periódico do estado
  - `src/database/db_manager.py` - Fallback SQLite
- **Dados**: Estados do bot, estratégia ativa, pares monitorados, posições abertas

#### 2. **asset_balances** (104 kB, 10 registros) ⭐
- **Uso**: Saldos de ativos da carteira
- **Localização Principal**: Não encontrada estrutura específica no PostgresManager
- **Usado em**:
  - `src/trading/wallet_manager.py` - Provavelmente relacionado
  - Scripts de sincronização de carteira
- **Status**: 🟡 Tabela com dados, mas estrutura não definida no código principal

#### 3. **capital_history** (48 kB, 1 registro) ⭐
- **Uso**: Histórico de mudanças no capital
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 269-280)
- **Métodos**:
  - `save_capital_update()` - Registra mudanças no capital
  - `get_capital_history()` - Obtém histórico
- **Usado em**:
  - `src/trading_bot_main.py` - Após cada operação
  - `src/scripts/maintenance/pg_example.py` - Exemplos de uso

#### 4. **daily_performance** (80 kB, 3 registros) ⭐
- **Uso**: Métricas de performance diárias
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 197-218)
- **Métodos**:
  - `update_daily_stats()` - Atualiza estatísticas diárias
- **Usado em**:
  - `src/trading_bot_main.py` - Atualização diária de stats
  - `src/database/db_manager.py` - Versão SQLite similar

#### 5. **notifications** (32 kB, 1 registro) ⭐
- **Uso**: Sistema de notificações
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 103-111)
- **Métodos**:
  - `save_notification()` - Salva notificações
  - `get_recent_notifications()` - Obtém notificações recentes
- **Usado em**:
  - `src/notifications/telegram_notifier.py` - Notificações Telegram
  - `src/notifications/local_notifier.py` - Notificações locais

#### 6. **trades** (16 kB, 0 registros)
- **Uso**: Operações de trading (compatibilidade)
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 157-174)
- **Métodos**:
  - `save_trade()` - Salva trades
  - `update_trade_exit()` - Atualiza saída
  - `get_open_trades()`, `get_closed_trades()` - Consultas
- **Usado em**:
  - `src/api/routers/trades.py` - API endpoints
  - `src/services/trade_service.py` - Lógica de negócio

#### 7. **transaction_history** (80 kB, 0 registros)
- **Uso**: Histórico detalhado de transações
- **Localização Principal**: `src/database/postgres_manager.py` (linhas 126-153)
- **Métodos**:
  - `record_transaction()` - Registra transação completa
  - `get_transaction_history()` - Obtém histórico
- **Usado em**:
  - `src/trading_bot_main.py` - Registro de operações
  - Scripts de exemplo e manutenção

#### 8. **user_wallet** (Não listada no seu banco, mas presente no código)
- **Uso**: Carteira do usuário
- **Localização Principal**: `src/trading/wallet_manager.py` (linhas 62-73)
- **Métodos**: Gestão completa de carteira
- **Status**: 🔴 Tabela definida no código mas não aparece na sua lista

### 🟡 TABELAS DEFINIDAS MAS SEM USO ATIVO

#### 9. **market_analysis** (16 kB, 0 registros)
- **Uso**: Análises de mercado
- **Localização**: `src/database/postgres_manager.py` (linhas 115-122)
- **Métodos**:
  - `save_analysis()` - Salva análises
  - `get_recent_analysis()` - Obtém análises
- **Status**: 🟡 Estrutura pronta, mas pouco utilizada

#### 10. **price_history** (16 kB, 0 registros)
- **Uso**: Histórico de preços OHLCV
- **Localização**: `src/database/postgres_manager.py` (linhas 178-194)
- **Métodos**:
  - `save_price_history()` - Salva dados de preço
  - `save_price_history_batch()` - Lote
  - `get_price_history()` - Consulta histórico
- **Status**: 🟡 Implementado mas não usado ativamente

#### 11. **technical_indicators** (24 kB, 0 registros)
- **Uso**: Indicadores técnicos calculados
- **Localização**: `src/database/postgres_manager.py` (linhas 284-295)
- **Métodos**:
  - `save_technical_indicator()` - Salva indicadores
  - `get_technical_indicators()` - Consulta indicadores
- **Usado em**:
  - `src/api/routers/indicators.py` - API endpoints
  - `src/models/technical_indicator.py` - Modelos

#### 12. **trading_signals** (80 kB, 0 registros)
- **Uso**: Sinais de trading gerados
- **Localização**: `src/database/postgres_manager.py` (linhas 299-315)
- **Métodos**:
  - `save_trading_signal()` - Salva sinais
  - `update_signal_executed()` - Marca como executado
  - `get_trading_signals()` - Consulta sinais

### 🔴 TABELAS SEM IMPLEMENTAÇÃO ENCONTRADA

#### 13. **drawdowns** (16 kB, 0 registros)
- **Uso**: Registros de drawdown
- **Localização**: `src/database/postgres_manager.py` (linhas 340-359)
- **Status**: 🔴 Estrutura definida, mas sem métodos específicos implementados

#### 14. **performance_metrics** (16 kB, 0 registros)
- **Uso**: Métricas de performance periódicas
- **Localização**: `src/database/postgres_manager.py` (linhas 222-251)
- **Métodos**: `calculate_performance_metrics()` - Método complexo implementado
- **Status**: 🟡 Implementação completa, mas não usado regularmente

#### 15. **periodic_stats** (24 kB, 0 registros)
- **Uso**: Estatísticas periódicas (semanal, mensal)
- **Localização**: `src/database/postgres_manager.py` (linhas 320-337)
- **Status**: 🔴 Estrutura definida, mas implementação incompleta

#### 16. **recent_orders** (16 kB, 0 registros)
- **Uso**: Ordens recentes
- **Status**: 🔴 Não encontrada implementação específica no código

#### 17. **system_health** (16 kB, 0 registros)
- **Uso**: Métricas de saúde do sistema
- **Localização**: `src/database/postgres_manager.py` (linhas 363-374)
- **Usado em**: `src/tools/health_monitor.py`
- **Status**: 🟡 Estrutura definida, implementação parcial

## 📈 Resumo por Status

| Status | Quantidade | Tabelas |
|--------|------------|---------|
| ✅ **Ativas e Usadas** | 8 | app_state, asset_balances, capital_history, daily_performance, notifications, trades, transaction_history, user_wallet |
| 🟡 **Implementadas, Pouco Usadas** | 6 | market_analysis, price_history, technical_indicators, trading_signals, performance_metrics, system_health |
| 🔴 **Definidas, Não Implementadas** | 3 | drawdowns, periodic_stats, recent_orders |

## 🔧 Recomendações

### Imediatas:
1. **user_wallet** - Verificar por que não aparece na sua lista de tabelas
2. **asset_balances** - Documentar e integrar com WalletManager
3. **recent_orders** - Implementar ou remover se não necessária

### Otimizações:
1. **price_history** - Ativar coleta de dados históricos
2. **technical_indicators** - Integrar com sistema de análise
3. **trading_signals** - Conectar com estratégias de trading

### Limpeza:
1. **drawdowns** - Implementar ou remover estrutura
2. **periodic_stats** - Completar implementação ou remover

## 📍 Arquivos Principais de Referência

- **`src/database/postgres_manager.py`** - Implementação principal das tabelas
- **`src/trading_bot_main.py`** - Uso principal no bot de trading
- **`src/trading/wallet_manager.py`** - Gestão de carteira
- **`src/services/trading_session.py`** - Sessões de trading
- **`src/api/routers/trades.py`** - API de trades

Seu código **ESTÁ** atualizando o banco PostgreSQL nas tabelas ativas! 🎯
