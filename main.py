"""
MeetAI - Gravador de Áudio com Resumos IA
Aplicação principal para gravação de áudio e geração de resumos
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime
from pathlib import Path

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber
from src.ai.summarizer import Summarizer
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager

class MeetAI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.audio_recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.summarizer = Summarizer()
        
        # Transcrição em tempo real REMOVIDA (sistema simplificado)
        
        # Criar diretórios necessários
        self.ensure_directories()
        
        # Carregar configurações de áudio
        self.load_audio_settings()
        
        # Inicializar interface
        self.root = tk.Tk()
        self.main_window = MainWindow(self.root, self)
        
        # Transcrição em tempo real DESABILITADA (usuário preferiu gravação completa)
        # self.audio_recorder.set_realtime_transcription_callback(self.realtime_transcription_callback)
        
    def ensure_directories(self):
        """Criar diretórios necessários se não existirem"""
        directories = ['data', 'config', 'outputs', 'temp']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def load_audio_settings(self):
        """Carregar configurações de áudio salvas"""
        try:
            settings_file = Path("config/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                    audio_config = settings.get('audio', {})
                    
                    # Configurar dispositivo de entrada
                    input_device = audio_config.get('input_device')
                    if input_device is not None:
                        self.audio_recorder.set_input_device(input_device)
                    else:
                        print("Dispositivo de microfone nao definido nas configuracoes; usando auto-detectado.")
                    
                    # Configurar sample rate
                    sample_rate = audio_config.get('sample_rate', 44100)
                    self.audio_recorder.rate = sample_rate
                    
                    # Configurar gravação de áudio do sistema
                    record_system = audio_config.get('record_system_audio', True)
                    self.audio_recorder.set_record_system_audio(record_system)
                    
                    device_label = input_device if input_device is not None else "Auto"
                    print(f"Configurações de áudio carregadas: Dispositivo={device_label}, Sample Rate={sample_rate}, Sistema={record_system}")
        except Exception as e:
            print(f"Erro ao carregar configurações de áudio: {e}")
    
    def realtime_transcription_callback(self, chunk_file, chunk_number):
        """Callback para transcrição em tempo real"""
        try:
            print(f"🎯 Transcrevendo chunk {chunk_number} em tempo real...")
            
            # Transcrever chunk
            chunk_transcript = self.transcriber.transcribe(chunk_file)
            
            if chunk_transcript:
                # Armazenar transcrição do chunk
                self.chunk_transcripts[chunk_number] = chunk_transcript
                
                # Reconstruir transcrição completa
                full_transcript = ""
                for i in sorted(self.chunk_transcripts.keys()):
                    if full_transcript and not full_transcript.endswith(" "):
                        full_transcript += " "
                    full_transcript += self.chunk_transcripts[i]
                
                self.realtime_transcript = full_transcript
                
                # Atualizar interface na thread principal
                self.root.after(0, lambda: self.main_window.update_realtime_transcript(full_transcript))
                
                print(f"✅ Chunk {chunk_number} transcrito: {len(chunk_transcript)} caracteres")
            else:
                print(f"❌ Falha na transcrição do chunk {chunk_number}")
                
        except Exception as e:
            print(f"Erro na transcrição em tempo real do chunk {chunk_number}: {e}")

    def start_recording(self):
        """Iniciar gravação de áudio - SISTEMA SIMPLIFICADO"""
        try:
            # Limpar interface
            self.main_window.clear_results()
            
            self.audio_recorder.start_recording()
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar gravação: {str(e)}")
            return False
    
    def stop_recording(self):
        """Parar gravação e processar áudio"""
        try:
            audio_file = self.audio_recorder.stop_recording()
            if audio_file:
                # Processar em thread separada
                threading.Thread(target=self.process_audio, args=(audio_file,), daemon=True).start()
            return audio_file
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao parar gravação: {str(e)}")
            return None
    
    def process_audio(self, audio_file):
        """Processar áudio gravado - SISTEMA SIMPLIFICADO"""
        try:
            # Fazer transcrição completa do arquivo (sem tempo real)
            self.main_window.update_status("Transcrevendo áudio...")
            transcript = self.transcriber.transcribe(audio_file)
            
            if transcript:
                # Exibir transcrição primeiro
                self.main_window.display_transcript_only(transcript)
                
                # Gerar resumo
                self.main_window.update_status("Gerando resumo...")
                template = self.main_window.get_selected_template()
                summary = self.summarizer.generate_summary(transcript, template)
                
                # Atualizar interface com transcrição + resumo final
                self.main_window.display_final_results(transcript, summary)
                self.main_window.update_status("Processamento concluído!")
            else:
                self.main_window.update_status("Erro na transcrição")
                self.main_window.show_error("Falha na transcrição do áudio")
                
        except Exception as e:
            error_msg = f"Erro no processamento: {str(e)}"
            self.main_window.update_status(error_msg)
            messagebox.showerror("Erro", error_msg)
    
    def run(self):
        """Executar aplicação"""
        self.root.mainloop()

def main():
    """Função principal"""
    try:
        app = MeetAI()
        app.run()
    except Exception as e:
        print(f"Erro ao inicializar aplicação: {e}")
        messagebox.showerror("Erro Fatal", f"Erro ao inicializar aplicação: {e}")

if __name__ == "__main__":
    main()
