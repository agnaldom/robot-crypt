#!/usr/bin/env python3
"""
Script de Integração Histórica para Robot-Crypt
Adiciona capacidades de análise histórica ao seu robô existente
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Adiciona src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.historical_comparator import HistoricalComparator
from src.integrations.historical_trading_integration import HistoricalTradingIntegration, TradingSignal
from src.core.logging_setup import logger


class HistoricalEnhancedStrategy:
    """
    Estratégia aprimorada que integra análise histórica ao seu robô existente
    """
    
    def __init__(self, original_strategy, binance_client=None, postgres_manager=None):
        """
        Inicializa a estratégia com análise histórica
        
        Args:
            original_strategy: Sua estratégia existente
            binance_client: Cliente Binance
            postgres_manager: Gerenciador PostgreSQL
        """
        self.original_strategy = original_strategy
        self.historical_integration = HistoricalTradingIntegration(
            binance_client=binance_client,
            postgres_manager=postgres_manager
        )
        
        # Configurações específicas para integração
        self.config = {
            'use_historical_analysis': True,
            'historical_weight': 0.3,  # Peso da análise histórica (30%)
            'original_weight': 0.7,    # Peso da análise original (70%)
            'min_historical_confidence': 0.6,
            'enable_historical_override': True,  # Permite histórico sobrescrever decisão original
            'historical_override_threshold': 0.8  # Threshold para override
        }
    
    async def analyze_symbol_enhanced(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise aprimorada que combina estratégia original com histórica
        
        Args:
            symbol: Símbolo para analisar
            market_data: Dados de mercado atuais
            
        Returns:
            Análise combinada
        """
        try:
            logger.info(f"Executando análise aprimorada para {symbol}")
            
            # 1. Executa análise original
            original_analysis = await self._execute_original_analysis(symbol, market_data)
            
            # 2. Executa análise histórica se habilitada
            historical_analysis = None
            if self.config['use_historical_analysis']:
                historical_analysis = await self._execute_historical_analysis(symbol, market_data)
            
            # 3. Combina as análises
            combined_analysis = self._combine_analyses(original_analysis, historical_analysis)
            
            logger.info(f"Análise aprimorada concluída para {symbol}: {combined_analysis.get('final_recommendation', 'N/A')}")
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Erro na análise aprimorada de {symbol}: {str(e)}")
            # Fallback para análise original
            return await self._execute_original_analysis(symbol, market_data)
    
    async def _execute_original_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise da estratégia original"""
        try:
            # Aqui você chamaria sua estratégia original
            # Por exemplo:
            # return await self.original_strategy.analyze(symbol, market_data)
            
            # Simulação para demonstração
            original_result = {
                'symbol': symbol,
                'recommendation': 'BUY',  # ou SELL, HOLD
                'confidence': 0.75,
                'entry_price': market_data.get('price', 50000),
                'reasoning': 'Análise técnica tradicional',
                'indicators': {
                    'rsi': 45,
                    'macd': 0.5,
                    'sma_20': 49500,
                    'sma_50': 48000
                },
                'risk_level': 'medium',
                'position_size': 0.02
            }
            
            logger.info(f"Análise original para {symbol}: {original_result['recommendation']} (confiança: {original_result['confidence']:.1%})")
            return original_result
            
        except Exception as e:
            logger.error(f"Erro na análise original: {str(e)}")
            return {
                'symbol': symbol,
                'recommendation': 'HOLD',
                'confidence': 0.1,
                'error': str(e)
            }
    
    async def _execute_historical_analysis(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Executa análise histórica"""
        try:
            # Prepara candle atual
            current_candle = {
                'open': market_data.get('open', market_data.get('price', 50000)),
                'high': market_data.get('high', market_data.get('price', 50000) * 1.01),
                'low': market_data.get('low', market_data.get('price', 50000) * 0.99),
                'close': market_data.get('price', 50000),
                'volume': market_data.get('volume', 1000),
                'open_time': int(datetime.now().timestamp() * 1000)
            }
            
            # Executa comparação histórica
            comparison_result = await self.historical_integration.historical_comparator.compare_with_historical(
                symbol=symbol,
                current_candle=current_candle,
                analysis_depth="medium"
            )
            
            # Converte resultado para formato compatível
            historical_result = {
                'symbol': symbol,
                'recommendation': comparison_result.recommendation,
                'confidence': comparison_result.confidence_score,
                'entry_price': comparison_result.current_price,
                'reasoning': f"Análise histórica: {comparison_result.historical_pattern_match:.1%} similaridade",
                'historical_context': {
                    'pattern_match': comparison_result.historical_pattern_match,
                    'trend_similarity': comparison_result.trend_similarity,
                    'volatility_ratio': comparison_result.volatility_comparison.get('volatility_ratio', 1.0),
                    'risk_level': comparison_result.risk_assessment.get('risk_level', 'medium'),
                    'support_levels': comparison_result.support_resistance_levels.get('support_levels', []),
                    'resistance_levels': comparison_result.support_resistance_levels.get('resistance_levels', []),
                    'similar_periods': len(comparison_result.similar_periods),
                    'prediction': comparison_result.price_prediction
                },
                'risk_level': comparison_result.risk_assessment.get('risk_level', 'medium'),
                'position_size': comparison_result.risk_assessment.get('recommended_position_size', 0.02)
            }
            
            logger.info(f"Análise histórica para {symbol}: {historical_result['recommendation']} (confiança: {historical_result['confidence']:.1%})")
            return historical_result
            
        except Exception as e:
            logger.error(f"Erro na análise histórica: {str(e)}")
            return None
    
    def _combine_analyses(self, original: Dict[str, Any], historical: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combina análises original e histórica"""
        try:
            # Se não há análise histórica, retorna original
            if not historical or historical['confidence'] < self.config['min_historical_confidence']:
                return {
                    **original,
                    'analysis_type': 'original_only',
                    'final_recommendation': original['recommendation'],
                    'final_confidence': original['confidence'],
                    'final_reasoning': original.get('reasoning', '')
                }
            
            # Verifica se histórica deve sobrescrever original
            if (self.config['enable_historical_override'] and 
                historical['confidence'] >= self.config['historical_override_threshold']):
                
                return {
                    **historical,
                    'analysis_type': 'historical_override',
                    'final_recommendation': historical['recommendation'],
                    'final_confidence': historical['confidence'],
                    'final_reasoning': f"Override histórico: {historical.get('reasoning', '')}",
                    'original_analysis': original
                }
            
            # Combina as duas análises
            combined_confidence = (
                original['confidence'] * self.config['original_weight'] +
                historical['confidence'] * self.config['historical_weight']
            )
            
            # Determina recomendação final baseada em consenso ou confiança
            final_recommendation = self._determine_consensus_recommendation(original, historical)
            
            # Combina reasoning
            final_reasoning = f"Análise combinada - Original: {original.get('reasoning', 'N/A')}; Histórica: {historical.get('reasoning', 'N/A')}"
            
            # Calcula tamanho de posição ajustado
            final_position_size = min(
                original.get('position_size', 0.02),
                historical.get('position_size', 0.02)
            )
            
            return {
                'symbol': original['symbol'],
                'analysis_type': 'combined',
                'final_recommendation': final_recommendation,
                'final_confidence': combined_confidence,
                'final_reasoning': final_reasoning,
                'final_position_size': final_position_size,
                'entry_price': (original.get('entry_price', 0) + historical.get('entry_price', 0)) / 2,
                'original_analysis': original,
                'historical_analysis': historical,
                'weights': {
                    'original': self.config['original_weight'],
                    'historical': self.config['historical_weight']
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao combinar análises: {str(e)}")
            return original
    
    def _determine_consensus_recommendation(self, original: Dict[str, Any], historical: Dict[str, Any]) -> str:
        """Determina recomendação final baseada em consenso"""
        original_rec = original.get('recommendation', 'HOLD')
        historical_rec = historical.get('recommendation', 'HOLD')
        
        # Se são iguais, usa consenso
        if original_rec == historical_rec:
            return original_rec
        
        # Se uma é HOLD, usa a outra se tiver alta confiança
        if original_rec == 'HOLD' and historical['confidence'] > 0.7:
            return historical_rec
        if historical_rec == 'HOLD' and original['confidence'] > 0.7:
            return original_rec
        
        # Se são opostas (BUY vs SELL), usa a de maior confiança
        if {original_rec, historical_rec} == {'BUY', 'SELL'}:
            if original['confidence'] > historical['confidence']:
                return original_rec
            else:
                return historical_rec
        
        # Fallback: usa original
        return original_rec


def integrate_historical_to_existing_strategy(strategy_class):
    """
    Decorator para integrar análise histórica a uma estratégia existente
    
    Usage:
    @integrate_historical_to_existing_strategy
    class MyExistingStrategy:
        # sua estratégia existente
    """
    
    class HistoricalIntegratedStrategy(strategy_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.historical_enhancer = HistoricalEnhancedStrategy(self)
        
        async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
            # Usa análise aprimorada
            return await self.historical_enhancer.analyze_symbol_enhanced(symbol, market_data)
    
    return HistoricalIntegratedStrategy


async def demo_integration():
    """Demonstra como integrar ao robô existente"""
    print("🤖 DEMONSTRAÇÃO: Integração com Robô Existente")
    print("=" * 60)
    
    # Simula estratégia existente
    class ExistingStrategy:
        async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                'symbol': symbol,
                'recommendation': 'BUY',
                'confidence': 0.8,
                'reasoning': 'Estratégia original'
            }
    
    # Cria estratégia aprimorada
    original_strategy = ExistingStrategy()
    enhanced_strategy = HistoricalEnhancedStrategy(original_strategy)
    
    # Testa com dados simulados
    market_data = {
        'price': 50000,
        'volume': 1000,
        'high': 51000,
        'low': 49000
    }
    
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    for symbol in symbols:
        print(f"\n📊 Testando {symbol}...")
        
        try:
            result = await enhanced_strategy.analyze_symbol_enhanced(symbol, market_data)
            
            print(f"✅ Resultado para {symbol}:")
            print(f"   • Tipo de análise: {result.get('analysis_type', 'N/A')}")
            print(f"   • Recomendação final: {result.get('final_recommendation', 'N/A')}")
            print(f"   • Confiança final: {result.get('final_confidence', 0):.1%}")
            print(f"   • Tamanho posição: {result.get('final_position_size', 0):.1%}")
            
            # Mostra detalhes se é análise combinada
            if result.get('analysis_type') == 'combined':
                orig = result.get('original_analysis', {})
                hist = result.get('historical_analysis', {})
                print(f"   • Original: {orig.get('recommendation', 'N/A')} ({orig.get('confidence', 0):.1%})")
                print(f"   • Histórica: {hist.get('recommendation', 'N/A')} ({hist.get('confidence', 0):.1%})")
                
                weights = result.get('weights', {})
                print(f"   • Pesos: Original {weights.get('original', 0):.1%}, Histórica {weights.get('historical', 0):.1%}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")


async def main():
    """Função principal"""
    print("🔧 INTEGRAÇÃO HISTÓRICA PARA ROBOT-CRYPT")
    print("⚡ Adicionando capacidades de análise histórica")
    print("⏰ Início:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    try:
        await demo_integration()
        
        print("\n" + "=" * 60)
        print("✅ DEMONSTRAÇÃO DE INTEGRAÇÃO CONCLUÍDA!")
        print("=" * 60)
        
        print("\n📋 Como integrar ao seu robô:")
        print("1. Importe: from scripts.integrate_historical_to_robot import HistoricalEnhancedStrategy")
        print("2. Inicialize: enhanced = HistoricalEnhancedStrategy(sua_estrategia_atual)")
        print("3. Use: result = await enhanced.analyze_symbol_enhanced(symbol, market_data)")
        print("4. Ou use o decorator @integrate_historical_to_existing_strategy")
        
        print("\n⚙️  Configurações disponíveis:")
        print("• historical_weight: Peso da análise histórica (padrão: 0.3)")
        print("• original_weight: Peso da análise original (padrão: 0.7)")
        print("• min_historical_confidence: Confiança mínima histórica (padrão: 0.6)")
        print("• enable_historical_override: Permite override histórico (padrão: True)")
        print("• historical_override_threshold: Threshold para override (padrão: 0.8)")
        
        print("\n🎯 Exemplo de uso no seu código:")
        print("""
# No seu arquivo de estratégia:
from scripts.integrate_historical_to_robot import HistoricalEnhancedStrategy

# Modifique sua classe de estratégia:
class MinhaEstrategia:
    def __init__(self, config, binance_api):
        # ... sua inicialização atual ...
        self.historical_enhancer = HistoricalEnhancedStrategy(self, binance_api)
    
    async def analyze_market(self, symbol, market_data):
        # Use análise aprimorada:
        return await self.historical_enhancer.analyze_symbol_enhanced(symbol, market_data)
        """)
        
    except Exception as e:
        print(f"\n❌ Erro na integração: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
