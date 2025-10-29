#!/usr/bin/env python3
"""
Teste da funcionalidade de transcrição em tempo real
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

def test_realtime_transcription():
    """Testar transcrição em tempo real"""
    print("🧪 TESTE DE TRANSCRIÇÃO EM TEMPO REAL")
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
    
    def realtime_callback(chunk_file, chunk_number):
        """Callback de teste"""
        print(f"📥 Recebido chunk {chunk_number}: {chunk_file}")
        
        try:
            # Simular transcrição
            transcript = transcriber.transcribe(chunk_file)
            if transcript:
                received_chunks.append((chunk_number, transcript))
                print(f"✅ Chunk {chunk_number} transcrito: {len(transcript)} chars")
                print(f"   Texto: {transcript[:100]}...")
            else:
                print(f"❌ Falha na transcrição do chunk {chunk_number}")
        except Exception as e:
            print(f"❌ Erro ao transcrever chunk {chunk_number}: {e}")
    
    # Configurar callback
    recorder.set_realtime_transcription_callback(realtime_callback)
    
    # Configurar para chunks menores para teste
    recorder.chunk_duration = 5  # 5 segundos por chunk
    
    print(f"⚙️ Configurações:")
    print(f"   - Duração por chunk: {recorder.chunk_duration}s")
    print(f"   - Taxa de amostragem: {recorder.rate}Hz")
    print(f"   - Canais: {recorder.channels}")
    print()
    
    try:
        print("🎙️ Iniciando gravação de teste (15 segundos)...")
        print("   💬 Fale algo para testar a transcrição em tempo real!")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar 15 segundos
        for i in range(15):
            time.sleep(1)
            print(f"   ⏱️ {i+1}/15s - Chunks recebidos: {len(received_chunks)}")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        # Aguardar processamento final
        time.sleep(2)
        
        print(f"\n📊 RESULTADOS:")
        print(f"   - Arquivo final: {audio_file}")
        print(f"   - Chunks processados: {len(received_chunks)}")
        
        if received_chunks:
            print(f"   - Transcrição completa:")
            full_transcript = " ".join([transcript for _, transcript in sorted(received_chunks)])
            print(f"     {full_transcript}")
            print(f"   - Total de caracteres: {len(full_transcript)}")
            return True
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
    success = test_realtime_transcription()
    if success:
        print("\n🎉 Teste de transcrição em tempo real PASSOU!")
        print("💡 A funcionalidade está pronta para uso na aplicação!")
    else:
        print("\n💥 Teste FALHOU!")