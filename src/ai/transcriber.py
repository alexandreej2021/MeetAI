"""
Módulo de transcrição usando OpenAI Whisper
"""

import openai
import os
from pathlib import Path
import json
import wave
import numpy as np
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class Transcriber:
    def __init__(self):
        self.client = None
        self.load_config()
    
    def load_config(self):
        """Carregar configurações da API"""
        config_file = Path("config/api_keys.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                api_key = config.get('openai_api_key')
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
    
    def get_file_size_mb(self, file_path):
        """Obter tamanho do arquivo em MB"""
        return os.path.getsize(file_path) / (1024 * 1024)
    
    def split_audio_file(self, input_file, max_size_mb=20):
        """Dividir arquivo de áudio em pedaços menores se necessário"""
        file_size_mb = self.get_file_size_mb(input_file)
        
        if file_size_mb <= max_size_mb:
            return [input_file]  # Arquivo pequeno o suficiente
        
        print(f"📂 Arquivo muito grande ({file_size_mb:.1f}MB). Dividindo em pedaços...")
        
        # Abrir arquivo WAV
        with wave.open(input_file, 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            params = wav_file.getparams()
            
            # Calcular quantos pedaços precisamos
            num_chunks = int(np.ceil(file_size_mb / max_size_mb))
            frames_per_chunk = len(frames) // num_chunks
            
            chunk_files = []
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            for i in range(num_chunks):
                chunk_filename = temp_dir / f"chunk_{i+1}.wav"
                
                start_frame = i * frames_per_chunk
                if i == num_chunks - 1:  # Último pedaço
                    end_frame = len(frames)
                else:
                    end_frame = (i + 1) * frames_per_chunk
                
                chunk_frames = frames[start_frame:end_frame]
                
                # Salvar pedaço
                with wave.open(str(chunk_filename), 'wb') as chunk_file:
                    chunk_file.setparams(params)
                    chunk_file.writeframes(chunk_frames)
                
                chunk_files.append(str(chunk_filename))
                print(f"  📄 Pedaço {i+1}/{num_chunks}: {chunk_filename.name}")
        
        return chunk_files
    
    def cleanup_temp_files(self, temp_files):
        """Limpar arquivos temporários"""
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file) and "chunk_" in temp_file:
                    os.remove(temp_file)
            except Exception as e:
                print(f"⚠️ Erro ao remover arquivo temporário {temp_file}: {e}")
    
    def transcribe(self, audio_file):
        """Transcrever arquivo de áudio"""
        if not self.client:
            raise Exception("API Key da OpenAI não configurada")
        
        if not os.path.exists(audio_file):
            raise Exception(f"Arquivo de áudio não encontrado: {audio_file}")
        
        try:
            # Verificar tamanho do arquivo e dividir se necessário
            file_size_mb = self.get_file_size_mb(audio_file)
            print(f"📁 Tamanho do arquivo: {file_size_mb:.1f}MB")
            
            if file_size_mb > 15:  # Limite otimizado para melhor paralelismo
                return self._transcribe_large_file(audio_file)
            else:
                return self._transcribe_single_file(audio_file)
                
        except Exception as e:
            print(f"Erro na transcrição: {e}")
            return None
    
    def _transcribe_single_file(self, audio_file):
        """Transcrever um único arquivo"""
        with open(audio_file, "rb") as audio:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="pt"  # Português
            )
        return response.text
    
    def _transcribe_large_file(self, audio_file):
        """Transcrever arquivo grande dividindo em pedaços com processamento paralelo"""
        print("🔄 Processando arquivo grande com transcrição simultânea...")
        
        # Dividir arquivo em pedaços menores para melhor paralelismo
        chunk_files = self.split_audio_file(audio_file, max_size_mb=12)
        
        if len(chunk_files) == 1:
            # Arquivo não foi dividido
            return self._transcribe_single_file(audio_file)
        
        # Transcrever pedaços em paralelo
        print(f"🚀 Iniciando transcrição simultânea de {len(chunk_files)} pedaços...")
        start_time = time.time()
        
        # Usar ThreadPoolExecutor para processamento paralelo
        transcripts = {}
        with ThreadPoolExecutor(max_workers=min(len(chunk_files), 4)) as executor:
            # Submeter todas as tarefas
            future_to_index = {
                executor.submit(self._transcribe_chunk_with_index, i, chunk_file): i 
                for i, chunk_file in enumerate(chunk_files)
            }
            
            # Coletar resultados conforme completam
            for future in as_completed(future_to_index):
                chunk_index = future_to_index[future]
                try:
                    result = future.result()
                    if result:
                        transcripts[chunk_index] = result
                        print(f"✅ Pedaço {chunk_index + 1}/{len(chunk_files)} concluído")
                    else:
                        print(f"❌ Erro no pedaço {chunk_index + 1}/{len(chunk_files)}")
                except Exception as e:
                    print(f"❌ Erro ao processar pedaço {chunk_index + 1}: {e}")
        
        # Montar transcrição final na ordem correta
        full_transcript = ""
        for i in range(len(chunk_files)):
            if i in transcripts:
                if full_transcript and not full_transcript.endswith(" "):
                    full_transcript += " "
                full_transcript += transcripts[i]
            else:
                print(f"⚠️ Pedaço {i + 1} não foi transcrito com sucesso")
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ Transcrição simultânea concluída em {elapsed_time:.1f} segundos")
        
        # Limpar arquivos temporários
        self.cleanup_temp_files(chunk_files)
        
        return full_transcript if full_transcript else None
    
    def _transcribe_chunk_with_index(self, index, chunk_file):
        """Transcrever um pedaço específico com índice (para processamento paralelo)"""
        try:
            print(f"🎯 Iniciando pedaço {index + 1}...")
            result = self._transcribe_single_file(chunk_file)
            return result
        except Exception as e:
            print(f"❌ Erro ao transcrever pedaço {index + 1}: {e}")
            return None
    
    def transcribe_with_timestamps(self, audio_file):
        """Transcrever com timestamps (para funcionalidade futura)"""
        if not self.client:
            raise Exception("API Key da OpenAI não configurada")
        
        try:
            with open(audio_file, "rb") as audio:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="pt",
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            return response.segments
            
        except Exception as e:
            print(f"Erro na transcrição com timestamps: {e}")
            return None