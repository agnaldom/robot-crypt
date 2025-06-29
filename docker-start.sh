#!/bin/bash
# Script para iniciar o Robot-Crypt usando Docker

echo "==================================="
echo "  Robot-Crypt Docker Direct Start  "
echo "==================================="
echo

# Verificando se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker não está instalado. Por favor, instale o Docker primeiro."
    echo "Visite: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se a imagem existe, se não, construí-la
if ! docker image inspect robot-crypt:latest &> /dev/null; then
    echo "Imagem robot-crypt:latest não encontrada. Construindo..."
    docker build -t robot-crypt:latest .
fi

# Iniciar o container
echo "Iniciando Robot-Crypt..."
docker run -d \
    --name robot-crypt \
    --restart unless-stopped \
    -v "$(pwd)/.env:/app/.env" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/data:/app/data" \
    -e TZ=America/Sao_Paulo \
    robot-crypt:latest

echo
echo "Robot-Crypt iniciado com sucesso!"
echo "Para verificar os logs: docker logs robot-crypt"
echo "Para parar o container: docker stop robot-crypt"
