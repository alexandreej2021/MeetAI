#!/usr/bin/env python3
"""
Teste para verificar se estamos perdendo palavras na transcrição em tempo real
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

def test_word_preservation():
    """Testar se não estamos perdendo palavras"""
    print("🔍 TESTE DE PRESERVAÇÃO DE PALAVRAS")
    print("=" * 60)
    
    # Inicializar componentes
    recorder = AudioRecorder()
    transcriber = Transcriber()
    
    if not transcriber.client:
        print("❌ OpenAI não configurado")
        return False
    
    print("✅ Componentes inicializados")
    
    # Variáveis de teste
    received_chunks = []
    all_words = []
    
    def realtime_callback(chunk_file, chunk_number):
        """Callback que coleta todas as palavras"""
        print(f"📥 Processando chunk {chunk_number}...")
        
        try:
            transcript = transcriber.transcribe(chunk_file)
            if transcript:
                words = transcript.lower().split()
                all_words.extend(words)
                received_chunks.append((chunk_number, transcript))
                print(f"✅ Chunk {chunk_number}: \"{transcript}\"")
                print(f"   📝 Palavras: {words}")
            else:
                print(f"❌ Chunk {chunk_number} vazio")
                
        except Exception as e:
            print(f"❌ Erro chunk {chunk_number}: {e}")
    
    # Configurar callback
    recorder.set_realtime_transcription_callback(realtime_callback)
    
    print(f"⚙️ Configurações balanceadas:")
    print(f"   - Duração por chunk: {recorder.chunk_duration}s (com sobreposição)")
    print(f"   - Sobreposição: +1 segundo para contexto")
    print(f"   - Qualidade: Priorizada sobre velocidade")
    print()
    
    # Frases de teste que o usuário deve falar
    test_phrases = [
        "Este é um teste de preservação de palavras",
        "Vamos verificar se todas as palavras são capturadas",
        "Especialmente nas transições entre os chunks de áudio"
    ]
    
    print("💬 INSTRUÇÕES PARA O TESTE:")
    print("   Fale as seguintes frases claramente:")
    for i, phrase in enumerate(test_phrases, 1):
        print(f"   {i}. \"{phrase}\"")
    print()
    
    try:
        print("🎙️ Iniciando teste de preservação (20 segundos)...")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar 20 segundos para capturar pelo menos 2-3 chunks
        for i in range(20):
            time.sleep(1)
            chunks_received = len(received_chunks)
            print(f"   ⏱️ {i+1}/20s - Chunks: {chunks_received}, Palavras únicas: {len(set(all_words))}")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        # Aguardar processamento final
        time.sleep(3)
        
        # Fazer transcrição completa do arquivo final para comparação
        print("\n🔍 Comparando com transcrição completa...")
        full_transcript = transcriber.transcribe(audio_file)
        full_words = full_transcript.lower().split() if full_transcript else []
        
        print(f"\n📊 ANÁLISE DE PRESERVAÇÃO:")
        print(f"   - Arquivo final: {audio_file}")
        print(f"   - Chunks processados: {len(received_chunks)}")
        print(f"   - Palavras por chunks: {len(set(all_words))}")
        print(f"   - Palavras transcrição completa: {len(set(full_words))}")
        
        # Calcular preservação
        if full_words:
            chunk_words_set = set(all_words)
            full_words_set = set(full_words)
            preserved_words = chunk_words_set.intersection(full_words_set)
            preservation_rate = len(preserved_words) / len(full_words_set) * 100
            
            print(f"   - Taxa de preservação: {preservation_rate:.1f}%")
            
            if preservation_rate >= 90:
                print("   ✅ EXCELENTE! Quase todas as palavras preservadas")
            elif preservation_rate >= 75:
                print("   ⚠️ BOM. Algumas palavras podem ter sido perdidas")
            else:
                print("   ❌ PROBLEMÁTICO. Muitas palavras perdidas")
                
            # Mostrar palavras perdidas
            lost_words = full_words_set - chunk_words_set
            if lost_words:
                print(f"   - Palavras perdidas: {list(lost_words)[:10]}...")
            
            print(f"\n📝 TRANSCRIÇÕES:")
            print(f"   - Por chunks: {' '.join([t for _, t in sorted(received_chunks)])}")  
            print(f"   - Completa: {full_transcript}")
            
            return preservation_rate >= 75
        else:
            print("   ❌ Transcrição completa falhou")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    finally:
        try:
            if recorder.recording:
                recorder.stop_recording()
        except:
            pass

if __name__ == "__main__":
    success = test_word_preservation()
    if success:
        print("\n🎉 TESTE DE PRESERVAÇÃO PASSOU!")
        print("💡 Ajustes balanceados mantêm qualidade e velocidade!")
    else:
        print("\n⚠️ Teste indica possível perda de palavras")
        print("💡 Pode ser necessário ajustar configurações")