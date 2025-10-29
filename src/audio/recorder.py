"""
Módulo de gravação de áudio
Grava áudio do sistema e microfone simultaneamente
"""

import pyaudio
import wave
import threading
import time
from datetime import datetime
import os
import numpy as np
import sounddevice as sd

class AudioRecorder:
    def __init__(self):
        self.chunk = 512  # Reduzido para menor latência (era 1024)
        self.format = pyaudio.paInt16
        self.channels = 2  # Tenta 2 canais, mas ajusta se necessário
        self.rate = 44100
        self.recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.input_device_index = None  # Device específico ou None para padrão
        
        # Para gravação de áudio do sistema
        self.system_audio_frames = []
        self.mic_frames = []
        self.system_stream = None
        self.mic_stream = None
        
        # Transcrição em tempo real DESABILITADA (por preferência do usuário)
        self.realtime_callback = None
        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.system_recording_thread = None
        self.record_system_audio = True  # Flag para incluir áudio do sistema
        
        # Para sincronização
        self.recording_start_time = None
        self.mic_timestamps = []
        self.system_timestamps = []
        
        # Configurações de áudio otimizadas para evitar estouro
        self.mic_gain = 1.0  # Ganho do microfone (otimizado)
        self.system_gain = 0.4  # Ganho do sistema (otimizado)
        self.enable_echo_reduction = True  # Habilitar redução de eco
        
        # Carregar configurações salvas se existirem
        self._load_audio_settings()
        
    def get_audio_devices(self):
        """Listar dispositivos de áudio disponíveis"""
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            # Só listar dispositivos que suportam entrada (microfones)
            if device_info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'default_sample_rate': device_info.get('defaultSampleRate', 44100)
                })
        return devices
    
    def get_system_audio_devices(self):
        """Listar dispositivos de saída (para capturar áudio do sistema)"""
        devices = []
        try:
            # Usar sounddevice para listar dispositivos
            sd_devices = sd.query_devices()
            for i, device_info in enumerate(sd_devices):
                # Procurar por dispositivos de saída que podem ser usados como entrada (loopback)
                if device_info['max_output_channels'] > 0:
                    # Adicionar dispositivos que suportam WASAPI loopback
                    if 'WASAPI' in str(device_info) or 'Speakers' in device_info['name'] or 'Alto-falantes' in device_info['name']:
                        devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['max_output_channels'],
                            'sample_rate': device_info['default_samplerate']
                        })
        except Exception as e:
            print(f"Erro ao listar dispositivos de sistema: {e}")
        return devices
    
    def set_input_device(self, device_index):
        """Definir dispositivo de entrada específico"""
        self.input_device_index = device_index
    
    def set_audio_gains(self, mic_gain=1.2, system_gain=0.5):
        """Configurar ganhos de áudio para evitar estouro"""
        self.mic_gain = max(0.1, min(mic_gain, 3.0))  # Limitar entre 0.1 e 3.0
        self.system_gain = max(0.1, min(system_gain, 2.0))  # Limitar entre 0.1 e 2.0
        print(f"⚙️  Ganhos configurados: Microfone={self.mic_gain:.1f}x, Sistema={self.system_gain:.1f}x")
    
    def set_echo_reduction(self, enabled=True):
        """Habilitar/desabilitar redução de eco"""
        self.enable_echo_reduction = enabled
        print(f"🔊 Redução de eco: {'Habilitada' if enabled else 'Desabilitada'}")
    
    def diagnose_audio_issues(self, audio_file=None):
        """Diagnosticar problemas comuns de áudio"""
        print("\n🔍 === DIAGNÓSTICO DE ÁUDIO ===")
        
        # Verificar configurações atuais
        print(f"⚙️  Configurações atuais:")
        print(f"   - Ganho microfone: {self.mic_gain:.1f}x")
        print(f"   - Ganho sistema: {self.system_gain:.1f}x")
        print(f"   - Redução de eco: {'Sim' if self.enable_echo_reduction else 'Não'}")
        print(f"   - Taxa de amostragem: {self.rate}Hz")
        print(f"   - Canais: {self.channels}")
        
        # Verificar dispositivos
        print(f"\n🎤 Dispositivo atual: {self.input_device_index or 'Padrão do sistema'}")
        
        # Recomendações baseadas nos problemas relatados
        print(f"\n💡 RECOMENDAÇÕES PARA SEU PROBLEMA:")
        print(f"   📢 MICROFONE ESTOURANDO:")
        print(f"      - Ganho atual: {self.mic_gain:.1f}x (Bom se < 1.5)")
        if self.mic_gain > 1.5:
            print(f"      ⚠️  AÇÃO: Reduzir ganho do microfone")
            recommended_mic = min(1.0, self.mic_gain * 0.7)
            print(f"      ✅ Sugestão: {recommended_mic:.1f}x")
        
        print(f"\n   🔊 ECO NO ÁUDIO DO SISTEMA:")
        print(f"      - Redução de eco: {'Ativa' if self.enable_echo_reduction else 'INATIVA'}")
        print(f"      - Ganho sistema: {self.system_gain:.1f}x")
        if not self.enable_echo_reduction:
            print(f"      ⚠️  AÇÃO: Habilitar redução de eco")
        if self.system_gain > 0.6:
            print(f"      ⚠️  AÇÃO: Reduzir ganho do sistema")
            recommended_sys = min(0.4, self.system_gain * 0.8)
            print(f"      ✅ Sugestão: {recommended_sys:.1f}x")
        
        # Análise do arquivo se fornecido
        if audio_file and os.path.exists(audio_file):
            try:
                print(f"\n📁 Analisando arquivo: {audio_file}")
                with wave.open(audio_file, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    
                    # Estatísticas básicas
                    max_val = np.max(np.abs(audio_data))
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                    
                    print(f"   - Pico máximo: {max_val}/32767 ({max_val/32767*100:.1f}%)")
                    print(f"   - RMS médio: {rms:.0f}")
                    
                    if max_val > 30000:
                        print(f"   ⚠️  CLIPPING DETECTADO! Áudio está estourando")
                    elif max_val < 5000:
                        print(f"   ⚠️  Áudio muito baixo")
                    else:
                        print(f"   ✅ Nível de áudio adequado")
                        
            except Exception as e:
                print(f"   ❌ Erro ao analisar arquivo: {e}")
        
        print(f"\n🔧 COMANDOS PARA CORRIGIR:")
        print(f"   recorder.set_audio_gains({min(1.0, self.mic_gain*0.8):.1f}, {min(0.4, self.system_gain*0.8):.1f})")
        print(f"   recorder.set_echo_reduction(True)")
        print(f"=== FIM DO DIAGNÓSTICO ===\n")
    
    def _load_audio_settings(self):
        """Carregar configurações de áudio salvas"""
        try:
            import json
            from pathlib import Path
            
            settings_file = Path("config/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Carregar configurações de áudio
                audio_config = settings.get('audio', {})
                
                # Aplicar configurações se existirem
                if 'mic_gain' in audio_config:
                    self.mic_gain = max(0.1, min(audio_config['mic_gain'], 3.0))
                
                if 'system_gain' in audio_config:
                    self.system_gain = max(0.1, min(audio_config['system_gain'], 2.0))
                
                if 'echo_reduction' in audio_config:
                    self.enable_echo_reduction = audio_config['echo_reduction']
                
                print(f"⚙️  Configurações de áudio carregadas: Mic={self.mic_gain:.1f}x, Sistema={self.system_gain:.1f}x, Eco={'On' if self.enable_echo_reduction else 'Off'}")
                
        except Exception as e:
            print(f"⚠️  Erro ao carregar configurações de áudio: {e}")
    
    def save_audio_settings(self):
        """Salvar configurações de áudio atuais"""
        try:
            import json
            from pathlib import Path
            
            # Criar diretório se não existir
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            settings_file = config_dir / "settings.json"
            
            # Carregar configurações existentes ou criar novas
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # Garantir que existe seção de áudio
            if 'audio' not in settings:
                settings['audio'] = {}
            
            # Atualizar configurações de áudio
            settings['audio']['mic_gain'] = self.mic_gain
            settings['audio']['system_gain'] = self.system_gain
            settings['audio']['echo_reduction'] = self.enable_echo_reduction
            
            # Salvar arquivo
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"💾 Configurações de áudio salvas!")
            
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
    
    def set_realtime_transcription_callback(self, callback):
        """Definir callback para transcrição em tempo real"""
        self.realtime_callback = callback
        
    def get_default_device(self):
        """Obter dispositivo de entrada padrão"""
        try:
            default_device = self.audio.get_default_input_device_info()
            return {
                'index': default_device['index'],
                'name': default_device['name'],
                'channels': default_device['maxInputChannels']
            }
        except:
            return None
    
    def start_recording(self):
        """Iniciar gravação de áudio (microfone + sistema)"""
        if self.recording:
            return False
            
        self.frames = []
        self.mic_frames = []
        self.system_audio_frames = []
        self.mic_timestamps = []
        self.system_timestamps = []
        self.recording_start_time = time.time()
        self.recording = True
        
        try:
            # 1. Iniciar gravação do microfone
            success_mic = self._start_microphone_recording()
            if not success_mic:
                print("Falha ao iniciar gravação do microfone")
                self.recording = False
                return False
            
            # 2. Tentar iniciar gravação do áudio do sistema
            if self.record_system_audio:
                success_system = self._start_system_audio_recording()
                if not success_system:
                    print("Aviso: Não foi possível capturar áudio do sistema, gravando apenas microfone")
            
            print("Gravação iniciada - Microfone + Áudio do Sistema")
            print("⚡ Configurações de baixa latência ativadas")
            
            # Iniciar thread de monitoramento de sincronização
            self.sync_monitor_thread = threading.Thread(target=self._monitor_sync, daemon=True)
            self.sync_monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar gravação: {e}")
            self.recording = False
            return False
    
    def _start_microphone_recording(self):
        """Iniciar gravação do microfone"""
        try:
            # Tenta abrir com 2 canais, se falhar tenta 1 canal
            try:
                self.mic_stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk,
                    stream_callback=self._mic_callback,
                    # Configurações para reduzir latência
                    input_host_api_specific_stream_info=None
                )
            except Exception as e:
                print(f"Tentando microfone com 1 canal devido ao erro: {e}")
                self.channels = 1
                self.mic_stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk,
                    stream_callback=self._mic_callback,
                    # Configurações para reduzir latência
                    input_host_api_specific_stream_info=None
                )
            
            self.mic_stream.start_stream()
            
            # Mostrar qual dispositivo está sendo usado
            if self.input_device_index is not None:
                device_info = self.audio.get_device_info_by_index(self.input_device_index)
                print(f"Microfone: {device_info['name']}")
            else:
                print("Microfone: Dispositivo padrão")
                
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar gravação do microfone: {e}")
            return False
    
    def _start_system_audio_recording(self):
        """Iniciar gravação do áudio do sistema usando sounddevice"""
        try:
            # Usar sounddevice para capturar áudio do sistema no Windows
            # Procurar por dispositivo loopback ou stereo mix
            loopback_device = self._find_loopback_device()
            
            if loopback_device is not None:
                # Usar sounddevice em thread separada
                self.system_recording_thread = threading.Thread(
                    target=self._record_system_audio_thread,
                    args=(loopback_device,)
                )
                self.system_recording_thread.daemon = True
                self.system_recording_thread.start()
                print(f"Áudio do sistema: Dispositivo {loopback_device}")
                return True
            else:
                # Fallback: tentar capturar usando WASAPI via PyAudio
                return self._start_system_audio_wasapi()
                
        except Exception as e:
            print(f"Erro ao iniciar gravação do sistema: {e}")
            return False
    
    def _find_loopback_device(self):
        """Encontrar dispositivo de loopback no Windows"""
        try:
            devices = sd.query_devices()
            
            # Primeira prioridade: Mixagem estéreo (Stereo Mix em português)
            for i, device in enumerate(devices):
                device_name = str(device['name']).lower()
                
                if any(keyword in device_name for keyword in [
                    'mixagem estéreo', 'mixagem estereo', 'mixagem estÃ©reo',
                    'stereo mix', 'what u hear', 'wave out mix'
                ]):
                    if device['max_input_channels'] > 0:
                        print(f"🎯 Encontrou Stereo Mix: {device['name']}")
                        return i
            
            # Segunda prioridade: outros dispositivos de loopback
            for i, device in enumerate(devices):
                device_name = str(device['name']).lower()
                
                if any(keyword in device_name for keyword in [
                    'sum', 'loopback'
                ]):
                    if device['max_input_channels'] > 0:
                        print(f"🎯 Encontrou dispositivo loopback: {device['name']}")
                        return i
            
            # Terceira prioridade: dispositivos que permitem entrada/saída
            for i, device in enumerate(devices):
                device_name = str(device['name']).lower()
                
                # Procurar por alto-falantes que também tenham entrada
                if 'alto-falante' in device_name or 'speakers' in device_name:
                    if device['max_input_channels'] > 0:
                        print(f"🎯 Encontrou alto-falante com entrada: {device['name']}")
                        return i
                        
            return None
            
        except Exception as e:
            print(f"Erro ao procurar dispositivo de loopback: {e}")
            return None
    
    def _record_system_audio_thread(self, device_index):
        """Thread para gravar áudio do sistema usando sounddevice"""
        try:
            # Obter informações do dispositivo para determinar canais corretos
            device_info = sd.query_devices(device_index)
            available_channels = device_info['max_input_channels']
            
            # Usar o número correto de canais (preferir 2, mas aceitar 1)
            channels = min(2, available_channels) if available_channels > 0 else 2
            
            # CORREÇÃO: Forçar usar a mesma taxa do microfone para evitar problemas de sync
            device_rate = int(device_info['default_samplerate'])
            sample_rate = self.rate  # Usar sempre a taxa do microfone (44100Hz)
            
            print(f"📡 Iniciando captura - Dispositivo: {device_info['name']}")
            print(f"📡 Canais: {channels}, Taxa: {sample_rate} Hz (forçada de {device_rate} para sincronização)")
            
            frame_count = 0
            
            def callback(indata, frames, time, status):
                nonlocal frame_count
                if self.recording:
                    try:
                        # Debug: verificar se está recebendo dados
                        frame_count += 1
                        if frame_count % 50 == 0:  # Log a cada ~1 segundo
                            volume = np.max(np.abs(indata)) if len(indata) > 0 else 0
                            print(f"📊 Frame {frame_count}: Volume máximo = {volume:.4f}")
                        
                        # Sempre adicionar frame (mesmo se silêncio) para manter sincronização
                        # Converter para o formato usado pelo PyAudio (int16)
                        audio_data = (indata * 32767).astype(np.int16)
                        
                        # Se foi gravado em mono mas precisamos de estéreo, duplicar
                        if audio_data.shape[1] == 1 and channels == 1:
                            # Duplicar canal mono para estéreo
                            audio_stereo = np.column_stack((audio_data[:, 0], audio_data[:, 0]))
                            audio_data = audio_stereo
                        
                        self.system_audio_frames.append(audio_data.tobytes())
                        
                        # Registrar timestamp básico
                        if hasattr(self, 'system_timestamps'):
                            self.system_timestamps.append(time.time())
                        
                    except Exception:
                        # Suprimir avisos de callback para evitar spam no terminal
                        pass
            
            # Iniciar gravação com sounddevice
            with sd.InputStream(
                device=device_index,
                channels=channels,
                samplerate=sample_rate,
                dtype=np.float32,
                callback=callback,
                blocksize=self.chunk,  # Usar chunk menor para menor latência
                latency='low'  # Configurar para baixa latência
            ):
                print("🎙️ Gravação de áudio do sistema ativa!")
                while self.recording:
                    time.sleep(0.01)  # Reduzido para 10ms para melhor responsividade
                    
        except Exception as e:
            print(f"❌ Erro na thread de gravação do sistema: {e}")
            # Tentar fallback com PyAudio
            self._fallback_pyaudio_system_recording(device_index)
    
    def _fallback_pyaudio_system_recording(self, device_index):
        """Fallback: usar PyAudio diretamente para Stereo Mix"""
        try:
            print("🔄 Tentando fallback com PyAudio...")
            
            # Mapear índice do sounddevice para PyAudio (geralmente são iguais)
            device_info = self.audio.get_device_info_by_index(device_index)
            
            if device_info['maxInputChannels'] > 0:
                # Tentar com diferentes configurações de canal
                for channels in [2, 1]:
                    try:
                        self.system_stream = self.audio.open(
                            format=self.format,
                            channels=channels,
                            rate=self.rate,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=self.chunk,
                            stream_callback=self._system_callback,
                            # Configurações para reduzir latência
                            input_host_api_specific_stream_info=None
                        )
                        self.system_stream.start_stream()
                        print(f"✅ Fallback PyAudio funcionou - {channels} canais")
                        return True
                        
                    except Exception as e:
                        print(f"Tentativa com {channels} canais falhou: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Fallback PyAudio também falhou: {e}")
            
        return False
    
    def _start_system_audio_wasapi(self):
        """Fallback: tentar WASAPI diretamente (método alternativo)"""
        try:
            # Procurar especificamente por Mixagem estéreo primeiro
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info['name'].lower()
                
                # Primeira prioridade: Mixagem estéreo
                if any(keyword in device_name for keyword in [
                    'mixagem estéreo', 'mixagem estereo', 'mixagem estÃ©reo', 'stereo mix'
                ]):
                    if device_info['maxInputChannels'] > 0:
                        return self._try_open_system_stream(i, device_info)
            
            # Segunda prioridade: outros dispositivos de sistema
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info['name'].lower()
                
                if any(keyword in device_name for keyword in [
                    'what u hear', 'wave out mix', 'sum', 'loopback'
                ]):
                    if device_info['maxInputChannels'] > 0:
                        return self._try_open_system_stream(i, device_info)
            
            print("⚠️  Nenhum dispositivo de captura de áudio do sistema encontrado")
            print("💡 Para capturar áudio do sistema no Windows:")
            print("   1. Vá em Configurações de Som > Painel de Som")
            print("   2. Aba 'Gravação' > Clique direito > 'Mostrar dispositivos desabilitados'")
            print("   3. Habilite 'Stereo Mix' se disponível")
            return False
                
        except Exception as e:
            print(f"Erro no fallback WASAPI: {e}")
            return False
    
    def _try_open_system_stream(self, device_index, device_info):
        """Tentar abrir stream de sistema com diferentes configurações"""
        for channels in [2, 1]:  # Tentar 2 canais primeiro, depois 1
            if channels <= device_info['maxInputChannels']:
                try:
                    self.system_stream = self.audio.open(
                        format=self.format,
                        channels=channels,
                        rate=self.rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=self.chunk,
                        stream_callback=self._system_callback
                    )
                    self.system_stream.start_stream()
                    print(f"✅ Áudio do sistema via PyAudio: {device_info['name']} ({channels} canais)")
                    return True
                    
                except Exception as e:
                    print(f"❌ Falha {channels} canais em {device_info['name']}: {e}")
                    continue
                    
        return False
    
    def _mic_callback(self, in_data, frame_count, time_info, status):
        """Callback para captura do microfone"""
        if self.recording:
            self.mic_frames.append(in_data)
            # Registrar timestamp básico
            if hasattr(self, 'mic_timestamps'):
                self.mic_timestamps.append(time.time())
            
            # Transcrição em tempo real DESABILITADA
            # self._process_chunk_for_realtime_transcription()
            
            return (in_data, pyaudio.paContinue)
        return (in_data, pyaudio.paComplete)
    
    def _system_callback(self, in_data, frame_count, time_info, status):
        """Callback para captura do áudio do sistema"""
        if self.recording:
            self.system_audio_frames.append(in_data)
            # Registrar timestamp básico
            if hasattr(self, 'system_timestamps'):
                self.system_timestamps.append(time.time())
            return (in_data, pyaudio.paContinue)
        return (in_data, pyaudio.paComplete)
    
    def stop_recording(self):
        """Parar gravação e salvar arquivo mixado"""
        if not self.recording:
            return None
            
        self.recording = False
        
        # Parar streams do microfone
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
            
        # Parar stream do sistema (PyAudio)
        if self.system_stream:
            self.system_stream.stop_stream()
            self.system_stream.close()
            self.system_stream = None
        
        # Aguardar thread do sistema terminar
        if self.system_recording_thread and self.system_recording_thread.is_alive():
            self.system_recording_thread.join(timeout=2.0)
            self.system_recording_thread = None
        
        # Aplicar sincronização se houver dados suficientes
        if (hasattr(self, 'mic_timestamps') and hasattr(self, 'system_timestamps') and 
            len(self.mic_timestamps) > 5 and len(self.system_timestamps) > 5):
            print("🔄 Verificando sincronização de streams...")
            
            # Calcular estatísticas de sincronização
            mic_avg = sum(self.mic_timestamps[-10:]) / min(10, len(self.mic_timestamps))
            system_avg = sum(self.system_timestamps[-10:]) / min(10, len(self.system_timestamps))
            time_diff = abs(mic_avg - system_avg)
            
            if time_diff > 0.1:
                print(f"⚠️  Detectado atraso de {time_diff:.3f}s entre streams")
            else:
                print(f"✅ Sincronização boa: {time_diff:.3f}s")
        
        # Mixar áudio do microfone e sistema
        filename = self._get_output_filename()
        try:
            mixed_audio = self._mix_audio_sources()
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(2)  # Sempre estéreo para o arquivo final
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)  # Usar taxa consistente (44100Hz)
                wf.writeframes(mixed_audio)
                
            print(f"💾 Arquivo salvo: {self.rate}Hz, 2 canais, 16-bit")
            
            print(f"Áudio mixado salvo em: {filename}")
            return filename
            
        except Exception as e:
            print(f"Erro ao salvar áudio: {e}")
            return None
    
    def _mix_audio_sources(self):
        """Mixar áudio do microfone e sistema"""
        try:
            # Converter frames para numpy arrays
            mic_data = b''.join(self.mic_frames) if self.mic_frames else b''
            system_data = b''.join(self.system_audio_frames) if self.system_audio_frames else b''
            
            if not mic_data and not system_data:
                return b''
            
            # Se só tem microfone
            if mic_data and not system_data:
                print("Mixagem: Apenas microfone")
                mic_array = np.frombuffer(mic_data, dtype=np.int16)
                # Converter mono para estéreo se necessário
                if self.channels == 1:
                    mic_stereo = np.column_stack((mic_array, mic_array)).flatten()
                else:
                    mic_stereo = mic_array
                # Amplificar microfone usando configuração
                mic_stereo = self._amplify_audio(mic_stereo, self.mic_gain)
                print(f"🔊 Microfone amplificado: {self.mic_gain:.1f}x")
                return mic_stereo.tobytes()
            
            # Se só tem áudio do sistema
            if system_data and not mic_data:
                print("Mixagem: Apenas áudio do sistema")
                system_array = np.frombuffer(system_data, dtype=np.int16)
                # Amplificar e normalizar áudio do sistema
                system_array = self._amplify_audio(system_array, 2.0)
                return system_array.tobytes()
            
            # Mixar ambos
            print("Mixagem: Microfone + Áudio do sistema")
            mic_array = np.frombuffer(mic_data, dtype=np.int16)
            system_array = np.frombuffer(system_data, dtype=np.int16)
            
            # Como agora ambos usam a mesma taxa (44100Hz), não precisa resample
            
            # Ajustar tamanhos para o menor
            min_length = min(len(mic_array), len(system_array))
            mic_array = mic_array[:min_length]
            system_array = system_array[:min_length]
            
            # Converter microfone para estéreo se necessário
            if self.channels == 1 and len(mic_array) * 2 == len(system_array):
                mic_array = np.repeat(mic_array, 2)
            
            # Garantir mesmo comprimento
            if len(mic_array) != len(system_array):
                min_length = min(len(mic_array), len(system_array))
                mic_array = mic_array[:min_length]
                system_array = system_array[:min_length]
            
            # Normalizar volumes individualmente antes de mixar
            mic_normalized = self._normalize_audio(mic_array)
            system_normalized = self._normalize_audio(system_array)
            
            # Aplicar redução de eco no áudio do sistema se habilitado
            if self.enable_echo_reduction:
                system_normalized = self._reduce_echo(system_normalized)
            
            # Mixar com volumes configuráveis - CORREÇÃO PARA EVITAR ESTOURO
            mixed = (mic_normalized * self.mic_gain + system_normalized * self.system_gain).astype(np.int16)
            
            print(f"🔊 Volumes aplicados: Microfone={self.mic_gain:.1f}x, Sistema={self.system_gain:.1f}x")
            
            # Prevenir clipping
            mixed = np.clip(mixed, -32767, 32767)
            
            return mixed.tobytes()
            
        except Exception as e:
            print(f"Erro na mixagem: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: retornar apenas microfone
            if self.mic_frames:
                return b''.join(self.mic_frames)
            return b''
    
    def _amplify_audio(self, audio_array, factor):
        """Amplificar áudio por um fator"""
        try:
            amplified = audio_array * factor
            # Prevenir clipping
            amplified = np.clip(amplified, -32767, 32767)
            return amplified.astype(np.int16)
        except:
            return audio_array
    
    def _normalize_audio(self, audio_array):
        """Normalizar áudio para usar toda a faixa dinâmica sem estouro"""
        try:
            if len(audio_array) == 0:
                return audio_array
                
            # Calcular RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
            
            if rms > 0:
                # Normalizar para ~50% da faixa máxima (mais conservador)
                target_rms = 32767 * 0.5
                factor = target_rms / rms
                # Limitar amplificação máxima para evitar estouro
                factor = min(factor, 2.0)
                normalized = audio_array * factor
                return np.clip(normalized, -32767, 32767).astype(np.int16)
            
            return audio_array
            
        except:
            return audio_array
    
    def _reduce_echo(self, system_audio):
        """Reduzir eco no áudio do sistema"""
        try:
            if len(system_audio) == 0:
                return system_audio
            
            # Aplicar filtro de redução de eco simples
            # Reduzir frequências que causam eco (normalmente baixas e médias)
            audio_float = system_audio.astype(np.float32)
            
            # Aplicar compressão dinâmica suave
            max_val = np.max(np.abs(audio_float))
            if max_val > 16000:  # Se muito alto
                compression_ratio = 16000 / max_val
                audio_float *= compression_ratio
            
            # Reduzir reverberação aplicando um filtro passa-alta leve
            if len(audio_float) > 10:
                # Filtro simples: reduzir componentes de baixa frequência
                filtered = audio_float.copy()
                for i in range(5, len(filtered)-5):
                    # Média móvel invertida para reduzir eco
                    filtered[i] = audio_float[i] * 0.8 + np.mean(audio_float[i-2:i+2]) * 0.2
                
                return np.clip(filtered, -32767, 32767).astype(np.int16)
            
            return np.clip(audio_float, -32767, 32767).astype(np.int16)
            
        except Exception as e:
            print(f"Erro na redução de eco: {e}")
            return system_audio
            
        except Exception as e:
            print(f"Erro na normalização: {e}")
            return system_audio
    
    def _resample_if_needed(self, audio_array, from_rate, to_rate):
        """Resample áudio se as taxas forem diferentes"""
        try:
            if from_rate == to_rate or len(audio_array) == 0:
                return audio_array
            
            # Resample simples usando interpolação linear
            # Para uma solução mais precisa, usaria scipy.signal.resample
            ratio = to_rate / from_rate
            new_length = int(len(audio_array) * ratio)
            
            if new_length > 0:
                # Interpolação linear simples
                old_indices = np.linspace(0, len(audio_array) - 1, new_length)
                resampled = np.interp(old_indices, np.arange(len(audio_array)), audio_array)
                return resampled.astype(np.int16)
            
            return audio_array
            
        except Exception as e:
            print(f"Erro no resample: {e}")
            return audio_array
    
    def _synchronize_audio_streams(self, mic_data, system_data):
        """Sincronizar streams de áudio baseado nos timestamps"""
        try:
            if not self.mic_timestamps or not self.system_timestamps:
                return mic_data, system_data
            
            # Calcular diferença de tempo média entre os streams
            mic_avg_time = sum(self.mic_timestamps) / len(self.mic_timestamps)
            system_avg_time = sum(self.system_timestamps) / len(self.system_timestamps)
            
            time_diff = abs(mic_avg_time - system_avg_time)
            
            if time_diff > 0.05:  # Se diferença > 50ms, tentar corrigir
                print(f"⚠️  Detectado atraso de {time_diff:.3f}s entre streams")
                
                # Se microfone está atrasado
                if mic_avg_time > system_avg_time:
                    # Calcular quantos samples remover do início do microfone
                    samples_to_remove = int(time_diff * self.rate * self.channels)
                    mic_array = np.frombuffer(mic_data, dtype=np.int16)
                    if len(mic_array) > samples_to_remove:
                        mic_array = mic_array[samples_to_remove:]
                        mic_data = mic_array.tobytes()
                        print(f"🔧 Cortou {samples_to_remove} samples do microfone")
                
                # Se sistema está atrasado
                elif system_avg_time > mic_avg_time:
                    # Calcular quantos samples remover do início do sistema
                    samples_to_remove = int(time_diff * self.rate * 2)  # Sistema sempre 2 canais
                    system_array = np.frombuffer(system_data, dtype=np.int16)
                    if len(system_array) > samples_to_remove:
                        system_array = system_array[samples_to_remove:]
                        system_data = system_array.tobytes()
                        print(f"🔧 Cortou {samples_to_remove} samples do sistema")
            
            return mic_data, system_data
            
        except Exception as e:
            print(f"Erro na sincronização: {e}")
            return mic_data, system_data
    
    def _monitor_sync(self):
        """Monitorar sincronização durante a gravação"""
        last_check = time.time()
        
        while self.recording:
            time.sleep(1.0)  # Verificar a cada segundo
            
            if len(self.mic_timestamps) > 5 and len(self.system_timestamps) > 5:
                # Pegar últimos 5 timestamps
                recent_mic = self.mic_timestamps[-5:]
                recent_system = self.system_timestamps[-5:]
                
                mic_avg = sum(recent_mic) / len(recent_mic)
                system_avg = sum(recent_system) / len(recent_system)
                
                time_diff = abs(mic_avg - system_avg)
                
                if time_diff > 0.1:  # Se diferença > 100ms
                    current_time = time.time()
                    if current_time - last_check > 5.0:  # Alertar apenas a cada 5s
                        print(f"⚠️  Atraso detectado: {time_diff:.3f}s entre streams")
                        last_check = current_time
    
    def _get_output_filename(self):
        """Gerar nome do arquivo de saída"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("data", exist_ok=True)
        return f"data/recording_{timestamp}.wav"
    
    def get_audio_level(self):
        """Obter nível de áudio atual (para indicador visual)"""
        if not self.mic_frames and not self.system_audio_frames:
            return 0
        
        try:
            # Priorizar microfone para indicador visual
            frames_to_check = self.mic_frames if self.mic_frames else self.system_audio_frames
            
            # Pegar os últimos frames
            recent_frames = frames_to_check[-5:] if len(frames_to_check) >= 5 else frames_to_check
            if not recent_frames:
                return 0
                
            # Converter para numpy array e calcular RMS
            audio_data = np.frombuffer(b''.join(recent_frames), dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Normalizar para 0-100
            return min(int((rms / 32767) * 100), 100)
            
        except Exception as e:
            return 0
    
    def set_record_system_audio(self, enable):
        """Habilitar/desabilitar gravação do áudio do sistema"""
        self.record_system_audio = enable
        print(f"Gravação de áudio do sistema: {'Habilitada' if enable else 'Desabilitada'}")
    
    def check_system_audio_capability(self):
        """Verificar se é possível gravar áudio do sistema"""
        try:
            # Verificar usando sounddevice
            loopback_device = self._find_loopback_device()
            if loopback_device is not None:
                return True, "Dispositivo de loopback encontrado"
            
            # Verificar usando PyAudio
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info['name'].lower()
                
                if any(keyword in device_name for keyword in [
                    'stereo mix', 'what u hear', 'wave out mix', 'sum'
                ]):
                    if device_info['maxInputChannels'] > 0:
                        return True, f"Stereo Mix encontrado: {device_info['name']}"
            
            return False, "Nenhum dispositivo de captura de sistema encontrado"
            
        except Exception as e:
            return False, f"Erro na verificação: {e}"
    
    def _process_chunk_for_realtime_transcription(self):
        """Processar chunk de áudio para transcrição em tempo real - OTIMIZADO"""
        if not self.realtime_callback or not self.recording:
            return
            
        current_time = time.time()
        if current_time - self.last_chunk_time < self.chunk_duration:
            return
            
        try:
            # Criar chunk temporário com os dados atuais
            self.chunk_counter += 1
            chunk_filename = f"{self.temp_dir}/realtime_chunk_{self.chunk_counter}.wav"
            
            # Mixar áudio atual (otimizado)
            mixed_audio = self._mix_audio_sources_fast()
            if not mixed_audio:
                return
                
            # Salvar chunk temporário (compressão otimizada)
            with wave.open(chunk_filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(mixed_audio)
            
            # Chamar callback para transcrição em thread separada (prioridade alta)
            def transcribe_chunk():
                try:
                    if self.realtime_callback:
                        self.realtime_callback(chunk_filename, self.chunk_counter)
                except Exception as e:
                    print(f"Erro na transcrição em tempo real: {e}")
                finally:
                    # Remover arquivo temporário
                    try:
                        if os.path.exists(chunk_filename):
                            os.remove(chunk_filename)
                    except:
                        pass
            
            threading.Thread(target=transcribe_chunk, daemon=True).start()
            self.last_chunk_time = current_time
            
            # Limpar frames antigas para liberar memória (manter últimos 2 chunks)
            frames_per_chunk = int(self.rate * self.chunk_duration / self.chunk)
            if len(self.mic_frames) > frames_per_chunk * 2:
                self.mic_frames = self.mic_frames[-frames_per_chunk:]
            if len(self.system_audio_frames) > frames_per_chunk * 2:
                self.system_audio_frames = self.system_audio_frames[-frames_per_chunk:]
                
        except Exception as e:
            print(f"Erro ao processar chunk para transcrição: {e}")

    def _mix_audio_sources_fast(self):
        """Mixagem otimizada para transcrição em tempo real com sobreposição inteligente"""
        try:
            # Usar frames com sobreposição de 2 segundos para garantir continuidade
            overlap_duration = 2  # segundos de sobreposição
            total_duration = self.chunk_duration + overlap_duration
            frames_needed = int(self.rate * total_duration / self.chunk)
            
            # Pegar frames com contexto substancial para não perder palavras
            mic_data = b''.join(self.mic_frames[-frames_needed:]) if self.mic_frames else b''
            system_data = b''.join(self.system_audio_frames[-frames_needed:]) if self.system_audio_frames else b''
            
            if not mic_data and not system_data:
                return b''
            
            # Processamento simplificado para velocidade
            if mic_data and not system_data:
                mic_array = np.frombuffer(mic_data, dtype=np.int16)
                if self.channels == 2 and len(mic_array) % 2 != 0:
                    mic_array = mic_array[:-1]  # Garantir número par para estéreo
                return self._amplify_audio(mic_array, 3.0).tobytes()
            
            if system_data and not mic_data:
                system_array = np.frombuffer(system_data, dtype=np.int16)
                return self._amplify_audio(system_array, 1.5).tobytes()
            
            # Mixagem rápida de ambos
            mic_array = np.frombuffer(mic_data, dtype=np.int16)
            system_array = np.frombuffer(system_data, dtype=np.int16)
            
            # Ajustar para mesmo tamanho rapidamente
            min_length = min(len(mic_array), len(system_array))
            mic_array = mic_array[:min_length]
            system_array = system_array[:min_length]
            
            # Mixagem simples com amplificação configurável
            mic_amplified = self._amplify_audio(mic_array, self.mic_gain)
            system_amplified = self._amplify_audio(system_array, self.system_gain)
            
            # Combinação sem overflow checking para velocidade
            mixed = (mic_amplified.astype(np.int32) + system_amplified.astype(np.int32))
            mixed = np.clip(mixed, -32768, 32767).astype(np.int16)
            
            return mixed.tobytes()
            
        except Exception as e:
            print(f"Erro na mixagem rápida: {e}")
            # Fallback para mixagem normal
            return self._mix_audio_sources()

    def get_system_audio_setup_instructions(self):
        """Retornar instruções para configurar captura de áudio do sistema"""
        return """
        Para habilitar a captura de áudio do sistema no Windows:
        
        1. Clique direito no ícone de som na barra de tarefas
        2. Selecione 'Configurações de som'
        3. Role para baixo e clique em 'Painel de som'
        4. Vá para a aba 'Gravação'
        5. Clique direito no espaço vazio e marque:
           ☑ Mostrar dispositivos desabilitados
           ☑ Mostrar dispositivos desconectados
        6. Se aparecer 'Stereo Mix', clique direito nele e selecione 'Habilitar'
        7. Defina como dispositivo padrão se necessário
        
        Nota: Nem todas as placas de som suportam Stereo Mix.
        Como alternativa, use cabos de áudio ou software de terceiros.
        """
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'audio'):
            self.audio.terminate()