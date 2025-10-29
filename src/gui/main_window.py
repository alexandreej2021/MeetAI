"""
Interface gráfica principal do MeetAI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from datetime import datetime
import os

class MainWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.recording = False
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        self.root.title("MeetAI - Gravador com Resumos IA")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(800, 600)  # Tamanho mínimo
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar grid principal - importante para redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Frame principal que ocupa toda a janela
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Row 3 (resultados) expande
        
        # Título
        title_label = ttk.Label(main_frame, text="MeetAI", font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 15), sticky=tk.W+tk.E)
        
        # Seção de gravação - compacta
        recording_frame = ttk.LabelFrame(main_frame, text="Gravação de Áudio", padding="8")
        recording_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        recording_frame.columnconfigure(1, weight=1)
        
        # Botão de gravação
        self.record_button = ttk.Button(
            recording_frame, 
            text="▶ Iniciar Gravação", 
            command=self.toggle_recording,
            style='Accent.TButton'
        )
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        # Indicador de status
        self.status_label = ttk.Label(recording_frame, text="Pronto para gravar")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Seção de templates - compacta
        template_frame = ttk.LabelFrame(main_frame, text="Template de Resumo", padding="8")
        template_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        template_frame.columnconfigure(1, weight=1)
        
        ttk.Label(template_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W)
        
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            state="readonly",
            width=30
        )
        self.template_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Carregar templates
        self.load_templates()
        
        # Seção de resultados - EXPANSÍVEL
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="8")
        results_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)  # Notebook expande
        
        # Notebook para abas - MAIOR
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Aba da transcrição
        transcript_frame = ttk.Frame(self.notebook)
        self.notebook.add(transcript_frame, text="📝 Transcrição")
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#fafafa',
            relief='flat',
            borderwidth=1
        )
        self.transcript_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=3, pady=3)
        
        # Aba do resumo
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="📋 Resumo")
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        
        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg='#f8f9fa',
            relief='flat',
            borderwidth=1
        )
        self.summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=3, pady=3)
        
        # BOTÕES FIXOS NA PARTE INFERIOR
        button_container = ttk.Frame(main_frame)
        button_container.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(8, 0))
        button_container.columnconfigure(1, weight=1)  # Espaço flexível no meio
        
        # Botões à esquerda
        left_buttons = ttk.Frame(button_container)
        left_buttons.grid(row=0, column=0, sticky=tk.W)
        
        self.save_button = ttk.Button(
            left_buttons,
            text="💾 Salvar Resultados",
            command=self.save_results,
            state='disabled'
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.clear_button = ttk.Button(
            left_buttons,
            text="🗑 Limpar",
            command=self.clear_results
        )
        self.clear_button.pack(side=tk.LEFT)
        
        # Botões à direita
        right_buttons = ttk.Frame(button_container)
        right_buttons.grid(row=0, column=2, sticky=tk.E)
        
        config_button = ttk.Button(
            right_buttons,
            text="⚙ Configurações",
            command=self.open_settings
        )
        config_button.pack(side=tk.RIGHT)
        
        # Monitoramento de nível de áudio removido
    
    def load_templates(self):
        """Carregar templates disponíveis"""
        try:
            templates = self.app.summarizer.get_available_templates()
            self.template_combo['values'] = [f"{name}" for _, name in templates]
            self.template_combo.set(templates[0][1] if templates else "")
            
            # Mapear nomes para IDs
            self.template_mapping = {name: template_id for template_id, name in templates}
        except Exception as e:
            print(f"Erro ao carregar templates: {e}")
            self.template_combo['values'] = ["Resumo de Conversa"]
            self.template_combo.set("Resumo de Conversa")
            self.template_mapping = {"Resumo de Conversa": "conversa"}
    
    def toggle_recording(self):
        """Alternar estado de gravação"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Iniciar gravação"""
        if self.app.start_recording():
            self.recording = True
            self.record_button.configure(text="⏹ Parar Gravação")
            self.status_label.configure(text="Gravando...")
            self.clear_results()
        else:
            messagebox.showerror("Erro", "Não foi possível iniciar a gravação")
    
    def stop_recording(self):
        """Parar gravação"""
        self.recording = False
        self.record_button.configure(text="▶ Iniciar Gravação")
        self.status_label.configure(text="Processando...")
        
        # Parar gravação em thread separada
        threading.Thread(target=self.app.stop_recording, daemon=True).start()
    
    # Método update_audio_level removido (barra de progresso removida)
    
    def get_selected_template(self):
        """Obter template selecionado"""
        template_name = self.template_var.get()
        return self.template_mapping.get(template_name, "conversa")
    
    def display_results(self, transcript, summary):
        """Exibir resultados da transcrição e resumo"""
        # Limpar textos anteriores
        self.transcript_text.delete('1.0', tk.END)
        self.summary_text.delete('1.0', tk.END)
        
        # Inserir novos textos
        if transcript:
            self.transcript_text.insert('1.0', transcript)
        
        if summary:
            self.summary_text.insert('1.0', summary)
        
        # Habilitar botão de salvar
        self.save_button.configure(state='normal')
        
        # Focar na aba do resumo
        self.notebook.select(1)
    
    def display_transcript_only(self, transcript):
        """Exibir apenas a transcrição (sistema simplificado)"""
        try:
            # Limpar e exibir transcrição
            self.transcript_text.delete('1.0', tk.END)
            if transcript:
                self.transcript_text.insert('1.0', transcript)
                
            # Focar na aba da transcrição
            self.notebook.select(0)
            
            # Atualizar contagem de palavras
            word_count = len(transcript.split()) if transcript else 0
            self.update_status(f"Transcrição concluída - {word_count} palavras")
            
        except Exception as e:
            print(f"Erro ao exibir transcrição: {e}")

    def display_final_results(self, transcript, summary):
        """Exibir resultados finais (transcrição + resumo)"""
        # Atualizar transcrição
        self.transcript_text.delete('1.0', tk.END)
        if transcript:
            self.transcript_text.insert('1.0', transcript)
            
        # Atualizar resumo
        self.summary_text.delete('1.0', tk.END)
        if summary:
            self.summary_text.insert('1.0', summary)
        
        # Habilitar botão de salvar
        self.save_button.configure(state='normal')
        
        # Focar na aba do resumo
        self.notebook.select(1)
    
    def update_status(self, status):
        """Atualizar status na interface"""
        self.status_label.configure(text=status)
        self.root.update_idletasks()
        
    def show_error(self, message):
        """Exibir mensagem de erro"""
        messagebox.showerror("Erro", message)
    
    def update_realtime_transcript(self, transcript):
        """Atualizar transcrição em tempo real durante a gravação - OTIMIZADO"""
        try:
            # Atualização incremental mais eficiente
            self.transcript_text.config(state=tk.NORMAL)
            
            # Limpar e inserir novo conteúdo de forma otimizada
            self.transcript_text.delete('1.0', tk.END)
            self.transcript_text.insert('1.0', transcript)
            
            # Scroll suave para o final
            self.transcript_text.see(tk.END)
            
            # Mudar para aba de resultados se não estiver já
            if self.recording:
                current_tab = self.notebook.index(self.notebook.select())
                if current_tab != 0:  # Se não está na aba de transcrição
                    self.notebook.select(0)
                
            # Atualizar status de forma eficiente
            word_count = len(transcript.split()) if transcript else 0
            self.update_status(f"🎙️ Gravando... ({word_count} palavras • Chunk de 8s)")
            
            # Forçar atualização da interface
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Erro ao atualizar transcrição em tempo real: {e}")
    
    def save_results(self):
        """Salvar resultados em arquivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt"), ("Arquivo markdown", "*.md")],
                initialfile=f"meetai_resultado_{timestamp}"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# MeetAI - Resultado {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
                    f.write(f"**Template:** {self.template_var.get()}\n\n")
                    
                    f.write("## Transcrição\n\n")
                    f.write(self.transcript_text.get('1.0', tk.END))
                    f.write("\n\n")
                    
                    f.write("## Resumo\n\n")
                    f.write(self.summary_text.get('1.0', tk.END))
                
                messagebox.showinfo("Sucesso", f"Resultados salvos em: {filename}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")
    
    def clear_results(self):
        """Limpar resultados"""
        self.transcript_text.delete('1.0', tk.END)
        self.summary_text.delete('1.0', tk.END)
        self.save_button.configure(state='disabled')
        self.notebook.select(0)  # Voltar para aba de transcrição
    
    def open_settings(self):
        """Abrir janela de configurações"""
        SettingsWindow(self.root, self.app)

class SettingsWindow:
    def __init__(self, parent, app):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("Configurações")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Configurar interface de configurações"""
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba Áudio (PRIMEIRA)
        audio_frame = ttk.Frame(notebook)
        notebook.add(audio_frame, text="🎤 Áudio")
        
        # Aba API (SEGUNDA)
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="🤖 APIs")
        
        # Frame para seleção de provedor de IA
        provider_frame = ttk.LabelFrame(api_frame, text="Provedor de IA", padding="10")
        provider_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.ai_provider_var = tk.StringVar()
        
        # OpenAI
        openai_radio = ttk.Radiobutton(
            provider_frame,
            text="🔵 OpenAI (GPT + Whisper)",
            variable=self.ai_provider_var,
            value="openai",
            command=self.on_provider_change
        )
        openai_radio.pack(anchor=tk.W, pady=2)
        
        # Gemini
        gemini_radio = ttk.Radiobutton(
            provider_frame,
            text="🟢 Google Gemini",
            variable=self.ai_provider_var,
            value="gemini",
            command=self.on_provider_change
        )
        gemini_radio.pack(anchor=tk.W, pady=2)
        
        self.ai_provider_var.set("openai")  # Padrão
        
        # Frame para chaves API
        keys_frame = ttk.LabelFrame(api_frame, text="Chaves de API", padding="10")
        keys_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # OpenAI API Key
        ttk.Label(keys_frame, text="OpenAI API Key:").pack(anchor=tk.W, pady=(5, 2))
        self.openai_key_var = tk.StringVar()
        openai_entry = ttk.Entry(keys_frame, textvariable=self.openai_key_var, show="*", width=50)
        openai_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Gemini API Key
        ttk.Label(keys_frame, text="Google Gemini API Key:").pack(anchor=tk.W, pady=(5, 2))
        self.gemini_key_var = tk.StringVar()
        gemini_entry = ttk.Entry(keys_frame, textvariable=self.gemini_key_var, show="*", width=50)
        gemini_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Informações sobre APIs
        info_text = tk.Text(keys_frame, height=6, wrap=tk.WORD, font=('Arial', 9))
        info_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        info_content = """💡 COMO OBTER AS CHAVES:

🔵 OpenAI: https://platform.openai.com/api-keys
   • Transcrição: Whisper (~$0.006/min)
   • Resumos: GPT-3.5-turbo (~$0.002/resumo)

🟢 Gemini: https://makersuite.google.com/app/apikey
   • Resumos: Gemini Pro (gratuito até 60 req/min)
   • Transcrição: Usa OpenAI Whisper (requer chave OpenAI)"""
        
        info_text.insert('1.0', info_content)
        info_text.configure(state='disabled')
        
        # Frame para dispositivo de entrada
        device_frame = ttk.LabelFrame(audio_frame, text="Dispositivo de Entrada (Microfone)", padding="10")
        device_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        
        # Label e Combobox para seleção de dispositivo
        ttk.Label(device_frame, text="Selecione o microfone:").pack(anchor=tk.W, pady=(0, 5))
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            state="readonly",
            width=60
        )
        self.device_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Carregar dispositivos únicos
        self.device_mapping = {}  # Mapear texto para índice
        try:
            devices = self.app.audio_recorder.get_audio_devices()
            unique_devices = self._filter_unique_devices(devices)
            
            device_options = ["🔄 Automático (Dispositivo Padrão do Sistema)"]
            self.device_mapping["🔄 Automático (Dispositivo Padrão do Sistema)"] = None
            
            for device in unique_devices:
                device_text = f"🎤 {device['clean_name']} ({device['channels']} {'canal' if device['channels'] == 1 else 'canais'})"
                device_options.append(device_text)
                self.device_mapping[device_text] = device['index']
            
            self.device_combo['values'] = device_options
            if device_options:
                self.device_combo.set(device_options[0])  # Selecionar automático por padrão
            
        except Exception as e:
            print(f"Erro detalhado ao carregar dispositivos: {e}")
            # Fallback: carregar dispositivos simples sem filtro
            try:
                devices = self.app.audio_recorder.get_audio_devices()
                device_options = ["🔄 Automático (Dispositivo Padrão do Sistema)"]
                self.device_mapping["🔄 Automático (Dispositivo Padrão do Sistema)"] = None
                
                for device in devices:
                    device_text = f"🎤 {device['name']} ({device['channels']} canais)"
                    device_options.append(device_text)
                    self.device_mapping[device_text] = device['index']
                
                self.device_combo['values'] = device_options
                if device_options:
                    self.device_combo.set(device_options[0])
                    
            except Exception as e2:
                error_label = ttk.Label(device_frame, text=f"❌ Erro ao carregar dispositivos: {e2}")
                error_label.pack(anchor=tk.W, pady=5)
        
        # Botão para testar dispositivo
        test_button = ttk.Button(
            device_frame,
            text="🔊 Testar Dispositivo Selecionado",
            command=self.test_audio_device
        )
        test_button.pack(pady=(10, 0))
        
        # Configurações de qualidade
        quality_frame = ttk.LabelFrame(audio_frame, text="Qualidade de Gravação", padding="10")
        quality_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Sample Rate
        ttk.Label(quality_frame, text="Taxa de Amostragem:").grid(row=0, column=0, sticky=tk.W)
        self.sample_rate_var = tk.StringVar()
        sample_rate_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.sample_rate_var,
            values=["22050", "44100", "48000"],
            state="readonly",
            width=10
        )
        sample_rate_combo.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)
        self.sample_rate_var.set("44100")
        
        # Opção para gravar áudio do sistema
        self.system_audio_var = tk.BooleanVar()
        system_audio_check = ttk.Checkbutton(
            quality_frame,
            text="🔊 Gravar áudio do sistema (saída do PC)",
            variable=self.system_audio_var
        )
        system_audio_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        self.system_audio_var.set(True)  # Habilitado por padrão
        
        # Botão para verificar capacidade de áudio do sistema
        check_system_button = ttk.Button(
            quality_frame,
            text="🔍 Verificar Áudio do Sistema",
            command=self.check_system_audio
        )
        check_system_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # Botões
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Salvar", command=self.save_settings).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancelar", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def on_provider_change(self):
        """Callback quando o provedor de IA é alterado"""
        provider = self.ai_provider_var.get()
        print(f"Provedor selecionado: {provider}")
        
        # Aqui você pode adicionar lógica adicional se necessário
        # Por exemplo, mostrar/ocultar campos específicos
    
    def load_current_settings(self):
        """Carregar configurações atuais"""
        try:
            import json
            from pathlib import Path
            
            # Carregar API Keys
            config_file = Path("config/api_keys.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # OpenAI API Key
                    openai_key = config.get('openai_api_key', '')
                    if openai_key:
                        self.openai_key_var.set('*' * len(openai_key))
                    
                    # Gemini API Key
                    gemini_key = config.get('gemini_api_key', '')
                    if gemini_key:
                        self.gemini_key_var.set('*' * len(gemini_key))
                    
                    # Provedor preferido
                    provider = config.get('ai_provider', 'openai')
                    self.ai_provider_var.set(provider)
            
            # Carregar configurações de áudio
            settings_file = Path("config/settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                    # Dispositivo de áudio
                    audio_device = settings.get('audio', {}).get('input_device')
                    if audio_device is None:
                        # Procurar pela opção "Automático"
                        for option in self.device_combo['values']:
                            if "Automático" in option:
                                self.device_var.set(option)
                                break
                    else:
                        # Procurar pelo dispositivo salvo
                        for option_text, device_index in self.device_mapping.items():
                            if device_index == audio_device:
                                self.device_var.set(option_text)
                                break
                    
                    # Sample rate
                    sample_rate = settings.get('audio', {}).get('sample_rate', 44100)
                    self.sample_rate_var.set(str(sample_rate))
                    
                    # Áudio do sistema
                    system_audio = settings.get('audio', {}).get('record_system_audio', True)
                    self.system_audio_var.set(system_audio)
            else:
                # Valores padrão
                if self.device_combo['values']:
                    self.device_var.set(self.device_combo['values'][0])
                self.sample_rate_var.set("44100")
                self.system_audio_var.set(True)
                
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    
    def _filter_unique_devices(self, devices):
        """Filtrar apenas dispositivos principais como no Windows (máximo 3-4)"""
        main_devices = []
        
        # Categorias de dispositivos que queremos mostrar
        found_categories = {
            'webcam': None,
            'realtek': None,
            'bluetooth': None,
            'usb_headset': None,
            'other': None
        }
        
        for device in devices:
            try:
                original_name = device['name'].lower()
                
                # Pular dispositivos técnicos do sistema
                skip_keywords = [
                    'mapeador de som', 'sound mapper', 'driver de captura', 
                    'primary sound capture', 'grupo de microfones'
                ]
                
                if any(keyword in original_name for keyword in skip_keywords):
                    continue
                
                # Categorizar dispositivos
                new_device = device.copy()
                
                if 'webcam' in original_name or 'general webcam' in original_name:
                    if found_categories['webcam'] is None:
                        new_device['clean_name'] = 'Webcam'
                        new_device['priority'] = 10
                        found_categories['webcam'] = new_device
                        
                elif 'realtek' in original_name and 'audio' in original_name:
                    # Preferir dispositivos com 2 canais para Realtek
                    if (found_categories['realtek'] is None or 
                        device['channels'] >= found_categories['realtek']['channels']):
                        new_device['clean_name'] = 'Microfone (Realtek Audio)'
                        new_device['priority'] = 8
                        found_categories['realtek'] = new_device
                        
                elif 'bluetooth' in original_name or 'headset' in original_name:
                    if found_categories['bluetooth'] is None:
                        clean_name = 'Headset Bluetooth' if 'bluetooth' in original_name else 'Headset'
                        new_device['clean_name'] = clean_name
                        new_device['priority'] = 9
                        found_categories['bluetooth'] = new_device
                        
                elif 'usb' in original_name or ('microfone' in original_name and 'realtek' not in original_name):
                    if found_categories['usb_headset'] is None:
                        clean_name = self._clean_device_name(device['name'])
                        new_device['clean_name'] = clean_name
                        new_device['priority'] = 7
                        found_categories['usb_headset'] = new_device
                        
            except Exception as e:
                print(f"Erro ao processar device {device}: {e}")
                continue
        
        # Adicionar dispositivos encontrados na ordem de prioridade
        for category in ['webcam', 'bluetooth', 'realtek', 'usb_headset', 'other']:
            if found_categories[category] is not None:
                main_devices.append(found_categories[category])
        
        # Limitar a 3 dispositivos principais
        return main_devices[:3]
    
    def _clean_device_name(self, name):
        """Limpar e simplificar nome do dispositivo"""
        # Remover prefixos comuns
        name = name.replace('Microfone (', '').replace(')', '')
        name = name.replace('Grupo de microfones (', '').replace(')', '')
        
        # Simplificar nomes específicos
        if 'GENERAL WEBCAM' in name:
            return 'Webcam'
        elif 'Realtek' in name and 'Audio' in name:
            return 'Microfone (Realtek Audio)'
        elif 'bluetooth' in name.lower():
            return 'Headset Bluetooth'
        elif 'headset' in name.lower():
            return 'Headset'
        else:
            # Para outros dispositivos, tentar limpar o nome
            name = name.replace('Realtek(R)', 'Realtek')
            name = name.replace('Microsoft', 'Sistema')
            return name.strip()
    
    def _get_base_device_name(self, name):
        """Obter nome base do dispositivo para evitar duplicatas"""
        name_lower = name.lower()
        if 'webcam' in name_lower:
            return 'webcam'
        elif 'realtek' in name_lower:
            return 'realtek'
        elif 'bluetooth' in name_lower or 'headset' in name_lower:
            return 'headset'
        else:
            # Para outros, usar as primeiras 2 palavras
            words = name.split()
            return '_'.join(words[:2]).lower() if len(words) >= 2 else name.lower()
    
    def _get_device_priority(self, name_lower):
        """Determinar prioridade do dispositivo baseado no nome"""
        if 'usb' in name_lower or 'headset' in name_lower:
            return 10  # Alta prioridade para USB e headsets
        elif 'bluetooth' in name_lower:
            return 8   # Boa prioridade para Bluetooth
        elif 'webcam' in name_lower:
            return 6   # Média prioridade para webcams
        elif 'realtek' in name_lower:
            return 4   # Baixa prioridade para dispositivos internos
        elif 'microsoft' in name_lower or 'sistema' in name_lower:
            return 2   # Muito baixa para dispositivos do sistema
        else:
            return 5   # Prioridade padrão
    
    def test_audio_device(self):
        """Testar dispositivo de áudio selecionado"""
        try:
            selected_text = self.device_var.get()
            device_index = self.device_mapping.get(selected_text)
            
            if device_index is None:
                device_info = self.app.audio_recorder.get_default_device()
                if device_info:
                    message = f"✅ Dispositivo Padrão\n\nNome: {device_info['name']}\nCanais: {device_info['channels']}"
                else:
                    message = "❌ Nenhum dispositivo padrão encontrado"
            else:
                devices = self.app.audio_recorder.get_audio_devices()
                device_info = next((d for d in devices if d['index'] == device_index), None)
                if device_info:
                    message = f"✅ Dispositivo Selecionado\n\nNome: {device_info['name']}\nÍndice: {device_info['index']}\nCanais: {device_info['channels']}\nTaxa Padrão: {device_info.get('default_sample_rate', 'N/A')} Hz"
                else:
                    message = "❌ Dispositivo não encontrado"
            
            messagebox.showinfo("Teste de Dispositivo", message)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao testar dispositivo: {str(e)}")
    
    def save_settings(self):
        """Salvar configurações"""
        try:
            import json
            from pathlib import Path
            
            # Criar diretório se não existir
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            # Carregar configurações existentes de API
            api_config_file = config_dir / "api_keys.json"
            if api_config_file.exists():
                with open(api_config_file, 'r') as f:
                    api_config = json.load(f)
            else:
                api_config = {}
            
            # Salvar chaves API se fornecidas
            openai_key = self.openai_key_var.get()
            if openai_key and not openai_key.startswith('*'):
                api_config["openai_api_key"] = openai_key
            
            gemini_key = self.gemini_key_var.get()
            if gemini_key and not gemini_key.startswith('*'):
                api_config["gemini_api_key"] = gemini_key
            
            # Salvar provedor preferido
            api_config["ai_provider"] = self.ai_provider_var.get()
            
            # Salvar arquivo de API
            with open(api_config_file, 'w') as f:
                json.dump(api_config, f, indent=2)
            
            # Recarregar configurações nos módulos
            self.app.transcriber.load_config()
            self.app.summarizer.load_config()
            
            # Salvar configurações de áudio
            settings_file = config_dir / "settings.json"
            
            # Carregar configurações existentes ou usar padrão
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {
                    "audio": {
                        "sample_rate": 44100,
                        "channels": 2,
                        "chunk_size": 1024,
                        "input_device": None
                    },
                    "ai": {
                        "model": "gpt-3.5-turbo",
                        "max_tokens": 1500,
                        "temperature": 0.3,
                        "language": "pt"
                    },
                    "ui": {
                        "theme": "clam",
                        "window_size": "900x700",
                        "auto_save": False
                    },
                    "output": {
                        "format": "txt",
                        "directory": "outputs",
                        "include_timestamp": True
                    }
                }
            
            # Atualizar configurações de áudio
            selected_text = self.device_var.get()
            device_index = self.device_mapping.get(selected_text)
            settings["audio"]["input_device"] = device_index
            settings["audio"]["sample_rate"] = int(self.sample_rate_var.get())
            settings["audio"]["record_system_audio"] = self.system_audio_var.get()
            
            # Salvar configurações
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Aplicar configurações no gravador
            self.apply_audio_settings()
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {str(e)}")
    
    def apply_audio_settings(self):
        """Aplicar configurações de áudio ao gravador"""
        try:
            selected_text = self.device_var.get()
            device_index = self.device_mapping.get(selected_text)
            self.app.audio_recorder.set_input_device(device_index)
            
            # Aplicar sample rate
            sample_rate = int(self.sample_rate_var.get())
            self.app.audio_recorder.rate = sample_rate
            
            # Aplicar configuração de áudio do sistema
            system_audio = self.system_audio_var.get()
            self.app.audio_recorder.set_record_system_audio(system_audio)
            
        except Exception as e:
            print(f"Erro ao aplicar configurações de áudio: {e}")
    
    def on_provider_change(self):
        """Callback quando o provedor de IA é alterado"""
        provider = self.ai_provider_var.get()
        print(f"Provedor de IA alterado para: {provider}")
    
    def check_system_audio(self):
        """Verificar capacidade de gravação de áudio do sistema"""
        try:
            can_record, message = self.app.audio_recorder.check_system_audio_capability()
            
            if can_record:
                messagebox.showinfo("✅ Áudio do Sistema", f"Captura de áudio do sistema disponível!\n\n{message}")
            else:
                # Mostrar instruções para habilitar
                instructions = self.app.audio_recorder.get_system_audio_setup_instructions()
                result = messagebox.askyesno(
                    "⚠️  Áudio do Sistema", 
                    f"Captura de áudio do sistema não disponível.\n\n{message}\n\nDeseja ver as instruções para habilitar?",
                    icon='warning'
                )
                
                if result:
                    # Criar janela com instruções
                    instruction_window = tk.Toplevel(self.window)
                    instruction_window.title("Instruções - Áudio do Sistema")
                    instruction_window.geometry("600x500")
                    instruction_window.transient(self.window)
                    
                    # Texto com instruções
                    text_widget = tk.Text(instruction_window, wrap=tk.WORD, padx=10, pady=10)
                    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_widget.insert('1.0', instructions)
                    text_widget.configure(state='disabled')
                    
                    # Botão para fechar
                    ttk.Button(
                        instruction_window, 
                        text="Fechar", 
                        command=instruction_window.destroy
                    ).pack(pady=10)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar áudio do sistema: {str(e)}")
    
    def load_api_settings(self):
        """Carregar configurações de API das chaves já salvas"""
        try:
            import json
            from pathlib import Path
            
            config_file = Path("config/api_keys.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Carregar chaves API (mostrar apenas asteriscos se existir)
                    if config.get('openai_api_key'):
                        self.openai_key_var.set('*' * 20)
                    
                    if config.get('gemini_api_key'):
                        self.gemini_key_var.set('*' * 20)
                    
                    # Carregar provedor preferido
                    provider = config.get('ai_provider', 'openai')
                    self.ai_provider_var.set(provider)
                    
        except Exception as e:
            print(f"Erro ao carregar configurações de API: {e}")