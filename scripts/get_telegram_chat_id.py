#!/usr/bin/env python3
"""
Script para obter o Chat ID do Telegram

Uso:
1. Configure o TELEGRAM_BOT_TOKEN no .env ou passe como argumento
2. Inicie uma conversa com seu bot e envie qualquer mensagem
3. Execute este script

Exemplo:
    python scripts/get_telegram_chat_id.py
    python scripts/get_telegram_chat_id.py --token "SEU_TOKEN_AQUI"
"""

import os
import sys
import argparse
import requests
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

def get_chat_id(bot_token):
    """
    Obtém o Chat ID a partir das mensagens recebidas pelo bot
    
    Args:
        bot_token (str): Token do bot do Telegram
        
    Returns:
        str: Chat ID encontrado ou None se não encontrado
    """
    try:
        print(f"🔍 Buscando mensagens para o bot...")
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Erro na API do Telegram: {data.get('description', 'Erro desconhecido')}")
            return None
        
        if not data.get('result'):
            print("❌ Nenhuma mensagem encontrada!")
            print("📝 Para obter o Chat ID:")
            print("   1. Abra o Telegram")
            print("   2. Procure pelo seu bot")
            print("   3. Envie qualquer mensagem (ex: /start ou 'olá')")
            print("   4. Execute este script novamente")
            return None
        
        # Busca pelo Chat ID na mensagem mais recente
        messages = data['result']
        latest_message = messages[-1]
        
        if 'message' in latest_message and 'chat' in latest_message['message']:
            chat_id = latest_message['message']['chat']['id']
            chat_type = latest_message['message']['chat']['type']
            
            # Informações do chat
            chat_info = latest_message['message']['chat']
            
            print("✅ Chat ID encontrado!")
            print(f"📊 Chat ID: {chat_id}")
            print(f"📋 Tipo: {chat_type}")
            
            if 'username' in chat_info:
                print(f"👤 Username: @{chat_info['username']}")
            if 'first_name' in chat_info:
                print(f"👤 Nome: {chat_info['first_name']}")
            if 'title' in chat_info:
                print(f"👥 Título do grupo: {chat_info['title']}")
            
            return str(chat_id)
        else:
            print("❌ Formato de mensagem inválido")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

def test_bot_token(bot_token):
    """
    Testa se o token do bot é válido
    
    Args:
        bot_token (str): Token do bot
        
    Returns:
        bool: True se o token é válido
    """
    try:
        print("🔍 Testando token do bot...")
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print("✅ Token válido!")
            print(f"🤖 Nome do bot: {bot_info.get('first_name', 'N/A')}")
            print(f"👤 Username: @{bot_info.get('username', 'N/A')}")
            print(f"🆔 Bot ID: {bot_info.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Token inválido: {data.get('description', 'Erro desconhecido')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de rede: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

def update_env_file(chat_id, env_file_path=".env"):
    """
    Atualiza ou adiciona o TELEGRAM_CHAT_ID no arquivo .env
    
    Args:
        chat_id (str): Chat ID para adicionar
        env_file_path (str): Caminho para o arquivo .env
    """
    try:
        env_path = Path(env_file_path)
        
        # Lê o arquivo existente
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Procura por TELEGRAM_CHAT_ID existente
        chat_id_line_index = None
        for i, line in enumerate(lines):
            if line.strip().startswith('TELEGRAM_CHAT_ID='):
                chat_id_line_index = i
                break
        
        # Atualiza ou adiciona a linha
        new_line = f"TELEGRAM_CHAT_ID={chat_id}\n"
        
        if chat_id_line_index is not None:
            lines[chat_id_line_index] = new_line
            print(f"✅ TELEGRAM_CHAT_ID atualizado no {env_file_path}")
        else:
            lines.append(new_line)
            print(f"✅ TELEGRAM_CHAT_ID adicionado ao {env_file_path}")
        
        # Escreve o arquivo atualizado
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar {env_file_path}: {str(e)}")
        return False

def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Obtém o Chat ID do Telegram para configurar notificações",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/get_telegram_chat_id.py
  python scripts/get_telegram_chat_id.py --token "123456789:ABCdefGHIjklMNOpqrSTUvwxyz"
  python scripts/get_telegram_chat_id.py --no-update-env
        """
    )
    
    parser.add_argument(
        '--token', 
        help='Token do bot do Telegram (se não fornecido, usa TELEGRAM_BOT_TOKEN do .env)'
    )
    parser.add_argument(
        '--no-update-env', 
        action='store_true',
        help='Não atualiza automaticamente o arquivo .env'
    )
    parser.add_argument(
        '--env-file',
        default='.env',
        help='Caminho para o arquivo .env (padrão: .env)'
    )
    
    args = parser.parse_args()
    
    print("🤖 Script para obter Chat ID do Telegram")
    print("=" * 50)
    
    # Obtém o token do bot
    bot_token = args.token
    if not bot_token:
        # Carrega do arquivo .env
        from dotenv import load_dotenv
        load_dotenv()
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ Token do bot não encontrado!")
        print("📝 Soluções:")
        print("   1. Defina TELEGRAM_BOT_TOKEN no arquivo .env")
        print("   2. Use o parâmetro --token")
        print("\n💡 Para criar um bot:")
        print("   1. Abra o Telegram")
        print("   2. Procure por @BotFather")
        print("   3. Use o comando /newbot")
        sys.exit(1)
    
    # Testa o token
    if not test_bot_token(bot_token):
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Obtém o Chat ID
    chat_id = get_chat_id(bot_token)
    
    if chat_id:
        print("\n" + "=" * 50)
        print("🎉 Sucesso! Configuração encontrada:")
        print(f"   TELEGRAM_BOT_TOKEN=...{bot_token[-10:]}")  # Mostra apenas os últimos 10 caracteres
        print(f"   TELEGRAM_CHAT_ID={chat_id}")
        
        # Atualiza o arquivo .env se solicitado
        if not args.no_update_env:
            print("\n📝 Atualizando arquivo .env...")
            if update_env_file(chat_id, args.env_file):
                print("✅ Arquivo .env atualizado com sucesso!")
            else:
                print("❌ Erro ao atualizar arquivo .env")
        
        print("\n🚀 Próximos passos:")
        print("   1. Verifique se as configurações estão corretas no .env")
        print("   2. Execute: python scripts/test_telegram.py")
        print("   3. Inicie o robot-crypt para receber notificações!")
        
    else:
        print("\n❌ Não foi possível obter o Chat ID")
        print("📝 Verifique se você enviou uma mensagem para o bot")
        sys.exit(1)

if __name__ == "__main__":
    main()
