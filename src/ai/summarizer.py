"""
Módulo de geração de resumos usando IA (OpenAI e Gemini)
"""

import openai
import json
from pathlib import Path

class Summarizer:
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self.ai_provider = "openai"  # padrão
        self.templates = {}
        self.load_config()
        self.load_templates()
    
    def load_config(self):
        """Carregar configurações das APIs"""
        config_file = Path("config/api_keys.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                
                # Configurar OpenAI
                openai_key = config.get('openai_api_key')
                if openai_key:
                    self.openai_client = openai.OpenAI(api_key=openai_key)
                
                # Configurar Gemini
                gemini_key = config.get('gemini_api_key')
                if gemini_key:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=gemini_key)
                        self.gemini_client = genai.GenerativeModel('gemini-2.5-flash')
                    except ImportError:
                        print("Biblioteca google-generativeai não encontrada. Execute: pip install google-generativeai")
                    except Exception as e:
                        print(f"Erro ao configurar Gemini: {e}")
                
                # Definir provedor preferido
                self.ai_provider = config.get('ai_provider', 'openai')
                
                # Aplicar o provedor selecionado
                self.set_ai_provider(self.ai_provider)
    
    def load_templates(self):
        """Carregar templates de resumo"""
        templates_dir = Path("src/templates")
        
        # Templates padrão removidos - usando apenas templates personalizados
        self.templates = {}
        
        # Carregar templates personalizados se existirem
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        custom_template = json.load(f)
                        template_id = template_file.stem
                        self.templates[template_id] = custom_template
                except Exception as e:
                    print(f"Erro ao carregar template {template_file}: {e}")
    
    def get_available_templates(self):
        """Retornar lista de templates disponíveis"""
        return [(key, template["name"]) for key, template in self.templates.items()]
    
    def set_ai_provider(self, provider):
        """Definir qual provedor de IA usar"""
        if provider in ["openai", "gemini"]:
            self.ai_provider = provider
            return True
        return False
    
    def get_current_provider(self):
        """Retornar provedor atual"""
        return self.ai_provider
    
    def is_provider_available(self, provider):
        """Verificar se o provedor está disponível"""
        if provider == "openai":
            return self.openai_client is not None
        elif provider == "gemini":
            return self.gemini_client is not None
        return False
    
    def generate_summary(self, transcript, template_id="auto"):
        """Gerar resumo usando o template especificado"""
        if not transcript or transcript.strip() == "":
            raise Exception("Transcrição vazia")
        
        # Usar o template solicitado ou "auto" como padrão
        if template_id not in self.templates:
            template_id = "auto"  # Fallback para template Auto
        
        template = self.templates.get(template_id)
        
        # Se ainda não encontrou o template, usar o primeiro disponível
        if not template and self.templates:
            template_id = list(self.templates.keys())[0]
            template = self.templates[template_id]
        
        if not template:
            raise Exception(f"Template '{template_id}' não encontrado e nenhum template disponível")
        
        # Usar o provedor configurado
        if self.ai_provider == "openai":
            return self._generate_summary_openai(transcript, template)
        elif self.ai_provider == "gemini":
            return self._generate_summary_gemini(transcript, template)
        else:
            raise Exception("Provedor de IA não configurado")
    
    def _generate_summary_openai(self, transcript, template):
        """Gerar resumo usando OpenAI"""
        if not self.openai_client:
            raise Exception("API Key da OpenAI não configurada")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": template["prompt"]
                    },
                    {
                        "role": "user", 
                        "content": f"Transcrição para resumir:\n\n{transcript}"
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Erro na geração do resumo com OpenAI: {e}")
            return None
    
    def _generate_summary_gemini(self, transcript, template):
        """Gerar resumo usando Gemini"""
        if not self.gemini_client:
            raise Exception("API Key do Gemini não configurada")
        
        try:
            # Construir prompt para Gemini
            full_prompt = f"""
            {template["prompt"]}
            
            Transcrição para resumir:
            {transcript}
            
            Por favor, crie um resumo seguindo exatamente a estrutura solicitada acima.
            """
            
            response = self.gemini_client.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Erro na geração do resumo com Gemini: {e}")
            return None
    
    def create_custom_template(self, template_id, name, prompt):
        """Criar template personalizado"""
        template = {
            "name": name,
            "prompt": prompt
        }
        
        # Salvar no diretório de templates
        templates_dir = Path("src/templates")
        templates_dir.mkdir(exist_ok=True)
        
        template_file = templates_dir / f"{template_id}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        # Adicionar ao dicionário de templates
        self.templates[template_id] = template
        
        return True