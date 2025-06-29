FROM python:3.9-slim

WORKDIR /app

# Instala dependências essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro (para melhor uso do cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Garante que o python-dotenv e outros pacotes essenciais estão instalados
RUN pip install --no-cache-dir python-dotenv requests

# Copia o restante dos arquivos do projeto
COPY . .

# Cria a estrutura de diretórios para logs, dados e relatórios
RUN mkdir -p /app/logs
RUN mkdir -p /app/data
RUN mkdir -p /app/reports

# Torna o script de entrada executável
RUN chmod +x /app/railway_entrypoint.sh

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Sao_Paulo
ENV PYTHONIOENCODING=utf-8

# Define o comando de entrada
ENTRYPOINT ["/app/railway_entrypoint.sh"]
