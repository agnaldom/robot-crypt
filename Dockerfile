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
# Garante que o python-dotenv está instalado
RUN pip install --no-cache-dir python-dotenv

# Copia o restante dos arquivos do projeto
COPY . .

# Cria a estrutura de diretórios para logs, dados e relatórios
RUN mkdir -p /app/logs
RUN mkdir -p /app/data
RUN mkdir -p /app/reports

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Sao_Paulo

# Define o comando de entrada
ENTRYPOINT ["python", "main.py"]
