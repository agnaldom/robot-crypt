#!/bin/bash
set -e

# Carrega variáveis de ambiente
source .env

# Executa o bot com log verbose
python main.py
