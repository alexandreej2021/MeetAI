# -*- coding: utf-8 -*-
"""Stack de captura e processamento de áudio do MeetAI."""

from __future__ import annotations

import json
import threading
import time
import wave
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Deque, List, Optional, Tuple

import numpy as np
import sounddevice as sd

RealtimeCallback = Callable[[str, int], None]

SYSTEM_KEYWORDS = [
    "stereo mix",
    "mixagem",
    "loopback",
    "what u hear",
    "wave out mix",
    "sum",
    "alto-falantes (loopback)",
]


class AudioProcessor:
    """Coleção de utilidades para tratamento de áudio em int16."""

    @staticmethod
    def db_to_linear(db_value: float) -> float:
        return 10.0 ** (db_value / 20.0)

    @staticmethod
    def linear_to_db(linear_gain: float) -> float:
        if linear_gain <= 0:
            return -80.0
        return 20.0 * np.log10(linear_gain)

    @staticmethod
    def safe_clip(audio: np.ndarray) -> np.ndarray:
        return np.clip(audio, -32768, 32767).astype(np.int16, copy=False)

    @staticmethod
    def apply_gain(audio: np.ndarray, gain_db: float) -> np.ndarray:
        if audio.size == 0 or gain_db == 0.0:
            return audio
        gain = AudioProcessor.db_to_linear(gain_db)
        amplified = audio.astype(np.float64) * gain
        return AudioProcessor.safe_clip(amplified)

    @staticmethod
    def high_pass_filter(audio: np.ndarray, sample_rate: int, cutoff: float = 80.0) -> np.ndarray:
        if audio.size < 2:
            return audio

        rc = 1.0 / (2 * np.pi * cutoff)
        dt = 1.0 / sample_rate
        alpha = rc / (rc + dt)

        filtered = np.zeros_like(audio, dtype=np.float64)
        filtered[0] = audio[0]
        for idx in range(1, len(audio)):
            filtered[idx] = alpha * (filtered[idx - 1] + audio[idx] - audio[idx - 1])
        return AudioProcessor.safe_clip(filtered)

    @staticmethod
    def apply_noise_gate(
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -65.0,
        attack_ms: float = 6.0,
        release_ms: float = 200.0,
        hold_ms: float = 250.0,
        floor: float = 0.3,
    ) -> np.ndarray:
        if audio.size == 0:
            return audio

        threshold = 32767.0 * (10.0 ** (threshold_db / 20.0))
        window = max(1, int(sample_rate * 0.01))

        squares = audio.astype(np.float64) ** 2
        kernel = np.ones(window)
        moving_rms = np.sqrt(np.convolve(squares, kernel, "same") / window)

        attack_samples = max(1, int(attack_ms * sample_rate / 1000))
        release_samples = max(1, int(release_ms * sample_rate / 1000))
        hold_samples = max(1, int(hold_ms * sample_rate / 1000))
        gate_state = floor
        hold_counter = 0
        output = np.zeros_like(audio, dtype=np.float64)

        for idx, sample in enumerate(audio.astype(np.float64)):
            if moving_rms[idx] >= threshold:
                gate_state += (1.0 - gate_state) / attack_samples
                hold_counter = hold_samples
            else:
                if hold_counter > 0:
                    hold_counter -= 1
                else:
                    gate_state -= (gate_state - floor) / release_samples

            gate_state = np.clip(gate_state, floor, 1.0)
            output[idx] = sample * gate_state

        return AudioProcessor.safe_clip(output)

    @staticmethod
    def apply_compressor(
        audio: np.ndarray,
        threshold_db: float = -16.0,
        ratio: float = 3.5,
        makeup_gain_db: float = 1.5,
    ) -> np.ndarray:
        if audio.size == 0:
            return audio

        audio_float = audio.astype(np.float64)
        threshold = 32767.0 * (10.0 ** (threshold_db / 20.0))

        magnitude = np.abs(audio_float)
        over_threshold = magnitude > threshold
        if np.any(over_threshold):
            excess = magnitude[over_threshold] - threshold
            compressed = threshold + (excess / ratio)
            audio_float[over_threshold] = np.sign(audio_float[over_threshold]) * compressed

        audio_float *= AudioProcessor.db_to_linear(makeup_gain_db)
        return AudioProcessor.safe_clip(audio_float)

    @staticmethod
    def normalize(audio: np.ndarray, target_db: float = -14.0) -> np.ndarray:
        if audio.size == 0:
            return audio

        rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
        if rms < 1e-6:
            return audio

        target = 32767.0 * (10.0 ** (target_db / 20.0))
        gain = target / rms
        gain = min(gain, 5.0)
        normalized = audio.astype(np.float64) * gain
        return AudioProcessor.safe_clip(normalized)

    @staticmethod
    def reduce_echo(
        system_audio: np.ndarray,
        mic_audio: np.ndarray,
        sample_rate: int,
        strength: float = 0.55,
    ) -> np.ndarray:
        if system_audio.size == 0 or mic_audio.size == 0:
            return system_audio

        length = min(system_audio.size, mic_audio.size)
        system = system_audio[:length].astype(np.float64)
        mic = mic_audio[:length].astype(np.float64)

        window = min(int(sample_rate * 0.05), length)
        if window < 32:
            return system_audio

        sys_window = system[:window]
        mic_window = mic[:window]

        denominator = (np.linalg.norm(sys_window) * np.linalg.norm(mic_window)) + 1e-9
        correlation = np.dot(sys_window, mic_window) / denominator
        correlation = np.clip(correlation, -1.0, 1.0)

        if abs(correlation) < 0.1:
            return system_audio

        effective_strength = np.clip(abs(correlation) * strength, 0.0, 0.8)
        echo_estimate = mic * effective_strength
        cleaned = system - echo_estimate
        return AudioProcessor.safe_clip(cleaned).astype(np.int16)

    @staticmethod
    def mix_tracks(mic_audio: np.ndarray, system_audio: np.ndarray) -> np.ndarray:
        if mic_audio.size == 0 and system_audio.size == 0:
            return np.array([], dtype=np.int16)

        if mic_audio.size == 0:
            return system_audio
        if system_audio.size == 0:
            return mic_audio

        length = min(mic_audio.size, system_audio.size)
        mixed = mic_audio[:length].astype(np.int32) + system_audio[:length].astype(np.int32)
        return AudioProcessor.safe_clip(mixed)

    @staticmethod
    def analyze_levels(audio: np.ndarray) -> Tuple[float, float]:
        if audio.size == 0:
            return -np.inf, -np.inf

        audio_float = audio.astype(np.float64)
        peak = np.max(np.abs(audio_float))
        rms = np.sqrt(np.mean(audio_float ** 2))

        peak_db = -np.inf if peak == 0 else 20.0 * np.log10(peak / 32767.0)
        rms_db = -np.inf if rms == 0 else 20.0 * np.log10(rms / 32767.0)
        return peak_db, rms_db


