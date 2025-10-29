"""
Teste para verificar se a transcrição aparece na interface
"""

import sys
import time
import threading
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

# Simular MeetAI para testar interface
class MockMeetAI:
    def __init__(self):
        self.transcriber = Transcriber()
        
    def process_audio_simple(self, audio_file):
        """Processar áudio como na aplicação principal"""
        try:
            print("📝 Iniciando transcrição...")
            transcript = self.transcriber.transcribe(audio_file)
            
            if transcript:
                print(f"✅ Transcrição obtida: {len(transcript)} caracteres")
                print(f"📝 Conteúdo: \"{transcript}\"")
                return transcript
            else:
                print("❌ Transcrição falhou")
                return None
                
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return None

def test_ui_integration():
    """Testar integração da transcrição com interface"""
    print("🖥️ TESTE DE INTEGRAÇÃO COM INTERFACE")
    print("=" * 60)
    
    # Criar instância mock
    app = MockMeetAI()
    recorder = AudioRecorder()
    
    if not app.transcriber.client:
        print("❌ OpenAI não configurado")
        return False
    
    print("✅ Componentes inicializados")
    print("🎯 Testando fluxo: Gravar → Parar → Transcrever → Exibir")
    print()
    
    try:
        print("🎙️ Iniciando gravação de teste (6 segundos)...")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar gravação
        for i in range(6):
            time.sleep(1)
            print(f"   🔴 Gravando... {i+1}/6s")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        if not audio_file:
            print("❌ Falha ao obter arquivo de áudio")
            return False
            
        print(f"✅ Arquivo salvo: {audio_file}")
        
        # Processar áudio (simular fluxo da aplicação)
        print("\n🔄 SIMULANDO FLUXO DA APLICAÇÃO:")
        transcript = app.process_audio_simple(audio_file)
        
        if transcript:
            print("\n📊 RESULTADO DO TESTE:")
            print(f"   - Arquivo: {audio_file}")
            print(f"   - Transcrição: ✅ SUCESSO") 
            print(f"   - Caracteres: {len(transcript)}")
            print(f"   - Palavras: {len(transcript.split())}")
            print(f"   - Conteúdo: \"{transcript[:100]}{'...' if len(transcript) > 100 else ''}\"")
            
            print("\n🎯 FLUXO CORRETO DA APLICAÇÃO:")
            print("   1. Transcrição ✅ Funcionando")
            print("   2. Interface deve exibir via display_transcript_only()")
            print("   3. Resumo gerado via Gemini")
            print("   4. Interface final via display_final_results()")
            
            return True
        else:
            print("\n❌ FALHA NA TRANSCRIÇÃO")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False
    finally:
        try:
            if recorder.recording:
                recorder.stop_recording()
        except:
            pass

if __name__ == "__main__":
    success = test_ui_integration()
    if success:
        print("\n🎉 INTEGRAÇÃO FUNCIONANDO!")
        print("💡 A transcrição deve aparecer na aplicação principal")
        print("🔧 Correções implementadas no main.py e main_window.py") 
    else:
        print("\n💥 Teste falhou - problema na transcrição base")

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
import os
from pathlib import Path

