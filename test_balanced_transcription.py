#!/usr/bin/env python3
"""
Teste final do equilíbrio entre velocidade e qualidade
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

def test_balanced_transcription():
    """Testar transcrição balanceada (8s + 2s overlap)"""
    print("⚖️ TESTE DE TRANSCRIÇÃO BALANCEADA")
    print("=" * 70)
    
    # Inicializar componentes
    recorder = AudioRecorder()
    transcriber = Transcriber()
    
    if not transcriber.client:
        print("❌ OpenAI não configurado")
        return False
    
    print("✅ Componentes inicializados")
    
    # Variáveis de teste
    received_chunks = []
    processing_times = []
    
    def realtime_callback(chunk_file, chunk_number):
        """Callback balanceado"""
        start_time = time.time()
        print(f"📥 Chunk {chunk_number} iniciado...")
        
        try:
            transcript = transcriber.transcribe(chunk_file)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            if transcript:
                received_chunks.append((chunk_number, transcript))
                print(f"✅ Chunk {chunk_number} - {processing_time:.1f}s")
                print(f"   📝 \"{transcript}\"")
            else:
                print(f"❌ Chunk {chunk_number} vazio - {processing_time:.1f}s")
                
        except Exception as e:
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            print(f"❌ Erro chunk {chunk_number} - {processing_time:.1f}s: {e}")
    
    # Configurar callback
    recorder.set_realtime_transcription_callback(realtime_callback)
    
    print(f"⚙️ Configurações BALANCEADAS:")
    print(f"   - Duração do chunk: {recorder.chunk_duration}s")
    print(f"   - Sobreposição: 2s (para contexto)")
    print(f"   - Total por chunk: 10s de áudio")
    print(f"   - Objetivo: Qualidade SEM perder velocidade")
    print()
    
    try:
        print("🎙️ Iniciando teste balanceado (16 segundos)...")
        print("   💬 Fale de forma natural e contínua!")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar 16 segundos (deve gerar 2 chunks de 8s)
        for i in range(16):
            time.sleep(1)
            chunks_expected = (i + 1) // recorder.chunk_duration
            chunks_received = len(received_chunks)
            print(f"   ⏱️ {i+1}/16s - Esperado: {chunks_expected}, Recebido: {chunks_received}")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        # Aguardar processamento final
        time.sleep(3)
        
        # Transcrição completa para comparação
        print("\n🔍 Fazendo transcrição completa...")
        full_transcript = transcriber.transcribe(audio_file)
        
        print(f"\n📊 AVALIAÇÃO DO EQUILÍBRIO:")
        print(f"   - Arquivo final: {audio_file}")
        print(f"   - Chunks processados: {len(received_chunks)}")
        
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            print(f"   - Tempo médio: {avg_time:.1f}s")
            
            if avg_time <= 6:
                print("   ✅ VELOCIDADE: Excelente!")
            elif avg_time <= 10:
                print("   ⚠️ VELOCIDADE: Aceitável")
            else:
                print("   ❌ VELOCIDADE: Lenta demais")
        
        # Comparar qualidade
        if received_chunks and full_transcript:
            chunk_text = " ".join([transcript for _, transcript in sorted(received_chunks)])
            chunk_words = set(chunk_text.lower().split())
            full_words = set(full_transcript.lower().split())
            
            if full_words:
                preservation = len(chunk_words.intersection(full_words)) / len(full_words) * 100
                print(f"   - Preservação: {preservation:.1f}%")
                
                if preservation >= 85:
                    print("   ✅ QUALIDADE: Excelente!")
                elif preservation >= 70:
                    print("   ⚠️ QUALIDADE: Boa")
                else:
                    print("   ❌ QUALIDADE: Problemática")
                
                print(f"\n📝 COMPARAÇÃO:")
                print(f"   - Chunks: \"{chunk_text}\"")
                print(f"   - Completo: \"{full_transcript}\"")
                
                # Sucesso se velocidade OK e qualidade boa
                speed_ok = avg_time <= 10 if processing_times else False
                quality_ok = preservation >= 70
                return speed_ok and quality_ok
        
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
    success = test_balanced_transcription()
    if success:
        print("\n🎯 EQUILÍBRIO PERFEITO ALCANÇADO!")
        print("✅ Velocidade adequada + Qualidade preservada")
        print("💡 Configuração de 8s + 2s overlap é ideal!")
    else:
        print("\n⚠️ Equilíbrio precisa de mais ajustes")
        print("💡 Pode ser necessário testar outras configurações")