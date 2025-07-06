# 📁 Estrutura do Projeto Robot-Crypt

## 🎯 Nova Organização Modular

O projeto Robot-Crypt foi reorganizado em uma estrutura modular profissional para melhorar a manutenibilidade, escalabilidade e clareza do código.

## 📂 Estrutura de Diretórios

```
robot-crypt/
├── 📄 main.py                    # Ponto de entrada principal
├── 📄 setup.sh                   # Script de configuração (proxy)
├── 📄 requirements.txt           # Dependências Python
├── 📄 .env                       # Configuração de ambiente
├── 📄 .gitignore                 # Arquivos ignorados pelo Git
├── 📄 README.md                  # Documentação principal
├── 📄 ESTRUTURA_PROJETO.md       # Esta documentação
│
├── 📁 src/                       # Código fonte principal
│   ├── 📄 __init__.py           # Pacote principal com exports
│   │
│   ├── 📁 core/                 # Módulos fundamentais
│   │   ├── 📄 __init__.py
│   │   └── 📄 config.py         # Configurações centrais
│   │
│   ├── 📁 api/                  # Integrações com APIs externas
│   │   ├── 📄 __init__.py
│   │   ├── 📄 binance_api.py    # API da Binance
│   │   └── 📄 binance_simulator.py # Simulador da Binance
│   │
│   ├── 📁 strategies/           # Estratégias de trading
│   │   ├── 📄 __init__.py
│   │   └── 📄 strategy.py       # ScalpingStrategy, SwingTradingStrategy
│   │
│   ├── 📁 analysis/             # Análise técnica e fundamental
│   │   ├── 📄 __init__.py
│   │   ├── 📄 technical_indicators.py  # RSI, MACD, Bollinger, etc.
│   │   ├── 📄 external_data_analyzer.py # Análise de dados externos
│   │   └── 📄 crypto_events.py  # Eventos de criptomoedas
│   │
│   ├── 📁 database/             # Gerenciamento de dados
│   │   ├── 📄 __init__.py
│   │   ├── 📄 db_manager.py     # SQLite manager
│   │   └── 📄 postgres_manager.py # PostgreSQL manager
│   │
│   ├── 📁 notifications/        # Sistema de notificações
│   │   ├── 📄 __init__.py
│   │   ├── 📄 telegram_notifier.py # Notificações Telegram
│   │   └── 📄 local_notifier.py # Notificações locais
│   │
│   ├── 📁 trading/              # Operações de trading
│   │   ├── 📄 __init__.py
│   │   ├── 📄 wallet_manager.py # Gerenciamento de carteira
│   │   └── 📄 report_generator.py # Relatórios de trading
│   │
│   ├── 📁 risk_management/      # Gestão de risco
│   │   ├── 📄 __init__.py
│   │   └── 📄 adaptive_risk_manager.py # Gestão adaptativa
│   │
│   └── 📁 utils/                # Utilitários gerais
│       ├── 📄 __init__.py
│       └── 📄 utils.py          # Funções auxiliares
│
├── 📁 scripts/                  # Scripts de automação
│   ├── 📁 setup/               # Scripts de configuração
│   │   ├── 📄 setup.sh         # Setup principal
│   │   ├── 📄 setup_simulation.py
│   │   └── 📄 setup_simulation.sh
│   │
│   ├── 📁 deployment/          # Scripts de deploy
│   │   ├── 📄 railway_entrypoint.sh
│   │   └── 📄 healthcheck.sh
│   │
│   └── 📁 maintenance/         # Scripts de manutenção
│       ├── 📄 sync_wallet.py
│       ├── 📄 sync_wallet.sh
│       ├── 📄 sync_config.py
│       ├── 📄 wallet_balance.sh
│       ├── 📄 run_binance_sync.sh
│       ├── 📄 run_performance_test.sh
│       └── 📄 pg_example.py
│
├── 📁 config/                   # Configurações do projeto
│   ├── 📄 railway.toml         # Configuração Railway
│   └── 📁 environments/        # Ambientes de configuração
│       ├── 📄 .env.example
│       ├── 📄 .env.development
│       ├── 📄 .env.real
│       └── 📄 .env.test
│
├── 📁 tests/                    # Testes automatizados
│   ├── 📁 unit/               # Testes unitários
│   ├── 📁 integration/        # Testes de integração
│   └── 📁 performance/        # Testes de performance
│
├── 📁 tools/                    # Ferramentas de desenvolvimento
│   ├── 📄 health_monitor.py    # Monitor de saúde do sistema
│   ├── 📄 postgres_checker.py  # Verificador PostgreSQL
│   ├── 📄 cleanup_analysis.py  # Análise de limpeza
│   ├── 📄 auto_cleanup.py      # Limpeza automatizada
│   ├── 📄 cleanup_log.json     # Log de limpeza
│   └── 📄 cleanup_report.json  # Relatório de limpeza
│
├── 📁 data/                     # Dados persistentes
├── 📁 logs/                     # Arquivos de log
├── 📁 reports/                  # Relatórios gerados
└── 📁 docs/                     # Documentação adicional
    ├── 📄 FUNCIONAMENTO.md
    ├── 📄 MONITORAMENTO.md
    └── 📄 CONTA_REAL.md
```

