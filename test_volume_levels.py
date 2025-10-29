#!/usr/bin/env python3
"""
Teste de níveis de volume do microfone vs sistema
"""

import time
import numpy as np
from src.audio.recorder import AudioRecorder

def test_volume_levels():
    """Testar níveis de volume entre microfone e sistema"""
    print("🔊 TESTE DE NÍVEIS DE VOLUME")
    print("=" * 40)
    
    recorder = AudioRecorder()
    
    print("📋 Instruções:")
    print("1. Fale no microfone em volume normal")
    print("2. Reproduza música/vídeo no computador")
    print("3. O teste gravará por 10 segundos")
    print("4. NOVO: Microfone amplificado 2.5x, Sistema 0.7x")
    print("5. Depois mostrará os níveis de volume detectados")
    print()
    
    try:
        if recorder.start_recording():
            print("✅ Gravação iniciada - monitorando volumes...")
            
            # Gravar por 120 segundos com monitoramento
            for i in range(20):
                time.sleep(1)
                print(f"⏱️  {i+1}s...", end="")
                
                # A cada 3 segundos, mostrar estatísticas de volume
                if (i+1) % 3 == 0:
                    mic_chunks = len(recorder.mic_frames) if hasattr(recorder, 'mic_frames') else 0
                    sys_chunks = len(recorder.system_audio_frames) if hasattr(recorder, 'system_audio_frames') else 0
                    print(f" | Mic chunks: {mic_chunks}, Sys chunks: {sys_chunks}")
                else:
                    print()
            
            print("\n🛑 Finalizando gravação...")
            filename = recorder.stop_recording()
            
            if filename:
                print(f"📁 Arquivo salvo: {filename}")
                
                # Analisar o arquivo gerado
                analyze_audio_levels(filename)
                
            else:
                print("❌ Erro ao salvar arquivo")
        else:
            print("❌ Falha ao iniciar gravação")
    
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

def analyze_audio_levels(filename):
    """Analisar níveis de volume do arquivo gravado"""
    try:
        import wave
        
        print(f"\n📊 ANÁLISE DE NÍVEIS DE VOLUME")
        print("=" * 40)
        
        with wave.open(filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
            # Para áudio estéreo, separar canais
            if wf.getnchannels() == 2:
                left_channel = audio_data[0::2]
                right_channel = audio_data[1::2]
                
                left_rms = np.sqrt(np.mean(left_channel**2))
                right_rms = np.sqrt(np.mean(right_channel**2))
                left_peak = np.max(np.abs(left_channel))
                right_peak = np.max(np.abs(right_channel))
                
                print(f"🔊 Canal Esquerdo:")
                print(f"   RMS: {left_rms:.2f}")
                print(f"   Pico: {left_peak}")
                print(f"   % da faixa: {(left_peak/32767)*100:.1f}%")
                
                print(f"\n🔊 Canal Direito:")
                print(f"   RMS: {right_rms:.2f}")
                print(f"   Pico: {right_peak}")
                print(f"   % da faixa: {(right_peak/32767)*100:.1f}%")
                
                # Determinar qual fonte está mais alta
                total_rms = np.sqrt(np.mean(audio_data**2))
                total_peak = np.max(np.abs(audio_data))
                
                print(f"\n📈 GERAL:")
                print(f"   RMS Total: {total_rms:.2f}")
                print(f"   Pico Total: {total_peak}")
                print(f"   % da faixa: {(total_peak/32767)*100:.1f}%")
                
                if total_peak > 20000:
                    print("✅ Boa utilização da faixa dinâmica!")
                elif total_peak > 10000:
                    print("⚠️  Volume moderado - pode aumentar")
                else:
                    print("❌ Volume muito baixo - precisa amplificar")
            
            else:  # Mono
                rms = np.sqrt(np.mean(audio_data**2))
                peak = np.max(np.abs(audio_data))
                
                print(f"🔊 Volume (Mono):")
                print(f"   RMS: {rms:.2f}")
                print(f"   Pico: {peak}")
                print(f"   % da faixa: {(peak/32767)*100:.1f}%")
    
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

if __name__ == "__main__":
    test_volume_levels()