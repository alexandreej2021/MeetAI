#!/usr/bin/env python3
"""
Teste específico para verificar se o resumo com Gemini está funcionando
"""

import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai.gemini_summarizer import GeminiSummarizer

def test_gemini_summary():
    """Testar geração de resumo com Gemini"""
    print("🧪 TESTE DE RESUMO COM GEMINI")
    print("=" * 50)
    
    try:
        # Inicializar o resumidor
        summarizer = GeminiSummarizer()
        
        if not summarizer.client:
            print("❌ Gemini não configurado corretamente")
            return False
            
        print("✅ Gemini configurado com sucesso")
        
        # Texto de teste
        test_transcript = """
        Bom dia pessoal! Hoje vamos discutir sobre o projeto MeetAI.
        Este projeto é uma ferramenta para gravar reuniões e gerar resumos automáticos.
        As principais funcionalidades incluem gravação de áudio, transcrição e resumos com IA.
        Acredito que isso vai facilitar muito o trabalho das equipes.
        Alguma dúvida sobre o projeto?
        """
        
        print("📝 Gerando resumo...")
        
        # Gerar resumo
        summary = summarizer.generate_summary(test_transcript, "conversa")
        
        if summary:
            print("✅ Resumo gerado com sucesso!")
            print("\n🎯 RESUMO GERADO:")
            print("-" * 30)
            print(summary)
            print("-" * 30)
            return True
        else:
            print("❌ Falha ao gerar resumo")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_summary()
    if success:
        print("\n🎉 Teste concluído com SUCESSO!")
    else:
        print("\n💥 Teste FALHOU!")