## 🚀 Como Usar

### 1. Configuração
```bash
# Modo simulação (padrão)
./setup.sh simulation

# Modo TestNet
./setup.sh testnet

# Modo produção
./setup.sh production
```

### 2. Execução
```bash
# Executar o bot
python main.py

# Ou usando o módulo
python -m src
```

### 3. Imports no Código

#### Novo Padrão (Recomendado)
```python
# Import centralizado e limpo
from src import (
    Config, BinanceAPI, ScalpingStrategy, SwingTradingStrategy,
    TelegramNotifier, WalletManager, AdaptiveRiskManager
)
```

#### Import Específico (Alternativo)
```python
# Import direto de módulos específicos
from src.core.config import Config
from src.api.binance_api import BinanceAPI
from src.strategies.strategy import ScalpingStrategy
from src.notifications.telegram_notifier import TelegramNotifier
```

## 🎯 Benefícios da Nova Estrutura

### 1. **Organização Modular**
- Cada componente tem sua responsabilidade específica
- Fácil localização de funcionalidades
- Melhor separação de responsabilidades

### 2. **Manutenibilidade**
- Código mais fácil de manter e atualizar
- Redução de dependências cruzadas
- Testes mais organizados

### 3. **Escalabilidade**
- Estrutura preparada para crescimento
- Fácil adição de novos módulos
- Arquitetura profissional

### 4. **Desenvolvimento**
- Imports mais limpos e organizados
- Melhor IntelliSense/autocomplete
- Estrutura familiar para desenvolvedores

## 🔧 Scripts Úteis

### Configuração
```bash
./setup.sh help                    # Ajuda do setup
./scripts/setup/setup.sh help      # Ajuda detalhada
```

### Manutenção
```bash
./scripts/maintenance/sync_wallet.sh     # Sincronizar carteira
./scripts/maintenance/wallet_balance.sh  # Verificar saldo
```

### Deployment
```bash
./scripts/deployment/healthcheck.sh      # Verificar saúde
```

## 📋 Migração de Código Antigo

Se você tem código que usa imports antigos, atualize-os:

```python
# ❌ Antigo
from config import Config
from binance_api import BinanceAPI
from strategy import ScalpingStrategy

# ✅ Novo
from src import Config, BinanceAPI, ScalpingStrategy
```

## 🚨 Compatibilidade

- **Python**: 3.8+
- **Estrutura**: Totalmente compatível com versões anteriores
- **APIs**: Sem mudanças nas interfaces públicas
- **Configuração**: Mesmos arquivos .env

---

**📝 Nota:** Esta nova estrutura mantém toda a funcionalidade existente enquanto melhora significativamente a organização e manutenibilidade do código.