class AudioRecorder:
    """Gravador de áudio completo com processamento e streaming em tempo real."""

    def __init__(self):
        # Parâmetros básicos
        self.sample_rate = 44100
        self.channels = 2
        self.dtype = np.int16
        self.chunk = 1024

        # Configuração de chunking
        self.chunk_duration = 8
        self.chunk_overlap = 2

        # Flags e callbacks
        self.record_system_audio = True
        self.realtime_callback: Optional[RealtimeCallback] = None

        # Processamento
        self.processor = AudioProcessor()
        self.config = {
            "mic_gain_db": 7.5,
            "system_gain_db": 5.0,
            "enable_echo_reduction": True,
            "echo_strength": 0.55,
            "enable_noise_gate": True,
            "noise_gate_threshold_db": -65.0,
            "noise_gate_hold_ms": 250.0,
            "noise_gate_floor": 0.3,
            "enable_compressor": True,
            "compressor_threshold_db": -16.0,
            "compressor_ratio": 3.5,
            "normalize_target_db": -14.0,
        }

        # Dispositivos
        self.mic_device: Optional[int] = None
        self.system_device: Optional[int] = None

        # Streams
        self.mic_stream: Optional[sd.InputStream] = None
        self.system_stream: Optional[sd.InputStream] = None

        # Buffers e estatísticas
        self.mic_frames: List[bytes] = []
        self.system_audio_frames: List[bytes] = []
        self.mic_timestamps: List[float] = []
        self.system_timestamps: List[float] = []

        # Filas para tempo real
        self._mic_queue: Deque[bytes] = deque()
        self._system_queue: Deque[bytes] = deque()

        # Controle de concorrência
        self.recording = False
        self._lock = threading.Lock()
        self._chunk_event = threading.Event()
        self._stop_event = threading.Event()
        self._chunk_thread: Optional[threading.Thread] = None
        self._chunk_counter = 0
        self.system_recording_thread: Optional[threading.Thread] = None

        # Pastas e arquivos
        self._data_dir = Path("data")
        self._temp_dir = Path("temp")
        self._config_path = Path("config/audio_config.json")

        self._data_dir.mkdir(exist_ok=True)
        self._temp_dir.mkdir(exist_ok=True)
        self._config_path.parent.mkdir(exist_ok=True)

        # Carregar configurações e detectar dispositivos
        self._load_settings()
        self._auto_detect_devices()

    # ------------------------------------------------------------------
    # Persistência e configuração
    # ------------------------------------------------------------------
    def _load_settings(self) -> None:
        try:
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.config.update(payload)
                self.record_system_audio = payload.get("record_system_audio", self.record_system_audio)
                self.chunk_duration = payload.get("chunk_duration", self.chunk_duration)
                self.chunk_overlap = payload.get("chunk_overlap", self.chunk_overlap)
            self.config.setdefault("noise_gate_hold_ms", 250.0)
            self.config.setdefault("noise_gate_floor", 0.3)
            if self.config.get("noise_gate_threshold_db", -65.0) > -62.0:
                self.config["noise_gate_threshold_db"] = -65.0
            if self.config.get("noise_gate_hold_ms", 250.0) < 200.0:
                self.config["noise_gate_hold_ms"] = 250.0
            if self.config.get("noise_gate_floor", 0.3) < 0.25:
                self.config["noise_gate_floor"] = 0.3
            if self.config.get("mic_gain_db", 0.0) < 7.0:
                self.config["mic_gain_db"] = 7.5
        except Exception as exc:
            print(f"[AVISO] Não foi possível carregar configurações de áudio: {exc}")

    def save_settings(self) -> None:
        data = {
            **self.config,
            "record_system_audio": self.record_system_audio,
            "chunk_duration": self.chunk_duration,
            "chunk_overlap": self.chunk_overlap,
        }
        try:
            with open(self._config_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            print("[OK] Configurações de áudio salvas.")
        except Exception as exc:
            print(f"[ERRO] Falha ao salvar configurações de áudio: {exc}")

    # ------------------------------------------------------------------
    # API de compatibilidade com código legado
    # ------------------------------------------------------------------
    def set_input_device(self, device_index: Optional[int]) -> None:
        self.mic_device = device_index

    def set_record_system_audio(self, enable: bool) -> None:
        self.record_system_audio = bool(enable)
        if enable and self.system_device is None:
            self._auto_detect_devices()

    def set_realtime_transcription_callback(self, callback: Optional[RealtimeCallback]) -> None:
        self.realtime_callback = callback

    def configure_audio(
        self,
        mic_gain_db: float = 6.0,
        system_gain_db: float = 5.0,
        enable_echo_reduction: bool = True,
        echo_strength: float = 0.55,
    ) -> None:
        self.config["mic_gain_db"] = mic_gain_db
        self.config["system_gain_db"] = system_gain_db
        self.config["enable_echo_reduction"] = enable_echo_reduction
        self.config["echo_strength"] = max(0.0, min(0.8, echo_strength))
        self.save_settings()

    def set_audio_gains(self, mic_gain: float = 1.0, system_gain: float = 1.0) -> None:
        self.config["mic_gain_db"] = self.processor.linear_to_db(max(mic_gain, 1e-3))
        self.config["system_gain_db"] = self.processor.linear_to_db(max(system_gain, 1e-3))
        self.save_settings()

    def set_echo_reduction(self, enable: bool, strength: float = 0.55) -> None:
        self.config["enable_echo_reduction"] = enable
        self.config["echo_strength"] = max(0.0, min(0.8, strength))
        self.save_settings()

    def get_audio_devices(self) -> List[dict]:
        devices: List[dict] = []
        try:
            for index, device in enumerate(sd.query_devices()):
                if int(device.get("max_input_channels", 0)) <= 0:
                    continue
                devices.append(
                    {
                        "index": index,
                        "name": device.get("name", f"Dispositivo {index}"),
                        "channels": device.get("max_input_channels", 0),
                        "default_sample_rate": device.get("default_samplerate"),
                    }
                )
        except Exception as exc:
            print(f"[ERRO] Ao listar dispositivos: {exc}")
        return devices

    def get_system_audio_devices(self) -> List[dict]:
        candidates: List[dict] = []
        try:
            for index, device in enumerate(sd.query_devices()):
                if int(device.get("max_input_channels", 0)) <= 0:
                    continue
                name = str(device.get("name", "")).lower()
                if any(keyword in name for keyword in SYSTEM_KEYWORDS):
                    candidates.append(
                        {
                            "index": index,
                            "name": device.get("name", f"Loopback {index}"),
                            "channels": device.get("max_input_channels", 0),
                            "default_sample_rate": device.get("default_samplerate"),
                        }
                    )
        except Exception as exc:
            print(f"[ERRO] Ao listar dispositivos de sistema: {exc}")
        return candidates

    def get_default_device(self) -> Optional[dict]:
        try:
            default = sd.query_devices(kind="input")
            if default and isinstance(default, dict):
                return {
                    "index": default.get("index"),
                    "name": default.get("name"),
                    "channels": default.get("max_input_channels"),
                }
        except Exception:
            pass
        return None

    @property
    def rate(self) -> int:
        return self.sample_rate

    @rate.setter
    def rate(self, value: int) -> None:
        if value and value > 8000:
            self.sample_rate = int(value)
            self.save_settings()

    # ------------------------------------------------------------------
    # Detecção de dispositivos
    # ------------------------------------------------------------------
    def _auto_detect_devices(self) -> None:
        try:
            default_input = sd.query_devices(kind="input")
            if default_input and isinstance(default_input, dict):
                self.mic_device = default_input.get("index")
                print(f"[MIC] Dispositivo padrão: {default_input.get('name')}")
        except Exception as exc:
            print(f"[AVISO] Falha ao detectar microfone padrão: {exc}")

        try:
            for idx, device in enumerate(sd.query_devices()):
                if int(device.get("max_input_channels", 0)) == 0:
                    continue
                name = str(device.get("name", "")).lower()
                if any(keyword in name for keyword in SYSTEM_KEYWORDS):
                    self.system_device = idx
                    print(f"[SYS] Dispositivo de sistema detectado: {device.get('name')}")
                    break
            else:
                print("[AVISO] Nenhum dispositivo de áudio do sistema encontrado.")
        except Exception as exc:
            print(f"[ERRO] Falha ao detectar dispositivos: {exc}")

    def set_devices(self, mic_device: Optional[int] = None, system_device: Optional[int] = None) -> None:
        if mic_device is not None:
            self.mic_device = mic_device
        if system_device is not None:
            self.system_device = system_device

    # ------------------------------------------------------------------
    # Captura principal
    # ------------------------------------------------------------------
    def start_recording(self) -> bool:
        if self.recording:
            print("[AVISO] Gravação já está em andamento.")
            return False

        if self.mic_device is None:
            print("[ERRO] Nenhum microfone configurado.")
            return False

        self._prepare_buffers()
        self._stop_event.clear()
        self._chunk_event.clear()
        self.recording = True
        self._chunk_counter = 0
        self._start_time = time.time()

        try:
            self.mic_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk,
                callback=self._mic_callback,
                device=self.mic_device,
                latency="low",
            )
            self.mic_stream.start()
            print("[REC] Captura do microfone iniciada.")
        except Exception as exc:
            print(f"[ERRO] Falha ao iniciar microfone: {exc}")
            self.recording = False
            return False

        if self.record_system_audio and self.system_device is not None:
            try:
                self.system_stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="int16",
                    blocksize=self.chunk,
                    callback=self._system_callback,
                    device=self.system_device,
                    latency="low",
                )
                self.system_stream.start()
                print("[REC] Captura do áudio do sistema iniciada.")
            except Exception as exc:
                print(f"[AVISO] Falha ao iniciar captura do sistema: {exc}")
                self.system_stream = None

        if self.realtime_callback:
            self._chunk_thread = threading.Thread(target=self._chunk_worker, daemon=True)
            self._chunk_thread.start()

        return True

    def _prepare_buffers(self) -> None:
        with self._lock:
            self.mic_frames.clear()
            self.system_audio_frames.clear()
            self.mic_timestamps.clear()
            self.system_timestamps.clear()
            self._mic_queue.clear()
            self._system_queue.clear()

    def _mic_callback(self, indata, frames, time_info, status) -> None:
        if status:
            print(f"[AVISO] Callback do microfone reportou status: {status}")

        if not self.recording:
            return

        data_bytes = bytes(indata.copy().tobytes())
        timestamp = time.time()

        with self._lock:
            self.mic_frames.append(data_bytes)
            self._mic_queue.append(data_bytes)
            self.mic_timestamps.append(timestamp)
        self._chunk_event.set()

    def _system_callback(self, indata, frames, time_info, status) -> None:
        if status:
            print(f"[AVISO] Callback do sistema reportou status: {status}")

        if not self.recording:
            return

        data_bytes = bytes(indata.copy().tobytes())
        timestamp = time.time()

        with self._lock:
            self.system_audio_frames.append(data_bytes)
            self._system_queue.append(data_bytes)
            self.system_timestamps.append(timestamp)
        self._chunk_event.set()

    def stop_recording(self) -> Optional[str]:
        if not self.recording:
            print("[AVISO] Nenhuma gravação ativa.")
            return None

        self.recording = False
        self._stop_event.set()
        self._chunk_event.set()

        self._cleanup_streams()

        if self._chunk_thread and self._chunk_thread.is_alive():
            self._chunk_thread.join(timeout=5.0)
        self._chunk_thread = None

        try:
            return self._render_final_file()
        except Exception as exc:
            print(f"[ERRO] Falha ao finalizar gravação: {exc}")
            return None

    def _cleanup_streams(self) -> None:
        if self.mic_stream:
            try:
                self.mic_stream.stop()
                self.mic_stream.close()
            except Exception:
                pass
            self.mic_stream = None

        if self.system_stream:
            try:
                self.system_stream.stop()
                self.system_stream.close()
            except Exception:
                pass
            self.system_stream = None

    # ------------------------------------------------------------------
    # Chunking e tempo real
    # ------------------------------------------------------------------
    def _chunk_worker(self) -> None:
        chunk_samples = int(self.chunk_duration * self.sample_rate * self.channels)
        step_seconds = max(self.chunk_duration - self.chunk_overlap, 1)
        step_samples = int(step_seconds * self.sample_rate * self.channels)

        mic_buffer = np.array([], dtype=np.int16)
        system_buffer = np.array([], dtype=np.int16)

        while True:
            self._chunk_event.wait(timeout=0.5)
            self._chunk_event.clear()

            with self._lock:
                mic_queue = self._drain_queue(self._mic_queue)
                system_queue = self._drain_queue(self._system_queue)

            if mic_queue.size:
                mic_buffer = np.concatenate((mic_buffer, mic_queue))
            if system_queue.size:
                system_buffer = np.concatenate((system_buffer, system_queue))

            should_continue = self.recording or mic_buffer.size >= chunk_samples
            if not should_continue and self._stop_event.is_set():
                if mic_buffer.size or system_buffer.size:
                    self._emit_chunk(mic_buffer, system_buffer, final_chunk=True)
                break

            while mic_buffer.size >= chunk_samples:
                mic_chunk = mic_buffer[:chunk_samples]
                sys_chunk = system_buffer[:chunk_samples] if system_buffer.size >= chunk_samples else np.array([], dtype=np.int16)
                self._emit_chunk(mic_chunk, sys_chunk)

                mic_buffer = mic_buffer[step_samples:]
                if system_buffer.size >= step_samples:
                    system_buffer = system_buffer[step_samples:]
                else:
                    system_buffer = np.array([], dtype=np.int16)

    def _drain_queue(self, queue: Deque[bytes]) -> np.ndarray:
        if not queue:
            return np.array([], dtype=np.int16)
        frames = []
        while queue:
            frames.append(np.frombuffer(queue.popleft(), dtype=np.int16))
        return np.concatenate(frames) if frames else np.array([], dtype=np.int16)

    def _emit_chunk(self, mic_chunk: np.ndarray, system_chunk: np.ndarray, final_chunk: bool = False) -> None:
        if self.realtime_callback is None:
            return

        processed = self._process_pair(mic_chunk, system_chunk)
        if processed.size == 0:
            return

        self._chunk_counter += 1
        chunk_name = f"chunk_{self._chunk_counter:03d}.wav"
        chunk_path = self._temp_dir / chunk_name
        self._write_wav(chunk_path, processed)

        try:
            self.realtime_callback(str(chunk_path), self._chunk_counter)
        except Exception as exc:
            print(f"[AVISO] Callback de chunk gerou exceção: {exc}")

        if final_chunk:
            self._chunk_event.set()

    # ------------------------------------------------------------------
    # Processamento e salvamento
    # ------------------------------------------------------------------
    def _process_pair(self, mic_audio: np.ndarray, system_audio: np.ndarray) -> np.ndarray:
        mic_audio = mic_audio.astype(np.int16, copy=False)
        system_audio = system_audio.astype(np.int16, copy=False)

        if mic_audio.size:
            mic_audio = self.processor.high_pass_filter(mic_audio, self.sample_rate)
            mic_audio = self.processor.apply_gain(mic_audio, self.config.get("mic_gain_db", 0.0))
            if self.config.get("enable_noise_gate", True):
                mic_audio = self.processor.apply_noise_gate(
                    mic_audio,
                    sample_rate=self.sample_rate,
                    threshold_db=self.config.get("noise_gate_threshold_db", -55.0),
                    hold_ms=self.config.get("noise_gate_hold_ms", 120.0),
                    floor=self.config.get("noise_gate_floor", 0.12),
                )

        if system_audio.size:
            system_audio = self.processor.high_pass_filter(system_audio, self.sample_rate, cutoff=60.0)
            system_audio = self.processor.apply_gain(system_audio, self.config.get("system_gain_db", 0.0))

        if self.config.get("enable_echo_reduction", True) and mic_audio.size and system_audio.size:
            system_audio = self.processor.reduce_echo(
                system_audio,
                mic_audio,
                sample_rate=self.sample_rate,
                strength=self.config.get("echo_strength", 0.55),
            )

        mixed = self.processor.mix_tracks(mic_audio, system_audio)

        if self.config.get("enable_compressor", True):
            mixed = self.processor.apply_compressor(
                mixed,
                threshold_db=self.config.get("compressor_threshold_db", -16.0),
                ratio=self.config.get("compressor_ratio", 3.5),
            )

        mixed = self.processor.normalize(mixed, target_db=self.config.get("normalize_target_db", -14.0))
        return mixed

    def _render_final_file(self) -> str:
        mic_audio = self._merge_bytes(self.mic_frames)
        system_audio = self._merge_bytes(self.system_audio_frames)
        final_audio = self._process_pair(mic_audio, system_audio)

        if final_audio.size == 0:
            raise RuntimeError("Nenhum áudio foi capturado.")

        peak_db, rms_db = self.processor.analyze_levels(final_audio)
        print(f"[ANÁLISE] Pico {peak_db:.1f} dBFS | RMS {rms_db:.1f} dBFS")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self._data_dir / f"recording_{timestamp}.wav"
        self._write_wav(output_path, final_audio)
        print(f"[OK] Arquivo salvo em {output_path}")
        return str(output_path)

    def _merge_bytes(self, frames: List[bytes]) -> np.ndarray:
        if not frames:
            return np.array([], dtype=np.int16)
        data = b"".join(frames)
        return np.frombuffer(data, dtype=np.int16)

    def _write_wav(self, path: Path, audio: np.ndarray) -> None:
        if audio.size == 0:
            return

        remainder = audio.size % self.channels
        if remainder:
            audio = audio[:-remainder]

        stereo = audio.reshape(-1, self.channels)

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(stereo.astype(np.int16).tobytes())

    # ------------------------------------------------------------------
    # Diagnósticos e utilidades
    # ------------------------------------------------------------------
    def diagnose_audio_issues(self, filename: Optional[str] = None) -> None:
        print("\n=== DIAGNÓSTICO DE ÁUDIO ===")
        print(f"Sample rate: {self.sample_rate} Hz | Canais: {self.channels}")
        print(f"Ganho Mic: {self.config['mic_gain_db']:+.1f} dB | Ganho Sistema: {self.config['system_gain_db']:+.1f} dB")
        print(f"Normalização alvo: {self.config['normalize_target_db']:.1f} dBFS")
        print(f"Redução de eco: {'Ativa' if self.config.get('enable_echo_reduction', True) else 'Inativa'}")
        print(f"Noise gate: {'Ativo' if self.config.get('enable_noise_gate', True) else 'Inativo'}")

        if filename:
            try:
                with wave.open(filename, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                peak_db, rms_db = self.processor.analyze_levels(audio)
                print(f"[Arquivo] {filename}")
                print(f"          Pico {peak_db:.1f} dBFS | RMS {rms_db:.1f} dBFS")
            except Exception as exc:
                print(f"[ERRO] Não foi possível analisar {filename}: {exc}")

        print("=== FIM DO DIAGNÓSTICO ===\n")

    def check_system_audio_capability(self) -> Tuple[bool, str]:
        devices = self.get_system_audio_devices()
        if not devices:
            message = (
                "Nenhum dispositivo de loopback encontrado. Habilite o 'Stereo Mix' ou recurso equivalente "
                "nas configurações de som."
            )
            return False, message
        return True, f"{len(devices)} dispositivo(s) de áudio do sistema disponíveis."

    def get_system_audio_setup_instructions(self) -> str:
        return (
            "Como habilitar a captura do áudio do sistema (Windows):\n"
            "1. Clique com o botão direito no ícone de som e selecione 'Sons'.\n"
            "2. Abra a aba 'Gravação'.\n"
            "3. Habilite 'Mostrar dispositivos desativados'.\n"
            "4. Ative 'Mixagem Estéreo' e defina como dispositivo padrão.\n"
            "5. Volte ao MeetAI e selecione o dispositivo na lista.\n"
        )

    def get_audio_level(self) -> int:
        with self._lock:
            recent = self.mic_frames[-5:] if self.mic_frames else []
        if not recent:
            return 0
        audio = np.frombuffer(b"".join(recent), dtype=np.int16)
        if audio.size == 0:
            return 0
        rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
        level = int((rms / 32767.0) * 100 * 2.5)
        return max(0, min(100, level))

    # ------------------------------------------------------------------
    # Operações adicionais / compatibilidade
    # ------------------------------------------------------------------
    def _start_system_audio_recording(self) -> bool:
        if self.system_device is None:
            return False

        self._prepare_buffers()
        self._stop_event.clear()
        self.record_system_audio = True
        self.recording = True

        try:
            self.system_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk,
                callback=self._system_callback,
                device=self.system_device,
                latency="low",
            )
            self.system_stream.start()
            print("[REC] Captura somente do áudio do sistema iniciada.")
            return True
        except Exception as exc:
            print(f"[ERRO] Falha ao iniciar captura do sistema: {exc}")
            self.system_stream = None
            self.recording = False
            return False

    def quick_setup_for_meetings(self) -> None:
        self.configure_audio(mic_gain_db=6.5, system_gain_db=6.0, enable_echo_reduction=True, echo_strength=0.5)
        self.config["noise_gate_threshold_db"] = -60.0

    def quick_setup_for_presentations(self) -> None:
        self.configure_audio(mic_gain_db=4.5, system_gain_db=6.5, enable_echo_reduction=True, echo_strength=0.45)
        self.config["noise_gate_threshold_db"] = -55.0

    def quick_setup_low_noise(self) -> None:
        self.configure_audio(mic_gain_db=8.0, system_gain_db=5.0, enable_echo_reduction=True, echo_strength=0.35)
        self.config["noise_gate_threshold_db"] = -60.0

    def __del__(self):
        try:
            self._cleanup_streams()
        except Exception:
            pass


def get_audio_devices() -> List[dict]:
    """Compatibilidade com importações antigas."""
    return AudioRecorder().get_audio_devices()


def get_system_audio_devices() -> List[dict]:
    """Compatibilidade com importações antigas."""
    return AudioRecorder().get_system_audio_devices()
