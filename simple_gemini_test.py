#!/usr/bin/env python3
"""
Teste simples do Gemini
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai.llm_client import get_llm_client

async def main():
    print("🧪 Teste Simples do Gemini")
    
    try:
        client = get_llm_client()
        print(f"Provider: {client.provider}")
        print(f"Model: {client.model}")
        
        # Teste básico
        print("\n1. Teste básico...")
        response = await client.chat("Olá! Como você está?")
        print(f"✅ Response: {response.content}")
        print(f"📊 Tokens: {response.tokens_used}")
        print(f"💰 Cost: ${response.cost_estimate:.6f}")
        
        # Teste análise crypto
        print("\n2. Teste análise crypto...")
        crypto_prompt = "Analise brevemente o Bitcoin como investimento."
        response = await client.chat(crypto_prompt)
        print(f"✅ Response: {response.content[:200]}...")
        print(f"📊 Tokens: {response.tokens_used}")
        
        # Teste JSON
        print("\n3. Teste JSON...")
        json_prompt = "Forneça uma análise JSON do mercado de Bitcoin com campos: sentiment, confidence, trend."
        response = await client.analyze_json(json_prompt)
        print(f"✅ JSON Response: {response}")
        
        print("\n🎉 Todos os testes concluídos!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
