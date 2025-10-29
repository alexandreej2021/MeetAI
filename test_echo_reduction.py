#!/usr/bin/env python3
"""
Teste específico para redução de eco no MeetAI
"""
import sys
import os
sys.path.insert(0, 'src')

from audio.recorder import AudioRecorder
import numpy as np
import wave

def test_echo_reduction():
    """Testar diferentes níveis de redução de eco"""
    print("🧪 === TESTE DE REDUÇÃO DE ECO ===\n")
    
    recorder = AudioRecorder()
    
    # Configurar para modo agressivo
    recorder.set_echo_reduction(True, "aggressive")
    recorder.set_audio_gains(1.0, 0.3)  # Sistema ainda mais baixo
    
    # Mostrar configurações
    print("📊 Configurações para redução de eco:")
    print(f"   - Ganho microfone: {recorder.mic_gain:.1f}x")
    print(f"   - Ganho sistema: {recorder.system_gain:.1f}x") 
    print(f"   - Redução de eco: {recorder.echo_reduction_strength}")
    
    # Simular processamento de eco
    print("\n🔧 Simulando redução de eco...")
    
    # Criar áudio de teste com eco (correlação alta entre canais)
    test_audio = np.random.randint(-1000, 1000, 1000, dtype=np.int16)
    
    # Aplicar redução de eco
    processed = recorder._reduce_echo(test_audio)
    
    # Comparar
    original_rms = np.sqrt(np.mean(test_audio.astype(np.float32)**2))
    processed_rms = np.sqrt(np.mean(processed.astype(np.float32)**2))
    
    print(f"   RMS original: {original_rms:.0f}")
    print(f"   RMS processado: {processed_rms:.0f}")
    print(f"   Redução: {((original_rms - processed_rms) / original_rms * 100):.1f}%")
    
    # Salvar configurações
    recorder.save_audio_settings()
    
    print("\n✅ Configurações otimizadas para redução de eco aplicadas!")
    print("\n💡 DICAS ADICIONAIS:")
    print("   - Verifique se o Stereo Mix não está duplicando entrada")
    print("   - Considere usar apenas microfone se eco persistir")
    print("   - Ajuste volume do sistema Windows para 50-70%")

if __name__ == "__main__":
    test_echo_reduction()