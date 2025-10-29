"""
Módulo de geração de resumos usando Google Gemini
"""

import json
from pathlib import Path

class GeminiSummarizer:
    def __init__(self):
        self.client = None
        self.templates = {}
        self.load_config()
        self.load_templates()
    
    def load_config(self):
        """Carregar configurações da API do Gemini"""
        config_file = Path("config/api_keys.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                api_key = config.get('gemini_api_key')
                if api_key:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        self.client = genai.GenerativeModel('gemini-2.5-flash')
                        print("Gemini configurado com sucesso")
                    except ImportError:
                        print("Biblioteca google-generativeai não encontrada. Execute: pip install google-generativeai")
                    except Exception as e:
                        print(f"Erro ao configurar Gemini: {e}")
    
    def load_templates(self):
        """Carregar templates de resumo (mesmos do OpenAI)"""
        templates_dir = Path("src/templates")
        
        # Templates padrão (mesmos do OpenAI)
        self.templates = {
            "reuniao": {
                "name": "ATA de Reunião",
                "prompt": """
                Analise a transcrição de uma reunião e crie uma ATA (Ata de Reunião) estruturada com:
                
                1. **Participantes**: Liste os participantes mencionados
                2. **Pauta**: Principais tópicos discutidos
                3. **Decisões**: Decisões tomadas durante a reunião
                4. **Ações**: Tarefas definidas e responsáveis
                5. **Próximos Passos**: O que precisa ser feito após a reunião
                
                Mantenha um tom formal e profissional.
                """
            },
            "conversa": {
                "name": "Resumo de Conversa",
                "prompt": """
                Faça um resumo conciso desta conversa, destacando:
                
                1. **Tema Principal**: O assunto central da conversa
                2. **Pontos Importantes**: Os pontos mais relevantes discutidos
                3. **Conclusões**: As principais conclusões ou insights
                4. **Observações**: Qualquer informação adicional relevante
                
                Use linguagem clara e objetiva.
                """
            },
            "palestra": {
                "name": "Resumo de Palestra/Apresentação",
                "prompt": """
                Crie um resumo estruturado desta palestra/apresentação incluindo:
                
                1. **Tema/Título**: O tema principal apresentado
                2. **Objetivos**: Os objetivos da apresentação
                3. **Pontos Principais**: Os conceitos e ideias centrais
                4. **Exemplos/Casos**: Exemplos ou casos práticos mencionados
                5. **Conclusões**: As principais conclusões e takeaways
                
                Organize de forma didática e fácil de entender.
                """
            },
            "entrevista": {
                "name": "Resumo de Entrevista",
                "prompt": """
                Resuma esta entrevista organizando as informações em:
                
                1. **Participantes**: Entrevistador(a) e entrevistado(a)
                2. **Contexto**: Propósito da entrevista
                3. **Perguntas e Respostas**: Principais perguntas e respostas
                4. **Insights**: Insights ou informações importantes
                5. **Perfil**: Perfil do entrevistado (se aplicável)
                
                Mantenha fidelidade ao conteúdo original.
                """
            }
        }
        
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
    
    def generate_summary(self, transcript, template_id="conversa"):
        """Gerar resumo usando o Gemini"""
        if not self.client:
            raise Exception("API Key do Gemini não configurada")
        
        if not transcript or transcript.strip() == "":
            raise Exception("Transcrição vazia")
        
        template = self.templates.get(template_id, self.templates["conversa"])
        
        try:
            # Construir prompt para Gemini
            full_prompt = f"""
            {template["prompt"]}
            
            Transcrição para resumir:
            {transcript}
            
            Por favor, crie um resumo seguindo exatamente a estrutura solicitada acima.
            """
            
            response = self.client.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Erro na geração do resumo com Gemini: {e}")
            return None
    
    def create_custom_template(self, template_id, name, prompt):
        """Criar template personalizado (mesmo método do OpenAI)"""
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