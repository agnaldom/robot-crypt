# Desenvolvimento do Dashboard Externo para Robot-Crypt

Este documento descreve como desenvolver um dashboard frontend separado para o Robot-Crypt, que se conectará ao banco de dados PostgreSQL.

## Motivação

Separar o dashboard do código principal do bot tem várias vantagens:

1. **Desacoplamento**: O bot pode ser executado de forma independente, sem depender de bibliotecas de visualização.
2. **Tecnologias especializadas**: Permite usar frameworks frontend modernos para construir uma interface mais rica.
3. **Escalabilidade**: O dashboard pode ser hospedado em um servidor diferente do bot.
4. **Manutenção**: Mudanças no frontend não exigem modificações no código do bot.

## Conexão com o Banco de Dados

O novo dashboard se conectará diretamente ao banco PostgreSQL:

```
POSTGRES_URL=postgresql://postgres.vlmklyizetfjybypswlp:%40G071290nm@aws-0-us-east-2.pooler.supabase.com:5432/postgres
```

## Tabelas Principais

O dashboard deve consultar as seguintes tabelas:

- `trades`: Registros de operações (trades)
- `stats`: Estatísticas diárias do bot
- `analysis`: Análises de mercado
- `notifications`: Notificações geradas pelo bot
- `market_data`: Dados de mercado coletados
- `app_state`: Estado do aplicativo

## Opções de Tecnologia para o Frontend

### Opção 1: React + Plotly/Chart.js

```bash
# Criar um novo projeto React
npx create-react-app robot-crypt-dashboard
cd robot-crypt-dashboard

# Instalar dependências
npm install axios pg plotly.js react-plotly.js chart.js react-chartjs-2
```

### Opção 2: Vue + D3.js

```bash
# Criar um novo projeto Vue
npm init vue@latest robot-crypt-dashboard
cd robot-crypt-dashboard

# Instalar dependências
npm install axios pg d3 vue-d3-charts
```

### Opção 3: Streamlit (Python)

Se preferir continuar usando Python para o frontend:

```bash
# Criar um ambiente virtual
python -m venv dashboard-venv
source dashboard-venv/bin/activate  # No Windows: dashboard-venv\Scripts\activate

# Instalar dependências
pip install streamlit psycopg2-binary pandas plotly
```

Exemplo de código Streamlit:

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import datetime, timedelta

# Configuração da conexão
conn_string = "postgresql://postgres.user:password@aws-host:5432/postgres"

# Função para carregar dados
def load_trade_data():
    conn = psycopg2.connect(conn_string)
    query = "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Interface
st.title("Robot-Crypt Dashboard")

# Filtros
st.sidebar.header("Filtros")
date_range = st.sidebar.date_input(
    "Período",
    [datetime.now() - timedelta(days=7), datetime.now()]
)

# Carregar e exibir dados
trades_df = load_trade_data()
st.header("Operações Recentes")
st.dataframe(trades_df)

# Gráficos
st.header("Performance")
fig = px.line(trades_df, x="timestamp", y="profit", title="Lucro por Operação")
st.plotly_chart(fig)
```

## API Backend (Opcional)

Para maior segurança, você pode criar uma API intermediária que acessa o banco de dados e fornece endpoints para o frontend:

```bash
# Usando Express.js
npm install express pg cors

# Ou usando Flask
pip install flask flask-cors psycopg2-binary
```

## Implantação

O dashboard pode ser implantado em:

1. Vercel ou Netlify (para opções baseadas em JavaScript)
2. Streamlit Cloud (para opção Streamlit)
3. Heroku, Railway ou render.com (para qualquer opção)

## Próximos Passos

1. Escolha a tecnologia frontend desejada
2. Configure a conexão com o banco de dados
3. Desenvolva os componentes de visualização essenciais
4. Implemente filtros e interatividade
5. Implante o dashboard em um serviço de hospedagem
