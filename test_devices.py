"""
Script de teste para verificar dispositivos de áudio
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.audio.recorder import AudioRecorder

def test_audio_devices():
    print("🎤 Testando carregamento de dispositivos de áudio...\n")
    
    try:
        recorder = AudioRecorder()
        devices = recorder.get_audio_devices()
        
        print(f"✅ Encontrados {len(devices)} dispositivos de entrada:\n")
        
        for i, device in enumerate(devices, 1):
            print(f"{i}. Índice: {device['index']}")
            print(f"   Nome: {device['name']}")
            print(f"   Canais: {device['channels']}")
            print(f"   Taxa Padrão: {device.get('default_sample_rate', 'N/A')} Hz")
            print()
        
        # Testar dispositivo padrão
        default = recorder.get_default_device()
        if default:
            print(f"🔊 Dispositivo padrão: {default['name']} ({default['channels']} canais)")
        else:
            print("❌ Nenhum dispositivo padrão encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao carregar dispositivos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_devices()