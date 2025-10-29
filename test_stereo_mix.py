#!/usr/bin/env python3
"""
Teste final para áudio do sistema - usando PyAudio diretamente
"""

import sys
import os
sys.path.insert(0, os.getcwd())

import pyaudio
import numpy as np
import time
import threading

def test_stereo_mix_pyaudio():
    """Testar Stereo Mix usando PyAudio diretamente"""
    print("🔧 TESTE DIRETO DO STEREO MIX")
    print("=" * 50)
    
    audio = pyaudio.PyAudio()
    
    # Primeiro, listar todos os dispositivos de entrada
    print("🔍 Procurando por dispositivos de entrada:")
    input_devices = []
    
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            input_devices.append((i, device_info))
            print(f"   Device {i}: {device_info['name']} ({device_info['maxInputChannels']} canais)")
    
    # Encontrar Mixagem estéreo
    stereo_mix_device = None
    for i, device_info in input_devices:
        device_name = device_info['name'].lower()
        
        if any(keyword in device_name for keyword in [
            'mixagem estéreo', 'mixagem estereo', 'mixagem estÃ©reo', 
            'stereo mix', 'what u hear', 'wave out mix'
        ]):
            stereo_mix_device = i
            print(f"\n✅ Encontrou Stereo Mix: {device_info['name']}")
            print(f"   Device Index: {i}")
            print(f"   Canais: {device_info['maxInputChannels']}")
            print(f"   Taxa padrão: {device_info['defaultSampleRate']}")
            break
    
    if stereo_mix_device is None:
        # Tentar forçadamente o Device 22 que vimos na listagem
        for i, device_info in input_devices:
            if i == 22:  # Device que vimos como "Mixagem estéreo"
                stereo_mix_device = i
                print(f"\n🔄 Tentando Device 22 (Mixagem estéreo): {device_info['name']}")
                break
    
    if stereo_mix_device is None:
        print("❌ Stereo Mix não encontrado!")
        audio.terminate()
        return False
    
    # Testar gravação
    frames = []
    
    def callback(in_data, frame_count, time_info, status):
        if len(frames) < 150:  # ~3 segundos a 44100Hz
            frames.append(in_data)
            
            # Verificar se há sinal
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            volume = np.max(np.abs(audio_data))
            if len(frames) % 20 == 0:  # Log periodicamente
                print(f"📊 Volume: {volume} (frame {len(frames)})")
            
        return (in_data, pyaudio.paContinue)
    
    try:
        print("\n🎵 REPRODUZA ÁUDIO AGORA! (3 segundos)")
        print("   - Abra YouTube, Spotify, ou qualquer player")
        print("   - Certifique-se que o áudio está audível")
        
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            input_device_index=stereo_mix_device,
            frames_per_buffer=1024,
            stream_callback=callback
        )
        
        stream.start_stream()
        
        # Aguardar 3 segundos
        time.sleep(3)
        
        stream.stop_stream()
        stream.close()
        
        # Analisar resultados
        if frames:
            print(f"\n✅ Capturou {len(frames)} frames")
            
            # Analisar volume geral
            all_data = b''.join(frames)
            audio_array = np.frombuffer(all_data, dtype=np.int16)
            
            max_volume = np.max(np.abs(audio_array))
            rms_volume = np.sqrt(np.mean(audio_array**2))
            
            print(f"📊 Volume máximo: {max_volume}")
            print(f"📊 Volume RMS: {rms_volume:.2f}")
            
            if max_volume > 100:
                print("🎉 ÁUDIO DO SISTEMA FUNCIONANDO!")
                return True
            else:
                print("⚠️  Volume muito baixo - possivelmente não está captando")
                return False
        else:
            print("❌ Nenhum frame capturado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False
    
    finally:
        audio.terminate()

def show_setup_instructions():
    """Mostrar instruções detalhadas"""
    print("\n" + "=" * 60)
    print("📋 INSTRUÇÕES PARA HABILITAR STEREO MIX")
    print("=" * 60)
    
    instructions = """
1. 🎛️  HABILITAR STEREO MIX:
   - Clique direito no ícone de som (canto inferior direito)
   - Selecione "Configurações de som"
   - Role para baixo e clique em "Painel de som"
   - Vá para a aba "Gravação"
   - Clique direito no espaço vazio e marque:
     ☑ Mostrar dispositivos desabilitados
     ☑ Mostrar dispositivos desconectados
   - Se aparecer "Stereo Mix" ou "Mixagem estéreo":
     - Clique direito nele > "Habilitar"
     - Clique direito novamente > "Definir como dispositivo padrão"
     - Ajuste o volume se necessário

2. 🔊 ALTERNATIVAS SE STEREO MIX NÃO ESTIVER DISPONÍVEL:
   - Use cabo P2: Saída de fone → Entrada de microfone
   - Software VoiceMeeter: https://voicemeeter.com/
   - VB-Audio Virtual Cable: https://vb-audio.com/Cable/
   - OBS Virtual Audio Output

3. 🎵 TESTE:
   - Execute este script novamente
   - Reproduza música/vídeo durante o teste
   - Volume do sistema deve estar > 20%

4. 🔧 SOLUÇÃO DE PROBLEMAS:
   - Reinicie o PC após habilitar Stereo Mix
   - Verifique se o driver Realtek está atualizado
   - Alguns PCs/notebooks não suportam Stereo Mix
   """
   
    print(instructions)

if __name__ == "__main__":
    success = test_stereo_mix_pyaudio()
    
    if not success:
        show_setup_instructions()
    else:
        print("\n🎉 Stereo Mix está funcionando perfeitamente!")
        print("🚀 O MeetAI poderá gravar áudio do sistema!")