#!/usr/bin/env python3
"""
Script de diagnóstico para áudio do sistema
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import pyaudio
import sounddevice as sd
import numpy as np

def test_pyaudio_devices():
    """Testar dispositivos PyAudio"""
    print("=== DISPOSITIVOS PYAUDIO ===")
    audio = pyaudio.PyAudio()
    
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {device_info['name']}")
        print(f"  Entrada: {device_info['maxInputChannels']} canais")
        print(f"  Saída: {device_info['maxOutputChannels']} canais")
        print(f"  Taxa padrão: {device_info['defaultSampleRate']}")
        
        # Marcar dispositivos interessantes
        name_lower = device_info['name'].lower()
        if any(keyword in name_lower for keyword in [
            'stereo mix', 'what u hear', 'wave out mix', 'sum', 'loopback'
        ]):
            print("  >>> POSSÍVEL DISPOSITIVO DE SISTEMA <<<")
        print()
    
    audio.terminate()

def test_sounddevice():
    """Testar dispositivos SoundDevice"""
    print("\n=== DISPOSITIVOS SOUNDDEVICE ===")
    
    try:
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            print(f"Device {i}: {device['name']}")
            print(f"  Entrada: {device['max_input_channels']} canais")
            print(f"  Saída: {device['max_output_channels']} canais")
            print(f"  Taxa padrão: {device['default_samplerate']}")
            
            # Marcar dispositivos interessantes
            name_lower = str(device['name']).lower()
            if any(keyword in name_lower for keyword in [
                'stereo mix', 'what u hear', 'wave out mix', 'sum', 'loopback',
                'speakers', 'alto-falantes'
            ]):
                print("  >>> POSSÍVEL DISPOSITIVO DE SISTEMA <<<")
            print()
            
    except Exception as e:
        print(f"Erro ao listar dispositivos sounddevice: {e}")

def test_system_recording():
    """Teste básico de gravação de áudio do sistema"""
    print("\n=== TESTE DE GRAVAÇÃO DO SISTEMA ===")
    
    from src.audio.recorder import AudioRecorder
    
    recorder = AudioRecorder()
    
    # Verificar capacidade
    can_record, message = recorder.check_system_audio_capability()
    print(f"Pode gravar áudio do sistema: {can_record}")
    print(f"Mensagem: {message}")
    
    if can_record:
        print("\n🔍 Testando gravação rápida (3 segundos)...")
        print("Reproduza algum áudio no PC agora!")
        
        # Configurar para gravar apenas áudio do sistema (sem microfone)
        recorder.record_system_audio = True
        
        # Teste de gravação curta
        import time
        
        # Simular início de gravação apenas do sistema
        success = recorder._start_system_audio_recording()
        if success:
            print("✅ Gravação do sistema iniciada")
            time.sleep(3)
            
            # Parar gravação
            recorder.recording = False
            if recorder.system_stream:
                recorder.system_stream.stop_stream()
                recorder.system_stream.close()
            
            if recorder.system_recording_thread and recorder.system_recording_thread.is_alive():
                recorder.system_recording_thread.join(timeout=2.0)
                
            # Verificar se capturou algo
            if recorder.system_audio_frames:
                print(f"✅ Capturou {len(recorder.system_audio_frames)} frames de áudio do sistema")
                
                # Calcular volume médio
                try:
                    all_data = b''.join(recorder.system_audio_frames)
                    audio_array = np.frombuffer(all_data, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_array**2))
                    print(f"Volume médio capturado: {rms:.2f} (máximo: 32767)")
                    
                    if rms > 100:
                        print("🎉 ÁUDIO DO SISTEMA FUNCIONANDO!")
                    else:
                        print("⚠️  Áudio muito baixo - pode não estar capturando corretamente")
                        
                except Exception as e:
                    print(f"Erro ao analisar áudio: {e}")
            else:
                print("❌ Nenhum frame de áudio capturado")
        else:
            print("❌ Falha ao iniciar gravação do sistema")

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE ÁUDIO DO SISTEMA")
    print("=" * 50)
    
    test_pyaudio_devices()
    test_sounddevice()
    test_system_recording()
    
    print("\n" + "=" * 50)
    print("Diagnóstico concluído!")