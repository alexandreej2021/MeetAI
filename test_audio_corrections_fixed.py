#!/usr/bin/env python3
"""
Teste das correções de áudio do MeetAI
"""
import sys
import os
sys.path.insert(0, 'src')

from audio.recorder import AudioRecorder

def test_audio_corrections():
    """Testar correções de áudio"""
    print("🧪 === TESTE DE CORREÇÕES DE ÁUDIO ===\n")
    
    # Criar gravador
    recorder = AudioRecorder()
    
    # Mostrar configurações padrão
    print("📊 Configurações padrão:")
    recorder.diagnose_audio_issues()
    
    # Aplicar correções para o problema relatado
    print("🔧 Aplicando correções otimizadas...")
    recorder.set_audio_gains(mic_gain=1.0, system_gain=0.4)
    recorder.set_echo_reduction(True)
    
    # Mostrar configurações corrigidas
    print("📊 Configurações após correção:")
    recorder.diagnose_audio_issues()
    
    # Analisar arquivo problemático se existir
    problem_file = "data/recording_20251029_105426.wav"
    if os.path.exists(problem_file):
        print(f"🔍 Analisando arquivo problemático...")
        recorder.diagnose_audio_issues(problem_file)
    else:
        print(f"⚠️  Arquivo {problem_file} não encontrado")
    
    print("✅ Teste concluído!")

if __name__ == "__main__":
    test_audio_corrections()