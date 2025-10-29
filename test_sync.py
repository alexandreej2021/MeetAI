#!/usr/bin/env python3
"""
Script de teste de sincronização de áudio
Testa a latência entre gravação do microfone e áudio do sistema
"""

import time
import threading
from src.audio.recorder import AudioRecorder

def test_synchronization():
    """Testar sincronização de áudio com feedback em tempo real"""
    print("🧪 TESTE DE SINCRONIZAÇÃO DE ÁUDIO")
    print("=" * 50)
    
    recorder = AudioRecorder()
    
    # Configurar para teste de sincronização
    recorder.chunk = 256  # Buffer ainda menor para teste
    
    print("📋 Instruções do teste:")
    print("1. Toque uma música ou faça barulho no computador")
    print("2. Fale no microfone ao mesmo tempo")
    print("3. Observe os alertas de sincronização")
    print("4. Pressione Ctrl+C para parar")
    print()
    
    try:
        if recorder.start_recording():
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                
                # Status a cada 5 segundos
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    print(f"⏱️  Gravando há {elapsed:.0f}s...")
                    
                    if len(recorder.mic_timestamps) > 0 and len(recorder.system_timestamps) > 0:
                        mic_latest = recorder.mic_timestamps[-1] if recorder.mic_timestamps else 0
                        system_latest = recorder.system_timestamps[-1] if recorder.system_timestamps else 0
                        diff = abs(mic_latest - system_latest)
                        
                        if diff < 0.05:
                            print(f"✅ Sincronização boa: {diff:.3f}s")
                        elif diff < 0.1:
                            print(f"⚠️  Sincronização aceitável: {diff:.3f}s")
                        else:
                            print(f"❌ Sincronização ruim: {diff:.3f}s")
                
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🛑 Parando teste...")
        filename = recorder.stop_recording()
        
        if filename:
            print(f"📁 Arquivo de teste salvo: {filename}")
            print("🎧 Reproduza o arquivo para verificar se está sincronizado")
        
        # Estatísticas finais
        if recorder.mic_timestamps and recorder.system_timestamps:
            mic_count = len(recorder.mic_timestamps)
            system_count = len(recorder.system_timestamps)
            
            print(f"\n📊 ESTATÍSTICAS FINAIS:")
            print(f"Chunks do microfone: {mic_count}")
            print(f"Chunks do sistema: {system_count}")
            print(f"Diferença de chunks: {abs(mic_count - system_count)}")
            
            if mic_count > 0 and system_count > 0:
                mic_avg = sum(recorder.mic_timestamps) / len(recorder.mic_timestamps)
                system_avg = sum(recorder.system_timestamps) / len(recorder.system_timestamps)
                avg_diff = abs(mic_avg - system_avg)
                
                print(f"Diferença média de tempo: {avg_diff:.3f}s")
                
                if avg_diff < 0.05:
                    print("✅ RESULTADO: Sincronização excelente!")
                elif avg_diff < 0.1:
                    print("⚠️  RESULTADO: Sincronização aceitável")
                else:
                    print("❌ RESULTADO: Sincronização precisa melhorar")

if __name__ == "__main__":
    test_synchronization()