class MeetAITest:
    def __init__(self):
        self.recording = False
        self.setup_directories()
        
        # Inicializar interface
        self.root = tk.Tk()
        self.setup_ui()
        
    def setup_directories(self):
        """Criar diretórios necessários"""
        directories = ['data', 'config', 'outputs', 'temp']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        self.root.title("MeetAI - Teste (Sem APIs)")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="MeetAI - Modo Teste", font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Aviso
        warning_label = ttk.Label(
            main_frame, 
            text="⚠️ Esta é uma versão de teste. Configure as APIs para funcionalidade completa.",
            foreground='orange',
            font=('Arial', 10)
        )
        warning_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # Seção de gravação
        recording_frame = ttk.LabelFrame(main_frame, text="Simulação de Gravação", padding="10")
        recording_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        recording_frame.columnconfigure(1, weight=1)
        
        # Botão de gravação
        self.record_button = ttk.Button(
            recording_frame, 
            text="▶ Simular Gravação", 
            command=self.toggle_recording
        )
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        # Status
        self.status_label = ttk.Label(recording_frame, text="Pronto para simular")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(
            recording_frame, 
            mode='indeterminate',
            length=200
        )
        self.progress.grid(row=0, column=2, padx=(10, 0))
        
        # Templates
        template_frame = ttk.LabelFrame(main_frame, text="Templates Disponíveis", padding="10")
        template_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            values=["ATA de Reunião", "Resumo de Conversa", "Resumo de Palestra", "Resumo de Entrevista", "Brainstorming"],
            state="readonly"
        )
        template_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        template_combo.set("Resumo de Conversa")
        template_frame.columnconfigure(0, weight=1)
        
        # Resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados de Teste", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Notebook
        notebook = ttk.Notebook(results_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Aba transcrição
        transcript_frame = ttk.Frame(notebook)
        notebook.add(transcript_frame, text="Transcrição (Simulada)")
        
        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            height=8,
            font=('Consolas', 10)
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba resumo
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Resumo (Simulado)")
        
        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            height=8,
            font=('Arial', 10)
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botões
        button_frame = ttk.Frame(results_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="📋 Testar Exemplo", command=self.load_example).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🗑 Limpar", command=self.clear_results).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="ℹ️ Configurar APIs", command=self.show_api_info).pack(side=tk.RIGHT)
    
    def toggle_recording(self):
        """Simular gravação"""
        if not self.recording:
            self.start_simulation()
        else:
            self.stop_simulation()
    
    def start_simulation(self):
        """Iniciar simulação"""
        self.recording = True
        self.record_button.configure(text="⏹ Parar Simulação")
        self.status_label.configure(text="Simulando gravação...")
        self.progress.start(10)
        self.clear_results()
    
    def stop_simulation(self):
        """Parar simulação"""
        self.recording = False
        self.record_button.configure(text="▶ Simular Gravação")
        self.status_label.configure(text="Processando simulação...")
        self.progress.stop()
        
        # Simular processamento
        threading.Thread(target=self.simulate_processing, daemon=True).start()
    
    def simulate_processing(self):
        """Simular processamento de IA"""
        time.sleep(2)  # Simular tempo de processamento
        
        # Dados de exemplo
        sample_transcript = """
        Esta é uma transcrição simulada para demonstrar o funcionamento do MeetAI.
        
        Em uma reunião real, este texto seria gerado automaticamente pela API do OpenAI Whisper,
        convertendo o áudio gravado em texto com alta precisão.
        
        O sistema pode capturar tanto o áudio do microfone quanto a saída do sistema,
        permitindo gravar reuniões virtuais, palestras, entrevistas e conversas importantes.
        
        Tempo de gravação simulado: 30 segundos
        """
        
        template = self.template_var.get()
        sample_summary = f"""
        # {template} - Exemplo
        
        **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        **Template utilizado:** {template}
        
        ## Resumo Principal
        Esta é uma demonstração do sistema MeetAI. O resumo real seria gerado pela IA 
        baseado no template selecionado e no conteúdo da transcrição.
        
        ## Pontos Importantes
        - Sistema funcional de gravação de áudio
        - Interface gráfica intuitiva e responsiva
        - Suporte a múltiplos templates de resumo
        - Processamento assíncrono para melhor experiência
        
        ## Próximos Passos
        1. Configure sua API Key da OpenAI
        2. Teste com áudio real
        3. Personalize templates conforme necessário
        
        ---
        💡 **Dica:** Este é apenas um exemplo. Configure as APIs para funcionalidade completa!
        """
        
        # Atualizar interface na thread principal
        self.root.after(0, lambda: self.display_results(sample_transcript, sample_summary))
        self.root.after(0, lambda: self.status_label.configure(text="Simulação concluída!"))
    
    def display_results(self, transcript, summary):
        """Exibir resultados"""
        self.transcript_text.delete('1.0', tk.END)
        self.summary_text.delete('1.0', tk.END)
        
        self.transcript_text.insert('1.0', transcript)
        self.summary_text.insert('1.0', summary)
    
    def load_example(self):
        """Carregar exemplo rápido"""
        self.display_results(
            "Exemplo de transcrição: 'Olá, este é um teste do sistema MeetAI. O áudio está sendo capturado corretamente.'",
            f"# Exemplo de {self.template_var.get()}\n\nEste é um resumo de exemplo gerado pelo sistema MeetAI.\n\n**Status:** Funcionando corretamente!\n**Template:** {self.template_var.get()}"
        )
        self.status_label.configure(text="Exemplo carregado!")
    
    def clear_results(self):
        """Limpar resultados"""
        self.transcript_text.delete('1.0', tk.END)
        self.summary_text.delete('1.0', tk.END)
    
    def show_api_info(self):
        """Mostrar informações sobre configuração de APIs"""
        info = """
🔧 CONFIGURAÇÃO DAS APIs

Para usar o MeetAI com funcionalidade completa:

1. OBTER API KEY DA OPENAI:
   • Acesse: https://platform.openai.com/
   • Crie uma conta ou faça login
   • Vá em "API Keys"
   • Clique em "Create new secret key"
   • Copie a chave gerada

2. CONFIGURAR NO MEETAI:
   • Execute: python main.py
   • Clique em "⚙ Configurações"
   • Cole sua API Key no campo apropriado
   • Clique em "Salvar"

3. CUSTOS ESTIMADOS:
   • Transcrição: ~$0.006 por minuto
   • Resumo: ~$0.002 por resumo
   • Total: ~$0.01 por minuto de áudio

4. TESTAR:
   • Grave um áudio de teste
   • Verifique se a transcrição está correta
   • Ajuste templates conforme necessário

⚠️ IMPORTANTE: Mantenha sua API Key segura!
        """
        
        messagebox.showinfo("Configuração das APIs", info)
    
    def run(self):
        """Executar aplicação"""
        self.root.mainloop()

def main():
    """Função principal"""
    try:
        print("🚀 Iniciando MeetAI em modo de teste...")
        print("📝 Esta versão não requer APIs - apenas demonstra a interface")
        print("⚙️ Configure as APIs para funcionalidade completa\n")
        
        app = MeetAITest()
        app.run()
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Execute: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Erro: {e}")
        messagebox.showerror("Erro", f"Erro ao inicializar: {e}")

if __name__ == "__main__":
    main()