#!/usr/bin/env python3
"""
Teste rápido das correções de áudio
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from src.audio.recorder import AudioRecorder
import time

def test_audio_corrections():
    """Testar as correções de sample rate e volume"""
    print("🔧 TESTE DAS CORREÇÕES DE ÁUDIO")
    print("=" * 50)
    
    recorder = AudioRecorder()
    
    print("🎵 REPRODUZA ÁUDIO NO PC AGORA!")
    print("   - Abra YouTube, Spotify, etc.")
    print("   - Volume moderado (não muito alto)")
    print("   - Gravação de 5 segundos...")
    
    # Iniciar gravação
    success = recorder.start_recording()
    
    if success:
        print("✅ Gravação iniciada")
        
        # Aguardar 5 segundos
        for i in range(5, 0, -1):
            print(f"⏳ {i} segundos restantes...")
            time.sleep(1)
        
        # Parar gravação
        filename = recorder.stop_recording()
        
        if filename:
            print(f"✅ Gravação salva: {filename}")
            
            # Verificar propriedades do arquivo
            import wave
            with wave.open(filename, 'rb') as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                duration = frames / sample_rate
                
                print(f"📊 PROPRIEDADES DO ARQUIVO:")
                print(f"   - Taxa de amostragem: {sample_rate} Hz")
                print(f"   - Canais: {channels}")
                print(f"   - Duração: {duration:.2f} segundos")
                print(f"   - Frames totais: {frames}")
                
                if sample_rate == 44100:
                    print("✅ Sample rate correto!")
                else:
                    print(f"⚠️  Sample rate inesperado: {sample_rate}")
                    
                if duration >= 4.5:
                    print("✅ Duração adequada!")
                else:
                    print(f"⚠️  Duração muito curta: {duration:.2f}s")
            
            print(f"\n🎵 Para testar o áudio:")
            print(f"   - Abra o arquivo: {filename}")
            print(f"   - Verifique se o volume está bom")
            print(f"   - Verifique se a velocidade está normal")
            
        else:
            print("❌ Falha ao salvar gravação")
    else:
        print("❌ Falha ao iniciar gravação")

if __name__ == "__main__":
    test_audio_corrections()