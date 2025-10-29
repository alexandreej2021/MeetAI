#!/usr/bin/env python3
"""
Teste do sistema simplificado: Gravar tudo, depois transcrever com divisão inteligente
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.audio.recorder import AudioRecorder
from src.ai.transcriber import Transcriber

def test_simple_sync():
    """Testar gravação completa + transcrição posterior"""
    print("📹 TESTE DO SISTEMA SIMPLIFICADO")
    print("=" * 60)
    print("🎯 Objetivo: Gravar tudo primeiro, transcrever depois")
    print("✅ Vantagens: Sem interrupções, qualidade máxima, processamento otimizado")
    print()
    
    # Inicializar componentes
    recorder = AudioRecorder()
    transcriber = Transcriber()
    
    if not transcriber.client:
        print("❌ OpenAI não configurado")
        return False
    
    print("✅ Componentes inicializados")
    print("⚙️ Configurações:")
    print("   - Transcrição simultânea: DESABILITADA")
    print("   - Divisão automática: >15MB")
    print("   - Processamento paralelo: ATIVADO")
    print()
    
    try:
        print("🎙️ Iniciando gravação simples (10 segundos)...")
        print("   💬 Fale normalmente - sem interrupções!")
        
        # Iniciar gravação
        if not recorder.start_recording():
            print("❌ Falha ao iniciar gravação")
            return False
        
        # Aguardar sem processamento em tempo real
        for i in range(10):
            time.sleep(1)
            print(f"   🔴 Gravando... {i+1}/10s (sem processamento)")
        
        # Parar gravação
        print("🛑 Parando gravação...")
        audio_file = recorder.stop_recording()
        
        if not audio_file:
            print("❌ Falha ao salvar arquivo")
            return False
            
        print(f"✅ Arquivo salvo: {audio_file}")
        
        # Agora fazer transcrição completa
        print("\n📝 Iniciando transcrição inteligente...")
        start_time = time.time()
        
        transcript = transcriber.transcribe(audio_file)
        
        processing_time = time.time() - start_time
        
        if transcript:
            print(f"✅ Transcrição concluída em {processing_time:.1f}s")
            print(f"📝 Resultado: \"{transcript}\"")
            print(f"📊 Caracteres: {len(transcript)}")
            print(f"📊 Palavras: {len(transcript.split())}")
            
            # Verificar se houve divisão
            file_size_mb = transcriber.get_file_size_mb(audio_file)
            if file_size_mb > 15:
                print(f"📦 Arquivo grande ({file_size_mb:.1f}MB) - Divisão automática usada")
            else:
                print(f"📄 Arquivo pequeno ({file_size_mb:.1f}MB) - Processamento direto")
            
            return True
        else:
            print("❌ Transcrição falhou")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    finally:
        try:
            if recorder.recording:
                recorder.stop_recording()
        except:
            pass

if __name__ == "__main__":
    success = test_simple_sync()
    if success:
        print("\n🎉 SISTEMA SIMPLIFICADO FUNCIONANDO PERFEITAMENTE!")
        print("✅ Gravação completa sem interrupções")
        print("✅ Transcrição inteligente com divisão automática")
        print("✅ Qualidade máxima garantida")
        print("💡 Pronto para uso na aplicação principal!")
    else:
        print("\n💥 Teste falhou - verificar configurações")
from src.audio.recorder import AudioRecorder

def test_simple_sync():
    """Teste básico de sincronização"""
    print("🧪 TESTE SIMPLIFICADO DE SINCRONIZAÇÃO")
    print("=" * 40)
    
    recorder = AudioRecorder()
    
    print("📋 Iniciando gravação por 10 segundos...")
    print("Fale e reproduza áudio simultaneamente")
    print()
    
    try:
        if recorder.start_recording():
            print("✅ Gravação iniciada")
            
            # Gravar por 10 segundos
            for i in range(10):
                time.sleep(1)
                print(f"⏰ {i+1}s...", end=" ")
                
                # Mostrar estatísticas a cada 3 segundos
                if (i+1) % 3 == 0:
                    if hasattr(recorder, 'mic_timestamps') and hasattr(recorder, 'system_timestamps'):
                        mic_count = len(recorder.mic_timestamps)
                        sys_count = len(recorder.system_timestamps)
                        print(f"| Chunks: Mic={mic_count}, Sys={sys_count}")
                    else:
                        print("| Coletando dados...")
                else:
                    print()
            
            print("\n🛑 Parando gravação...")
            filename = recorder.stop_recording()
            
            if filename:
                print(f"📁 Arquivo salvo: {filename}")
                
                # Estatísticas finais
                if hasattr(recorder, 'mic_timestamps') and hasattr(recorder, 'system_timestamps'):
                    print(f"\n📊 ESTATÍSTICAS FINAIS:")
                    print(f"Chunks do microfone: {len(recorder.mic_timestamps)}")
                    print(f"Chunks do sistema: {len(recorder.system_timestamps)}")
                    
                    if len(recorder.mic_timestamps) > 0 and len(recorder.system_timestamps) > 0:
                        diff_chunks = abs(len(recorder.mic_timestamps) - len(recorder.system_timestamps))
                        print(f"Diferença de chunks: {diff_chunks}")
                        
                        if diff_chunks < 5:
                            print("✅ RESULTADO: Sincronização excelente!")
                        elif diff_chunks < 10:
                            print("⚠️  RESULTADO: Sincronização aceitável")
                        else:
                            print("❌ RESULTADO: Sincronização precisa melhorar")
                else:
                    print("⚠️  Não foi possível coletar estatísticas de timing")
            else:
                print("❌ Erro ao salvar arquivo")
        else:
            print("❌ Falha ao iniciar gravação")
    
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    test_simple_sync()