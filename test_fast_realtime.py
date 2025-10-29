#!/usr/bin/env python3
"""
Teste de velocidade da transcrição em tempo real otimizada
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

def test_fast_realtime_transcription():
    """Testar transcrição em tempo real otimizada"""
    print("⚡ TESTE DE TRANSCRIÇÃO EM TEMPO REAL OTIMIZADA")
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
    chunk_times = []
    
    def realtime_callback(chunk_file, chunk_number):
        """Callback de teste com medição de tempo"""
        start_time = time.time()
        print(f"📥 Processando chunk {chunk_number}...")
        
        try:
            # Transcrever o chunk
            transcript = transcriber.transcribe(chunk_file)
            processing_time = time.time() - start_time
            
            if transcript:
                received_chunks.append((chunk_number, transcript))
                chunk_times.append(processing_time)
                print(f"✅ Chunk {chunk_number} - {processing_time:.1f}s - {len(transcript)} chars")
                print(f"   📝 \"{transcript[:60]}{'...' if len(transcript) > 60 else ''}\"")
            else:
                print(f"❌ Chunk {chunk_number} vazio - {processing_time:.1f}s")
                
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Erro chunk {chunk_number} - {processing_time:.1f}s: {e}")
    
    # Configurar callback
    recorder.set_realtime_transcription_callback(realtime_callback)
    
    print(f"⚙️ Configurações otimizadas:")
    print(f"   - Duração por chunk: {recorder.chunk_duration}s (REDUZIDO!)")
    print(f"   - Taxa de amostragem: {recorder.rate}Hz")
    print(f"   - Canais: {recorder.channels}")
    print(f"   - Processamento: Mixagem rápida ativada")
    print()
    
    try:
        print("🎙️ Iniciando gravação otimizada (12 segundos)...")
        print("   💬 Fale naturalmente para testar chunks rápidos!")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar 12 segundos (deve gerar 3 chunks de 4s)
        for i in range(12):
            time.sleep(1)
            chunks_expected = (i + 1) // recorder.chunk_duration
            chunks_received = len(received_chunks)
            print(f"   ⏱️ {i+1}/12s - Esperado: {chunks_expected} chunks, Recebido: {chunks_received}")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        # Aguardar processamento final
        time.sleep(3)
        
        print(f"\n📊 RESULTADOS DA OTIMIZAÇÃO:")
        print(f"   - Arquivo final: {audio_file}")
        print(f"   - Chunks processados: {len(received_chunks)}")
        
        if chunk_times:
            avg_time = sum(chunk_times) / len(chunk_times)
            max_time = max(chunk_times)
            min_time = min(chunk_times)
            print(f"   - Tempo médio por chunk: {avg_time:.1f}s")
            print(f"   - Tempo máximo: {max_time:.1f}s")
            print(f"   - Tempo mínimo: {min_time:.1f}s")
            
            if avg_time < 3.0:
                print(f"   ✅ EXCELENTE! Processamento mais rápido que chunk (4s)")
            elif avg_time < 5.0:
                print(f"   ⚠️ BOM. Processamento ligeiramente mais lento que chunk")
            else:
                print(f"   ❌ LENTO. Processamento muito mais lento que chunk")
        
        if received_chunks:
            print(f"   - Transcrição completa:")
            full_transcript = " ".join([transcript for _, transcript in sorted(received_chunks)])
            print(f"     📝 {full_transcript}")
            print(f"   - Total de caracteres: {len(full_transcript)}")
            return len(received_chunks) >= 2  # Pelo menos 2 chunks processados
        else:
            print("   ❌ Nenhum chunk foi processado")
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
    success = test_fast_realtime_transcription()
    if success:
        print("\n🚀 OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("💡 Chunks de 4 segundos oferecem transcrição mais responsiva!")
        print("⚡ A aplicação agora deve ser muito mais rápida!")
    else:
        print("\n💥 Teste de otimização falhou!")